"""
Authentication & user-management API routes.

All endpoints are mounted under the ``/auth`` prefix in ``main.py``.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from schemas.user import (
    UserCreate,
    UserResponse,
    UserRole,
    TokenPair,
    TokenRefreshRequest,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from services.auth_service import (
    register_user,
    authenticate_user,
    issue_token_pair,
    refresh_access_token,
    logout_session,
    get_current_user,
    get_current_admin,
)
from services.conversation_manager import conversation_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --------------------------------------------------------------------------- #
#  Public endpoints
# --------------------------------------------------------------------------- #


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(body: UserCreate):
    """
    Create a new user account.

    - Password is hashed with bcrypt before storage.
    - A ``user_settings`` row is auto-created (no API key by default).
    - Email verification is *not* enforced yet (``is_email_verified=False``).
    """
    user = await register_user(body.email, body.password)
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        role=UserRole(user["role"]),
        is_active=user["is_active"],
        is_email_verified=user["is_email_verified"],
        created_at=datetime.fromisoformat(user["created_at"]),
        updated_at=datetime.fromisoformat(user["updated_at"]),
    )


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Log in and receive tokens",
)
async def login(body: UserCreate):
    """
    Authenticate with email + password.

    Returns a short-lived **access token** (JWT, 30 min) and a long-lived
    **refresh token** (opaque UUID, 7 days).  The refresh token is stored
    as a SHA-256 hash in ``user_sessions``.
    """
    user = await authenticate_user(body.email, body.password)
    tokens = await issue_token_pair(user)
    return TokenPair(**tokens)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh the access token",
)
async def refresh(body: TokenRefreshRequest):
    """
    Exchange a valid refresh token for a new access + refresh token pair.

    Implements **token rotation**: the old session is deleted and a new one
    is created, so each refresh token can only be used once.
    """
    tokens = await refresh_access_token(body.refresh_token)
    return TokenPair(**tokens)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out (invalidate refresh token)",
)
async def logout(body: TokenRefreshRequest):
    """
    Invalidate the refresh token by removing its session from the database.

    The access token will remain valid until it expires (stateless JWT),
    but the client should discard it.
    """
    await logout_session(body.refresh_token)
    return None


# --------------------------------------------------------------------------- #
#  Protected endpoints
# --------------------------------------------------------------------------- #


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def me(user: dict = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        role=UserRole(user["role"]),
        is_active=user["is_active"],
        is_email_verified=user["is_email_verified"],
        created_at=datetime.fromisoformat(user["created_at"]),
        updated_at=datetime.fromisoformat(user["updated_at"]),
    )


# --------------------------------------------------------------------------- #
#  User settings
# --------------------------------------------------------------------------- #


@router.get(
    "/settings",
    response_model=UserSettingsResponse,
    summary="Get current user's settings",
)
async def get_settings(user: dict = Depends(get_current_user)):
    """
    Return the user's settings (masked API key flag, preferred model).
    """
    settings = await conversation_manager.get_user_settings(user["user_id"])
    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found",
        )
    return UserSettingsResponse(
        has_api_key=settings["has_api_key"],
        preferred_model=settings["preferred_model"],
        updated_at=datetime.fromisoformat(settings["updated_at"]),
    )


@router.patch(
    "/settings",
    response_model=UserSettingsResponse,
    summary="Update current user's settings",
)
async def update_settings(
    body: UserSettingsUpdate,
    user: dict = Depends(get_current_user),
):
    """
    Update OpenAI API key and/or preferred model.

    - The API key is encrypted at rest with ``Fernet`` (server-side ``ENCRYPTION_KEY``).
    - Passing ``openai_api_key: null`` leaves the key unchanged; to *remove* the key
      send an empty string.
    """
    updated = await conversation_manager.update_user_settings(
        user_id=user["user_id"],
        openai_api_key=body.openai_api_key,
        preferred_model=body.preferred_model,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found",
        )

    # Return refreshed settings
    settings = await conversation_manager.get_user_settings(user["user_id"])
    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found",
        )
    return UserSettingsResponse(
        has_api_key=settings["has_api_key"],
        preferred_model=settings["preferred_model"],
        updated_at=datetime.fromisoformat(settings["updated_at"]),
    )
