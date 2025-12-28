"""Unit tests for MCP Manager.

Tests cover:
- MCPManager class initialization and properties
- Server connection management (add, remove, list)
- Tool discovery and registration
- Error handling for connection failures
- Health check functionality
- Shutdown and cleanup
- Global singleton functions
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from src.mcp.manager import (
    MCPManager,
    get_mcp_manager,
    shutdown_mcp_manager,
    reconnect_mcp_servers,
)
from src.mcp.models import (
    MCPServerConfig,
    MCPServerInstance,
    MCPToolInfo,
    ServerStatus,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mcp_manager():
    """Create a fresh MCPManager instance for each test."""
    return MCPManager()


@pytest.fixture
def sample_server_config():
    """Create a sample MCP server configuration."""
    return MCPServerConfig(
        id="test-server-1",
        name="Test MCP Server",
        url="https://mcp.example.com/api",
        headers={"Authorization": "Bearer test-token"},
        template="github",
    )


@pytest.fixture
def sample_server_config_2():
    """Create a second sample MCP server configuration."""
    return MCPServerConfig(
        id="test-server-2",
        name="Second Test Server",
        url="https://mcp2.example.com/api",
        headers={"X-API-Key": "api-key-123"},
        template="slack",
    )


@pytest.fixture
def sample_tool_info():
    """Create a sample MCP tool info."""
    return MCPToolInfo(
        name="search_files",
        description="Search for files in the repository",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Maximum results"},
            },
            "required": ["query"],
        },
        server_id="test-server-1",
    )


@pytest.fixture
def sample_tool_info_2():
    """Create a second sample MCP tool info."""
    return MCPToolInfo(
        name="create_issue",
        description="Create a new issue",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body"},
            },
            "required": ["title"],
        },
        server_id="test-server-1",
    )


@pytest.fixture
def mock_mcp_client(sample_tool_info, sample_tool_info_2):
    """Create a mock MCP client."""
    mock_client = AsyncMock()
    mock_client.is_connected = True
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.list_tools = AsyncMock(return_value=[sample_tool_info, sample_tool_info_2])
    return mock_client


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry."""
    mock_registry = MagicMock()
    mock_registry.register = MagicMock()
    mock_registry.unregister = MagicMock(return_value=True)
    return mock_registry


# ============================================================================
# MCPManager Initialization Tests
# ============================================================================


class TestMCPManagerInit:
    """Tests for MCPManager initialization."""

    def test_init_creates_empty_clients_dict(self, mcp_manager):
        """MCPManager should initialize with empty clients dict."""
        assert mcp_manager._clients == {}

    def test_init_creates_empty_servers_dict(self, mcp_manager):
        """MCPManager should initialize with empty servers dict."""
        assert mcp_manager._servers == {}

    def test_server_count_initially_zero(self, mcp_manager):
        """Server count should be 0 on initialization."""
        assert mcp_manager.server_count == 0

    def test_connected_servers_initially_empty(self, mcp_manager):
        """Connected servers list should be empty on initialization."""
        assert mcp_manager.connected_servers == []


# ============================================================================
# MCPManager.add_server Tests
# ============================================================================


class TestMCPManagerAddServer:
    """Tests for adding MCP servers."""

    @pytest.mark.asyncio
    async def test_add_server_success(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Successfully adding a server should register tools and update status."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                instance = await mcp_manager.add_server(sample_server_config)

        assert instance.id == sample_server_config.id
        assert instance.name == sample_server_config.name
        assert instance.status == ServerStatus.ACTIVE
        assert instance.error_message is None
        assert mcp_manager.server_count == 1

    @pytest.mark.asyncio
    async def test_add_server_stores_client(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Adding a server should store the client reference."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)

        assert sample_server_config.id in mcp_manager._clients
        assert mcp_manager._clients[sample_server_config.id] == mock_mcp_client

    @pytest.mark.asyncio
    async def test_add_server_registers_tools(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Adding a server should register all discovered tools."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)

        # Should register 2 tools (from our mock)
        assert mock_tool_registry.register.call_count == 2

    @pytest.mark.asyncio
    async def test_add_server_without_tool_registration(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Adding a server with register_tools=False should not register tools."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                instance = await mcp_manager.add_server(
                    sample_server_config, register_tools=False
                )

        assert instance.status == ServerStatus.ACTIVE
        assert mock_tool_registry.register.call_count == 0

    @pytest.mark.asyncio
    async def test_add_server_connection_failure(
        self,
        mcp_manager,
        sample_server_config,
    ):
        """Failed connection should set ERROR status and error message."""
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(side_effect=ConnectionError("Connection refused"))

        with patch("src.mcp.manager.MCPClient", return_value=mock_client):
            instance = await mcp_manager.add_server(sample_server_config)

        assert instance.status == ServerStatus.ERROR
        assert "Connection refused" in instance.error_message
        # Client should not be stored on failure
        assert sample_server_config.id not in mcp_manager._clients

    @pytest.mark.asyncio
    async def test_add_server_timeout_error(
        self,
        mcp_manager,
        sample_server_config,
    ):
        """Timeout during connection should set ERROR status."""
        import asyncio

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch("src.mcp.manager.MCPClient", return_value=mock_client):
            instance = await mcp_manager.add_server(sample_server_config)

        assert instance.status == ServerStatus.ERROR
        assert instance.error_message is not None

    @pytest.mark.asyncio
    async def test_add_multiple_servers(
        self,
        mcp_manager,
        sample_server_config,
        sample_server_config_2,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Should be able to add multiple servers."""
        mock_client_2 = AsyncMock()
        mock_client_2.is_connected = True
        mock_client_2.connect = AsyncMock()
        mock_client_2.list_tools = AsyncMock(return_value=[])

        with patch("src.mcp.manager.MCPClient") as MockClient:
            MockClient.side_effect = [mock_mcp_client, mock_client_2]
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                await mcp_manager.add_server(sample_server_config_2)

        assert mcp_manager.server_count == 2
        assert sample_server_config.id in mcp_manager._clients
        assert sample_server_config_2.id in mcp_manager._clients


# ============================================================================
# MCPManager.remove_server Tests
# ============================================================================


class TestMCPManagerRemoveServer:
    """Tests for removing MCP servers."""

    @pytest.mark.asyncio
    async def test_remove_server_success(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Successfully removing a server should disconnect and unregister tools."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                result = await mcp_manager.remove_server(sample_server_config.id)

        assert result is True
        assert sample_server_config.id not in mcp_manager._clients
        assert sample_server_config.id not in mcp_manager._servers
        mock_mcp_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_server_unregisters_tools(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Removing a server should unregister all its tools."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                await mcp_manager.remove_server(sample_server_config.id)

        # Should unregister 2 tools (from our mock)
        assert mock_tool_registry.unregister.call_count == 2

    @pytest.mark.asyncio
    async def test_remove_nonexistent_server(self, mcp_manager):
        """Removing a non-existent server should return False."""
        result = await mcp_manager.remove_server("nonexistent-server")
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_server_updates_count(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Server count should decrease after removal."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                assert mcp_manager.server_count == 1

                await mcp_manager.remove_server(sample_server_config.id)
                assert mcp_manager.server_count == 0


# ============================================================================
# MCPManager.get_server Tests
# ============================================================================


class TestMCPManagerGetServer:
    """Tests for getting server instances."""

    @pytest.mark.asyncio
    async def test_get_server_exists(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Should return server instance when it exists."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                instance = await mcp_manager.get_server(sample_server_config.id)

        assert instance is not None
        assert instance.id == sample_server_config.id

    @pytest.mark.asyncio
    async def test_get_server_not_found(self, mcp_manager):
        """Should return None for non-existent server."""
        instance = await mcp_manager.get_server("nonexistent")
        assert instance is None


# ============================================================================
# MCPManager.list_servers Tests
# ============================================================================


class TestMCPManagerListServers:
    """Tests for listing servers."""

    @pytest.mark.asyncio
    async def test_list_servers_empty(self, mcp_manager):
        """Should return empty list when no servers are added."""
        servers = await mcp_manager.list_servers()
        assert servers == []

    @pytest.mark.asyncio
    async def test_list_servers_with_servers(
        self,
        mcp_manager,
        sample_server_config,
        sample_server_config_2,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Should return all added servers."""
        mock_client_2 = AsyncMock()
        mock_client_2.is_connected = True
        mock_client_2.connect = AsyncMock()
        mock_client_2.list_tools = AsyncMock(return_value=[])

        with patch("src.mcp.manager.MCPClient") as MockClient:
            MockClient.side_effect = [mock_mcp_client, mock_client_2]
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                await mcp_manager.add_server(sample_server_config_2)
                servers = await mcp_manager.list_servers()

        assert len(servers) == 2
        server_ids = {s.id for s in servers}
        assert sample_server_config.id in server_ids
        assert sample_server_config_2.id in server_ids


# ============================================================================
# MCPManager.get_tools Tests
# ============================================================================


class TestMCPManagerGetTools:
    """Tests for getting tools."""

    @pytest.mark.asyncio
    async def test_get_all_tools(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
        sample_tool_info,
        sample_tool_info_2,
    ):
        """Should return tools from all connected servers."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                tools = await mcp_manager.get_tools()

        assert len(tools) == 2
        tool_names = {t.name for t in tools}
        assert "search_files" in tool_names
        assert "create_issue" in tool_names

    @pytest.mark.asyncio
    async def test_get_tools_by_server_id(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Should return tools only from specified server."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                tools = await mcp_manager.get_tools(server_id=sample_server_config.id)

        assert len(tools) == 2

    @pytest.mark.asyncio
    async def test_get_tools_nonexistent_server(self, mcp_manager):
        """Should return empty list for non-existent server."""
        tools = await mcp_manager.get_tools(server_id="nonexistent")
        assert tools == []

    @pytest.mark.asyncio
    async def test_get_tools_disconnected_server(
        self,
        mcp_manager,
        sample_server_config,
        mock_tool_registry,
    ):
        """Should not return tools from disconnected servers."""
        mock_client = AsyncMock()
        mock_client.is_connected = False
        mock_client.connect = AsyncMock()
        mock_client.list_tools = AsyncMock(return_value=[])

        # Manually set up the client as disconnected
        with patch("src.mcp.manager.MCPClient", return_value=mock_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                # Simulate disconnection
                mock_client.is_connected = False
                tools = await mcp_manager.get_tools()

        assert tools == []


# ============================================================================
# MCPManager.health_check Tests
# ============================================================================


class TestMCPManagerHealthCheck:
    """Tests for health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_active_server(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Should report ACTIVE for connected server."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                status = await mcp_manager.health_check()

        assert status[sample_server_config.id] == ServerStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_health_check_disconnected_server(
        self,
        mcp_manager,
        sample_server_config,
        mock_tool_registry,
    ):
        """Should report DISCONNECTED for disconnected server."""
        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.connect = AsyncMock()
        mock_client.list_tools = AsyncMock(return_value=[])

        with patch("src.mcp.manager.MCPClient", return_value=mock_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                # Simulate disconnection
                mock_client.is_connected = False
                status = await mcp_manager.health_check()

        assert status[sample_server_config.id] == ServerStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_health_check_error_server(
        self,
        mcp_manager,
        sample_server_config,
    ):
        """Should report ERROR for servers with connection errors."""
        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(side_effect=ConnectionError("Failed"))

        with patch("src.mcp.manager.MCPClient", return_value=mock_client):
            await mcp_manager.add_server(sample_server_config)
            status = await mcp_manager.health_check()

        assert status[sample_server_config.id] == ServerStatus.ERROR

    @pytest.mark.asyncio
    async def test_health_check_empty(self, mcp_manager):
        """Should return empty dict when no servers."""
        status = await mcp_manager.health_check()
        assert status == {}


# ============================================================================
# MCPManager.shutdown Tests
# ============================================================================


class TestMCPManagerShutdown:
    """Tests for manager shutdown."""

    @pytest.mark.asyncio
    async def test_shutdown_removes_all_servers(
        self,
        mcp_manager,
        sample_server_config,
        sample_server_config_2,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Shutdown should remove all servers."""
        mock_client_2 = AsyncMock()
        mock_client_2.is_connected = True
        mock_client_2.connect = AsyncMock()
        mock_client_2.disconnect = AsyncMock()
        mock_client_2.list_tools = AsyncMock(return_value=[])

        with patch("src.mcp.manager.MCPClient") as MockClient:
            MockClient.side_effect = [mock_mcp_client, mock_client_2]
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                await mcp_manager.add_server(sample_server_config_2)
                await mcp_manager.shutdown()

        assert mcp_manager.server_count == 0
        assert mcp_manager._clients == {}
        assert mcp_manager._servers == {}

    @pytest.mark.asyncio
    async def test_shutdown_disconnects_all_clients(
        self,
        mcp_manager,
        sample_server_config,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """Shutdown should disconnect all clients."""
        with patch("src.mcp.manager.MCPClient", return_value=mock_mcp_client):
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                await mcp_manager.shutdown()

        mock_mcp_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_empty_manager(self, mcp_manager):
        """Shutdown should handle empty manager gracefully."""
        # Should not raise any errors
        await mcp_manager.shutdown()
        assert mcp_manager.server_count == 0


# ============================================================================
# MCPManager Properties Tests
# ============================================================================


class TestMCPManagerProperties:
    """Tests for MCPManager properties."""

    @pytest.mark.asyncio
    async def test_connected_servers_property(
        self,
        mcp_manager,
        sample_server_config,
        sample_server_config_2,
        mock_mcp_client,
        mock_tool_registry,
    ):
        """connected_servers should only list servers with connected clients."""
        mock_client_2 = AsyncMock()
        mock_client_2.is_connected = False  # This one is not connected
        mock_client_2.connect = AsyncMock()
        mock_client_2.list_tools = AsyncMock(return_value=[])

        with patch("src.mcp.manager.MCPClient") as MockClient:
            MockClient.side_effect = [mock_mcp_client, mock_client_2]
            with patch("src.mcp.manager.get_registry", return_value=mock_tool_registry):
                await mcp_manager.add_server(sample_server_config)
                await mcp_manager.add_server(sample_server_config_2)

        connected = mcp_manager.connected_servers
        assert len(connected) == 1
        assert sample_server_config.id in connected


# ============================================================================
# Global Singleton Functions Tests
# ============================================================================


class TestGlobalMCPManager:
    """Tests for global MCP manager singleton functions."""

    @pytest.mark.asyncio
    async def test_get_mcp_manager_creates_singleton(self):
        """get_mcp_manager should create singleton on first call."""
        # Reset global state
        import src.mcp.manager as manager_module

        manager_module._mcp_manager = None

        manager = get_mcp_manager()
        assert manager is not None
        assert isinstance(manager, MCPManager)

        # Calling again should return same instance
        manager2 = get_mcp_manager()
        assert manager is manager2

        # Cleanup
        manager_module._mcp_manager = None

    @pytest.mark.asyncio
    async def test_shutdown_mcp_manager(self):
        """shutdown_mcp_manager should shutdown and clear singleton."""
        import src.mcp.manager as manager_module

        # Setup
        manager_module._mcp_manager = None
        manager = get_mcp_manager()

        # Add a mock client
        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.disconnect = AsyncMock()
        mock_client.list_tools = AsyncMock(return_value=[])
        manager._clients["test"] = mock_client

        with patch("src.mcp.manager.get_registry") as mock_registry:
            mock_registry.return_value = MagicMock()
            await shutdown_mcp_manager()

        assert manager_module._mcp_manager is None

    @pytest.mark.asyncio
    async def test_shutdown_mcp_manager_no_instance(self):
        """shutdown_mcp_manager should handle None instance gracefully."""
        import src.mcp.manager as manager_module

        manager_module._mcp_manager = None
        # Should not raise any errors
        await shutdown_mcp_manager()


# ============================================================================
# reconnect_mcp_servers Tests
# ============================================================================


class TestReconnectMCPServers:
    """Tests for reconnecting MCP servers on startup."""

    @pytest.fixture
    def mock_async_session_context(self):
        """Create a mock async context manager for get_async_session."""
        mock_session = AsyncMock()

        class MockContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        return MockContextManager(), mock_session

    @pytest.mark.asyncio
    async def test_reconnect_mcp_servers_success(
        self, sample_server_config, mock_async_session_context
    ):
        """Should reconnect all servers from database."""
        import src.mcp.manager as manager_module

        manager_module._mcp_manager = None

        mock_context, mock_session = mock_async_session_context
        mock_repository = AsyncMock()
        mock_server = MagicMock()
        mock_server.id = "test-server"
        mock_server.name = "Test Server"
        mock_repository.list_all = AsyncMock(return_value=[mock_server])
        mock_repository.get_config = AsyncMock(return_value=sample_server_config)
        mock_repository.update_status = AsyncMock()

        mock_manager = AsyncMock()
        mock_manager.add_server = AsyncMock()

        with patch("src.storage.get_async_session", return_value=mock_context):
            with patch("src.mcp.repository.MCPServerRepository", return_value=mock_repository):
                with patch("src.mcp.manager.get_mcp_manager", return_value=mock_manager):
                    count = await reconnect_mcp_servers()

        assert count == 1
        mock_manager.add_server.assert_called_once_with(sample_server_config)
        mock_repository.update_status.assert_called_with("test-server", ServerStatus.ACTIVE)

        # Cleanup
        manager_module._mcp_manager = None

    @pytest.mark.asyncio
    async def test_reconnect_mcp_servers_with_failures(
        self, sample_server_config, mock_async_session_context
    ):
        """Should handle server reconnection failures gracefully."""
        import src.mcp.manager as manager_module

        manager_module._mcp_manager = None

        mock_context, mock_session = mock_async_session_context
        mock_repository = AsyncMock()
        mock_server = MagicMock()
        mock_server.id = "test-server"
        mock_server.name = "Test Server"
        mock_repository.list_all = AsyncMock(return_value=[mock_server])
        mock_repository.get_config = AsyncMock(return_value=sample_server_config)
        mock_repository.update_status = AsyncMock()

        mock_manager = AsyncMock()
        mock_manager.add_server = AsyncMock(side_effect=ConnectionError("Failed"))

        with patch("src.storage.get_async_session", return_value=mock_context):
            with patch("src.mcp.repository.MCPServerRepository", return_value=mock_repository):
                with patch("src.mcp.manager.get_mcp_manager", return_value=mock_manager):
                    count = await reconnect_mcp_servers()

        assert count == 0
        mock_repository.update_status.assert_called()
        # Should be called with ERROR status
        call_args = mock_repository.update_status.call_args
        assert call_args[0][1] == ServerStatus.ERROR

        # Cleanup
        manager_module._mcp_manager = None

    @pytest.mark.asyncio
    async def test_reconnect_mcp_servers_no_servers(self, mock_async_session_context):
        """Should handle empty server list."""
        import src.mcp.manager as manager_module

        manager_module._mcp_manager = None

        mock_context, mock_session = mock_async_session_context
        mock_repository = AsyncMock()
        mock_repository.list_all = AsyncMock(return_value=[])

        mock_manager = MCPManager()

        with patch("src.storage.get_async_session", return_value=mock_context):
            with patch("src.mcp.repository.MCPServerRepository", return_value=mock_repository):
                with patch("src.mcp.manager.get_mcp_manager", return_value=mock_manager):
                    count = await reconnect_mcp_servers()

        assert count == 0

        # Cleanup
        manager_module._mcp_manager = None

    @pytest.mark.asyncio
    async def test_reconnect_mcp_servers_no_config(self, mock_async_session_context):
        """Should skip servers with no config."""
        import src.mcp.manager as manager_module

        manager_module._mcp_manager = None

        mock_context, mock_session = mock_async_session_context
        mock_repository = AsyncMock()
        mock_server = MagicMock()
        mock_server.id = "test-server"
        mock_server.name = "Test Server"
        mock_repository.list_all = AsyncMock(return_value=[mock_server])
        mock_repository.get_config = AsyncMock(return_value=None)  # No config

        mock_manager = MCPManager()

        with patch("src.storage.get_async_session", return_value=mock_context):
            with patch("src.mcp.repository.MCPServerRepository", return_value=mock_repository):
                with patch("src.mcp.manager.get_mcp_manager", return_value=mock_manager):
                    count = await reconnect_mcp_servers()

        assert count == 0

        # Cleanup
        manager_module._mcp_manager = None
