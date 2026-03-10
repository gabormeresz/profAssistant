# 3.1 Model Performance Profiling & Cost Analysis — Implementation

## Scope

Operational benchmarking of all four generation pipelines (course outline, lesson plan, presentation, assessment) across five OpenAI models (`gpt-4o-mini`, `gpt-4.1-mini`, `gpt-5-mini`, `gpt-5`, `gpt-5.2`). Answers the central research question:

> How do cheaper mini models compare to large (GPT-5-class) models in operational efficiency? Do larger models compensate for higher token costs with fewer refinement cycles or more efficient MCP tool usage, or is the FinOps advantage clearly with smaller models?

Pedagogical quality is **not** scored here — this benchmark focuses exclusively on latency, token consumption, tool-call patterns, refinement loop behaviour, and projected USD costs.

## Approach

Two-phase pytest pipeline with JSON artifact handoff:

```
Phase 1 (benchmark)   ──→  benchmark_raw.json
Phase 2 (analysis)    ──→  analysis.json  +  report.md  +  assertions
```

- **Models**: gpt-4o-mini, gpt-4.1-mini, gpt-5-mini, gpt-5, gpt-5.2 (all user-selectable models)
- **Prompts**: 10 prompts from `prompt_set_ab.json` — 2–3 per module (simple, complex, and tool-trigger variants for course outline)
- **Total runs**: 50 (5 models × 10 prompts)
- **Measurement level**: Graph-level via `astream_events` (v2) — no HTTP/SSE overhead
- **MCP tools**: Live Wikipedia MCP server + Tavily API (not mocked)
- **Checkpointer**: In-memory SQLite (`:memory:`) — no test pollution

## Test Files

| File                             | Phase | Description                                                               |
| -------------------------------- | ----- | ------------------------------------------------------------------------- |
| `tests/prompt_set_ab.json`       | Data  | 10 prompts: 2–3 per module × 4 modules (simple + complex + tool variants) |
| `tests/pricing.json`             | Data  | OpenAI API pricing per 1M tokens (USD) per model                          |
| `tests/conftest.py`              | Setup | API key, model registry, graph builders, patch factory, path constants    |
| `tests/test_phase1_benchmark.py` | 1     | Full pipeline execution for all model × prompt combinations               |
| `tests/test_phase2_analysis.py`  | 2     | Loads Phase 1 artifact, computes aggregates, generates report             |
| `tests/rerun_prompt.py`          | Util  | Re-run a single prompt for a model and swap the result in-place           |
| `tests/visualize.py`             | Util  | Generates 4 PNG charts from `analysis.json` (cost, latency, modules)      |

## Design Decisions

1. **Graph-level measurement over API-level**: Avoids HTTP/auth overhead, gives per-node granularity, and matches the existing judge-test pattern. TTFT is measured as the delta between `graph.astream_events()` start and the first `on_chat_model_stream` event.

2. **Two phases with JSON handoff**: Phase 1 is expensive (~40 real LLM invocations with MCP tool calls). Phase 2 is pure computation and can be re-run independently any number of times to refine the analysis without re-running benchmarks.

3. **Live MCP tools required**: Unlike the judge tests (Section 2.3) which mock MCP to `[]`, this benchmark keeps `mcp_manager` live so tool-call latency and frequency are captured realistically. Only `conversation_manager` and the RAG pipeline are mocked (no uploaded documents in benchmarks, no DB writes).

4. **Per-module patch factory (`mock_infra_for_module`)**: Each module requires its own set of `resolve_user_llm_config` patches (shared base + module-specific evaluation/response nodes) plus its module-specific `conversation_manager`. A single factory handles all 4 modules.

5. **Sequential execution within Phase 1**: Each (model × prompt) pair runs sequentially to avoid rate limiting, produce clean timing measurements, and maintain predictable MCP server load.

6. **Incremental artifact saving**: `benchmark_raw.json` is re-saved after every run — if the benchmark crashes mid-way, partial data is preserved.

7. **Token extraction from `on_chat_model_end`**: LangChain v2 events include `usage_metadata` on `AIMessage` objects — this is the only reliable source since the graph state has no token tracking fields. Both `usage_metadata` (new) and `response_metadata.token_usage` (legacy) are checked.

8. **Pricing in separate JSON file**: Allows updating prices without touching test code. Pricing is loaded only at Phase 2 analysis time.

9. **All four modules benchmarked**: Unlike Section 2.3 (course outline only), this benchmark exercises all pipelines to confirm that model-level operational findings generalise across content types and to surface module-specific complexity differences.

## Metrics

### Latency

| Metric                     | Description                                                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| TTFT (Time to First Token) | `perf_counter` delta from `astream_events` start to first `on_chat_model_stream` event                                    |
| Total duration             | `perf_counter` delta from start to `on_chain_end("LangGraph")` event                                                      |
| Per-node timing            | `on_chain_start` / `on_chain_end` deltas for `generate`, `evaluate`, `refine`, `respond` (accumulated across invocations) |

### Token Usage

| Metric            | Description                                                                 |
| ----------------- | --------------------------------------------------------------------------- |
| Prompt tokens     | Sum of `usage_metadata.input_tokens` across all `on_chat_model_end` events  |
| Completion tokens | Sum of `usage_metadata.output_tokens` across all `on_chat_model_end` events |
| Total tokens      | Prompt + Completion                                                         |

### FinOps

| Metric                 | Description                                                                              |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| Cost per generation    | `(mean_prompt_tokens / 1M) × input_price + (mean_completion_tokens / 1M) × output_price` |
| Cost per 100 documents | `cost_per_generation × 100`                                                              |

### MCP Tool Usage

| Metric               | Description                                               |
| -------------------- | --------------------------------------------------------- |
| Tools per generation | Mean number of `on_tool_start` events per run             |
| Tool breakdown       | Count and mean duration per tool name (Wikipedia, Tavily) |

### Refinement Loop

| Metric            | Description                                                                          |
| ----------------- | ------------------------------------------------------------------------------------ |
| Refinement count  | Number of `on_chain_start("refine")` events per run                                  |
| Exit reason       | Classified as `first_pass_approved`, `refined_approved`, `plateau`, or `max_retries` |
| Evaluation scores | Captured from `evaluate` node output and final graph state `evaluation_history`      |

## Prerequisites

1. **Wikipedia MCP server** running on port 8765:
   ```bash
   uv run wikipedia-mcp --transport sse --port 8765
   # or: docker compose up mcp-wiki
   ```
2. **TAVILY_API_KEY** set in `.env` (remote hosted service)
3. **OPENAI_API_KEY** set in `.env`

## Run Commands

### Quick start (`run_tests.sh`)

```bash
cd backend && source .venv/bin/activate

# All models, both phases
bash test_and_evals/03_performance_and_cost/run_tests.sh

# Single model
bash test_and_evals/03_performance_and_cost/run_tests.sh gpt-4o-mini

# Multiple specific models
bash test_and_evals/03_performance_and_cost/run_tests.sh gpt-4o-mini gpt-5
```

### Manual commands

```bash
cd backend && source .venv/bin/activate

# Phase 1: Benchmark ALL models (~1-2 hours for 40 runs with live MCP)
python -m pytest test_and_evals/03_performance_and_cost/01_model_profiling/tests/test_phase1_benchmark.py \
  -m llm -v --tb=short -s \
  2>&1 | tee test_and_evals/03_performance_and_cost/01_model_profiling/tests/logs/phase1_$(date +%F).log

# Phase 1: Benchmark a SINGLE model
python -m pytest test_and_evals/03_performance_and_cost/01_model_profiling/tests/test_phase1_benchmark.py \
  -m llm --model gpt-4o-mini -v --tb=short -s \
  2>&1 | tee test_and_evals/03_performance_and_cost/01_model_profiling/tests/logs/phase1_gpt-4o-mini_$(date +%F).log

# Phase 2: Analyse ALL collected model results (seconds, no LLM calls)
python -m pytest test_and_evals/03_performance_and_cost/01_model_profiling/tests/test_phase2_analysis.py \
  -v --tb=short -s \
  2>&1 | tee test_and_evals/03_performance_and_cost/01_model_profiling/tests/logs/phase2_$(date +%F).log

# Phase 2: Analyse only specific model(s)
python -m pytest test_and_evals/03_performance_and_cost/01_model_profiling/tests/test_phase2_analysis.py \
  --model gpt-4o-mini -v --tb=short -s
```

### `--model` CLI option

The `--model` flag selects which model(s) to benchmark or analyse. It can be repeated to select multiple models. When omitted, all models in `MODEL_LIST` are used.

| Flag                                | Effect                         |
| ----------------------------------- | ------------------------------ |
| _(none)_                            | Runs all 5 models (default)    |
| `--model gpt-4o-mini`               | Runs only `gpt-4o-mini`        |
| `--model gpt-4o-mini --model gpt-5` | Runs `gpt-4o-mini` and `gpt-5` |

Phase 1 produces **one test per model** (parametrized), so each model's pass/fail status is reported independently. Each model's raw data is saved to a **separate artifact file** (`benchmark_raw_<model>.json`), enabling:

- Running models in separate sessions (e.g. cheap models first, expensive later)
- Resuming after a crash without re-running already completed models
- Collecting data incrementally and analysing partial results

Phase 2 automatically discovers all per-model artifact files and merges them for analysis. Use `--model` in Phase 2 to restrict analysis to specific models.

### Smoke test (single model)

Run Phase 1 with `--model gpt-4o-mini`. Verify `artifacts/benchmark_raw_gpt-4o-mini.json` contains 10 records with non-zero token counts.

### Re-running a single prompt

Use `rerun_prompt.py` to re-execute one prompt for a specific model and swap the result in the existing per-model benchmark file. Useful when a single run failed, timed out, or when the prompt text was changed and needs re-collection.

```bash
cd backend
python test_and_evals/03_performance_and_cost/01_model_profiling/tests/rerun_prompt.py \
  --model gpt-4o-mini --prompt co_simple_ws
```

- Loads the existing `benchmark_raw_gpt-4o-mini.json`
- Runs the specified prompt through the full pipeline (with live MCP)
- Swaps the matching record in-place (or appends if not found)
- Saves the updated file

### Visualization

After Phase 2 has produced `analysis.json`, run `visualize.py` to generate charts:

```bash
cd backend && source .venv/bin/activate

python test_and_evals/03_performance_and_cost/01_model_profiling/tests/visualize.py
```

**Input**: `tests/artifacts/analysis.json` (produced by Phase 2).

**Output** (all saved to `tests/artifacts/`)

## Output

- `tests/artifacts/benchmark_raw_<model>.json` — Per-model raw metrics (10 records each, one per prompt)
- `tests/artifacts/analysis.json` — Aggregated statistics per model, per variant, per module, and cross-model comparisons
- `tests/artifacts/report.md` — Human-readable markdown report with tables
- `tests/artifacts/cost_vs_latency.png` — Cost vs latency scatter chart
- `tests/artifacts/model_comparison.png` — Latency + cost bar comparison
- `tests/artifacts/per_module_latency.png` — Per-module latency bar chart
- `tests/artifacts/cost_scaling.png` — Cost-at-scale horizontal bar chart
- `tests/logs/phase1_<date>.log` — Raw pytest output for Phase 1
- `tests/logs/phase2_<date>.log` — Raw pytest output for Phase 2
