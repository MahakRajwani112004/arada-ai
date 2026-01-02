"""Comprehensive unit tests for the secrets module.

Tests cover:
- LocalEncryptedManager: store, retrieve, delete, exists, list_keys
- VaultSecretsManager: store, retrieve, delete, exists, list_keys with mocked hvac client
- Factory: init_secrets_manager, get_secrets_manager, close_secrets_manager
- Error handling for missing secrets, invalid providers, and auth failures
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from cryptography.fernet import Fernet

from src.secrets.base import SecretsManager
from src.secrets.local import LocalEncryptedManager
from src.secrets.vault import VaultSecretsManager
from src.secrets import factory


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def encryption_key():
    """Generate a valid Fernet encryption key for testing."""
    return Fernet.generate_key().decode()


@pytest.fixture
def temp_storage_path(tmp_path):
    """Create a temporary directory for secret storage."""
    storage_dir = tmp_path / "secrets"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return str(storage_dir)


@pytest.fixture
def local_manager(encryption_key, temp_storage_path):
    """Create a LocalEncryptedManager with test configuration."""
    return LocalEncryptedManager(
        encryption_key=encryption_key,
        storage_path=temp_storage_path,
    )


@pytest.fixture
def mock_hvac_client():
    """Create a mock hvac client for Vault testing."""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True

    # Mock token lookup for initialization
    mock_client.auth.token.lookup_self.return_value = {
        "data": {
            "renewable": False,
            "ttl": 0,
        }
    }

    # Mock KV v2 operations
    mock_client.secrets.kv.v2 = MagicMock()

    return mock_client


@pytest.fixture
def sample_credentials():
    """Sample credential data for testing."""
    return {
        "api_key": "sk-test-12345",
        "api_secret": "secret-value-67890",
        "endpoint": "https://api.example.com",
    }


# ============================================================================
# LocalEncryptedManager Tests
# ============================================================================


class TestLocalEncryptedManagerInitialization:
    """Tests for LocalEncryptedManager initialization."""

    def test_init_creates_storage_directory(self, encryption_key, tmp_path):
        """Test that initialization creates the storage directory."""
        storage_path = tmp_path / "new_secrets_dir"
        assert not storage_path.exists()

        LocalEncryptedManager(
            encryption_key=encryption_key,
            storage_path=str(storage_path),
        )

        assert storage_path.exists()
        assert storage_path.is_dir()

    def test_init_uses_default_path_when_not_provided(self, encryption_key):
        """Test that default path is used when storage_path is None."""
        manager = LocalEncryptedManager(encryption_key=encryption_key)
        expected_path = Path.home() / ".magure" / "secrets"
        assert manager._storage_path == expected_path

    def test_generate_key_returns_valid_fernet_key(self):
        """Test that generate_key produces a valid Fernet key."""
        key = LocalEncryptedManager.generate_key()

        assert isinstance(key, str)
        # Should be valid for Fernet
        fernet = Fernet(key.encode())
        assert fernet is not None

    def test_generate_key_unique_each_call(self):
        """Test that generate_key produces unique keys."""
        key1 = LocalEncryptedManager.generate_key()
        key2 = LocalEncryptedManager.generate_key()

        assert key1 != key2


class TestLocalEncryptedManagerStore:
    """Tests for LocalEncryptedManager.store method."""

    @pytest.mark.asyncio
    async def test_store_returns_key_as_reference(self, local_manager, sample_credentials):
        """Test that store returns the key as the secret reference."""
        key = "oauth/google/calendar"
        result = await local_manager.store(key, sample_credentials)

        assert result == key

    @pytest.mark.asyncio
    async def test_store_creates_encrypted_file(self, local_manager, sample_credentials, temp_storage_path):
        """Test that store creates an encrypted file."""
        key = "test_secret"
        await local_manager.store(key, sample_credentials)

        # Check file exists (URL encoded filename)
        files = list(Path(temp_storage_path).glob("*.enc"))
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_store_file_is_encrypted(self, local_manager, sample_credentials, temp_storage_path):
        """Test that stored file content is encrypted (not plaintext JSON)."""
        key = "test_secret"
        await local_manager.store(key, sample_credentials)

        files = list(Path(temp_storage_path).glob("*.enc"))
        content = files[0].read_bytes()

        # Content should not be valid JSON (it's encrypted)
        with pytest.raises(json.JSONDecodeError):
            json.loads(content.decode())

    @pytest.mark.asyncio
    async def test_store_with_special_characters_in_key(self, local_manager, sample_credentials):
        """Test storing secrets with special characters in the key."""
        key = "mcp/servers/srv_abc123/credentials"
        result = await local_manager.store(key, sample_credentials)

        assert result == key
        assert await local_manager.exists(key)

    @pytest.mark.asyncio
    async def test_store_overwrites_existing_secret(self, local_manager, sample_credentials):
        """Test that storing with same key overwrites existing secret."""
        key = "test_secret"
        original_creds = {"old_key": "old_value"}
        new_creds = {"new_key": "new_value"}

        await local_manager.store(key, original_creds)
        await local_manager.store(key, new_creds)

        retrieved = await local_manager.retrieve(key)
        assert retrieved == new_creds
        assert "old_key" not in retrieved


class TestLocalEncryptedManagerRetrieve:
    """Tests for LocalEncryptedManager.retrieve method."""

    @pytest.mark.asyncio
    async def test_retrieve_returns_stored_credentials(self, local_manager, sample_credentials):
        """Test that retrieve returns the exact credentials that were stored."""
        key = "test_secret"
        await local_manager.store(key, sample_credentials)

        retrieved = await local_manager.retrieve(key)

        assert retrieved == sample_credentials

    @pytest.mark.asyncio
    async def test_retrieve_missing_secret_raises_keyerror(self, local_manager):
        """Test that retrieving non-existent secret raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            await local_manager.retrieve("nonexistent_secret")

        assert "Secret not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retrieve_with_special_characters_in_key(self, local_manager, sample_credentials):
        """Test retrieving secrets with special characters in the key."""
        key = "oauth/google/calendar"
        await local_manager.store(key, sample_credentials)

        retrieved = await local_manager.retrieve(key)

        assert retrieved == sample_credentials

    @pytest.mark.asyncio
    async def test_retrieve_preserves_data_types(self, local_manager):
        """Test that retrieve preserves string data types."""
        credentials = {
            "string_val": "test",
            "numeric_string": "12345",
            "empty_string": "",
        }
        key = "type_test"
        await local_manager.store(key, credentials)

        retrieved = await local_manager.retrieve(key)

        assert all(isinstance(v, str) for v in retrieved.values())
        assert retrieved == credentials


class TestLocalEncryptedManagerDelete:
    """Tests for LocalEncryptedManager.delete method."""

    @pytest.mark.asyncio
    async def test_delete_removes_secret(self, local_manager, sample_credentials):
        """Test that delete removes the secret."""
        key = "test_secret"
        await local_manager.store(key, sample_credentials)

        await local_manager.delete(key)

        assert not await local_manager.exists(key)

    @pytest.mark.asyncio
    async def test_delete_removes_file(self, local_manager, sample_credentials, temp_storage_path):
        """Test that delete removes the encrypted file."""
        key = "test_secret"
        await local_manager.store(key, sample_credentials)

        files_before = list(Path(temp_storage_path).glob("*.enc"))
        assert len(files_before) == 1

        await local_manager.delete(key)

        files_after = list(Path(temp_storage_path).glob("*.enc"))
        assert len(files_after) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises_keyerror(self, local_manager):
        """Test that deleting non-existent secret raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            await local_manager.delete("nonexistent_secret")

        assert "Secret not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_with_special_characters_in_key(self, local_manager, sample_credentials):
        """Test deleting secrets with special characters in the key."""
        key = "mcp/servers/srv_123"
        await local_manager.store(key, sample_credentials)

        await local_manager.delete(key)

        assert not await local_manager.exists(key)


class TestLocalEncryptedManagerExists:
    """Tests for LocalEncryptedManager.exists method."""

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_stored_secret(self, local_manager, sample_credentials):
        """Test that exists returns True for stored secret."""
        key = "test_secret"
        await local_manager.store(key, sample_credentials)

        assert await local_manager.exists(key) is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_missing_secret(self, local_manager):
        """Test that exists returns False for non-existent secret."""
        assert await local_manager.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_exists_returns_false_after_delete(self, local_manager, sample_credentials):
        """Test that exists returns False after secret is deleted."""
        key = "test_secret"
        await local_manager.store(key, sample_credentials)
        await local_manager.delete(key)

        assert await local_manager.exists(key) is False


class TestLocalEncryptedManagerListKeys:
    """Tests for LocalEncryptedManager.list_keys method."""

    @pytest.mark.asyncio
    async def test_list_keys_empty_storage(self, local_manager):
        """Test list_keys returns empty list for empty storage."""
        keys = await local_manager.list_keys()
        assert keys == []

    @pytest.mark.asyncio
    async def test_list_keys_returns_all_keys(self, local_manager, sample_credentials):
        """Test list_keys returns all stored secret keys."""
        keys_to_store = ["secret1", "secret2", "secret3"]

        for key in keys_to_store:
            await local_manager.store(key, sample_credentials)

        listed_keys = await local_manager.list_keys()

        assert len(listed_keys) == 3
        assert set(listed_keys) == set(keys_to_store)

    @pytest.mark.asyncio
    async def test_list_keys_returns_sorted_keys(self, local_manager, sample_credentials):
        """Test list_keys returns keys in sorted order."""
        keys_to_store = ["zebra", "alpha", "mango"]

        for key in keys_to_store:
            await local_manager.store(key, sample_credentials)

        listed_keys = await local_manager.list_keys()

        assert listed_keys == sorted(keys_to_store)

    @pytest.mark.asyncio
    async def test_list_keys_with_special_characters(self, local_manager, sample_credentials):
        """Test list_keys handles keys with special characters."""
        keys_to_store = ["oauth/google/calendar", "mcp/servers/srv_123"]

        for key in keys_to_store:
            await local_manager.store(key, sample_credentials)

        listed_keys = await local_manager.list_keys()

        assert len(listed_keys) == 2


# ============================================================================
# VaultSecretsManager Tests (with mocked hvac client)
# ============================================================================


class TestVaultSecretsManagerInitialization:
    """Tests for VaultSecretsManager initialization."""

    def test_init_with_valid_credentials(self, mock_hvac_client):
        """Test successful initialization with valid credentials."""
        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            assert manager._mount_point == "secret"
            assert manager._path_prefix == "magure"

    def test_init_with_custom_mount_point(self, mock_hvac_client):
        """Test initialization with custom mount point."""
        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
                mount_point="custom-secret",
                path_prefix="myapp",
            )

            assert manager._mount_point == "custom-secret"
            assert manager._path_prefix == "myapp"

    def test_init_fails_when_not_authenticated(self, mock_hvac_client):
        """Test that initialization fails when not authenticated."""
        mock_hvac_client.is_authenticated.return_value = False

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            with pytest.raises(RuntimeError) as exc_info:
                VaultSecretsManager(
                    vault_url="http://localhost:8200",
                    vault_token="invalid-token",
                )

            assert "Failed to authenticate with Vault" in str(exc_info.value)

    def test_init_sets_token_renewal_info(self, mock_hvac_client):
        """Test that initialization retrieves token renewal info."""
        mock_hvac_client.auth.token.lookup_self.return_value = {
            "data": {
                "renewable": True,
                "ttl": 3600,
            }
        }

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            assert manager._token_renewable is True
            assert manager._token_expires_at is not None


class TestVaultSecretsManagerStore:
    """Tests for VaultSecretsManager.store method."""

    @pytest.mark.asyncio
    async def test_store_calls_vault_create_or_update(self, mock_hvac_client, sample_credentials):
        """Test that store calls the Vault KV v2 create_or_update_secret."""
        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            result = await manager.store("test/secret", sample_credentials)

            mock_hvac_client.secrets.kv.v2.create_or_update_secret.assert_called_once()
            assert result == "test/secret"

    @pytest.mark.asyncio
    async def test_store_uses_correct_path(self, mock_hvac_client, sample_credentials):
        """Test that store uses the correct full path with prefix."""
        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
                path_prefix="myapp",
            )

            await manager.store("oauth/google", sample_credentials)

            call_kwargs = mock_hvac_client.secrets.kv.v2.create_or_update_secret.call_args
            assert call_kwargs[1]["path"] == "myapp/oauth/google"


class TestVaultSecretsManagerRetrieve:
    """Tests for VaultSecretsManager.retrieve method."""

    @pytest.mark.asyncio
    async def test_retrieve_returns_secret_data(self, mock_hvac_client, sample_credentials):
        """Test that retrieve returns the secret data from Vault."""
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {
                "data": sample_credentials,
            }
        }

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            result = await manager.retrieve("test/secret")

            assert result == sample_credentials

    @pytest.mark.asyncio
    async def test_retrieve_missing_secret_raises_keyerror(self, mock_hvac_client):
        """Test that retrieving non-existent secret raises KeyError."""
        from hvac.exceptions import InvalidPath

        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = InvalidPath()

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            with pytest.raises(KeyError) as exc_info:
                await manager.retrieve("nonexistent")

            assert "Secret not found" in str(exc_info.value)


class TestVaultSecretsManagerDelete:
    """Tests for VaultSecretsManager.delete method."""

    @pytest.mark.asyncio
    async def test_delete_calls_vault_delete_metadata(self, mock_hvac_client, sample_credentials):
        """Test that delete calls the Vault delete_metadata_and_all_versions."""
        # Mock exists check to return True
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": sample_credentials}
        }

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            await manager.delete("test/secret")

            mock_hvac_client.secrets.kv.v2.delete_metadata_and_all_versions.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises_keyerror(self, mock_hvac_client):
        """Test that deleting non-existent secret raises KeyError."""
        from hvac.exceptions import InvalidPath

        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = InvalidPath()

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            with pytest.raises(KeyError) as exc_info:
                await manager.delete("nonexistent")

            assert "Secret not found" in str(exc_info.value)


class TestVaultSecretsManagerExists:
    """Tests for VaultSecretsManager.exists method."""

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_found(self, mock_hvac_client, sample_credentials):
        """Test that exists returns True when secret is found."""
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": sample_credentials}
        }

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            result = await manager.exists("test/secret")

            assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_not_found(self, mock_hvac_client):
        """Test that exists returns False when secret is not found."""
        from hvac.exceptions import InvalidPath

        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = InvalidPath()

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            result = await manager.exists("nonexistent")

            assert result is False


class TestVaultSecretsManagerListKeys:
    """Tests for VaultSecretsManager.list_keys method."""

    @pytest.mark.asyncio
    async def test_list_keys_returns_all_secrets(self, mock_hvac_client):
        """Test that list_keys returns all secrets in the vault."""
        mock_hvac_client.secrets.kv.v2.list_secrets.return_value = {
            "data": {
                "keys": ["secret1", "secret2", "secret3"]
            }
        }

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            result = await manager.list_keys()

            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_keys_empty_vault(self, mock_hvac_client):
        """Test list_keys with empty vault."""
        from hvac.exceptions import InvalidPath

        mock_hvac_client.secrets.kv.v2.list_secrets.side_effect = InvalidPath()

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            result = await manager.list_keys()

            assert result == []


class TestVaultSecretsManagerTokenRenewal:
    """Tests for VaultSecretsManager token renewal functionality."""

    @pytest.mark.asyncio
    async def test_token_renewal_when_near_expiry(self, mock_hvac_client, sample_credentials):
        """Test that token is renewed when near expiration."""
        # Set up token that expires soon
        mock_hvac_client.auth.token.lookup_self.return_value = {
            "data": {
                "renewable": True,
                "ttl": 60,  # 60 seconds - below threshold
            }
        }
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": sample_credentials}
        }

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            await manager.retrieve("test/secret")

            # Token should be renewed because ttl < threshold
            mock_hvac_client.auth.token.renew_self.assert_called()

    @pytest.mark.asyncio
    async def test_no_renewal_when_not_renewable(self, mock_hvac_client, sample_credentials):
        """Test that non-renewable tokens are not renewed."""
        mock_hvac_client.auth.token.lookup_self.return_value = {
            "data": {
                "renewable": False,
                "ttl": 60,
            }
        }
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": sample_credentials}
        }

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = VaultSecretsManager(
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            await manager.retrieve("test/secret")

            mock_hvac_client.auth.token.renew_self.assert_not_called()


# ============================================================================
# Factory Tests
# ============================================================================


class TestFactoryInitSecretsManager:
    """Tests for factory.init_secrets_manager function."""

    def test_init_local_manager(self, encryption_key, temp_storage_path):
        """Test initializing a local secrets manager."""
        # Reset the global manager first
        factory._secrets_manager = None

        manager = factory.init_secrets_manager(
            provider="local",
            encryption_key=encryption_key,
            storage_path=temp_storage_path,
        )

        assert isinstance(manager, LocalEncryptedManager)

    def test_init_local_generates_key_if_not_provided(self, temp_storage_path):
        """Test that local manager generates key if not provided."""
        factory._secrets_manager = None

        manager = factory.init_secrets_manager(
            provider="local",
            storage_path=temp_storage_path,
        )

        assert isinstance(manager, LocalEncryptedManager)

    def test_init_hashicorp_requires_url_and_token(self):
        """Test that HashiCorp provider requires vault_url and vault_token."""
        factory._secrets_manager = None

        with pytest.raises(ValueError) as exc_info:
            factory.init_secrets_manager(
                provider="hashicorp",
                vault_url=None,
                vault_token=None,
            )

        assert "VAULT_URL" in str(exc_info.value)
        assert "VAULT_TOKEN" in str(exc_info.value)

    def test_init_hashicorp_with_valid_credentials(self, mock_hvac_client):
        """Test initializing HashiCorp Vault manager with valid credentials."""
        factory._secrets_manager = None

        with patch("src.secrets.vault.hvac.Client", return_value=mock_hvac_client):
            manager = factory.init_secrets_manager(
                provider="hashicorp",
                vault_url="http://localhost:8200",
                vault_token="test-token",
            )

            assert isinstance(manager, VaultSecretsManager)

    def test_init_aws_not_implemented(self):
        """Test that AWS provider is not yet implemented."""
        factory._secrets_manager = None

        with pytest.raises(NotImplementedError) as exc_info:
            factory.init_secrets_manager(provider="aws")

        assert "AWS Secrets Manager" in str(exc_info.value)

    def test_init_azure_not_implemented(self):
        """Test that Azure provider is not yet implemented."""
        factory._secrets_manager = None

        with pytest.raises(NotImplementedError) as exc_info:
            factory.init_secrets_manager(provider="azure")

        assert "Azure Key Vault" in str(exc_info.value)

    def test_init_unknown_provider_raises_error(self):
        """Test that unknown provider raises ValueError."""
        factory._secrets_manager = None

        with pytest.raises(ValueError) as exc_info:
            factory.init_secrets_manager(provider="unknown_provider")

        assert "Unknown vault provider" in str(exc_info.value)


class TestFactoryGetSecretsManager:
    """Tests for factory.get_secrets_manager function."""

    def test_get_raises_error_when_not_initialized(self):
        """Test that get_secrets_manager raises error when not initialized."""
        factory._secrets_manager = None

        with pytest.raises(RuntimeError) as exc_info:
            factory.get_secrets_manager()

        assert "not initialized" in str(exc_info.value)

    def test_get_returns_initialized_manager(self, encryption_key, temp_storage_path):
        """Test that get_secrets_manager returns the initialized manager."""
        factory._secrets_manager = None

        initialized = factory.init_secrets_manager(
            provider="local",
            encryption_key=encryption_key,
            storage_path=temp_storage_path,
        )

        retrieved = factory.get_secrets_manager()

        assert retrieved is initialized

    def test_get_returns_same_instance(self, encryption_key, temp_storage_path):
        """Test that get_secrets_manager returns singleton instance."""
        factory._secrets_manager = None

        factory.init_secrets_manager(
            provider="local",
            encryption_key=encryption_key,
            storage_path=temp_storage_path,
        )

        instance1 = factory.get_secrets_manager()
        instance2 = factory.get_secrets_manager()

        assert instance1 is instance2


class TestFactoryCloseSecretsManager:
    """Tests for factory.close_secrets_manager function."""

    @pytest.mark.asyncio
    async def test_close_clears_manager(self, encryption_key, temp_storage_path):
        """Test that close_secrets_manager clears the global manager."""
        factory._secrets_manager = None

        factory.init_secrets_manager(
            provider="local",
            encryption_key=encryption_key,
            storage_path=temp_storage_path,
        )

        # Verify it's initialized
        assert factory._secrets_manager is not None

        await factory.close_secrets_manager()

        assert factory._secrets_manager is None

    @pytest.mark.asyncio
    async def test_close_when_not_initialized(self):
        """Test that close_secrets_manager works even when not initialized."""
        factory._secrets_manager = None

        # Should not raise
        await factory.close_secrets_manager()

        assert factory._secrets_manager is None


# ============================================================================
# Base SecretsManager Abstract Class Tests
# ============================================================================


class TestSecretsManagerAbstractClass:
    """Tests for the SecretsManager abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test that SecretsManager cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SecretsManager()

    def test_subclass_must_implement_all_methods(self):
        """Test that subclasses must implement all abstract methods."""
        class IncompleteManager(SecretsManager):
            pass

        with pytest.raises(TypeError):
            IncompleteManager()

    def test_valid_subclass_can_be_instantiated(self, encryption_key, temp_storage_path):
        """Test that a properly implemented subclass can be instantiated."""
        manager = LocalEncryptedManager(
            encryption_key=encryption_key,
            storage_path=temp_storage_path,
        )

        assert isinstance(manager, SecretsManager)


# ============================================================================
# Integration Tests (LocalEncryptedManager end-to-end)
# ============================================================================


class TestLocalEncryptedManagerIntegration:
    """End-to-end integration tests for LocalEncryptedManager."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, local_manager, sample_credentials):
        """Test complete lifecycle: store -> retrieve -> delete."""
        key = "integration/test/secret"

        # Store
        ref = await local_manager.store(key, sample_credentials)
        assert ref == key

        # Exists check
        assert await local_manager.exists(key) is True

        # Retrieve
        retrieved = await local_manager.retrieve(key)
        assert retrieved == sample_credentials

        # List keys
        keys = await local_manager.list_keys()
        assert key in keys

        # Delete
        await local_manager.delete(key)

        # Verify deleted
        assert await local_manager.exists(key) is False

        keys_after = await local_manager.list_keys()
        assert key not in keys_after

    @pytest.mark.asyncio
    async def test_multiple_secrets(self, local_manager):
        """Test managing multiple secrets."""
        secrets = {
            "oauth/google/calendar": {"client_id": "google-123", "client_secret": "secret-google"},
            "oauth/github/api": {"token": "ghp_xxx123"},
            "mcp/servers/srv_abc": {"api_key": "sk-test"},
        }

        # Store all
        for key, value in secrets.items():
            await local_manager.store(key, value)

        # Verify all exist
        for key in secrets:
            assert await local_manager.exists(key) is True

        # Retrieve all and verify
        for key, expected_value in secrets.items():
            retrieved = await local_manager.retrieve(key)
            assert retrieved == expected_value

        # List keys
        keys = await local_manager.list_keys()
        assert len(keys) == 3

    @pytest.mark.asyncio
    async def test_encryption_uses_provided_key(self, encryption_key, temp_storage_path, sample_credentials):
        """Test that encryption uses the provided key (can decrypt with same key)."""
        manager1 = LocalEncryptedManager(
            encryption_key=encryption_key,
            storage_path=temp_storage_path,
        )

        await manager1.store("test_secret", sample_credentials)

        # Create new manager with same key - should be able to read
        manager2 = LocalEncryptedManager(
            encryption_key=encryption_key,
            storage_path=temp_storage_path,
        )

        retrieved = await manager2.retrieve("test_secret")
        assert retrieved == sample_credentials

    @pytest.mark.asyncio
    async def test_different_key_cannot_decrypt(self, encryption_key, temp_storage_path, sample_credentials):
        """Test that different encryption key cannot decrypt secrets."""
        manager1 = LocalEncryptedManager(
            encryption_key=encryption_key,
            storage_path=temp_storage_path,
        )

        await manager1.store("test_secret", sample_credentials)

        # Create new manager with different key
        different_key = Fernet.generate_key().decode()
        manager2 = LocalEncryptedManager(
            encryption_key=different_key,
            storage_path=temp_storage_path,
        )

        # Should raise an exception when trying to decrypt with wrong key
        with pytest.raises(Exception):  # Fernet raises InvalidToken
            await manager2.retrieve("test_secret")
