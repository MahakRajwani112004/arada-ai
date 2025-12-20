"""MCP configuration models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ServerStatus(str, Enum):
    """MCP server connection status."""

    ACTIVE = "active"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class CredentialSpec(BaseModel):
    """Specification for a credential field."""

    name: str
    description: str
    sensitive: bool = True
    header_name: Optional[str] = None  # HTTP header name for Streamable HTTP


class MCPServerTemplate(BaseModel):
    """Template for a catalog MCP server."""

    id: str
    name: str
    url_template: Optional[str] = None  # Remote MCP server URL
    auth_type: str = "oauth_token"  # oauth_token, api_token, none
    token_guide_url: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    credentials_required: List[CredentialSpec] = Field(default_factory=list)
    credentials_optional: List[CredentialSpec] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)


class MCPServerConfig(BaseModel):
    """Configuration for connecting to an MCP server."""

    id: str
    name: str
    url: str  # Remote MCP server URL
    headers: Dict[str, str] = Field(default_factory=dict)  # Auth headers
    template: Optional[str] = None  # Template ID from catalog


class MCPServerInstance(BaseModel):
    """User's configured MCP server instance."""

    id: str = Field(..., description="Unique server ID (e.g., srv_abc123)")
    name: str = Field(..., description="User-friendly name")
    template: Optional[str] = Field(None, description="Catalog template ID")
    url: str = Field(..., description="MCP server URL")
    status: ServerStatus = Field(default=ServerStatus.DISCONNECTED)
    secret_ref: str = Field(..., description="Vault reference for credentials")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    error_message: Optional[str] = None


class MCPToolInfo(BaseModel):
    """Information about an MCP tool."""

    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    server_id: str  # Which MCP server provides this tool


class MCPToolCallResult(BaseModel):
    """Result from calling an MCP tool."""

    success: bool
    content: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
