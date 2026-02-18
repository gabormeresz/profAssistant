"""
Authentication & user-management API routes.

All endpoints are mounted under the ``/auth`` prefix in ``main.py``.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from schemas.user import (
    UserCreate,
    UserResponse,
    UserRole,
    AccessTokenResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
    AvailableModel,
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
from services.user_settings_repository import user_settings_repository
from config import AuthConfig, LLMConfig
from rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --------------------------------------------------------------------------- #
#  Cookie helpers
# --------------------------------------------------------------------------- #

REFRESH_TOKEN_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as an httpOnly cookie on the response."""
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=AuthConfig.COOKIE_SECURE,
        samesite=AuthConfig.COOKIE_SAMESITE,
        domain=AuthConfig.COOKIE_DOMAIN,
        max_age=AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",  # Use root path so the cookie is sent regardless of
        # reverse-proxy prefix (e.g. /api/auth/* via nginx).
        # The cookie is httpOnly so JS cannot read it anyway.
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Delete the refresh token cookie."""
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        httponly=True,
        secure=AuthConfig.COOKIE_SECURE,
        samesite=AuthConfig.COOKIE_SAMESITE,
        domain=AuthConfig.COOKIE_DOMAIN,
        path="/",
    )


# --------------------------------------------------------------------------- #
#  Public endpoints
# --------------------------------------------------------------------------- #


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit("3/minute")
async def register(request: Request, body: UserCreate):
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
    response_model=AccessTokenResponse,
    summary="Log in and receive tokens",
)
@limiter.limit("5/minute")
async def login(request: Request, body: UserCreate, response: Response):
    """
    Authenticate with email + password.

    Returns a short-lived **access token** (JWT, 30 min) in the response body.
    A long-lived **refresh token** (opaque UUID, 7 days) is set as an
    ``httpOnly`` cookie (path ``/auth``). The refresh token is stored
    as a SHA-256 hash in ``user_sessions``.
    """
    user = await authenticate_user(body.email, body.password)
    tokens = await issue_token_pair(user)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return AccessTokenResponse(access_token=tokens["access_token"])


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh the access token",
)
@limiter.limit("10/minute")
async def refresh(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE),
):
    """
    Exchange a valid refresh token for a new access + refresh token pair.

    The refresh token is read from the ``httpOnly`` cookie. Implements
    **token rotation**: the old session is deleted and a new one is
    created, so each refresh token can only be used once. The new refresh
    token is set back as a cookie.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    tokens = await refresh_access_token(refresh_token)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return AccessTokenResponse(access_token=tokens["access_token"])


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out (invalidate refresh token)",
)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE),
):
    """
    Invalidate the refresh token by removing its session from the database
    and clearing the cookie.

    The access token will remain valid until it expires (stateless JWT),
    but the client should discard it.
    """
    if refresh_token:
        await logout_session(refresh_token)
    _clear_refresh_cookie(response)
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
    settings = await user_settings_repository.get_user_settings(user["user_id"])
    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found",
        )
    return UserSettingsResponse(
        has_api_key=settings["has_api_key"],
        preferred_model=settings["preferred_model"],
        available_models=[AvailableModel(**m) for m in LLMConfig.AVAILABLE_MODELS],
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
    updated = await user_settings_repository.update_user_settings(
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
    settings = await user_settings_repository.get_user_settings(user["user_id"])
    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found",
        )
    return UserSettingsResponse(
        has_api_key=settings["has_api_key"],
        preferred_model=settings["preferred_model"],
        available_models=[AvailableModel(**m) for m in LLMConfig.AVAILABLE_MODELS],
        updated_at=datetime.fromisoformat(settings["updated_at"]),
    )
