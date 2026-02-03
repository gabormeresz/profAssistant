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
    ADVANCED_MODEL: str = "gpt-4o"

    # Temperature settings
    DEFAULT_TEMPERATURE: float = 0.7
    CREATIVE_TEMPERATURE: float = 0.9
    PRECISE_TEMPERATURE: float = 0.3


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
