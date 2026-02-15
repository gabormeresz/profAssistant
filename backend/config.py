"""
Central configuration for the backend application.

All configurable constants and settings should be defined here.
"""

import base64
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
    PERSIST_DIRECTORY: str = os.path.join(os.getenv("DATA_DIR", "."), "chroma_db")
    COLLECTION_NAME: str = "documents"

    # Embedding model
    EMBEDDING_MODEL: str = "text-embedding-3-small"


# =============================================================================
# LLM Configuration
# =============================================================================


class LLMConfig:
    """Configuration for LLM models."""

    # Default model assigned to every new user
    DEFAULT_MODEL: str = "gpt-4o-mini"

    # Supported models the user may choose from.
    # Each entry carries an id (OpenAI model name), a human-readable label,
    # and an i18n description key resolved by the frontend.
    AVAILABLE_MODELS: list[dict] = [
        {
            "id": "gpt-4o-mini",
            "label": "GPT-4o Mini",
            "description_key": "profile.models.gpt4oMiniDesc",
        },
        {
            "id": "gpt-4.1-mini",
            "label": "GPT-4.1 Mini",
            "description_key": "profile.models.gpt41MiniDesc",
        },
        {
            "id": "gpt-5-mini",
            "label": "GPT-5 Mini",
            "description_key": "profile.models.gpt5MiniDesc",
        },
        {"id": "gpt-5", "label": "GPT-5", "description_key": "profile.models.gpt5Desc"},
        {
            "id": "gpt-5.2",
            "label": "GPT-5.2",
            "description_key": "profile.models.gpt52Desc",
        },
    ]

    # Quick set for validation
    ALLOWED_MODEL_IDS: set[str] = {m["id"] for m in AVAILABLE_MODELS}

    # Models that use internal chain-of-thought (reasoning tokens).
    # These support ``reasoning_effort`` but NOT custom ``temperature``.
    REASONING_MODELS: set[str] = {"gpt-5-mini", "gpt-5", "gpt-5.2"}

    # -----------------------------------------------------------------
    # Purpose-based model presets
    # -----------------------------------------------------------------
    # Each preset defines parameters sent to the OpenAI API.
    #   • temperature / max_tokens  → used by non-reasoning models only
    #   • reasoning_effort           → used by reasoning models only
    # Incompatible params are stripped automatically in model.py.
    #
    # max_tokens caps output length for non-reasoning models to prevent
    # unbounded output cost.

    MODEL_PRESETS: dict[str, dict] = {
        "enhancer": {
            "temperature": 0.5,
            "max_tokens": 250,
            "reasoning_effort": "low",
        },
        "generator": {
            "temperature": 0.5,
            "max_tokens": 16000,
            "reasoning_effort": "medium",
        },
        "evaluator": {
            "temperature": 0.3,
            "max_tokens": 2000,
            "reasoning_effort": "low",
        },
    }


# =============================================================================
# API Configuration
# =============================================================================


class APIConfig:
    """Configuration for API settings."""

    # CORS origins — override via CORS_ORIGINS env var (comma-separated)
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ]


# =============================================================================
# Database Configuration
# =============================================================================


class DBConfig:
    """Configuration for database settings."""

    DATA_DIR: str = os.getenv("DATA_DIR", ".")
    CONVERSATIONS_DB: str = os.path.join(DATA_DIR, "conversations.db")
    CHECKPOINTS_DB: str = os.path.join(DATA_DIR, "checkpoints.db")


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

    # Cookie settings for refresh tokens
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    COOKIE_SAMESITE: str = os.getenv(
        "COOKIE_SAMESITE", "lax"
    )  # "lax" for dev, "strict" for prod
    COOKIE_DOMAIN: str | None = os.getenv("COOKIE_DOMAIN") or None

    @classmethod
    def validate(cls) -> None:
        """Fail fast if critical auth secrets are missing or insecure."""
        if not cls.JWT_SECRET or len(cls.JWT_SECRET) < 32:
            raise RuntimeError(
                "JWT_SECRET env var must be set and be at least 32 characters. "
                'Generate one with: python3 -c "import secrets; print(secrets.token_hex(32))"'
            )

        if not cls.ENCRYPTION_KEY:
            raise RuntimeError(
                "ENCRYPTION_KEY env var must be set. "
                'Generate one with: python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"'
            )

        # Validate that ENCRYPTION_KEY is a valid Fernet key (URL-safe base64, 32 bytes)
        try:
            key_bytes = base64.urlsafe_b64decode(cls.ENCRYPTION_KEY)
            if len(key_bytes) != 32:
                raise ValueError("Key must be 32 bytes")
        except Exception:
            raise RuntimeError(
                "ENCRYPTION_KEY must be a valid Fernet key (URL-safe base64-encoded 32 bytes). "
                'Generate one with: python3 -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"'
            )


AuthConfig.validate()


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
# Upload Configuration
# =============================================================================


class UploadConfig:
    """Configuration for file upload limits."""

    # Maximum file size in bytes (default: 10 MB)
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))


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
    # Only expose these tools from the Wikipedia MCP server
    WIKIPEDIA_ALLOWED_TOOLS: list[str] = [
        "search_wikipedia",
        "get_article",
        "get_summary",
    ]

    # Tavily MCP server settings (remote hosted)
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    TAVILY_URL: str = "https://mcp.tavily.com/mcp/"
    TAVILY_TRANSPORT: str = "http"
    # Only expose these tools from the Tavily MCP server
    TAVILY_ALLOWED_TOOLS: list[str] = ["tavily_search", "tavily_extract"]


# =============================================================================
# Debug / Testing Configuration
# =============================================================================


class DebugConfig:
    """Configuration for debug and testing features."""

    # When True, the course outline endpoint uses a dummy generator that
    # returns hardcoded data with realistic SSE events (no LLM calls).
    # Toggle this to quickly reproduce SSE streaming bugs.
    USE_DUMMY_GRAPH: bool = os.getenv("USE_DUMMY_GRAPH", "false").lower() == "true"


# =============================================================================
# Logging Configuration
# =============================================================================


class LoggingConfig:
    """Configuration for application logging."""

    # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LEVEL: int = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
