"""
Central configuration for the backend application.

All configurable constants and settings should be defined here.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =============================================================================
# RAG Pipeline Configuration
# =============================================================================


class RAGConfig:
    """Configuration for the RAG pipeline."""

    # Chunking settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100

    # ChromaDB settings
    PERSIST_DIRECTORY: str = "chroma_db"
    COLLECTION_NAME: str = "documents"

    # Embedding model
    EMBEDDING_MODEL: str = "text-embedding-3-small"


# =============================================================================
# LLM Configuration
# =============================================================================


class LLMConfig:
    """Configuration for LLM models."""

    # Default models
    DEFAULT_MODEL: str = "gpt-4o-mini"

    # Temperature settings
    DEFAULT_TEMPERATURE: float = 0.7


# =============================================================================
# API Configuration
# =============================================================================


class APIConfig:
    """Configuration for API settings."""

    # CORS origins
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
    ]


# =============================================================================
# Database Configuration
# =============================================================================


class DBConfig:
    """Configuration for database settings."""

    CONVERSATIONS_DB: str = "conversations.db"
    CHECKPOINTS_DB: str = "checkpoints.db"


# =============================================================================
# Evaluation Agents Configuration
# =============================================================================


class EvaluationConfig:
    """Configuration for the evaluation agents."""

    MAX_RETRIES: int = 3
    APPROVAL_THRESHOLD: float = 0.8
