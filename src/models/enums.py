"""Agent type enumerations."""
from enum import Enum


class AgentType(str, Enum):
    """Available agent types - maps to base agent classes."""

    SIMPLE = "SimpleAgent"
    LLM = "LLMAgent"
    RAG = "RAGAgent"
    TOOL = "ToolAgent"
    FULL = "FullAgent"
    ROUTER = "RouterAgent"
    ORCHESTRATOR = "OrchestratorAgent"


class ResponseType(str, Enum):
    """Types of responses an agent can return."""

    TEXT = "text"
    JSON = "json"
    STREAM = "stream"
    ROUTE = "route"


class SafetyLevel(str, Enum):
    """Safety check levels."""

    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"
