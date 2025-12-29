"""Tests for LLM configuration model."""

import pytest
from pydantic import ValidationError

from src.models.llm_config import LLMConfig


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_create_basic_config(self):
        """Test creating a basic LLM config."""
        config = LLMConfig(provider="openai", model="gpt-4o-mini")

        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"

    def test_default_values(self):
        """Test default values are set."""
        config = LLMConfig()

        assert config.provider == "openai"  # default
        assert config.model == "gpt-4-turbo"  # default
        assert config.temperature == 0.0  # default (deterministic)
        assert config.max_tokens == 4096  # default

    def test_custom_temperature(self):
        """Test setting custom temperature."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.3,
        )

        assert config.temperature == 0.3

    def test_custom_max_tokens(self):
        """Test setting custom max_tokens."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            max_tokens=2048,
        )

        assert config.max_tokens == 2048

    def test_temperature_range_min(self):
        """Test temperature minimum value."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.0,
        )
        assert config.temperature == 0.0

    def test_temperature_range_max(self):
        """Test temperature maximum value."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=2.0,
        )
        assert config.temperature == 2.0

    def test_provider_case_preservation(self):
        """Test that provider case is preserved."""
        config = LLMConfig(provider="OpenAI", model="gpt-4o-mini")
        assert config.provider == "OpenAI"

    def test_model_name_preserved(self):
        """Test that model name is preserved exactly."""
        config = LLMConfig(provider="anthropic", model="claude-3-opus-20240229")
        assert config.model == "claude-3-opus-20240229"

    def test_with_api_base(self):
        """Test config with custom API base."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            api_base="https://custom-api.example.com",
        )
        assert config.api_base == "https://custom-api.example.com"

    def test_optional_api_base(self):
        """Test that API base is optional."""
        config = LLMConfig(provider="openai", model="gpt-4o-mini")
        assert config.api_base is None

    def test_top_p_default(self):
        """Test top_p default value."""
        config = LLMConfig()
        assert config.top_p == 1.0

    def test_frequency_penalty_default(self):
        """Test frequency_penalty default value."""
        config = LLMConfig()
        assert config.frequency_penalty == 0.0

    def test_presence_penalty_default(self):
        """Test presence_penalty default value."""
        config = LLMConfig()
        assert config.presence_penalty == 0.0

    def test_stop_sequences_default(self):
        """Test stop_sequences default value."""
        config = LLMConfig()
        assert config.stop_sequences == []

    def test_extra_params(self):
        """Test extra_params functionality."""
        config = LLMConfig(
            extra_params={"custom_param": "value"},
        )
        assert config.extra_params["custom_param"] == "value"


class TestLLMConfigValidation:
    """Tests for LLMConfig validation."""

    def test_temperature_below_zero(self):
        """Test temperature below 0 raises error."""
        with pytest.raises(ValidationError):
            LLMConfig(
                provider="openai",
                model="gpt-4o-mini",
                temperature=-0.1,
            )

    def test_temperature_above_max(self):
        """Test temperature above max raises error."""
        with pytest.raises(ValidationError):
            LLMConfig(
                provider="openai",
                model="gpt-4o-mini",
                temperature=2.5,
            )

    def test_max_tokens_below_one(self):
        """Test max_tokens below 1 raises error."""
        with pytest.raises(ValidationError):
            LLMConfig(
                provider="openai",
                model="gpt-4o-mini",
                max_tokens=0,
            )

    def test_top_p_below_zero(self):
        """Test top_p below 0 raises error."""
        with pytest.raises(ValidationError):
            LLMConfig(top_p=-0.1)

    def test_top_p_above_one(self):
        """Test top_p above 1 raises error."""
        with pytest.raises(ValidationError):
            LLMConfig(top_p=1.5)
