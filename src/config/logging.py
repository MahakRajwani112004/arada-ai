"""Logging configuration with structlog."""
import logging
import re
import sys
from typing import Any, Dict

import structlog
from structlog.types import Processor

from .settings import get_settings


# ============================================
# Human-Readable Message Templates
# ============================================

EVENT_MESSAGES = {
    # Auth events
    "user_logged_in": "User {email} logged in successfully",
    "login_failed": "Login failed for {email}: {reason}",
    "user_logged_out": "User logged out",
    "user_registered": "New user registered: {email}",
    "invite_created": "Invite created for {email}",

    # Agent events
    "agent_generate_started": "Generating agent: {name}",
    "agent_generate_completed": "Generated agent: {name} (type: {suggested_type})",
    "agent_generate_failed": "Failed to generate agent {name}: {error}",
    "agent_created": "Agent created: {name} ({agent_type})",
    "agent_updated": "Agent updated: {name}",
    "agent_deleted": "Agent deleted: {agent_id}",
    "agent_create_conflict": "Agent already exists: {agent_id}",
    "agent_update_not_found": "Agent not found: {agent_id}",
    "agent_delete_not_found": "Agent not found: {agent_id}",

    # MCP events
    "mcp_server_created": "MCP connected: {name}",
    "mcp_server_connection_failed": "MCP connection failed: {error}",
    "mcp_server_deleted": "MCP disconnected: {server_id}",
    "mcp_server_reconnect_initiated": "MCP reconnecting: {service}",
    "mcp_server_reconnected": "MCP reconnected: {server_id}",
    "mcp_server_reconnect_failed": "MCP reconnect failed: {error}",
    "mcp_servers_reconnected": "Reconnected {total} MCP servers",
    "oauth_token_resolved": "OAuth token resolved for {credential_name}",
    "oauth_token_resolution_failed": "OAuth token failed: {error}",

    # Knowledge Base events
    "knowledge_base_create_started": "Creating knowledge base: {name}",
    "knowledge_base_created": "Knowledge base created: {name}",
    "knowledge_base_updated": "Knowledge base updated: {name}",
    "knowledge_base_deleted": "Knowledge base deleted: {name}",
    "knowledge_base_delete_not_found": "Knowledge base not found: {kb_id}",
    "knowledge_base_update_not_found": "Knowledge base not found: {kb_id}",
    "document_upload_started": "Uploading document: {filename}",
    "document_upload_completed": "Document indexed: {filename}",
    "document_indexing_failed": "Document indexing failed: {error}",
    "document_indexed": "Document indexed: {chunks} chunks",
    "document_deleted": "Document deleted: {doc_id}",
    "knowledge_base_search_started": "Searching knowledge base",
    "knowledge_base_search_completed": "Search found {results_count} results",
    "knowledge_base_search_failed": "Search failed: {error}",

    # LLM events
    "llm_call_completed": "LLM call: {provider}/{model} ({latency_ms}ms)",
    "llm_call_failed": "LLM call failed: {error}",

    # Agent execution events
    "agent_execution_completed": "Agent executed: {agent_id} ({latency_ms}ms)",
    "agent_execution_failed": "Agent execution failed: {error}",

    # Application events
    "application_started": "Application started: {name} v{version}",
    "request_started": "{method} {path}",
    "request_completed": "{method} {path} → {status_code} ({process_time_ms}ms)",
}


def add_human_message(
    logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Structlog processor that adds a human-readable 'message' field."""
    event = event_dict.get("event", "")

    template = EVENT_MESSAGES.get(event)
    if template:
        try:
            # Format template with available context
            message = template.format(**{k: v for k, v in event_dict.items() if v is not None})
        except KeyError:
            # Partial format if some placeholders missing
            message = template
            for key, value in event_dict.items():
                if value is not None:
                    message = message.replace("{" + key + "}", str(value))
            message = re.sub(r'\{[^}]+\}', '?', message)
        event_dict["message"] = message
    else:
        # For unknown events, convert snake_case to readable text
        event_dict["message"] = event.replace("_", " ").capitalize()

    return event_dict


def setup_logging() -> None:
    """Configure structured logging with structlog."""
    settings = get_settings()

    # Common processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_human_message,  # Add human-readable message
    ]

    if settings.log_format == "json":
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Set levels for noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance."""
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding context to logs."""

    def __init__(self, **context: Any):
        """Initialize with context values."""
        self.context = context
        self._token = None

    def __enter__(self) -> "LogContext":
        """Enter context and bind values."""
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context and clear bindings."""
        structlog.contextvars.clear_contextvars()

    def bind(self, **more_context: Any) -> None:
        """Add more context values."""
        structlog.contextvars.bind_contextvars(**more_context)
