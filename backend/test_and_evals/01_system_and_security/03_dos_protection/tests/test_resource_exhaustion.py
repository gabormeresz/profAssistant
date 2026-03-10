"""
Test 1.3 — LLM Resource Exhaustion Protection (Model DoS — OWASP LLM04)
=========================================================================

**Objective:** Prove that the backend's input validation layer immediately
rejects excessively large or malformed requests *before* any LLM token
consumption occurs.

**What is tested:**

1. **Oversized text fields** — Every ``Form()`` parameter on every generation
   endpoint has a ``max_length`` constraint.  Submitting data that exceeds the
   limit must return HTTP 422 (Pydantic validation error) without touching the
   LLM.

2. **Oversized file uploads** — Files larger than ``UploadConfig.MAX_FILE_SIZE``
   (default 10 MB) must be rejected with HTTP 413.

3. **Invalid enum / structured fields** — Malformed ``assessment_type``,
   ``difficulty_level``, and ``question_type_configs`` values must return
   HTTP 400 before the generation pipeline starts.

4. **Concurrent generation cap** — A single user exceeding
   ``MAX_CONCURRENT_GENERATIONS`` (2) must receive HTTP 429.

**Strategy:**
- Tests reuse the shared ``test_app`` / ``client`` fixtures from the
  top-level ``conftest.py`` (auth + API-key already stubbed).
- For oversized-field tests the LangGraph generator is patched to a
  *canary* that raises ``AssertionError("LLM was called")`` — if validation
  is correctly enforced the canary will never fire.
- For concurrency-cap tests we inject a slow generator and saturate the
  slots, then verify the third request is rejected with 429.

No real LLM calls, API keys, or database connections are needed.
"""

import asyncio
import io
import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CANARY_ERROR = "LLM was called — input validation did not reject the oversized request"


async def _canary_generator(*args, **kwargs):
    """Generator that should NEVER be reached if validation works."""
    raise AssertionError(CANARY_ERROR)
    yield  # noqa: unreachable — makes this an async generator  # pragma: no cover


# ---------------------------------------------------------------------------
# Form data builders
# ---------------------------------------------------------------------------


def _course_outline_form(overrides: dict | None = None) -> dict:
    base = {
        "message": "Create a course outline",
        "topic": "Software Testing",
        "number_of_classes": "8",
        "language": "English",
    }
    if overrides:
        base.update(overrides)
    return base


def _lesson_plan_form(overrides: dict | None = None) -> dict:
    base = {
        "message": "Plan a lesson",
        "course_title": "Intro to CS",
        "class_number": "1",
        "class_title": "Variables",
        "learning_objectives": json.dumps(["Understand variables"]),
        "key_topics": json.dumps(["Variables", "Types"]),
        "activities_projects": json.dumps(["Write a program"]),
        "language": "English",
    }
    if overrides:
        base.update(overrides)
    return base


def _presentation_form(overrides: dict | None = None) -> dict:
    base = {
        "message": "Create slides",
        "course_title": "Intro to CS",
        "class_number": "1",
        "class_title": "Variables",
        "learning_objective": "Understand variable types",
        "key_points": json.dumps(["Variables", "Types"]),
        "language": "English",
    }
    if overrides:
        base.update(overrides)
    return base


def _assessment_form(overrides: dict | None = None) -> dict:
    base = {
        "message": "Create an assessment",
        "course_title": "Intro to CS",
        "class_title": "Variables",
        "key_topics": json.dumps(["Variables", "Types"]),
        "assessment_type": "quiz",
        "difficulty_level": "medium",
        "question_type_configs": json.dumps(
            [
                {"question_type": "multiple_choice", "count": 5, "points_each": 10},
            ]
        ),
        "language": "English",
    }
    if overrides:
        base.update(overrides)
    return base


def _enhance_prompt_form(overrides: dict | None = None) -> dict:
    base = {
        "message": "Help me improve this prompt",
        "context_type": "course_outline",
    }
    if overrides:
        base.update(overrides)
    return base


# Mapping endpoint → (form builder, generator patch target)
ENDPOINTS = {
    "/course-outline-generator": (
        _course_outline_form,
        "routes.generation.run_course_outline_generator",
    ),
    "/lesson-plan-generator": (
        _lesson_plan_form,
        "routes.generation.run_lesson_plan_generator",
    ),
    "/presentation-generator": (
        _presentation_form,
        "routes.generation.run_presentation_generator",
    ),
    "/assessment-generator": (
        _assessment_form,
        "routes.generation.run_assessment_generator",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# 1. Oversized text fields → HTTP 422
# ═══════════════════════════════════════════════════════════════════════════


class TestOversizedTextFields:
    """
    Every ``Form(max_length=N)`` constraint must reject oversized input with
    HTTP 422 *before* the LLM pipeline is invoked.
    """

    # ── Course outline ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "field, limit",
        [
            ("message", 5_000),
            ("topic", 500),
            ("language", 50),
            ("thread_id", 100),
        ],
    )
    async def test_course_outline_oversized_field(self, client, field, limit):
        """Oversized field on /course-outline-generator → 422."""
        form = _course_outline_form({field: "x" * (limit + 1)})
        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/course-outline-generator", data=form)
        assert (
            resp.status_code == 422
        ), f"Expected 422 for {field} ({limit + 1} chars), got {resp.status_code}"

    # ── Lesson plan ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "field, limit",
        [
            ("message", 5_000),
            ("course_title", 500),
            ("class_title", 500),
            ("learning_objectives", 5_000),
            ("key_topics", 5_000),
            ("activities_projects", 5_000),
            ("language", 50),
            ("thread_id", 100),
        ],
    )
    async def test_lesson_plan_oversized_field(self, client, field, limit):
        """Oversized field on /lesson-plan-generator → 422."""
        form = _lesson_plan_form({field: "x" * (limit + 1)})
        with patch(
            "routes.generation.run_lesson_plan_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/lesson-plan-generator", data=form)
        assert (
            resp.status_code == 422
        ), f"Expected 422 for {field} ({limit + 1} chars), got {resp.status_code}"

    # ── Presentation ──────────────────────────────────────────────────────

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "field, limit",
        [
            ("message", 5_000),
            ("course_title", 500),
            ("class_title", 500),
            ("learning_objective", 2_000),
            ("key_points", 5_000),
            ("lesson_breakdown", 5_000),
            ("activities", 5_000),
            ("homework", 5_000),
            ("extra_activities", 5_000),
            ("language", 50),
            ("thread_id", 100),
        ],
    )
    async def test_presentation_oversized_field(self, client, field, limit):
        """Oversized field on /presentation-generator → 422."""
        form = _presentation_form({field: "x" * (limit + 1)})
        with patch(
            "routes.generation.run_presentation_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/presentation-generator", data=form)
        assert (
            resp.status_code == 422
        ), f"Expected 422 for {field} ({limit + 1} chars), got {resp.status_code}"

    # ── Assessment ────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "field, limit",
        [
            ("message", 5_000),
            ("course_title", 500),
            ("class_title", 500),
            ("key_topics", 5_000),
            ("assessment_type", 50),
            ("difficulty_level", 50),
            ("question_type_configs", 5_000),
            ("additional_instructions", 5_000),
            ("language", 50),
            ("thread_id", 100),
        ],
    )
    async def test_assessment_oversized_field(self, client, field, limit):
        """Oversized field on /assessment-generator → 422."""
        form = _assessment_form({field: "x" * (limit + 1)})
        with patch(
            "routes.generation.run_assessment_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/assessment-generator", data=form)
        assert (
            resp.status_code == 422
        ), f"Expected 422 for {field} ({limit + 1} chars), got {resp.status_code}"

    # ── Prompt enhancement ────────────────────────────────────────────────

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "field, limit",
        [
            ("message", 5_000),
            ("context_type", 50),
            ("additional_context", 10_000),
            ("language", 50),
        ],
    )
    async def test_enhance_prompt_oversized_field(self, client, field, limit):
        """Oversized field on /enhance-prompt → 422."""
        form = _enhance_prompt_form({field: "x" * (limit + 1)})
        with patch(
            "routes.generation.prompt_enhancer",
            new=AsyncMock(return_value="enhanced"),
        ):
            resp = await client.post("/enhance-prompt", data=form)
        assert (
            resp.status_code == 422
        ), f"Expected 422 for {field} ({limit + 1} chars), got {resp.status_code}"

    # ── Cross-endpoint: message field is the primary attack vector ────────

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", list(ENDPOINTS.keys()))
    async def test_100k_message_rejected_across_all_endpoints(self, client, endpoint):
        """A 100 KB message (well above 5000 chars) is rejected on every generator."""
        form_builder, gen_target = ENDPOINTS[endpoint]
        form = form_builder({"message": "A" * 100_000})
        with patch(gen_target, side_effect=_canary_generator):
            resp = await client.post(endpoint, data=form)
        assert (
            resp.status_code == 422
        ), f"Expected 422 on {endpoint} for 100K message, got {resp.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 2. At-boundary values → accepted (positive control)
# ═══════════════════════════════════════════════════════════════════════════


class TestBoundaryAcceptance:
    """
    Values that are exactly at the ``max_length`` limit should be ACCEPTED
    (not rejected). This ensures the limits are not off-by-one.
    """

    @pytest.mark.asyncio
    async def test_message_at_exact_limit_accepted(self, client):
        """A 5000-char message is at the limit and must be accepted (not 422)."""
        form = _course_outline_form({"message": "A" * 5_000})

        async def _ok_gen(*a, **kw):
            yield {"type": "thread_id", "thread_id": "t-boundary"}
            yield {"type": "result", "data": {"course_title": "Test"}}

        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=_ok_gen,
        ):
            resp = await client.post("/course-outline-generator", data=form)
        assert (
            resp.status_code == 200
        ), f"Expected 200 for exactly-at-limit message, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_topic_at_exact_limit_accepted(self, client):
        """A 500-char topic is at the limit and must be accepted (not 422)."""
        form = _course_outline_form({"topic": "T" * 500})

        async def _ok_gen(*a, **kw):
            yield {"type": "thread_id", "thread_id": "t-boundary2"}
            yield {"type": "result", "data": {"course_title": "Test"}}

        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=_ok_gen,
        ):
            resp = await client.post("/course-outline-generator", data=form)
        assert (
            resp.status_code == 200
        ), f"Expected 200 for exactly-at-limit topic, got {resp.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 3. File upload size enforcement (10 MB limit)
# ═══════════════════════════════════════════════════════════════════════════


class TestFileUploadSizeLimit:
    """
    Files exceeding ``UploadConfig.MAX_FILE_SIZE`` (default 10 MB) must be
    rejected with HTTP 413.  Files under the limit must be accepted.
    """

    @pytest.mark.asyncio
    async def test_file_slightly_above_10mb_rejected(self, client):
        """A 10.1 MB file upload → HTTP 413."""
        size = 10 * 1024 * 1024 + 100 * 1024  # ~10.1 MB
        oversized = b"\x00" * size
        form = _course_outline_form()
        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=form,
                files={"files": ("big.pdf", io.BytesIO(oversized), "application/pdf")},
            )
        assert (
            resp.status_code == 413
        ), f"Expected 413 for ~10.1 MB file, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_file_slightly_below_10mb_accepted(self, client):
        """A 9.9 MB file upload → NOT rejected as oversized."""
        size = 10 * 1024 * 1024 - 100 * 1024  # ~9.9 MB
        under_limit = b"x" * size
        form = _course_outline_form()

        async def _ok_gen(*a, **kw):
            yield {"type": "thread_id", "thread_id": "t-file-ok"}
            yield {"type": "result", "data": {"course_title": "Test"}}

        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=_ok_gen,
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=form,
                files={"files": ("ok.txt", io.BytesIO(under_limit), "text/plain")},
            )
        assert (
            resp.status_code != 413
        ), f"~9.9 MB file should not be rejected as oversized, got {resp.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 4. Invalid enum / structured input fields → HTTP 400
# ═══════════════════════════════════════════════════════════════════════════


class TestInvalidEnumValues:
    """
    Assessment-specific enum fields (``assessment_type``, ``difficulty_level``,
    ``question_type_configs``) must be validated against whitelists and rejected
    with HTTP 400 before the LLM is invoked.
    """

    @pytest.mark.asyncio
    async def test_invalid_assessment_type_rejected(self, client):
        """assessment_type='hacked_type' → 400."""
        form = _assessment_form({"assessment_type": "hacked_type"})
        with patch(
            "routes.generation.run_assessment_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/assessment-generator", data=form)
        assert (
            resp.status_code == 400
        ), f"Expected 400 for invalid assessment_type, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_invalid_difficulty_level_rejected(self, client):
        """difficulty_level='impossible' → 400."""
        form = _assessment_form({"difficulty_level": "impossible"})
        with patch(
            "routes.generation.run_assessment_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/assessment-generator", data=form)
        assert (
            resp.status_code == 400
        ), f"Expected 400 for invalid difficulty_level, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_invalid_question_type_rejected(self, client):
        """question_type='free_form' (not in allowed set) → 400."""
        form = _assessment_form(
            {
                "question_type_configs": json.dumps(
                    [{"question_type": "free_form", "count": 5}]
                )
            }
        )
        with patch(
            "routes.generation.run_assessment_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/assessment-generator", data=form)
        assert (
            resp.status_code == 400
        ), f"Expected 400 for invalid question_type, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_question_count_exceeds_max(self, client):
        """question count > 50 → 400."""
        form = _assessment_form(
            {
                "question_type_configs": json.dumps(
                    [{"question_type": "multiple_choice", "count": 999}]
                )
            }
        )
        with patch(
            "routes.generation.run_assessment_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/assessment-generator", data=form)
        assert (
            resp.status_code == 400
        ), f"Expected 400 for question count > 50, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_malformed_json_key_topics_rejected(self, client):
        """Malformed JSON in key_topics → 400."""
        form = _assessment_form({"key_topics": "not-valid-json{{"})
        with patch(
            "routes.generation.run_assessment_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/assessment-generator", data=form)
        assert (
            resp.status_code == 400
        ), f"Expected 400 for malformed JSON, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_malformed_json_key_points_presentation(self, client):
        """Malformed JSON in key_points on /presentation-generator → 400."""
        form = _presentation_form({"key_points": "{invalid json"})
        with patch(
            "routes.generation.run_presentation_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/presentation-generator", data=form)
        assert (
            resp.status_code == 400
        ), f"Expected 400 for malformed JSON on presentation, got {resp.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 5. Concurrent generation cap → HTTP 429
# ═══════════════════════════════════════════════════════════════════════════


class TestConcurrentGenerationCap:
    """
    A single user may run at most ``MAX_CONCURRENT_GENERATIONS`` (2) parallel
    SSE generation streams.  The third concurrent request must be rejected
    with HTTP 429.

    Note: The concurrency check happens inside ``_guarded_sse_stream``
    (an async generator), which executes *after* ``StreamingResponse`` has
    committed the HTTP 200 status.  Therefore we test the concurrency logic
    directly via ``_acquire_generation_slot`` rather than through the full
    HTTP transport — the important property is that the slot-acquisition
    raises ``HTTPException(429)`` before the LLM generator is ever iterated.
    """

    @pytest.mark.asyncio
    async def test_third_concurrent_slot_raises_429(self):
        """Acquiring a 3rd slot while 2 are active → HTTPException(429)."""
        from fastapi import HTTPException as FastAPIHTTPException
        from routes.generation import (
            _acquire_generation_slot,
            _active_generations,
            _active_generations_lock,
        )
        import time

        user_id = "test-user-concurrency"

        async with _active_generations_lock:
            _active_generations[user_id] = [
                time.monotonic(),
                time.monotonic(),
            ]

        try:
            with pytest.raises(FastAPIHTTPException) as exc_info:
                await _acquire_generation_slot(user_id)
            assert exc_info.value.status_code == 429
            assert "concurrent" in exc_info.value.detail.lower()
        finally:
            async with _active_generations_lock:
                _active_generations.pop(user_id, None)

    @pytest.mark.asyncio
    async def test_slot_acquired_when_under_limit(self):
        """Acquiring a slot when 0 are active → succeeds (no exception)."""
        from routes.generation import (
            _acquire_generation_slot,
            _release_generation_slot,
            _active_generations,
            _active_generations_lock,
        )

        user_id = "test-user-under-limit"

        # Ensure clean state
        async with _active_generations_lock:
            _active_generations.pop(user_id, None)

        try:
            # Should not raise
            await _acquire_generation_slot(user_id)
            async with _active_generations_lock:
                assert len(_active_generations.get(user_id, [])) == 1
        finally:
            async with _active_generations_lock:
                _active_generations.pop(user_id, None)

    @pytest.mark.asyncio
    async def test_expired_slots_are_reclaimed(self):
        """Slots older than MAX_GENERATION_DURATION_SECONDS are auto-evicted."""
        from routes.generation import (
            _acquire_generation_slot,
            _active_generations,
            _active_generations_lock,
            MAX_GENERATION_DURATION_SECONDS,
        )
        import time

        user_id = "test-user-expired"

        # Fill both slots with expired timestamps
        async with _active_generations_lock:
            expired_time = time.monotonic() - MAX_GENERATION_DURATION_SECONDS - 60
            _active_generations[user_id] = [expired_time, expired_time]

        try:
            # Should succeed because expired slots are evicted first
            await _acquire_generation_slot(user_id)
            async with _active_generations_lock:
                # Expired slots removed, only the new one remains
                assert len(_active_generations[user_id]) == 1
        finally:
            async with _active_generations_lock:
                _active_generations.pop(user_id, None)

    @pytest.mark.asyncio
    async def test_guarded_stream_rejects_via_sse_transport(self, client):
        """
        Full integration: saturate slots, then POST → the RuntimeError from
        the aborted streaming response confirms the 429 was raised inside
        the SSE stream before the LLM generator was reached.

        Uses /assessment-generator (least likely to hit rate limiter when
        running the full suite) and patches the rate limiter to avoid
        cross-test interference.
        """
        from routes.generation import (
            _active_generations,
            _active_generations_lock,
        )
        import time

        user_id = "test-user-001"

        async with _active_generations_lock:
            _active_generations[user_id] = [
                time.monotonic(),
                time.monotonic(),
            ]

        try:
            form = _assessment_form()
            # The 429 HTTPException is raised inside the StreamingResponse
            # generator after headers are sent, which the ASGI transport
            # surfaces as a RuntimeError. Catching it proves the guard fired.
            with pytest.raises(RuntimeError, match="response already started"):
                with patch("routes.generation.limiter.limit", return_value=lambda f: f):
                    await client.post("/assessment-generator", data=form)
        finally:
            async with _active_generations_lock:
                _active_generations.pop(user_id, None)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Combination attack: oversized + valid token → still rejected
# ═══════════════════════════════════════════════════════════════════════════


class TestCombinationAttacks:
    """
    Ensure that validation is enforced even for authenticated users —
    a valid auth token does not bypass input length checks.
    """

    @pytest.mark.asyncio
    async def test_authenticated_user_still_rejected_on_oversized_input(self, client):
        """
        An authenticated user (valid token from fixture) sending a 100K
        message still gets 422 — authentication does not bypass validation.
        """
        form = _course_outline_form({"message": "B" * 100_000})
        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/course-outline-generator", data=form)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_all_fields_oversized_simultaneously(self, client):
        """
        Sending ALL fields oversized at once → still 422 (the first field
        to fail triggers validation rejection).
        """
        form = _course_outline_form(
            {
                "message": "x" * 6_000,
                "topic": "x" * 600,
                "language": "x" * 60,
            }
        )
        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=_canary_generator,
        ):
            resp = await client.post("/course-outline-generator", data=form)
        assert resp.status_code == 422


# ===========================================================================
# 6. Rate Limiting (slowapi)
# ===========================================================================


@contextmanager
def _rate_limiter_enabled():
    """Temporarily re-enable the slowapi rate limiter (disabled in conftest)."""
    from rate_limit import limiter

    limiter.enabled = True
    try:
        yield limiter
    finally:
        limiter.enabled = False
        # Reset internal storage so counts don't leak between tests
        try:
            limiter.reset()
        except Exception:
            pass


class TestRateLimiting:
    """
    Verify that slowapi's ``@limiter.limit("10/minute")`` actually rejects
    the 11th request within the same window with HTTP 429.

    The rate limiter is globally disabled in conftest for other tests.
    These tests temporarily re-enable it and target ``/enhance-prompt``
    (lightweight non-streaming endpoint) to avoid side effects.
    """

    @pytest.mark.asyncio
    async def test_rate_limiter_triggers_429_after_limit(self, client):
        """
        Send 12 requests in rapid succession → first 10 should succeed
        (or at least not return 429), the 11th must return 429.
        """
        with _rate_limiter_enabled():
            # Use enhance-prompt: non-streaming, fast, lightweight
            form = {
                "message": "Improve this prompt",
                "context_type": "course_outline",
                "language": "English",
            }

            # Patch the actual implementation so we never call the LLM
            with patch(
                "routes.generation.prompt_enhancer",
                new=AsyncMock(return_value="Enhanced prompt text"),
            ):
                statuses = []
                for _ in range(12):
                    resp = await client.post("/enhance-prompt", data=form)
                    statuses.append(resp.status_code)

            # At least one request should have been rate-limited
            assert (
                429 in statuses
            ), f"Expected at least one 429 in 12 requests, got: {statuses}"
            # The first request should NOT be rate-limited
            assert statuses[0] != 429, "First request should not be rate-limited"

    @pytest.mark.asyncio
    async def test_rate_limiter_returns_json_error_body(self, client):
        """
        When rate-limited, the 429 response should contain a JSON body
        with an error description (slowapi default behavior).
        """
        with _rate_limiter_enabled():
            form = {
                "message": "Improve this prompt",
                "context_type": "course_outline",
                "language": "English",
            }

            with patch(
                "routes.generation.prompt_enhancer",
                new=AsyncMock(return_value="Enhanced prompt text"),
            ):
                last_resp = None
                for _ in range(12):
                    resp = await client.post("/enhance-prompt", data=form)
                    if resp.status_code == 429:
                        last_resp = resp
                        break

            assert last_resp is not None, "Never hit 429 in 12 requests"
            # slowapi returns a JSON body with error detail
            body = last_resp.json()
            assert (
                "error" in body or "detail" in body
            ), f"429 response should contain an error description, got: {body}"
