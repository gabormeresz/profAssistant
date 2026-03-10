# 03 — DoS Protection (OWASP LLM04): Results Summary

**Pass rate: 59/59 (100%)**

| Category                          | Tests | Passed |
| --------------------------------- | ----- | ------ |
| Oversized Text Fields (→ 422)     | 41    | 41     |
| Boundary Acceptance (→ 200)       | 2     | 2      |
| File Upload Size Limit (10 MB)    | 2     | 2      |
| Invalid Enum / Structured (→ 400) | 6     | 6      |
| Concurrent Generation Cap (→ 429) | 4     | 4      |
| Combination Attacks (→ 422)       | 2     | 2      |
| Rate Limiting (→ 429)             | 2     | 2      |

## Key Findings

### All 37 Form() fields enforce max_length — Verified

Every text field on every endpoint rejects input exceeding the limit by even 1 character with HTTP 422. The canary pattern confirms rejection occurs at request parsing — no LLM pipeline code is ever reached.

### File size limits work — Verified

~10.1 MB upload → HTTP 413. ~9.9 MB upload → accepted. The 10 MB boundary is correctly enforced.

### Assessment enum validation blocks arbitrary input — Verified

Invalid `assessment_type`, `difficulty_level`, `question_type`, and out-of-range `count` values all return HTTP 400 before the LLM pipeline starts.

### Per-user concurrent generation cap works — Verified

`_acquire_generation_slot()` enforces max 2 concurrent streams. Third request → `HTTPException(429)`. Expired slots (>10 min) are auto-evicted, preventing permanent lockout.

### Boundary values handled correctly — Verified

5,000-char message and 500-char topic (at exact limit) → HTTP 200. Confirms `max_length=N` enforces `<= N`, not `< N`.

### Auth does not bypass validation — Verified

Authenticated users with valid tokens are still rejected on oversized input (HTTP 422).

### Per-IP rate limiting enforced — Verified

`slowapi`'s `@limiter.limit("10/minute")` correctly returns HTTP 429 after the 10th request within a 1-minute window. The 429 response includes a JSON error body. The rate limiter is globally disabled during other tests (via `conftest.py`) and temporarily re-enabled for these specific tests.

## Defense Layer Coverage

| OWASP LLM04 Vector               | Defense                               | Status               |
| -------------------------------- | ------------------------------------- | -------------------- |
| Oversized text input             | `Form(max_length=N)`                  | **Blocked**          |
| Oversized file upload            | `MAX_FILE_SIZE` (10 MB)               | **Blocked**          |
| Invalid structured input         | Pydantic validators + enum whitelists | **Blocked**          |
| Concurrent request amplification | Per-user slot cap (2)                 | **Blocked**          |
| Rate-based flooding              | `@limiter.limit("10/minute")`         | **Blocked** (tested) |

See [tests/logs/test_output_resource_exhaustion_20260307_225603.log](tests/logs/test_output_resource_exhaustion_20260307_225603.log) for full pytest output.
