# AI Evaluation — Overview

**Total: 51 tests** (all LLM) | **Pass rate: 48/49 (2.1–2.2), pending re-run (2.3)** | **Hit Rate@5: 100%, MRR@5: 0.9348, Detection Rate: 100%**

## Structure

| Folder                                             | Section | Tests | Topic                                                        |
| -------------------------------------------------- | ------- | ----- | ------------------------------------------------------------ |
| [01_isolated_rag/](01_isolated_rag/)               | 2.1     | 41    | RAG retrieval quality: Hit Rate@5, MRR@5, bilingual (EN+HU)  |
| [02_evaluator_detection/](02_evaluator_detection/) | 2.2     | 8     | Evaluator error detection rate: flawed output classification |
| [03_llm_judge/](03_llm_judge/)                     | 2.3     | 2     | Zero-shot quality validation: GPT-5.2 judge, 15 prompts      |

Each subfolder contains:

- `implementation.md` — approach, design decisions, test structure
- `results_summary.md` — pass rates, key findings
- `tests/` — test files, fixtures, ground truth data
  - `artifacts/` — generated files during test runs
  - `logs/` — raw pytest output

## Quick Start

```bash
cd backend && source .venv/bin/activate

# Run all AI evaluation tests (requires OPENAI_API_KEY)
pytest test_and_evals/02_ai_evaluation/ -m llm -v -s
```
