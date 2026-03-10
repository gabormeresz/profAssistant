"""
Phase 2 — External judge scoring, statistical analysis, and assertions.

Loads ``drafts.json`` produced by Phase 1 and:

1. Scores each **draft** (zero-shot output) with an independent GPT-5.2
   judge using the identical pedagogical rubric from the production evaluator.
2. Computes zero-shot quality statistics (overall and per-dimension).
3. Computes meta-evaluation statistics (internal gpt-4o-mini evaluator
   vs GPT-5.2 judge).
4. Runs quality assertions.

Results are persisted to ``judge_results.json`` and ``analysis_summary.json``.
"""

import json
import logging
import math
import time
from typing import Any, Dict, List, Optional

import pytest

from conftest import (
    ANALYSIS_FILE,
    DRAFTS_FILE,
    JUDGE_MODEL,
    JUDGE_RESULTS_FILE,
    build_judge_messages,
    get_judge_model,
    serialize_course_outline_to_text,
)

pytestmark = pytest.mark.llm
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Statistical helpers (pure Python — no numpy dependency)
# ---------------------------------------------------------------------------

DIMENSIONS = [
    "learning_objectives",
    "content_coverage",
    "progression",
    "activities",
    "completeness",
]


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _median(xs: List[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def _std(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _mae(xs: List[float], ys: List[float]) -> float:
    """Mean absolute error."""
    if not xs:
        return 0.0
    return sum(abs(x - y) for x, y in zip(xs, ys)) / len(xs)


# ---------------------------------------------------------------------------
# Serialisation helper
# ---------------------------------------------------------------------------


def _eval_result_to_dict(ev) -> dict:
    """Serialise a judge ``EvaluationResult`` to a plain dict."""
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
# Phase 2 test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_judge_and_analyse(real_api_key: str):
    """
    Score every zero-shot draft with the external GPT-5.2 judge,
    compute statistics, and run quality assertions.
    """
    # ── load Phase 1 artifact ──
    if not DRAFTS_FILE.exists():
        pytest.skip(
            f"Phase 1 artifact not found at {DRAFTS_FILE}. "
            "Run test_01_generate_drafts.py first."
        )

    with open(DRAFTS_FILE, encoding="utf-8") as f:
        drafts_data = json.load(f)

    drafts: List[Dict[str, Any]] = drafts_data["drafts"]
    assert drafts, "drafts.json contains no drafts"

    judge = get_judge_model(real_api_key)
    judge_results: List[Dict[str, Any]] = []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 1: Score each draft with GPT-5.2
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    for idx, draft in enumerate(drafts, start=1):
        prompt_id = draft["prompt_id"]
        topic = draft["topic"]
        num_classes = draft["number_of_classes"]
        language = draft["language"]

        logger.info("━━━ [%d/%d] Judging: %s ━━━", idx, len(drafts), prompt_id)

        draft_content = draft.get("draft_content")
        judge_result_dict = None

        if draft_content:
            messages = build_judge_messages(
                draft_content,
                topic=topic,
                number_of_classes=num_classes,
                language=language,
            )
            t0 = time.perf_counter()
            judge_eval = await judge.ainvoke(messages)
            judge_time = time.perf_counter() - t0
            judge_result_dict = _eval_result_to_dict(judge_eval)
            judge_result_dict["judge_latency_sec"] = round(judge_time, 2)
            logger.info(
                "  score=%.2f  (%s)  [%.1fs]",
                judge_eval.score,
                judge_eval.verdict,
                judge_time,
            )
        else:
            logger.warning("  Draft content missing for %s — skipping", prompt_id)

        internal_first_score = draft.get("generation_metadata", {}).get(
            "internal_first_score"
        )

        record = {
            "prompt_id": prompt_id,
            "discipline": draft["discipline"],
            "topic": topic,
            "draft_judge": judge_result_dict,
            "internal_first_score": internal_first_score,
        }
        judge_results.append(record)

    # Persist judge results
    judge_export = {
        "judge_model": JUDGE_MODEL,
        "generation_model": drafts_data.get("model", "unknown"),
        "total_drafts": len(drafts),
        "scored": len(judge_results),
        "results": judge_results,
    }
    JUDGE_RESULTS_FILE.write_text(
        json.dumps(judge_export, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 2: Compute zero-shot quality statistics
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    draft_scores: List[float] = []
    per_dim_scores: Dict[str, List[float]] = {d: [] for d in DIMENSIONS}
    prompt_details: List[Dict[str, Any]] = []

    for r in judge_results:
        dj = r.get("draft_judge")
        if not dj:
            continue

        score = dj["score"]
        draft_scores.append(score)
        for d in DIMENSIONS:
            dim_val = dj["score_breakdown"].get(d)
            if dim_val is not None:
                per_dim_scores[d].append(dim_val)

        prompt_details.append(
            {
                "prompt_id": r["prompt_id"],
                "discipline": r["discipline"],
                "judge_score": score,
                "judge_verdict": dj["verdict"],
                "internal_first_score": r.get("internal_first_score"),
                "judge_breakdown": dj["score_breakdown"],
            }
        )

    zero_shot_stats = {
        "n": len(draft_scores),
        "mean": round(_mean(draft_scores), 4) if draft_scores else None,
        "median": round(_median(draft_scores), 4) if draft_scores else None,
        "std": round(_std(draft_scores), 4) if draft_scores else None,
        "min": round(min(draft_scores), 4) if draft_scores else None,
        "max": round(max(draft_scores), 4) if draft_scores else None,
        "pass_count": sum(1 for s in draft_scores if s >= 0.80),
        "pass_rate": (
            round(sum(1 for s in draft_scores if s >= 0.80) / len(draft_scores), 4)
            if draft_scores
            else None
        ),
        "per_dimension_mean": {
            d: round(_mean(per_dim_scores[d]), 4) if per_dim_scores[d] else None
            for d in DIMENSIONS
        },
        "per_dimension_min": {
            d: round(min(per_dim_scores[d]), 4) if per_dim_scores[d] else None
            for d in DIMENSIONS
        },
    }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 3: Meta-evaluation (internal evaluator vs judge)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Compare the internal gpt-4o-mini evaluator's first score against
    # the GPT-5.2 judge's score — both assessing the same draft.

    internal_scores: List[float] = []
    judge_scores_paired: List[float] = []
    per_dim_internal: Dict[str, List[float]] = {d: [] for d in DIMENSIONS}
    per_dim_judge: Dict[str, List[float]] = {d: [] for d in DIMENSIONS}

    for draft_rec, judge_rec in zip(drafts, judge_results):
        jdg = judge_rec.get("draft_judge")
        if not jdg:
            continue

        # Internal evaluator's first assessment
        first_eval = draft_rec.get("internal_first_eval")
        internal_first = draft_rec.get("generation_metadata", {}).get(
            "internal_first_score"
        )
        if internal_first is None:
            continue

        internal_scores.append(internal_first)
        judge_scores_paired.append(jdg["score"])

        # Per-dimension comparison
        if first_eval and first_eval.get("score_breakdown"):
            for d in DIMENSIONS:
                int_d = first_eval["score_breakdown"].get(d)
                jdg_d = jdg["score_breakdown"].get(d)
                if int_d is not None and jdg_d is not None:
                    per_dim_internal[d].append(int_d)
                    per_dim_judge[d].append(jdg_d)

    overall_mae = _mae(internal_scores, judge_scores_paired)
    bias = (
        round(_mean(internal_scores) - _mean(judge_scores_paired), 4)
        if internal_scores
        else None
    )

    per_dim_mae_vals = {}
    for d in DIMENSIONS:
        per_dim_mae_vals[d] = round(_mae(per_dim_internal[d], per_dim_judge[d]), 4)

    meta_eval_stats = {
        "n": len(internal_scores),
        "mae": round(overall_mae, 4),
        "bias": bias,
        "internal_mean": (
            round(_mean(internal_scores), 4) if internal_scores else None
        ),
        "judge_mean": (
            round(_mean(judge_scores_paired), 4) if judge_scores_paired else None
        ),
        "per_dimension_mae": per_dim_mae_vals,
    }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Export analysis summary
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    summary = {
        "generation_model": drafts_data.get("model"),
        "judge_model": JUDGE_MODEL,
        "approval_threshold": drafts_data.get("approval_threshold"),
        "zero_shot_quality": zero_shot_stats,
        "meta_evaluation": meta_eval_stats,
        "prompt_details": prompt_details,
    }

    ANALYSIS_FILE.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Pretty-print report
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    print("\n")
    print("=" * 90)
    print("  PHASE 2 — ZERO-SHOT QUALITY (GPT-5.2 JUDGE)")
    print("=" * 90)
    print(f"  Judge model:      {JUDGE_MODEL}")
    print(f"  Generation model: {drafts_data.get('model', '?')}")
    print(
        f"  Threshold:        {drafts_data.get('approval_threshold', '?')} (production)"
    )
    print(f"  Drafts scored:    {len(judge_results)} / {len(drafts)}")

    # Section A: Per-prompt scores
    print()
    print("-" * 90)
    print(f"  {'ID':<30} {'Judge':>7} {'Verdict':<20} {'Internal':>9}")
    print("-" * 90)
    for d in prompt_details:
        js = f"{d['judge_score']:.2f}"
        int_s = (
            f"{d['internal_first_score']:.2f}"
            if d["internal_first_score"] is not None
            else "N/A"
        )
        print(f"  {d['prompt_id']:<30} {js:>7} {d['judge_verdict']:<20} {int_s:>9}")
    print("-" * 90)

    # Section B: Zero-shot quality summary
    zs = zero_shot_stats
    print(f"\n  ┌─ A) ZERO-SHOT QUALITY SUMMARY")
    print(f"  │  N = {zs['n']}")
    if zs["mean"] is not None:
        print(f"  │  Mean   = {zs['mean']:.4f}")
        print(f"  │  Median = {zs['median']:.4f}")
        print(f"  │  Std    = {zs['std']:.4f}")
        print(f"  │  Min    = {zs['min']:.4f}  |  Max = {zs['max']:.4f}")
        print(
            f"  │  Pass (≥0.80): {zs['pass_count']}/{zs['n']} "
            f"({zs['pass_rate']:.0%})"
        )
    print("  │")
    print("  │  Per-dimension mean scores:")
    for d in DIMENSIONS:
        v = zs["per_dimension_mean"][d]
        m = zs["per_dimension_min"][d]
        print(
            f"  │    {d:<25} mean={v:.3f}  min={m:.3f}"
            if v is not None
            else f"  │    {d:<25} N/A"
        )
    print("  └" + "─" * 55)

    # Section C: Meta-evaluation
    me = meta_eval_stats
    print(f"\n  ┌─ B) META-EVALUATION (Internal gpt-4o-mini vs GPT-5.2 judge)")
    print(f"  │  N = {me['n']}")
    print(f"  │  MAE  = {me['mae']:.4f}")
    if me["bias"] is not None:
        direction = "internal lenient" if me["bias"] > 0 else "internal strict"
        print(f"  │  Bias = {me['bias']:+.4f} ({direction})")
    if me["internal_mean"] is not None:
        print(f"  │  Internal mean = {me['internal_mean']:.4f}")
        print(f"  │  Judge mean    = {me['judge_mean']:.4f}")
    print("  │")
    print("  │  Per-dimension MAE:")
    for d in DIMENSIONS:
        print(f"  │    {d:<25} {me['per_dimension_mae'][d]:.4f}")
    print("  └" + "─" * 55)
    print("=" * 90)
    print()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Assertions
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # 1) Mean draft score ≥ 0.80 (production threshold)
    assert zs["mean"] is not None, "No draft scores to analyse"
    assert zs["mean"] >= 0.80, (
        f"Mean draft score {zs['mean']:.4f} is below 0.80 — "
        f"zero-shot quality does not meet the production threshold"
    )

    # 2) ≥ 80% of prompts pass the 0.80 threshold
    assert zs["pass_rate"] is not None
    assert zs["pass_rate"] >= 0.80, (
        f"Only {zs['pass_rate']:.0%} of prompts scored ≥ 0.80 — "
        f"expected ≥ 80% pass rate"
    )

    # 3) No catastrophic failures: min score ≥ 0.70
    assert zs["min"] is not None
    assert zs["min"] >= 0.70, (
        f"Minimum draft score {zs['min']:.4f} is below 0.70 — "
        f"at least one prompt produced catastrophically low quality"
    )

    # 4) Per-dimension means ≥ 0.75 (no weak axis)
    for d in DIMENSIONS:
        dim_mean = zs["per_dimension_mean"][d]
        assert dim_mean is not None, f"No scores for dimension {d}"
        assert dim_mean >= 0.75, (
            f"Per-dimension mean for '{d}' is {dim_mean:.4f} — "
            f"expected ≥ 0.75 (no weak rubric axis)"
        )

    # 5) Meta-evaluation: MAE < 0.15
    assert me["mae"] < 0.15, (
        f"MAE {me['mae']:.4f} exceeds 0.15 — internal evaluator diverges "
        f"too much from the GPT-5.2 judge"
    )

    logger.info(
        "Phase 2 complete — mean=%.4f, pass_rate=%.0f%%, min=%.4f, MAE=%.4f",
        zs["mean"] or 0,
        (zs["pass_rate"] or 0) * 100,
        zs["min"] or 0,
        me["mae"],
    )
