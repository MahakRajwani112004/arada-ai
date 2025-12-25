"""LLM Completion Activity for Temporal workflows."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from temporalio import activity

from src.llm import LLMClient, LLMMessage, ToolCall, ToolDefinition
from src.models.llm_config import LLMConfig


@dataclass
class ToolDefinitionInput:
    """Tool definition for LLM function calling."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema


@dataclass
class ToolCallOutput:
    """A tool call from the LLM."""

    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMCompletionInput:
    """Input for LLM completion activity."""

    provider: str
    model: str
    messages: List[Dict[str, Any]]  # List of message dicts
    user_id: str  # Required for user-level analytics
    temperature: float = 0.7
    max_tokens: int = 1024
    stop_sequences: Optional[List[str]] = None
    tools: Optional[List[ToolDefinitionInput]] = None  # Tools for function calling
    agent_id: Optional[str] = None  # Optional correlation
    request_id: Optional[str] = None  # Optional correlation
    workflow_id: Optional[str] = None  # Optional correlation


@dataclass
class LLMCompletionOutput:
    """Output from LLM completion activity."""

    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    tool_calls: List[ToolCallOutput] = field(default_factory=list)


@activity.defn
async def llm_completion(input: LLMCompletionInput) -> LLMCompletionOutput:
    """
    Execute LLM completion as a Temporal activity.

    This activity supports native function/tool calling when tools are provided.
    """
    activity.logger.info(
        f"LLM completion: provider={input.provider}, model={input.model}, "
        f"tools={len(input.tools) if input.tools else 0}"
    )

    # Build config
    config = LLMConfig(
        provider=input.provider,
        model=input.model,
        temperature=input.temperature,
        max_tokens=input.max_tokens,
    )

    # Get provider and execute
    provider = LLMClient.get_provider(config)

    # Build messages with proper handling for tool calls
    messages = []
    for m in input.messages:
        msg = LLMMessage(
            role=m["role"],
            content=m.get("content", ""),
            tool_call_id=m.get("tool_call_id"),
        )
        # Handle tool_calls in assistant messages
        if m.get("tool_calls"):
            msg.tool_calls = [
                ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    arguments=tc["arguments"],
                )
                for tc in m["tool_calls"]
            ]
        messages.append(msg)

    # Build tool definitions if provided
    tools = None
    if input.tools:
        tools = [
            ToolDefinition(
                name=t.name,
                description=t.description,
                parameters=t.parameters,
            )
            for t in input.tools
        ]

    response = await provider.complete(
        messages=messages,
        stop_sequences=input.stop_sequences,
        tools=tools,
        user_id=input.user_id,
        agent_id=input.agent_id,
        request_id=input.request_id,
        workflow_id=input.workflow_id,
    )

    activity.logger.info(
        f"LLM completion finished: tokens={response.usage.get('total_tokens', 0)}, "
        f"tool_calls={len(response.tool_calls)}"
    )

    # Convert tool calls to output format
    tool_calls_output = [
        ToolCallOutput(
            id=tc.id,
            name=tc.name,
            arguments=tc.arguments,
        )
        for tc in response.tool_calls
    ]

    return LLMCompletionOutput(
        content=response.content,
        model=response.model,
        usage=response.usage,
        finish_reason=response.finish_reason,
        tool_calls=tool_calls_output,
    )
