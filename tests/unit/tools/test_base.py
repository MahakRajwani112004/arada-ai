"""Tests for base tool interface and types."""

import pytest
from src.tools.base import ToolParameter, ToolDefinition, ToolResult, BaseTool


class TestToolParameter:
    """Tests for ToolParameter dataclass."""

    def test_create_basic_parameter(self):
        """Test creating a basic parameter."""
        param = ToolParameter(
            name="query",
            type="string",
            description="The search query",
        )

        assert param.name == "query"
        assert param.type == "string"
        assert param.description == "The search query"
        assert param.required is True  # default

    def test_optional_parameter(self):
        """Test creating an optional parameter."""
        param = ToolParameter(
            name="limit",
            type="number",
            description="Maximum results",
            required=False,
            default=10,
        )

        assert param.required is False
        assert param.default == 10

    def test_parameter_with_enum(self):
        """Test creating a parameter with enum values."""
        param = ToolParameter(
            name="sort",
            type="string",
            description="Sort order",
            enum=["asc", "desc"],
        )

        assert param.enum == ["asc", "desc"]

    def test_array_parameter_with_items(self):
        """Test creating an array parameter with items."""
        param = ToolParameter(
            name="tags",
            type="array",
            description="Tags to filter by",
            items={"type": "string"},
        )

        assert param.type == "array"
        assert param.items == {"type": "string"}


class TestToolDefinition:
    """Tests for ToolDefinition dataclass."""

    def test_create_tool_definition(self):
        """Test creating a tool definition."""
        tool_def = ToolDefinition(
            name="search",
            description="Search for items",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query",
                )
            ],
        )

        assert tool_def.name == "search"
        assert tool_def.description == "Search for items"
        assert len(tool_def.parameters) == 1

    def test_empty_parameters(self):
        """Test tool with no parameters."""
        tool_def = ToolDefinition(
            name="get_time",
            description="Get current time",
        )

        assert tool_def.parameters == []

    def test_to_openai_format_basic(self):
        """Test converting to OpenAI format."""
        tool_def = ToolDefinition(
            name="calculator",
            description="Perform calculations",
            parameters=[
                ToolParameter(
                    name="expression",
                    type="string",
                    description="Mathematical expression",
                )
            ],
        )

        result = tool_def.to_openai_format()

        assert result["type"] == "function"
        assert result["function"]["name"] == "calculator"
        assert result["function"]["description"] == "Perform calculations"
        assert "expression" in result["function"]["parameters"]["properties"]
        assert "expression" in result["function"]["parameters"]["required"]

    def test_to_openai_format_with_optional(self):
        """Test OpenAI format with optional parameters."""
        tool_def = ToolDefinition(
            name="search",
            description="Search items",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Query",
                    required=True,
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Limit",
                    required=False,
                ),
            ],
        )

        result = tool_def.to_openai_format()

        required = result["function"]["parameters"]["required"]
        assert "query" in required
        assert "limit" not in required

    def test_to_openai_format_with_enum(self):
        """Test OpenAI format with enum parameter."""
        tool_def = ToolDefinition(
            name="sort",
            description="Sort items",
            parameters=[
                ToolParameter(
                    name="order",
                    type="string",
                    description="Sort order",
                    enum=["asc", "desc"],
                )
            ],
        )

        result = tool_def.to_openai_format()
        props = result["function"]["parameters"]["properties"]

        assert props["order"]["enum"] == ["asc", "desc"]

    def test_to_openai_format_array_with_items(self):
        """Test OpenAI format with array parameter and items."""
        tool_def = ToolDefinition(
            name="filter",
            description="Filter by tags",
            parameters=[
                ToolParameter(
                    name="tags",
                    type="array",
                    description="Tags",
                    items={"type": "string"},
                )
            ],
        )

        result = tool_def.to_openai_format()
        props = result["function"]["parameters"]["properties"]

        assert props["tags"]["type"] == "array"
        assert props["tags"]["items"] == {"type": "string"}

    def test_to_openai_format_array_default_items(self):
        """Test OpenAI format with array but no items specified."""
        tool_def = ToolDefinition(
            name="filter",
            description="Filter by tags",
            parameters=[
                ToolParameter(
                    name="tags",
                    type="array",
                    description="Tags",
                )
            ],
        )

        result = tool_def.to_openai_format()
        props = result["function"]["parameters"]["properties"]

        # Should default to string items
        assert props["tags"]["items"] == {"type": "string"}


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful result."""
        result = ToolResult(
            success=True,
            output={"data": "test"},
        )

        assert result.success is True
        assert result.output == {"data": "test"}
        assert result.error is None

    def test_failed_result(self):
        """Test creating a failed result."""
        result = ToolResult(
            success=False,
            output=None,
            error="Something went wrong",
        )

        assert result.success is False
        assert result.output is None
        assert result.error == "Something went wrong"

    def test_result_with_any_output(self):
        """Test result can hold any output type."""
        # String output
        result1 = ToolResult(success=True, output="Hello")
        assert result1.output == "Hello"

        # List output
        result2 = ToolResult(success=True, output=[1, 2, 3])
        assert result2.output == [1, 2, 3]

        # Number output
        result3 = ToolResult(success=True, output=42)
        assert result3.output == 42


class TestBaseTool:
    """Tests for BaseTool abstract class."""

    def test_cannot_instantiate_directly(self):
        """Test that BaseTool cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseTool()

    def test_subclass_implementation(self):
        """Test implementing a tool subclass."""

        class MockTool(BaseTool):
            @property
            def definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="mock_tool",
                    description="A mock tool for testing",
                )

            async def execute(self, **kwargs) -> ToolResult:
                return ToolResult(success=True, output="executed")

        tool = MockTool()
        assert tool.name == "mock_tool"
        assert tool.definition.description == "A mock tool for testing"

    def test_name_property(self):
        """Test that name property returns definition name."""

        class TestTool(BaseTool):
            @property
            def definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="test_tool",
                    description="Test",
                )

            async def execute(self, **kwargs) -> ToolResult:
                return ToolResult(success=True, output=None)

        tool = TestTool()
        assert tool.name == "test_tool"

    @pytest.mark.asyncio
    async def test_execute_method(self):
        """Test executing a tool."""

        class AddTool(BaseTool):
            @property
            def definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="add",
                    description="Add two numbers",
                    parameters=[
                        ToolParameter(name="a", type="number", description="First"),
                        ToolParameter(name="b", type="number", description="Second"),
                    ],
                )

            async def execute(self, a: int, b: int, **kwargs) -> ToolResult:
                return ToolResult(success=True, output=a + b)

        tool = AddTool()
        result = await tool.execute(a=5, b=3)

        assert result.success is True
        assert result.output == 8
