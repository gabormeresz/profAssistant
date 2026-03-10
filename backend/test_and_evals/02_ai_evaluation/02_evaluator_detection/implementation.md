# 02 — Evaluator Error Detection Rate: Implementation

## Scope

Section **2.2** — Measuring the evaluator's ability to detect pedagogical and structural errors in Course Outline generation outputs.

**Detection Rate**: Can the evaluator reliably classify deliberately flawed outputs as `NEEDS_REFINEMENT`?

## Approach

| Aspect             | Detail                                                                                     |
| ------------------ | ------------------------------------------------------------------------------------------ |
| **Module**         | Course Outline only (all modules share the same base `route_after_evaluate` logic)         |
| **Model**          | `gpt-4o-mini`                                                                              |
| **Test type**      | Integration tests with real OpenAI API calls (no mocks for LLM)                            |
| **Detection data** | 7 crafted flawed outputs (2 structural + 3 pedagogical + 2 mixed) in `flawed_outputs.json` |
| **Infrastructure** | `evaluate_outline` called directly with crafted `AIMessage` as `agent_response`            |
| **Auth deps**      | `resolve_user_llm_config` patched to return real `OPENAI_API_KEY` + `gpt-4o-mini`          |

## Test Files

| File                     | Tests | Purpose                                                        |
| ------------------------ | ----- | -------------------------------------------------------------- |
| `test_detection_rate.py` | 8     | 7 parametrised flawed-output evaluations + 1 aggregate/export  |
| `conftest.py`            | —     | Fixtures: `mock_resolve_llm_config`, `evaluator_state_factory` |
| `flawed_outputs.json`    | —     | 7 deliberately flawed course outline texts with metadata       |

**Total: 8 test cases**, all marked `@pytest.mark.llm`.

## Flawed Output Design (Detection Rate)

| ID  | Category    | Targeted Dimension(s)                 | Flaw                                                        |
| --- | ----------- | ------------------------------------- | ----------------------------------------------------------- |
| S1  | Structural  | completeness                          | 3/6 classes missing learning_objectives; "TBD" placeholders |
| S2  | Structural  | content_coverage, completeness        | Only 2 classes instead of requested 6                       |
| P1  | Pedagogical | learning_objectives                   | All objectives use "understand", "know", "learn about"      |
| P2  | Pedagogical | progression                           | Reverse complexity: ML first, "what is a computer" last     |
| P3  | Pedagogical | activities                            | Identical "Lecture and Q&A" in every class                  |
| M1  | Mixed       | learning_objectives, content_coverage | Vague verbs + off-topic classes (cooking, gardening, music) |
| M2  | Mixed       | progression, activities, completeness | Random ordering + copy-pasted activity + missing key_topics |

## Key Design Decisions

1. **Direct evaluator call** — Isolates the evaluator's detection capability without graph routing/refining complexity. We call `evaluate_outline(state)` with a crafted `AIMessage(content=…)` as `agent_response`.
2. **JSON test data** — The 7 flawed outputs are substantial text blocks. Keeping them in `flawed_outputs.json` makes test code readable and data extensible.
3. **Dimension-level assertion** — Beyond checking `verdict == NEEDS_REFINEMENT`, we assert the targeted dimension scores are notably low (`< 0.75`), verifying the evaluator correctly _localises_ the error.
4. **Fixed model** — Tests use `gpt-4o-mini`, which achieved 100% detection rate.

## Measured Metrics

| Metric                 | Definition                                                                   | Target |
| ---------------------- | ---------------------------------------------------------------------------- | ------ |
| **Detection rate**     | Fraction of flawed outputs classified as `NEEDS_REFINEMENT` by the evaluator | 100%   |
| **Dimension accuracy** | Targeted dimension scores < 0.75 for each flawed output                      | 100%   |

## How to Run

```bash
cd backend && source .venv/bin/activate

# Run detection-rate tests
pytest test_and_evals/02_ai_evaluation/02_evaluator_detection/tests/ -m llm -v -s

# Via shell script (logs to tests/logs/run.log)
./test_and_evals/02_ai_evaluation/02_evaluator_detection/run_tests.sh
```

## Output

- `tests/artifacts/detection_results.json` — Per-case verdicts, scores, breakdowns, reasoning
- `tests/logs/run.log` — Raw pytest output
