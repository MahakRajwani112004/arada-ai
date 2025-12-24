"""Builtin tools."""
from .calculator import CalculatorTool
from .datetime_tool import DateTimeTool
from .kpi_calculator import KPICalculatorTool
from .real_estate_query import RealEstateQueryTool
from .what_if_simulator import WhatIfSimulatorTool

__all__ = [
    "CalculatorTool",
    "DateTimeTool",
    "KPICalculatorTool",
    "RealEstateQueryTool",
    "WhatIfSimulatorTool",
]


def register_builtin_tools():
    """Register all builtin tools in the global registry."""
    from src.tools.registry import get_registry

    registry = get_registry()
    registry.register(CalculatorTool())
    registry.register(DateTimeTool())
    # Arada AI Real Estate Analytics tools
    registry.register(KPICalculatorTool())
    registry.register(RealEstateQueryTool())
    registry.register(WhatIfSimulatorTool())
