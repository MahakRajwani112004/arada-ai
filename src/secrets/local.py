"""Local encrypted storage for secrets (dev/testing)."""

import json
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote, unquote

import aiofiles
import aiofiles.os
from cryptography.fernet import Fernet

from .base import SecretsManager


class LocalEncryptedManager(SecretsManager):
    """Local encrypted storage using Fernet symmetric encryption.

    This is suitable for development and testing. For production,
    use HashiCorp Vault or cloud provider secrets managers.
    """

    def __init__(
        self,
        encryption_key: str,
        storage_path: Optional[str] = None,
    ):
        """Initialize local encrypted storage.

        Args:
            encryption_key: Fernet encryption key (base64-encoded 32 bytes)
            storage_path: Path to store encrypted secrets. Defaults to ~/.magure/secrets
        """
        self._fernet = Fernet(encryption_key.encode())
        self._storage_path = Path(storage_path) if storage_path else self._default_path()
        self._storage_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _default_path() -> Path:
        """Get default storage path."""
        return Path.home() / ".magure" / "secrets"

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet encryption key.

        Returns:
            Base64-encoded 32-byte key string
        """
        return Fernet.generate_key().decode()

    def _secret_file(self, secret_ref: str) -> Path:
        """Get path to secret file.

        Uses URL encoding to safely convert keys to filenames.
        This allows keys with slashes and other special characters.
        """
        # URL encode the key - safe='' means encode everything except alphanumerics
        safe_name = quote(secret_ref, safe='')
        return self._storage_path / f"{safe_name}.enc"

    def _legacy_secret_file(self, secret_ref: str) -> Path:
        """Get legacy path (underscore-based) for backward compatibility."""
        safe_name = secret_ref.replace("/", "_").replace("\\", "_")
        return self._storage_path / f"{safe_name}.enc"

    def _find_secret_file(self, secret_ref: str) -> Path | None:
        """Find secret file, checking both new and legacy formats."""
        # Try new format first
        new_path = self._secret_file(secret_ref)
        if new_path.exists():
            return new_path
        # Try legacy format
        legacy_path = self._legacy_secret_file(secret_ref)
        if legacy_path.exists():
            return legacy_path
        return None

    async def store(self, key: str, value: Dict[str, str]) -> str:
        """Store credentials encrypted locally using async file I/O."""
        secret_ref = key
        encrypted = self._fernet.encrypt(json.dumps(value).encode())

        secret_file = self._secret_file(secret_ref)
        async with aiofiles.open(secret_file, "wb") as f:
            await f.write(encrypted)

        return secret_ref

    async def retrieve(self, secret_ref: str) -> Dict[str, str]:
        """Retrieve and decrypt credentials using async file I/O."""
        secret_file = self._find_secret_file(secret_ref)

        if secret_file is None:
            raise KeyError(f"Secret not found: {secret_ref}")

        async with aiofiles.open(secret_file, "rb") as f:
            encrypted = await f.read()

        decrypted = self._fernet.decrypt(encrypted)
        return json.loads(decrypted.decode())

    async def delete(self, secret_ref: str) -> None:
        """Delete encrypted secret file using async file I/O."""
        secret_file = self._find_secret_file(secret_ref)

        if secret_file is None:
            raise KeyError(f"Secret not found: {secret_ref}")

        await aiofiles.os.remove(secret_file)

    async def exists(self, secret_ref: str) -> bool:
        """Check if secret file exists."""
        return self._find_secret_file(secret_ref) is not None

    async def list_keys(self) -> list[str]:
        """List all secret keys stored locally."""
        keys = []
        for file in self._storage_path.glob("*.enc"):
            filename = file.stem
            # Check if it's URL encoded (contains %XX patterns)
            if '%' in filename:
                # New format: URL encoded
                key = unquote(filename)
            else:
                # Legacy format: underscores replaced slashes
                # Try to detect the pattern - oauth_google_xxx or mcp_servers_xxx
                if filename.startswith("oauth_"):
                    # oauth_google_calendar -> oauth/google/calendar
                    key = filename.replace("_", "/")
                elif filename.startswith("mcp_servers_"):
                    # mcp_servers_srv_xxx -> mcp_servers/srv_xxx
                    key = "mcp_servers/" + filename[12:]
                else:
                    # Unknown format, use as-is
                    key = filename
            keys.append(key)
        return sorted(keys)
