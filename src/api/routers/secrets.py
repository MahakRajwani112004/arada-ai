"""Secrets management API routes."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.secrets import get_secrets_manager
from src.storage import get_session
from src.storage.models import MCPServerModel

router = APIRouter(prefix="/secrets", tags=["secrets"])
logger = get_logger(__name__)


class SecretInfo(BaseModel):
    """Information about a stored secret (no values exposed)."""

    key: str
    type: str  # "oauth", "mcp", "unknown"
    provider: Optional[str] = None  # "google", etc.
    service: Optional[str] = None  # "calendar", "gmail", "drive"
    linked_server_id: Optional[str] = None
    linked_server_name: Optional[str] = None
    is_orphaned: bool = False


class SecretsListResponse(BaseModel):
    """Response containing list of secrets."""

    secrets: List[SecretInfo]
    total: int
    orphaned_count: int


class SecretsStatsResponse(BaseModel):
    """Summary statistics about secrets."""

    total: int
    oauth_tokens: int
    mcp_credentials: int
    orphaned: int


def _parse_secret_key(key: str) -> dict:
    """Parse a secret key to extract metadata.

    Examples:
        oauth/google/calendar/abc123 -> type=oauth, provider=google, service=calendar
        mcp_servers/srv_abc123 -> type=mcp
    """
    # Handle both slash-based and underscore-based formats
    if key.startswith("oauth/google/") or key.startswith("oauth_google_"):
        # oauth/google/calendar/abc123 or oauth_google_calendar_abc123
        if "/" in key:
            parts = key.split("/")
        else:
            parts = key.split("_")
        if len(parts) >= 3:
            return {
                "type": "oauth",
                "provider": "google",
                "service": parts[2] if len(parts) > 2 else None,
            }
    elif key.startswith("mcp_servers/") or key.startswith("mcp/servers/"):
        return {"type": "mcp"}

    return {"type": "unknown"}


@router.get("", response_model=SecretsListResponse)
async def list_secrets(
    session: AsyncSession = Depends(get_session),
) -> SecretsListResponse:
    """List all stored secrets with metadata.

    Returns secret keys and metadata, but never secret values.
    Includes information about which secrets are orphaned (not linked to any server).
    """
    secrets_manager = get_secrets_manager()
    keys = await secrets_manager.list_keys()

    # Get all MCP servers to check for linked secrets
    result = await session.execute(select(MCPServerModel))
    servers = {s.id: s for s in result.scalars().all()}

    # Build linked refs map
    linked_secret_refs = {}
    linked_oauth_refs = {}

    for server in servers.values():
        linked_secret_refs[server.secret_ref] = server
        if server.oauth_token_ref:
            linked_oauth_refs[server.oauth_token_ref] = server

    secrets = []
    orphaned_count = 0

    for key in keys:
        parsed = _parse_secret_key(key)
        info = SecretInfo(
            key=key,
            type=parsed.get("type", "unknown"),
            provider=parsed.get("provider"),
            service=parsed.get("service"),
        )

        # Check if linked to a server
        if key in linked_secret_refs:
            server = linked_secret_refs[key]
            info.linked_server_id = server.id
            info.linked_server_name = server.name
        elif key in linked_oauth_refs:
            server = linked_oauth_refs[key]
            info.linked_server_id = server.id
            info.linked_server_name = server.name
        else:
            # Not linked to any server - orphaned
            info.is_orphaned = True
            orphaned_count += 1

        secrets.append(info)

    return SecretsListResponse(
        secrets=secrets,
        total=len(secrets),
        orphaned_count=orphaned_count,
    )


@router.get("/stats", response_model=SecretsStatsResponse)
async def get_secrets_stats(
    session: AsyncSession = Depends(get_session),
) -> SecretsStatsResponse:
    """Get summary statistics about stored secrets."""
    secrets_manager = get_secrets_manager()
    keys = await secrets_manager.list_keys()

    # Get all MCP servers to check for linked secrets
    result = await session.execute(select(MCPServerModel))
    servers = list(result.scalars().all())

    # Build linked refs set
    linked_refs = set()
    for server in servers:
        linked_refs.add(server.secret_ref)
        if server.oauth_token_ref:
            linked_refs.add(server.oauth_token_ref)

    oauth_count = 0
    mcp_count = 0
    orphaned_count = 0

    for key in keys:
        parsed = _parse_secret_key(key)
        if parsed["type"] == "oauth":
            oauth_count += 1
        elif parsed["type"] == "mcp":
            mcp_count += 1

        if key not in linked_refs:
            orphaned_count += 1

    return SecretsStatsResponse(
        total=len(keys),
        oauth_tokens=oauth_count,
        mcp_credentials=mcp_count,
        orphaned=orphaned_count,
    )


@router.delete("/{secret_key:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_key: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete an orphaned secret.

    Only allows deletion of secrets that are not linked to any MCP server.
    This is a safety measure to prevent accidentally breaking server connections.
    """
    # Check if secret is linked to any server
    result = await session.execute(select(MCPServerModel))
    servers = list(result.scalars().all())

    for server in servers:
        if server.secret_ref == secret_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete: secret is linked to server '{server.name}' ({server.id}). Delete the server first.",
            )
        if server.oauth_token_ref == secret_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete: OAuth token is linked to server '{server.name}' ({server.id}). Delete the server first.",
            )

    # Safe to delete
    secrets_manager = get_secrets_manager()
    try:
        await secrets_manager.delete(secret_key)
        logger.info("orphaned_secret_deleted", key=secret_key)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secret '{secret_key}' not found",
        )
