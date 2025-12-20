"""Base tool interface and types."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""

    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[str]] = None
    items: Optional[Dict[str, Any]] = None  # For array types


@dataclass
class ToolDefinition:
    """Definition of a tool for LLM function calling."""

    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        properties = {}
        required = []

        for param in self.parameters:
            prop: Dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            # For array types, include items schema (required by OpenAI)
            if param.type == "array":
                if param.items:
                    prop["items"] = param.items
                else:
                    # Default to string items if not specified
                    prop["items"] = {"type": "string"}

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    output: Any
    error: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for tools."""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the tool definition."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with the given arguments.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult with success status and output
        """
        pass

    @property
    def name(self) -> str:
        """Get tool name from definition."""
        return self.definition.name
