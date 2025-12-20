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

    async def execute(self, context: AgentContext) -> AgentResponse:
        """Execute agent with tool loop."""
        messages = self._build_messages(context)
        tool_definitions = self._registry.get_openai_tools(self._enabled_tools)

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

            # Execute tools and add results to messages
            for tool_call in tool_calls:
                tool_result = await self._execute_tool(tool_call)
                tool_calls_made.append({
                    "tool": tool_call["name"],
                    "args": tool_call["arguments"],
                    "result": tool_result,
                })

                # Add tool call and result to messages
                messages.append(LLMMessage(
                    role="assistant",
                    content=f"[Tool Call: {tool_call['name']}({json.dumps(tool_call['arguments'])})]",
                ))
                messages.append(LLMMessage(
                    role="user",
                    content=f"[Tool Result: {json.dumps(tool_result)}]",
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
        # For now, use standard completion
        # In production, use provider-specific tool calling
        return await self._provider.complete(messages)

    def _extract_tool_calls(
        self, response
    ) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        # Parse tool calls from response content
        # Format: [TOOL: name({"arg": "value"})]
        import re

        tool_calls = []
        pattern = r'\[TOOL:\s*(\w+)\((\{.*?\})\)\]'

        for match in re.finditer(pattern, response.content, re.DOTALL):
            try:
                name = match.group(1)
                args = json.loads(match.group(2))
                tool_calls.append({
                    "name": name,
                    "arguments": args,
                })
            except json.JSONDecodeError:
                continue

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
