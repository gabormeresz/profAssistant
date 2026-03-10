# 2.3 LLM-as-a-Judge — Implementation

## Scope

External validation of zero-shot course outline generation quality using an independent GPT-5.2 judge. Answers one central question:

> Do the baseline generation prompts already achieve the ≥ 0.8 QA threshold on the first pass (zero-shot), without relying on the iterative refinement loop?

Secondary goal: verify that the internal gpt-4o-mini evaluator agrees with the GPT-5.2 gold standard on absolute score levels (meta-evaluation).

## Approach

Two-phase pytest pipeline with JSON artifact handoff:

```
Phase 1 (generate_drafts)   ──→  drafts.json
Phase 2 (judge_and_analyse)  ──→  judge_results.json  +  analysis_summary.json  +  assertions
```

- **Generation model**: gpt-4o-mini (same model for generator + internal evaluator)
- **Judge model**: GPT-5.2 (reasoning_effort=low via evaluator preset — the best available model judging the least capable)
- **Approval threshold**: 0.8 (production default — no override)
- **Module**: Course Outline only
- **Prompt set**: 15 prompts across 5 disciplines (CS, Natural Sciences, Humanities, Social Sciences, Engineering), 3 per discipline

## Test Files

| File                                 | Phase | Description                                                         |
| ------------------------------------ | ----- | ------------------------------------------------------------------- |
| `tests/prompt_set.json`              | Data  | 15 prompts: 3 per discipline (reusable for Section 3.1)             |
| `tests/conftest.py`                  | Setup | API key, model constants, judge helpers, serializer, path constants |
| `tests/test_01_generate_drafts.py`   | 1     | Full graph execution, first-pass draft capture                      |
| `tests/test_02_judge_and_analyse.py` | 2     | GPT-5.2 scoring of drafts, statistics, and assertions               |

## Design Decisions

1. **Production threshold (0.8)**: We use the production default. Drafts that pass on the first try are exactly the zero-shot behavior we want to measure — no artificial forcing of the refinement loop.

2. **Draft extraction via `astream_events`**: The graph's `agent_response` is overwritten on each refine step. We intercept the first `on_chain_end` event for the `generate` node to capture the raw draft before any refinement occurs.

3. **Same rubric for judge**: `build_judge_messages()` reuses `get_evaluator_system_prompt()` and the identical XML-wrapped evaluation request format from the production `evaluate_outline` node — the only variables are the model (GPT-5.2 vs gpt-4o-mini) and reasoning mode (low-effort reasoning vs none). The judge uses `get_structured_output_model(purpose="evaluator")` — the same factory the app uses — so presets (reasoning_effort, temperature filtering) are applied identically.

4. **Two phases instead of three**: Generation is expensive (~20–40 min for 15 prompts). Judge scoring, analysis, and assertions are combined into a single Phase 2 that can re-run independently against the Phase 1 artifact.

5. **Draft-only scoring**: Since the focus is on zero-shot quality, the judge only scores drafts (first-pass output). Final/refined outputs are not scored — the refinement delta is not a metric of interest.

6. **Sequential prompt execution** (single test, loop): Avoids 15 separate graph compilations and produces a single consolidated artifact file.

7. **Serialize draft to markdown**: `serialize_course_outline_to_text()` converts the draft to readable markdown so the judge evaluates a clean text format.

8. **In-memory SQLite checkpointer**: Each prompt gets a fresh `:memory:` database — no test pollution, no cleanup needed.

9. **Infrastructure mocking**: `conversation_manager`, `mcp_manager` (MCP tools), and `rag_pipeline` are all mocked since they're irrelevant for zero-shot quality measurement. Only the LLM calls are real.

## Metrics and Thresholds

### Zero-Shot Quality (all prompts)

| Metric                            | Threshold | Rationale                                                                    |
| --------------------------------- | --------- | ---------------------------------------------------------------------------- |
| Mean draft score (GPT-5.2 judge)  | ≥ 0.80    | Production approval threshold; drafts should meet it without refinement      |
| % prompts with draft score ≥ 0.80 | ≥ 80%     | Vast majority of prompts must pass zero-shot; occasional outliers acceptable |
| Min draft score                   | ≥ 0.70    | No prompt should produce catastrophically low quality                        |

### Per-Dimension Zero-Shot Quality

| Metric                         | Threshold | Rationale                                                       |
| ------------------------------ | --------- | --------------------------------------------------------------- |
| Per-dimension mean draft score | ≥ 0.75    | Each rubric dimension individually must be strong; no weak axis |

### Meta-Evaluation

| Metric                  | Threshold | Rationale                                                             |
| ----------------------- | --------- | --------------------------------------------------------------------- |
| MAE (internal vs judge) | < 0.15    | Internal evaluator and external judge should agree on absolute levels |

## Run Commands

```bash
cd backend && source .venv/bin/activate

# Phase 1: Generate drafts (~20-40 min, 15 full generation runs)
python -m pytest test_and_evals/02_ai_evaluation/03_llm_judge/tests/test_01_generate_drafts.py \
  -m llm -v --tb=short -s \
  2>&1 | tee test_and_evals/02_ai_evaluation/03_llm_judge/tests/logs/phase1_$(date +%F).log

# Phase 2: Judge scoring + analysis + assertions (~5-10 min, 15 GPT-5.2 calls)
python -m pytest test_and_evals/02_ai_evaluation/03_llm_judge/tests/test_02_judge_and_analyse.py \
  -m llm -v --tb=short -s \
  2>&1 | tee test_and_evals/02_ai_evaluation/03_llm_judge/tests/logs/phase2_$(date +%F).log
```

### Smoke test (single prompt)

Temporarily edit `prompt_set.json` to keep only 1 prompt, then run Phase 1.

## Output

- `tests/artifacts/drafts.json` — Draft content, internal eval score, generation metadata per prompt
- `tests/artifacts/judge_results.json` — Judge scores per draft, per-dimension breakdown
- `tests/artifacts/analysis_summary.json` — Aggregated statistics and assertion results
- `tests/logs/phase1_<date>.log` — Raw pytest output for Phase 1 (generation)
- `tests/logs/phase2_<date>.log` — Raw pytest output for Phase 2 (judge + analysis)
