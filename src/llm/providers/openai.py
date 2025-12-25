"""OpenAI LLM provider."""
import json
from typing import Any, AsyncIterator, Dict, List, Optional

from openai import AsyncOpenAI

from src.config import get_settings
from src.models.llm_config import LLMConfig

from .base import BaseLLMProvider, LLMMessage, LLMResponse, ToolCall, ToolDefinition


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider implementation."""

    _provider_name = "openai"

    def __init__(self, config: LLMConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set in .env or environment")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    def _format_messages(
        self, messages: List[LLMMessage]
    ) -> List[Dict[str, Any]]:
        """Format messages for OpenAI API."""
        formatted = []
        for msg in messages:
            if msg.role == "tool":
                # Tool result message
                formatted.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id,
                })
            elif msg.tool_calls:
                # Assistant message with tool calls
                formatted.append({
                    "role": "assistant",
                    "content": msg.content or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                })
            else:
                formatted.append({"role": msg.role, "content": msg.content})
        return formatted

    def _format_tools(
        self, tools: List[ToolDefinition]
    ) -> List[Dict[str, Any]]:
        """Format tools for OpenAI API function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
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
    ) -> LLMResponse:
        """Generate completion using GPT with optional tool calling."""
        formatted_messages = self._format_messages(messages)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self._get_max_tokens(max_tokens),
            "temperature": self._get_temperature(temperature),
        }

        if stop_sequences:
            kwargs["stop"] = stop_sequences

        if tools:
            kwargs["tools"] = self._format_tools(tools)
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        content = choice.message.content or ""

        # Parse tool calls if present
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=arguments,
                    )
                )

        usage = response.usage
        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
            finish_reason=choice.finish_reason or "stop",
            tool_calls=tool_calls,
            raw_response=response.model_dump(),
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream completion using GPT."""
        formatted_messages = self._format_messages(messages)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self._get_max_tokens(max_tokens),
            "temperature": self._get_temperature(temperature),
            "stream": True,
        }

        stream = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
