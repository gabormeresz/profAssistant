"""
Phase 1 — Benchmark data collection.

Runs every prompt in ``prompt_set_ab.json`` through each selected model,
capturing latency, token usage, tool calls, and refinement loop data via
``astream_events``.  Each model's results are persisted to a **separate**
artifact file (``artifacts/benchmark_raw_<model>.json``) so that models
can be benchmarked independently and results collected incrementally.

Usage (all models):
    cd backend
    python -m pytest test_and_evals/03_performance_and_cost/01_model_profiling/tests/test_phase1_benchmark.py \
        -m llm -v --tb=short -s 2>&1 | tee test_and_evals/03_performance_and_cost/01_model_profiling/tests/logs/phase1_$(date +%F).log

Usage (single model):
    cd backend
    python -m pytest test_and_evals/03_performance_and_cost/01_model_profiling/tests/test_phase1_benchmark.py \
        -m llm --model gpt-4o-mini -v --tb=short -s

Usage (multiple specific models):
    python -m pytest ... --model gpt-4o-mini --model gpt-5
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import pytest

from conftest import (
    ARTIFACTS_DIR,
    MODEL_LIST,
    PROMPT_SET_FILE,
    benchmark_file_for_model,
    build_input_state,
    get_graph_builders,
    mock_infra_for_module,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Metrics collection helper
# ---------------------------------------------------------------------------

# Node names whose start / end events we track individually.
_TRACKED_NODES = {
    "initialize",
    "ingest_documents",
    "generate",
    "evaluate",
    "refine",
    "respond",
}


async def run_and_collect(graph, input_state: dict, config: dict) -> Dict[str, Any]:
    """
    Execute *graph* via ``astream_events`` and collect operational metrics.

    Returns a dict with keys:
        total_duration_s, ttft_s, node_timings, token_usage,
        tool_calls, refinement, success, error
    """
    metrics: Dict[str, Any] = {
        "total_duration_s": 0.0,
        "ttft_s": None,
        "node_timings": {},
        "token_usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "reasoning_tokens": 0,
            "cached_tokens": 0,
        },
        "tool_calls": [],
        "refinement": {
            "count": 0,
            "exit_reason": "first_pass_approved",
            "scores": [],
        },
        "success": False,
        "error": None,
    }

    # Timing helpers
    t_start = time.perf_counter()
    node_starts: Dict[str, float] = {}
    tool_starts: Dict[str, float] = {}
    ttft_captured = False

    try:
        async for event in graph.astream_events(
            input_state, config=config, version="v2"
        ):
            event_type = event.get("event")
            event_name = event.get("name", "")
            now = time.perf_counter()

            # ----- Node lifecycle -----
            if event_type == "on_chain_start" and event_name in _TRACKED_NODES:
                node_starts[event_name] = now

                # Track refinement iterations
                if event_name == "refine":
                    metrics["refinement"]["count"] += 1

            elif event_type == "on_chain_end" and event_name in _TRACKED_NODES:
                if event_name in node_starts:
                    duration = now - node_starts[event_name]
                    # Accumulate — refine/evaluate may run multiple times
                    existing = metrics["node_timings"].get(event_name)
                    if existing is None:
                        metrics["node_timings"][event_name] = {
                            "total_duration_s": duration,
                            "invocations": 1,
                        }
                    else:
                        existing["total_duration_s"] += duration
                        existing["invocations"] += 1

                # Capture evaluation scores from the evaluate node output
                if event_name == "evaluate":
                    output = event.get("data", {}).get("output", {})
                    score = None
                    if isinstance(output, dict):
                        score = output.get("current_score")
                        # Also check evaluation_history
                        history = output.get("evaluation_history")
                        if history and isinstance(history, list):
                            for entry in history:
                                if hasattr(entry, "overall_score"):
                                    score = entry.overall_score
                                elif isinstance(entry, dict):
                                    score = entry.get("overall_score", score)
                    if score is not None:
                        metrics["refinement"]["scores"].append(float(score))

            # ----- TTFT: first LLM stream token -----
            elif event_type == "on_chat_model_stream" and not ttft_captured:
                metrics["ttft_s"] = now - t_start
                ttft_captured = True

            # ----- Token usage from LLM completions -----
            elif event_type == "on_chat_model_end":
                output = event.get("data", {}).get("output")
                if output is not None:
                    _accumulate_tokens(metrics["token_usage"], output)

            # ----- Tool calls -----
            elif event_type == "on_tool_start":
                tool_name = event.get("name", "unknown")
                tool_starts[f"{tool_name}_{id(event)}"] = now
                # Append placeholder — duration filled on end
                metrics["tool_calls"].append(
                    {"tool_name": tool_name, "duration_s": None}
                )

            elif event_type == "on_tool_end":
                tool_name = event.get("name", "unknown")
                # Find the matching start (latest unclosed)
                for tc in reversed(metrics["tool_calls"]):
                    if tc["tool_name"] == tool_name and tc["duration_s"] is None:
                        # Find matching start key
                        for key in list(tool_starts.keys()):
                            if key.startswith(tool_name):
                                tc["duration_s"] = now - tool_starts.pop(key)
                                break
                        break

            # ----- Final output -----
            elif event_type == "on_chain_end" and event_name == "LangGraph":
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict):
                    if output.get("final_response") is not None:
                        metrics["success"] = True
                    if output.get("error"):
                        metrics["error"] = str(output["error"])

                    # Extract final evaluation data from graph state
                    eval_history = output.get("evaluation_history", [])
                    if eval_history:
                        for entry in eval_history:
                            s = None
                            if hasattr(entry, "overall_score"):
                                s = entry.overall_score
                            elif isinstance(entry, dict):
                                s = entry.get("overall_score")
                            if (
                                s is not None
                                and s not in metrics["refinement"]["scores"]
                            ):
                                metrics["refinement"]["scores"].append(float(s))

    except Exception as exc:
        metrics["error"] = f"{type(exc).__name__}: {exc}"
        logger.exception("Error during benchmark run")

    metrics["total_duration_s"] = time.perf_counter() - t_start

    # Determine refinement exit reason
    _classify_exit_reason(metrics)

    return metrics


def _accumulate_tokens(usage: Dict[str, int], output: Any) -> None:
    """Extract token counts from an AIMessage or similar object."""
    # LangChain AIMessage carries usage_metadata (may be dict or dataclass)
    um = getattr(output, "usage_metadata", None)
    if um is not None:
        if isinstance(um, dict):
            usage["prompt_tokens"] += um.get("input_tokens", 0) or 0
            usage["completion_tokens"] += um.get("output_tokens", 0) or 0
            usage["total_tokens"] += um.get("total_tokens", 0) or 0
            # Capture reasoning tokens for o-series / reasoning models
            details = um.get("output_token_details") or {}
            if isinstance(details, dict):
                usage["reasoning_tokens"] += details.get("reasoning", 0) or 0
            # Capture cached input tokens
            input_details = um.get("input_token_details") or {}
            if isinstance(input_details, dict):
                usage["cached_tokens"] += input_details.get("cache_read", 0) or 0
        else:
            usage["prompt_tokens"] += getattr(um, "input_tokens", 0) or 0
            usage["completion_tokens"] += getattr(um, "output_tokens", 0) or 0
            usage["total_tokens"] += getattr(um, "total_tokens", 0) or 0
        return

    # Fallback: response_metadata.token_usage (older versions)
    rm = getattr(output, "response_metadata", None)
    if rm and isinstance(rm, dict):
        tu = rm.get("token_usage") or rm.get("usage", {})
        if isinstance(tu, dict):
            usage["prompt_tokens"] += tu.get("prompt_tokens", 0)
            usage["completion_tokens"] += tu.get("completion_tokens", 0)
            usage["total_tokens"] += tu.get("total_tokens", 0)


def _classify_exit_reason(metrics: Dict[str, Any]) -> None:
    """Classify why the refinement loop terminated."""
    ref = metrics["refinement"]
    scores = ref["scores"]
    count = ref["count"]

    if count == 0:
        ref["exit_reason"] = "first_pass_approved"
    elif metrics["success"] and scores:
        last = scores[-1]
        if last >= 0.8:
            ref["exit_reason"] = "refined_approved"
        elif count >= 3:
            ref["exit_reason"] = "max_retries"
        elif len(scores) >= 2 and abs(scores[-1] - scores[-2]) < 0.02:
            ref["exit_reason"] = "plateau"
        else:
            ref["exit_reason"] = "refined_approved"
    elif count >= 3:
        ref["exit_reason"] = "max_retries"
    else:
        ref["exit_reason"] = "unknown"


# ---------------------------------------------------------------------------
# Main benchmark test
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Main benchmark test — one test per model
# ---------------------------------------------------------------------------


def pytest_generate_tests(metafunc):
    """Parametrize ``model_name`` based on the ``--model`` CLI option."""
    if "model_name" in metafunc.fixturenames:
        from conftest import _selected_models

        models = _selected_models(metafunc.config)
        metafunc.parametrize("model_name", models, scope="session")


@pytest.mark.llm
@pytest.mark.asyncio
async def test_benchmark_model(real_api_key, prompt_set, live_mcp, model_name):
    """
    Run all prompts for a single *model_name* and save raw benchmark data
    to ``artifacts/benchmark_raw_<model_name>.json``.

    Each model produces its own artifact file, enabling independent runs
    and incremental data collection across sessions.
    """
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    from config import EvaluationConfig

    graph_builders = get_graph_builders()
    out_file = benchmark_file_for_model(model_name)

    # Load any previously collected results for this model so we can
    # resume after a crash without losing earlier prompts.
    results: List[Dict[str, Any]] = []
    already_done: set = set()
    if out_file.exists():
        with open(out_file, encoding="utf-8") as f:
            results = json.load(f)
        already_done = {r["prompt_id"] for r in results}
        if already_done:
            print(
                f"\n  [resume] {len(already_done)} prompts already recorded "
                f"for {model_name} — skipping them."
            )

    remaining_prompts = [p for p in prompt_set if p["id"] not in already_done]
    total = len(prompt_set)
    done_before = len(already_done)

    for idx, prompt in enumerate(remaining_prompts, start=done_before + 1):
        prompt_id = prompt["id"]
        module = prompt["module"]
        variant = prompt["variant"]

        print(
            f"\n{'='*70}\n"
            f"[{idx}/{total}] "
            f"Model: {model_name} | Prompt: {prompt_id} ({module}/{variant})\n"
            f"{'='*70}"
        )

        build_fn = graph_builders[module]
        input_state = build_input_state(prompt)
        thread_id = input_state["thread_id"]

        with mock_infra_for_module(real_api_key, model_name, module, use_live_mcp=True):
            workflow = build_fn()
            async with AsyncSqliteSaver.from_conn_string(":memory:") as memory:
                graph = workflow.compile(checkpointer=memory)
                config = {
                    "configurable": {"thread_id": thread_id},
                    "recursion_limit": EvaluationConfig.GRAPH_RECURSION_LIMIT,
                }

                metrics = await run_and_collect(graph, input_state, config)

        record = {
            "model": model_name,
            "prompt_id": prompt_id,
            "module": module,
            "variant": variant,
            "discipline": prompt["discipline"],
            "thread_id": thread_id,
            **metrics,
        }
        results.append(record)

        # Print summary for this run
        status = "OK" if metrics["success"] else "FAIL"
        dur = metrics["total_duration_s"]
        ttft = metrics["ttft_s"]
        tokens = metrics["token_usage"]["total_tokens"]
        refine_n = metrics["refinement"]["count"]
        n_tools = len(metrics["tool_calls"])
        print(
            f"  -> {status} | {dur:.1f}s total | "
            f"TTFT={ttft:.2f}s | "
            f"{tokens:,} tokens | "
            f"{refine_n} refinements | "
            f"{n_tools} tool calls"
        )

        # Incremental save — don't lose data on crash
        _save_results(results, out_file)

    # Final save
    _save_results(results, out_file)

    print(f"\n{'='*70}")
    print(
        f"Benchmark complete for {model_name}: "
        f"{len(results)} runs saved to {out_file}"
    )
    print(f"{'='*70}\n")

    # Basic sanity assertions
    assert (
        len(results) == total
    ), f"Expected {total} results for {model_name} but got {len(results)}"
    success_count = sum(1 for r in results if r["success"])
    print(f"Success rate for {model_name}: {success_count}/{len(results)}")


def _save_results(results: List[Dict[str, Any]], path) -> None:
    """Persist results to JSON with pretty-printing."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
