"""Complete agent configuration model."""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import AgentType
from .knowledge_config import KnowledgeBaseConfig
from .llm_config import LLMConfig
from .persona import AgentExample, AgentGoal, AgentInstructions, AgentRole
from .safety_config import GovernanceConfig, SafetyConfig
from .tool_config import ToolConfig


class AgentConfig(BaseModel):
    """
    Complete agent configuration.

    This is what gets stored in the database and created from UI.
    The agent_type determines which base agent class to use.
    """

    # Identity
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent description")
    version: str = Field(default="1.0.0", description="Config version")

    # Type - determines which base agent class to use
    agent_type: AgentType = Field(..., description="Agent type")

    # Persona
    role: AgentRole = Field(..., description="Agent role definition")
    goal: AgentGoal = Field(..., description="Agent goal definition")
    instructions: AgentInstructions = Field(
        default_factory=AgentInstructions,
        description="Agent instructions",
    )
    examples: List[AgentExample] = Field(
        default_factory=list,
        description="Few-shot examples",
    )

    # Capabilities (optional based on agent_type)
    llm_config: Optional[LLMConfig] = Field(
        default=None,
        description="LLM configuration",
    )
    knowledge_base: Optional[KnowledgeBaseConfig] = Field(
        default=None,
        description="Knowledge base configuration",
    )
    tools: List[ToolConfig] = Field(
        default_factory=list,
        description="Tool configurations",
    )

    # For RouterAgent
    routing_table: Optional[Dict[str, str]] = Field(
        default=None,
        description="Intent to agent_id mapping for routing",
    )

    # Safety & Governance
    safety: SafetyConfig = Field(
        default_factory=SafetyConfig,
        description="Safety configuration",
    )
    governance: GovernanceConfig = Field(
        default_factory=GovernanceConfig,
        description="Governance configuration",
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )
    created_by: Optional[str] = Field(
        default=None,
        description="Creator user ID",
    )
    is_active: bool = Field(
        default=True,
        description="Whether agent is active",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for organization",
    )

    def validate_for_type(self) -> List[str]:
        """Validate config has required fields for agent type."""
        errors = []

        # LLM config required for LLM-based agents
        llm_required = [
            AgentType.LLM,
            AgentType.RAG,
            AgentType.TOOL,
            AgentType.FULL,
            AgentType.ROUTER,
        ]
        if self.agent_type in llm_required and not self.llm_config:
            errors.append(f"{self.agent_type.value} requires llm_config")

        # Knowledge base required for RAG agents
        kb_required = [AgentType.RAG, AgentType.FULL]
        if self.agent_type in kb_required and not self.knowledge_base:
            errors.append(f"{self.agent_type.value} requires knowledge_base")

        # Tools required for tool agents
        tool_required = [AgentType.TOOL, AgentType.FULL]
        if self.agent_type in tool_required and not self.tools:
            errors.append(f"{self.agent_type.value} requires at least one tool")

        # Routing table required for router
        if self.agent_type == AgentType.ROUTER and not self.routing_table:
            errors.append("RouterAgent requires routing_table")

        return errors

    model_config = {"extra": "forbid"}
