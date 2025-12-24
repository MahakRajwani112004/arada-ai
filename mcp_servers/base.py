"""Base MCP Server - handles protocol, logging, and provides tool decorator.

All MCP servers should extend BaseMCPServer and use @tool decorator to define tools.
"""
import functools
import json
import logging
import time
import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type

from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable
    credential_headers: List[str] = field(default_factory=list)


def tool(
    name: str,
    description: str,
    input_schema: Optional[Dict[str, Any]] = None,
    credential_headers: Optional[List[str]] = None,
):
    """Decorator to register a method as an MCP tool.

    Args:
        name: Tool name (e.g., "list_events")
        description: Human-readable description
        input_schema: JSON Schema for input parameters
        credential_headers: List of header names to extract as credentials

    Example:
        @tool(
            name="list_events",
            description="List calendar events",
            input_schema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date (YYYY-MM-DD)"}
                }
            },
            credential_headers=["X-Google-Refresh-Token"]
        )
        async def list_events(self, date: str, credentials: dict) -> dict:
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        # Attach metadata to function
        wrapper._mcp_tool = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema or {"type": "object", "properties": {}},
            handler=wrapper,
            credential_headers=credential_headers or [],
        )
        return wrapper

    return decorator


class BaseMCPServer(ABC):
    """Base class for MCP servers.

    Handles:
    - MCP protocol (initialize, tools/list, tools/call)
    - FastAPI app setup
    - Structured logging
    - Health checks
    - Error handling
    - Credential extraction from headers

    Subclasses just define tools using @tool decorator.
    """

    MCP_PROTOCOL_VERSION = "2025-06-18"

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
    ):
        """Initialize MCP server.

        Args:
            name: Server name (e.g., "google-calendar")
            version: Server version
            description: Human-readable description
        """
        self.name = name
        self.version = version
        self.description = description
        self.logger = logging.getLogger(f"mcp.{name}")

        # Discover tools from decorated methods
        self._tools: Dict[str, ToolDefinition] = {}
        self._discover_tools()

        # Create FastAPI app
        self.app = self._create_app()

        self.logger.info(
            f"Initialized MCP server: {name} v{version} with {len(self._tools)} tools"
        )

    def _discover_tools(self) -> None:
        """Discover tools from @tool decorated methods."""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "_mcp_tool"):
                tool_def: ToolDefinition = attr._mcp_tool
                # Update handler to bound method
                tool_def.handler = attr
                self._tools[tool_def.name] = tool_def
                self.logger.debug(f"Registered tool: {tool_def.name}")

    def _create_app(self) -> FastAPI:
        """Create FastAPI app with MCP endpoints."""
        app = FastAPI(
            title=f"MCP Server: {self.name}",
            description=self.description,
            version=self.version,
        )

        @app.post("/mcp")
        async def mcp_endpoint(
            request: Request,
            mcp_protocol_version: Optional[str] = Header(
                None, alias="MCP-Protocol-Version"
            ),
        ):
            return await self._handle_mcp_request(request)

        @app.get("/mcp")
        async def mcp_sse():
            """SSE endpoint (not implemented - for server-initiated messages)."""
            return JSONResponse(
                {"message": "SSE not implemented"},
                status_code=501,
            )

        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "server": self.name,
                "version": self.version,
                "tools": list(self._tools.keys()),
            }

        @app.get("/")
        async def root():
            return {
                "name": self.name,
                "version": self.version,
                "protocol": self.MCP_PROTOCOL_VERSION,
                "tools": list(self._tools.keys()),
            }

        return app

    async def _handle_mcp_request(self, request: Request) -> JSONResponse:
        """Handle incoming MCP JSON-RPC request."""
        start_time = time.time()
        body = await request.json()

        jsonrpc = body.get("jsonrpc", "2.0")
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        self.logger.info(f"MCP request: {method} (id={request_id})")

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "notifications/initialized":
                # 204 No Content - use Response not JSONResponse to avoid Content-Length issues
                return Response(status_code=204)
            elif method == "tools/list":
                result = self._handle_tools_list(params)
            elif method == "tools/call":
                result = await self._handle_tools_call(params, request)
            else:
                return self._error_response(
                    request_id, -32601, f"Method not found: {method}"
                )

            duration_ms = (time.time() - start_time) * 1000
            self.logger.info(f"MCP response: {method} ({duration_ms:.1f}ms)")

            return JSONResponse(
                content={"jsonrpc": jsonrpc, "id": request_id, "result": result},
                headers={
                    "MCP-Protocol-Version": self.MCP_PROTOCOL_VERSION,
                    "Mcp-Session-Id": str(uuid.uuid4()),
                },
            )

        except Exception as e:
            self.logger.error(f"MCP error: {method} - {str(e)}", exc_info=True)
            return self._error_response(request_id, -32000, str(e))

    def _handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request."""
        return {
            "protocolVersion": self.MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": self.name, "version": self.version},
        }

    def _handle_tools_list(self, params: Dict) -> Dict:
        """Handle tools/list request."""
        tools = [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema,
            }
            for t in self._tools.values()
        ]
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict, request: Request) -> Dict:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self._tools:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True,
            }

        tool_def = self._tools[tool_name]

        # Extract credentials from headers
        credentials = {}
        for header_name in tool_def.credential_headers:
            value = request.headers.get(header_name)
            if value:
                # Convert header name to key (X-Google-Refresh-Token -> refresh_token)
                key = header_name.lower().replace("x-", "").replace("-", "_")
                credentials[key] = value

        try:
            # Call the tool handler
            result = await tool_def.handler(credentials=credentials, **arguments)

            # Format result
            if isinstance(result, (dict, list)):
                content_text = json.dumps(result, indent=2, default=str)
            else:
                content_text = str(result)

            return {"content": [{"type": "text", "text": content_text}]}

        except Exception as e:
            self.logger.error(f"Tool error: {tool_name} - {str(e)}", exc_info=True)
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True,
            }

    def _error_response(
        self, request_id: Any, code: int, message: str
    ) -> JSONResponse:
        """Create JSON-RPC error response."""
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": code, "message": message},
            }
        )

    def run(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Run the MCP server."""
        import uvicorn

        self.logger.info(f"Starting MCP server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)
