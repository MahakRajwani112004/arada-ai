"""SQLAlchemy ORM models for database storage."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class AgentModel(Base):
    """SQLAlchemy model for agents table."""

    __tablename__ = "agents"

    # Primary key
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Indexed columns for queries
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Full config as JSONB for flexibility
    config_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<AgentModel(id={self.id!r}, name={self.name!r}, type={self.agent_type!r})>"


class WorkflowDefinitionModel(Base):
    """SQLAlchemy model for workflow definitions table."""

    __tablename__ = "workflow_definitions"

    # Primary key
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Indexed columns for queries
    name: Mapped[str] = mapped_column(String(200), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Workflow structure as JSONB
    steps_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    entry_step: Mapped[str] = mapped_column(String(100), nullable=True)
    context_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True, default={})

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<WorkflowDefinitionModel(id={self.id!r}, name={self.name!r})>"


class MCPServerModel(Base):
    """SQLAlchemy model for MCP servers table.

    Stores MCP server configurations. Credentials are NOT stored here -
    only a reference to the vault where credentials are securely stored.
    """

    __tablename__ = "mcp_servers"

    # Primary key
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Server info
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    template: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="disconnected")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Vault reference for credentials (NOT the actual credentials!)
    secret_ref: Mapped[str] = mapped_column(String(500), nullable=False)

    # Headers config (non-sensitive headers only)
    headers_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default={})

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<MCPServerModel(id={self.id!r}, name={self.name!r}, status={self.status!r})>"


class WorkflowModel(Base):
    """SQLAlchemy model for workflows table.

    Stores workflow definitions independently from agents.
    Workflows reference agents by ID rather than embedding them.
    """

    __tablename__ = "workflows"

    # Primary key (pattern: [a-zA-Z][a-zA-Z0-9_-]{0,99})
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Categorization
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, default="general", index=True
    )
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False, default=[])

    # Template relationship
    is_template: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    source_template_id: Mapped[Optional[str]] = mapped_column(
        String(100), ForeignKey("workflows.id"), nullable=True
    )

    # The actual workflow definition as JSONB
    definition_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Version tracking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<WorkflowModel(id={self.id!r}, name={self.name!r}, version={self.version})>"


class WorkflowExecutionModel(Base):
    """SQLAlchemy model for workflow execution history.

    Tracks each execution of a workflow including status, inputs, outputs,
    and step-by-step results for debugging and analytics.
    """

    __tablename__ = "workflow_executions"

    # Primary key (format: execution-{uuid})
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Reference to workflow
    workflow_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("workflows.id"), nullable=False, index=True
    )

    # Temporal workflow ID for correlation
    temporal_workflow_id: Mapped[str] = mapped_column(String(200), nullable=False)

    # Execution status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="RUNNING", index=True
    )  # RUNNING, COMPLETED, FAILED, CANCELLED

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Input/Output
    input_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    output_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Step tracking
    steps_executed: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=False, default=[]
    )
    step_results: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default={}
    )

    # Metadata
    triggered_by: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # user, api, schedule
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<WorkflowExecutionModel(id={self.id!r}, workflow_id={self.workflow_id!r}, status={self.status!r})>"
