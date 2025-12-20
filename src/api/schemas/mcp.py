"""API schemas for MCP (Model Context Protocol) servers."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.mcp.models import ServerStatus


# ========== Catalog Schemas ==========


class CredentialSpecSchema(BaseModel):
    """Schema for credential specification."""

    name: str
    description: str
    sensitive: bool
    header_name: Optional[str] = None


class CatalogTemplateSchema(BaseModel):
    """Schema for MCP server template from catalog."""

    id: str
    name: str
    url_template: Optional[str] = None
    auth_type: str
    token_guide_url: Optional[str] = None
    scopes: List[str] = []
    credentials_required: List[CredentialSpecSchema]
    credentials_optional: List[CredentialSpecSchema] = []
    tools: List[str] = []


class CatalogListResponse(BaseModel):
    """Response containing catalog templates."""

    servers: List[CatalogTemplateSchema]
    total: int


# ========== Server Management Schemas ==========


class CreateServerFromTemplateRequest(BaseModel):
    """Request to create MCP server from catalog template."""

    template: str = Field(..., description="Template ID from catalog")
    name: str = Field(..., min_length=1, max_length=200)
    credentials: Dict[str, str] = Field(
        ...,
        description="Credentials as key-value pairs (e.g., GOOGLE_REFRESH_TOKEN)",
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Additional non-sensitive headers",
    )


class CreateCustomServerRequest(BaseModel):
    """Request to create custom MCP server."""

    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., description="MCP server URL (Streamable HTTP endpoint)")
    credentials: Dict[str, str] = Field(
        default_factory=dict,
        description="Credentials as key-value pairs",
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Additional HTTP headers",
    )


class MCPServerResponse(BaseModel):
    """Response containing MCP server details."""

    id: str
    name: str
    template: Optional[str] = None
    url: str
    status: ServerStatus
    created_at: datetime
    last_used: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class MCPServerListResponse(BaseModel):
    """Response containing list of MCP servers."""

    servers: List[MCPServerResponse]
    total: int


class MCPServerToolSchema(BaseModel):
    """Schema for tool provided by MCP server."""

    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPServerDetailResponse(BaseModel):
    """Detailed response with server info and available tools."""

    id: str
    name: str
    template: Optional[str] = None
    url: str
    status: ServerStatus
    created_at: datetime
    last_used: Optional[datetime] = None
    error_message: Optional[str] = None
    tools: List[MCPServerToolSchema] = []

    class Config:
        from_attributes = True


# ========== Health & Status Schemas ==========


class ServerHealthStatus(BaseModel):
    """Health status for a single server."""

    server_id: str
    name: str
    status: ServerStatus
    error: Optional[str] = None


class MCPHealthResponse(BaseModel):
    """Response containing health status of all MCP servers."""

    servers: List[ServerHealthStatus]
    total_active: int
    total_error: int
    total_disconnected: int
