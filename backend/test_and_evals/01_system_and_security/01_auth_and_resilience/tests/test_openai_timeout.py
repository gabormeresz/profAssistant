"""
Test 1.1a — OpenAI Timeout Resilience
======================================

**Objective:** Verify that the backend does NOT crash and returns a proper
SSE error event when the OpenAI API call raises a timeout or APIError.

**Strategy:**
We mock ``run_course_outline_generator`` (the async generator that wraps the
full LangGraph workflow) so it yields a ``thread_id`` event and then raises
an ``openai.APITimeoutError``.  The route's ``except`` clause in
``_course_outline_event_generator`` should catch this via ``classify_error``
and emit an SSE ``error`` event with a frontend-translatable message key.

We test multiple failure modes:
1. ``openai.APITimeoutError``   → should yield ``errors.generationFailed``
2. ``openai.APIStatusError``    → 5xx → should yield ``errors.openaiUnavailable``
3. ``openai.AuthenticationError`` → should yield ``errors.invalidApiKey``
4. ``openai.RateLimitError``    → quota → should yield ``errors.insufficientQuota``

All tests assert:
- HTTP 200 (the SSE stream itself starts fine)
- The SSE body contains ``event: error``
- The JSON payload carries the correct ``message_key``
- No unhandled exception / 500 crash
"""

import json
from unittest.mock import AsyncMock, patch

import httpx
import openai
import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_sse_events(body: str) -> list[dict]:
    """
    Parse a raw SSE response body into a list of ``{event, data}`` dicts.

    Handles the standard SSE format:
        event: <name>
        data: <json>

    Lines without an explicit ``event:`` prefix are treated as ``data`` events.
    """
    events = []
    current = {}
    for line in body.splitlines():
        if line.startswith("event:"):
            current["event"] = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            raw = line.split(":", 1)[1].strip()
            try:
                current["data"] = json.loads(raw)
            except json.JSONDecodeError:
                current["data"] = raw
            events.append(current)
            current = {}
    return events


def find_event(events: list[dict], event_type: str) -> dict | None:
    """Return the first SSE event matching *event_type*, or None."""
    return next((e for e in events if e.get("event") == event_type), None)


# ---------------------------------------------------------------------------
# Fake generator helpers
# ---------------------------------------------------------------------------


async def _failing_generator(exc: Exception):
    """
    Simulate a generator that emits a thread_id and then raises *exc*,
    mimicking a failure partway through LangGraph execution.
    """
    yield {"type": "thread_id", "thread_id": "test-thread-timeout"}
    yield {"type": "progress", "message_key": "overlay.initializingConversation"}
    raise exc


# ---------------------------------------------------------------------------
# Course-outline form data shared across tests
# ---------------------------------------------------------------------------
COURSE_OUTLINE_FORM = {
    "message": "Create a course outline for testing",
    "topic": "Software Testing",
    "number_of_classes": "8",
    "language": "English",
}


# ═══════════════════════════════════════════════════════════════════════════
# Test cases
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestOpenAITimeout:
    """The OpenAI client raises ``APITimeoutError`` during generation."""

    async def test_timeout_returns_sse_error_not_500(self, client: httpx.AsyncClient):
        """
        When the OpenAI call times out, the SSE stream must still return
        HTTP 200 (streaming already started) and contain an ``event: error``
        frame — NOT an HTTP 500 or a broken connection.
        """
        exc = openai.APITimeoutError(
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        )

        with patch(
            "routes.generation.run_course_outline_generator",
            return_value=_failing_generator(exc),
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=COURSE_OUTLINE_FORM,
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        events = parse_sse_events(resp.text)
        error_evt = find_event(events, "error")

        assert (
            error_evt is not None
        ), f"No SSE error event found in response. Events: {events}"
        assert error_evt["data"]["message_key"] == "errors.generationFailed"

    async def test_timeout_emits_thread_id_before_error(
        self, client: httpx.AsyncClient
    ):
        """
        The generator yields a ``thread_id`` event first, so the frontend
        can track the conversation even when the generation itself fails.
        """
        exc = openai.APITimeoutError(
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        )

        with patch(
            "routes.generation.run_course_outline_generator",
            return_value=_failing_generator(exc),
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=COURSE_OUTLINE_FORM,
            )

        events = parse_sse_events(resp.text)
        thread_evt = find_event(events, "thread_id")
        assert thread_evt is not None, "thread_id event expected before error"
        assert "thread_id" in thread_evt["data"]


@pytest.mark.asyncio
class TestOpenAIServiceUnavailable:
    """The OpenAI API returns HTTP 500/503 (``APIStatusError``)."""

    async def test_5xx_returns_openai_unavailable_key(self, client: httpx.AsyncClient):
        """
        A 5xx from OpenAI should be classified as ``errors.openaiUnavailable``
        so the frontend can display a meaningful message.
        """
        mock_response = httpx.Response(
            status_code=503,
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        )
        exc = openai.APIStatusError(
            message="Service unavailable",
            response=mock_response,
            body=None,
        )

        with patch(
            "routes.generation.run_course_outline_generator",
            return_value=_failing_generator(exc),
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=COURSE_OUTLINE_FORM,
            )

        assert resp.status_code == 200
        events = parse_sse_events(resp.text)
        error_evt = find_event(events, "error")
        assert error_evt is not None
        assert error_evt["data"]["message_key"] == "errors.openaiUnavailable"


@pytest.mark.asyncio
class TestOpenAIAuthenticationError:
    """An invalid or revoked API key is used."""

    async def test_auth_error_returns_invalid_api_key(self, client: httpx.AsyncClient):
        mock_response = httpx.Response(
            status_code=401,
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        )
        exc = openai.AuthenticationError(
            message="Invalid API key",
            response=mock_response,
            body=None,
        )

        with patch(
            "routes.generation.run_course_outline_generator",
            return_value=_failing_generator(exc),
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=COURSE_OUTLINE_FORM,
            )

        assert resp.status_code == 200
        events = parse_sse_events(resp.text)
        error_evt = find_event(events, "error")
        assert error_evt is not None
        assert error_evt["data"]["message_key"] == "errors.invalidApiKey"


@pytest.mark.asyncio
class TestOpenAIRateLimitQuota:
    """The account has exceeded its billing quota."""

    async def test_quota_exceeded_returns_insufficient_quota(
        self, client: httpx.AsyncClient
    ):
        mock_response = httpx.Response(
            status_code=429,
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        )
        exc = openai.RateLimitError(
            message="You exceeded your current quota",
            response=mock_response,
            body=None,
        )

        with patch(
            "routes.generation.run_course_outline_generator",
            return_value=_failing_generator(exc),
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=COURSE_OUTLINE_FORM,
            )

        assert resp.status_code == 200
        events = parse_sse_events(resp.text)
        error_evt = find_event(events, "error")
        assert error_evt is not None
        assert error_evt["data"]["message_key"] == "errors.insufficientQuota"

    async def test_rate_limited_returns_rate_limited(self, client: httpx.AsyncClient):
        """Pure rate limiting (no quota keywords) → ``errors.rateLimited``."""
        mock_response = httpx.Response(
            status_code=429,
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        )
        exc = openai.RateLimitError(
            message="Rate limit reached for requests",
            response=mock_response,
            body=None,
        )

        with patch(
            "routes.generation.run_course_outline_generator",
            return_value=_failing_generator(exc),
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=COURSE_OUTLINE_FORM,
            )

        assert resp.status_code == 200
        events = parse_sse_events(resp.text)
        error_evt = find_event(events, "error")
        assert error_evt is not None
        assert error_evt["data"]["message_key"] == "errors.rateLimited"


@pytest.mark.asyncio
class TestUnexpectedExceptionFallback:
    """Any unexpected, unclassified exception should still be caught."""

    async def test_generic_exception_returns_generation_failed(
        self, client: httpx.AsyncClient
    ):
        """
        An unforeseen error (e.g. ``RuntimeError``) must NOT crash the
        server. It should fall through to the generic
        ``errors.generationFailed`` message key.
        """
        exc = RuntimeError("Something completely unexpected")

        with patch(
            "routes.generation.run_course_outline_generator",
            return_value=_failing_generator(exc),
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=COURSE_OUTLINE_FORM,
            )

        assert resp.status_code == 200
        events = parse_sse_events(resp.text)
        error_evt = find_event(events, "error")
        assert error_evt is not None
        assert error_evt["data"]["message_key"] == "errors.generationFailed"


@pytest.mark.asyncio
class TestLessonPlanTimeoutResilience:
    """
    Verify the same resilience on the lesson-plan endpoint to confirm
    the error-handling pattern is applied consistently across all SSE routes.
    """

    LESSON_PLAN_FORM = {
        "message": "Create a lesson plan for testing",
        "course_title": "Software Engineering",
        "class_number": "1",
        "class_title": "Introduction to Testing",
        "learning_objectives": '["Understand unit testing"]',
        "key_topics": '["pytest basics"]',
        "activities_projects": '["Write a test suite"]',
        "language": "English",
    }

    async def test_lesson_plan_timeout_returns_sse_error(
        self, client: httpx.AsyncClient
    ):
        exc = openai.APITimeoutError(
            request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        )

        with patch(
            "routes.generation.run_lesson_plan_generator",
            return_value=_failing_generator(exc),
        ):
            resp = await client.post(
                "/lesson-plan-generator",
                data=self.LESSON_PLAN_FORM,
            )

        assert resp.status_code == 200
        events = parse_sse_events(resp.text)
        error_evt = find_event(events, "error")
        assert error_evt is not None
        assert error_evt["data"]["message_key"] == "errors.generationFailed"
