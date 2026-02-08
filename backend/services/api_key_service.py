"""
Service for resolving per-user OpenAI API keys.

Centralises the "who uses which key?" logic so that individual nodes
and endpoints never need to handle raw keys or threading them through
function signatures.

Rules:
    - **Admin users** → server-side ``OPENAI_API_KEY`` from ``.env``
    - **Regular users** → encrypted key stored in the database,
      decrypted on demand via ``user_settings_repository``
"""

import os
import logging
from typing import Optional

from services.user_repository import user_repository
from services.user_settings_repository import user_settings_repository

logger = logging.getLogger(__name__)


async def get_api_key_for_user(user_id: str) -> Optional[str]:
    """
    Resolve the OpenAI API key for a given user.

    Args:
        user_id: The unique user identifier.

    Returns:
        The plaintext API key, or ``None`` if the user has not
        configured one (and is not admin).
    """
    user = await user_repository.get_user_by_id(user_id)
    if user is None:
        return None

    # Admin users always use the server-side key
    if user["role"] == "admin":
        return os.environ.get("OPENAI_API_KEY") or None

    # Regular users: decrypt their personal key from the database
    return await user_settings_repository.get_decrypted_api_key(user_id)


async def require_api_key(user_id: str) -> str:
    """
    Same as :func:`get_api_key_for_user` but raises if no key is
    available.  Useful in request handlers that must fail early.

    Raises:
        ValueError: If no API key could be resolved.
    """
    key = await get_api_key_for_user(user_id)
    if not key:
        raise ValueError(
            "No OpenAI API key available. "
            "Please configure your API key in your profile settings."
        )
    return key


async def resolve_user_llm_config(user_id: str) -> tuple[str, Optional[str]]:
    """
    Resolve both the API key **and** preferred model for a user in a
    single DB look-up.

    Returns:
        ``(api_key, preferred_model)`` — *preferred_model* may be
        ``None`` (falls back to the default in the model layer).

    Raises:
        ValueError: If no API key could be resolved.
    """
    user = await user_repository.get_user_by_id(user_id)
    if user is None:
        raise ValueError("User not found.")

    # Admin → server-side key; model preference still comes from DB.
    if user["role"] == "admin":
        api_key = os.environ.get("OPENAI_API_KEY") or None
    else:
        api_key = await user_settings_repository.get_decrypted_api_key(user_id)

    if not api_key:
        raise ValueError(
            "No OpenAI API key available. "
            "Please configure your API key in your profile settings."
        )

    # Preferred model — one lightweight query (already cached by SQLite)
    settings = await user_settings_repository.get_user_settings(user_id)
    preferred_model = settings["preferred_model"] if settings else None

    return api_key, preferred_model
