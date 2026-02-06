"""
Central configuration for the backend application.

All configurable constants and settings should be defined here.
"""

import logging
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
# Prompt Enhancer Configuration
# =============================================================================


class PromptEnhancerConfig:
    """Configuration for the prompt enhancer."""

    TEMPERATURE: float = 0.5
    MAX_TOKENS: int = 250


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
# Authentication Configuration
# =============================================================================


class AuthConfig:
    """Configuration for authentication and encryption."""

    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")

    # Token expiry
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )

    # Admin seed credentials
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")

    JWT_ALGORITHM: str = "HS256"


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


# =============================================================================
# Debug / Testing Configuration
# =============================================================================


class DebugConfig:
    """Configuration for debug and testing features."""

    # When True, the course outline endpoint uses a dummy generator that
    # returns hardcoded data with realistic SSE events (no LLM calls).
    # Toggle this to quickly reproduce SSE streaming bugs.
    USE_DUMMY_GRAPH: bool = os.getenv("USE_DUMMY_GRAPH", "true").lower() == "true"


# =============================================================================
# Logging Configuration
# =============================================================================


class LoggingConfig:
    """Configuration for application logging."""

    # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LEVEL: int = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
