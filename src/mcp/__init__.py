"""MCP (Model Context Protocol) integration module."""

from .adapter import MCPToolAdapter
from .client import MCPClient
from .manager import MCPManager, get_mcp_manager, reconnect_mcp_servers, shutdown_mcp_manager
from .models import (
    MCPServerConfig,
    MCPServerInstance,
    MCPServerTemplate,
    MCPToolCallResult,
    MCPToolInfo,
    ServerStatus,
)

__all__ = [
    # Client
    "MCPClient",
    # Adapter
    "MCPToolAdapter",
    # Manager
    "MCPManager",
    "get_mcp_manager",
    "shutdown_mcp_manager",
    "reconnect_mcp_servers",
    # Models
    "MCPServerConfig",
    "MCPServerInstance",
    "MCPServerTemplate",
    "MCPToolInfo",
    "MCPToolCallResult",
    "ServerStatus",
]
