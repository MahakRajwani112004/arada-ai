"""Unit tests for MCP Tool Adapter.

Tests cover:
- MCPToolAdapter class initialization
- Tool definition creation from MCP tool info
- JSON Schema to ToolParameter conversion
- Tool execution and result handling
- Error handling for tool calls
- Property accessors
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.mcp.adapter import MCPToolAdapter
from src.mcp.models import MCPToolInfo, MCPToolCallResult
from src.tools.base import ToolDefinition, ToolParameter, ToolResult


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = AsyncMock()
    client.call_tool = AsyncMock()
    return client


@pytest.fixture
def simple_tool_info():
    """Create a simple MCP tool info without parameters."""
    return MCPToolInfo(
        name="simple_tool",
        description="A simple tool with no parameters",
        input_schema={},
        server_id="test-server",
    )


@pytest.fixture
def tool_with_string_param():
    """Create a tool with a string parameter."""
    return MCPToolInfo(
        name="search",
        description="Search for content",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                }
            },
            "required": ["query"],
        },
        server_id="github-server",
    )


@pytest.fixture
def tool_with_multiple_params():
    """Create a tool with multiple parameter types."""
    return MCPToolInfo(
        name="create_issue",
        description="Create a new issue in the repository",
        input_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Issue title",
                },
                "body": {
                    "type": "string",
                    "description": "Issue body content",
                },
                "labels": {
                    "type": "array",
                    "description": "Labels to apply",
                    "items": {"type": "string"},
                },
                "priority": {
                    "type": "integer",
                    "description": "Priority level",
                    "default": 1,
                },
                "assignee": {
                    "type": "string",
                    "description": "Username to assign",
                    "enum": ["user1", "user2", "user3"],
                },
                "is_urgent": {
                    "type": "boolean",
                    "description": "Whether the issue is urgent",
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata",
                },
            },
            "required": ["title"],
        },
        server_id="github-server",
    )


@pytest.fixture
def tool_with_number_params():
    """Create a tool with number parameters."""
    return MCPToolInfo(
        name="calculate",
        description="Perform calculation",
        input_schema={
            "type": "object",
            "properties": {
                "value": {
                    "type": "number",
                    "description": "A floating point value",
                },
                "count": {
                    "type": "integer",
                    "description": "An integer count",
                },
            },
            "required": ["value", "count"],
        },
        server_id="math-server",
    )


@pytest.fixture
def tool_without_description():
    """Create a tool without description."""
    return MCPToolInfo(
        name="unnamed_tool",
        description=None,
        input_schema={
            "type": "object",
            "properties": {
                "param": {
                    "type": "string",
                }
            },
        },
        server_id="test-server",
    )


# ============================================================================
# MCPToolAdapter Initialization Tests
# ============================================================================


class TestMCPToolAdapterInit:
    """Tests for MCPToolAdapter initialization."""

    def test_init_stores_client(self, mock_mcp_client, simple_tool_info):
        """Adapter should store the MCP client reference."""
        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        assert adapter._client is mock_mcp_client

    def test_init_stores_tool_info(self, mock_mcp_client, simple_tool_info):
        """Adapter should store the tool info."""
        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        assert adapter._tool_info is simple_tool_info

    def test_init_creates_definition(self, mock_mcp_client, simple_tool_info):
        """Adapter should create tool definition on init."""
        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        assert adapter._definition is not None
        assert isinstance(adapter._definition, ToolDefinition)


# ============================================================================
# Tool Definition Creation Tests
# ============================================================================


class TestToolDefinitionCreation:
    """Tests for creating ToolDefinition from MCP tool info."""

    def test_definition_has_prefixed_name(self, mock_mcp_client, simple_tool_info):
        """Tool name should be prefixed with server ID."""
        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        assert adapter.definition.name == "test-server:simple_tool"

    def test_definition_uses_description(self, mock_mcp_client, tool_with_string_param):
        """Tool definition should use the MCP tool description."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_string_param)
        assert adapter.definition.description == "Search for content"

    def test_definition_fallback_description(self, mock_mcp_client, tool_without_description):
        """Tool definition should use fallback description when none provided."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_without_description)
        assert "MCP tool: unnamed_tool" in adapter.definition.description

    def test_definition_with_no_parameters(self, mock_mcp_client, simple_tool_info):
        """Tool definition should handle empty input schema."""
        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        assert adapter.definition.parameters == []


# ============================================================================
# JSON Schema Parsing Tests
# ============================================================================


class TestJSONSchemaParsingSimple:
    """Tests for parsing simple JSON Schema properties."""

    def test_parse_string_parameter(self, mock_mcp_client, tool_with_string_param):
        """Should parse string parameters correctly."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_string_param)
        params = adapter.definition.parameters

        assert len(params) == 1
        param = params[0]
        assert param.name == "query"
        assert param.type == "string"
        assert param.description == "The search query"
        assert param.required is True

    def test_parse_integer_parameter(self, mock_mcp_client, tool_with_number_params):
        """Should map integer to number type."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_number_params)
        params = {p.name: p for p in adapter.definition.parameters}

        assert params["count"].type == "number"

    def test_parse_number_parameter(self, mock_mcp_client, tool_with_number_params):
        """Should parse number parameters correctly."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_number_params)
        params = {p.name: p for p in adapter.definition.parameters}

        assert params["value"].type == "number"


class TestJSONSchemaParsingComplex:
    """Tests for parsing complex JSON Schema properties."""

    def test_parse_multiple_parameters(self, mock_mcp_client, tool_with_multiple_params):
        """Should parse all parameters from complex schema."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_multiple_params)
        params = adapter.definition.parameters

        assert len(params) == 7
        param_names = {p.name for p in params}
        assert param_names == {
            "title",
            "body",
            "labels",
            "priority",
            "assignee",
            "is_urgent",
            "metadata",
        }

    def test_parse_required_parameters(self, mock_mcp_client, tool_with_multiple_params):
        """Should correctly identify required parameters."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_multiple_params)
        params = {p.name: p for p in adapter.definition.parameters}

        assert params["title"].required is True
        assert params["body"].required is False
        assert params["labels"].required is False

    def test_parse_array_parameter(self, mock_mcp_client, tool_with_multiple_params):
        """Should parse array parameters with items schema."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_multiple_params)
        params = {p.name: p for p in adapter.definition.parameters}

        assert params["labels"].type == "array"
        assert params["labels"].items == {"type": "string"}

    def test_parse_boolean_parameter(self, mock_mcp_client, tool_with_multiple_params):
        """Should parse boolean parameters correctly."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_multiple_params)
        params = {p.name: p for p in adapter.definition.parameters}

        assert params["is_urgent"].type == "boolean"

    def test_parse_object_parameter(self, mock_mcp_client, tool_with_multiple_params):
        """Should parse object parameters correctly."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_multiple_params)
        params = {p.name: p for p in adapter.definition.parameters}

        assert params["metadata"].type == "object"

    def test_parse_enum_values(self, mock_mcp_client, tool_with_multiple_params):
        """Should parse enum values correctly."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_multiple_params)
        params = {p.name: p for p in adapter.definition.parameters}

        assert params["assignee"].enum == ["user1", "user2", "user3"]

    def test_parse_default_values(self, mock_mcp_client, tool_with_multiple_params):
        """Should parse default values correctly."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_multiple_params)
        params = {p.name: p for p in adapter.definition.parameters}

        assert params["priority"].default == 1

    def test_parse_array_without_items(self, mock_mcp_client):
        """Should handle array without explicit items schema."""
        tool_info = MCPToolInfo(
            name="list_tool",
            description="Tool with array without items",
            input_schema={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "List of items",
                    }
                },
            },
            server_id="test-server",
        )
        adapter = MCPToolAdapter(mock_mcp_client, tool_info)
        params = {p.name: p for p in adapter.definition.parameters}

        # Should default to string items
        assert params["items"].type == "array"
        assert params["items"].items == {"type": "string"}


class TestJSONSchemaParsingEdgeCases:
    """Tests for edge cases in JSON Schema parsing."""

    def test_parse_unknown_type(self, mock_mcp_client):
        """Should map unknown types to string."""
        tool_info = MCPToolInfo(
            name="unknown_type_tool",
            description="Tool with unknown type",
            input_schema={
                "type": "object",
                "properties": {
                    "weird_param": {
                        "type": "custom_type",
                        "description": "Custom type parameter",
                    }
                },
            },
            server_id="test-server",
        )
        adapter = MCPToolAdapter(mock_mcp_client, tool_info)
        params = {p.name: p for p in adapter.definition.parameters}

        # Unknown types should default to string
        assert params["weird_param"].type == "string"

    def test_parse_missing_type(self, mock_mcp_client):
        """Should default to string when type is missing."""
        tool_info = MCPToolInfo(
            name="missing_type_tool",
            description="Tool with missing type",
            input_schema={
                "type": "object",
                "properties": {
                    "no_type_param": {
                        "description": "Parameter without type",
                    }
                },
            },
            server_id="test-server",
        )
        adapter = MCPToolAdapter(mock_mcp_client, tool_info)
        params = {p.name: p for p in adapter.definition.parameters}

        assert params["no_type_param"].type == "string"

    def test_parse_missing_description(self, mock_mcp_client):
        """Should provide fallback description when missing."""
        tool_info = MCPToolInfo(
            name="no_desc_tool",
            description="Tool with param without description",
            input_schema={
                "type": "object",
                "properties": {
                    "no_desc_param": {
                        "type": "string",
                    }
                },
            },
            server_id="test-server",
        )
        adapter = MCPToolAdapter(mock_mcp_client, tool_info)
        params = {p.name: p for p in adapter.definition.parameters}

        assert "Parameter: no_desc_param" in params["no_desc_param"].description

    def test_parse_empty_schema(self, mock_mcp_client):
        """Should handle empty input schema gracefully."""
        # MCPToolInfo.input_schema defaults to empty dict, cannot be None
        tool_info = MCPToolInfo(
            name="empty_schema_tool",
            description="Tool with empty schema",
            input_schema={},
            server_id="test-server",
        )
        adapter = MCPToolAdapter(mock_mcp_client, tool_info)

        assert adapter.definition.parameters == []

    def test_parse_empty_properties(self, mock_mcp_client):
        """Should handle empty properties object."""
        tool_info = MCPToolInfo(
            name="empty_props_tool",
            description="Tool with empty properties",
            input_schema={
                "type": "object",
                "properties": {},
            },
            server_id="test-server",
        )
        adapter = MCPToolAdapter(mock_mcp_client, tool_info)

        assert adapter.definition.parameters == []


# ============================================================================
# Property Accessor Tests
# ============================================================================


class TestMCPToolAdapterProperties:
    """Tests for MCPToolAdapter property accessors."""

    def test_definition_property(self, mock_mcp_client, simple_tool_info):
        """definition property should return ToolDefinition."""
        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)

        definition = adapter.definition
        assert isinstance(definition, ToolDefinition)
        assert definition is adapter._definition

    def test_mcp_tool_name_property(self, mock_mcp_client, simple_tool_info):
        """mcp_tool_name should return original tool name without prefix."""
        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)

        assert adapter.mcp_tool_name == "simple_tool"
        # Should NOT include server prefix
        assert ":" not in adapter.mcp_tool_name

    def test_server_id_property(self, mock_mcp_client, tool_with_string_param):
        """server_id should return the MCP server ID."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_string_param)

        assert adapter.server_id == "github-server"

    def test_name_property_from_base_class(self, mock_mcp_client, simple_tool_info):
        """name property (from BaseTool) should return prefixed name."""
        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)

        # BaseTool.name property uses definition.name
        assert adapter.name == "test-server:simple_tool"


# ============================================================================
# Tool Execution Tests
# ============================================================================


class TestMCPToolAdapterExecution:
    """Tests for tool execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_mcp_client, simple_tool_info):
        """Successful execution should return success ToolResult."""
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=True,
            content="Tool executed successfully",
            duration_ms=100.5,
        )

        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        result = await adapter.execute()

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.output == "Tool executed successfully"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_execute_with_parameters(self, mock_mcp_client, tool_with_string_param):
        """Should pass parameters to client.call_tool."""
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=True,
            content=["result1", "result2"],
            duration_ms=50.0,
        )

        adapter = MCPToolAdapter(mock_mcp_client, tool_with_string_param)
        result = await adapter.execute(query="test search")

        mock_mcp_client.call_tool.assert_called_once_with(
            "search", {"query": "test search"}
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_multiple_parameters(
        self, mock_mcp_client, tool_with_multiple_params
    ):
        """Should handle multiple parameters correctly."""
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=True,
            content={"issue_id": 123},
            duration_ms=200.0,
        )

        adapter = MCPToolAdapter(mock_mcp_client, tool_with_multiple_params)
        result = await adapter.execute(
            title="Bug report",
            body="Description of the bug",
            labels=["bug", "urgent"],
            priority=2,
        )

        mock_mcp_client.call_tool.assert_called_once()
        call_args = mock_mcp_client.call_tool.call_args
        assert call_args[0][0] == "create_issue"
        assert call_args[0][1]["title"] == "Bug report"
        assert call_args[0][1]["labels"] == ["bug", "urgent"]

    @pytest.mark.asyncio
    async def test_execute_failure(self, mock_mcp_client, simple_tool_info):
        """Failed execution should return failure ToolResult with error."""
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=False,
            content=None,
            error="Connection timeout",
            duration_ms=5000.0,
        )

        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        result = await adapter.execute()

        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.output is None
        assert result.error == "Connection timeout"

    @pytest.mark.asyncio
    async def test_execute_uses_mcp_tool_name(self, mock_mcp_client, tool_with_string_param):
        """Execute should use original MCP tool name, not prefixed name."""
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=True,
            content="OK",
            duration_ms=10.0,
        )

        adapter = MCPToolAdapter(mock_mcp_client, tool_with_string_param)
        await adapter.execute(query="test")

        # Should use "search", not "github-server:search"
        call_args = mock_mcp_client.call_tool.call_args
        assert call_args[0][0] == "search"

    @pytest.mark.asyncio
    async def test_execute_with_empty_kwargs(self, mock_mcp_client, simple_tool_info):
        """Should handle execution with no arguments."""
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=True,
            content="Done",
            duration_ms=5.0,
        )

        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        result = await adapter.execute()

        mock_mcp_client.call_tool.assert_called_once_with("simple_tool", {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_various_content_types(self, mock_mcp_client, simple_tool_info):
        """Should handle various content types in response."""
        # Test with dict content
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=True,
            content={"key": "value", "nested": {"inner": 123}},
            duration_ms=10.0,
        )
        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        result = await adapter.execute()
        assert result.output == {"key": "value", "nested": {"inner": 123}}

        # Test with list content
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=True,
            content=[1, 2, 3, "four"],
            duration_ms=10.0,
        )
        result = await adapter.execute()
        assert result.output == [1, 2, 3, "four"]

        # Test with None content
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=True,
            content=None,
            duration_ms=10.0,
        )
        result = await adapter.execute()
        assert result.output is None


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestMCPToolAdapterErrorHandling:
    """Tests for error handling in tool execution."""

    @pytest.mark.asyncio
    async def test_execute_returns_error_from_mcp(self, mock_mcp_client, simple_tool_info):
        """Should propagate error messages from MCP tool call result."""
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=False,
            error="Rate limit exceeded",
            duration_ms=0.0,
        )

        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        result = await adapter.execute()

        assert result.success is False
        assert result.error == "Rate limit exceeded"

    @pytest.mark.asyncio
    async def test_execute_with_authentication_error(
        self, mock_mcp_client, simple_tool_info
    ):
        """Should handle authentication errors from MCP server."""
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=False,
            error="Authentication failed: Invalid token",
            duration_ms=50.0,
        )

        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)
        result = await adapter.execute()

        assert result.success is False
        assert "Authentication failed" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_validation_error(
        self, mock_mcp_client, tool_with_string_param
    ):
        """Should handle validation errors from MCP server."""
        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=False,
            error="Validation error: query is required",
            duration_ms=10.0,
        )

        adapter = MCPToolAdapter(mock_mcp_client, tool_with_string_param)
        result = await adapter.execute()  # Missing required query

        assert result.success is False
        assert "Validation error" in result.error


# ============================================================================
# Integration-like Tests
# ============================================================================


class TestMCPToolAdapterIntegration:
    """Integration-like tests for MCPToolAdapter."""

    @pytest.mark.asyncio
    async def test_full_workflow_success(self, mock_mcp_client):
        """Test complete workflow: create adapter, check definition, execute."""
        tool_info = MCPToolInfo(
            name="get_user",
            description="Get user information",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The user's unique identifier",
                    }
                },
                "required": ["user_id"],
            },
            server_id="user-service",
        )

        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=True,
            content={"id": "usr_123", "name": "John Doe", "email": "john@example.com"},
            duration_ms=45.0,
        )

        adapter = MCPToolAdapter(mock_mcp_client, tool_info)

        # Verify definition
        assert adapter.name == "user-service:get_user"
        assert adapter.mcp_tool_name == "get_user"
        assert adapter.server_id == "user-service"
        assert len(adapter.definition.parameters) == 1
        assert adapter.definition.parameters[0].name == "user_id"
        assert adapter.definition.parameters[0].required is True

        # Execute
        result = await adapter.execute(user_id="usr_123")

        assert result.success is True
        assert result.output["id"] == "usr_123"
        assert result.output["name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_multiple_adapters_same_client(self, mock_mcp_client):
        """Multiple adapters can share the same client."""
        tool_info_1 = MCPToolInfo(
            name="tool_a",
            description="First tool",
            input_schema={},
            server_id="shared-server",
        )
        tool_info_2 = MCPToolInfo(
            name="tool_b",
            description="Second tool",
            input_schema={},
            server_id="shared-server",
        )

        mock_mcp_client.call_tool.return_value = MCPToolCallResult(
            success=True,
            content="OK",
            duration_ms=10.0,
        )

        adapter_1 = MCPToolAdapter(mock_mcp_client, tool_info_1)
        adapter_2 = MCPToolAdapter(mock_mcp_client, tool_info_2)

        await adapter_1.execute()
        await adapter_2.execute()

        assert mock_mcp_client.call_tool.call_count == 2
        calls = mock_mcp_client.call_tool.call_args_list
        assert calls[0][0][0] == "tool_a"
        assert calls[1][0][0] == "tool_b"

    def test_adapter_as_base_tool(self, mock_mcp_client, simple_tool_info):
        """Adapter should be usable as BaseTool in registry."""
        from src.tools.base import BaseTool

        adapter = MCPToolAdapter(mock_mcp_client, simple_tool_info)

        # Should be instance of BaseTool
        assert isinstance(adapter, BaseTool)

        # Should have required BaseTool interface
        assert hasattr(adapter, "definition")
        assert hasattr(adapter, "execute")
        assert hasattr(adapter, "name")

    def test_definition_to_openai_format(self, mock_mcp_client, tool_with_multiple_params):
        """Tool definition should be convertible to OpenAI format."""
        adapter = MCPToolAdapter(mock_mcp_client, tool_with_multiple_params)

        openai_format = adapter.definition.to_openai_format()

        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "github-server:create_issue"
        assert openai_format["function"]["description"] == "Create a new issue in the repository"
        assert "properties" in openai_format["function"]["parameters"]
        assert "title" in openai_format["function"]["parameters"]["properties"]
        assert "required" in openai_format["function"]["parameters"]
        assert "title" in openai_format["function"]["parameters"]["required"]
