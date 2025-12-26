"""Base interface for secrets management."""

from abc import ABC, abstractmethod
from typing import Dict


class SecretsManager(ABC):
    """Abstract interface for secrets storage.

    Implementations can use HashiCorp Vault, AWS Secrets Manager,
    Azure Key Vault, or local encrypted storage.
    """

    @abstractmethod
    async def store(self, key: str, value: Dict[str, str]) -> str:
        """Store credentials and return a secret reference.

        Args:
            key: Unique identifier for the secret (e.g., "mcp/servers/srv_abc123")
            value: Dictionary of credential key-value pairs

        Returns:
            Secret reference (path) that can be used to retrieve the credentials
        """
        pass

    @abstractmethod
    async def retrieve(self, secret_ref: str) -> Dict[str, str]:
        """Retrieve credentials by reference.

        Args:
            secret_ref: Secret reference returned from store()

        Returns:
            Dictionary of credential key-value pairs

        Raises:
            KeyError: If secret not found
        """
        pass

    @abstractmethod
    async def delete(self, secret_ref: str) -> None:
        """Delete credentials.

        Args:
            secret_ref: Secret reference to delete

        Raises:
            KeyError: If secret not found
        """
        pass

    @abstractmethod
    async def exists(self, secret_ref: str) -> bool:
        """Check if a secret exists.

        Args:
            secret_ref: Secret reference to check

        Returns:
            True if secret exists, False otherwise
        """
        pass

    @abstractmethod
    async def list_keys(self) -> list[str]:
        """List all secret keys.

        Returns:
            List of secret key names (not values)
        """
        pass
