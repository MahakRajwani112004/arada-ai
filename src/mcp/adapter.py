"""MCP tool adapter - wraps MCP tools as BaseTool instances."""

from typing import TYPE_CHECKING, Any, List

from src.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult

from .models import MCPToolInfo

if TYPE_CHECKING:
    from .client import MCPClient


class MCPToolAdapter(BaseTool):
    """Adapts an MCP tool to the BaseTool interface.

    This allows MCP tools to be registered with the global ToolRegistry
    and used by agents just like builtin tools.
    """

    def __init__(self, client: "MCPClient", tool_info: MCPToolInfo):
        """Initialize MCP tool adapter.

        Args:
            client: MCP client for executing the tool
            tool_info: Tool information from MCP server
        """
        self._client = client
        self._tool_info = tool_info
        self._definition = self._create_definition()

    def _create_definition(self) -> ToolDefinition:
        """Create ToolDefinition from MCP tool schema."""
        # Tool name is prefixed with server ID for uniqueness
        tool_name = f"{self._tool_info.server_id}:{self._tool_info.name}"

        # Convert JSON Schema to ToolParameters
        parameters = self._parse_json_schema(self._tool_info.input_schema)

        return ToolDefinition(
            name=tool_name,
            description=self._tool_info.description or f"MCP tool: {self._tool_info.name}",
            parameters=parameters,
        )

    def _parse_json_schema(self, schema: dict) -> List[ToolParameter]:
        """Parse JSON Schema into ToolParameters."""
        parameters = []

        if not schema:
            return parameters

        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        for name, prop in properties.items():
            param_type = prop.get("type", "string")

            # Map JSON Schema types to our types
            type_mapping = {
                "string": "string",
                "integer": "number",
                "number": "number",
                "boolean": "boolean",
                "array": "array",
                "object": "object",
            }

            # Get items schema for array types
            items = None
            if param_type == "array":
                items = prop.get("items", {"type": "string"})

            parameters.append(
                ToolParameter(
                    name=name,
                    type=type_mapping.get(param_type, "string"),
                    description=prop.get("description", f"Parameter: {name}"),
                    required=name in required,
                    default=prop.get("default"),
                    enum=prop.get("enum"),
                    items=items,
                )
            )

        return parameters

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition."""
        return self._definition

    @property
    def mcp_tool_name(self) -> str:
        """Get the original MCP tool name (without server prefix)."""
        return self._tool_info.name

    @property
    def server_id(self) -> str:
        """Get the MCP server ID."""
        return self._tool_info.server_id

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the MCP tool.

        Args:
            **kwargs: Tool arguments

        Returns:
            ToolResult with success status and output
        """
        result = await self._client.call_tool(self.mcp_tool_name, kwargs)

        if result.success:
            return ToolResult(
                success=True,
                output=result.content,
            )
        else:
            return ToolResult(
                success=False,
                output=None,
                error=result.error,
            )
