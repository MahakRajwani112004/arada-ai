"""Base LLM provider interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

from src.models.llm_config import LLMConfig


@dataclass
class LLMMessage:
    """Message for LLM conversation."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: Optional[str] = None  # For tool result messages
    tool_calls: Optional[List["ToolCall"]] = None  # For assistant messages with tool calls


@dataclass
class ToolCall:
    """A tool call from the LLM."""

    id: str  # Unique ID for the tool call
    name: str  # Tool name
    arguments: Dict[str, Any]  # Parsed arguments


@dataclass
class ToolDefinition:
    """Tool definition for LLM function calling."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    content: str
    model: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: str
    tool_calls: List[ToolCall] = field(default_factory=list)  # Tool calls if any
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        """Initialize provider with config."""
        self.config = config
        self.model = config.model

    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        tools: Optional[List[ToolDefinition]] = None,
    ) -> LLMResponse:
        """
        Generate a completion for the given messages.

        Args:
            messages: List of conversation messages
            temperature: Override config temperature
            max_tokens: Override config max_tokens
            stop_sequences: Sequences that stop generation
            tools: Optional list of tools the LLM can call

        Returns:
            LLMResponse with content and metadata (and tool_calls if any)
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Stream a completion for the given messages.

        Args:
            messages: List of conversation messages
            temperature: Override config temperature
            max_tokens: Override config max_tokens

        Yields:
            Content chunks as they're generated
        """
        pass

    def _get_temperature(self, override: Optional[float]) -> float:
        """Get temperature, using override if provided."""
        if override is not None:
            return override
        return self.config.temperature

    def _get_max_tokens(self, override: Optional[int]) -> int:
        """Get max_tokens, using override if provided."""
        if override is not None:
            return override
        return self.config.max_tokens
