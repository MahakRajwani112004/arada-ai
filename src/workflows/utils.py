"""Workflow utility functions for tool handling."""
from typing import Any, Dict, List

from src.activities.llm_activity import ToolDefinitionInput


def sanitize_tool_name(name: str) -> str:
    """
    Convert tool name to OpenAI-compatible format.

    OpenAI requires tool names to match ^[a-zA-Z0-9_-]+$ (no colons).
    We convert colons to double underscores.
    """
    return name.replace(":", "__")


def build_param_schema(param: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build parameter schema with proper array handling.

    Ensures array types have items schema as required by OpenAI.
    """
    schema: Dict[str, Any] = {
        "type": param["type"],
        "description": param["description"],
    }
    # For array types, add items schema
    if param["type"] == "array":
        schema["items"] = param.get("items") or {"type": "string"}
    return schema


def build_tool_definitions(
    definitions: List[Any],
    tool_name_map: Dict[str, str],
) -> List[ToolDefinitionInput]:
    """
    Convert tool definitions to LLM activity format.

    Args:
        definitions: List of tool definition objects
        tool_name_map: Dict to populate with sanitized -> original name mapping

    Returns:
        List of ToolDefinitionInput for LLM activity
    """
    tools = []
    for d in definitions:
        sanitized_name = sanitize_tool_name(d.name)
        tool_name_map[sanitized_name] = d.name
        tools.append(
            ToolDefinitionInput(
                name=sanitized_name,
                description=d.description,
                parameters={
                    "type": "object",
                    "properties": {
                        p["name"]: build_param_schema(p) for p in d.parameters
                    },
                    "required": [
                        p["name"] for p in d.parameters if p.get("required", True)
                    ],
                },
            )
        )
    return tools
