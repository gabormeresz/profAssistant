"""
RAG Pipeline Service for document ingestion and retrieval.

This service handles:
- Document chunking with recursive text splitting
- Vector storage using ChromaDB
- Document retrieval for RAG queries

The service is independent and can be used by agents for dynamic querying.

All public methods are async.  ChromaDB has no native async API in embedded
mode, so every blocking call is wrapped with ``asyncio.to_thread``.
"""

import asyncio
import hashlib
from typing import List, Optional, Dict, Any, cast
from dataclasses import dataclass
from datetime import datetime

import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from config import RAGConfig


@dataclass
class DocumentChunk:
    """Represents a chunk of a document."""

    content: str
    metadata: Dict[str, Any]
    chunk_index: int


@dataclass
class IngestedDocument:
    """Represents an ingested document with its chunks."""

    document_id: str
    filename: str
    chunk_count: int
    total_characters: int
    ingested_at: str


class RAGPipeline:
    """
    RAG Pipeline for document ingestion and retrieval using ChromaDB.

    Features:
    - Recursive text chunking (configurable via RAGConfig)
    - ChromaDB vector storage with persistence
    - Session-based document management
    - Semantic similarity search for retrieval
    """

    def __init__(
        self,
        persist_directory: str = RAGConfig.PERSIST_DIRECTORY,
        collection_name: str = RAGConfig.COLLECTION_NAME,
        chunk_size: int = RAGConfig.CHUNK_SIZE,
        chunk_overlap: int = RAGConfig.CHUNK_OVERLAP,
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        )

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
            ),
        )

        # Default embeddings instance (server-side key from env)
        self._default_embeddings = OpenAIEmbeddings(model=RAGConfig.EMBEDDING_MODEL)

        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )

    # ------------------------------------------------------------------
    #  Private helpers (sync — only called inside to_thread)
    # ------------------------------------------------------------------

    def _get_embeddings(self, api_key: Optional[str] = None) -> OpenAIEmbeddings:
        """Return an OpenAIEmbeddings instance for the given API key.

        If *api_key* is provided, a fresh instance scoped to that key is
        created (so that non-admin users consume their own OpenAI budget).
        Otherwise the default server-side instance is returned.
        """
        if api_key:
            return OpenAIEmbeddings(
                model=RAGConfig.EMBEDDING_MODEL,
                api_key=api_key,
            )
        return self._default_embeddings

    def _generate_document_id(self, content: str, filename: str) -> str:
        """Generate a unique document ID based on content hash and filename."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{filename}_{content_hash}"

    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """Generate a unique chunk ID."""
        return f"{document_id}_chunk_{chunk_index}"

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks using recursive character text splitter."""
        return self.text_splitter.split_text(text)

    def _ingest_document_sync(
        self,
        content: str,
        filename: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
    ) -> IngestedDocument:
        """Synchronous core of ingest_document (runs inside to_thread)."""
        if not content.strip():
            raise ValueError("Document content cannot be empty")

        base_document_id = self._generate_document_id(content, filename)
        document_id = (
            f"{base_document_id}_{session_id}" if session_id else base_document_id
        )

        # Check if document already exists for this session
        existing = self.collection.get(
            where={"document_id": document_id},
            limit=1,
        )

        if existing and existing["ids"]:
            return IngestedDocument(
                document_id=document_id,
                filename=filename,
                chunk_count=len(existing["ids"]),
                total_characters=len(content),
                ingested_at=str(
                    existing["metadatas"][0].get("ingested_at", "unknown")
                    if existing["metadatas"]
                    else "unknown"
                ),
            )

        # Chunk the document
        chunks = self._chunk_text(content)

        if not chunks:
            raise ValueError("Document could not be chunked - content may be too short")

        # Prepare metadata
        base_metadata = {
            "document_id": document_id,
            "filename": filename,
            "ingested_at": datetime.utcnow().isoformat(),
            "total_chunks": len(chunks),
        }

        if session_id:
            base_metadata["session_id"] = session_id

        if metadata:
            base_metadata.update(metadata)

        # Generate embeddings for all chunks (sync OpenAI call)
        embeddings_model = self._get_embeddings(api_key)
        chunk_embeddings = embeddings_model.embed_documents(chunks)

        # Prepare data for ChromaDB
        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for idx, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
            chunk_id = self._generate_chunk_id(document_id, idx)
            chunk_metadata = {
                **base_metadata,
                "chunk_index": idx,
            }

            ids.append(chunk_id)
            documents.append(chunk)
            embeddings.append(embedding)
            metadatas.append(chunk_metadata)

        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return IngestedDocument(
            document_id=document_id,
            filename=filename,
            chunk_count=len(chunks),
            total_characters=len(content),
            ingested_at=base_metadata["ingested_at"],
        )

    def _query_sync(
        self,
        query_text: str,
        n_results: int = 5,
        session_id: Optional[str] = None,
        min_similarity: float = 0.3,
        api_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Synchronous core of query (runs inside to_thread)."""
        if not session_id:
            print(
                f"[RAG] Warning: No session_id provided for query '{query_text[:50]}...' - returning empty results"
            )
            return []

        print(
            f"[RAG] Querying with session_id={session_id}, query='{query_text[:50]}...'"
        )

        where_filter = {"session_id": session_id}
        embeddings_model = self._get_embeddings(api_key)
        query_embedding = embeddings_model.embed_query(query_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=cast(Optional[Dict[str, Any]], where_filter),
            include=["documents", "metadatas", "distances"],
        )

        formatted_results = []
        if results and results["ids"] and results["ids"][0]:
            for idx, chunk_id in enumerate(results["ids"][0]):
                formatted_results.append(
                    {
                        "chunk_id": chunk_id,
                        "content": (
                            results["documents"][0][idx] if results["documents"] else ""
                        ),
                        "metadata": (
                            results["metadatas"][0][idx] if results["metadatas"] else {}
                        ),
                        "distance": (
                            results["distances"][0][idx]
                            if results["distances"]
                            else None
                        ),
                        "similarity_score": (
                            1 - results["distances"][0][idx]
                            if results["distances"]
                            else None
                        ),
                    }
                )

        if min_similarity > 0:
            formatted_results = [
                r
                for r in formatted_results
                if r.get("similarity_score", 0) >= min_similarity
            ]

        print(
            f"[RAG] Query completed: found {len(formatted_results)} results for session_id={session_id} (min_similarity={min_similarity})"
        )
        return formatted_results

    def _delete_document_sync(self, document_id: str) -> bool:
        """Synchronous core of delete_document."""
        try:
            existing = self.collection.get(
                where={"document_id": document_id},
            )
            if existing and existing["ids"]:
                self.collection.delete(ids=existing["ids"])
                return True
            return False
        except Exception as e:
            print(f"Error deleting document {document_id}: {e}")
            return False

    def _delete_session_sync(self, session_id: str) -> int:
        """Synchronous core of delete_session."""
        try:
            existing = self.collection.get(
                where={"session_id": session_id},
            )
            if existing and existing["ids"]:
                count = len(existing["ids"])
                self.collection.delete(ids=existing["ids"])
                return count
            return 0
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return 0

    def _list_documents_sync(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Synchronous core of list_documents."""
        where_filter = {"session_id": session_id} if session_id else None

        results = self.collection.get(
            where=cast(Optional[Dict[str, Any]], where_filter),
            limit=limit * 10,
        )

        documents = {}
        if results and results["metadatas"]:
            for metadata in results["metadatas"]:
                doc_id = metadata.get("document_id")
                if doc_id and doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id,
                        "filename": metadata.get("filename", "unknown"),
                        "chunk_count": metadata.get("total_chunks", 1),
                        "ingested_at": metadata.get("ingested_at", "unknown"),
                        "session_id": metadata.get("session_id"),
                    }

        return list(documents.values())[:limit]

    def _get_collection_stats_sync(self) -> Dict[str, Any]:
        """Synchronous core of get_collection_stats."""
        count = self.collection.count()
        documents = self._list_documents_sync()

        return {
            "total_chunks": count,
            "total_documents": len(documents),
            "collection_name": self.collection_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }

    def _clear_collection_sync(self) -> bool:
        """Synchronous core of clear_collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False

    def _get_document_info_sync(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous core of get_document_info."""
        existing = self.collection.get(
            where={"document_id": document_id},
            limit=1,
        )

        if existing and existing["ids"]:
            metadata = existing["metadatas"][0] if existing["metadatas"] else {}
            return {
                "document_id": document_id,
                "filename": metadata.get("filename", "unknown"),
                "chunk_count": metadata.get("total_chunks", len(existing["ids"])),
                "ingested_at": metadata.get("ingested_at", "unknown"),
                "session_id": metadata.get("session_id"),
            }
        return None

    # ------------------------------------------------------------------
    #  Public async API
    # ------------------------------------------------------------------

    async def ingest_document(
        self,
        content: str,
        filename: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
    ) -> IngestedDocument:
        """Ingest a single document into the vector store (async)."""
        return await asyncio.to_thread(
            self._ingest_document_sync, content, filename, session_id, metadata, api_key
        )

    async def ingest_documents(
        self,
        documents: List[Dict[str, str]],
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
    ) -> List[IngestedDocument]:
        """Ingest multiple documents into the vector store (async)."""
        results = []
        for doc in documents:
            try:
                result = await self.ingest_document(
                    content=doc["content"],
                    filename=doc["filename"],
                    session_id=session_id,
                    metadata=metadata,
                    api_key=api_key,
                )
                results.append(result)
            except Exception as e:
                print(f"Error ingesting document {doc.get('filename', 'unknown')}: {e}")
        return results

    async def query(
        self,
        query_text: str,
        n_results: int = 5,
        session_id: Optional[str] = None,
        min_similarity: float = 0.3,
        api_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query the vector store for relevant document chunks (async)."""
        return await asyncio.to_thread(
            self._query_sync, query_text, n_results, session_id, min_similarity, api_key
        )

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks from the vector store (async)."""
        return await asyncio.to_thread(self._delete_document_sync, document_id)

    async def delete_session(self, session_id: str) -> int:
        """Delete all documents from a session (async)."""
        return await asyncio.to_thread(self._delete_session_sync, session_id)

    async def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an ingested document (async)."""
        return await asyncio.to_thread(self._get_document_info_sync, document_id)

    async def list_documents(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List all ingested documents (async)."""
        return await asyncio.to_thread(self._list_documents_sync, session_id, limit)

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection (async)."""
        return await asyncio.to_thread(self._get_collection_stats_sync)

    async def clear_collection(self) -> bool:
        """Clear all documents from the collection (async)."""
        return await asyncio.to_thread(self._clear_collection_sync)


# Lazy singleton instance
_rag_pipeline_instance: Optional[RAGPipeline] = None


def get_rag_pipeline(
    persist_directory: str = RAGConfig.PERSIST_DIRECTORY,
    collection_name: str = RAGConfig.COLLECTION_NAME,
    chunk_size: int = RAGConfig.CHUNK_SIZE,
    chunk_overlap: int = RAGConfig.CHUNK_OVERLAP,
) -> RAGPipeline:
    """
    Get or create the RAG pipeline singleton instance.

    This function provides lazy initialization of the RAG pipeline,
    which is useful when the OpenAI API key may not be available at import time.
    """
    global _rag_pipeline_instance

    if _rag_pipeline_instance is None:
        _rag_pipeline_instance = RAGPipeline(
            persist_directory=persist_directory,
            collection_name=collection_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    return _rag_pipeline_instance
