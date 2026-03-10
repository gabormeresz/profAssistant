"""
Pytest fixtures for isolated RAG pipeline evaluation.

Session-scoped fixtures ingest each test PDF once, keeping the ChromaDB
instance alive for all queries in the session.  This minimises OpenAI
embedding API calls (and therefore cost).

All tests in this directory require a real OPENAI_API_KEY.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
TESTS_DIR = Path(__file__).parent
ARTIFACTS_DIR = TESTS_DIR / "artifacts"
GROUND_TRUTH_EN = ARTIFACTS_DIR / "ground_truth_en.json"
GROUND_TRUTH_HU = ARTIFACTS_DIR / "ground_truth_hu.json"
PDF_EN = ARTIFACTS_DIR / "test_document_en.pdf"
PDF_HU = ARTIFACTS_DIR / "test_document_hu.pdf"

SESSION_ID = "rag-eval-ground-truth"


# ---------------------------------------------------------------------------
# Session-scoped temp directory for ChromaDB
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def chroma_tmp_dir():
    """Create a temporary directory for ChromaDB that persists for the session."""
    tmp = tempfile.mkdtemp(prefix="rag_eval_")
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Session-scoped RAG pipeline
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def rag_pipeline(chroma_tmp_dir):
    """
    Create a fresh RAGPipeline backed by a temp ChromaDB directory.

    Uses the real OpenAI ``text-embedding-3-small`` model — requires
    ``OPENAI_API_KEY`` in environment.
    """
    import sys

    # Ensure backend root is importable
    backend_dir = str(Path(__file__).resolve().parents[4])
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    from services.rag_pipeline import RAGPipeline

    return RAGPipeline(persist_directory=chroma_tmp_dir)


# ---------------------------------------------------------------------------
# Ingest test documents (once per session)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def ingested_en(rag_pipeline):
    """Ingest the English test PDF and return its IngestedDocument metadata."""
    import sys

    backend_dir = str(Path(__file__).resolve().parents[4])
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    from utils.file_processor import FileProcessor

    text = FileProcessor.extract_text_from_pdf(PDF_EN.read_bytes())
    result = await rag_pipeline.ingest_document(
        content=text,
        filename=PDF_EN.name,
        session_id=SESSION_ID,
    )
    return result


@pytest_asyncio.fixture(scope="session")
async def ingested_hu(rag_pipeline):
    """Ingest the Hungarian test PDF and return its IngestedDocument metadata."""
    import sys

    backend_dir = str(Path(__file__).resolve().parents[4])
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    from utils.file_processor import FileProcessor

    text = FileProcessor.extract_text_from_pdf(PDF_HU.read_bytes())
    result = await rag_pipeline.ingest_document(
        content=text,
        filename=PDF_HU.name,
        session_id=SESSION_ID,
    )
    return result


# ---------------------------------------------------------------------------
# Ground truth data
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def ground_truth_en() -> Dict:
    """Load English ground truth annotations."""
    return json.loads(GROUND_TRUTH_EN.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def ground_truth_hu() -> Dict:
    """Load Hungarian ground truth annotations."""
    return json.loads(GROUND_TRUTH_HU.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Helper: build chunk_id from index
# ---------------------------------------------------------------------------


def chunk_id_from_index(document_id: str, index: int) -> str:
    """Build the chunk ID that RAGPipeline would generate for a given index."""
    return f"{document_id}_chunk_{index}"


def resolve_chunk_ids(document_id: str, indices: List[int]) -> List[str]:
    """Convert a list of chunk indices into full chunk IDs."""
    return [chunk_id_from_index(document_id, idx) for idx in indices]
