"""API schemas for workflow execution."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageSchema(BaseModel):
    """Schema for conversation message."""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ExecuteAgentRequest(BaseModel):
    """Request to execute an agent."""

    agent_id: str = Field(..., min_length=1)
    user_input: str = Field(..., min_length=1)
    conversation_history: List[MessageSchema] = []
    session_id: Optional[str] = None


class ExecuteAgentResponse(BaseModel):
    """Response from agent execution."""

    content: str
    agent_id: str
    agent_type: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    workflow_id: Optional[str] = None


class WorkflowStatusRequest(BaseModel):
    """Request to check workflow status."""

    workflow_id: str


class WorkflowStatusResponse(BaseModel):
    """Response with workflow status."""

    workflow_id: str
    status: str  # RUNNING, COMPLETED, FAILED, CANCELLED
    result: Optional[ExecuteAgentResponse] = None
