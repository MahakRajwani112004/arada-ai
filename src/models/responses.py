"""Agent context and response models."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentContext:
    """Runtime context passed to agent execution."""

    user_input: str
    session_id: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_input": self.user_input,
            "session_id": self.session_id,
            "conversation_history": self.conversation_history,
            "metadata": self.metadata,
        }


@dataclass
class AgentResponse:
    """Response from agent execution."""

    content: str
    confidence: float = 1.0
    sources: Optional[List[str]] = None
    tool_calls_made: Optional[List[Dict[str, Any]]] = None
    needs_confirmation: bool = False
    route_to_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize optional fields."""
        if self.sources is None:
            self.sources = []
        if self.tool_calls_made is None:
            self.tool_calls_made = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "confidence": self.confidence,
            "sources": self.sources,
            "tool_calls_made": self.tool_calls_made,
            "needs_confirmation": self.needs_confirmation,
            "route_to_agent": self.route_to_agent,
            "metadata": self.metadata,
        }


@dataclass
class Message:
    """Chat message."""

    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"role": self.role, "content": self.content}
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result
