"""Pydantic schemas for authentication."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ============ User Schemas ============

class UserCreate(BaseModel):
    """Schema for user registration (open signup)."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, max_length=200)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""

    id: str
    email: str
    display_name: Optional[str]
    is_active: bool
    is_superuser: bool
    org_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserMe(BaseModel):
    """Schema for current user info."""

    id: str
    email: str
    display_name: Optional[str]
    is_superuser: bool
    org_id: str


# ============ Token Schemas ============

class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


# ============ Invite Schemas ============

class InviteCreate(BaseModel):
    """Schema for creating an invite."""

    email: EmailStr


class InviteResponse(BaseModel):
    """Schema for invite response."""

    id: str
    email: str
    invite_code: str
    expires_at: datetime
    is_used: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteValidate(BaseModel):
    """Schema for validating an invite."""

    invite_code: str


class InviteValidateResponse(BaseModel):
    """Schema for invite validation response."""

    valid: bool
    email: str
    expires_at: datetime
