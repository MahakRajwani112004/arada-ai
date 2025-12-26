"""Factory for creating secrets manager based on configuration."""

from typing import Optional

from .base import SecretsManager
from .local import LocalEncryptedManager
from .vault import VaultSecretsManager


_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get the configured secrets manager singleton.

    Returns:
        SecretsManager instance

    Raises:
        RuntimeError: If secrets manager not initialized
    """
    if _secrets_manager is None:
        raise RuntimeError(
            "SecretsManager not initialized. Call init_secrets_manager() first."
        )
    return _secrets_manager


def init_secrets_manager(
    provider: Optional[str] = None,
    encryption_key: Optional[str] = None,
    storage_path: Optional[str] = None,
    vault_url: Optional[str] = None,
    vault_token: Optional[str] = None,
    aws_region: Optional[str] = None,
) -> SecretsManager:
    """Initialize the secrets manager singleton.

    If no arguments provided, loads from application settings.

    Args:
        provider: Vault provider ("local", "hashicorp", "aws", "azure")
        encryption_key: Fernet key for local provider
        storage_path: Storage path for local provider
        vault_url: HashiCorp Vault URL
        vault_token: HashiCorp Vault token
        aws_region: AWS region for Secrets Manager

    Returns:
        Configured SecretsManager instance
    """
    global _secrets_manager

    # Load from settings if no arguments provided
    if provider is None:
        from src.config.settings import get_settings

        settings = get_settings()
        provider = settings.vault_provider
        encryption_key = encryption_key or settings.secrets_encryption_key
        storage_path = storage_path or settings.secrets_storage_path
        vault_url = vault_url or settings.vault_url
        vault_token = vault_token or settings.vault_token
        aws_region = aws_region or settings.aws_secrets_region

    if provider == "local":
        if not encryption_key:
            encryption_key = LocalEncryptedManager.generate_key()
        _secrets_manager = LocalEncryptedManager(
            encryption_key=encryption_key,
            storage_path=storage_path,
        )
    elif provider == "hashicorp":
        if not vault_url or not vault_token:
            raise ValueError(
                "HashiCorp Vault requires VAULT_URL and VAULT_TOKEN environment variables"
            )
        _secrets_manager = VaultSecretsManager(
            vault_url=vault_url,
            vault_token=vault_token,
        )
    elif provider == "aws":
        raise NotImplementedError("AWS Secrets Manager support coming soon")
    elif provider == "azure":
        raise NotImplementedError("Azure Key Vault support coming soon")
    else:
        raise ValueError(f"Unknown vault provider: {provider}")

    return _secrets_manager


async def close_secrets_manager() -> None:
    """Close the secrets manager (cleanup)."""
    global _secrets_manager
    _secrets_manager = None
