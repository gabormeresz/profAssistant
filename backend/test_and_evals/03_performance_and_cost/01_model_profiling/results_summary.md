# 3.1 — Model Performance Profiling & Cost Analysis: Results Summary

> **Status:** PASSED — 50/50 runs succeeded, 100% overall success rate. Run date: 2026-03-03.

## Run Info

| Field                  | Value                                                 |
| ---------------------- | ----------------------------------------------------- |
| Date                   | 2026-03-03                                            |
| Models tested          | gpt-4o-mini, gpt-4.1-mini, gpt-5-mini, gpt-5, gpt-5.2 |
| Total runs             | 50 (plain: 40, tool-augmented: 10)                    |
| Overall success rate   | 100%                                                  |
| First-pass rate        | 98% (49/50 — gpt-5.2 required 1 refinement)           |
| Tool-augmented prompts | co_simple_wiki, co_simple_ws                          |

> **Terminology.** _Plain_ = generation without external tool access (no web search, no Wikipedia). _Tool-augmented_ = generation with MCP tool access (Tavily web search, Wikipedia). Both use the same LangGraph agent workflow (generate → evaluate → refine).

## Plain Generation — Latency & Cost

| Model        | Runs | Mean Lat. (s) | Median Lat. (s) | P95 Lat. (s) | Mean TTFT (s) | Mean Total Tok. | $/gen   | $/100 docs |
| ------------ | ---- | ------------- | --------------- | ------------ | ------------- | --------------- | ------- | ---------- |
| gpt-4o-mini  | 8    | 64.6          | 59.0            | 118.2        | 0.75          | 11,232          | $0.0028 | $0.28      |
| gpt-4.1-mini | 8    | 57.2          | 47.7            | 125.6        | 0.68          | 13,030          | $0.0092 | $0.92      |
| gpt-5-mini   | 8    | 129.3         | 124.5           | 194.7        | 23.31         | 21,805          | $0.0206 | $2.06      |
| gpt-5        | 8    | 164.6         | 151.9           | 266.3        | 56.18         | 22,062          | $0.1173 | $11.73     |
| gpt-5.2      | 8    | 82.6          | 78.6            | 124.0        | 7.06          | 18,695          | $0.1056 | $10.56     |

## Cross-Model Comparison (baseline: gpt-4o-mini)

| Model        | Cost Ratio | Latency Ratio |
| ------------ | ---------- | ------------- |
| gpt-4o-mini  | 1.0×       | 1.0×          |
| gpt-4.1-mini | 3.2×       | 0.9×          |
| gpt-5-mini   | 7.2×       | 2.0×          |
| gpt-5        | 41.2×      | 2.5×          |
| gpt-5.2      | 37.1×      | 1.3×          |

## Per-Module Summary (plain prompts, all models)

| Module         | Runs | Mean Lat. (s) | Mean Tokens | $/gen   |
| -------------- | ---- | ------------- | ----------- | ------- |
| course_outline | 10   | 78.7          | 14,820      | $0.0388 |
| lesson_plan    | 10   | 96.6          | 17,335      | $0.0505 |
| presentation   | 10   | 107.2         | 17,861      | $0.0561 |
| assessment     | 10   | 116.2         | 19,442      | $0.0590 |

## Tool-Augmented vs Plain Generation Comparison

> Compares tool-augmented prompts (co_simple_wiki, co_simple_ws) against the matching plain baseline (co_simple) — same module, variant, and discipline but without tool access. Ratios >1× indicate tool overhead.

| Model        | Lat. Δ | Tok. Δ | Cost Δ | Plain Cache% | Tool Cache% | Calls (ok/fail) | Tool Breakdown                                                                            |
| ------------ | ------ | ------ | ------ | ------------ | ----------- | --------------- | ----------------------------------------------------------------------------------------- |
| gpt-4o-mini  | 0.90×  | 1.59×  | 1.35×  | 0%           | 47%         | 3ok/0fail       | tavily_search: 1ok, search_wikipedia: 1ok, get_summary: 1ok                               |
| gpt-4.1-mini | 0.76×  | 1.50×  | 1.31×  | 0%           | 46%         | 3ok/0fail       | tavily_search: 1ok, search_wikipedia: 2ok                                                 |
| gpt-5-mini   | 1.17×  | 1.77×  | 1.21×  | 0%           | 49%         | 4ok/2fail       | tavily_search: 2ok/1fail, search_wikipedia: 1ok, get_summary: 0ok/1fail, get_article: 1ok |
| gpt-5        | 1.67×  | 2.72×  | 1.72×  | 0%           | 47%         | 11ok/1fail      | tavily_search: 7ok/1fail, search_wikipedia: 1ok, get_summary: 3ok                         |
| gpt-5.2      | 1.40×  | 2.23×  | 1.66×  | 0%           | 31%         | 10ok/0fail      | tavily_search: 3ok, search_wikipedia: 3ok, get_summary: 4ok                               |

> **Reliability note.** Token and cost deltas are structurally reliable — tool-augmented runs deterministically ingest retrieved context, producing a consistent 1.5×–2.7× token overhead. Latency deltas are **not** reliable for two reasons: (1) the plain baseline is a single run (n=1) per model, so run-to-run variance dominates; (2) **prompt caching is a confounding variable** — the plain baseline (`co_simple`) always ran first with 0% cached prompt tokens, while subsequent tool runs benefited from 21–75% prompt caching on the shared system-prompt prefix, reducing their TTFT (e.g. gpt-5-mini: 18.6s → 2.4s). For fast non-reasoning models, this caching advantage can outweigh tool-call overhead, producing the sub-1× latency ratios for gpt-4o-mini and gpt-4.1-mini.

## Reasoning Token Overhead (reasoning models only)

| Model      | Mean Completion Tok. | Mean Reasoning Tok. | Reasoning / Completion |
| ---------- | -------------------- | ------------------- | ---------------------- |
| gpt-5-mini | 8,086                | 2,400               | 29.7%                  |
| gpt-5      | 9,886                | 5,005               | 50.6%                  |
| gpt-5.2    | 5,402                | 582                 | 10.8%                  |

> gpt-4o-mini and gpt-4.1-mini report 0 reasoning tokens (non-reasoning models).

## Key Findings

1. **100% success rate across all models** — All 50 runs completed successfully. Every model produced schema-valid, self-approved output for all four generation modules. Note: each model evaluates its own output (same model type generates and judges), so approval rates are **not** comparable across models as a quality measure.
2. **gpt-4o-mini is the most cost-efficient** — At $0.0028/generation ($0.28/100 docs) it is 3–41× cheaper than alternatives. gpt-4.1-mini is slightly faster (0.9× latency) but 3.2× the cost. Since each model self-evaluates, the identical 100% approval rates do not imply equal output quality — cross-model quality comparison requires an external judge (see Section 2.3).
3. **gpt-5 and gpt-5.2 are prohibitively expensive** — 37–41× the cost of gpt-4o-mini. gpt-5 is also the slowest (2.5× latency, 56s mean TTFT). gpt-5.2 is faster (1.3× latency) but was the **only model to require refinement** (1/10 runs), meaning its own evaluator rejected its first draft once — the only self-evaluation failure in the benchmark.
4. **TTFT scales dramatically with model size** — gpt-4o-mini: 0.75s, gpt-4.1-mini: 0.68s, gpt-5-mini: 23.3s, gpt-5: 56.2s, gpt-5.2: 7.1s. Models with reasoning capabilities (gpt-5, gpt-5-mini) have significantly higher time-to-first-token due to internal chain-of-thought.
5. **Assessment is the heaviest module** — Across all models, assessment generation is the slowest (116.2s mean) and most token-heavy (19,442 mean tokens), while course outline is the lightest (78.7s, 14,820 tokens).
6. **Complex prompts ~1.6–1.8× more expensive than simple** — Across models, complex variants consistently consume more tokens and latency than simple variants, but the ratio is stable and predictable.
7. **Tool-augmented runs add 1.5×–2.7× token overhead but modest cost overhead** — Retrieved context from tool calls inflates token counts consistently across all models. Cost overhead (1.21×–1.72×) is lower than token overhead because OpenAI charges half price for cached prompt tokens. More capable models make more tool calls (gpt-5: 11/run, gpt-5.2: 10/run) and retrieve more context, amplifying their token overhead (2.72× and 2.23×) compared to smaller models (1.50×–1.59×).
8. **Prompt caching confounds latency comparison** — The plain baseline (`co_simple`) always ran first per model with 0% prompt caching, while subsequent tool runs benefited from 31–52% cached prompt tokens on the shared system-prompt prefix. This reduced tool-run TTFT dramatically (e.g. gpt-5-mini: 18.6s → 2.4s) and explains the counterintuitive sub-1× latency deltas for gpt-4o-mini (0.90×) and gpt-4.1-mini (0.76×) — their caching benefit outweighed tool-call overhead. Latency deltas in this benchmark are therefore not reliable indicators of tool overhead.
9. **Self-evaluation caveat** — This benchmark measures operational characteristics (latency, cost, token usage, tool reliability) rather than absolute output quality. All approval/refinement metrics reflect each model's self-assessment. For cross-model quality comparison with an independent judge, see Section 2.3 (LLM-as-a-Judge).

## Log References

- Phase 1 logs: `tests/logs/phase1_<model_name>_2026-03-03.log`
- Phase 2 analysis: `tests/logs/phase2_2026-03-03.log`
- Full report: `tests/artifacts/report.md`
