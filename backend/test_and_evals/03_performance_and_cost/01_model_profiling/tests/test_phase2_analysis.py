"""
Phase 2 — Benchmark analysis and reporting.

Discovers per-model benchmark files (``artifacts/benchmark_raw_<model>.json``)
produced by Phase 1, merges them, computes aggregate statistics, FinOps
projections, and generates structured analysis JSON plus a human-readable
markdown report.

You can also restrict analysis to specific models via ``--model``.

Usage (analyse all collected models):
    cd backend
    python -m pytest test_and_evals/03_performance_and_cost/01_model_profiling/tests/test_phase2_analysis.py \
        -v --tb=short -s 2>&1 | tee test_and_evals/03_performance_and_cost/01_model_profiling/tests/logs/phase2_$(date +%F).log

Usage (analyse a single model):
    python -m pytest ... --model gpt-4o-mini
"""

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

from conftest import (
    ANALYSIS_FILE,
    BENCHMARK_RAW_FILE,
    MODEL_LIST,
    PRICING_FILE,
    REPORT_FILE,
    benchmark_file_for_model,
    discover_model_benchmark_files,
)

# ---------------------------------------------------------------------------
# Prompt categories
# ---------------------------------------------------------------------------
# Prompts that trigger MCP tool calls (web-search / Wikipedia).  All other
# prompt_ids are considered "plain" (no external tool usage).
TOOL_PROMPT_IDS: set[str] = {"co_simple_ws", "co_simple_wiki"}


def _split_results(
    results: List[Dict],
) -> tuple[List[Dict], List[Dict]]:
    """Split results into (plain_runs, tool_runs) based on prompt id."""
    plain = [r for r in results if r["prompt_id"] not in TOOL_PROMPT_IDS]
    tool = [r for r in results if r["prompt_id"] in TOOL_PROMPT_IDS]
    return plain, tool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _safe_mean(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _safe_median(values: List[float]) -> float:
    return statistics.median(values) if values else 0.0


def _safe_p95(values: List[float]) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    idx = int(len(sorted_v) * 0.95)
    return sorted_v[min(idx, len(sorted_v) - 1)]


def _safe_stdev(values: List[float]) -> float:
    return statistics.stdev(values) if len(values) >= 2 else 0.0


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def compute_per_model_stats(
    results: List[Dict], pricing: Dict
) -> Dict[str, Dict[str, Any]]:
    """Compute per-model aggregate statistics."""
    by_model: Dict[str, List[Dict]] = defaultdict(list)
    for r in results:
        by_model[r["model"]].append(r)

    stats = {}
    for model, runs in by_model.items():
        durations = [r["total_duration_s"] for r in runs]
        ttfts = [r["ttft_s"] for r in runs if r["ttft_s"] is not None]
        prompt_tokens = [r["token_usage"]["prompt_tokens"] for r in runs]
        completion_tokens = [r["token_usage"]["completion_tokens"] for r in runs]
        total_tokens = [r["token_usage"]["total_tokens"] for r in runs]
        cached_tokens = [r["token_usage"].get("cached_tokens", 0) for r in runs]
        reasoning_tokens = [r["token_usage"].get("reasoning_tokens", 0) for r in runs]

        # Tool calls — separate successful (duration_s present) from failed (null)
        all_tool_calls = []
        successful_tool_calls = 0
        failed_tool_calls = 0
        tool_counts_by_name: Dict[str, int] = defaultdict(int)
        tool_success_by_name: Dict[str, int] = defaultdict(int)
        tool_fail_by_name: Dict[str, int] = defaultdict(int)
        tool_durations_by_name: Dict[str, List[float]] = defaultdict(list)
        for r in runs:
            for tc in r.get("tool_calls", []):
                all_tool_calls.append(tc)
                tool_counts_by_name[tc["tool_name"]] += 1
                if tc.get("duration_s") is not None:
                    successful_tool_calls += 1
                    tool_success_by_name[tc["tool_name"]] += 1
                    tool_durations_by_name[tc["tool_name"]].append(tc["duration_s"])
                else:
                    failed_tool_calls += 1
                    tool_fail_by_name[tc["tool_name"]] += 1

        tools_per_gen = len(all_tool_calls) / len(runs) if runs else 0

        # Refinement
        refine_counts = [r["refinement"]["count"] for r in runs]
        first_pass_pct = (
            sum(
                1
                for r in runs
                if r["refinement"]["exit_reason"] == "first_pass_approved"
            )
            / len(runs)
            * 100
            if runs
            else 0
        )

        # FinOps
        model_pricing = pricing.get(model, {})
        input_price = model_pricing.get("input_per_1m", 0)
        output_price = model_pricing.get("output_per_1m", 0)

        mean_prompt = _safe_mean(prompt_tokens)
        mean_completion = _safe_mean(completion_tokens)
        cost_per_gen = (mean_prompt / 1_000_000) * input_price + (
            mean_completion / 1_000_000
        ) * output_price
        cost_per_100 = cost_per_gen * 100

        stats[model] = {
            "n_runs": len(runs),
            "success_rate": sum(1 for r in runs if r["success"]) / len(runs) * 100,
            "latency": {
                "mean_s": _safe_mean(durations),
                "median_s": _safe_median(durations),
                "p95_s": _safe_p95(durations),
                "stdev_s": _safe_stdev(durations),
            },
            "ttft": {
                "mean_s": _safe_mean(ttfts),
                "median_s": _safe_median(ttfts),
            },
            "tokens": {
                "mean_prompt": _safe_mean(prompt_tokens),
                "mean_completion": _safe_mean(completion_tokens),
                "mean_total": _safe_mean(total_tokens),
                "total_prompt": sum(prompt_tokens),
                "total_completion": sum(completion_tokens),
                "mean_cached": _safe_mean(cached_tokens),
                "total_cached": sum(cached_tokens),
                "cached_ratio": (
                    round(sum(cached_tokens) / sum(prompt_tokens), 3)
                    if sum(prompt_tokens) > 0
                    else 0.0
                ),
                "mean_reasoning": _safe_mean(reasoning_tokens),
                "total_reasoning": sum(reasoning_tokens),
                "reasoning_ratio": (
                    round(sum(reasoning_tokens) / sum(completion_tokens), 3)
                    if sum(completion_tokens) > 0
                    else 0.0
                ),
            },
            "tools": {
                "mean_per_generation": round(tools_per_gen, 2),
                "total_calls": len(all_tool_calls),
                "successful_calls": successful_tool_calls,
                "failed_calls": failed_tool_calls,
                "by_name": {
                    name: {
                        "count": count,
                        "successful": tool_success_by_name.get(name, 0),
                        "failed": tool_fail_by_name.get(name, 0),
                        "mean_duration_s": _safe_mean(
                            tool_durations_by_name.get(name, [])
                        ),
                    }
                    for name, count in tool_counts_by_name.items()
                },
            },
            "refinement": {
                "mean_iterations": _safe_mean(refine_counts),
                "max_iterations": max(refine_counts) if refine_counts else 0,
                "first_pass_approved_pct": round(first_pass_pct, 1),
                "exit_reasons": _count_exit_reasons(runs),
            },
            "finops": {
                "cost_per_generation_usd": round(cost_per_gen, 6),
                "cost_per_100_docs_usd": round(cost_per_100, 4),
                "input_price_per_1m": input_price,
                "output_price_per_1m": output_price,
            },
        }

    return stats


def compute_per_model_per_variant(
    results: List[Dict], pricing: Dict
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Compute per-model, per-variant (simple/complex) statistics."""
    grouped: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        grouped[r["model"]][r["variant"]].append(r)

    out = {}
    for model, variants in grouped.items():
        out[model] = {}
        for variant, runs in variants.items():
            durations = [r["total_duration_s"] for r in runs]
            total_tokens = [r["token_usage"]["total_tokens"] for r in runs]
            refine_counts = [r["refinement"]["count"] for r in runs]
            tool_calls_count = [len(r.get("tool_calls", [])) for r in runs]

            out[model][variant] = {
                "n_runs": len(runs),
                "mean_latency_s": _safe_mean(durations),
                "mean_total_tokens": _safe_mean(total_tokens),
                "mean_refinements": _safe_mean(refine_counts),
                "mean_tool_calls": _safe_mean(tool_calls_count),
            }

    return out


def compute_per_module_stats(
    results: List[Dict], pricing: Dict
) -> Dict[str, Dict[str, Any]]:
    """Compute per-module aggregate statistics (across all models)."""
    by_module: Dict[str, List[Dict]] = defaultdict(list)
    for r in results:
        by_module[r["module"]].append(r)

    out = {}
    for module, runs in by_module.items():
        durations = [r["total_duration_s"] for r in runs]
        total_tokens = [r["token_usage"]["total_tokens"] for r in runs]
        costs = []
        for r in runs:
            mp = pricing.get(r["model"], {})
            inp = mp.get("input_per_1m", 0)
            outp = mp.get("output_per_1m", 0)
            tu = r["token_usage"]
            cost = (tu["prompt_tokens"] / 1_000_000) * inp + (
                tu["completion_tokens"] / 1_000_000
            ) * outp
            costs.append(cost)

        out[module] = {
            "n_runs": len(runs),
            "mean_latency_s": _safe_mean(durations),
            "mean_total_tokens": _safe_mean(total_tokens),
            "mean_cost_per_generation_usd": _safe_mean(costs),
            "success_rate": sum(1 for r in runs if r["success"]) / len(runs) * 100,
        }

    return out


def compute_cross_model_comparison(
    per_model: Dict[str, Dict],
) -> Dict[str, Any]:
    """Compute ratios relative to the cheapest model."""
    if not per_model:
        return {}

    # Use cheapest model as baseline
    cheapest = min(
        per_model.keys(),
        key=lambda m: per_model[m]["finops"]["cost_per_generation_usd"],
    )
    baseline_cost = per_model[cheapest]["finops"]["cost_per_generation_usd"]
    baseline_latency = per_model[cheapest]["latency"]["mean_s"]

    comparison = {}
    for model, s in per_model.items():
        comparison[model] = {
            "cost_ratio_vs_cheapest": (
                round(s["finops"]["cost_per_generation_usd"] / baseline_cost, 2)
                if baseline_cost > 0
                else 0
            ),
            "latency_ratio_vs_cheapest": (
                round(s["latency"]["mean_s"] / baseline_latency, 2)
                if baseline_latency > 0
                else 0
            ),
            "mean_refinements": s["refinement"]["mean_iterations"],
            "first_pass_pct": s["refinement"]["first_pass_approved_pct"],
            "mean_tool_calls": s["tools"]["mean_per_generation"],
        }

    comparison["_baseline_model"] = cheapest
    return comparison


# The plain baseline prompt that matches the tool-augmented prompts
# (same module=course_outline, variant=simple, discipline).
TOOL_PLAIN_BASELINE_ID: str = "co_simple"


def compute_tool_vs_plain_comparison(
    results: List[Dict],
    per_model_tool: Dict[str, Dict],
    pricing: Dict,
) -> Dict[str, Dict[str, Any]]:
    """Compare tool-augmented vs matching plain baseline (co_simple).

    Uses *only* ``co_simple`` runs as the plain baseline so latency /
    token / cost deltas reflect genuine tool overhead rather than
    module-mix differences.
    """
    # Filter raw results to co_simple runs, group by model
    baseline_by_model: Dict[str, List[Dict]] = defaultdict(list)
    for r in results:
        if r["prompt_id"] == TOOL_PLAIN_BASELINE_ID:
            baseline_by_model[r["model"]].append(r)

    comparison = {}
    for model in per_model_tool:
        baseline_runs = baseline_by_model.get(model, [])
        if not baseline_runs:
            continue
        t = per_model_tool[model]

        # Plain baseline stats from co_simple runs
        p_lats = [r["total_duration_s"] for r in baseline_runs]
        p_toks = [r["token_usage"]["total_tokens"] for r in baseline_runs]
        p_prompt_toks = [r["token_usage"]["prompt_tokens"] for r in baseline_runs]
        p_compl_toks = [r["token_usage"]["completion_tokens"] for r in baseline_runs]

        # Prompt caching ratios
        p_cached = [r["token_usage"].get("cached_tokens", 0) for r in baseline_runs]
        p_cache_pcts = [
            (c / p * 100) if p > 0 else 0.0 for c, p in zip(p_cached, p_prompt_toks)
        ]

        p_lat = _safe_mean(p_lats)
        p_tok = _safe_mean(p_toks)
        t_lat = t["latency"]["mean_s"]
        t_tok = t["tokens"]["mean_total"]

        # Cost for plain baseline
        model_pricing = pricing.get(model, {})
        input_price = model_pricing.get("input_per_1m", 0)
        output_price = model_pricing.get("output_per_1m", 0)
        p_cost = (_safe_mean(p_prompt_toks) / 1_000_000) * input_price + (
            _safe_mean(p_compl_toks) / 1_000_000
        ) * output_price
        t_cost = t["finops"]["cost_per_generation_usd"]

        # Tool-run cache percentages from per_model_tool stats
        tool_cache_pct = t["tokens"].get("cached_ratio", 0.0) * 100

        comparison[model] = {
            "plain_baseline_prompt": TOOL_PLAIN_BASELINE_ID,
            "plain_runs": len(baseline_runs),
            "tool_runs": t["n_runs"],
            "plain_mean_latency_s": round(p_lat, 1),
            "tool_mean_latency_s": round(t_lat, 1),
            "latency_ratio": round(t_lat / p_lat, 2) if p_lat > 0 else 0,
            "plain_mean_tokens": round(p_tok),
            "tool_mean_tokens": round(t_tok),
            "token_ratio": round(t_tok / p_tok, 2) if p_tok > 0 else 0,
            "plain_cost_usd": round(p_cost, 6),
            "tool_cost_usd": round(t_cost, 6),
            "cost_ratio": round(t_cost / p_cost, 2) if p_cost > 0 else 0,
            "plain_cache_pct": round(_safe_mean(p_cache_pcts), 1),
            "tool_cache_pct": round(tool_cache_pct, 1),
            "tool_total_calls": t["tools"]["total_calls"],
            "tool_successful_calls": t["tools"]["successful_calls"],
            "tool_failed_calls": t["tools"]["failed_calls"],
        }

    return comparison


def _count_exit_reasons(runs: List[Dict]) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for r in runs:
        reason = r.get("refinement", {}).get("exit_reason", "unknown")
        counts[reason] += 1
    return dict(counts)


# ---------------------------------------------------------------------------
# Markdown report generator
# ---------------------------------------------------------------------------


def generate_report(
    per_model: Dict[str, Dict],
    per_model_plain: Dict[str, Dict],
    per_model_tool: Dict[str, Dict],
    per_variant: Dict[str, Dict],
    per_module: Dict[str, Dict],
    cross_model_plain: Dict[str, Any],
    tool_vs_plain: Dict[str, Dict],
    results: List[Dict],
) -> str:
    """Generate a human-readable markdown report.

    Metrics affected by external tool latency / token overhead are reported
    separately for *plain* (no-tool) and *tool-augmented* prompts.  Metrics
    that are comparable across both categories (refinement, success rate) are
    shown in unified tables.
    """
    plain_results, tool_results = _split_results(results)

    lines = [
        "# Section 3.1 — Model Performance Profiling & Cost Analysis Report",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Total benchmark runs: {len(results)}  "
        f"(plain: {len(plain_results)}, tool-augmented: {len(tool_results)})",
        f"Models tested: {', '.join(per_model.keys())}",
        f"Tool-augmented prompts: {', '.join(sorted(TOOL_PROMPT_IDS))}",
        "",
    ]

    # === SECTION 1 — Overall success & refinement (unified) ================
    lines.append("## 1. Per-Model Overview (all prompts)")
    lines.append("")
    lines.append(
        "| Model | Runs | Success% | Mean Refine Iter. | Max Iter. | First-Pass% | Exit Reasons |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for model in MODEL_LIST:
        if model not in per_model:
            continue
        s = per_model[model]
        reasons = ", ".join(
            f"{k}: {v}" for k, v in s["refinement"]["exit_reasons"].items()
        )
        lines.append(
            f"| {model} | {s['n_runs']} | {s['success_rate']:.0f}% "
            f"| {s['refinement']['mean_iterations']:.1f} "
            f"| {s['refinement']['max_iterations']} "
            f"| {s['refinement']['first_pass_approved_pct']:.0f}% "
            f"| {reasons} |"
        )
    lines.append("")

    # === SECTION 1b — Token consumption comparison ==========================
    lines.append("## 1b. Token Consumption Comparison (all prompts)")
    lines.append("")
    lines.append(
        "| Model | Mean Prompt | Mean Completion | Mean Total "
        "| Mean Cached | Cached % "
        "| Mean Reasoning | Reasoning/Compl. % |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for model in MODEL_LIST:
        if model not in per_model:
            continue
        t = per_model[model]["tokens"]
        lines.append(
            f"| {model} "
            f"| {t['mean_prompt']:,.0f} "
            f"| {t['mean_completion']:,.0f} "
            f"| {t['mean_total']:,.0f} "
            f"| {t['mean_cached']:,.0f} "
            f"| {t['cached_ratio'] * 100:.1f}% "
            f"| {t['mean_reasoning']:,.0f} "
            f"| {t['reasoning_ratio'] * 100:.1f}% |"
        )
    lines.append("")

    # === SECTION 2 — Plain-prompt latency & tokens =========================
    lines.append("## 2. Plain Generation — Latency & Tokens")
    lines.append("")
    lines.append(
        "> Excludes tool-augmented prompts "
        f"({', '.join(sorted(TOOL_PROMPT_IDS))}) "
        "so that external-call overhead does not skew the numbers."
    )
    lines.append("")
    lines.append(
        "| Model | Runs | Mean Lat. (s) | Median Lat. (s) | P95 Lat. (s) | Mean TTFT (s) "
        "| Mean Prompt Tok. | Mean Compl. Tok. | Mean Total Tok. | $/gen | $/100 docs |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for model in MODEL_LIST:
        if model not in per_model_plain:
            continue
        s = per_model_plain[model]
        lines.append(
            f"| {model} | {s['n_runs']} "
            f"| {s['latency']['mean_s']:.1f} "
            f"| {s['latency']['median_s']:.1f} "
            f"| {s['latency']['p95_s']:.1f} "
            f"| {s['ttft']['mean_s']:.2f} "
            f"| {s['tokens']['mean_prompt']:,.0f} "
            f"| {s['tokens']['mean_completion']:,.0f} "
            f"| {s['tokens']['mean_total']:,.0f} "
            f"| ${s['finops']['cost_per_generation_usd']:.4f} "
            f"| ${s['finops']['cost_per_100_docs_usd']:.2f} |"
        )
    lines.append("")

    # === SECTION 3 — Tool vs Plain comparison ==============================
    lines.append("## 3. Tool-Augmented vs Plain Generation Comparison")
    lines.append("")
    lines.append(
        "> Compares tool-augmented prompts "
        f"({', '.join(sorted(TOOL_PROMPT_IDS))}) "
        f"against the matching plain baseline ({TOOL_PLAIN_BASELINE_ID}) "
        "— same module, variant, and discipline but without tool access. "
        "Ratios >1× indicate tool overhead."
    )
    lines.append("")
    lines.append(
        "| Model "
        "| Plain Lat. (s) | Tool Lat. (s) | Lat. Δ "
        "| Plain Tok. | Tool Tok. | Tok. Δ "
        "| Plain $/gen | Tool $/gen | Cost Δ "
        "| Plain Cache% | Tool Cache% "
        "| Calls (ok/fail) | Tool Breakdown |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for model in MODEL_LIST:
        if model not in tool_vs_plain or model not in per_model_tool:
            continue
        c = tool_vs_plain[model]
        s = per_model_tool[model]
        # Build tool breakdown string
        breakdown_parts = []
        for name, info in s["tools"]["by_name"].items():
            parts = f"{name}: {info['successful']}ok"
            if info["failed"] > 0:
                parts += f"/{info['failed']}fail"
            breakdown_parts.append(parts)
        breakdown = ", ".join(breakdown_parts) if breakdown_parts else "—"
        lines.append(
            f"| {model} "
            f"| {c['plain_mean_latency_s']:.1f} "
            f"| {c['tool_mean_latency_s']:.1f} "
            f"| {c['latency_ratio']:.2f}× "
            f"| {c['plain_mean_tokens']:,} "
            f"| {c['tool_mean_tokens']:,} "
            f"| {c['token_ratio']:.2f}× "
            f"| ${c['plain_cost_usd']:.4f} "
            f"| ${c['tool_cost_usd']:.4f} "
            f"| {c['cost_ratio']:.2f}× "
            f"| {c['plain_cache_pct']:.0f}% "
            f"| {c['tool_cache_pct']:.0f}% "
            f"| {c['tool_successful_calls']}ok/{c['tool_failed_calls']}fail "
            f"| {breakdown} |"
        )
    lines.append("")
    lines.append(
        "> **Reliability note.** Token and cost deltas are structurally reliable "
        "— tool-augmented runs deterministically ingest retrieved context, "
        "producing a consistent 1.5×–2.7× token overhead. "
        "Latency deltas are **not** reliable for two reasons: "
        "(1) the plain baseline is a single run (n=1) per model, so "
        "run-to-run variance dominates; "
        "(2) **prompt caching is a confounding variable** — the plain "
        "baseline (`co_simple`) always ran first with 0% cached prompt "
        "tokens, while subsequent tool runs benefited from 21–75% prompt "
        "caching on the shared system-prompt prefix, reducing their TTFT "
        "(e.g. gpt-5-mini: 18.6s → 2.4s). For fast non-reasoning models, "
        "this caching advantage can outweigh tool-call overhead, producing "
        "the sub-1× latency ratios."
    )
    lines.append("")

    # === SECTION 4 — Simple vs Complex (plain only) ========================
    lines.append("## 4. Simple vs Complex Variant Comparison (plain prompts)")
    lines.append("")
    lines.append("| Model | Variant | Runs | Mean Lat. (s) | Mean Tokens |")
    lines.append("|---|---|---|---|---|")
    for model in MODEL_LIST:
        if model not in per_variant:
            continue
        for variant in ("simple", "complex"):
            v = per_variant[model].get(variant, {})
            if not v:
                continue
            lines.append(
                f"| {model} | {variant} "
                f"| {v.get('n_runs', 0)} "
                f"| {v.get('mean_latency_s', 0):.1f} "
                f"| {v.get('mean_total_tokens', 0):,.0f} |"
            )
    lines.append("")

    # === SECTION 5 — Per-Module (plain only) ===============================
    lines.append("## 5. Per-Module Summary (plain prompts, across all models)")
    lines.append("")
    lines.append("| Module | Runs | Mean Lat. (s) | Mean Tokens | $/gen |")
    lines.append("|---|---|---|---|---|")
    for module, ms in per_module.items():
        lines.append(
            f"| {module} | {ms['n_runs']} "
            f"| {ms['mean_latency_s']:.1f} "
            f"| {ms['mean_total_tokens']:,.0f} "
            f"| ${ms['mean_cost_per_generation_usd']:.4f} |"
        )
    lines.append("")

    # === SECTION 6 — Cross-Model Comparison (plain) ========================
    baseline = cross_model_plain.get("_baseline_model", "?")
    lines.append(
        f"## 6. Cross-Model Comparison — Plain Generation (baseline: {baseline})"
    )
    lines.append("")
    lines.append("| Model | Cost Ratio | Latency Ratio | First-Pass% |")
    lines.append("|---|---|---|---|")
    for model in MODEL_LIST:
        if model not in cross_model_plain or model.startswith("_"):
            continue
        c = cross_model_plain[model]
        lines.append(
            f"| {model} "
            f"| {c['cost_ratio_vs_cheapest']:.1f}× "
            f"| {c['latency_ratio_vs_cheapest']:.1f}× "
            f"| {c['first_pass_pct']:.0f}% |"
        )
    lines.append("")

    # === SECTION 7 — Individual Run Log ====================================
    lines.append("## 7. Individual Run Log")
    lines.append("")
    lines.append(
        "| # | Model | Prompt | Category | Module | Status | Duration (s) | TTFT (s) | Tokens | Refine | Tools (ok/fail) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(results, 1):
        status = "OK" if r["success"] else "FAIL"
        ttft = f"{r['ttft_s']:.2f}" if r["ttft_s"] is not None else "—"
        cat = "tool" if r["prompt_id"] in TOOL_PROMPT_IDS else "plain"
        tool_calls = r.get("tool_calls", [])
        tc_ok = sum(1 for tc in tool_calls if tc.get("duration_s") is not None)
        tc_fail = len(tool_calls) - tc_ok
        tools_str = f"{tc_ok}/{tc_fail}" if tool_calls else "—"
        lines.append(
            f"| {i} | {r['model']} | {r['prompt_id']} | {cat} | {r['module']} "
            f"| {status} "
            f"| {r['total_duration_s']:.1f} "
            f"| {ttft} "
            f"| {r['token_usage']['total_tokens']:,} "
            f"| {r['refinement']['count']} "
            f"| {tools_str} |"
        )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main analysis test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_benchmark(request):
    """
    Load Phase 1 results, compute statistics, and generate reports.

    Discovers per-model ``benchmark_raw_<model>.json`` files in the
    artifacts directory and merges them.  If ``--model`` is given, only
    those models are included.  Also falls back to the legacy combined
    ``benchmark_raw.json`` for backward compatibility.

    This test does not require LLM API access — it only reads the
    JSON artifacts from Phase 1 and computes aggregates.
    """
    from conftest import _selected_models

    # --- Discover per-model files ---
    available = discover_model_benchmark_files()

    # Filter to --model selection (defaults to all)
    try:
        wanted = _selected_models(request.config)
    except pytest.UsageError:
        wanted = list(MODEL_LIST)

    results: List[Dict] = []
    loaded_models: List[str] = []

    for model in wanted:
        mfile = benchmark_file_for_model(model)
        if mfile.exists():
            with open(mfile, encoding="utf-8") as f:
                model_results = json.load(f)
            results.extend(model_results)
            loaded_models.append(model)

    # Fallback: try legacy combined file if nothing found per-model
    if not results and BENCHMARK_RAW_FILE.exists():
        results = _load_json(BENCHMARK_RAW_FILE)
        loaded_models = sorted({r["model"] for r in results})
        print(
            f"\n  [compat] Using legacy {BENCHMARK_RAW_FILE.name} "
            f"({len(results)} records)"
        )

    if not results:
        available_list = list(available.keys()) if available else ["(none)"]
        pytest.skip(
            f"No benchmark artifacts found for models {wanted}.\n"
            f"Available per-model files: {available_list}\n"
            "Run Phase 1 (test_phase1_benchmark.py) first."
        )
    pricing = _load_json(PRICING_FILE)
    # Strip metadata keys from pricing
    pricing = {k: v for k, v in pricing.items() if not k.startswith("_")}

    print(
        f"\nLoaded {len(results)} benchmark records from {len(loaded_models)} model(s)"
    )
    print(f"Models: {loaded_models}")
    print(f"Prompts: {sorted(set(r['prompt_id'] for r in results))}")

    # --- Split by prompt category ---
    plain_results, tool_results = _split_results(results)
    print(
        f"Split: {len(plain_results)} plain runs, "
        f"{len(tool_results)} tool-augmented runs"
    )

    # --- Compute statistics per category ---
    per_model = compute_per_model_stats(results, pricing)  # combined
    per_model_plain = compute_per_model_stats(plain_results, pricing)
    per_model_tool = compute_per_model_stats(tool_results, pricing)

    # Variant comparison uses plain runs only (tool prompts are all 'simple'
    # course_outline — mixing them in would skew simple vs complex).
    per_variant = compute_per_model_per_variant(plain_results, pricing)

    # Per-module uses plain runs so module latency isn't inflated by tool overhead.
    per_module = compute_per_module_stats(plain_results, pricing)

    # Cross-model comparison on plain runs — apples-to-apples.
    cross_model_plain = compute_cross_model_comparison(per_model_plain)

    # Tool vs plain comparison — per-model deltas (co_simple baseline).
    tool_vs_plain = compute_tool_vs_plain_comparison(results, per_model_tool, pricing)

    analysis = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_runs": len(results),
        "plain_runs": len(plain_results),
        "tool_augmented_runs": len(tool_results),
        "tool_prompt_ids": sorted(TOOL_PROMPT_IDS),
        "models_tested": sorted(per_model.keys()),
        "per_model_combined": per_model,
        "per_model_plain": per_model_plain,
        "per_model_tool_augmented": per_model_tool,
        "per_model_per_variant": per_variant,
        "per_module": per_module,
        "cross_model_comparison_plain": cross_model_plain,
        "tool_vs_plain_comparison": tool_vs_plain,
    }

    # --- Save analysis JSON ---
    with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nAnalysis saved to {ANALYSIS_FILE}")

    # --- Generate and save markdown report ---
    report = generate_report(
        per_model,
        per_model_plain,
        per_model_tool,
        per_variant,
        per_module,
        cross_model_plain,
        tool_vs_plain,
        results,
    )
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved to {REPORT_FILE}")

    # --- Print report to stdout ---
    print(f"\n{'='*70}")
    print(report)
    print(f"{'='*70}\n")

    # --- Sanity assertions ---
    # All models tested
    tested_models = set(per_model.keys())
    for model in MODEL_LIST:
        if any(r["model"] == model for r in results):
            assert model in tested_models, f"Missing stats for model {model}"

    # At least some runs succeeded
    total_success = sum(1 for r in results if r["success"])
    print(f"Overall success rate: {total_success}/{len(results)}")
    assert total_success > 0, "No successful benchmark runs — check Phase 1 logs"

    # Token counts should be non-zero for successful runs
    for r in results:
        if r["success"]:
            assert (
                r["token_usage"]["total_tokens"] > 0
            ), f"Zero tokens for successful run: {r['model']}/{r['prompt_id']}"
