"""
Document ingestion node shared across all generation workflows.

Processes uploaded file contents and stores them in ChromaDB for
retrieval during generation. Uses thread_id as session_id to scope
queries to the current conversation.

After successful ingestion the full document text is stripped from
``file_contents`` — only filenames are retained in state so that
downstream nodes (``build_messages``, ``initialize_conversation``)
can still reference them.  This avoids serialising potentially
megabytes of raw text into the SQLite checkpointer at every
subsequent graph step.
"""

import logging

from services.rag_pipeline import get_rag_pipeline

from ..state import BaseGenerationState

logger = logging.getLogger(__name__)


async def ingest_documents(state: BaseGenerationState) -> dict:
    """
    Ingest uploaded documents into the vector database.

    For follow-up calls without new files, checks if documents were
    previously ingested for this session.

    Args:
        state: The current workflow state.

    Returns:
        Dict with has_ingested_documents flag.
    """
    file_contents = state.get("file_contents")
    thread_id = state["thread_id"]
    rag = get_rag_pipeline()

    if not file_contents:
        # No new files - check if documents were previously ingested for this session
        try:
            existing_docs = await rag.list_documents(session_id=thread_id)
            has_existing = len(existing_docs) > 0
            logger.info(
                f"No new files for thread {thread_id}, existing documents: {len(existing_docs)}"
            )
            return {"has_ingested_documents": has_existing}
        except Exception as e:
            logger.error(f"Failed to check existing documents: {e}")
            return {"has_ingested_documents": False}

    try:
        # Prepare documents for ingestion
        documents = [
            {"content": f["content"], "filename": f["filename"]}
            for f in file_contents
            if f.get("content", "").strip()
        ]

        if documents:
            results = await rag.ingest_documents(
                documents=documents,
                session_id=thread_id,
            )
            logger.info(
                f"Ingested {len(results)} documents "
                f"({sum(r.chunk_count for r in results)} chunks) for thread {thread_id}"
            )
            # Strip full document text from state — only keep filenames.
            # Content is now in ChromaDB; downstream nodes only need filenames.
            stripped = [
                {"filename": f.get("filename", "unknown")} for f in file_contents
            ]
            return {"has_ingested_documents": True, "file_contents": stripped}
        else:
            # No valid new content - check for existing documents
            existing_docs = await rag.list_documents(session_id=thread_id)
            has_existing = len(existing_docs) > 0
            logger.debug(
                f"No valid content to ingest for thread {thread_id}, "
                f"existing documents: {len(existing_docs)}"
            )
            return {"has_ingested_documents": has_existing}

    except Exception as e:
        logger.error(f"Failed to ingest documents: {e}")
        # Don't fail the workflow, just log the error
        return {"has_ingested_documents": False}
