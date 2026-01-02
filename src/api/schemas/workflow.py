"""API schemas for workflow execution."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageSchema(BaseModel):
    """Schema for conversation message."""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., max_length=50000)  # 50k chars per message


class ExecuteAgentRequest(BaseModel):
    """Request to execute an agent."""

    agent_id: str = Field(..., min_length=1, max_length=100)
    user_input: str = Field(..., min_length=1, max_length=10000)  # 10k chars max
    conversation_history: List[MessageSchema] = Field(
        default_factory=list,
        max_length=100  # Max 100 messages in history
    )
    session_id: Optional[str] = None
    # Optional reference to a saved workflow from the workflows table
    # If provided, execution history will be saved
    source_workflow_id: Optional[str] = Field(
        None,
        description="ID of the workflow from workflows table (for execution tracking)"
    )
    # Optional workflow definition for WORKFLOW mode orchestrators
    # JSON structure: {"id": "...", "steps": [...], "entry_step": "..."}
    workflow_definition: Optional[Dict[str, Any]] = Field(
        None,
        description="Workflow definition for WORKFLOW mode orchestrators"
    )


class ExecuteAgentResponse(BaseModel):
    """Response from agent execution."""

    content: str
    agent_id: str
    agent_type: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    workflow_id: Optional[str] = None

    # Clarification fields - for interactive follow-up questions
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    clarification_options: Optional[List[str]] = None


class WorkflowStatusRequest(BaseModel):
    """Request to check workflow status."""

    workflow_id: str


class WorkflowStatusResponse(BaseModel):
    """Response with workflow status."""

    workflow_id: str
    status: str  # RUNNING, COMPLETED, FAILED, CANCELLED
    result: Optional[ExecuteAgentResponse] = None
