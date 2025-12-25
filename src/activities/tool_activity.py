"""Tool Execution Activity for Temporal workflows."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from temporalio import activity

from src.tools.registry import get_registry


async def resolve_mcp_tool_name(tool_name: str) -> str:
    """Resolve mcp:{template}:{tool} format to actual server_id:tool format.

    Args:
        tool_name: Tool name like mcp:google-calendar:list_events

    Returns:
        Resolved tool name like srv_xxx:list_events, or original if not found
    """
    if not tool_name.startswith("mcp:"):
        return tool_name

    # Parse: mcp:{template}:{tool_name}
    parts = tool_name.split(":", 2)
    if len(parts) != 3:
        activity.logger.warning(f"Invalid MCP tool format: {tool_name}")
        return tool_name

    _, template, mcp_tool = parts

    # Look up server by template
    from src.mcp.manager import get_mcp_manager

    manager = get_mcp_manager()
    servers = await manager.list_servers()

    # Find server matching the template
    for server in servers:
        if server.template == template:
            resolved = f"{server.id}:{mcp_tool}"
            activity.logger.info(f"Resolved MCP tool: {tool_name} -> {resolved}")
            return resolved

    activity.logger.warning(
        f"No MCP server found for template '{template}'. "
        f"Available templates: {[s.template for s in servers]}"
    )
    return tool_name


@dataclass
class ToolExecutionInput:
    """Input for tool execution activity."""

    tool_name: str
    user_id: str  # Required for user-level analytics
    arguments: Dict[str, Any] = field(default_factory=dict)
    # Agent execution context (for nested agent calls)
    current_depth: int = 0
    max_depth: int = 3
    parent_session_id: Optional[str] = None


@dataclass
class ToolExecutionOutput:
    """Output from tool execution activity."""

    success: bool
    output: Any
    tool_name: str
    error: Optional[str] = None


@activity.defn
async def execute_tool(input: ToolExecutionInput) -> ToolExecutionOutput:
    """
    Execute a tool as a Temporal activity.

    This activity executes the specified tool with the given arguments.
    Tools must be registered in the global registry.

    Special handling for:
    - agent: prefix - routes to execute_agent_as_tool activity
    - mcp: prefix - resolves to actual server_id:tool format
    """
    activity.logger.info(f"Executing tool: {input.tool_name} with args: {input.arguments}")

    # Check if this is an agent tool call
    if input.tool_name.startswith("agent:"):
        return await _execute_agent_tool(input)

    # Resolve MCP tool names (mcp:template:tool -> srv_xxx:tool)
    resolved_tool_name = await resolve_mcp_tool_name(input.tool_name)

    registry = get_registry()

    # Log available tools for debugging
    available = registry.available_tools
    activity.logger.info(f"Available tools in registry: {available}")

    if resolved_tool_name not in available:
        activity.logger.error(
            f"Tool {input.tool_name} (resolved: {resolved_tool_name}) not found. "
            f"Available: {available}"
        )
        return ToolExecutionOutput(
            success=False,
            output=None,
            tool_name=input.tool_name,
            error=f"Tool not found: {resolved_tool_name}. Available tools: {available}",
        )

    result = await registry.execute(resolved_tool_name, **input.arguments)

    if result.success:
        activity.logger.info(f"Tool {resolved_tool_name} completed successfully: {result.output}")
    else:
        activity.logger.warning(f"Tool {resolved_tool_name} failed: {result.error}")

    return ToolExecutionOutput(
        success=result.success,
        output=result.output,
        tool_name=input.tool_name,  # Return original name for consistency
        error=result.error,
    )


async def _execute_agent_tool(input: ToolExecutionInput) -> ToolExecutionOutput:
    """
    Execute an agent as a tool.

    This is called when tool_name starts with 'agent:'.
    Routes to the execute_agent_as_tool activity.
    """
    from src.activities.agent_tool_activity import (
        AgentToolExecutionInput,
        execute_agent_as_tool,
    )

    # Extract agent ID from tool name (format: agent:{agent_id})
    agent_id = input.tool_name.split(":", 1)[1]

    activity.logger.info(
        f"Routing to agent execution: {agent_id}, "
        f"depth={input.current_depth}/{input.max_depth}"
    )

    # Build agent execution input
    agent_input = AgentToolExecutionInput(
        agent_id=agent_id,
        query=input.arguments.get("query", ""),
        user_id=input.user_id,
        context={
            "additional_context": input.arguments.get("context", ""),
            "conversation_history": input.arguments.get("conversation_history", []),
        },
        current_depth=input.current_depth,
        max_depth=input.max_depth,
        parent_session_id=input.parent_session_id,
    )

    # Execute the agent
    result = await execute_agent_as_tool(agent_input)

    return ToolExecutionOutput(
        success=result.success,
        output=result.content,
        tool_name=input.tool_name,
        error=result.error,
    )


@dataclass
class GetToolDefinitionsInput:
    """Input for getting tool definitions."""

    tool_names: Optional[List[str]] = None


@dataclass
class ToolDefinitionInfo:
    """Simplified tool definition for serialization."""

    name: str
    description: str
    parameters: List[Dict[str, Any]]


@dataclass
class GetToolDefinitionsOutput:
    """Output with tool definitions."""

    definitions: List[ToolDefinitionInfo]
    openai_format: List[Dict[str, Any]]


@activity.defn
async def get_tool_definitions(
    input: GetToolDefinitionsInput,
) -> GetToolDefinitionsOutput:
    """
    Get tool definitions for the specified tools.

    Returns definitions in both internal and OpenAI formats.
    Resolves mcp:template:tool format to actual server_id:tool.
    """
    registry = get_registry()

    # Resolve MCP tool names if provided
    resolved_names = None
    if input.tool_names:
        resolved_names = []
        for name in input.tool_names:
            resolved = await resolve_mcp_tool_name(name)
            resolved_names.append(resolved)

    definitions = registry.get_definitions(resolved_names)
    openai_tools = registry.get_openai_tools(resolved_names)

    definition_infos = [
        ToolDefinitionInfo(
            name=d.name,
            description=d.description,
            parameters=[
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "items": p.items,  # Include items for array types
                }
                for p in d.parameters
            ],
        )
        for d in definitions
    ]

    return GetToolDefinitionsOutput(
        definitions=definition_infos,
        openai_format=openai_tools,
    )
