# System & Security Testing — Overview

**Total: 235 tests** (221 deterministic + 14 LLM) | **Pass rate: 200/202 on gpt-4o-mini, 202/202 on gpt-5-mini** _(1.1–1.3)_

## Structure

| Folder                                             | Section | Tests | Topic                                                                        |
| -------------------------------------------------- | ------- | ----- | ---------------------------------------------------------------------------- |
| [01_auth_and_resilience/](01_auth_and_resilience/) | 1.1     | 39    | OpenAI error handling, SSE disconnection, JWT validation                     |
| [02_prompt_injection/](02_prompt_injection/)       | 1.2     | 103   | Regex adversarial testing, LLM-level injection resistance                    |
| [03_dos_protection/](03_dos_protection/)           | 1.3     | 60    | Input validation, file size limits, concurrent generation cap, rate limiting |
| [04_insecure_output/](04_insecure_output/)         | 1.4     | 33    | XSS payload transport verification, frontend static security scan            |

Each subfolder contains:

- `results_summary.md` — pass rates, key findings
- `tests/logs/*.log` — raw pytest output

## Shared Files

> **Note:** Shared fixtures and the log-capture plugin live in the root [`test_and_evals/conftest.py`](../conftest.py). Logs are written per-test-file with a `_YYYYMMDD_HHMMSS` timestamp suffix; older logs are preserved.

## Quick Start

```bash
cd backend && source .venv/bin/activate

# All deterministic tests (no API key needed)
pytest test_and_evals/01_system_and_security/ -v -m "not llm"

# Everything including LLM tests
pytest test_and_evals/01_system_and_security/ -v
```
