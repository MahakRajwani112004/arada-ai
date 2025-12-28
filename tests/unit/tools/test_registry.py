"""Tests for Tool Registry - manages tool registration and execution."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.registry import ToolRegistry, get_registry, _global_registry
from src.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult


# ============================================================================
# Test Helper - Mock Tool Implementation
# ============================================================================


class MockTool(BaseTool):
    """Mock tool for testing purposes."""

    def __init__(self, name: str = "mock_tool", description: str = "A mock tool"):
        self._name = name
        self._description = description

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self._name,
            description=self._description,
            parameters=[
                ToolParameter(
                    name="input",
                    type="string",
                    description="Input value",
                    required=True,
                ),
            ],
        )

    async def execute(self, **kwargs) -> ToolResult:
        input_val = kwargs.get("input", "")
        return ToolResult(success=True, output=f"Processed: {input_val}")


class FailingTool(BaseTool):
    """Tool that raises an exception during execution."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="failing_tool",
            description="A tool that always fails",
        )

    async def execute(self, **kwargs) -> ToolResult:
        raise ValueError("Tool execution intentionally failed")


class CalculatorTool(BaseTool):
    """Tool that performs calculation for testing."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="calculator",
            description="Performs arithmetic operations",
            parameters=[
                ToolParameter(name="a", type="number", description="First operand"),
                ToolParameter(name="b", type="number", description="Second operand"),
                ToolParameter(
                    name="operation",
                    type="string",
                    description="Operation to perform",
                    enum=["add", "subtract", "multiply", "divide"],
                ),
            ],
        )

    async def execute(self, a: float, b: float, operation: str, **kwargs) -> ToolResult:
        if operation == "add":
            return ToolResult(success=True, output=a + b)
        elif operation == "subtract":
            return ToolResult(success=True, output=a - b)
        elif operation == "multiply":
            return ToolResult(success=True, output=a * b)
        elif operation == "divide":
            if b == 0:
                return ToolResult(success=False, output=None, error="Division by zero")
            return ToolResult(success=True, output=a / b)
        return ToolResult(success=False, output=None, error=f"Unknown operation: {operation}")


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def registry():
    """Create a fresh ToolRegistry for each test."""
    return ToolRegistry()


@pytest.fixture
def mock_tool():
    """Create a mock tool instance."""
    return MockTool()


@pytest.fixture
def calculator_tool():
    """Create a calculator tool instance."""
    return CalculatorTool()


@pytest.fixture
def failing_tool():
    """Create a failing tool instance."""
    return FailingTool()


@pytest.fixture(autouse=True)
def reset_global_registry():
    """Reset the global registry before and after each test."""
    import src.tools.registry as registry_module
    original = registry_module._global_registry
    registry_module._global_registry = None
    yield
    registry_module._global_registry = original


# ============================================================================
# TestToolRegistry - Initialization
# ============================================================================


class TestToolRegistryInit:
    """Tests for ToolRegistry initialization."""

    def test_init_creates_empty_registry(self, registry):
        """Test that a new registry is empty."""
        assert registry.available_tools == []

    def test_init_internal_dict_is_empty(self, registry):
        """Test that internal tools dictionary is empty."""
        assert len(registry._tools) == 0


# ============================================================================
# TestToolRegistry - Registration
# ============================================================================


class TestToolRegistration:
    """Tests for tool registration functionality."""

    def test_register_single_tool(self, registry, mock_tool):
        """Test registering a single tool."""
        registry.register(mock_tool)

        assert "mock_tool" in registry.available_tools
        assert len(registry.available_tools) == 1

    def test_register_multiple_tools(self, registry, mock_tool, calculator_tool):
        """Test registering multiple tools."""
        registry.register(mock_tool)
        registry.register(calculator_tool)

        assert len(registry.available_tools) == 2
        assert "mock_tool" in registry.available_tools
        assert "calculator" in registry.available_tools

    def test_register_overwrites_duplicate(self, registry):
        """Test that registering a tool with the same name overwrites the existing one."""
        tool1 = MockTool(name="test_tool", description="First version")
        tool2 = MockTool(name="test_tool", description="Second version")

        registry.register(tool1)
        registry.register(tool2)

        assert len(registry.available_tools) == 1
        retrieved_tool = registry.get("test_tool")
        assert retrieved_tool.definition.description == "Second version"

    def test_register_preserves_tool_instance(self, registry, mock_tool):
        """Test that the registered tool is the same instance."""
        registry.register(mock_tool)

        retrieved = registry.get("mock_tool")
        assert retrieved is mock_tool


# ============================================================================
# TestToolRegistry - Unregistration
# ============================================================================


class TestToolUnregistration:
    """Tests for tool unregistration functionality."""

    def test_unregister_existing_tool(self, registry, mock_tool):
        """Test unregistering an existing tool returns True."""
        registry.register(mock_tool)

        result = registry.unregister("mock_tool")

        assert result is True
        assert "mock_tool" not in registry.available_tools

    def test_unregister_nonexistent_tool(self, registry):
        """Test unregistering a non-existent tool returns False."""
        result = registry.unregister("nonexistent_tool")

        assert result is False

    def test_unregister_removes_from_internal_dict(self, registry, mock_tool):
        """Test that unregister removes tool from internal dictionary."""
        registry.register(mock_tool)
        registry.unregister("mock_tool")

        assert "mock_tool" not in registry._tools

    def test_unregister_one_of_multiple(self, registry, mock_tool, calculator_tool):
        """Test unregistering one tool leaves others intact."""
        registry.register(mock_tool)
        registry.register(calculator_tool)

        registry.unregister("mock_tool")

        assert "mock_tool" not in registry.available_tools
        assert "calculator" in registry.available_tools
        assert len(registry.available_tools) == 1


# ============================================================================
# TestToolRegistry - Get Tool
# ============================================================================


class TestGetTool:
    """Tests for retrieving tools by name."""

    def test_get_registered_tool(self, registry, mock_tool):
        """Test getting a registered tool."""
        registry.register(mock_tool)

        retrieved = registry.get("mock_tool")

        assert retrieved is not None
        assert retrieved.name == "mock_tool"

    def test_get_nonexistent_tool_returns_none(self, registry):
        """Test getting a non-existent tool returns None."""
        result = registry.get("nonexistent_tool")

        assert result is None

    def test_get_after_unregister_returns_none(self, registry, mock_tool):
        """Test getting a tool after unregistering returns None."""
        registry.register(mock_tool)
        registry.unregister("mock_tool")

        result = registry.get("mock_tool")

        assert result is None

    def test_get_returns_correct_tool(self, registry, mock_tool, calculator_tool):
        """Test that get returns the correct tool when multiple are registered."""
        registry.register(mock_tool)
        registry.register(calculator_tool)

        retrieved = registry.get("calculator")

        assert retrieved is calculator_tool
        assert retrieved.name == "calculator"


# ============================================================================
# TestToolRegistry - Get Definitions
# ============================================================================


class TestGetDefinitions:
    """Tests for getting tool definitions."""

    def test_get_all_definitions_empty_registry(self, registry):
        """Test getting definitions from empty registry."""
        definitions = registry.get_definitions()

        assert definitions == []

    def test_get_all_definitions(self, registry, mock_tool, calculator_tool):
        """Test getting all tool definitions when no filter provided."""
        registry.register(mock_tool)
        registry.register(calculator_tool)

        definitions = registry.get_definitions()

        assert len(definitions) == 2
        names = [d.name for d in definitions]
        assert "mock_tool" in names
        assert "calculator" in names

    def test_get_definitions_with_specific_names(self, registry, mock_tool, calculator_tool):
        """Test getting definitions for specific tool names."""
        registry.register(mock_tool)
        registry.register(calculator_tool)

        definitions = registry.get_definitions(["mock_tool"])

        assert len(definitions) == 1
        assert definitions[0].name == "mock_tool"

    def test_get_definitions_with_multiple_names(self, registry, mock_tool, calculator_tool):
        """Test getting definitions for multiple specific tools."""
        registry.register(mock_tool)
        registry.register(calculator_tool)

        definitions = registry.get_definitions(["mock_tool", "calculator"])

        assert len(definitions) == 2

    def test_get_definitions_ignores_missing_tools(self, registry, mock_tool):
        """Test that missing tool names are silently ignored."""
        registry.register(mock_tool)

        definitions = registry.get_definitions(["mock_tool", "nonexistent"])

        assert len(definitions) == 1
        assert definitions[0].name == "mock_tool"

    def test_get_definitions_all_missing(self, registry, mock_tool):
        """Test requesting only missing tools returns empty list."""
        registry.register(mock_tool)

        definitions = registry.get_definitions(["nonexistent1", "nonexistent2"])

        assert definitions == []

    def test_get_definitions_empty_list(self, registry, mock_tool):
        """Test getting definitions with empty list returns empty."""
        registry.register(mock_tool)

        definitions = registry.get_definitions([])

        assert definitions == []

    def test_get_definitions_returns_tool_definition_objects(self, registry, mock_tool):
        """Test that returned definitions are ToolDefinition instances."""
        registry.register(mock_tool)

        definitions = registry.get_definitions()

        assert all(isinstance(d, ToolDefinition) for d in definitions)


# ============================================================================
# TestToolRegistry - Get OpenAI Tools
# ============================================================================


class TestGetOpenAITools:
    """Tests for getting tools in OpenAI format."""

    def test_get_openai_tools_empty_registry(self, registry):
        """Test getting OpenAI tools from empty registry."""
        tools = registry.get_openai_tools()

        assert tools == []

    def test_get_openai_tools_format(self, registry, mock_tool):
        """Test OpenAI tools have correct format."""
        registry.register(mock_tool)

        tools = registry.get_openai_tools()

        assert len(tools) == 1
        tool = tools[0]
        assert tool["type"] == "function"
        assert "function" in tool
        assert tool["function"]["name"] == "mock_tool"
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]

    def test_get_openai_tools_with_filter(self, registry, mock_tool, calculator_tool):
        """Test filtering OpenAI tools by name."""
        registry.register(mock_tool)
        registry.register(calculator_tool)

        tools = registry.get_openai_tools(["calculator"])

        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "calculator"

    def test_get_openai_tools_parameters_structure(self, registry, calculator_tool):
        """Test OpenAI tools have correct parameter structure."""
        registry.register(calculator_tool)

        tools = registry.get_openai_tools()
        params = tools[0]["function"]["parameters"]

        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params
        assert "a" in params["properties"]
        assert "b" in params["properties"]
        assert "operation" in params["properties"]

    def test_get_openai_tools_enum_included(self, registry, calculator_tool):
        """Test that enum values are included in OpenAI format."""
        registry.register(calculator_tool)

        tools = registry.get_openai_tools()
        props = tools[0]["function"]["parameters"]["properties"]

        assert "enum" in props["operation"]
        assert props["operation"]["enum"] == ["add", "subtract", "multiply", "divide"]


# ============================================================================
# TestToolRegistry - Execute
# ============================================================================


class TestExecute:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_execute_registered_tool(self, registry, mock_tool):
        """Test executing a registered tool."""
        registry.register(mock_tool)

        result = await registry.execute("mock_tool", input="test value")

        assert result.success is True
        assert result.output == "Processed: test value"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self, registry):
        """Test executing a non-existent tool returns failure."""
        result = await registry.execute("nonexistent", input="value")

        assert result.success is False
        assert result.output is None
        assert result.error == "Tool not found: nonexistent"

    @pytest.mark.asyncio
    async def test_execute_handles_tool_exception(self, registry, failing_tool):
        """Test that tool exceptions are caught and returned as errors."""
        registry.register(failing_tool)

        result = await registry.execute("failing_tool")

        assert result.success is False
        assert result.output is None
        assert "Tool execution failed" in result.error
        assert "intentionally failed" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_kwargs(self, registry, calculator_tool):
        """Test executing a tool with keyword arguments."""
        registry.register(calculator_tool)

        result = await registry.execute("calculator", a=10, b=5, operation="add")

        assert result.success is True
        assert result.output == 15

    @pytest.mark.asyncio
    async def test_execute_calculator_operations(self, registry, calculator_tool):
        """Test various calculator operations."""
        registry.register(calculator_tool)

        # Test addition
        result = await registry.execute("calculator", a=10, b=5, operation="add")
        assert result.output == 15

        # Test subtraction
        result = await registry.execute("calculator", a=10, b=5, operation="subtract")
        assert result.output == 5

        # Test multiplication
        result = await registry.execute("calculator", a=10, b=5, operation="multiply")
        assert result.output == 50

        # Test division
        result = await registry.execute("calculator", a=10, b=5, operation="divide")
        assert result.output == 2.0

    @pytest.mark.asyncio
    async def test_execute_tool_returns_tool_result(self, registry, mock_tool):
        """Test that execute returns a ToolResult instance."""
        registry.register(mock_tool)

        result = await registry.execute("mock_tool", input="test")

        assert isinstance(result, ToolResult)


# ============================================================================
# TestToolRegistry - Available Tools Property
# ============================================================================


class TestAvailableTools:
    """Tests for the available_tools property."""

    def test_available_tools_empty(self, registry):
        """Test available_tools is empty for new registry."""
        assert registry.available_tools == []

    def test_available_tools_returns_list(self, registry, mock_tool):
        """Test available_tools returns a list."""
        registry.register(mock_tool)

        result = registry.available_tools

        assert isinstance(result, list)

    def test_available_tools_contains_registered_names(self, registry, mock_tool, calculator_tool):
        """Test available_tools contains all registered tool names."""
        registry.register(mock_tool)
        registry.register(calculator_tool)

        tools = registry.available_tools

        assert len(tools) == 2
        assert "mock_tool" in tools
        assert "calculator" in tools

    def test_available_tools_reflects_unregistration(self, registry, mock_tool):
        """Test available_tools updates after unregistration."""
        registry.register(mock_tool)
        registry.unregister("mock_tool")

        assert registry.available_tools == []


# ============================================================================
# TestGlobalRegistry
# ============================================================================


class TestGlobalRegistry:
    """Tests for the global registry functions."""

    def test_get_registry_creates_instance(self):
        """Test get_registry creates a new instance if none exists."""
        registry = get_registry()

        assert registry is not None
        assert isinstance(registry, ToolRegistry)

    def test_get_registry_returns_same_instance(self):
        """Test get_registry returns the same instance on subsequent calls."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_global_registry_persists_tools(self):
        """Test that tools registered in global registry persist."""
        registry = get_registry()
        tool = MockTool(name="global_test_tool")
        registry.register(tool)

        # Get registry again
        same_registry = get_registry()

        assert "global_test_tool" in same_registry.available_tools

    def test_global_registry_is_separate_from_local(self):
        """Test that global registry is separate from locally created registries."""
        global_registry = get_registry()
        local_registry = ToolRegistry()

        tool = MockTool(name="local_only")
        local_registry.register(tool)

        assert "local_only" in local_registry.available_tools
        assert "local_only" not in global_registry.available_tools


# ============================================================================
# TestEdgeCases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_register_tool_with_empty_name(self, registry):
        """Test registering a tool with empty name."""
        tool = MockTool(name="", description="Empty name tool")
        registry.register(tool)

        assert "" in registry.available_tools
        assert registry.get("") is tool

    def test_register_tool_with_special_characters(self, registry):
        """Test registering a tool with special characters in name."""
        tool = MockTool(name="tool-with_special.chars", description="Special chars")
        registry.register(tool)

        assert "tool-with_special.chars" in registry.available_tools

    @pytest.mark.asyncio
    async def test_execute_with_no_arguments(self, registry):
        """Test executing a tool with no arguments."""
        tool = MockTool()
        registry.register(tool)

        result = await registry.execute("mock_tool")

        assert result.success is True
        assert result.output == "Processed: "

    def test_get_definitions_with_none_explicitly(self, registry, mock_tool):
        """Test that passing None returns all definitions."""
        registry.register(mock_tool)

        definitions = registry.get_definitions(None)

        assert len(definitions) == 1

    @pytest.mark.asyncio
    async def test_execute_after_re_registration(self, registry):
        """Test executing a tool after it has been re-registered."""
        tool1 = MockTool(name="test", description="v1")
        tool2 = MockTool(name="test", description="v2")

        registry.register(tool1)
        registry.register(tool2)  # Re-register with same name

        # Should use the latest registered tool
        retrieved = registry.get("test")
        assert retrieved.definition.description == "v2"

    def test_multiple_registrations_same_tool_instance(self, registry, mock_tool):
        """Test registering the same tool instance multiple times."""
        registry.register(mock_tool)
        registry.register(mock_tool)  # Same instance again

        assert len(registry.available_tools) == 1
        assert registry.get("mock_tool") is mock_tool

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self, registry, mock_tool, calculator_tool):
        """Test executing multiple tools concurrently."""
        import asyncio

        registry.register(mock_tool)
        registry.register(calculator_tool)

        results = await asyncio.gather(
            registry.execute("mock_tool", input="test1"),
            registry.execute("mock_tool", input="test2"),
            registry.execute("calculator", a=1, b=2, operation="add"),
        )

        assert all(r.success for r in results)
        assert results[0].output == "Processed: test1"
        assert results[1].output == "Processed: test2"
        assert results[2].output == 3
