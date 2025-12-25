"""JWT token handling utilities."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from src.config import get_settings

settings = get_settings()


def create_access_token(user_id: str, email: str, is_superuser: bool = False) -> str:
    """Create a JWT access token.

    Args:
        user_id: User's unique ID
        email: User's email
        is_superuser: Whether user is a superuser

    Returns:
        Encoded JWT token string
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": user_id,
        "email": email,
        "is_superuser": is_superuser,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token() -> tuple[str, str, datetime]:
    """Create a refresh token.

    Returns:
        Tuple of (raw_token, token_hash, expires_at)
    """
    # Generate a secure random token
    raw_token = secrets.token_urlsafe(32)

    # Hash the token for storage
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    # Set expiry
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )

    return raw_token, token_hash, expires_at


def hash_token(token: str) -> str:
    """Hash a token for secure storage/lookup.

    Args:
        token: Raw token string

    Returns:
        SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token.

    Args:
        token: Encoded JWT token

    Returns:
        Decoded payload dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None
