"""Anthropic (Claude) LLM provider."""
import json
from typing import Any, AsyncIterator, Dict, List, Optional

from anthropic import AsyncAnthropic

from src.config import get_settings
from src.models.llm_config import LLMConfig

from .base import BaseLLMProvider, LLMMessage, LLMResponse, ToolCall, ToolDefinition


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation."""

    _provider_name = "anthropic"

    def __init__(self, config: LLMConfig):
        """Initialize Anthropic provider."""
        super().__init__(config)
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in .env or environment")
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    def _format_messages(
        self, messages: List[LLMMessage]
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Format messages for Anthropic API.

        Anthropic uses a separate system parameter, not in messages array.

        Returns:
            Tuple of (system_prompt, messages_list)
        """
        system_prompt = ""
        formatted_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role == "tool":
                # Tool result message
                formatted_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content,
                        }
                    ],
                })
            elif msg.tool_calls:
                # Assistant message with tool calls
                content_blocks = []
                if msg.content:
                    content_blocks.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                formatted_messages.append({
                    "role": "assistant",
                    "content": content_blocks,
                })
            else:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        return system_prompt, formatted_messages

    def _format_tools(
        self, tools: List[ToolDefinition]
    ) -> List[Dict[str, Any]]:
        """Format tools for Anthropic API."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in tools
        ]

    async def _complete_impl(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        """Generate completion using Claude with optional tool calling.

        Args:
            tool_choice: "auto" (default), "required" (force tool call),
                        "none" (no tool calls), or a specific tool name.
        """
        system_prompt, formatted_messages = self._format_messages(messages)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self._get_max_tokens(max_tokens),
            "temperature": self._get_temperature(temperature),
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if stop_sequences:
            kwargs["stop_sequences"] = stop_sequences

        if tools:
            kwargs["tools"] = self._format_tools(tools)
            # Handle tool_choice parameter - Anthropic uses different format
            if tool_choice == "required":
                kwargs["tool_choice"] = {"type": "any"}
            elif tool_choice == "none":
                # Anthropic doesn't have explicit "none", so we just don't pass tools
                del kwargs["tools"]
            elif tool_choice and tool_choice not in ("auto", "required", "none"):
                # Specific tool name - force that tool to be called
                kwargs["tool_choice"] = {"type": "tool", "name": tool_choice}
            # For "auto" or None, Anthropic uses auto by default (no tool_choice needed)

        response = await self.client.messages.create(**kwargs)

        # Extract content and tool calls from response
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": (
                    response.usage.input_tokens + response.usage.output_tokens
                ),
            },
            finish_reason=response.stop_reason or "end_turn",
            tool_calls=tool_calls,
            raw_response=response.model_dump(),
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream completion using Claude."""
        system_prompt, formatted_messages = self._format_messages(messages)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self._get_max_tokens(max_tokens),
            "temperature": self._get_temperature(temperature),
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
