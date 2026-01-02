"""MCP Manager - manages multiple MCP server connections."""

from typing import Dict, List, Optional

from src.config.logging import get_logger
from src.tools.registry import get_registry

from .adapter import MCPToolAdapter
from .client import MCPClient
from .models import MCPServerConfig, MCPServerInstance, MCPToolInfo, ServerStatus

logger = get_logger(__name__)


class MCPManager:
    """Manages MCP server connections and tool registration.

    Responsibilities:
    - Connect to MCP servers via Streamable HTTP
    - Discover and register tools with global ToolRegistry
    - Track server status and health
    - Handle reconnection on failures
    """

    def __init__(self):
        """Initialize MCP manager."""
        self._clients: Dict[str, MCPClient] = {}
        self._servers: Dict[str, MCPServerInstance] = {}

    @property
    def server_count(self) -> int:
        """Get number of connected servers."""
        return len(self._clients)

    @property
    def connected_servers(self) -> List[str]:
        """Get list of connected server IDs."""
        return [
            server_id
            for server_id, client in self._clients.items()
            if client.is_connected
        ]

    async def add_server(
        self,
        config: MCPServerConfig,
        register_tools: bool = True,
    ) -> MCPServerInstance:
        """Connect to an MCP server and optionally register its tools.

        Args:
            config: Server configuration
            register_tools: Whether to register tools with global registry

        Returns:
            MCPServerInstance with connection status
        """
        server_id = config.id

        # Create server instance
        instance = MCPServerInstance(
            id=server_id,
            name=config.name,
            template=config.template,
            url=config.url,
            status=ServerStatus.DISCONNECTED,
            secret_ref="",  # Will be set by repository
        )

        try:
            # Create and connect client
            client = MCPClient(config)
            await client.connect()

            self._clients[server_id] = client
            instance.status = ServerStatus.ACTIVE

            # Get tools once and cache
            tools = await client.list_tools()

            # Register tools with global registry
            if register_tools:
                registry = get_registry()

                for tool_info in tools:
                    adapter = MCPToolAdapter(client, tool_info)
                    registry.register(adapter)
                    logger.info(
                        "mcp_tool_registered",
                        tool=adapter.name,
                        server=config.name,
                    )

            logger.info(
                "mcp_server_added",
                server_id=server_id,
                name=config.name,
                tools_count=len(tools),
            )

        except Exception as e:
            instance.status = ServerStatus.ERROR
            instance.error_message = str(e)
            logger.error(
                "mcp_server_add_failed",
                server_id=server_id,
                error=str(e),
            )

        self._servers[server_id] = instance
        return instance

    async def remove_server(self, server_id: str) -> bool:
        """Disconnect and remove an MCP server.

        Args:
            server_id: Server ID to remove

        Returns:
            True if server was removed, False if not found
        """
        if server_id not in self._clients:
            return False

        client = self._clients[server_id]

        # Unregister tools from global registry
        registry = get_registry()
        tools = await client.list_tools()
        for tool_info in tools:
            tool_name = f"{server_id}:{tool_info.name}"
            registry.unregister(tool_name)

        # Disconnect client
        await client.disconnect()

        del self._clients[server_id]
        if server_id in self._servers:
            del self._servers[server_id]

        logger.info("mcp_server_removed", server_id=server_id)
        return True

    async def get_server(self, server_id: str) -> Optional[MCPServerInstance]:
        """Get server instance by ID."""
        return self._servers.get(server_id)

    async def list_servers(self) -> List[MCPServerInstance]:
        """List all MCP servers."""
        return list(self._servers.values())

    async def get_tools(self, server_id: Optional[str] = None) -> List[MCPToolInfo]:
        """Get tools from specified server or all servers.

        Args:
            server_id: Optional server ID to filter by

        Returns:
            List of tool info
        """
        tools = []

        clients = (
            [self._clients[server_id]]
            if server_id and server_id in self._clients
            else self._clients.values()
        )

        for client in clients:
            if client.is_connected:
                tools.extend(await client.list_tools())

        return tools

    async def health_check(self) -> Dict[str, ServerStatus]:
        """Check health of all connected servers.

        Returns:
            Dict of server_id -> status
        """
        status = {}

        for server_id, instance in self._servers.items():
            client = self._clients.get(server_id)

            if client and client.is_connected:
                status[server_id] = ServerStatus.ACTIVE
            elif instance.status == ServerStatus.ERROR:
                status[server_id] = ServerStatus.ERROR
            else:
                status[server_id] = ServerStatus.DISCONNECTED

        return status

    async def shutdown(self) -> None:
        """Disconnect all servers and cleanup."""
        logger.info("mcp_manager_shutting_down", server_count=len(self._clients))

        for server_id in list(self._clients.keys()):
            await self.remove_server(server_id)

        self._clients.clear()
        self._servers.clear()

        logger.info("mcp_manager_shutdown_complete")


# Global manager instance
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """Get the global MCP manager singleton."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager


async def shutdown_mcp_manager() -> None:
    """Shutdown the global MCP manager."""
    global _mcp_manager
    if _mcp_manager:
        await _mcp_manager.shutdown()
        _mcp_manager = None


async def reconnect_mcp_servers() -> int:
    """Reconnect all MCP servers from database on startup.

    Returns:
        Number of servers successfully reconnected
    """
    from src.mcp.repository import MCPServerRepository
    from src.storage import get_async_session

    manager = get_mcp_manager()
    connected = 0

    async with get_async_session() as session:
        repository = MCPServerRepository(session)
        servers = await repository.list_all()

        for server in servers:
            try:
                config = await repository.get_config(server.id)
                if config:
                    await manager.add_server(config)
                    await repository.update_status(server.id, ServerStatus.ACTIVE)
                    connected += 1
                    logger.info(
                        "mcp_server_reconnected",
                        server_id=server.id,
                        name=server.name,
                    )
            except Exception as e:
                await repository.update_status(
                    server.id, ServerStatus.ERROR, str(e)
                )
                logger.error(
                    "mcp_server_reconnect_failed",
                    server_id=server.id,
                    error=str(e),
                )

    logger.info("mcp_servers_reconnected", total=connected)
    return connected
