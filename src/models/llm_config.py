"""LLM provider configuration."""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = Field(
        default="openai",
        description="LLM provider: openai, anthropic, azure, ollama",
    )
    model: str = Field(
        default="gpt-4-turbo",
        description="Model identifier",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens in response",
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter",
    )
    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty",
    )
    presence_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty",
    )
    stop_sequences: list[str] = Field(
        default_factory=list,
        description="Stop sequences",
    )
    api_base: Optional[str] = Field(
        default=None,
        description="Custom API base URL",
    )
    extra_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific parameters",
    )

    model_config = {"extra": "allow"}
