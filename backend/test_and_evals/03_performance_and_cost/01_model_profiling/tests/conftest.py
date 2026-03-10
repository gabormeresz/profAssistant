"""
Pytest fixtures for Section 3.1 — Model Performance Profiling & Cost Analysis.

Provides:
- sys.path setup for backend imports
- Real API key retrieval (skips if missing)
- Model and graph builder registries
- ``mock_infra_for_module`` context-manager factory that patches
  ``resolve_user_llm_config``, ``conversation_manager``, RAG pipeline,
  and (optionally) MCP tools for each generation module
- Live MCP initialisation fixture for real tool-call benchmarking
- Shared path constants for JSON artifact files

All tests in this directory require a real OPENAI_API_KEY and are
marked with ``@pytest.mark.llm`` (deselected by default).
"""

import json
import os
import sys
import uuid
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Tuple
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
# Load .env so OPENAI_API_KEY / TAVILY_API_KEY are available
# ---------------------------------------------------------------------------
_project_root = Path(BACKEND_DIR).parent
load_dotenv(_project_root / ".env")
load_dotenv(Path(BACKEND_DIR) / ".env")  # fallback

# ---------------------------------------------------------------------------
# Model list — all models being benchmarked
# ---------------------------------------------------------------------------
MODEL_LIST: List[str] = [
    "gpt-4o-mini",
    "gpt-4.1-mini",
    "gpt-5-mini",
    "gpt-5",
    "gpt-5.2",
]

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
TESTS_DIR = Path(__file__).parent
ARTIFACTS_DIR = TESTS_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)
LOGS_DIR = TESTS_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

PROMPT_SET_FILE = TESTS_DIR / "prompt_set_ab.json"
PRICING_FILE = TESTS_DIR / "pricing.json"
BENCHMARK_RAW_FILE = ARTIFACTS_DIR / "benchmark_raw.json"  # legacy combined
ANALYSIS_FILE = ARTIFACTS_DIR / "analysis.json"
REPORT_FILE = ARTIFACTS_DIR / "report.md"


def benchmark_file_for_model(model_name: str) -> Path:
    """Return the per-model benchmark artifact path.

    Example: ``artifacts/benchmark_raw_gpt-4o-mini.json``
    """
    safe = model_name.replace("/", "_")
    return ARTIFACTS_DIR / f"benchmark_raw_{safe}.json"


def discover_model_benchmark_files() -> Dict[str, Path]:
    """Discover all per-model benchmark JSON files in the artifacts dir.

    Returns a dict mapping model name → file path for every file that
    matches the ``benchmark_raw_<model>.json`` pattern.
    """
    found: Dict[str, Path] = {}
    for p in sorted(ARTIFACTS_DIR.glob("benchmark_raw_*.json")):
        stem = p.stem  # e.g. benchmark_raw_gpt-4o-mini
        model = stem.replace("benchmark_raw_", "", 1)
        if model:  # skip empty
            found[model] = p
    return found


# ---------------------------------------------------------------------------
# Graph builder registry
# ---------------------------------------------------------------------------
# Lazy imports — resolved at first call to avoid import-time side effects.

_GRAPH_BUILDERS: Dict[str, Callable] | None = None


def get_graph_builders() -> Dict[str, Callable]:
    """Return a dict mapping module name → graph builder function."""
    global _GRAPH_BUILDERS
    if _GRAPH_BUILDERS is None:
        from agent.course_outline.graph import build_course_outline_graph
        from agent.lesson_plan.graph import build_lesson_plan_graph
        from agent.presentation.graph import build_presentation_graph
        from agent.assessment.graph import build_assessment_graph

        _GRAPH_BUILDERS = {
            "course_outline": build_course_outline_graph,
            "lesson_plan": build_lesson_plan_graph,
            "presentation": build_presentation_graph,
            "assessment": build_assessment_graph,
        }
    return _GRAPH_BUILDERS


# ---------------------------------------------------------------------------
# Module → patch-target mappings
# ---------------------------------------------------------------------------
# Each module needs its own evaluation / response / initialize_conversation
# patch targets.  Base generate & refine are shared across all modules.

_MODULE_PATCH_TARGETS: Dict[str, Dict[str, List[str]]] = {
    "course_outline": {
        "resolve_user_llm_config": [
            "agent.base.nodes.generate.resolve_user_llm_config",
            "agent.base.nodes.refine.resolve_user_llm_config",
            "agent.course_outline.nodes.evaluation.resolve_user_llm_config",
            "agent.course_outline.nodes.response.resolve_user_llm_config",
        ],
        "conversation_manager": [
            "agent.course_outline.nodes.initialize_conversation.conversation_manager",
        ],
    },
    "lesson_plan": {
        "resolve_user_llm_config": [
            "agent.base.nodes.generate.resolve_user_llm_config",
            "agent.base.nodes.refine.resolve_user_llm_config",
            "agent.lesson_plan.nodes.evaluation.resolve_user_llm_config",
            "agent.lesson_plan.nodes.response.resolve_user_llm_config",
        ],
        "conversation_manager": [
            "agent.lesson_plan.nodes.initialize_conversation.conversation_manager",
        ],
    },
    "presentation": {
        "resolve_user_llm_config": [
            "agent.base.nodes.generate.resolve_user_llm_config",
            "agent.base.nodes.refine.resolve_user_llm_config",
            "agent.presentation.nodes.evaluation.resolve_user_llm_config",
            "agent.presentation.nodes.response.resolve_user_llm_config",
        ],
        "conversation_manager": [
            "agent.presentation.nodes.initialize_conversation.conversation_manager",
        ],
    },
    "assessment": {
        "resolve_user_llm_config": [
            "agent.base.nodes.generate.resolve_user_llm_config",
            "agent.base.nodes.refine.resolve_user_llm_config",
            "agent.assessment.nodes.evaluation.resolve_user_llm_config",
            "agent.assessment.nodes.response.resolve_user_llm_config",
        ],
        "conversation_manager": [
            "agent.assessment.nodes.initialize_conversation.conversation_manager",
        ],
    },
}


def mock_infra_for_module(
    api_key: str,
    model_name: str,
    module: str,
    *,
    use_live_mcp: bool = True,
):
    """
    Return a context manager that patches infrastructure for *module*.

    Parameters
    ----------
    api_key : str
        Real OpenAI API key.
    model_name : str
        Model id to inject via the ``resolve_user_llm_config`` mock.
    module : str
        One of ``course_outline``, ``lesson_plan``, ``presentation``,
        ``assessment``.
    use_live_mcp : bool
        If *True* (default), do **not** mock ``mcp_manager`` — MCP tools
        are available via the live server.  If *False*, stub out tools
        with an empty list (faster, offline).
    """
    targets = _MODULE_PATCH_TARGETS[module]

    llm_mock = AsyncMock(return_value=(api_key, model_name))

    # --- conversation_manager mock ---
    conv_mock = AsyncMock()
    # Cover all possible module-specific methods
    for attr in (
        "create_course_outline",
        "create_lesson_plan",
        "create_presentation",
        "create_assessment",
        "increment_message_count",
        "get_conversation",
    ):
        setattr(conv_mock, attr, AsyncMock(return_value=None))

    # --- RAG pipeline mock (no uploaded documents in benchmarks) ---
    rag_mock = AsyncMock()
    rag_mock.list_documents = AsyncMock(return_value=[])
    rag_mock.ingest_documents = AsyncMock(return_value=[])

    patches = []

    # resolve_user_llm_config
    for target in targets["resolve_user_llm_config"]:
        patches.append(patch(target, llm_mock))

    # conversation_manager
    for target in targets["conversation_manager"]:
        patches.append(patch(target, conv_mock))

    # RAG pipeline (shared paths)
    patches.append(
        patch(
            "agent.base.nodes.ingest_documents.get_rag_pipeline",
            return_value=rag_mock,
        )
    )
    patches.append(
        patch(
            "agent.base.nodes.ingest_documents.get_api_key_for_user",
            AsyncMock(return_value=api_key),
        )
    )

    # MCP: only mock if explicitly asked for offline mode
    if not use_live_mcp:
        mcp_mock = MagicMock()
        mcp_mock.get_tools.return_value = []
        patches.append(patch("agent.tool_config.mcp_manager", mcp_mock))

    @contextmanager
    def _ctx():
        stack = [p.start() for p in patches]
        try:
            yield llm_mock
        finally:
            for p in patches:
                p.stop()

    return _ctx()


# ---------------------------------------------------------------------------
# Input state builder
# ---------------------------------------------------------------------------


def build_input_state(prompt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a prompt_set_ab entry into the ``input_state`` dict expected
    by the corresponding module's graph.

    A fresh ``thread_id`` is generated for each run.
    """
    inp = dict(prompt["input"])
    inp["thread_id"] = str(uuid.uuid4())
    inp["is_first_call"] = True
    inp["user_id"] = "bench-user-001"
    inp["file_contents"] = inp.get("file_contents", [])
    return inp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def real_api_key() -> str:
    """Return the real OPENAI_API_KEY or skip the entire session."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set — skipping benchmark tests")
    return key


@pytest.fixture(scope="session")
async def live_mcp():
    """
    Initialize the real MCP client (Wikipedia + Tavily) once per session.

    The singleton is reset first to ensure a clean connection, then
    ``initialize()`` connects to the configured MCP servers.  Tools become
    available via ``mcp_manager.get_tools()`` for the entire session.
    Cleans up on teardown.
    """
    from services.mcp_client import mcp_manager

    # Reset singleton state in case a previous test run left it stale
    mcp_manager._initialized = False
    mcp_manager._tools = None
    mcp_manager._client = None

    await mcp_manager.initialize()

    tool_names = [t.name for t in mcp_manager.get_tools()]
    print(f"\n  [MCP] Initialized with {len(tool_names)} tools: {tool_names}")

    if not tool_names:
        pytest.skip(
            "MCP initialization returned no tools — "
            "ensure Wikipedia MCP (port 8765) and TAVILY_API_KEY are available"
        )

    yield mcp_manager

    await mcp_manager.cleanup()
    print("  [MCP] Cleanup complete")


@pytest.fixture(scope="session")
def prompt_set() -> List[Dict[str, Any]]:
    """Load the benchmark prompt set."""
    with open(PROMPT_SET_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def pricing() -> Dict[str, Any]:
    """Load the pricing configuration."""
    with open(PRICING_FILE, encoding="utf-8") as f:
        data = json.load(f)
    # Strip metadata keys
    return {k: v for k, v in data.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# --model CLI option
# ---------------------------------------------------------------------------


def pytest_addoption(parser):
    parser.addoption(
        "--model",
        action="append",
        default=None,
        help=(
            "Model(s) to benchmark. Can be repeated: "
            "--model gpt-4o-mini --model gpt-5. "
            "Defaults to all models in MODEL_LIST."
        ),
    )


def _selected_models(config) -> List[str]:
    """Return the list of models to benchmark based on --model flag."""
    chosen = config.getoption("model")
    if not chosen:
        return list(MODEL_LIST)
    unknown = [m for m in chosen if m not in MODEL_LIST]
    if unknown:
        raise pytest.UsageError(
            f"Unknown model(s): {unknown}. " f"Available: {MODEL_LIST}"
        )
    return chosen


@pytest.fixture(scope="session")
def selected_models(request) -> List[str]:
    """Return the model(s) selected via --model (or all models)."""
    return _selected_models(request.config)
