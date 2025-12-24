"""API schemas for workflow definitions CRUD."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ParallelBranchSchema(BaseModel):
    """Schema for a branch in a parallel step."""

    id: Optional[str] = None
    agent_id: str
    input: str = "${user_input}"
    timeout: int = 120


class LoopInnerStepSchema(BaseModel):
    """Schema for a step inside a loop."""

    id: str
    agent_id: str
    input: str = "${user_input}"
    timeout: int = 120


class WorkflowStepSchema(BaseModel):
    """Schema for a workflow step."""

    id: str = Field(..., pattern=r"^[a-zA-Z][a-zA-Z0-9_-]{0,99}$")
    type: str = Field(default="agent", pattern="^(agent|parallel|conditional|loop)$")

    # Agent step fields
    agent_id: Optional[str] = None
    input: Optional[str] = None
    timeout: int = Field(default=120, ge=1, le=600)
    retries: int = Field(default=0, ge=0, le=5)
    on_error: str = "fail"

    # Parallel step fields
    branches: Optional[List[ParallelBranchSchema]] = None
    aggregation: str = Field(default="all", pattern="^(all|first|merge|best)$")

    # Conditional step fields
    condition_source: Optional[str] = None
    conditional_branches: Optional[Dict[str, str]] = None
    default: Optional[str] = None

    # Loop step fields
    max_iterations: int = Field(default=5, ge=1, le=20)
    exit_condition: Optional[str] = None
    steps: Optional[List[LoopInnerStepSchema]] = None


class CreateWorkflowDefinitionRequest(BaseModel):
    """Request to create a workflow definition."""

    id: str = Field(..., pattern=r"^[a-zA-Z][a-zA-Z0-9_-]{0,99}$")
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    steps: List[WorkflowStepSchema] = Field(..., min_length=1, max_length=50)
    entry_step: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class UpdateWorkflowDefinitionRequest(BaseModel):
    """Request to update a workflow definition."""

    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    steps: Optional[List[WorkflowStepSchema]] = Field(None, min_length=1, max_length=50)
    entry_step: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class WorkflowDefinitionResponse(BaseModel):
    """Response with workflow definition."""

    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    steps: List[WorkflowStepSchema]
    entry_step: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WorkflowDefinitionListResponse(BaseModel):
    """Response with list of workflow definitions."""

    workflows: List[WorkflowDefinitionResponse]
    total: int


class WorkflowValidationResponse(BaseModel):
    """Response from workflow validation."""

    valid: bool
    errors: List[str] = []
