"""Stream event types for agent execution progress."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class StreamEventType(str, Enum):
    """Types of streaming events during agent execution."""

    # Agent thinking/processing
    THINKING = "thinking"

    # RAG retrieval
    RETRIEVING = "retrieving"
    RETRIEVED = "retrieved"

    # Tool execution
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"

    # MCP tool execution
    MCP_START = "mcp_start"
    MCP_END = "mcp_end"

    # Skill injection
    SKILL_START = "skill_start"
    SKILL_END = "skill_end"

    # LLM generation
    GENERATING = "generating"
    CHUNK = "chunk"

    # Completion
    COMPLETE = "complete"
    ERROR = "error"

    # Message events
    MESSAGE_SAVED = "message_saved"


@dataclass
class StreamEvent:
    """A streaming event during agent execution.

    Attributes:
        type: The type of event
        data: Event-specific data payload
    """

    type: StreamEventType
    data: Dict[str, Any] = field(default_factory=dict)

    def to_sse(self) -> Dict[str, Any]:
        """Convert to Server-Sent Event format."""
        return {
            "event": self.type.value,
            "data": self.data,
        }


# Convenience constructors for common events


def thinking_event(step: Optional[str] = None) -> StreamEvent:
    """Create a thinking event."""
    data = {}
    if step:
        data["step"] = step
    return StreamEvent(type=StreamEventType.THINKING, data=data)


def retrieving_event(
    knowledge_base_name: str, query_preview: Optional[str] = None
) -> StreamEvent:
    """Create a retrieving event (RAG search starting)."""
    data = {"knowledge_base_name": knowledge_base_name}
    if query_preview:
        data["query_preview"] = query_preview[:100]
    return StreamEvent(type=StreamEventType.RETRIEVING, data=data)


def retrieved_event(document_count: int, chunks_used: int) -> StreamEvent:
    """Create a retrieved event (RAG search complete)."""
    return StreamEvent(
        type=StreamEventType.RETRIEVED,
        data={
            "document_count": document_count,
            "chunks_used": chunks_used,
        },
    )


def tool_start_event(
    tool_name: str,
    tool_id: Optional[str] = None,
    args_preview: Optional[str] = None,
) -> StreamEvent:
    """Create a tool start event."""
    data = {"tool_name": tool_name}
    if tool_id:
        data["tool_id"] = tool_id
    if args_preview:
        data["args_preview"] = args_preview[:200]
    return StreamEvent(type=StreamEventType.TOOL_START, data=data)


def tool_end_event(
    tool_name: str,
    success: bool,
    result_preview: Optional[str] = None,
) -> StreamEvent:
    """Create a tool end event."""
    data = {
        "tool_name": tool_name,
        "success": success,
    }
    if result_preview:
        data["result_preview"] = result_preview[:200]
    return StreamEvent(type=StreamEventType.TOOL_END, data=data)


def mcp_start_event(server_name: str, tool_name: str) -> StreamEvent:
    """Create an MCP tool start event."""
    return StreamEvent(
        type=StreamEventType.MCP_START,
        data={
            "server_name": server_name,
            "tool_name": tool_name,
        },
    )


def mcp_end_event(
    server_name: str, tool_name: str, success: bool
) -> StreamEvent:
    """Create an MCP tool end event."""
    return StreamEvent(
        type=StreamEventType.MCP_END,
        data={
            "server_name": server_name,
            "tool_name": tool_name,
            "success": success,
        },
    )


def skill_start_event(skill_name: str, skill_id: str) -> StreamEvent:
    """Create a skill injection start event."""
    return StreamEvent(
        type=StreamEventType.SKILL_START,
        data={
            "skill_name": skill_name,
            "skill_id": skill_id,
        },
    )


def skill_end_event(skill_name: str, skill_id: str) -> StreamEvent:
    """Create a skill injection end event."""
    return StreamEvent(
        type=StreamEventType.SKILL_END,
        data={
            "skill_name": skill_name,
            "skill_id": skill_id,
        },
    )


def generating_event() -> StreamEvent:
    """Create a generating event (LLM starting to generate)."""
    return StreamEvent(type=StreamEventType.GENERATING, data={})


def chunk_event(content: str, token_count: Optional[int] = None) -> StreamEvent:
    """Create a streaming content chunk event."""
    data = {"content": content}
    if token_count is not None:
        data["token_count"] = token_count
    return StreamEvent(type=StreamEventType.CHUNK, data=data)


def complete_event(
    message_id: str,
    total_tokens: Optional[int] = None,
    execution_id: Optional[str] = None,
) -> StreamEvent:
    """Create a completion event."""
    data = {"message_id": message_id}
    if total_tokens is not None:
        data["total_tokens"] = total_tokens
    if execution_id:
        data["execution_id"] = execution_id
    return StreamEvent(type=StreamEventType.COMPLETE, data=data)


def error_event(
    error: str,
    error_type: Optional[str] = None,
    recoverable: bool = False,
) -> StreamEvent:
    """Create an error event."""
    data = {
        "error": error,
        "recoverable": recoverable,
    }
    if error_type:
        data["error_type"] = error_type
    return StreamEvent(type=StreamEventType.ERROR, data=data)


def message_saved_event(role: str, message_id: Optional[str] = None) -> StreamEvent:
    """Create a message saved event."""
    data = {"role": role}
    if message_id:
        data["message_id"] = message_id
    return StreamEvent(type=StreamEventType.MESSAGE_SAVED, data=data)
