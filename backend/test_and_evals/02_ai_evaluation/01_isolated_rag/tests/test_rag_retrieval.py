"""
Isolated RAG Pipeline Retrieval Tests.

Measures ChromaDB retrieval quality (Hit Rate@5, MRR@5) against
synthetic test documents using real OpenAI embeddings.

All tests require OPENAI_API_KEY — marked with ``@pytest.mark.llm``.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest
import pytest_asyncio

from conftest import SESSION_ID, resolve_chunk_ids

# ---------------------------------------------------------------------------
# Mark entire module as LLM (needs real OpenAI API)
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.llm

TESTS_DIR = Path(__file__).parent
K = 5  # top-k for retrieval


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def compute_hit(retrieved_ids: List[str], relevant_ids: List[str]) -> bool:
    """Check if any retrieved chunk is in the relevant set."""
    return bool(set(retrieved_ids) & set(relevant_ids))


def compute_reciprocal_rank(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
    """Return 1/rank of the first relevant chunk, or 0.0 if none found."""
    relevant_set = set(relevant_ids)
    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_set:
            return 1.0 / rank
    return 0.0


# ---------------------------------------------------------------------------
# Result collector (session-scoped)
# ---------------------------------------------------------------------------

# Module-level result storage — collected across all parametrized tests
_results: Dict[str, List[Dict[str, Any]]] = {"en": [], "hu": []}


# ---------------------------------------------------------------------------
# English query tests
# ---------------------------------------------------------------------------


def _en_query_ids():
    """Load English query IDs for parametrize."""
    gt = json.loads((TESTS_DIR / "ground_truth_en.json").read_text(encoding="utf-8"))
    return [q["id"] for q in gt["queries"]]


def _en_query_by_id(query_id: str) -> Dict:
    """Look up an English query by ID."""
    gt = json.loads((TESTS_DIR / "ground_truth_en.json").read_text(encoding="utf-8"))
    for q in gt["queries"]:
        if q["id"] == query_id:
            return q
    raise KeyError(f"Query {query_id} not found")


@pytest.mark.parametrize("query_id", _en_query_ids())
async def test_en_retrieval(query_id, rag_pipeline, ingested_en, ground_truth_en):
    """Test retrieval quality for a single English query."""
    query = _en_query_by_id(query_id)
    doc_id = ground_truth_en["document_id"]
    relevant_ids = resolve_chunk_ids(doc_id, query["relevant_chunk_indices"])

    # Execute retrieval
    results = await rag_pipeline.query(
        query_text=query["query"],
        n_results=K,
        session_id=SESSION_ID,
        min_similarity=0.3,
    )

    retrieved_ids = [r["chunk_id"] for r in results]
    retrieved_scores = [r["similarity_score"] for r in results]

    hit = compute_hit(retrieved_ids, relevant_ids)
    rr = compute_reciprocal_rank(retrieved_ids, relevant_ids)

    result_entry = {
        "query_id": query_id,
        "query_text": query["query"],
        "category": query["category"],
        "hit": hit,
        "reciprocal_rank": rr,
        "retrieved_chunk_ids": retrieved_ids,
        "relevant_chunk_ids": relevant_ids,
        "top_similarities": retrieved_scores,
    }
    _results["en"].append(result_entry)

    # We don't assert pass/fail on individual queries — aggregate metrics
    # are what matter. But we record everything.


# ---------------------------------------------------------------------------
# Hungarian query tests
# ---------------------------------------------------------------------------


def _hu_query_ids():
    """Load Hungarian query IDs for parametrize."""
    gt = json.loads((TESTS_DIR / "ground_truth_hu.json").read_text(encoding="utf-8"))
    return [q["id"] for q in gt["queries"]]


def _hu_query_by_id(query_id: str) -> Dict:
    """Look up a Hungarian query by ID."""
    gt = json.loads((TESTS_DIR / "ground_truth_hu.json").read_text(encoding="utf-8"))
    for q in gt["queries"]:
        if q["id"] == query_id:
            return q
    raise KeyError(f"Query {query_id} not found")


@pytest.mark.parametrize("query_id", _hu_query_ids())
async def test_hu_retrieval(query_id, rag_pipeline, ingested_hu, ground_truth_hu):
    """Test retrieval quality for a single Hungarian query."""
    query = _hu_query_by_id(query_id)
    doc_id = ground_truth_hu["document_id"]
    relevant_ids = resolve_chunk_ids(doc_id, query["relevant_chunk_indices"])

    results = await rag_pipeline.query(
        query_text=query["query"],
        n_results=K,
        session_id=SESSION_ID,
        min_similarity=0.3,
    )

    retrieved_ids = [r["chunk_id"] for r in results]
    retrieved_scores = [r["similarity_score"] for r in results]

    hit = compute_hit(retrieved_ids, relevant_ids)
    rr = compute_reciprocal_rank(retrieved_ids, relevant_ids)

    result_entry = {
        "query_id": query_id,
        "query_text": query["query"],
        "category": query["category"],
        "hit": hit,
        "reciprocal_rank": rr,
        "retrieved_chunk_ids": retrieved_ids,
        "relevant_chunk_ids": relevant_ids,
        "top_similarities": retrieved_scores,
    }
    _results["hu"].append(result_entry)


# ---------------------------------------------------------------------------
# Aggregate metrics (runs after all parametrized tests)
# ---------------------------------------------------------------------------


def _compute_aggregate(results: List[Dict]) -> Dict[str, Any]:
    """Compute Hit Rate, MRR, and per-category breakdowns."""
    if not results:
        return {"hit_rate": 0.0, "mrr": 0.0, "total": 0}

    hits = sum(1 for r in results if r.get("hit", False))
    rrs = [r.get("reciprocal_rank", 0.0) for r in results]

    hit_rate = hits / len(results)
    mrr = sum(rrs) / len(rrs)

    # Per-category breakdown
    categories = set(r["category"] for r in results)
    by_category = {}
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        cat_hits = sum(1 for r in cat_results if r.get("hit", False))
        cat_rrs = [r.get("reciprocal_rank", 0.0) for r in cat_results]
        by_category[cat] = {
            "count": len(cat_results),
            "hit_rate": cat_hits / len(cat_results) if cat_results else 0.0,
            "mrr": sum(cat_rrs) / len(cat_rrs) if cat_rrs else 0.0,
        }

    return {
        "hit_rate": round(hit_rate, 4),
        "mrr": round(mrr, 4),
        "total_queries": len(results),
        "hits": hits,
        "by_category": by_category,
    }


def test_aggregate_and_export():
    """
    Aggregate all per-query results and write rag_results.json.

    This test runs last (alphabetically after test_en_* and test_hu_*)
    and produces the final evaluation report.
    """
    from config import RAGConfig

    en_agg = _compute_aggregate(_results["en"])
    hu_agg = _compute_aggregate(_results["hu"])

    # Combined aggregate
    all_results = _results["en"] + _results["hu"]
    all_hits = sum(1 for r in all_results if r.get("hit", False))
    all_rrs = [r.get("reciprocal_rank", 0.0) for r in all_results]

    combined = {
        "hit_rate": round(all_hits / len(all_results), 4) if all_results else 0.0,
        "mrr": round(sum(all_rrs) / len(all_rrs), 4) if all_rrs else 0.0,
        "total_queries": len(all_results),
    }

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "chunk_size": RAGConfig.CHUNK_SIZE,
            "chunk_overlap": RAGConfig.CHUNK_OVERLAP,
            "embedding_model": RAGConfig.EMBEDDING_MODEL,
            "k": K,
            "min_similarity": 0.3,
        },
        "combined": combined,
        "english": en_agg,
        "hungarian": hu_agg,
        "per_query_results": {
            "en": _results["en"],
            "hu": _results["hu"],
        },
    }

    artifacts_dir = TESTS_DIR / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    output_path = artifacts_dir / "rag_results.json"
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Print summary to stdout
    print("\n")
    print("=" * 60)
    print("  RAG RETRIEVAL EVALUATION RESULTS")
    print("=" * 60)
    print(
        f"  Config: chunk_size={RAGConfig.CHUNK_SIZE}, overlap={RAGConfig.CHUNK_OVERLAP}, "
        f"model={RAGConfig.EMBEDDING_MODEL}, K={K}"
    )
    print(
        f"  Combined:  Hit Rate@{K} = {combined['hit_rate']:.2%}  |  MRR@{K} = {combined['mrr']:.4f}"
    )
    print(
        f"  English:   Hit Rate@{K} = {en_agg['hit_rate']:.2%}  |  MRR@{K} = {en_agg['mrr']:.4f}"
    )
    print(
        f"  Hungarian: Hit Rate@{K} = {hu_agg['hit_rate']:.2%}  |  MRR@{K} = {hu_agg['mrr']:.4f}"
    )
    print()

    if en_agg.get("by_category"):
        print("  English — by category:")
        for cat, stats in en_agg["by_category"].items():
            print(
                f"    {cat:20s}  HR={stats['hit_rate']:.2%}  MRR={stats['mrr']:.4f}  (n={stats['count']})"
            )

    if hu_agg.get("by_category"):
        print("  Hungarian — by category:")
        for cat, stats in hu_agg["by_category"].items():
            print(
                f"    {cat:20s}  HR={stats['hit_rate']:.2%}  MRR={stats['mrr']:.4f}  (n={stats['count']})"
            )

    print()
    print(f"  Results written to: {output_path}")
    print("=" * 60)

    # Assertions — these define success/failure
    assert (
        en_agg["hit_rate"] >= 0.5
    ), f"English Hit Rate@{K} = {en_agg['hit_rate']:.2%} — below 50% threshold"
    assert (
        hu_agg["hit_rate"] >= 0.5
    ), f"Hungarian Hit Rate@{K} = {hu_agg['hit_rate']:.2%} — below 50% threshold"
    assert (
        combined["hit_rate"] >= 0.5
    ), f"Combined Hit Rate@{K} = {combined['hit_rate']:.2%} — below 50% threshold"
