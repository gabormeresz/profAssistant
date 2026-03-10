"""
Phase 1 — Generate zero-shot drafts for LLM-as-a-Judge evaluation.

Runs each prompt from ``prompt_set.json`` through the full course-outline
LangGraph pipeline (gpt-4o-mini), capturing:

* **Draft**: The raw ``agent_response.content`` after the first ``generate``
  node — before any refinement.
* **Internal evaluator first score**: The ``EvaluationResult`` from the
  internal evaluator's initial assessment of the draft.

Results are persisted to ``drafts.json`` so Phase 2 (judge scoring +
analysis) can run without re-generation.

This test is implemented as a single function (not parametrised) to
avoid compiling the graph 15 times and to produce a single consolidated
artifact file.
"""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pytest
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.course_outline.graph import build_course_outline_graph
from config import EvaluationConfig
from schemas.course_outline import CourseOutline

from conftest import DRAFTS_FILE, GENERATION_MODEL, TESTS_DIR

pytestmark = pytest.mark.llm
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load prompt set
# ---------------------------------------------------------------------------
PROMPT_SET_FILE = TESTS_DIR / "prompt_set.json"

with open(PROMPT_SET_FILE, encoding="utf-8") as f:
    _PROMPT_DATA = json.load(f)

PROMPTS: List[Dict[str, Any]] = _PROMPT_DATA["prompts"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _evaluation_to_dict(ev) -> dict:
    """Serialise an ``EvaluationResult`` object to a plain dict."""
    return {
        "score": ev.score,
        "verdict": ev.verdict,
        "reasoning": ev.reasoning,
        "score_breakdown": {
            "learning_objectives": ev.score_breakdown.learning_objectives,
            "content_coverage": ev.score_breakdown.content_coverage,
            "progression": ev.score_breakdown.progression,
            "activities": ev.score_breakdown.activities,
            "completeness": ev.score_breakdown.completeness,
        },
        "suggestions": [
            {"dimension": s.dimension, "text": s.text} for s in (ev.suggestions or [])
        ],
    }


# ---------------------------------------------------------------------------
# Phase 1 test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_all_drafts(real_api_key: str):
    """
    Run each prompt through the course-outline generation graph and
    capture the zero-shot draft (first ``generate`` output).

    The graph runs to completion (including any internal refinement)
    so we can also record whether refinement was triggered and capture
    the internal evaluator's first score — but the focus is on the
    draft itself.
    """
    results: List[Dict[str, Any]] = []

    for idx, prompt in enumerate(PROMPTS, start=1):
        prompt_id = prompt["id"]
        logger.info(
            "━━━ [%d/%d] Generating: %s — %s ━━━",
            idx,
            len(PROMPTS),
            prompt_id,
            prompt["topic"],
        )

        thread_id = str(uuid.uuid4())

        input_state = {
            "topic": prompt["topic"],
            "number_of_classes": prompt["number_of_classes"],
            "message": prompt["message"],
            "file_contents": [],
            "language": prompt["language"],
            "thread_id": thread_id,
            "is_first_call": True,
            "user_id": "judge-test",
        }

        workflow = build_course_outline_graph()

        async with AsyncSqliteSaver.from_conn_string(":memory:") as memory:
            graph = workflow.compile(checkpointer=memory)
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": EvaluationConfig.GRAPH_RECURSION_LIMIT,
            }

            # ── stream events to capture draft ──
            draft_content: str | None = None
            first_generate_seen = False
            t_start = time.perf_counter()

            async for event in graph.astream_events(
                input_state, config=config, version="v2"
            ):
                event_type = event.get("event")
                event_name = event.get("name", "")

                # Capture the first generate output as the "draft"
                if (
                    event_type == "on_chain_end"
                    and event_name == "generate"
                    and not first_generate_seen
                ):
                    output = event.get("data", {}).get("output", {})
                    agent_resp = output.get("agent_response")
                    if agent_resp is not None:
                        content = (
                            agent_resp.content
                            if hasattr(agent_resp, "content")
                            else str(agent_resp)
                        )
                        # Only capture real content (not bare tool calls)
                        if content and not (
                            hasattr(agent_resp, "tool_calls")
                            and agent_resp.tool_calls
                            and not content.strip()
                        ):
                            draft_content = content
                            first_generate_seen = True

            t_elapsed = time.perf_counter() - t_start

            # ── fetch final state for metadata ──
            final_state = await graph.aget_state(config)
            state_values = final_state.values if final_state else {}

            final_response = state_values.get("final_response")
            evaluation_history = state_values.get("evaluation_history", [])

            # Serialise final_response (kept for reference, not scored)
            if isinstance(final_response, CourseOutline):
                final_response_dict = final_response.model_dump()
            elif isinstance(final_response, dict):
                final_response_dict = final_response
            else:
                final_response_dict = None

            # Internal evaluator's first assessment of the draft
            first_eval = (
                _evaluation_to_dict(evaluation_history[0])
                if evaluation_history
                else None
            )
            first_score = evaluation_history[0].score if evaluation_history else None

            record = {
                "prompt_id": prompt_id,
                "discipline": prompt["discipline"],
                "topic": prompt["topic"],
                "number_of_classes": prompt["number_of_classes"],
                "language": prompt["language"],
                "draft_content": draft_content,
                "final_response": final_response_dict,
                "internal_first_eval": first_eval,
                "generation_metadata": {
                    "model": GENERATION_MODEL,
                    "approval_threshold": EvaluationConfig.APPROVAL_THRESHOLD,
                    "internal_first_score": first_score,
                    "refinement_rounds": len(evaluation_history),
                    "duration_sec": round(t_elapsed, 2),
                },
            }
            results.append(record)

            logger.info(
                "  ✓ %s  internal_first=%.2f  rounds=%d  (%.1fs)",
                prompt_id,
                first_score or 0,
                len(evaluation_history),
                t_elapsed,
            )

    # ── persist results ──
    export = {
        "model": GENERATION_MODEL,
        "approval_threshold": EvaluationConfig.APPROVAL_THRESHOLD,
        "total_prompts": len(PROMPTS),
        "generated": len(results),
        "drafts": results,
    }
    DRAFTS_FILE.write_text(
        json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # ── summary table ──
    print("\n")
    print("=" * 80)
    print("  PHASE 1 — ZERO-SHOT DRAFT GENERATION")
    print("=" * 80)
    print(f"  Model:     {GENERATION_MODEL}")
    print(f"  Threshold: {EvaluationConfig.APPROVAL_THRESHOLD} (production)")
    print(f"  Prompts:   {len(results)} / {len(PROMPTS)}")
    print("-" * 80)
    print(f"  {'ID':<30} {'Int.Score':>10} {'Rounds':>7} {'Time':>8}")
    print("-" * 80)
    for r in results:
        m = r["generation_metadata"]
        score_str = (
            f"{m['internal_first_score']:.2f}" if m["internal_first_score"] else "N/A"
        )
        print(
            f"  {r['prompt_id']:<30} {score_str:>10} "
            f"{m['refinement_rounds']:>7} {m['duration_sec']:>7.1f}s"
        )
    print("=" * 80)

    total_time = sum(r["generation_metadata"]["duration_sec"] for r in results)
    scores = [
        r["generation_metadata"]["internal_first_score"]
        for r in results
        if r["generation_metadata"]["internal_first_score"] is not None
    ]
    avg_score = sum(scores) / len(scores) if scores else 0
    print(
        f"  Total time: {total_time:.0f}s  |  Avg internal first score: {avg_score:.3f}"
    )
    print()

    # Sanity checks (quality assertions are in Phase 2)
    assert len(results) == len(
        PROMPTS
    ), f"Expected {len(PROMPTS)} results, got {len(results)}"
    for r in results:
        assert (
            r["draft_content"] is not None
        ), f"[{r['prompt_id']}] draft_content is None — draft capture failed"
        assert (
            r["final_response"] is not None
        ), f"[{r['prompt_id']}] final_response is None — generation may have failed"
