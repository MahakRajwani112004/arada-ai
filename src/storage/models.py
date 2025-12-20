"""SQLAlchemy ORM models for database storage."""
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
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
