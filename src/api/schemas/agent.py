"""API schemas for agents."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

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
    available_agents: List[AgentReferenceSchema] = []
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
    routing_table: Optional[Dict[str, str]] = None
    orchestrator_config: Optional[OrchestratorConfigSchema] = None
    safety: SafetyConfigSchema = Field(default_factory=SafetyConfigSchema)


class AgentResponse(BaseModel):
    """Response containing agent details."""

    id: str
    name: str
    description: str
    agent_type: AgentType
    created: bool = True

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
