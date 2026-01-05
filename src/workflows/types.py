"""Workflow type definitions - Input and Output dataclasses."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentWorkflowInput:
    """Input for agent workflow."""

    agent_id: str
    agent_type: str
    user_input: str
    user_id: str  # Required for user-level analytics
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    session_id: Optional[str] = None

    # Agent configuration (flattened for workflow)
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024

    # System prompt (pre-built from config)
    system_prompt: str = ""

    # Safety settings
    safety_level: str = "standard"
    blocked_topics: List[str] = field(default_factory=list)

    # RAG settings (for RAGAgent/FullAgent)
    knowledge_collection: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    top_k: int = 5
    similarity_threshold: Optional[float] = None

    # Tool settings (for ToolAgent/FullAgent)
    enabled_tools: List[str] = field(default_factory=list)

    # Router settings (for RouterAgent)
    routing_table: Dict[str, str] = field(default_factory=dict)

    # Orchestrator settings (for OrchestratorAgent)
    orchestrator_mode: str = "llm_driven"
    orchestrator_available_agents: List[Dict[str, Any]] = field(default_factory=list)
    orchestrator_max_parallel: int = 5
    orchestrator_max_depth: int = 3
    orchestrator_aggregation: str = "all"
    # Routing rules for hybrid mode (pattern -> agent mapping)
    orchestrator_routing_rules: Optional[Dict[str, Any]] = None
    # Max consecutive calls to same agent (prevents loops)
    orchestrator_max_same_agent_calls: int = 3

    # Fanout settings (for fanout mode)
    fanout_classifier_model: str = "gpt-4o-mini"  # Fast model for agent selection
    fanout_classifier_provider: str = "openai"
    fanout_synthesis_prompt: Optional[str] = None  # Custom synthesis instructions

    # Workflow definition (for WORKFLOW mode)
    # JSON structure: {"id": "...", "steps": [...], "entry_step": "..."}
    workflow_definition: Optional[Dict[str, Any]] = None

    # Action Validator settings (enabled by default for ToolAgent/FullAgent)
    # Validates that tools are called when expected and retries with forced tool_choice
    enable_action_validator: bool = True
    validator_model: str = "gpt-4o-mini"  # Fast/cheap model for validation
    validator_provider: str = "openai"
    max_validation_retries: int = 1  # Number of retry attempts with forced tool_choice

    # Agent description for validator context (extracted from config)
    agent_description: str = ""


@dataclass
class AgentWorkflowOutput:
    """Output from agent workflow."""

    content: str
    agent_id: str
    agent_type: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Clarification fields - for interactive follow-up questions
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    clarification_options: Optional[List[str]] = None
