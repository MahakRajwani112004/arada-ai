"""API schemas for workflow management, generation, and execution history."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== Workflow Definition Schemas ====================


class WorkflowStepSchema(BaseModel):
    """Schema for a workflow step."""

    id: str = Field(..., min_length=1, max_length=100)
    type: str = Field(
        ..., description="Step type: agent, parallel, conditional, loop"
    )
    agent_id: Optional[str] = Field(None, description="Agent ID for agent steps")
    input: Optional[str] = Field(
        "${user_input}", description="Input template with ${...} placeholders"
    )
    timeout: int = Field(120, ge=1, le=600)
    retries: int = Field(0, ge=0, le=5)
    on_error: str = Field("fail", description="Error handling: fail, skip, or step_id")

    # Parallel step fields
    branches: Optional[List[Dict[str, Any]]] = None
    aggregation: Optional[str] = Field(None, description="all, first, merge, best")

    # Conditional step fields
    condition_source: Optional[str] = None
    conditional_branches: Optional[Dict[str, str]] = None
    default: Optional[str] = None

    # Loop step fields
    max_iterations: Optional[int] = Field(None, ge=1, le=20)
    exit_condition: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None


class WorkflowDefinitionSchema(BaseModel):
    """Schema for workflow definition."""

    id: str = Field(..., min_length=1, max_length=100)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    steps: List[WorkflowStepSchema] = Field(..., min_length=1, max_length=50)
    entry_step: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


# ==================== Workflow CRUD Schemas ====================


class CreateWorkflowRequest(BaseModel):
    """Request to create a new workflow."""

    id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=1000)
    category: str = Field("general", max_length=100)
    tags: List[str] = Field(default_factory=list)
    definition: WorkflowDefinitionSchema
    created_by: Optional[str] = None


class UpdateWorkflowRequest(BaseModel):
    """Request to update a workflow."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    definition: Optional[WorkflowDefinitionSchema] = None


class WorkflowResponse(BaseModel):
    """Response containing workflow details."""

    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    definition: Dict[str, Any]
    version: int
    is_template: bool
    is_active: bool
    source_template_id: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class WorkflowSummaryResponse(BaseModel):
    """Summary of a workflow for listing."""

    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    version: int
    is_template: bool
    created_at: datetime
    updated_at: datetime


class WorkflowListResponse(BaseModel):
    """Response containing list of workflows."""

    workflows: List[WorkflowSummaryResponse]
    total: int


class CopyWorkflowRequest(BaseModel):
    """Request to copy a workflow."""

    new_id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    new_name: str = Field(..., min_length=1, max_length=200)
    created_by: Optional[str] = None


# ==================== Execution History Schemas ====================


class WorkflowExecutionResponse(BaseModel):
    """Response containing execution details."""

    id: str
    workflow_id: str
    temporal_workflow_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error: Optional[str]
    steps_executed: List[str]
    step_results: Dict[str, Any]
    triggered_by: Optional[str]


class WorkflowExecutionListResponse(BaseModel):
    """Response containing list of executions."""

    executions: List[WorkflowExecutionResponse]
    total: int


# ==================== Resource Discovery Schemas ====================


class AvailableAgentResponse(BaseModel):
    """An agent available for use in workflows."""

    id: str
    name: str
    description: str
    agent_type: str


class AvailableAgentsResponse(BaseModel):
    """List of available agents."""

    agents: List[AvailableAgentResponse]
    total: int


class MCPToolResponse(BaseModel):
    """An MCP tool available for use in workflows."""

    id: str  # Format: server_id:tool_name
    name: str
    description: str


class AvailableMCPServerResponse(BaseModel):
    """An MCP server with its tools."""

    id: str
    name: str
    template: Optional[str]
    status: str
    tools: List[MCPToolResponse]


class AvailableMCPsResponse(BaseModel):
    """List of available MCP servers."""

    mcp_servers: List[AvailableMCPServerResponse]
    total: int


class AvailableToolResponse(BaseModel):
    """A tool (native or MCP) available for use."""

    id: str
    name: str
    description: str
    source: str  # "native" or "mcp:{server_id}"


class AvailableToolsResponse(BaseModel):
    """List of all available tools."""

    tools: List[AvailableToolResponse]
    total: int


# ==================== AI Generation Schemas ====================


class GenerateWorkflowRequest(BaseModel):
    """Request to generate a workflow from natural language."""

    prompt: str = Field(..., min_length=10, max_length=2000)
    context: Optional[str] = Field(None, max_length=1000)
    preferred_complexity: str = Field(
        "auto", description="simple, moderate, complex, or auto"
    )
    include_agents: bool = Field(True, description="Generate agent configs if needed")
    include_mcps: bool = Field(True, description="Suggest MCP servers if needed")


class GeneratedAgentConfig(BaseModel):
    """Agent configuration generated by AI."""

    id: str
    name: str
    description: str
    agent_type: str
    role: Dict[str, Any]
    goal: Dict[str, Any]
    instructions: Dict[str, Any]


class MCPSuggestion(BaseModel):
    """MCP server suggestion from AI generation."""

    template: str
    reason: str
    required_for_steps: List[str] = []


class GenerateWorkflowResponse(BaseModel):
    """Response from AI workflow generation."""

    workflow: WorkflowDefinitionSchema
    agents_to_create: List[GeneratedAgentConfig]
    existing_agents_used: List[str]
    mcps_suggested: List[MCPSuggestion]
    existing_mcps_used: List[str]
    explanation: str
    warnings: List[str] = []
    estimated_complexity: str


class ApplyGeneratedWorkflowRequest(BaseModel):
    """Request to save a generated workflow (without auto-creating agents).

    Per the plan: User creates agents separately. This just saves the workflow.
    """

    workflow: WorkflowDefinitionSchema
    workflow_name: str = Field(..., min_length=1, max_length=200)
    workflow_description: str = Field("", max_length=1000)
    workflow_category: str = Field("ai-generated", max_length=100)
    created_by: Optional[str] = None


class ApplyGeneratedWorkflowResponse(BaseModel):
    """Response after saving generated workflow.

    Indicates which steps are blocked due to missing agents.
    """

    workflow_id: str
    blocked_steps: List[str] = Field(
        default_factory=list, description="Steps with missing agents"
    )
    missing_agents: List[str] = Field(
        default_factory=list, description="Agent IDs that don't exist"
    )
    can_execute: bool = Field(
        ..., description="True only if all agents exist"
    )
    next_action: str = Field(
        ..., description="'create_agents' or 'ready_to_run'"
    )


# ==================== Workflow Execution Schemas ====================


class ExecuteWorkflowRequest(BaseModel):
    """Request to execute a stored workflow."""

    user_input: str = Field(..., min_length=1, max_length=10000)
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context variables for the workflow"
    )
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")


class StepExecutionResult(BaseModel):
    """Result of executing a single workflow step."""

    step_id: str
    status: str  # "completed", "failed", "skipped"
    output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class ExecuteWorkflowResponse(BaseModel):
    """Response from workflow execution."""

    execution_id: str
    workflow_id: str
    status: str  # "completed", "failed", "running"
    final_output: Optional[str] = None
    step_results: List[StepExecutionResult]
    total_duration_ms: Optional[int] = None
    error: Optional[str] = None


# ==================== Workflow Validation Schemas ====================


class ValidationError(BaseModel):
    """A single validation error."""

    field: str
    message: str
    severity: str = "error"  # "error" or "warning"


class ValidateWorkflowRequest(BaseModel):
    """Request to validate a workflow definition."""

    definition: WorkflowDefinitionSchema


class ValidateWorkflowResponse(BaseModel):
    """Response from workflow validation."""

    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    missing_agents: List[str] = []
    missing_mcps: List[str] = []
