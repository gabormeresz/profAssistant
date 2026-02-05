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

    # Minimum improvement required between iterations to continue refining
    # If score improves by less than this, consider it a plateau
    MIN_IMPROVEMENT_THRESHOLD: float = 0.05

    # Dimension weights for overall score calculation
    DIMENSION_WEIGHTS: dict = {
        "learning_objectives": 0.25,
        "content_coverage": 0.20,
        "progression": 0.20,
        "activities": 0.20,
        "completeness": 0.15,
    }


# =============================================================================
# MCP Configuration
# =============================================================================


class MCPConfig:
    """Configuration for MCP (Model Context Protocol) servers."""

    # Wikipedia MCP server settings
    WIKIPEDIA_ENABLED: bool = (
        os.getenv("MCP_WIKIPEDIA_ENABLED", "true").lower() == "true"
    )
    WIKIPEDIA_URL: str = os.getenv("MCP_WIKIPEDIA_URL", "http://localhost:8765/sse")
    WIKIPEDIA_TRANSPORT: str = "sse"
