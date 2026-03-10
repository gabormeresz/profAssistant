"""
Re-run a single prompt for a given model and swap the result in the
per-model benchmark artifact file.

Usage:
    cd backend
    python test_and_evals/03_performance_and_cost/01_model_profiling/tests/rerun_prompt.py \
        --model gpt-4o-mini --prompt co_simple_ws
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ensure backend is importable
BACKEND_DIR = str(Path(__file__).resolve().parents[4])
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from conftest import (
    MODEL_LIST,
    benchmark_file_for_model,
    build_input_state,
    get_graph_builders,
    mock_infra_for_module,
    PROMPT_SET_FILE,
)
from test_phase1_benchmark import run_and_collect


async def main(model_name: str, prompt_id: str) -> None:
    import os
    from dotenv import load_dotenv

    project_root = Path(BACKEND_DIR).parent
    load_dotenv(project_root / ".env")
    load_dotenv(Path(BACKEND_DIR) / ".env")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        sys.exit(1)

    # Load prompt set
    with open(PROMPT_SET_FILE, encoding="utf-8") as f:
        prompt_set = json.load(f)

    prompt = next((p for p in prompt_set if p["id"] == prompt_id), None)
    if prompt is None:
        ids = [p["id"] for p in prompt_set]
        print(f"ERROR: prompt_id '{prompt_id}' not found. Available: {ids}")
        sys.exit(1)

    # Load existing benchmark file
    out_file = benchmark_file_for_model(model_name)
    if not out_file.exists():
        print(f"ERROR: Benchmark file not found: {out_file}")
        sys.exit(1)

    with open(out_file, encoding="utf-8") as f:
        results = json.load(f)

    # Initialize live MCP
    from services.mcp_client import mcp_manager

    mcp_manager._initialized = False
    mcp_manager._tools = None
    mcp_manager._client = None
    await mcp_manager.initialize()
    tool_names = [t.name for t in mcp_manager.get_tools()]
    print(f"[MCP] Initialized with {len(tool_names)} tools: {tool_names}")

    # Run the prompt
    module = prompt["module"]
    graph_builders = get_graph_builders()
    build_fn = graph_builders[module]
    input_state = build_input_state(prompt)
    thread_id = input_state["thread_id"]

    print(f"\nRe-running: model={model_name} prompt={prompt_id} module={module}")
    print("=" * 70)

    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    from config import EvaluationConfig

    with mock_infra_for_module(api_key, model_name, module, use_live_mcp=True):
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
        "variant": prompt["variant"],
        "discipline": prompt["discipline"],
        "thread_id": thread_id,
        **metrics,
    }

    # Print summary
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

    # Swap in the results list
    swapped = False
    for i, r in enumerate(results):
        if r["prompt_id"] == prompt_id:
            results[i] = record
            swapped = True
            break

    if not swapped:
        print(f"WARNING: prompt_id '{prompt_id}' not found in {out_file}, appending.")
        results.append(record)

    # Save
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    action = "Swapped" if swapped else "Appended"
    print(f"\n{action} result for '{prompt_id}' in {out_file}")

    await mcp_manager.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-run a single benchmark prompt")
    parser.add_argument(
        "--model",
        required=True,
        help=f"Model name. Available: {MODEL_LIST}",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Prompt ID from prompt_set_ab.json (e.g. co_simple_ws)",
    )
    args = parser.parse_args()

    if args.model not in MODEL_LIST:
        print(f"ERROR: Unknown model '{args.model}'. Available: {MODEL_LIST}")
        sys.exit(1)

    asyncio.run(main(args.model, args.prompt))
