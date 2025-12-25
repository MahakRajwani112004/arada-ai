"""Secrets Manager for storing and retrieving sensitive credentials.

This implementation uses Fernet encryption to store secrets locally.
In production, this should be replaced with a proper vault solution
like HashiCorp Vault, AWS Secrets Manager, or Google Secret Manager.
"""

import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

from src.config import get_settings


class SecretsManager:
    """Manages storage and retrieval of encrypted secrets.

    Uses Fernet symmetric encryption for local storage.
    Secrets are stored in a JSON file, encrypted with a key from environment.
    """

    def __init__(self, encryption_key: str | None = None, storage_path: str | None = None):
        """Initialize the secrets manager.

        Args:
            encryption_key: Fernet encryption key. If not provided, uses env var.
            storage_path: Path to store encrypted secrets. Defaults to ~/.magoneai/secrets.json
        """
        self._key = encryption_key or os.getenv("SECRETS_ENCRYPTION_KEY")

        # Generate a key if not provided (for development)
        if not self._key or self._key == "your-fernet-encryption-key":
            self._key = Fernet.generate_key().decode()

        self._fernet = Fernet(self._key.encode() if isinstance(self._key, str) else self._key)

        if storage_path:
            self._storage_path = Path(storage_path)
        else:
            self._storage_path = Path.home() / ".magoneai" / "secrets.json"

        # Ensure directory exists
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize storage file if it doesn't exist
        if not self._storage_path.exists():
            self._save_secrets({})

    def _load_secrets(self) -> dict[str, Any]:
        """Load and decrypt all secrets from storage."""
        try:
            with open(self._storage_path, "r") as f:
                encrypted_data = f.read()
                if not encrypted_data:
                    return {}
                decrypted = self._fernet.decrypt(encrypted_data.encode())
                return json.loads(decrypted.decode())
        except Exception:
            return {}

    def _save_secrets(self, secrets: dict[str, Any]) -> None:
        """Encrypt and save all secrets to storage."""
        encrypted = self._fernet.encrypt(json.dumps(secrets).encode())
        with open(self._storage_path, "w") as f:
            f.write(encrypted.decode())

    async def store(self, key: str, value: dict[str, str]) -> None:
        """Store a secret under the given key.

        Args:
            key: Unique identifier for the secret
            value: Dictionary of credential key-value pairs
        """
        secrets = self._load_secrets()
        secrets[key] = value
        self._save_secrets(secrets)

    async def retrieve(self, key: str) -> dict[str, str] | None:
        """Retrieve a secret by key.

        Args:
            key: Unique identifier for the secret

        Returns:
            Dictionary of credentials or None if not found
        """
        secrets = self._load_secrets()
        return secrets.get(key)

    async def delete(self, key: str) -> bool:
        """Delete a secret by key.

        Args:
            key: Unique identifier for the secret

        Returns:
            True if deleted, False if not found
        """
        secrets = self._load_secrets()
        if key in secrets:
            del secrets[key]
            self._save_secrets(secrets)
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a secret exists.

        Args:
            key: Unique identifier for the secret

        Returns:
            True if secret exists
        """
        secrets = self._load_secrets()
        return key in secrets

    async def list_keys(self, path: str = "") -> list[str]:
        """List all secret keys, optionally filtered by path prefix.

        Args:
            path: Optional path prefix to filter keys

        Returns:
            List of secret keys
        """
        secrets = self._load_secrets()
        if path:
            return [k for k in secrets.keys() if k.startswith(path)]
        return list(secrets.keys())


# Global instance
_secrets_manager: SecretsManager | None = None


def init_secrets_manager(encryption_key: str | None = None, storage_path: str | None = None) -> SecretsManager:
    """Initialize the global secrets manager.

    Args:
        encryption_key: Optional encryption key override
        storage_path: Optional storage path override

    Returns:
        Initialized SecretsManager instance
    """
    global _secrets_manager
    _secrets_manager = SecretsManager(encryption_key=encryption_key, storage_path=storage_path)
    return _secrets_manager


def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance.

    Returns:
        SecretsManager instance

    Raises:
        RuntimeError: If secrets manager not initialized
    """
    global _secrets_manager
    if _secrets_manager is None:
        # Auto-initialize with defaults for convenience
        _secrets_manager = SecretsManager()
    return _secrets_manager
