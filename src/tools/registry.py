"""Tool Registry - manages available tools."""
from typing import Any, Dict, List, Optional, Type

from .base import BaseTool, ToolDefinition, ToolResult


class ToolRegistry:
    """
    Registry for managing tools.

    Usage:
        registry = ToolRegistry()
        registry.register(MyTool())

        # Get tool definitions for LLM
        definitions = registry.get_definitions(["my_tool"])

        # Execute a tool
        result = await registry.execute("my_tool", arg1="value")
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool by name.

        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_definitions(
        self, tool_names: Optional[List[str]] = None
    ) -> List[ToolDefinition]:
        """
        Get tool definitions for specified tools.

        Args:
            tool_names: List of tool names. If None, returns all.

        Returns:
            List of tool definitions
        """
        if tool_names is None:
            return [tool.definition for tool in self._tools.values()]

        definitions = []
        for name in tool_names:
            tool = self._tools.get(name)
            if tool:
                definitions.append(tool.definition)
        return definitions

    def get_openai_tools(
        self, tool_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tools in OpenAI function calling format.

        Args:
            tool_names: List of tool names. If None, returns all.

        Returns:
            List of tools in OpenAI format
        """
        definitions = self.get_definitions(tool_names)
        return [d.to_openai_format() for d in definitions]

    async def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            **kwargs: Tool arguments

        Returns:
            ToolResult with execution output
        """
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool not found: {name}",
            )

        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool execution failed: {str(e)}",
            )

    @property
    def available_tools(self) -> List[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
