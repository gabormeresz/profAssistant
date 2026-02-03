"""
RAG Pipeline Service for document ingestion and retrieval.

This service handles:
- Document chunking with recursive text splitting
- Vector storage using ChromaDB
- Document retrieval for RAG queries

The service is independent and can be used by agents for dynamic querying.
"""

import hashlib
from typing import List, Optional, Dict, Any
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
        """
        Initialize the RAG pipeline.

        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the ChromaDB collection
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
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

        # Initialize embeddings with configured model
        self.embeddings = OpenAIEmbeddings(model=RAGConfig.EMBEDDING_MODEL)

        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )

    def _generate_document_id(self, content: str, filename: str) -> str:
        """Generate a unique document ID based on content hash and filename."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{filename}_{content_hash}"

    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """Generate a unique chunk ID."""
        return f"{document_id}_chunk_{chunk_index}"

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks using recursive character text splitter.

        Args:
            text: The text content to split

        Returns:
            List of text chunks
        """
        return self.text_splitter.split_text(text)

    def ingest_document(
        self,
        content: str,
        filename: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestedDocument:
        """
        Ingest a single document into the vector store.

        Args:
            content: The text content of the document
            filename: Name of the file
            session_id: Optional session ID for grouping documents
            metadata: Optional additional metadata

        Returns:
            IngestedDocument with ingestion details
        """
        if not content.strip():
            raise ValueError("Document content cannot be empty")

        # Generate document ID
        document_id = self._generate_document_id(content, filename)

        # Check if document already exists (by document_id)
        existing = self.collection.get(
            where={"document_id": document_id},
            limit=1,
        )

        if existing and existing["ids"]:
            # Document already ingested, return existing info
            return IngestedDocument(
                document_id=document_id,
                filename=filename,
                chunk_count=len(existing["ids"]),
                total_characters=len(content),
                ingested_at=(
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

        # Generate embeddings for all chunks
        chunk_embeddings = self.embeddings.embed_documents(chunks)

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

    def ingest_documents(
        self,
        documents: List[Dict[str, str]],
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[IngestedDocument]:
        """
        Ingest multiple documents into the vector store.

        Args:
            documents: List of dicts with 'content' and 'filename' keys
            session_id: Optional session ID for grouping documents
            metadata: Optional additional metadata to apply to all documents

        Returns:
            List of IngestedDocument objects
        """
        results = []
        for doc in documents:
            try:
                result = self.ingest_document(
                    content=doc["content"],
                    filename=doc["filename"],
                    session_id=session_id,
                    metadata=metadata,
                )
                results.append(result)
            except Exception as e:
                # Log error but continue with other documents
                print(f"Error ingesting document {doc.get('filename', 'unknown')}: {e}")

        return results

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        session_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store for relevant document chunks.

        Args:
            query_text: The query string
            n_results: Number of results to return
            session_id: Optional session ID to filter results
            document_ids: Optional list of document IDs to filter results

        Returns:
            List of relevant document chunks with metadata and scores
        """
        # Build where filter
        where_filter = None
        if session_id or document_ids:
            conditions = []
            if session_id:
                conditions.append({"session_id": session_id})
            if document_ids:
                conditions.append({"document_id": {"$in": document_ids}})

            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}

        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query_text)

        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
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

        return formatted_results

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks from the vector store.

        Args:
            document_id: The ID of the document to delete

        Returns:
            True if deletion was successful
        """
        try:
            # Get all chunks for this document
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

    def delete_session(self, session_id: str) -> int:
        """
        Delete all documents from a session.

        Args:
            session_id: The session ID

        Returns:
            Number of chunks deleted
        """
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

    def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an ingested document.

        Args:
            document_id: The document ID

        Returns:
            Document information or None if not found
        """
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

    def list_documents(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List all ingested documents.

        Args:
            session_id: Optional session ID to filter
            limit: Maximum number of documents to return

        Returns:
            List of document information
        """
        where_filter = {"session_id": session_id} if session_id else None

        results = self.collection.get(
            where=where_filter,
            limit=limit * 10,  # Get more chunks to dedupe
        )

        # Deduplicate by document_id
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

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Collection statistics
        """
        count = self.collection.count()
        documents = self.list_documents()

        return {
            "total_chunks": count,
            "total_documents": len(documents),
            "collection_name": self.collection_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }

    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.

        Returns:
            True if successful
        """
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False


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

    Args:
        persist_directory: Directory for ChromaDB persistence
        collection_name: Name of the ChromaDB collection
        chunk_size: Size of text chunks in characters
        chunk_overlap: Overlap between chunks in characters

    Returns:
        RAGPipeline instance
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
