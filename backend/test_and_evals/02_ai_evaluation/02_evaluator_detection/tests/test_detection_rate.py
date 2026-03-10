"""
Part 1 — Evaluator Detection Rate.

Tests whether the internal evaluator agent reliably classifies
deliberately flawed course outlines as ``NEEDS_REFINEMENT``.

Each of the 7 flawed outputs in ``flawed_outputs.json`` is fed
directly through the real ``evaluate_outline`` node (no graph
overhead) so the measurement isolates the evaluator's detection
capability.

Metrics collected
-----------------
* Per-case: verdict, score, score_breakdown, targeted-dimension scores
* Aggregate: detection rate (target: 100 %)

Results are exported to ``detection_results.json`` in the ``tests/artifacts/``
directory and a human-readable summary is printed to stdout.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent.course_outline.nodes.evaluation import evaluate_outline
from config import EvaluationConfig

pytestmark = pytest.mark.llm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths & data loading
# ---------------------------------------------------------------------------
TESTS_DIR = Path(__file__).parent
ARTIFACTS_DIR = TESTS_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)
DATA_FILE = TESTS_DIR / "flawed_outputs.json"
RESULTS_FILE = ARTIFACTS_DIR / "detection_results.json"

with open(DATA_FILE, encoding="utf-8") as f:
    _DATA = json.load(f)

FLAWED_OUTPUTS: List[Dict[str, Any]] = _DATA["flawed_outputs"]
EXPECTED_TOPIC: str = _DATA["topic"]
EXPECTED_NUM_CLASSES: int = _DATA["number_of_classes"]

# Module-level accumulator for the aggregate test
_detection_results: List[Dict[str, Any]] = []

# ---------------------------------------------------------------------------
# Parametrised test — one case per flawed output
# ---------------------------------------------------------------------------
_IDS = [item["id"] for item in FLAWED_OUTPUTS]


@pytest.mark.parametrize(
    "flawed",
    FLAWED_OUTPUTS,
    ids=_IDS,
)
@pytest.mark.asyncio
async def test_evaluator_detects_flaw(
    flawed: Dict[str, Any],
    evaluator_state_factory,
):
    """The evaluator must classify every flawed output as NEEDS_REFINEMENT."""

    state = evaluator_state_factory(
        content=flawed["content"],
        topic=EXPECTED_TOPIC,
        number_of_classes=EXPECTED_NUM_CLASSES,
    )

    result = await evaluate_outline(state)

    # --- unpack returned state update ---
    history = result.get("evaluation_history", [])
    assert (
        history
    ), f"[{flawed['id']}] evaluation_history is empty — evaluator may have crashed"
    evaluation: Any = history[-1]  # EvaluationResult

    score = evaluation.score
    verdict = evaluation.verdict
    breakdown = evaluation.score_breakdown

    # --- record for aggregate test ---
    record = {
        "id": flawed["id"],
        "category": flawed["category"],
        "targeted_dimensions": flawed["targeted_dimensions"],
        "flaw_description": flawed["flaw_description"],
        "verdict": verdict,
        "score": score,
        "score_breakdown": {
            "learning_objectives": breakdown.learning_objectives,
            "content_coverage": breakdown.content_coverage,
            "progression": breakdown.progression,
            "activities": breakdown.activities,
            "completeness": breakdown.completeness,
        },
        "reasoning": evaluation.reasoning,
        "suggestions": [
            {"dimension": s.dimension, "text": s.text} for s in evaluation.suggestions
        ],
    }
    _detection_results.append(record)

    # --- assertions ---
    assert verdict == "NEEDS_REFINEMENT", (
        f"[{flawed['id']}] Expected NEEDS_REFINEMENT but got {verdict} "
        f"(score={score:.2f})"
    )
    assert score < EvaluationConfig.APPROVAL_THRESHOLD, (
        f"[{flawed['id']}] Score {score:.2f} should be below "
        f"{EvaluationConfig.APPROVAL_THRESHOLD}"
    )

    # Verify the evaluator localised the error to the right dimension(s).
    # This is a softer secondary check — the verdict assertion above is primary.
    # 0.75 allows for some scoring leniency while still confirming the evaluator
    # penalised the targeted area more than unflawed dimensions.
    DIMENSION_LOW_THRESHOLD = 0.75
    for dim in flawed["targeted_dimensions"]:
        dim_score = getattr(breakdown, dim)
        if dim_score >= DIMENSION_LOW_THRESHOLD:
            logger.warning(
                f"[{flawed['id']}] Targeted dimension '{dim}' scored "
                f"{dim_score:.2f} — expected < {DIMENSION_LOW_THRESHOLD}"
            )
        assert dim_score < DIMENSION_LOW_THRESHOLD, (
            f"[{flawed['id']}] Targeted dimension '{dim}' scored "
            f"{dim_score:.2f} — expected < {DIMENSION_LOW_THRESHOLD} "
            f"for a deliberately flawed output"
        )

    logger.info(
        f"[{flawed['id']}] ✓ verdict={verdict}, score={score:.2f}, "
        f"targeted dims: {', '.join(f'{d}={getattr(breakdown, d):.2f}' for d in flawed['targeted_dimensions'])}"
    )


# ---------------------------------------------------------------------------
# Aggregate test — runs last, computes + exports metrics
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_z_aggregate_detection_rate():
    """Compute overall detection rate and export results JSON."""

    total = len(FLAWED_OUTPUTS)
    assert (
        _detection_results
    ), "No detection results collected — parametrised tests may have been skipped"

    detected = sum(1 for r in _detection_results if r["verdict"] == "NEEDS_REFINEMENT")
    detection_rate = detected / total

    # Export full results
    export = {
        "model": "gpt-4o-mini",
        "total_cases": total,
        "detected": detected,
        "detection_rate": detection_rate,
        "cases": _detection_results,
    }
    RESULTS_FILE.write_text(
        json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Pretty-print summary table
    print("\n")
    print("=" * 72)
    print("  DETECTION RATE RESULTS")
    print("=" * 72)
    print(f"  Model:          {export['model']}")
    print(f"  Total cases:    {total}")
    print(f"  Detected:       {detected}")
    print(f"  Detection rate: {detection_rate:.0%}")
    print("-" * 72)
    print(f"  {'ID':<30} {'Verdict':<20} {'Score':>6}")
    print("-" * 72)
    for r in _detection_results:
        mark = "✓" if r["verdict"] == "NEEDS_REFINEMENT" else "✗"
        print(f"  {mark} {r['id']:<28} {r['verdict']:<20} {r['score']:>5.2f}")
    print("=" * 72)
    print()

    assert detection_rate == 1.0, (
        f"Detection rate {detection_rate:.0%} is below the 100% target. "
        f"Missed: {[r['id'] for r in _detection_results if r['verdict'] != 'NEEDS_REFINEMENT']}"
    )
