"""HashiCorp Vault secrets management."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

import hvac
from hvac.exceptions import InvalidPath

from src.config.logging import get_logger

from .base import SecretsManager

logger = get_logger(__name__)

# Renew token when less than this many seconds remaining
TOKEN_RENEWAL_THRESHOLD_SECONDS = 300  # 5 minutes


class VaultSecretsManager(SecretsManager):
    """HashiCorp Vault secrets manager using KV v2 secrets engine.

    This is the recommended secrets manager for production deployments.
    Provides audit logging, access policies, and automatic token rotation.

    All hvac calls are wrapped with asyncio.to_thread() to prevent
    blocking the event loop.
    """

    def __init__(
        self,
        vault_url: str,
        vault_token: str,
        mount_point: str = "secret",
        path_prefix: str = "magure",
    ):
        """Initialize Vault secrets manager.

        Args:
            vault_url: Vault server URL (e.g., http://localhost:8200)
            vault_token: Vault authentication token
            mount_point: KV v2 secrets engine mount point (default: "secret")
            path_prefix: Prefix for all secrets paths (default: "magure")
        """
        self._client = hvac.Client(url=vault_url, token=vault_token)
        self._mount_point = mount_point
        self._path_prefix = path_prefix
        self._token_expires_at: Optional[datetime] = None
        self._token_renewable: bool = False

        # Verify connection and get token info
        if not self._client.is_authenticated():
            raise RuntimeError("Failed to authenticate with Vault")

        # Get token TTL info for renewal tracking
        self._update_token_info()

        logger.info(
            "vault_secrets_manager_initialized",
            vault_url=vault_url,
            mount_point=mount_point,
            path_prefix=path_prefix,
            token_renewable=self._token_renewable,
            token_expires_at=self._token_expires_at.isoformat() if self._token_expires_at else None,
        )

    def _update_token_info(self) -> None:
        """Update token expiration info from Vault."""
        try:
            token_info = self._client.auth.token.lookup_self()
            data = token_info.get("data", {})

            # Check if token is renewable
            self._token_renewable = data.get("renewable", False)

            # Get TTL and calculate expiration time
            ttl = data.get("ttl", 0)
            if ttl > 0:
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            else:
                # Token never expires (root token or infinite TTL)
                self._token_expires_at = None

        except Exception as e:
            logger.warning("vault_token_lookup_failed", error=str(e))
            self._token_renewable = False
            self._token_expires_at = None

    async def _check_and_renew_token(self) -> None:
        """Check if token needs renewal and renew if possible.

        Should be called before Vault operations to ensure token validity.
        """
        if not self._token_renewable or self._token_expires_at is None:
            return

        time_remaining = (self._token_expires_at - datetime.utcnow()).total_seconds()

        if time_remaining <= TOKEN_RENEWAL_THRESHOLD_SECONDS:
            try:
                await asyncio.to_thread(self._client.auth.token.renew_self)
                self._update_token_info()
                logger.info(
                    "vault_token_renewed",
                    new_expires_at=self._token_expires_at.isoformat() if self._token_expires_at else None,
                )
            except Exception as e:
                logger.error("vault_token_renewal_failed", error=str(e))

    def _full_path(self, key: str) -> str:
        """Get full path with prefix."""
        return f"{self._path_prefix}/{key}"

    async def store(self, key: str, value: Dict[str, str]) -> str:
        """Store credentials in Vault.

        Args:
            key: Unique identifier for the secret
            value: Dictionary of credential key-value pairs

        Returns:
            Secret reference (path) for retrieval
        """
        await self._check_and_renew_token()
        path = self._full_path(key)

        try:
            await asyncio.to_thread(
                self._client.secrets.kv.v2.create_or_update_secret,
                path=path,
                secret=value,
                mount_point=self._mount_point,
            )
            logger.info("vault_secret_stored", path=path)
            return key
        except Exception as e:
            logger.error("vault_secret_store_failed", path=path, error=str(e))
            raise

    async def retrieve(self, secret_ref: str) -> Dict[str, str]:
        """Retrieve credentials from Vault.

        Args:
            secret_ref: Secret reference returned from store()

        Returns:
            Dictionary of credential key-value pairs

        Raises:
            KeyError: If secret not found
        """
        await self._check_and_renew_token()
        path = self._full_path(secret_ref)

        try:
            response = await asyncio.to_thread(
                self._client.secrets.kv.v2.read_secret_version,
                path=path,
                mount_point=self._mount_point,
            )
            return response["data"]["data"]
        except InvalidPath:
            raise KeyError(f"Secret not found: {secret_ref}")
        except Exception as e:
            logger.error("vault_secret_retrieve_failed", path=path, error=str(e))
            raise

    async def delete(self, secret_ref: str) -> None:
        """Delete credentials from Vault.

        Args:
            secret_ref: Secret reference to delete

        Raises:
            KeyError: If secret not found
        """
        await self._check_and_renew_token()
        path = self._full_path(secret_ref)

        try:
            # Check if exists first
            if not await self.exists(secret_ref):
                raise KeyError(f"Secret not found: {secret_ref}")

            # Delete all versions and metadata
            await asyncio.to_thread(
                self._client.secrets.kv.v2.delete_metadata_and_all_versions,
                path=path,
                mount_point=self._mount_point,
            )
            logger.info("vault_secret_deleted", path=path)
        except KeyError:
            raise
        except Exception as e:
            logger.error("vault_secret_delete_failed", path=path, error=str(e))
            raise

    async def exists(self, secret_ref: str) -> bool:
        """Check if a secret exists in Vault.

        Args:
            secret_ref: Secret reference to check

        Returns:
            True if secret exists, False otherwise
        """
        await self._check_and_renew_token()
        path = self._full_path(secret_ref)

        try:
            await asyncio.to_thread(
                self._client.secrets.kv.v2.read_secret_version,
                path=path,
                mount_point=self._mount_point,
            )
            return True
        except InvalidPath:
            return False
        except Exception as e:
            logger.error("vault_secret_exists_check_failed", path=path, error=str(e))
            return False

    async def list_keys(self) -> list[str]:
        """List all secret keys in the vault.

        Returns:
            List of secret key names (not values)
        """
        await self._check_and_renew_token()
        return await self._list_recursive(self._path_prefix)

    async def _list_recursive(self, path: str) -> list[str]:
        """Recursively list all secrets under a path.

        Args:
            path: Path to list

        Returns:
            List of full secret paths
        """
        keys = []

        try:
            response = await asyncio.to_thread(
                self._client.secrets.kv.v2.list_secrets,
                path=path,
                mount_point=self._mount_point,
            )
            items = response["data"]["keys"]

            for item in items:
                full_item = f"{path}/{item}".lstrip("/")
                if item.endswith("/"):
                    # It's a folder, recurse
                    keys.extend(await self._list_recursive(full_item.rstrip("/")))
                else:
                    # It's a secret, strip the prefix
                    key = full_item.replace(f"{self._path_prefix}/", "", 1)
                    keys.append(key)
        except InvalidPath:
            pass
        except Exception as e:
            logger.error("vault_secret_list_failed", path=path, error=str(e))

        return sorted(keys)
