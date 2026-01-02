"""Tests for LLM Client factory."""

import pytest
from unittest.mock import MagicMock, patch

from src.llm.client import LLMClient
from src.llm.providers.base import BaseLLMProvider
from src.models.llm_config import LLMConfig


class TestLLMClient:
    """Tests for LLMClient factory."""

    def test_get_provider_openai(self):
        """Test getting OpenAI provider."""
        config = LLMConfig(provider="openai", model="gpt-4o-mini")
        provider = LLMClient.get_provider(config)

        assert provider is not None
        assert provider.model == "gpt-4o-mini"

    def test_get_provider_anthropic(self):
        """Test getting Anthropic provider."""
        config = LLMConfig(provider="anthropic", model="claude-3-sonnet-20240229")
        provider = LLMClient.get_provider(config)

        assert provider is not None
        assert provider.model == "claude-3-sonnet-20240229"

    def test_get_provider_case_insensitive(self):
        """Test provider name is case insensitive."""
        config1 = LLMConfig(provider="OpenAI", model="gpt-4o-mini")
        config2 = LLMConfig(provider="OPENAI", model="gpt-4o-mini")
        config3 = LLMConfig(provider="openai", model="gpt-4o-mini")

        provider1 = LLMClient.get_provider(config1)
        provider2 = LLMClient.get_provider(config2)
        provider3 = LLMClient.get_provider(config3)

        assert type(provider1) == type(provider2) == type(provider3)

    def test_get_provider_unsupported(self):
        """Test getting unsupported provider raises error."""
        config = LLMConfig(provider="unsupported", model="some-model")

        with pytest.raises(ValueError) as exc_info:
            LLMClient.get_provider(config)

        assert "Unsupported LLM provider" in str(exc_info.value)
        assert "unsupported" in str(exc_info.value)

    def test_get_provider_error_shows_supported(self):
        """Test error message shows supported providers."""
        config = LLMConfig(provider="invalid", model="model")

        with pytest.raises(ValueError) as exc_info:
            LLMClient.get_provider(config)

        error_msg = str(exc_info.value)
        assert "openai" in error_msg or "anthropic" in error_msg

    def test_supported_providers(self):
        """Test getting list of supported providers."""
        providers = LLMClient.supported_providers()

        assert isinstance(providers, list)
        assert "openai" in providers
        assert "anthropic" in providers

    def test_register_provider(self):
        """Test registering a custom provider."""

        class CustomProvider(BaseLLMProvider):
            _provider_name = "custom"

            async def _complete_impl(self, messages, **kwargs):
                pass

            async def stream(self, messages, **kwargs):
                yield ""

        # Register custom provider
        LLMClient.register_provider("custom", CustomProvider)

        # Verify it's registered
        assert "custom" in LLMClient.supported_providers()

        # Clean up
        del LLMClient._providers["custom"]

    def test_register_provider_case_insensitive(self):
        """Test that registered provider names are lowercase."""

        class CustomProvider(BaseLLMProvider):
            _provider_name = "custom"

            async def _complete_impl(self, messages, **kwargs):
                pass

            async def stream(self, messages, **kwargs):
                yield ""

        LLMClient.register_provider("CUSTOM", CustomProvider)
        assert "custom" in LLMClient.supported_providers()

        # Clean up
        del LLMClient._providers["custom"]

    def test_provider_uses_config_model(self):
        """Test that provider uses model from config."""
        config = LLMConfig(provider="openai", model="gpt-4-turbo")
        provider = LLMClient.get_provider(config)

        assert provider.model == "gpt-4-turbo"
        assert provider.config.model == "gpt-4-turbo"


class TestLLMProviderBase:
    """Tests for BaseLLMProvider functionality."""

    def test_get_temperature_with_override(self):
        """Test _get_temperature with override."""
        config = LLMConfig(provider="openai", model="gpt-4o-mini", temperature=0.7)
        provider = LLMClient.get_provider(config)

        # Without override, use config
        assert provider._get_temperature(None) == 0.7

        # With override, use override
        assert provider._get_temperature(0.3) == 0.3

    def test_get_max_tokens_with_override(self):
        """Test _get_max_tokens with override."""
        config = LLMConfig(provider="openai", model="gpt-4o-mini", max_tokens=1000)
        provider = LLMClient.get_provider(config)

        # Without override, use config
        assert provider._get_max_tokens(None) == 1000

        # With override, use override
        assert provider._get_max_tokens(500) == 500
