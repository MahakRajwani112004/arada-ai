"""Builtin tools."""
from .calculator import CalculatorTool
from .datetime_tool import DateTimeTool
from .document_generator import DocumentGeneratorTool, TemplateFillerTool
from .docx_template_filler import DocxTemplateFiller

__all__ = [
    "CalculatorTool",
    "DateTimeTool",
    "DocumentGeneratorTool",
    "TemplateFillerTool",
    "DocxTemplateFiller",
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
