"""Pydantic schemas for authentication."""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============ User Schemas ============

class UserCreate(BaseModel):
    """Schema for user registration (open signup)."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, max_length=200)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets strength requirements."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
        return v


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


# ============ Settings Schemas ============

class EmailUpdate(BaseModel):
    """Schema for updating email address."""

    new_email: EmailStr


class PasswordUpdate(BaseModel):
    """Schema for updating password."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets strength requirements."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
        return v


class DisplayNameUpdate(BaseModel):
    """Schema for updating display name."""

    display_name: Optional[str] = Field(None, max_length=200)


# ============ API Key Schemas ============

class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str = Field(..., min_length=1, max_length=200)


class APIKeyResponse(BaseModel):
    """Schema for API key response (without the full key)."""

    id: str
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(BaseModel):
    """Schema for newly created API key (includes full key - only shown once)."""

    id: str
    name: str
    key: str  # Full key - only returned on creation
    key_prefix: str
    created_at: datetime


class APIKeyListResponse(BaseModel):
    """Schema for list of API keys."""

    api_keys: list[APIKeyResponse]
    total: int


# ============ LLM Credential Schemas ============

class LLMCredentialCreate(BaseModel):
    """Schema for creating an LLM provider credential."""

    provider: str = Field(..., min_length=1, max_length=50, description="LLM provider name (openai, anthropic, etc.)")
    display_name: str = Field(..., min_length=1, max_length=200, description="Display name for this credential")
    api_key: str = Field(..., min_length=1, description="API key for the LLM provider")
    api_base: Optional[str] = Field(None, max_length=500, description="Custom API base URL (optional)")


class LLMCredentialUpdate(BaseModel):
    """Schema for updating an LLM provider credential."""

    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    api_key: Optional[str] = Field(None, min_length=1, description="New API key (leave empty to keep existing)")
    api_base: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class LLMCredentialResponse(BaseModel):
    """Schema for LLM credential response (without the full API key)."""

    id: str
    provider: str
    display_name: str
    api_key_preview: str  # First 8 chars + masked
    api_base: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LLMCredentialListResponse(BaseModel):
    """Schema for list of LLM credentials."""

    credentials: list[LLMCredentialResponse]
    total: int


# ============ Admin Schemas ============

class UserAdminResponse(BaseModel):
    """Schema for user info in admin view."""

    id: str
    email: str
    display_name: Optional[str]
    is_active: bool
    is_superuser: bool
    org_id: str
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Schema for paginated list of users."""

    users: list[UserAdminResponse]
    total: int
    page: int
    limit: int


class UserUpdateByAdmin(BaseModel):
    """Schema for admin updating a user's profile."""

    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(None, max_length=200)


class UserStatusUpdate(BaseModel):
    """Schema for admin toggling user active status."""

    is_active: bool


class PasswordResetByAdmin(BaseModel):
    """Schema for admin resetting a user's password."""

    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets strength requirements."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
        return v
