"""
Authentication service: JWT token management, password verification,
and FastAPI dependencies for protected routes.
"""

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import AuthConfig
from services.conversation_manager import conversation_manager

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  FastAPI security scheme (Bearer token)
# --------------------------------------------------------------------------- #
_bearer_scheme = HTTPBearer(auto_error=False)


# --------------------------------------------------------------------------- #
#  Token helpers
# --------------------------------------------------------------------------- #


def _hash_token(token: str) -> str:
    """SHA-256 hash of a raw token (used for refresh tokens stored in DB)."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: str, role: str) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(
        payload, AuthConfig.JWT_SECRET, algorithm=AuthConfig.JWT_ALGORITHM
    )


def create_refresh_token() -> str:
    """Create a random refresh token (raw value — hash before storing)."""
    return str(uuid.uuid4())


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Returns the payload dict on success.
    Raises HTTPException 401 on any failure.
    """
    try:
        payload = jwt.decode(
            token,
            AuthConfig.JWT_SECRET,
            algorithms=[AuthConfig.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Not an access token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --------------------------------------------------------------------------- #
#  Registration & Login helpers
# --------------------------------------------------------------------------- #


def register_user(email: str, password: str) -> dict:
    """Register a new user. Returns the user dict or raises 409."""
    user = conversation_manager.create_user(email, password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )
    return user


def authenticate_user(email: str, password: str) -> dict:
    """Verify credentials. Returns user dict or raises 401."""
    user = conversation_manager.get_user_by_email(email)
    if user is None or not conversation_manager.verify_password(
        password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


def issue_token_pair(user: dict) -> dict:
    """Create access + refresh tokens and persist the session.

    Returns ``{"access_token", "refresh_token", "token_type"}``.
    """
    access_token = create_access_token(user["user_id"], user["role"])
    refresh_token = create_refresh_token()

    # Store hashed refresh token in DB
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS)
    ).isoformat()

    conversation_manager.create_session(
        user_id=user["user_id"],
        refresh_token_hash=_hash_token(refresh_token),
        expires_at=expires_at,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_access_token(raw_refresh_token: str) -> dict:
    """Validate a refresh token and issue a new token pair.

    The old session is deleted (token rotation).
    """
    token_hash = _hash_token(raw_refresh_token)

    session = conversation_manager.get_session_by_refresh_hash(token_hash)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Check expiry
    expires_at = datetime.fromisoformat(session["expires_at"])
    # Make naive datetime timezone-aware (assume UTC)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        conversation_manager.delete_session(session["session_id"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Delete old session (rotation)
    conversation_manager.delete_session(session["session_id"])

    # Fetch user
    user = conversation_manager.get_user_by_id(session["user_id"])
    if user is None or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    return issue_token_pair(user)


def logout_session(raw_refresh_token: str) -> bool:
    """Delete the session associated with the refresh token."""
    token_hash = _hash_token(raw_refresh_token)
    session = conversation_manager.get_session_by_refresh_hash(token_hash)
    if session:
        return conversation_manager.delete_session(session["session_id"])
    return False


# --------------------------------------------------------------------------- #
#  FastAPI dependencies
# --------------------------------------------------------------------------- #


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    """Dependency that extracts and validates the Bearer token.

    Returns the full user dict from the database.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    user_id: str = payload.get("sub", "")

    user = conversation_manager.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


async def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency that requires admin role."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
