"""API schemas for agents."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models.enums import AgentType, SafetyLevel


class AgentRoleSchema(BaseModel):
    """API schema for agent role."""

    title: str
    expertise: List[str] = []
    personality: List[str] = []
    communication_style: str = "professional"


class AgentGoalSchema(BaseModel):
    """API schema for agent goal."""

    objective: str
    success_criteria: List[str] = []
    constraints: List[str] = []


class AgentInstructionsSchema(BaseModel):
    """API schema for agent instructions."""

    steps: List[str] = []
    rules: List[str] = []
    prohibited: List[str] = []
    output_format: Optional[str] = None


class AgentExampleSchema(BaseModel):
    """API schema for agent example."""

    input: str
    output: str


class LLMConfigSchema(BaseModel):
    """API schema for LLM config."""

    provider: str = "anthropic"
    model: str = "claude-3-sonnet-20240229"
    temperature: float = 0.7
    max_tokens: int = 1024


class KnowledgeBaseConfigSchema(BaseModel):
    """API schema for knowledge base config."""

    collection_name: str
    embedding_model: str = "text-embedding-3-small"
    top_k: int = 5
    similarity_threshold: Optional[float] = None


class ToolConfigSchema(BaseModel):
    """API schema for tool config."""

    tool_id: str
    enabled: bool = True
    requires_confirmation: bool = False


class SkillConfigSchema(BaseModel):
    """API schema for skill config."""

    skill_id: str
    enabled: bool = True
    parameters: Dict[str, Any] = {}
    priority: int = 0


class SafetyConfigSchema(BaseModel):
    """API schema for safety config."""

    level: SafetyLevel = SafetyLevel.STANDARD
    blocked_topics: List[str] = []
    blocked_patterns: List[str] = []


class AgentReferenceSchema(BaseModel):
    """API schema for agent reference in orchestrator."""

    agent_id: str
    alias: Optional[str] = None
    description: Optional[str] = None


class OrchestratorConfigSchema(BaseModel):
    """API schema for orchestrator config."""

    mode: str = "llm_driven"  # llm_driven, workflow, hybrid
    auto_discover: bool = False  # If True, automatically discover all available agents
    exclude_agent_types: List[str] = ["OrchestratorAgent"]  # Agent types to exclude when auto_discover is True
    exclude_agent_ids: List[str] = []  # Specific agent IDs to exclude when auto_discover is True
    available_agents: List[AgentReferenceSchema] = []  # Ignored if auto_discover is True
    workflow_definition: Optional[str] = None
    default_aggregation: str = "all"  # first, all, vote, merge, best
    max_parallel: int = 5
    max_depth: int = 3
    allow_self_reference: bool = False


class CreateAgentRequest(BaseModel):
    """Request to create an agent."""

    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    agent_type: AgentType
    role: AgentRoleSchema
    goal: AgentGoalSchema
    instructions: AgentInstructionsSchema = Field(default_factory=AgentInstructionsSchema)
    examples: List[AgentExampleSchema] = []
    llm_config: Optional[LLMConfigSchema] = None
    knowledge_base: Optional[KnowledgeBaseConfigSchema] = None
    tools: List[ToolConfigSchema] = []
    skills: List[SkillConfigSchema] = []
    routing_table: Optional[Dict[str, str]] = None
    orchestrator_config: Optional[OrchestratorConfigSchema] = None
    safety: SafetyConfigSchema = Field(default_factory=SafetyConfigSchema)


class AgentResponse(BaseModel):
    """Response containing agent summary."""

    id: str
    name: str
    description: str
    agent_type: AgentType
    created: bool = True
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about potential issues (e.g., hallucination risks)"
    )

    class Config:
        from_attributes = True


class AgentDetailResponse(BaseModel):
    """Response containing full agent details for editing."""

    id: str
    name: str
    description: str
    agent_type: AgentType
    role: AgentRoleSchema
    goal: AgentGoalSchema
    instructions: AgentInstructionsSchema
    examples: List[AgentExampleSchema] = []
    llm_config: Optional[LLMConfigSchema] = None
    knowledge_base: Optional[KnowledgeBaseConfigSchema] = None
    tools: List[ToolConfigSchema] = []
    skills: List[SkillConfigSchema] = []
    routing_table: Optional[Dict[str, str]] = None
    orchestrator_config: Optional[OrchestratorConfigSchema] = None
    safety: SafetyConfigSchema

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Response containing list of agents."""

    agents: List[AgentResponse]
    total: int


class GenerateAgentRequest(BaseModel):
    """Request to generate agent configuration with AI."""

    name: str = Field(..., min_length=1, max_length=200)
    context: Optional[str] = Field(None, max_length=500, description="Optional context about what the agent should do")


class GenerateAgentResponse(BaseModel):
    """Response containing AI-generated agent configuration."""

    description: str
    role: AgentRoleSchema
    goal: AgentGoalSchema
    instructions: AgentInstructionsSchema
    examples: List[AgentExampleSchema] = []
    suggested_agent_type: AgentType


# ============================================================================
# Agent Overview Tab - Stats & Executions
# ============================================================================


class AgentStatsResponse(BaseModel):
    """Response containing agent performance statistics."""

    agent_id: str
    time_range: str  # "24h", "7d", "30d", "90d"

    # Performance metrics
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float  # 0.0 to 1.0
    avg_latency_ms: float
    p95_latency_ms: float

    # Cost metrics
    total_cost_cents: int
    total_tokens: int

    # Trends (percentage change vs previous period)
    executions_trend: float  # +12.5 means 12.5% increase
    success_trend: float
    latency_trend: float
    cost_trend: float


class ExecutionSummary(BaseModel):
    """Summary of a single execution."""

    id: str
    status: str  # "completed", "failed"
    timestamp: str  # ISO format
    duration_ms: int
    input_preview: Optional[str] = None
    output_preview: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    total_tokens: int = 0
    total_cost_cents: int = 0


class AgentExecutionsResponse(BaseModel):
    """Response containing list of agent executions."""

    executions: List[ExecutionSummary]
    total: int
    has_more: bool


class ExecutionDetailResponse(BaseModel):
    """Full execution details including metadata."""

    id: str
    agent_id: str
    agent_type: str
    timestamp: str  # ISO format
    status: str  # "completed", "failed"
    duration_ms: int
    input_preview: Optional[str] = None
    output_preview: Optional[str] = None
    total_tokens: int = 0
    total_cost_cents: int = 0
    llm_calls_count: int = 0
    tool_calls_count: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    workflow_id: Optional[str] = None
    execution_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="ignore")


class UsageDataPoint(BaseModel):
    """Single data point for usage chart."""

    timestamp: str  # ISO format
    executions: int
    successful: int
    failed: int
    avg_latency_ms: float
    total_cost_cents: int


class AgentUsageHistoryResponse(BaseModel):
    """Response containing usage history for charts."""

    data: List[UsageDataPoint]
    granularity: str  # "hour" or "day"
    time_range: str
