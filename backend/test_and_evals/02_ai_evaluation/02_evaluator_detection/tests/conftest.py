"""
Pytest fixtures for the Evaluator Error Detection Rate tests.

Provides:
- sys.path setup for backend imports
- ``resolve_user_llm_config`` mock returning real API key + gpt-4o-mini
- Shared state builder for detection-rate tests

All tests in this directory require a real OPENAI_API_KEY and are
marked with ``@pytest.mark.llm`` (deselected by default).
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Ensure backend root is importable
# ---------------------------------------------------------------------------
BACKEND_DIR = str(Path(__file__).resolve().parents[4])
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ---------------------------------------------------------------------------
# Model used for evaluator detection tests
# ---------------------------------------------------------------------------
TARGET_MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Core fixture: patch resolve_user_llm_config everywhere it's imported
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_resolve_llm_config():
    """
    Patch ``resolve_user_llm_config`` in the evaluation module so that
    the evaluator node uses the real OPENAI_API_KEY from the environment
    with gpt-4o-mini.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set — skipping LLM test")

    mock = AsyncMock(return_value=(api_key, TARGET_MODEL))

    with patch(
        "agent.course_outline.nodes.evaluation.resolve_user_llm_config",
        mock,
    ):
        yield mock


# ---------------------------------------------------------------------------
# Shared state builder for the evaluator (detection-rate tests)
# ---------------------------------------------------------------------------
@pytest.fixture()
def evaluator_state_factory():
    """
    Return a callable that builds a minimal ``CourseOutlineState``-
    compatible dict for calling ``evaluate_outline`` directly.

    Usage::

        state = evaluator_state_factory(
            content="…flawed course outline…",
            topic="Intro to CS",
            number_of_classes=6,
        )
        result = await evaluate_outline(state)
    """
    from langchain_core.messages import AIMessage

    def _build(
        content: str,
        *,
        topic: str = "Introduction to Computer Science",
        number_of_classes: int = 6,
        language: str = "English",
    ) -> dict:
        return {
            "messages": [],
            "agent_response": AIMessage(content=content),
            "evaluation_count": 0,
            "evaluation_history": [],
            "current_score": None,
            "topic": topic,
            "number_of_classes": number_of_classes,
            "language": language,
            "user_id": "test-user-eval",
            "thread_id": "test-thread-eval",
            "is_first_call": True,
            "has_ingested_documents": False,
            "file_contents": None,
            "message": None,
            "final_response": None,
            "error": None,
        }

    return _build
