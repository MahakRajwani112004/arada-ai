"""LLM Client - Factory for LLM providers."""
from typing import Dict, Type

from src.models.llm_config import LLMConfig

from .providers.anthropic import AnthropicProvider
from .providers.base import BaseLLMProvider, LLMMessage, LLMResponse
from .providers.openai import OpenAIProvider


class LLMClient:
    """
    Factory for creating LLM provider instances.

    Usage:
        config = LLMConfig(provider="anthropic", model="claude-3-sonnet-20240229")
        provider = LLMClient.get_provider(config)
        response = await provider.complete(messages)
    """

    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
    }

    @classmethod
    def get_provider(cls, config: LLMConfig) -> BaseLLMProvider:
        """
        Get an LLM provider instance based on config.

        Args:
            config: LLM configuration with provider name

        Returns:
            Provider instance ready to use

        Raises:
            ValueError: If provider is not supported
        """
        provider_name = config.provider.lower()

        if provider_name not in cls._providers:
            supported = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unsupported LLM provider: {provider_name}. "
                f"Supported providers: {supported}"
            )

        provider_class = cls._providers[provider_name]
        return provider_class(config)

    @classmethod
    def register_provider(
        cls, name: str, provider_class: Type[BaseLLMProvider]
    ) -> None:
        """
        Register a custom LLM provider.

        Args:
            name: Provider name (e.g., "custom")
            provider_class: Provider class implementing BaseLLMProvider
        """
        cls._providers[name.lower()] = provider_class

    @classmethod
    def supported_providers(cls) -> list[str]:
        """Get list of supported provider names."""
        return list(cls._providers.keys())


__all__ = [
    "LLMClient",
    "LLMMessage",
    "LLMResponse",
    "BaseLLMProvider",
]
