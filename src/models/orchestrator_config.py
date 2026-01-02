"""Orchestrator agent configuration models."""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from src.models.routing_rules import RoutingRules


class OrchestratorMode(str, Enum):
    """How the orchestrator decides which agents to run."""

    FANOUT = "fanout"  # Classify, run relevant agents in parallel, synthesize
    LLM_DRIVEN = "llm_driven"  # LLM decides at runtime
    WORKFLOW = "workflow"  # Follow predefined workflow
    HYBRID = "hybrid"  # LLM can deviate from workflow


class AggregationStrategy(str, Enum):
    """Strategies for aggregating multi-agent results."""

    FIRST = "first"  # Return first successful result
    ALL = "all"  # Return all results
    VOTE = "vote"  # Majority voting (for classification)
    MERGE = "merge"  # Merge results into single object
    BEST = "best"  # LLM selects best result


class AgentReference(BaseModel):
    """Reference to an agent for orchestration."""

    agent_id: str = Field(..., description="ID of the agent to invoke")
    alias: Optional[str] = Field(
        None, description="Friendly name for LLM to use when calling"
    )
    description: Optional[str] = Field(
        None, description="Override description for this context"
    )


class OrchestratorConfig(BaseModel):
    """Configuration specific to OrchestratorAgent."""

    mode: OrchestratorMode = Field(
        default=OrchestratorMode.LLM_DRIVEN,
        description="How orchestrator decides agent execution",
    )

    auto_discover: bool = Field(
        default=False,
        description="If True, automatically discover all available agents instead of using available_agents list",
    )

    exclude_agent_types: List[str] = Field(
        default_factory=lambda: ["OrchestratorAgent"],
        description="Agent types to exclude when auto_discover is True (prevents orchestrator loops)",
    )

    exclude_agent_ids: List[str] = Field(
        default_factory=list,
        description="Specific agent IDs to exclude when auto_discover is True",
    )

    available_agents: List[AgentReference] = Field(
        default_factory=list,
        description="Agents available to this orchestrator (ignored if auto_discover is True)",
    )

    workflow_definition: Optional[str] = Field(
        None, description="Workflow definition ID (for workflow/hybrid modes)"
    )

    default_aggregation: AggregationStrategy = Field(
        default=AggregationStrategy.ALL,
        description="Default strategy for aggregating results",
    )

    max_parallel: int = Field(
        default=5, description="Maximum concurrent agent executions"
    )

    max_depth: int = Field(
        default=3, description="Maximum nesting depth for agent calls"
    )

    allow_self_reference: bool = Field(
        default=False, description="Whether orchestrator can call itself"
    )

    routing_rules: Optional[RoutingRules] = Field(
        default=None,
        description="Explicit routing rules for hybrid mode (pattern -> agent mapping)",
    )

    max_same_agent_calls: int = Field(
        default=3,
        description="Maximum times the same agent can be called consecutively (prevents loops)",
    )

    max_iterations: int = Field(
        default=15,
        description="Maximum number of LLM-tool call iterations before returning",
    )
