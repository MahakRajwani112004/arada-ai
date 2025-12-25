"""ToolAgent - LLM with function calling capabilities."""
import json
from typing import Any, Dict, List, Optional

from src.agents.base import BaseAgent
from src.llm import LLMClient, LLMMessage
from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse
from src.tools.registry import get_registry


class ToolAgent(BaseAgent):
    """
    Agent that can use tools via LLM function calling.

    Use cases:
    - Task automation
    - Data processing
    - API integrations
    - Multi-step workflows
    """

    MAX_TOOL_ITERATIONS = 10

    def __init__(self, config: AgentConfig):
        """Initialize ToolAgent."""
        super().__init__(config)
        if not config.llm_config:
            raise ValueError("ToolAgent requires llm_config")

        self._provider = LLMClient.get_provider(config.llm_config)
        self._registry = get_registry()
        self._enabled_tools = self.get_enabled_tools()

    def _build_messages(self, context: AgentContext) -> List[LLMMessage]:
        """Build LLM messages from context."""
        messages = []
        system_prompt = self.build_system_prompt()
        messages.append(LLMMessage(role="system", content=system_prompt))

        for msg in context.conversation_history:
            messages.append(LLMMessage(role=msg.role, content=msg.content))

        messages.append(LLMMessage(role="user", content=context.user_input))
        return messages

    async def _execute_impl(self, context: AgentContext) -> AgentResponse:
        """Execute agent with tool loop."""
        import structlog
        logger = structlog.get_logger(__name__)

        messages = self._build_messages(context)

        # Debug logging for tools
        logger.info(
            "tool_agent_execute",
            enabled_tools=self._enabled_tools,
            registry_tools=self._registry.available_tools,
        )

        tool_definitions = self._registry.get_openai_tools(self._enabled_tools)
        logger.info(
            "tool_definitions_retrieved",
            count=len(tool_definitions),
            tools=[t.get("function", {}).get("name") for t in tool_definitions] if tool_definitions else [],
        )

        tool_calls_made = []
        iterations = 0

        while iterations < self.MAX_TOOL_ITERATIONS:
            iterations += 1

            # Call LLM with tools
            response = await self._call_with_tools(messages, tool_definitions)

            # Check if LLM wants to call tools
            tool_calls = self._extract_tool_calls(response)

            if not tool_calls:
                # No more tool calls, return final response
                return AgentResponse(
                    content=response.content,
                    confidence=0.9,
                    metadata={
                        "model": response.model,
                        "usage": response.usage,
                        "tool_calls": tool_calls_made,
                        "iterations": iterations,
                    },
                )

            # Build ToolCall objects for the assistant message
            from src.llm.providers.base import ToolCall
            tc_objects = [
                ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    arguments=tc["arguments"],
                )
                for tc in tool_calls
            ]

            # Add assistant message with tool calls
            messages.append(LLMMessage(
                role="assistant",
                content="",
                tool_calls=tc_objects,
            ))

            # Execute tools and add results to messages
            for tool_call in tool_calls:
                tool_result = await self._execute_tool(tool_call)
                tool_calls_made.append({
                    "tool": tool_call["name"],
                    "args": tool_call["arguments"],
                    "result": tool_result,
                })

                # Add tool result message
                messages.append(LLMMessage(
                    role="tool",
                    content=json.dumps(tool_result),
                    tool_call_id=tool_call["id"],
                ))

        # Max iterations reached
        return AgentResponse(
            content="I've reached the maximum number of tool operations.",
            confidence=0.5,
            metadata={
                "tool_calls": tool_calls_made,
                "iterations": iterations,
                "max_iterations_reached": True,
            },
        )

    async def _call_with_tools(
        self,
        messages: List[LLMMessage],
        tools: List[Dict[str, Any]],
    ):
        """Call LLM with tool definitions."""
        return await self._provider.complete(messages, tools=tools if tools else None)

    def _extract_tool_calls(
        self, response
    ) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        tool_calls = []

        # Use actual tool_calls from LLM response
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments,
                })

        return tool_calls

    async def _execute_tool(
        self, tool_call: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single tool call."""
        result = await self._registry.execute(
            tool_call["name"],
            **tool_call["arguments"],
        )

        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
        }
