"""
Service for resolving per-user OpenAI API keys.

Centralises the "who uses which key?" logic so that individual nodes
and endpoints never need to handle raw keys or threading them through
function signatures.

Rules:
    - **Admin users** → server-side ``OPENAI_API_KEY`` from ``.env``
    - **Regular users** → encrypted key stored in the database,
      decrypted on demand via ``conversation_manager``
"""

import os
import logging
from typing import Optional

from services.conversation_manager import conversation_manager

logger = logging.getLogger(__name__)


def get_api_key_for_user(user_id: str) -> Optional[str]:
    """
    Resolve the OpenAI API key for a given user.

    Args:
        user_id: The unique user identifier.

    Returns:
        The plaintext API key, or ``None`` if the user has not
        configured one (and is not admin).
    """
    user = conversation_manager.get_user_by_id(user_id)
    if user is None:
        return None

    # Admin users always use the server-side key
    if user["role"] == "admin":
        return os.environ.get("OPENAI_API_KEY") or None

    # Regular users: decrypt their personal key from the database
    return conversation_manager.get_decrypted_api_key(user_id)


def require_api_key(user_id: str) -> str:
    """
    Same as :func:`get_api_key_for_user` but raises if no key is
    available.  Useful in request handlers that must fail early.

    Raises:
        ValueError: If no API key could be resolved.
    """
    key = get_api_key_for_user(user_id)
    if not key:
        raise ValueError(
            "No OpenAI API key available. "
            "Please configure your API key in your profile settings."
        )
    return key
