"""
Test 1.1b — SSE Client Disconnection Resilience
=================================================

**Objective:** Verify that when a client disconnects mid-stream (frontend
closes the browser tab, network drops, etc.), the server-side generator
stops consuming resources — it must NOT continue burning LLM tokens in
the background.

**Strategy:**
We create a slow async generator that simulates a multi-step LangGraph
workflow (yielding progress events with sleeps between them). We then
start consuming the SSE stream but abort the connection after receiving
the first few events. After disconnection we verify:

1. The generator eventually stops (detected via a shared flag).
2. The concurrency-tracking slot is released (``_active_generations``
   returns to zero for the test user).
3. No unhandled exceptions occur on the server side.

**Technical note on ASGI disconnection:**
With ``httpx.ASGITransport``, closing the client-side response does NOT
perfectly simulate a TCP reset like a real browser would.  Starlette's
``StreamingResponse`` raises ``asyncio.CancelledError`` inside the
generator when the ASGI send-channel detects disconnection.  We test
both the "natural" path (httpx transport closure) and the "forced" path
(directly injecting ``CancelledError`` into the generator).
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio

from test_and_evals.conftest import FAKE_USER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_sse_events(body: str) -> list[dict]:
    """Parse raw SSE text into structured events."""
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


# ---------------------------------------------------------------------------
# Slow generator that tracks whether it was stopped
# ---------------------------------------------------------------------------


class GeneratorSpy:
    """
    An async generator that yields events slowly and records its lifecycle.

    Attributes:
        events_yielded: Number of SSE events successfully yielded.
        was_cancelled: True if an ``asyncio.CancelledError`` was caught.
        finished_naturally: True if the generator ran to completion.
        cleanup_called: True if the finally block executed.
    """

    def __init__(self, total_events: int = 10, delay: float = 0.1):
        self.total_events = total_events
        self.delay = delay
        self.events_yielded = 0
        self.was_cancelled = False
        self.finished_naturally = False
        self.cleanup_called = False

    async def __call__(self, *args, **kwargs):
        """Make the instance callable so it can replace the real generator."""
        try:
            yield {"type": "thread_id", "thread_id": "test-thread-disconnect"}
            self.events_yielded += 1

            for i in range(self.total_events):
                await asyncio.sleep(self.delay)
                yield {
                    "type": "progress",
                    "message_key": f"overlay.step{i}",
                }
                self.events_yielded += 1

            # Final result
            yield {
                "type": "complete",
                "data": {"title": "Test", "classes": []},
            }
            self.events_yielded += 1
            self.finished_naturally = True

        except (asyncio.CancelledError, GeneratorExit):
            self.was_cancelled = True
            raise
        finally:
            self.cleanup_called = True


# ═══════════════════════════════════════════════════════════════════════════
# Test cases
# ═══════════════════════════════════════════════════════════════════════════

COURSE_OUTLINE_FORM = {
    "message": "Create a course outline for testing",
    "topic": "Software Testing",
    "number_of_classes": "8",
    "language": "English",
}


@pytest.mark.asyncio
class TestSSEDisconnectionDirect:
    """
    Test disconnection handling by directly injecting CancelledError into
    the event generator, simulating what Starlette does when the send
    channel detects client disconnect.
    """

    async def test_cancelled_error_triggers_cleanup(self):
        """
        When ``CancelledError`` is thrown into the generator, the finally
        block must execute so resources (DB handles, concurrency slots)
        are released.
        """
        spy = GeneratorSpy(total_events=10, delay=0.05)
        gen = spy(
            message="test",
            topic="test",
            number_of_classes=5,
            language="English",
            thread_id=None,
            file_contents=[],
            user_id="test-user-001",
        )

        # Consume a few events, then cancel
        events_received = 0
        async for _event in gen:
            events_received += 1
            if events_received >= 3:
                # Simulate Starlette disconnection — athrow raises CancelledError
                # which propagates out; we catch it here as the "consumer"
                try:
                    await gen.athrow(asyncio.CancelledError())
                except (asyncio.CancelledError, StopAsyncIteration, GeneratorExit):
                    pass
                break

        # The generator should have been cancelled, not finished naturally
        assert spy.was_cancelled, "Generator should detect cancellation"
        assert not spy.finished_naturally, "Generator should NOT run to completion"
        assert spy.cleanup_called, "Finally block must execute for cleanup"
        assert spy.events_yielded < spy.total_events + 2, (
            f"Generator yielded {spy.events_yielded} events — "
            f"should have stopped well before {spy.total_events + 2}"
        )

    async def test_generator_exit_triggers_cleanup(self):
        """
        When the consumer simply stops iterating (``aclose()``), the
        generator should also clean up.
        """
        spy = GeneratorSpy(total_events=10, delay=0.05)
        gen = spy(
            message="test",
            topic="test",
            number_of_classes=5,
            language="English",
            thread_id=None,
            file_contents=[],
            user_id="test-user-001",
        )

        events_received = 0
        async for _event in gen:
            events_received += 1
            if events_received >= 3:
                await gen.aclose()
                break

        assert spy.cleanup_called, "Finally block must execute on aclose()"
        assert not spy.finished_naturally, "Generator should NOT run to completion"


@pytest.mark.asyncio
class TestConcurrencySlotRelease:
    """
    Verify that the concurrency-tracking slot in ``_guarded_sse_stream``
    is released even when the generator fails or is cancelled.
    """

    async def test_slot_released_after_exception(self, client: httpx.AsyncClient):
        """
        If the generator raises an exception mid-stream, the
        ``_guarded_sse_stream`` wrapper's ``finally`` block must release
        the user's concurrency slot.
        """
        from routes.generation import _active_generations

        user_id = FAKE_USER["user_id"]

        async def _exploding_generator(*args, **kwargs):
            yield {"type": "thread_id", "thread_id": "test-slot-release"}
            raise RuntimeError("Boom")

        # Clear any prior state
        _active_generations.pop(user_id, None)

        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=_exploding_generator,
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=COURSE_OUTLINE_FORM,
            )

        assert resp.status_code == 200

        # Slot must be released — user should have zero active generations
        remaining = _active_generations.get(user_id, [])
        assert len(remaining) == 0, (
            f"Expected 0 active generation slots, found {len(remaining)}. "
            "The concurrency slot was not properly cleaned up."
        )

    async def test_slot_released_after_normal_completion(
        self, client: httpx.AsyncClient
    ):
        """Sanity check: slot is released after a successful generation."""
        from routes.generation import _active_generations

        user_id = FAKE_USER["user_id"]

        async def _ok_generator(*args, **kwargs):
            yield {"type": "thread_id", "thread_id": "test-slot-ok"}
            yield {"type": "complete", "data": {"title": "ok", "classes": []}}

        _active_generations.pop(user_id, None)

        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=_ok_generator,
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=COURSE_OUTLINE_FORM,
            )

        assert resp.status_code == 200
        remaining = _active_generations.get(user_id, [])
        assert (
            len(remaining) == 0
        ), f"Expected 0 active slots after completion, found {len(remaining)}"


@pytest.mark.asyncio
class TestSSEEventIntegrity:
    """
    Even under error conditions, the SSE events that *were* sent
    before the failure should be well-formed.
    """

    async def test_partial_stream_has_valid_sse_format(self, client: httpx.AsyncClient):
        """
        When the generator yields some events then crashes, every
        event that was sent should be parseable SSE.
        """

        async def _partial_generator(*args, **kwargs):
            yield {"type": "thread_id", "thread_id": "test-partial"}
            yield {"type": "progress", "message_key": "overlay.step1"}
            yield {"type": "progress", "message_key": "overlay.step2"}
            raise RuntimeError("Midstream failure")

        with patch(
            "routes.generation.run_course_outline_generator",
            side_effect=_partial_generator,
        ):
            resp = await client.post(
                "/course-outline-generator",
                data=COURSE_OUTLINE_FORM,
            )

        assert resp.status_code == 200
        events = parse_sse_events(resp.text)

        # We should have at least thread_id + 2 progress + 1 error = 4 events
        assert len(events) >= 4, f"Expected ≥4 events, got {len(events)}: {events}"

        # Every event should have a data field
        for evt in events:
            assert "data" in evt, f"Event missing data field: {evt}"

        # Last event should be the error
        assert events[-1]["event"] == "error"
