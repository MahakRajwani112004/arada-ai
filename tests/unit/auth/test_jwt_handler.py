"""Tests for JWT token handling utilities."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from src.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)


class TestCreateAccessToken:
    """Tests for create_access_token function."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string."""
        token = create_access_token("user-123", "test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_decodable(self):
        """Test that created token can be decoded."""
        user_id = "user-123"
        email = "test@example.com"
        token = create_access_token(user_id, email)

        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == user_id
        assert decoded["email"] == email
        assert decoded["type"] == "access"
        assert decoded["is_superuser"] is False

    def test_create_access_token_superuser(self):
        """Test creating access token for superuser."""
        token = create_access_token("admin-1", "admin@example.com", is_superuser=True)
        decoded = decode_token(token)
        assert decoded["is_superuser"] is True

    def test_create_access_token_has_expiry(self):
        """Test that token has expiry claim."""
        token = create_access_token("user-123", "test@example.com")
        decoded = decode_token(token)
        assert "exp" in decoded
        assert "iat" in decoded

    def test_create_access_token_different_users(self):
        """Test tokens for different users are different."""
        token1 = create_access_token("user-1", "user1@example.com")
        token2 = create_access_token("user-2", "user2@example.com")
        assert token1 != token2


class TestCreateRefreshToken:
    """Tests for create_refresh_token function."""

    def test_create_refresh_token_returns_tuple(self):
        """Test that create_refresh_token returns a tuple of 3 items."""
        result = create_refresh_token()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_create_refresh_token_structure(self):
        """Test the structure of returned tuple."""
        raw_token, token_hash, expires_at = create_refresh_token()

        assert isinstance(raw_token, str)
        assert isinstance(token_hash, str)
        assert isinstance(expires_at, datetime)

    def test_create_refresh_token_raw_token_format(self):
        """Test that raw token is URL-safe base64."""
        raw_token, _, _ = create_refresh_token()
        # URL-safe base64 uses only these characters
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        assert all(c in valid_chars for c in raw_token)

    def test_create_refresh_token_hash_is_sha256(self):
        """Test that token hash is 64-char SHA-256."""
        _, token_hash, _ = create_refresh_token()
        assert len(token_hash) == 64
        # SHA-256 produces hex output
        assert all(c in "0123456789abcdef" for c in token_hash)

    def test_create_refresh_token_expires_in_future(self):
        """Test that expiry is in the future."""
        _, _, expires_at = create_refresh_token()
        assert expires_at > datetime.now(timezone.utc)

    def test_create_refresh_token_unique(self):
        """Test that each call produces unique tokens."""
        token1, hash1, _ = create_refresh_token()
        token2, hash2, _ = create_refresh_token()

        assert token1 != token2
        assert hash1 != hash2

    def test_create_refresh_token_hash_matches(self):
        """Test that hash_token produces same hash."""
        raw_token, token_hash, _ = create_refresh_token()
        computed_hash = hash_token(raw_token)
        assert computed_hash == token_hash


class TestHashToken:
    """Tests for hash_token function."""

    def test_hash_token_returns_string(self):
        """Test that hash_token returns a string."""
        result = hash_token("some-token")
        assert isinstance(result, str)

    def test_hash_token_sha256_format(self):
        """Test that result is 64-char SHA-256 hex."""
        result = hash_token("any-input")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_token_deterministic(self):
        """Test that same input produces same hash."""
        token = "my-secret-token"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        assert hash1 == hash2

    def test_hash_token_different_inputs(self):
        """Test that different inputs produce different hashes."""
        hash1 = hash_token("token1")
        hash2 = hash_token("token2")
        assert hash1 != hash2

    def test_hash_token_empty_string(self):
        """Test hashing empty string."""
        result = hash_token("")
        assert len(result) == 64


class TestDecodeToken:
    """Tests for decode_token function."""

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        token = create_access_token("user-123", "test@example.com")
        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["email"] == "test@example.com"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token returns None."""
        result = decode_token("not-a-valid-token")
        assert result is None

    def test_decode_empty_token(self):
        """Test decoding empty string returns None."""
        result = decode_token("")
        assert result is None

    def test_decode_malformed_jwt(self):
        """Test decoding malformed JWT returns None."""
        result = decode_token("header.payload.signature")
        assert result is None

    def test_decode_token_wrong_signature(self):
        """Test token with wrong signature fails."""
        token = create_access_token("user-123", "test@example.com")
        # Corrupt the signature
        parts = token.split(".")
        corrupted = ".".join(parts[:-1] + ["wrongsignature"])
        result = decode_token(corrupted)
        assert result is None

    def test_decode_expired_token(self):
        """Test that expired token returns None."""
        from jose import jwt
        from src.config import get_settings

        settings = get_settings()
        # Create an already expired token
        expired_payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(expired_payload, settings.secret_key, algorithm=settings.jwt_algorithm)

        result = decode_token(expired_token)
        assert result is None
