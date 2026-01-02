"""ToolAgent - LLM with function calling capabilities."""
import asyncio
import json
from typing import Any, Dict, List, Optional

from src.agents.base import BaseAgent
from src.agents.confidence import ConfidenceCalculator
from src.llm import LLMClient, LLMMessage
from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse
from src.skills.models import Skill
from src.tools.registry import get_registry


class ToolAgent(BaseAgent):
    """
    Agent that can use tools via LLM function calling.

    Components Used:
    - Skills: YES (injected into system prompt via build_system_prompt)
    - Tools: YES (native LLM function calling)
    - Knowledge Base: NO

    Use cases:
    - Task automation
    - Data processing
    - API integrations
    - Multi-step workflows
    """

    MAX_TOOL_ITERATIONS = 10
    TOOL_TIMEOUT_SECONDS = 30  # Timeout for individual tool execution

    def __init__(
        self,
        config: AgentConfig,
        skills: Optional[List[Skill]] = None,
    ):
        """
        Initialize ToolAgent.

        Args:
            config: Agent configuration
            skills: List of Skill objects for domain expertise
        """
        super().__init__(config, skills=skills)
        if not config.llm_config:
            raise ValueError("ToolAgent requires llm_config")

        self._provider = LLMClient.get_provider(config.llm_config)
        self._registry = get_registry()
        self._enabled_tools = self.get_enabled_tools()

        # Validate enabled tools exist in registry
        self._validate_tools()

    def _validate_tools(self) -> None:
        """Validate that enabled tools exist in the registry."""
        import structlog
        logger = structlog.get_logger(__name__)

        if not self._enabled_tools:
            return

        available = set(self._registry.available_tools)
        missing = [t for t in self._enabled_tools if t not in available]

        if missing:
            logger.warning(
                "tools_not_found_in_registry",
                agent_id=self.id,
                missing_tools=missing,
                available_tools=list(available),
            )

    def _build_messages(
        self,
        context: AgentContext,
        selected_skills: List = None,
    ) -> List[LLMMessage]:
        """Build LLM messages from context."""
        messages = []
        system_prompt = self.build_system_prompt(selected_skills=selected_skills)
        messages.append(LLMMessage(role="system", content=system_prompt))

        for msg in context.conversation_history:
            messages.append(LLMMessage(role=msg.role, content=msg.content))

        messages.append(LLMMessage(role="user", content=context.user_input))
        return messages

    async def _execute_impl(self, context: AgentContext) -> AgentResponse:
        """Execute agent with tool loop."""
        import structlog
        logger = structlog.get_logger(__name__)

        # Select relevant skills for this query
        selected_skills = await self._select_skills_for_query(
            context.user_input,
            user_id=context.user_id,
        )

        messages = self._build_messages(context, selected_skills=selected_skills)

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
            response = await self._call_with_tools(messages, tool_definitions, context)

            # Check if LLM wants to call tools
            tool_calls = self._extract_tool_calls(response)

            if not tool_calls:
                # No more tool calls, return final response
                confidence = ConfidenceCalculator.from_llm_response(
                    response,
                    tool_calls_made=tool_calls_made,
                    iterations=iterations,
                    max_iterations_reached=False,
                )
                return AgentResponse(
                    content=response.content,
                    confidence=confidence,
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

        # Max iterations reached - calculate confidence with penalty
        from src.agents.confidence import ConfidenceSignals
        signals = ConfidenceSignals(
            tool_calls_total=len(tool_calls_made),
            tool_calls_succeeded=sum(1 for tc in tool_calls_made if tc.get("result", {}).get("success", False)),
            tool_calls_failed=sum(1 for tc in tool_calls_made if not tc.get("result", {}).get("success", False)),
            iterations_used=iterations,
            max_iterations_reached=True,
        )
        confidence = ConfidenceCalculator.calculate(signals)

        return AgentResponse(
            content="I've reached the maximum number of tool operations.",
            confidence=confidence,
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
        context: AgentContext,
    ):
        """Call LLM with tool definitions."""
        return await self._provider.complete(
            messages,
            tools=tools if tools else None,
            user_id=context.user_id,
            agent_id=self.id,
            request_id=context.request_id,
            workflow_id=context.workflow_id,
        )

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
        """Execute a single tool call with error handling and timeout."""
        import structlog
        logger = structlog.get_logger(__name__)

        tool_name = tool_call.get("name", "unknown")
        arguments = tool_call.get("arguments", {})

        # Validate arguments is a dict
        if not isinstance(arguments, dict):
            logger.warning(
                "tool_invalid_arguments",
                tool=tool_name,
                arguments_type=type(arguments).__name__,
            )
            return {
                "success": False,
                "output": None,
                "error": f"Invalid arguments type: expected dict, got {type(arguments).__name__}",
            }

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._registry.execute(tool_name, **arguments),
                timeout=self.TOOL_TIMEOUT_SECONDS,
            )
            return {
                "success": result.success,
                "output": result.output,
                "error": result.error,
            }
        except asyncio.TimeoutError:
            logger.warning(
                "tool_timeout",
                tool=tool_name,
                timeout_seconds=self.TOOL_TIMEOUT_SECONDS,
            )
            return {
                "success": False,
                "output": None,
                "error": f"Tool execution timed out after {self.TOOL_TIMEOUT_SECONDS} seconds",
            }
        except TypeError as e:
            # Argument mismatch (missing required args, unexpected args)
            logger.warning(
                "tool_argument_error",
                tool=tool_name,
                error=str(e),
            )
            return {
                "success": False,
                "output": None,
                "error": f"Tool argument error: {e}",
            }
        except Exception as e:
            # Catch-all for tool execution failures
            logger.error(
                "tool_execution_error",
                tool=tool_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "success": False,
                "output": None,
                "error": f"Tool execution failed: {type(e).__name__}: {e}",
            }
