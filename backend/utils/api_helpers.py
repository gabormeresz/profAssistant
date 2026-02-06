"""
Shared helpers for API-key resolution and OpenAI error classification.

Used by generation routes to validate keys before streaming and to
map exceptions to frontend-translatable error payloads.
"""

from fastapi import HTTPException


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
