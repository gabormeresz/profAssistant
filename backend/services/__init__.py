"""Services module for business logic and data management."""

from services.database import DatabaseManager, db
from services.rag_pipeline import RAGPipeline, get_rag_pipeline
from services.mcp_client import MCPClientManager, mcp_manager
from services.auth_service import get_current_user, get_current_admin
from services.conversation_manager import ConversationRepository, conversation_manager
from services.user_repository import UserRepository, user_repository
from services.session_repository import SessionRepository, session_repository
from services.user_settings_repository import (
    UserSettingsRepository,
    user_settings_repository,
)

__all__ = [
    "DatabaseManager",
    "db",
    "RAGPipeline",
    "get_rag_pipeline",
    "MCPClientManager",
    "mcp_manager",
    "get_current_user",
    "get_current_admin",
    "ConversationRepository",
    "conversation_manager",
    "UserRepository",
    "user_repository",
    "SessionRepository",
    "session_repository",
    "UserSettingsRepository",
    "user_settings_repository",
]
