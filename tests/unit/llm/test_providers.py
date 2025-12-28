"""Tests for LLM provider interfaces and data classes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.llm.providers.base import (
    LLMMessage,
    ToolCall,
    ToolDefinition,
    LLMResponse,
    BaseLLMProvider,
)
from src.models.llm_config import LLMConfig


class TestLLMMessage:
    """Tests for LLMMessage dataclass."""

    def test_create_user_message(self):
        """Test creating a user message."""
        msg = LLMMessage(role="user", content="Hello, world!")

        assert msg.role == "user"
        assert msg.content == "Hello, world!"
        assert msg.tool_call_id is None
        assert msg.tool_calls is None

    def test_create_system_message(self):
        """Test creating a system message."""
        msg = LLMMessage(role="system", content="You are a helpful assistant.")

        assert msg.role == "system"
        assert msg.content == "You are a helpful assistant."

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = LLMMessage(role="assistant", content="How can I help you?")

        assert msg.role == "assistant"

    def test_create_tool_result_message(self):
        """Test creating a tool result message."""
        msg = LLMMessage(
            role="tool",
            content='{"result": "success"}',
            tool_call_id="call_123",
        )

        assert msg.role == "tool"
        assert msg.tool_call_id == "call_123"

    def test_message_with_tool_calls(self):
        """Test assistant message with tool calls."""
        tool_calls = [
            ToolCall(id="call_1", name="search", arguments={"query": "test"}),
        ]
        msg = LLMMessage(
            role="assistant",
            content="",
            tool_calls=tool_calls,
        )

        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "search"


class TestToolCall:
    """Tests for ToolCall dataclass."""

    def test_create_tool_call(self):
        """Test creating a tool call."""
        call = ToolCall(
            id="call_abc123",
            name="get_weather",
            arguments={"city": "New York"},
        )

        assert call.id == "call_abc123"
        assert call.name == "get_weather"
        assert call.arguments == {"city": "New York"}

    def test_tool_call_with_multiple_args(self):
        """Test tool call with multiple arguments."""
        call = ToolCall(
            id="call_123",
            name="search",
            arguments={
                "query": "python",
                "limit": 10,
                "sort": "relevance",
            },
        )

        assert len(call.arguments) == 3


class TestToolDefinition:
    """Tests for ToolDefinition dataclass."""

    def test_create_tool_definition(self):
        """Test creating a tool definition."""
        tool = ToolDefinition(
            name="calculator",
            description="Perform calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string"},
                },
            },
        )

        assert tool.name == "calculator"
        assert tool.description == "Perform calculations"
        assert "expression" in tool.parameters["properties"]


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_create_basic_response(self):
        """Test creating a basic LLM response."""
        response = LLMResponse(
            content="Hello! How can I help you?",
            model="gpt-4o-mini",
            usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
            finish_reason="stop",
        )

        assert response.content == "Hello! How can I help you?"
        assert response.model == "gpt-4o-mini"
        assert response.usage["total_tokens"] == 25
        assert response.finish_reason == "stop"
        assert response.tool_calls == []  # default

    def test_response_with_tool_calls(self):
        """Test response with tool calls."""
        tool_calls = [
            ToolCall(id="call_1", name="search", arguments={"q": "test"}),
        ]
        response = LLMResponse(
            content="",
            model="gpt-4o",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="tool_calls",
            tool_calls=tool_calls,
        )

        assert response.finish_reason == "tool_calls"
        assert len(response.tool_calls) == 1

    def test_response_with_raw_response(self):
        """Test response with raw response data."""
        response = LLMResponse(
            content="Test",
            model="claude-3-sonnet",
            usage={"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
            finish_reason="end_turn",
            raw_response={"id": "msg_123", "type": "message"},
        )

        assert response.raw_response is not None
        assert response.raw_response["id"] == "msg_123"


class TestBaseLLMProvider:
    """Tests for BaseLLMProvider abstract class."""

    def test_cannot_instantiate_directly(self):
        """Test that BaseLLMProvider cannot be instantiated."""
        config = LLMConfig(provider="test", model="test-model")

        with pytest.raises(TypeError):
            BaseLLMProvider(config)

    def test_subclass_stores_config(self):
        """Test that subclass stores config."""

        class MockProvider(BaseLLMProvider):
            _provider_name = "mock"

            async def _complete_impl(self, messages, **kwargs):
                return LLMResponse(
                    content="test",
                    model=self.model,
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    finish_reason="stop",
                )

            async def stream(self, messages, **kwargs):
                yield "test"

        config = LLMConfig(provider="mock", model="mock-model", temperature=0.5)
        provider = MockProvider(config)

        assert provider.config == config
        assert provider.model == "mock-model"

    def test_get_temperature_with_override(self):
        """Test _get_temperature method."""

        class MockProvider(BaseLLMProvider):
            _provider_name = "mock"

            async def _complete_impl(self, messages, **kwargs):
                pass

            async def stream(self, messages, **kwargs):
                yield ""

        config = LLMConfig(provider="mock", model="model", temperature=0.7)
        provider = MockProvider(config)

        # Without override
        assert provider._get_temperature(None) == 0.7

        # With override
        assert provider._get_temperature(0.3) == 0.3

    def test_get_max_tokens_with_override(self):
        """Test _get_max_tokens method."""

        class MockProvider(BaseLLMProvider):
            _provider_name = "mock"

            async def _complete_impl(self, messages, **kwargs):
                pass

            async def stream(self, messages, **kwargs):
                yield ""

        config = LLMConfig(provider="mock", model="model", max_tokens=1000)
        provider = MockProvider(config)

        # Without override
        assert provider._get_max_tokens(None) == 1000

        # With override
        assert provider._get_max_tokens(500) == 500

    @pytest.mark.asyncio
    async def test_complete_calls_impl(self):
        """Test that complete() calls _complete_impl()."""
        from typing import List, Optional

        class MockProvider(BaseLLMProvider):
            _provider_name = "mock"

            async def _complete_impl(
                self,
                messages: List[LLMMessage],
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                stop_sequences: Optional[List[str]] = None,
                tools: Optional[List[ToolDefinition]] = None,
            ):
                return LLMResponse(
                    content="Mocked response",
                    model=self.model,
                    usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                    finish_reason="stop",
                )

            async def stream(self, messages, **kwargs):
                yield ""

        config = LLMConfig(provider="mock", model="mock-model")
        provider = MockProvider(config)

        # Mock settings to disable monitoring and analytics
        with patch("src.llm.providers.base.settings") as mock_settings:
            mock_settings.monitoring_enabled = False
            mock_settings.analytics_enabled = False

            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.complete(messages, user_id="user-123")

            assert response.content == "Mocked response"
            assert response.model == "mock-model"

    @pytest.mark.asyncio
    async def test_complete_handles_errors(self):
        """Test that complete() propagates errors from _complete_impl()."""
        from typing import List, Optional

        class ErrorProvider(BaseLLMProvider):
            _provider_name = "error"

            async def _complete_impl(
                self,
                messages: List[LLMMessage],
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                stop_sequences: Optional[List[str]] = None,
                tools: Optional[List[ToolDefinition]] = None,
            ):
                raise ValueError("API Error")

            async def stream(self, messages, **kwargs):
                yield ""

        config = LLMConfig(provider="error", model="error-model")
        provider = ErrorProvider(config)

        with patch("src.llm.providers.base.settings") as mock_settings:
            mock_settings.monitoring_enabled = False
            mock_settings.analytics_enabled = False

            messages = [LLMMessage(role="user", content="Hello")]

            with pytest.raises(ValueError) as exc_info:
                await provider.complete(messages, user_id="user-123")

            assert "API Error" in str(exc_info.value)
