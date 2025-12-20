"""Tool Execution Activity for Temporal workflows."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from temporalio import activity

from src.tools.registry import get_registry


@dataclass
class ToolExecutionInput:
    """Input for tool execution activity."""

    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)


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
    """
    activity.logger.info(f"Executing tool: {input.tool_name} with args: {input.arguments}")

    registry = get_registry()

    # Log available tools for debugging
    available = registry.available_tools
    activity.logger.info(f"Available tools in registry: {available}")

    if input.tool_name not in available:
        activity.logger.error(f"Tool {input.tool_name} not found in registry. Available: {available}")
        return ToolExecutionOutput(
            success=False,
            output=None,
            tool_name=input.tool_name,
            error=f"Tool not found: {input.tool_name}. Available tools: {available}",
        )

    result = await registry.execute(input.tool_name, **input.arguments)

    if result.success:
        activity.logger.info(f"Tool {input.tool_name} completed successfully: {result.output}")
    else:
        activity.logger.warning(f"Tool {input.tool_name} failed: {result.error}")

    return ToolExecutionOutput(
        success=result.success,
        output=result.output,
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
    """
    registry = get_registry()

    definitions = registry.get_definitions(input.tool_names)
    openai_tools = registry.get_openai_tools(input.tool_names)

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
