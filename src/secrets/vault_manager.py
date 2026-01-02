"""HashiCorp Vault Secrets Manager.

Production-ready secrets management using HashiCorp Vault.
"""

from typing import Any

import hvac
from hvac.exceptions import InvalidPath

from src.config.logging import get_logger

logger = get_logger(__name__)


class VaultSecretsManager:
    """Secrets manager using HashiCorp Vault.

    Uses the KV v2 secrets engine for storing and retrieving secrets.
    Supports both dev mode (token auth) and production (AppRole auth).
    """

    def __init__(
        self,
        vault_url: str,
        vault_token: str | None = None,
        mount_point: str = "secret",
        namespace: str | None = None,
    ):
        """Initialize the Vault secrets manager.

        Args:
            vault_url: Vault server URL (e.g., http://localhost:8200)
            vault_token: Authentication token (for dev/simple auth)
            mount_point: KV secrets engine mount point (default: "secret")
            namespace: Vault namespace (for enterprise)
        """
        self._mount_point = mount_point
        self._client = hvac.Client(
            url=vault_url,
            token=vault_token,
            namespace=namespace,
        )

        if not self._client.is_authenticated():
            raise RuntimeError(
                f"Failed to authenticate with Vault at {vault_url}. "
                "Check VAULT_TOKEN or authentication configuration."
            )

        logger.info("vault_connected", url=vault_url, mount_point=mount_point)

        # Ensure KV v2 engine is enabled (in dev mode it's auto-enabled)
        self._ensure_kv_engine()

    def _ensure_kv_engine(self) -> None:
        """Ensure KV v2 secrets engine is enabled."""
        try:
            # Check if mount point exists
            mounts = self._client.sys.list_mounted_secrets_engines()
            mount_key = f"{self._mount_point}/"

            if mount_key not in mounts:
                # Enable KV v2 engine
                self._client.sys.enable_secrets_engine(
                    backend_type="kv",
                    path=self._mount_point,
                    options={"version": "2"},
                )
                logger.info("vault_kv_engine_enabled", mount_point=self._mount_point)
        except Exception as e:
            # In dev mode, this might fail but the engine is already there
            logger.debug("vault_kv_engine_check", error=str(e))

    async def store(self, key: str, value: dict[str, Any]) -> None:
        """Store a secret in Vault.

        Args:
            key: Unique identifier for the secret (can include path separators)
            value: Dictionary of secret key-value pairs
        """
        try:
            self._client.secrets.kv.v2.create_or_update_secret(
                path=key,
                secret=value,
                mount_point=self._mount_point,
            )
            logger.info("vault_secret_stored", key=key)
        except Exception as e:
            logger.error("vault_secret_store_failed", key=key, error=str(e))
            raise

    async def retrieve(self, key: str) -> dict[str, Any] | None:
        """Retrieve a secret from Vault.

        Args:
            key: Unique identifier for the secret

        Returns:
            Dictionary of secret data or None if not found
        """
        try:
            response = self._client.secrets.kv.v2.read_secret_version(
                path=key,
                mount_point=self._mount_point,
            )
            return response["data"]["data"]
        except InvalidPath:
            logger.debug("vault_secret_not_found", key=key)
            return None
        except Exception as e:
            logger.error("vault_secret_retrieve_failed", key=key, error=str(e))
            raise

    async def delete(self, key: str) -> bool:
        """Delete a secret from Vault.

        Permanently deletes all versions and metadata.

        Args:
            key: Unique identifier for the secret

        Returns:
            True if deleted, False if not found
        """
        try:
            self._client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=key,
                mount_point=self._mount_point,
            )
            logger.info("vault_secret_deleted", key=key)
            return True
        except InvalidPath:
            logger.debug("vault_secret_not_found_for_delete", key=key)
            return False
        except Exception as e:
            logger.error("vault_secret_delete_failed", key=key, error=str(e))
            raise

    async def exists(self, key: str) -> bool:
        """Check if a secret exists in Vault.

        Args:
            key: Unique identifier for the secret

        Returns:
            True if secret exists
        """
        try:
            self._client.secrets.kv.v2.read_secret_version(
                path=key,
                mount_point=self._mount_point,
            )
            return True
        except InvalidPath:
            return False
        except Exception as e:
            logger.error("vault_secret_exists_check_failed", key=key, error=str(e))
            raise

    async def list_keys(self, path: str = "") -> list[str]:
        """List all secret keys under a path.

        Args:
            path: Path prefix to list (empty for root)

        Returns:
            List of secret keys
        """
        all_keys = []

        try:
            response = self._client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=self._mount_point,
            )
            keys = response["data"]["keys"]

            for key in keys:
                full_path = f"{path}{key}" if path else key

                if key.endswith("/"):
                    # It's a directory, recurse
                    nested_keys = await self.list_keys(full_path)
                    all_keys.extend(nested_keys)
                else:
                    all_keys.append(full_path)

        except InvalidPath:
            # No secrets at this path
            pass
        except Exception as e:
            logger.error("vault_list_keys_failed", path=path, error=str(e))
            raise

        return all_keys
