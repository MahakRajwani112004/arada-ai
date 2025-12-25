"""Authentication module for MagOneAI."""
from src.auth.dependencies import get_current_user, get_current_superuser
from src.auth.password import hash_password, verify_password
from src.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from src.auth.service import AuthService
from src.auth.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    InviteCreate,
    InviteResponse,
)

__all__ = [
    # Dependencies
    "get_current_user",
    "get_current_superuser",
    # Password
    "hash_password",
    "verify_password",
    # JWT
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    # Service
    "AuthService",
    # Schemas
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "InviteCreate",
    "InviteResponse",
]
