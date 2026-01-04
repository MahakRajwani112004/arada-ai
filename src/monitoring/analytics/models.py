"""SQLAlchemy ORM models for monitoring analytics."""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.storage.models import Base


class LLMUsageModel(Base):
    """SQLAlchemy model for LLM usage tracking.

    Stores every LLM API call with tokens, cost, and latency.
    Data is kept forever for analytics and cost reporting.
    """

    __tablename__ = "llm_usage"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # User ownership - all analytics are user-scoped
    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # Correlation IDs
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    agent_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    workflow_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )

    # LLM call details
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # "openai" | "anthropic"
    model: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # "gpt-4o" | "claude-3-5-sonnet"

    # Token usage
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Cost in cents (for easy aggregation)
    cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Performance
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Status
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<LLMUsageModel(id={self.id!r}, provider={self.provider!r}, "
            f"model={self.model!r}, tokens={self.total_tokens})>"
        )


class AgentExecutionModel(Base):
    """SQLAlchemy model for agent execution tracking.

    Stores every agent execution with timing and success status.
    Data is kept forever for analytics and debugging.
    """

    __tablename__ = "agent_executions"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # User ownership - all analytics are user-scoped
    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # Correlation IDs
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    workflow_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )

    # Agent details
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    agent_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # llm, rag, tool, full, router, orchestrator, simple

    # Performance
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Call counts (for agents that make multiple calls)
    llm_calls_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tool_calls_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Status
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # === Overview Tab Fields (MVP) ===

    # Input/output previews for display in execution list
    input_preview: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="First 200 chars of sanitized user input"
    )
    output_preview: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="First 500 chars of agent output"
    )

    # Token and cost tracking at execution level
    total_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Total tokens used in this execution"
    )
    total_cost_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Total cost in cents for this execution"
    )

    # Parent execution for nested agent calls (orchestrator -> sub-agent)
    parent_execution_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True,
        comment="Parent execution ID for nested agent calls"
    )

    # Full execution metadata (tool calls, agent results, etc.)
    execution_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True,
        comment="Full execution metadata including tool_calls, agent_results, etc."
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AgentExecutionModel(id={self.id!r}, agent_id={self.agent_id!r}, "
            f"type={self.agent_type!r}, success={self.success})>"
        )


# Type aliases for cleaner imports
LLMUsage = LLMUsageModel
AgentExecution = AgentExecutionModel
