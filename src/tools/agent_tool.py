"""Agent Tool - wraps agent execution as a callable tool."""
from typing import Any, Dict, Optional

from src.models.agent_config import AgentConfig
from src.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult


class AgentTool(BaseTool):
    """
    Wraps an agent as a tool that can be called by other agents.

    This enables:
    - LLM to call agents like functions via native tool calling
    - Nested agent calls (A -> B -> C)
    - Agents appearing in tool lists with descriptions

    Note: Actual execution happens via Temporal activities/child workflows.
    This class provides the tool definition and interface.
    """

    def __init__(
        self,
        agent_config: AgentConfig,
        execution_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize AgentTool.

        Args:
            agent_config: Configuration of the agent to wrap
            execution_context: Optional context (depth, parent workflow, etc.)
        """
        self._config = agent_config
        self._context = execution_context or {}
        self._definition = self._create_definition()

    def _create_definition(self) -> ToolDefinition:
        """Create tool definition from agent config."""
        # Tool name format: agent:<agent_id>
        tool_name = f"agent:{self._config.id}"

        # Build description from agent config
        description = self._config.description or f"Execute agent: {self._config.name}"
        if self._config.role:
            description += f" Role: {self._config.role.title}."

        # Standard parameters for agent invocation
        parameters = [
            ToolParameter(
                name="query",
                type="string",
                description="The input/query to send to the agent",
                required=True,
            ),
            ToolParameter(
                name="context",
                type="string",
                description="Optional additional context to provide to the agent",
                required=False,
            ),
        ]

        return ToolDefinition(
            name=tool_name,
            description=description,
            parameters=parameters,
        )

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition."""
        return self._definition

    @property
    def agent_id(self) -> str:
        """Get the wrapped agent's ID."""
        return self._config.id

    @property
    def agent_name(self) -> str:
        """Get the wrapped agent's name."""
        return self._config.name

    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the agent as a tool.

        Note: This method is typically not called directly. Instead,
        the tool_activity detects agent: prefix and routes to
        execute_agent_as_tool activity which handles Temporal execution.

        Args:
            query: The input to send to the agent
            context: Optional additional context

        Returns:
            ToolResult with agent's response
        """
        query = kwargs.get("query", "")
        context = kwargs.get("context", "")

        if not query:
            return ToolResult(
                success=False,
                output=None,
                error="Query parameter is required",
            )

        # This is a placeholder - actual execution happens via Temporal
        # The tool_activity.py will detect agent: prefix and route appropriately
        return ToolResult(
            success=False,
            output=None,
            error="AgentTool.execute() should not be called directly. "
            "Use Temporal activity for agent execution.",
        )


def create_agent_tools_from_configs(
    configs: list[AgentConfig],
) -> list[AgentTool]:
    """
    Create AgentTool instances from a list of agent configs.

    Args:
        configs: List of agent configurations

    Returns:
        List of AgentTool instances
    """
    return [AgentTool(config) for config in configs]
