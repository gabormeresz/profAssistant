#!/usr/bin/env python3
"""
Chunk Dump Generator for RAG Evaluation.

Step 1 of the two-step ground truth workflow:
  1. Ingest each test PDF into a fresh, temporary ChromaDB instance.
  2. Dump all chunks with their IDs, indices, and content to JSON files.

The resulting chunk dumps (``chunks_en.json``, ``chunks_hu.json``) must then
be **manually reviewed** to create the ground truth files
(``ground_truth_en.json``, ``ground_truth_hu.json``) with queries and their
corresponding ``relevant_chunk_indices``.

This script uses the real RAGPipeline (with real OpenAI embeddings) so that
chunk IDs match exactly what the test suite will produce.

All output is written to the ``artifacts/`` directory.

Usage:
    cd backend
    python test_and_evals/02_ai_evaluation/01_isolated_rag/tests/generate_ground_truth.py

Requires:
    OPENAI_API_KEY in environment or .env
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

# Ensure backend is on the path
BACKEND_DIR = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(BACKEND_DIR))

from services.rag_pipeline import RAGPipeline
from utils.file_processor import FileProcessor

TESTS_DIR = Path(__file__).parent
ARTIFACTS_DIR = TESTS_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)
SESSION_ID = "rag-eval-ground-truth"


async def dump_chunks_for_document(pdf_path: Path, output_path: Path) -> None:
    """Ingest a PDF and dump all resulting chunks to a JSON file."""

    print(f"\n{'='*60}")
    print(f"  Processing: {pdf_path.name}")
    print(f"{'='*60}")

    # Read PDF bytes and extract text
    file_bytes = pdf_path.read_bytes()
    text_content = FileProcessor.extract_text_from_pdf(file_bytes)
    print(f"  Extracted text: {len(text_content):,} characters")

    # Create a temporary ChromaDB directory for isolation
    with tempfile.TemporaryDirectory(prefix="rag_eval_") as tmp_dir:
        pipeline = RAGPipeline(persist_directory=tmp_dir)

        # Ingest
        result = await pipeline.ingest_document(
            content=text_content,
            filename=pdf_path.name,
            session_id=SESSION_ID,
        )
        print(f"  Ingested: {result.chunk_count} chunks, doc_id={result.document_id}")

        # Fetch all chunks from the collection
        all_data = pipeline.collection.get(
            where={"document_id": result.document_id},
            include=["documents", "metadatas"],
        )

        chunks = []
        for i, chunk_id in enumerate(all_data["ids"]):
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "chunk_index": all_data["metadatas"][i].get("chunk_index", i),
                    "content": all_data["documents"][i],
                    "metadata": {
                        k: v
                        for k, v in all_data["metadatas"][i].items()
                        if k
                        in (
                            "document_id",
                            "filename",
                            "session_id",
                            "chunk_index",
                            "total_chunks",
                        )
                    },
                }
            )

        # Sort by chunk_index for readability
        chunks.sort(key=lambda c: c["chunk_index"])

        dump = {
            "source_file": pdf_path.name,
            "document_id": result.document_id,
            "total_chunks": result.chunk_count,
            "total_characters": result.total_characters,
            "session_id": SESSION_ID,
            "chunks": chunks,
        }

        output_path.write_text(
            json.dumps(dump, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"  Dumped to: {output_path}")
        print(f"  Chunks: {len(chunks)}")

        # Show a preview
        for c in chunks[:3]:
            preview = c["content"][:80].replace("\n", " ")
            print(f"    [{c['chunk_index']:2d}] {preview}...")
        if len(chunks) > 3:
            print(f"    ... and {len(chunks) - 3} more chunks")


async def main():
    print("RAG Evaluation — Ground Truth Chunk Dump")
    print("=" * 60)
    print(f"Session ID: {SESSION_ID}")
    print(f"Output dir: {ARTIFACTS_DIR}")

    en_pdf = ARTIFACTS_DIR / "test_document_en.pdf"
    hu_pdf = ARTIFACTS_DIR / "test_document_hu.pdf"

    if not en_pdf.exists() or not hu_pdf.exists():
        print("\nERROR: Test PDFs not found. Run generate_test_pdfs.py first.")
        sys.exit(1)

    await dump_chunks_for_document(en_pdf, ARTIFACTS_DIR / "chunks_en.json")
    await dump_chunks_for_document(hu_pdf, ARTIFACTS_DIR / "chunks_hu.json")

    print(f"\n{'='*60}")
    print(
        "Done. Review artifacts/chunks_en.json and artifacts/chunks_hu.json, then use"
    )
    print("the chunk_ids to populate ground_truth_en.json and ground_truth_hu.json.")


if __name__ == "__main__":
    asyncio.run(main())
