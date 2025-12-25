"""SQLAlchemy ORM models for database storage."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# Default hardcoded organization ID
DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000000"


class OrganizationModel(Base):
    """SQLAlchemy model for organizations table."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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
        return f"<OrganizationModel(id={self.id!r}, name={self.name!r})>"


class UserModel(Base):
    """SQLAlchemy model for users table."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Organization (hardcoded to default org for now)
    org_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id"),
        nullable=False,
        default=DEFAULT_ORG_ID,
    )

    # Tracking
    invited_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
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
        return f"<UserModel(id={self.id!r}, email={self.email!r}, is_superuser={self.is_superuser})>"


class UserInviteModel(Base):
    """SQLAlchemy model for user invites table."""

    __tablename__ = "user_invites"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    invite_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    invited_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    used_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<UserInviteModel(id={self.id!r}, email={self.email!r}, is_used={self.is_used})>"


class RefreshTokenModel(Base):
    """SQLAlchemy model for refresh tokens."""

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AgentModel(Base):
    """SQLAlchemy model for agents table."""

    __tablename__ = "agents"

    # Primary key
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Owner - each user owns their own agents
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

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


class MCPServerModel(Base):
    """SQLAlchemy model for MCP servers table.

    Stores MCP server configurations. Credentials are NOT stored here -
    only a reference to the vault where credentials are securely stored.
    """

    __tablename__ = "mcp_servers"

    # Primary key
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Owner - each user owns their own MCP servers
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Server info
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    template: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="disconnected")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Vault reference for credentials (NOT the actual credentials!)
    secret_ref: Mapped[str] = mapped_column(String(500), nullable=False)

    # OAuth token reference (for cascade delete when server is removed)
    oauth_token_ref: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

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

    # Owner - each user owns their own workflows
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

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

    # Owner - track who executed the workflow
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

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


class KnowledgeBaseModel(Base):
    """SQLAlchemy model for knowledge bases.

    A knowledge base is a collection of documents that can be searched
    using vector similarity. Used by RAGAgent and FullAgent types.
    """

    __tablename__ = "knowledge_bases"

    # Primary key
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Owner - each user owns their own knowledge bases
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Vector store configuration
    collection_name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    embedding_model: Mapped[str] = mapped_column(
        String(100), nullable=False, default="text-embedding-3-small"
    )

    # Stats
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Status: active, indexing, error
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
        return f"<KnowledgeBaseModel(id={self.id!r}, name={self.name!r}, docs={self.document_count})>"


class APIKeyModel(Base):
    """SQLAlchemy model for user API keys.

    API keys are used for programmatic access to the API.
    The key itself is hashed for security - we only store the hash.
    """

    __tablename__ = "api_keys"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Owner - each user owns their own API keys
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Key info
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)  # First 8 chars for display
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<APIKeyModel(id={self.id!r}, name={self.name!r}, prefix={self.key_prefix!r})>"


class KnowledgeDocumentModel(Base):
    """SQLAlchemy model for documents within a knowledge base.

    Tracks individual documents uploaded to a knowledge base,
    their processing status, and chunk counts.
    """

    __tablename__ = "knowledge_documents"

    # Primary key
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Reference to knowledge base
    knowledge_base_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File info
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, txt, md, docx
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # local storage path

    # Processing info
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Status: pending, processing, indexed, error
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<KnowledgeDocumentModel(id={self.id!r}, filename={self.filename!r}, status={self.status!r})>"
