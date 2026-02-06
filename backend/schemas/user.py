"""
User-related schemas for authentication, sessions, and settings.
"""

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User roles for authorization."""

    ADMIN = "admin"
    USER = "user"


# =============================================================================
# User Schemas
# =============================================================================


class UserCreate(BaseModel):
    """Request model for user registration."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")


class UserResponse(BaseModel):
    """Response model for user data (never includes password)."""

    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    is_active: bool = Field(default=True, description="Whether the account is active")
    is_email_verified: bool = Field(
        default=False, description="Whether the email has been verified"
    )
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# =============================================================================
# Session / Token Schemas
# =============================================================================


class TokenPair(BaseModel):
    """JWT access + refresh token pair returned on login."""

    access_token: str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Long-lived refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenRefreshRequest(BaseModel):
    """Request model to refresh an access token."""

    refresh_token: str = Field(..., description="The refresh token to use")


# =============================================================================
# User Settings Schemas
# =============================================================================


class UserSettingsResponse(BaseModel):
    """Response model for user settings (API key shown as masked)."""

    has_api_key: bool = Field(
        ..., description="Whether the user has provided an OpenAI API key"
    )
    preferred_model: str = Field(
        default="gpt-4o-mini", description="Preferred OpenAI model"
    )
    updated_at: datetime = Field(..., description="Last settings update timestamp")


class UserSettingsUpdate(BaseModel):
    """Request model for updating user settings."""

    openai_api_key: Optional[str] = Field(
        None, description="OpenAI API key (will be encrypted at rest)"
    )
    preferred_model: Optional[str] = Field(
        None, description="Preferred OpenAI model identifier"
    )
