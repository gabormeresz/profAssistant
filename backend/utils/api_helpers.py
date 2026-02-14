"""
Shared helpers for API-key resolution, thread ownership validation,
and OpenAI error classification.

Used by generation routes to validate keys before streaming, enforce
thread ownership on follow-up requests, and map exceptions to
frontend-translatable error payloads.
"""

import logging
from typing import Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def validate_thread_ownership(
    thread_id: Optional[str], current_user: dict
) -> None:
    """
    Validate that a follow-up ``thread_id`` belongs to the requesting user.

    For first calls (``thread_id is None``), this is a no-op — the
    generator will create a new thread owned by the current user.

    For follow-up calls, the function looks up the conversation in the
    database and verifies that ``conversation.user_id`` matches
    ``current_user["user_id"]``.  Admin users may access any thread.

    Raises:
        HTTPException 404 – thread not found or belongs to another user
            (unified 404 prevents leaking thread existence information).
    """
    if thread_id is None:
        return  # First call — nothing to validate

    from services.conversation_manager import conversation_manager

    conversation = await conversation_manager.get_conversation(thread_id)

    if conversation is None:
        logger.warning(
            "Thread ownership check failed: thread_id=%s not found (user=%s)",
            thread_id,
            current_user["user_id"],
        )
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Admin users can access any thread (consistent with conversation routes)
    if current_user.get("role") == "admin":
        return

    if conversation.user_id != current_user["user_id"]:
        logger.warning(
            "Thread ownership check failed: thread_id=%s belongs to user=%s, "
            "requested by user=%s",
            thread_id,
            conversation.user_id,
            current_user["user_id"],
        )
        raise HTTPException(status_code=404, detail="Conversation not found")


async def resolve_api_key(user: dict) -> str:
    """
    Validate that the user has a usable OpenAI API key.

    Delegates to ``api_key_service`` so that the logic lives in one
    place.  The returned key is used **only** for early HTTP-level
    validation — nodes and helpers resolve it themselves from
    ``user_id``.

    Raises HTTPException 403/500 when no key is available.
    """
    from services.api_key_service import require_api_key

    try:
        return await require_api_key(user["user_id"])
    except ValueError:
        if user["role"] == "admin":
            raise HTTPException(
                status_code=500,
                detail="Server-side OPENAI_API_KEY is not configured.",
            )
        raise HTTPException(
            status_code=403,
            detail="errors.apiKeyRequired",
        )


def classify_error(exc: Exception) -> dict:
    """
    Map common OpenAI / API-key errors to frontend-translatable message keys.

    Returns a dict suitable for ``json.dumps`` inside an SSE error event,
    containing both ``message`` (raw) and ``message_key`` (i18n key).
    """
    import openai

    raw = str(exc)

    if isinstance(exc, openai.AuthenticationError):
        return {"message": raw, "message_key": "errors.invalidApiKey"}
    if isinstance(exc, openai.RateLimitError):
        lower = raw.lower()
        if "quota" in lower or "billing" in lower or "exceeded" in lower:
            return {"message": raw, "message_key": "errors.insufficientQuota"}
        return {"message": raw, "message_key": "errors.rateLimited"}
    if isinstance(exc, openai.APIStatusError) and exc.status_code >= 500:
        return {"message": raw, "message_key": "errors.openaiUnavailable"}
    if isinstance(exc, ValueError) and "API key" in raw:
        return {"message": raw, "message_key": "errors.apiKeyRequired"}

    return {"message": raw, "message_key": "errors.generationFailed"}
