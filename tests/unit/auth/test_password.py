"""Tests for password hashing utilities."""

import pytest
from src.auth.password import hash_password, verify_password


class TestHashPassword:
    """Tests for hash_password function."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        result = hash_password("testpassword")
        assert isinstance(result, str)

    def test_hash_password_different_from_input(self):
        """Test that hashed password differs from input."""
        password = "mysecretpassword"
        hashed = hash_password(password)
        assert hashed != password

    def test_hash_password_produces_bcrypt_format(self):
        """Test that hash follows bcrypt format ($2b$...)."""
        hashed = hash_password("testpassword")
        assert hashed.startswith("$2b$")

    def test_hash_password_different_salts(self):
        """Test that same password produces different hashes (different salts)."""
        password = "samepassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_hash_password_with_unicode(self):
        """Test hashing password with unicode characters."""
        password = "пароль123日本語"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_with_empty_string(self):
        """Test hashing empty string."""
        hashed = hash_password("")
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_hash_password_with_special_characters(self):
        """Test hashing password with special characters."""
        password = "P@$$w0rd!#$%^&*()"
        hashed = hash_password(password)
        assert isinstance(hashed, str)

    def test_hash_password_with_long_password(self):
        """Test hashing very long password (bcrypt truncates at 72 bytes)."""
        # bcrypt has a 72-byte limit, so test with 72 chars
        password = "a" * 72
        hashed = hash_password(password)
        assert isinstance(hashed, str)

    def test_hash_password_exceeding_bcrypt_limit(self):
        """Test that password exceeding bcrypt limit raises error."""
        password = "a" * 1000  # Exceeds bcrypt's 72-byte limit
        with pytest.raises(ValueError):
            hash_password(password)


class TestVerifyPassword:
    """Tests for verify_password function."""

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "correctpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "correctpassword"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_with_unicode(self):
        """Test verifying unicode password."""
        password = "пароль123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("пароль124", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test verifying against invalid hash returns False."""
        assert verify_password("password", "not-a-valid-hash") is False

    def test_verify_password_empty_hash(self):
        """Test verifying against empty hash returns False."""
        assert verify_password("password", "") is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "MyPassword"
        hashed = hash_password(password)
        assert verify_password("MyPassword", hashed) is True
        assert verify_password("mypassword", hashed) is False
        assert verify_password("MYPASSWORD", hashed) is False

    def test_verify_password_whitespace_sensitive(self):
        """Test that whitespace matters in password."""
        password = "password "
        hashed = hash_password(password)
        assert verify_password("password ", hashed) is True
        assert verify_password("password", hashed) is False

    def test_verify_empty_password(self):
        """Test verifying empty password."""
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password(" ", hashed) is False
