"""MCP client using Streamable HTTP transport."""

import json
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx

from src.config.logging import get_logger

from .models import MCPServerConfig, MCPToolCallResult, MCPToolInfo

logger = get_logger(__name__)


class MCPClient:
    """MCP client using Streamable HTTP transport (MCP 2025-06-18).

    Connects to remote MCP servers via HTTPS. No local subprocesses needed.
    """

    MCP_PROTOCOL_VERSION = "2025-06-18"

    def __init__(self, config: MCPServerConfig):
        """Initialize MCP client.

        Args:
            config: Server configuration with URL and headers
        """
        self.config = config
        self._session_id: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._tools: List[MCPToolInfo] = []
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected

    @property
    def server_id(self) -> str:
        """Get server ID."""
        return self.config.id

    async def connect(self) -> None:
        """Connect to MCP server and initialize session."""
        logger.info(
            "mcp_server_connecting",
            server=self.config.name,
            url=self.config.url,
        )

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

        try:
            # Send initialize request
            response = await self._send_request(
                "initialize",
                {
                    "protocolVersion": self.MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {
                        "name": "magure-ai-platform",
                        "version": "0.1.0",
                    },
                },
            )

            # Extract session ID if provided
            self._session_id = response.get("sessionId")

            # Send initialized notification
            await self._send_notification("notifications/initialized", {})

            # Discover tools
            await self._discover_tools()

            self._connected = True
            logger.info(
                "mcp_server_connected",
                server=self.config.name,
                tools_count=len(self._tools),
            )

        except Exception as e:
            logger.error(
                "mcp_server_connection_failed",
                server=self.config.name,
                error=str(e),
            )
            await self.disconnect()
            raise

    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        self._session_id = None
        self._tools = []
        logger.info("mcp_server_disconnected", server=self.config.name)

    async def _discover_tools(self) -> None:
        """Discover available tools from MCP server."""
        response = await self._send_request("tools/list", {})
        tools_data = response.get("tools", [])

        self._tools = [
            MCPToolInfo(
                name=tool["name"],
                description=tool.get("description"),
                input_schema=tool.get("inputSchema", {}),
                server_id=self.config.id,
            )
            for tool in tools_data
        ]

    async def list_tools(self) -> List[MCPToolInfo]:
        """Get list of available tools."""
        return self._tools

    async def call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> MCPToolCallResult:
        """Call an MCP tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool call result
        """
        start_time = time.time()

        logger.info(
            "mcp_tool_call_started",
            server=self.config.name,
            tool=name,
        )

        try:
            response = await self._send_request(
                "tools/call",
                {
                    "name": name,
                    "arguments": arguments,
                },
            )

            duration_ms = (time.time() - start_time) * 1000

            # Extract content from response
            content = response.get("content", [])
            if content and isinstance(content, list):
                # MCP returns content as array of content blocks
                text_content = [
                    c.get("text", "") for c in content if c.get("type") == "text"
                ]
                result_content = "\n".join(text_content) if text_content else content
            else:
                result_content = content

            logger.info(
                "mcp_tool_call_completed",
                server=self.config.name,
                tool=name,
                duration_ms=duration_ms,
            )

            return MCPToolCallResult(
                success=True,
                content=result_content,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "mcp_tool_call_failed",
                server=self.config.name,
                tool=name,
                error=str(e),
                duration_ms=duration_ms,
            )
            return MCPToolCallResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

    async def _send_request(
        self, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP server.

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            Response result
        """
        if not self._client:
            raise RuntimeError("Client not connected")

        request_id = str(uuid.uuid4())

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": self.MCP_PROTOCOL_VERSION,
            **self.config.headers,
        }

        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        response = await self._client.post(
            self.config.url,
            json=payload,
            headers=headers,
        )

        response.raise_for_status()

        # Handle SSE response
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            return await self._parse_sse_response(response)

        # Handle JSON response
        result = response.json()

        if "error" in result:
            error = result["error"]
            raise RuntimeError(f"MCP error: {error.get('message', error)}")

        return result.get("result", {})

    async def _send_notification(
        self, method: str, params: Dict[str, Any]
    ) -> None:
        """Send JSON-RPC notification (no response expected)."""
        if not self._client:
            raise RuntimeError("Client not connected")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "MCP-Protocol-Version": self.MCP_PROTOCOL_VERSION,
            **self.config.headers,
        }

        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        response = await self._client.post(
            self.config.url,
            json=payload,
            headers=headers,
        )

        # Notifications should return 202 Accepted
        if response.status_code not in (200, 202):
            response.raise_for_status()

    async def _parse_sse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse SSE response from MCP server."""
        result = {}

        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                if "result" in data:
                    result = data["result"]
                    break
                if "error" in data:
                    error = data["error"]
                    raise RuntimeError(f"MCP error: {error.get('message', error)}")

        return result
