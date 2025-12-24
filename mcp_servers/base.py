"""Base MCP Server - handles protocol, logging, and provides tool decorator.

All MCP servers should extend BaseMCPServer and use @tool decorator to define tools.

Features:
- Structured logging with structlog (JSON output)
- Temporal workflow context extraction from headers
- Request tracing with request_id
- Tool execution metrics tracking
- Enhanced health checks with statistics
"""
import functools
import json
import logging
import sys
import time
import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel


def _configure_logging(log_level: str = "INFO", json_output: bool = True) -> None:
    """Configure structlog for MCP servers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_output: If True, output JSON logs; otherwise console format
    """
    # Shared processors for all output formats
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
        force=True,
    )

    # Quiet noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# Configure logging on module load
_configure_logging()


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable
    credential_headers: List[str] = field(default_factory=list)


@dataclass
class ToolMetrics:
    """Runtime metrics for a single tool.

    Tracks call counts, success/failure rates, and timing information.
    All MCP servers automatically collect these metrics.
    """

    call_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration_ms: float = 0.0
    last_called: Optional[datetime] = None
    last_error: Optional[str] = None

    @property
    def success_rate(self) -> Optional[float]:
        """Calculate success rate as percentage."""
        if self.call_count == 0:
            return None
        return round((self.success_count / self.call_count) * 100, 1)

    @property
    def avg_duration_ms(self) -> Optional[float]:
        """Calculate average duration in milliseconds."""
        if self.call_count == 0:
            return None
        return round(self.total_duration_ms / self.call_count, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for health endpoint."""
        return {
            "calls": self.call_count,
            "successes": self.success_count,
            "failures": self.failure_count,
            "success_rate": self.success_rate,
            "avg_duration_ms": self.avg_duration_ms,
            "last_called": self.last_called.isoformat() if self.last_called else None,
            "last_error": self.last_error,
        }


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
    - Structured logging with structlog
    - Temporal workflow context extraction
    - Request tracing with request_id
    - Tool execution metrics
    - Health checks with statistics
    - Error handling
    - Credential extraction from headers

    Subclasses just define tools using @tool decorator.
    All logging, metrics, and Temporal context are handled automatically.
    """

    MCP_PROTOCOL_VERSION = "2025-06-18"

    # Temporal context headers - automatically extracted and added to logs
    TEMPORAL_HEADERS = {
        "X-Temporal-Workflow-Id": "workflow_id",
        "X-Temporal-Run-Id": "run_id",
        "X-Temporal-Activity-Id": "activity_id",
        "X-Temporal-Namespace": "namespace",
    }

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
        self.logger = structlog.get_logger(f"mcp.{name}")

        # Server lifecycle tracking
        self._start_time = datetime.utcnow()

        # Discover tools from decorated methods
        self._tools: Dict[str, ToolDefinition] = {}
        self._discover_tools()

        # Initialize metrics for each tool
        self._metrics: Dict[str, ToolMetrics] = {
            tool_name: ToolMetrics() for tool_name in self._tools.keys()
        }

        # Create FastAPI app
        self.app = self._create_app()

        self.logger.info(
            "mcp_server_initialized",
            server=name,
            version=version,
            tools=list(self._tools.keys()),
            tool_count=len(self._tools),
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
                self.logger.debug("tool_registered", tool=tool_def.name)

    def _extract_request_context(self, request: Request) -> Dict[str, str]:
        """Extract Temporal and tracing context from request headers.

        This context is automatically bound to all logs within the request.

        Args:
            request: FastAPI request object

        Returns:
            Dictionary with context values (request_id, workflow_id, etc.)
        """
        context = {
            "request_id": request.headers.get("X-Request-Id", str(uuid.uuid4())),
            "server": self.name,
        }

        # Extract Temporal workflow context if present
        for header, key in self.TEMPORAL_HEADERS.items():
            value = request.headers.get(header)
            if value:
                context[key] = value

        return context

    def _record_tool_metric(
        self, tool_name: str, duration_ms: float, success: bool, error: Optional[str] = None
    ) -> None:
        """Record metrics for a tool execution.

        Args:
            tool_name: Name of the tool
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
            error: Error message if failed
        """
        if tool_name not in self._metrics:
            self._metrics[tool_name] = ToolMetrics()

        metrics = self._metrics[tool_name]
        metrics.call_count += 1
        metrics.total_duration_ms += duration_ms
        metrics.last_called = datetime.utcnow()

        if success:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1
            metrics.last_error = error

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
            uptime_seconds = (datetime.utcnow() - self._start_time).total_seconds()
            total_calls = sum(m.call_count for m in self._metrics.values())
            total_failures = sum(m.failure_count for m in self._metrics.values())

            return {
                "status": "healthy",
                "server": self.name,
                "version": self.version,
                "uptime_seconds": round(uptime_seconds, 1),
                "stats": {
                    "total_calls": total_calls,
                    "total_failures": total_failures,
                    "success_rate": round(
                        ((total_calls - total_failures) / total_calls) * 100, 1
                    ) if total_calls > 0 else None,
                },
                "tools": {
                    name: metrics.to_dict()
                    for name, metrics in self._metrics.items()
                },
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
        """Handle incoming MCP JSON-RPC request.

        Extracts Temporal context from headers and binds it to all logs.
        """
        start_time = time.time()

        # Extract and bind context for all logs in this request
        context = self._extract_request_context(request)
        clear_contextvars()
        bind_contextvars(**context)

        body = await request.json()

        jsonrpc = body.get("jsonrpc", "2.0")
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        self.logger.info(
            "mcp_request_received",
            method=method,
            jsonrpc_id=request_id,
        )

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
                self.logger.warning("mcp_method_not_found", method=method)
                return self._error_response(
                    request_id, -32601, f"Method not found: {method}"
                )

            duration_ms = (time.time() - start_time) * 1000
            self.logger.info(
                "mcp_request_completed",
                method=method,
                duration_ms=round(duration_ms, 2),
                status="success",
            )

            return JSONResponse(
                content={"jsonrpc": jsonrpc, "id": request_id, "result": result},
                headers={
                    "MCP-Protocol-Version": self.MCP_PROTOCOL_VERSION,
                    "Mcp-Session-Id": str(uuid.uuid4()),
                },
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.exception(
                "mcp_request_failed",
                method=method,
                duration_ms=round(duration_ms, 2),
                error=str(e),
                error_type=type(e).__name__,
            )
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
        """Handle tools/call request with metrics tracking."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        start_time = time.time()

        # Bind tool context for logging
        bind_contextvars(tool=tool_name)

        if tool_name not in self._tools:
            self.logger.warning("tool_not_found", tool=tool_name)
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True,
            }

        tool_def = self._tools[tool_name]

        # Log tool execution start (don't log argument values for security)
        self.logger.info(
            "tool_execution_started",
            tool=tool_name,
            argument_keys=list(arguments.keys()),
        )

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

            # Record success metrics
            duration_ms = (time.time() - start_time) * 1000
            self._record_tool_metric(tool_name, duration_ms, success=True)

            self.logger.info(
                "tool_execution_completed",
                tool=tool_name,
                duration_ms=round(duration_ms, 2),
                status="success",
            )

            # Format result
            if isinstance(result, (dict, list)):
                content_text = json.dumps(result, indent=2, default=str)
            else:
                content_text = str(result)

            return {"content": [{"type": "text", "text": content_text}]}

        except Exception as e:
            # Record failure metrics
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self._record_tool_metric(tool_name, duration_ms, success=False, error=error_msg)

            self.logger.exception(
                "tool_execution_failed",
                tool=tool_name,
                duration_ms=round(duration_ms, 2),
                error=error_msg,
                error_type=type(e).__name__,
            )
            return {
                "content": [{"type": "text", "text": f"Error: {error_msg}"}],
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
