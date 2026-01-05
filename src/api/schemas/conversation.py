"""API schemas for agent conversation management."""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ==================== Request Schemas ====================


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    title: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional title. If not provided, auto-generated from first message.",
    )


class UpdateConversationRequest(BaseModel):
    """Request to update a conversation (rename)."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="New title for the conversation",
    )


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="Message content",
    )


class AddMessageRequest(BaseModel):
    """Request to add a message to a conversation (internal use)."""

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role"
    )
    content: str = Field(
        ..., min_length=1, max_length=100000, description="Message content"
    )
    workflow_id: Optional[str] = Field(
        None, description="Associated Temporal workflow ID"
    )
    execution_id: Optional[str] = Field(
        None, description="Associated agent execution ID"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata (token usage, tool calls, etc.)"
    )


# ==================== Response Schemas ====================


class MessageResponse(BaseModel):
    """Individual message in a conversation."""

    id: str
    role: str
    content: str
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ConversationSummaryResponse(BaseModel):
    """Summary of a conversation for list views (rich preview)."""

    id: str
    agent_id: str
    agent_name: str
    agent_type: str
    title: str
    message_count: int
    last_message_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """List of conversations with pagination."""

    conversations: List[ConversationSummaryResponse]
    total: int


class ConversationDetailResponse(BaseModel):
    """Full conversation with messages."""

    id: str
    agent_id: str
    agent_name: str
    agent_type: str
    title: str
    is_auto_title: bool
    message_count: int
    messages: List[MessageResponse]
    created_at: datetime
    updated_at: datetime


class CreateConversationResponse(BaseModel):
    """Response after creating a conversation."""

    id: str
    agent_id: str
    title: str
    created_at: datetime


class AddMessageResponse(BaseModel):
    """Response after adding a message."""

    id: str
    role: str
    content: str
    created_at: datetime


# ==================== Streaming Event Schemas ====================


class StreamEventType(str):
    """Types of streaming events."""

    THINKING = "thinking"
    RETRIEVING = "retrieving"
    RETRIEVED = "retrieved"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    MCP_START = "mcp_start"
    MCP_END = "mcp_end"
    SKILL_START = "skill_start"
    SKILL_END = "skill_end"
    GENERATING = "generating"
    CHUNK = "chunk"
    COMPLETE = "complete"
    ERROR = "error"


class StreamEventData(BaseModel):
    """Base streaming event data."""

    type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class ThinkingEventData(BaseModel):
    """Data for thinking event."""

    step: Optional[str] = None


class RetrievingEventData(BaseModel):
    """Data for retrieving event (RAG)."""

    knowledge_base_name: str
    query_preview: Optional[str] = None


class RetrievedEventData(BaseModel):
    """Data for retrieved event (RAG complete)."""

    document_count: int
    chunks_used: int


class ToolEventData(BaseModel):
    """Data for tool start/end events."""

    tool_name: str
    tool_id: Optional[str] = None
    args_preview: Optional[str] = None
    success: Optional[bool] = None
    result_preview: Optional[str] = None


class MCPEventData(BaseModel):
    """Data for MCP tool events."""

    server_name: str
    tool_name: str
    success: Optional[bool] = None


class SkillEventData(BaseModel):
    """Data for skill injection events."""

    skill_name: str
    skill_id: str


class ChunkEventData(BaseModel):
    """Data for streaming content chunk."""

    content: str
    token_count: Optional[int] = None


class CompleteEventData(BaseModel):
    """Data for completion event."""

    message_id: str
    total_tokens: Optional[int] = None
    execution_id: Optional[str] = None


class ErrorEventData(BaseModel):
    """Data for error event."""

    error: str
    error_type: Optional[str] = None
    recoverable: bool = False
