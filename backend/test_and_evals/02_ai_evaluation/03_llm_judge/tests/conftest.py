"""
Pytest fixtures for the LLM-as-a-Judge zero-shot quality validation (Section 2.3).

Provides:
- sys.path setup for backend imports
- Real API key retrieval (skips if missing)
- Model configuration constants
- ``resolve_user_llm_config`` patching for graph execution
- Judge model factory for external GPT-5.2 scoring
- Judge message builder reusing the official evaluator rubric
- Shared path constants for JSON artifact files

All tests in this directory require a real OPENAI_API_KEY and are
marked with ``@pytest.mark.llm`` (deselected by default).
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Ensure backend root is importable
# ---------------------------------------------------------------------------
BACKEND_DIR = str(Path(__file__).resolve().parents[4])
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ---------------------------------------------------------------------------
# Load .env so OPENAI_API_KEY is available for all phases.
# ---------------------------------------------------------------------------
_project_root = Path(BACKEND_DIR).parent
load_dotenv(_project_root / ".env")
load_dotenv(Path(BACKEND_DIR) / ".env")  # fallback

# ---------------------------------------------------------------------------
# Model constants
# ---------------------------------------------------------------------------
GENERATION_MODEL = "gpt-4o-mini"
JUDGE_MODEL = "gpt-5.2"

# ---------------------------------------------------------------------------
# Artifact paths (persisted between test phases)
# ---------------------------------------------------------------------------
TESTS_DIR = Path(__file__).parent
ARTIFACTS_DIR = TESTS_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)
LOGS_DIR = TESTS_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
DRAFTS_FILE = ARTIFACTS_DIR / "drafts.json"
JUDGE_RESULTS_FILE = ARTIFACTS_DIR / "judge_results.json"
ANALYSIS_FILE = ARTIFACTS_DIR / "analysis_summary.json"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def real_api_key() -> str:
    """Return the real OPENAI_API_KEY or skip the entire session."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set — skipping LLM judge tests")
    return key


@pytest.fixture(autouse=True)
def mock_resolve_llm_config():
    """
    Patch ``resolve_user_llm_config`` in every module that imports it so
    the generation graph and evaluator node use the real OPENAI_API_KEY
    with the configured generation model.

    Also mocks infrastructure dependencies that the graph nodes call
    but are irrelevant for the judge evaluation (conversation manager,
    MCP tools, RAG pipeline).
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set — skipping LLM judge tests")

    llm_mock = AsyncMock(return_value=(api_key, GENERATION_MODEL))

    # --- conversation_manager (initialize_conversation node) ---
    conv_mock = AsyncMock()
    conv_mock.create_course_outline = AsyncMock(return_value=None)
    conv_mock.increment_message_count = AsyncMock(return_value=None)
    conv_mock.get_conversation = AsyncMock(return_value=None)

    # --- MCP tools (tool_config.get_base_tools) ---
    mcp_mock = MagicMock()
    mcp_mock.get_tools.return_value = []  # no external tools for judge tests

    # --- RAG pipeline (ingest_documents node) ---
    rag_mock = AsyncMock()
    rag_mock.list_documents = AsyncMock(return_value=[])
    rag_mock.ingest_documents = AsyncMock(return_value=[])

    with (
        patch(
            "agent.base.nodes.generate.resolve_user_llm_config",
            llm_mock,
        ),
        patch(
            "agent.course_outline.nodes.evaluation.resolve_user_llm_config",
            llm_mock,
        ),
        patch(
            "agent.base.nodes.refine.resolve_user_llm_config",
            llm_mock,
        ),
        patch(
            "agent.course_outline.nodes.response.resolve_user_llm_config",
            llm_mock,
        ),
        patch(
            "agent.course_outline.nodes.initialize_conversation.conversation_manager",
            conv_mock,
        ),
        patch(
            "agent.tool_config.mcp_manager",
            mcp_mock,
        ),
        patch(
            "agent.base.nodes.ingest_documents.get_rag_pipeline",
            return_value=rag_mock,
        ),
        patch(
            "agent.base.nodes.ingest_documents.get_api_key_for_user",
            AsyncMock(return_value=api_key),
        ),
    ):
        yield llm_mock


# ---------------------------------------------------------------------------
# Judge helpers (used by Phase 2)
# ---------------------------------------------------------------------------


def get_judge_model(api_key: str):
    """
    Create a GPT-5.2 structured-output model that returns ``EvaluationResult``.

    Uses the standard evaluator preset from the app (``purpose="evaluator"``).
    GPT-5.2 is in ``REASONING_MODELS``, so the preset system automatically
    applies ``reasoning_effort="low"`` and strips incompatible params.
    """
    from agent.model import get_structured_output_model
    from schemas.evaluation import EvaluationResult

    return get_structured_output_model(
        EvaluationResult,
        api_key=api_key,
        model_name=JUDGE_MODEL,
        purpose="evaluator",
    )


def build_judge_messages(
    content: str,
    *,
    topic: str,
    number_of_classes: int,
    language: str = "English",
):
    """
    Build the message list for the external judge, reusing the identical
    evaluator system prompt and request format from the production evaluator
    node (``evaluate_outline``).

    This ensures the judge applies the exact same rubric as the internal
    evaluator — the only variable is the model (GPT-5.2 vs gpt-4o-mini).
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    from agent.course_outline.prompts import get_evaluator_system_prompt
    from agent.input_sanitizer import wrap_user_input
    from config import EvaluationConfig

    user_context = f"""Expected Topic: {topic}
Expected Number of Classes: {number_of_classes}"""

    evaluation_request = f"""## Course Outline Evaluation Request

{wrap_user_input(user_context)}

Please evaluate the following course outline against the rubric.
Score each dimension independently, then provide the overall weighted score.

---

## Course Outline to Evaluate

<content_to_evaluate>
{content}
</content_to_evaluate>

---

Provide your evaluation with:
1. Score for each dimension (0.0-1.0)
2. Overall weighted score
3. Verdict (APPROVED if >= {EvaluationConfig.APPROVAL_THRESHOLD}, NEEDS_REFINEMENT otherwise)
4. Brief reasoning
5. 1-3 specific, actionable suggestions if NEEDS_REFINEMENT"""

    return [
        SystemMessage(
            content=get_evaluator_system_prompt(
                language, approval_threshold=EvaluationConfig.APPROVAL_THRESHOLD
            )
        ),
        HumanMessage(content=evaluation_request),
    ]


# ---------------------------------------------------------------------------
# Utility: serialize CourseOutline dict to readable text for fair comparison
# ---------------------------------------------------------------------------


def serialize_course_outline_to_text(outline: dict) -> str:
    """
    Convert a structured ``CourseOutline`` dict (as returned by
    ``final_response``) into readable markdown text suitable for
    the judge to evaluate.
    """
    lines = []
    title = outline.get("course_title", "Untitled Course")
    lines.append(f"# {title}\n")

    for cls in outline.get("classes", []):
        num = cls.get("class_number", "?")
        cls_title = cls.get("class_title", "Untitled")
        lines.append(f"## Class {num}: {cls_title}\n")

        objectives = cls.get("learning_objectives", [])
        if objectives:
            lines.append("### Learning Objectives")
            for obj in objectives:
                lines.append(f"- {obj}")
            lines.append("")

        topics = cls.get("key_topics", [])
        if topics:
            lines.append("### Key Topics")
            for t in topics:
                lines.append(f"- {t}")
            lines.append("")

        activities = cls.get("activities_projects", [])
        if activities:
            lines.append("### Activities & Projects")
            for a in activities:
                lines.append(f"- {a}")
            lines.append("")

    return "\n".join(lines)
