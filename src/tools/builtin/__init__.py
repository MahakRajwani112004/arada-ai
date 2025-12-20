"""Builtin tools."""
from .calculator import CalculatorTool
from .datetime_tool import DateTimeTool

__all__ = [
    "CalculatorTool",
    "DateTimeTool",
]


def register_builtin_tools():
    """Register all builtin tools in the global registry."""
    from src.tools.registry import get_registry

    registry = get_registry()
    registry.register(CalculatorTool())
    registry.register(DateTimeTool())
