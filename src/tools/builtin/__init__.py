"""Builtin tools."""
from .calculator import CalculatorTool
from .datetime_tool import DateTimeTool
from .document_generator import DocumentGeneratorTool, TemplateFillerTool
from .docx_template_filler import DocxTemplateFiller
from .kpi_calculator import KPICalculatorTool
from .real_estate_query import RealEstateQueryTool
from .what_if_simulator import WhatIfSimulatorTool
from .chart_generator import ChartGeneratorTool

__all__ = [
    "CalculatorTool",
    "DateTimeTool",
    "DocumentGeneratorTool",
    "TemplateFillerTool",
    "DocxTemplateFiller",
    "KPICalculatorTool",
    "RealEstateQueryTool",
    "WhatIfSimulatorTool",
    "ChartGeneratorTool",
]


def register_builtin_tools():
    """Register all builtin tools in the global registry."""
    from src.tools.registry import get_registry

    registry = get_registry()
    registry.register(CalculatorTool())
    registry.register(DateTimeTool())
    registry.register(DocumentGeneratorTool())
    registry.register(TemplateFillerTool())
    registry.register(DocxTemplateFiller())
    # Arada AI Real Estate Analytics tools
    registry.register(KPICalculatorTool())
    registry.register(RealEstateQueryTool())
    registry.register(WhatIfSimulatorTool())
    registry.register(ChartGeneratorTool())
