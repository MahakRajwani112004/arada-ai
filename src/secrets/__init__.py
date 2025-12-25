"""Secrets management module for storing and retrieving sensitive credentials.

Supports multiple backends:
- local: Encrypted local file storage (development)
- hashicorp: HashiCorp Vault (production)
"""

from typing import Any, Protocol, runtime_checkable

from src.config import get_settings
from src.config.logging import get_logger

logger = get_logger(__name__)


@runtime_checkable
class SecretsManagerProtocol(Protocol):
    """Protocol defining the secrets manager interface."""

    async def store(self, key: str, value: dict[str, Any]) -> None:
        """Store a secret."""
        ...

    async def retrieve(self, key: str) -> dict[str, Any] | None:
        """Retrieve a secret."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete a secret."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if a secret exists."""
        ...

    async def list_keys(self, path: str = "") -> list[str]:
        """List all secret keys."""
        ...


# Global instance
_secrets_manager: SecretsManagerProtocol | None = None


def init_secrets_manager(
    provider: str | None = None,
    **kwargs,
) -> SecretsManagerProtocol:
    """Initialize the global secrets manager based on configuration.

    Args:
        provider: Override provider (local, hashicorp). If not specified, uses settings.
        **kwargs: Additional arguments passed to the specific manager.

    Returns:
        Initialized secrets manager instance
    """
    global _secrets_manager

    settings = get_settings()
    provider = provider or settings.vault_provider

    if provider == "hashicorp":
        from .vault_manager import VaultSecretsManager

        vault_url = kwargs.get("vault_url") or settings.vault_url
        vault_token = kwargs.get("vault_token") or settings.vault_token

        if not vault_url:
            raise ValueError(
                "VAULT_URL is required when using HashiCorp Vault. "
                "Set it in your environment or .env file."
            )
        if not vault_token:
            raise ValueError(
                "VAULT_TOKEN is required when using HashiCorp Vault. "
                "Set it in your environment or .env file."
            )

        _secrets_manager = VaultSecretsManager(
            vault_url=vault_url,
            vault_token=vault_token,
            mount_point=kwargs.get("mount_point", "secret"),
        )
        logger.info("secrets_manager_initialized", provider="hashicorp", url=vault_url)

    elif provider == "local":
        from .manager import SecretsManager

        _secrets_manager = SecretsManager(
            encryption_key=kwargs.get("encryption_key") or settings.secrets_encryption_key,
            storage_path=kwargs.get("storage_path") or settings.secrets_storage_path,
        )
        logger.info("secrets_manager_initialized", provider="local")

    else:
        raise ValueError(
            f"Unsupported vault provider: {provider}. "
            "Supported providers: local, hashicorp"
        )

    return _secrets_manager


def get_secrets_manager() -> SecretsManagerProtocol:
    """Get the global secrets manager instance.

    Auto-initializes based on settings if not already initialized.

    Returns:
        SecretsManager instance
    """
    global _secrets_manager

    if _secrets_manager is None:
        settings = get_settings()
        init_secrets_manager(provider=settings.vault_provider)

    return _secrets_manager


# Re-export for backwards compatibility
from .manager import SecretsManager
from .vault_manager import VaultSecretsManager

__all__ = [
    "SecretsManager",
    "VaultSecretsManager",
    "SecretsManagerProtocol",
    "get_secrets_manager",
    "init_secrets_manager",
]
