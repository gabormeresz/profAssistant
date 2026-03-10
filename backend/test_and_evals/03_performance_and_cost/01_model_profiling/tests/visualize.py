"""
Visualize model profiling results — Cost & Latency focus.

Reads analysis.json and produces EN + HU versions of:
  1. cost_vs_latency_{lang}.png   — scatter: cost/gen vs mean latency (plain runs)
  2. model_comparison_{lang}.png  — side-by-side bars: latency + cost per model
  3. per_module_latency_{lang}.png — bar chart: mean latency by generation module
  4. cost_scaling_{lang}.png      — horizontal bars: projected cost at scale

Output goes to tests/artifacts/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ── paths ────────────────────────────────────────────────────────────
ARTIFACTS = Path(__file__).parent / "artifacts"
DATA_FILE = ARTIFACTS / "analysis.json"

# ── style ────────────────────────────────────────────────────────────
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "#f8f9fa",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "font.family": "sans-serif",
        "font.size": 11,
    }
)

MODEL_COLORS = {
    "gpt-4o-mini": "#4CAF50",
    "gpt-4.1-mini": "#2196F3",
    "gpt-5-mini": "#FF9800",
    "gpt-5": "#F44336",
    "gpt-5.2": "#9C27B0",
}

MODEL_ORDER = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-5-mini", "gpt-5", "gpt-5.2"]

# ── i18n ─────────────────────────────────────────────────────────────
LOCALES: dict[str, dict[str, str | list[str]]] = {
    "en": {
        # Chart 1 — Cost vs Latency
        "c1_xlabel": "Mean Latency (seconds)",
        "c1_ylabel": "Cost per Generation (USD)",
        "c1_title": "Cost vs Latency — Plain Generation",
        # Chart 2 — Model Comparison
        "c2_lat_ylabel": "Mean Latency (s)",
        "c2_lat_title": "Mean Latency per Generation",
        "c2_cost_ylabel": "Cost per Generation (USD)",
        "c2_cost_title": "Cost per Generation",
        "c2_suptitle": "Model Comparison — Plain Generation (no tools)",
        # Chart 3 — Per-module latency
        "c3_mod_labels": [
            "Course\nOutline",
            "Lesson\nPlan",
            "Presentation",
            "Assessment",
        ],
        "c3_ylabel": "Mean Latency (s)",
        "c3_title": "Mean Latency by Generation Module (all models averaged)",
        "c3_tok_label": "tok",
        # Chart 4 — Cost scaling
        "c4_xlabel": "Cost per 100 Documents (USD)",
        "c4_title": "Projected Cost at Scale — 100 Generations",
    },
    "hu": {
        # Chart 1 — Költség vs Késleltetés
        "c1_xlabel": "Átlagos késleltetés (másodperc)",
        "c1_ylabel": "Költség / generálás (USD)",
        "c1_title": "Költség vs Késleltetés — Alap generálás",
        # Chart 2 — Modell összehasonlítás
        "c2_lat_ylabel": "Átlagos késleltetés (s)",
        "c2_lat_title": "Átlagos késleltetés generálásonként",
        "c2_cost_ylabel": "Költség / generálás (USD)",
        "c2_cost_title": "Költség generálásonként",
        "c2_suptitle": "Modell összehasonlítás — Alap generálás (eszközök nélkül)",
        # Chart 3 — Modulonkénti késleltetés
        "c3_mod_labels": ["Tematika", "Óraterv", "Prezentáció", "Értékelés"],
        "c3_ylabel": "Átlagos késleltetés (s)",
        "c3_title": "Átlagos késleltetés generálási modulonként (összes modell átlaga)",
        "c3_tok_label": "tok",
        # Chart 4 — Költség skálázás
        "c4_xlabel": "Költség / 100 dokumentum (USD)",
        "c4_title": "Várható költség skálázásnál — 100 generálás",
    },
}


def load_data() -> dict:
    with open(DATA_FILE) as f:
        return json.load(f)


def _suffix(lang: str) -> str:
    return f"_{lang}"


# ── Chart 1: Cost vs Latency scatter ────────────────────────────────
def chart_cost_vs_latency(data: dict, lang: str) -> None:
    t = LOCALES[lang]
    plain = data["per_model_plain"]

    fig, ax = plt.subplots(figsize=(8, 5.5))

    for model in MODEL_ORDER:
        info = plain[model]
        cost = info["finops"]["cost_per_generation_usd"]
        lat = info["latency"]["mean_s"]
        color = MODEL_COLORS[model]

        ax.scatter(
            lat,
            cost,
            s=180,
            color=color,
            edgecolors="white",
            linewidths=1.5,
            zorder=5,
            label=model,
        )
        ax.annotate(
            f"${cost:.4f}",
            (lat, cost),
            textcoords="offset points",
            xytext=(10, 6),
            fontsize=9,
            color=color,
            fontweight="bold",
        )

    ax.set_xlabel(t["c1_xlabel"], fontsize=12)
    ax.set_ylabel(t["c1_ylabel"], fontsize=12)
    ax.set_title(t["c1_title"], fontsize=14, fontweight="bold")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.4f}"))
    ax.legend(loc="upper left", framealpha=0.9)

    fname = f"cost_vs_latency{_suffix(lang)}.png"
    fig.tight_layout()
    fig.savefig(ARTIFACTS / fname, dpi=150)
    plt.close(fig)
    print(f"  ✓ {fname}")


# ── Chart 2: Side-by-side bars — Latency + Cost ─────────────────────
def chart_model_comparison(data: dict, lang: str) -> None:
    t = LOCALES[lang]
    plain = data["per_model_plain"]

    models = MODEL_ORDER
    latencies = [plain[m]["latency"]["mean_s"] for m in models]
    costs = [plain[m]["finops"]["cost_per_generation_usd"] for m in models]
    colors = [MODEL_COLORS[m] for m in models]
    labels = [m.replace("gpt-", "") for m in models]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # -- latency bars --
    bars1 = ax1.bar(labels, latencies, color=colors, edgecolor="white", linewidth=1.2)
    ax1.set_ylabel(t["c2_lat_ylabel"], fontsize=12)
    ax1.set_title(t["c2_lat_title"], fontsize=13, fontweight="bold")
    for bar, val in zip(bars1, latencies):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{val:.1f}s",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )
    ax1.set_ylim(0, max(latencies) * 1.25)

    # -- cost bars (log scale) --
    bars2 = ax2.bar(labels, costs, color=colors, edgecolor="white", linewidth=1.2)
    ax2.set_ylabel(t["c2_cost_ylabel"], fontsize=12)
    ax2.set_title(t["c2_cost_title"], fontsize=13, fontweight="bold")
    ax2.set_yscale("log")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:.4f}"))
    for bar, val in zip(bars2, costs):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() * 1.15,
            f"${val:.4f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )
    ax2.set_ylim(top=max(costs) * 2.5)

    fig.suptitle(
        t["c2_suptitle"],
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    fname = f"model_comparison{_suffix(lang)}.png"
    fig.tight_layout()
    fig.savefig(ARTIFACTS / fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {fname}")


# ── Chart 3: Per-module latency ──────────────────────────────────────
def chart_per_module_latency(data: dict, lang: str) -> None:
    t = LOCALES[lang]
    modules = data["per_module"]
    mod_order = ["course_outline", "lesson_plan", "presentation", "assessment"]
    mod_labels = t["c3_mod_labels"]
    tok_label = t["c3_tok_label"]

    latencies = [modules[m]["mean_latency_s"] for m in mod_order]
    tokens = [modules[m]["mean_total_tokens"] for m in mod_order]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    bar_colors = ["#42A5F5", "#66BB6A", "#FFA726", "#EF5350"]
    bars = ax1.bar(
        mod_labels, latencies, color=bar_colors, edgecolor="white", linewidth=1.2
    )
    ax1.set_ylabel(t["c3_ylabel"], fontsize=12)
    ax1.set_title(
        t["c3_title"],
        fontsize=13,
        fontweight="bold",
    )

    for bar, lat, tok in zip(bars, latencies, tokens):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{lat:.1f}s\n({tok:,.0f} {tok_label})",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    ax1.set_ylim(0, max(latencies) * 1.2)
    fname = f"per_module_latency{_suffix(lang)}.png"
    fig.tight_layout()
    fig.savefig(ARTIFACTS / fname, dpi=150)
    plt.close(fig)
    print(f"  ✓ {fname}")


# ── Chart 4: Cost scaling — $/100 docs ───────────────────────────────
def chart_cost_scaling(data: dict, lang: str) -> None:
    t = LOCALES[lang]
    plain = data["per_model_plain"]

    models = MODEL_ORDER
    costs_100 = [plain[m]["finops"]["cost_per_100_docs_usd"] for m in models]
    colors = [MODEL_COLORS[m] for m in models]
    labels = [m.replace("gpt-", "GPT-") for m in models]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(
        labels, costs_100, color=colors, edgecolor="white", linewidth=1.2, height=0.6
    )

    for bar, val in zip(bars, costs_100):
        ax.text(
            bar.get_width() + 0.15,
            bar.get_y() + bar.get_height() / 2,
            f"${val:.2f}",
            va="center",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_xlabel(t["c4_xlabel"], fontsize=12)
    ax.set_title(t["c4_title"], fontsize=13, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlim(0, max(costs_100) * 1.25)

    fname = f"cost_scaling{_suffix(lang)}.png"
    fig.tight_layout()
    fig.savefig(ARTIFACTS / fname, dpi=150)
    plt.close(fig)
    print(f"  ✓ {fname}")


# ── main ─────────────────────────────────────────────────────────────
def main() -> None:
    data = load_data()
    for lang in LOCALES:
        print(f"Generating charts [{lang}] …")
        chart_cost_vs_latency(data, lang)
        chart_model_comparison(data, lang)
        chart_per_module_latency(data, lang)
        chart_cost_scaling(data, lang)
    print(f"Done — charts saved to {ARTIFACTS}/")


if __name__ == "__main__":
    main()
