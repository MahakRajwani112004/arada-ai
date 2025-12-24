"""MCP (Model Context Protocol) API routes."""
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.mcp import (
    CatalogListResponse,
    CatalogTemplateSchema,
    CreateCustomServerRequest,
    CreateServerFromTemplateRequest,
    CredentialSpecSchema,
    MCPHealthResponse,
    MCPServerDetailResponse,
    MCPServerListResponse,
    MCPServerResponse,
    MCPServerToolSchema,
    ServerHealthStatus,
)
from src.config.logging import get_logger
from src.mcp import MCPManager, get_mcp_manager
from src.mcp.catalog import get_catalog, get_template
from src.mcp.models import ServerStatus
from src.mcp.repository import MCPServerRepository
from src.secrets import get_secrets_manager
from src.storage import get_session

logger = get_logger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


async def get_mcp_repository(
    session: AsyncSession = Depends(get_session),
) -> MCPServerRepository:
    """Get MCP server repository with database session."""
    return MCPServerRepository(session)


# ========== Catalog Endpoints ==========


@router.get("/catalog", response_model=CatalogListResponse)
async def list_catalog() -> CatalogListResponse:
    """List all available MCP server templates from catalog."""
    catalog = get_catalog()
    templates = [
        CatalogTemplateSchema(
            id=t.id,
            name=t.name,
            url_template=t.url_template,
            auth_type=t.auth_type,
            token_guide_url=t.token_guide_url,
            scopes=t.scopes,
            credentials_required=[
                CredentialSpecSchema(
                    name=c.name,
                    description=c.description,
                    sensitive=c.sensitive,
                    header_name=c.header_name,
                )
                for c in t.credentials_required
            ],
            credentials_optional=[
                CredentialSpecSchema(
                    name=c.name,
                    description=c.description,
                    sensitive=c.sensitive,
                    header_name=c.header_name,
                )
                for c in t.credentials_optional
            ],
            tools=t.tools,
        )
        for t in catalog.values()
    ]

    return CatalogListResponse(servers=templates, total=len(templates))


@router.get("/catalog/{template_id}", response_model=CatalogTemplateSchema)
async def get_catalog_template(template_id: str) -> CatalogTemplateSchema:
    """Get details of a specific catalog template."""
    template = get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found in catalog",
        )

    return CatalogTemplateSchema(
        id=template.id,
        name=template.name,
        url_template=template.url_template,
        auth_type=template.auth_type,
        token_guide_url=template.token_guide_url,
        scopes=template.scopes,
        credentials_required=[
            CredentialSpecSchema(
                name=c.name,
                description=c.description,
                sensitive=c.sensitive,
                header_name=c.header_name,
            )
            for c in template.credentials_required
        ],
        credentials_optional=[
            CredentialSpecSchema(
                name=c.name,
                description=c.description,
                sensitive=c.sensitive,
                header_name=c.header_name,
            )
            for c in template.credentials_optional
        ],
        tools=template.tools,
    )


# ========== Server Management Endpoints ==========


@router.post("/servers", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    request: Union[CreateServerFromTemplateRequest, CreateCustomServerRequest],
    repository: MCPServerRepository = Depends(get_mcp_repository),
    manager: MCPManager = Depends(get_mcp_manager),
) -> MCPServerResponse:
    """Create a new MCP server configuration.

    Supports two modes:
    - From template: Provide `template` field with catalog template ID
    - Custom: Provide `url` field with MCP server URL

    For template-based servers with OAuth, you can provide `oauth_token_ref` instead of raw credentials.
    The token_ref is obtained from the OAuth callback endpoint.
    """
    # Determine if this is template-based or custom
    if isinstance(request, CreateServerFromTemplateRequest):
        # Template-based server
        template = get_template(request.template)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template '{request.template}' not found in catalog",
            )

        # Resolve credentials from oauth_token_ref if provided
        credentials = dict(request.credentials)
        if request.oauth_token_ref:
            try:
                secrets_manager = get_secrets_manager()
                oauth_data = await secrets_manager.retrieve(request.oauth_token_ref)

                # Map OAuth refresh_token to the template's expected credential name
                # OAuth stores: {"refresh_token": "...", "service": "...", "provider": "..."}
                # Template expects: {"GOOGLE_REFRESH_TOKEN": "..."}
                if "refresh_token" in oauth_data:
                    # Find the first required credential that looks like a refresh token
                    for cred_spec in template.credentials_required:
                        if "REFRESH_TOKEN" in cred_spec.name.upper():
                            credentials[cred_spec.name] = oauth_data["refresh_token"]
                            logger.info(
                                "oauth_token_resolved",
                                token_ref=request.oauth_token_ref,
                                credential_name=cred_spec.name,
                            )
                            break
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"OAuth token reference '{request.oauth_token_ref}' not found or expired",
                )
            except Exception as e:
                logger.error("oauth_token_resolution_failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to resolve OAuth token: {str(e)}",
                )

        # Validate required credentials
        required_creds = {c.name for c in template.credentials_required}
        provided_creds = set(credentials.keys())
        missing = required_creds - provided_creds
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required credentials: {', '.join(missing)}. Provide them directly or use oauth_token_ref.",
            )

        url = template.url_template
        if not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template '{request.template}' requires a custom URL",
            )

        # Create server in database (credentials go to vault)
        instance = await repository.create(
            name=request.name,
            url=url,
            credentials=credentials,  # Use resolved credentials (from oauth_token_ref or direct)
            template=request.template,
            headers=request.headers,
            oauth_token_ref=request.oauth_token_ref,  # Store for cascade delete
        )
    else:
        # Custom server
        instance = await repository.create(
            name=request.name,
            url=request.url,
            credentials=request.credentials,
            template=None,
            headers=request.headers,
        )

    # Connect to server via MCP manager
    try:
        config = await repository.get_config(instance.id)
        if config:
            await manager.add_server(config)
            # Update status to active
            instance = await repository.update_status(instance.id, ServerStatus.ACTIVE)

        logger.info(
            "mcp_server_created",
            server_id=instance.id,
            name=instance.name,
            template=instance.template,
        )
    except Exception as e:
        # Update status to error but don't fail the request
        instance = await repository.update_status(
            instance.id, ServerStatus.ERROR, str(e)
        )
        logger.error(
            "mcp_server_connection_failed",
            server_id=instance.id,
            error=str(e),
        )

    return MCPServerResponse(
        id=instance.id,
        name=instance.name,
        template=instance.template,
        url=instance.url,
        status=instance.status,
        created_at=instance.created_at,
        last_used=instance.last_used,
        error_message=instance.error_message,
    )


@router.get("/servers", response_model=MCPServerListResponse)
async def list_servers(
    repository: MCPServerRepository = Depends(get_mcp_repository),
) -> MCPServerListResponse:
    """List all configured MCP servers."""
    instances = await repository.list_all()
    servers = [
        MCPServerResponse(
            id=i.id,
            name=i.name,
            template=i.template,
            url=i.url,
            status=i.status,
            created_at=i.created_at,
            last_used=i.last_used,
            error_message=i.error_message,
        )
        for i in instances
    ]
    return MCPServerListResponse(servers=servers, total=len(servers))


@router.get("/servers/{server_id}", response_model=MCPServerDetailResponse)
async def get_server(
    server_id: str,
    repository: MCPServerRepository = Depends(get_mcp_repository),
    manager: MCPManager = Depends(get_mcp_manager),
) -> MCPServerDetailResponse:
    """Get MCP server details including available tools."""
    instance = await repository.get(server_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_id}' not found",
        )

    # Get tools from manager if connected
    tools = []
    try:
        tool_infos = await manager.get_tools(server_id)
        tools = [
            MCPServerToolSchema(
                name=t.name,
                description=t.description,
                input_schema=t.input_schema,
            )
            for t in tool_infos
        ]
    except Exception:
        pass  # Server might not be connected

    return MCPServerDetailResponse(
        id=instance.id,
        name=instance.name,
        template=instance.template,
        url=instance.url,
        status=instance.status,
        created_at=instance.created_at,
        last_used=instance.last_used,
        error_message=instance.error_message,
        tools=tools,
    )


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: str,
    repository: MCPServerRepository = Depends(get_mcp_repository),
    manager: MCPManager = Depends(get_mcp_manager),
) -> None:
    """Delete an MCP server configuration."""
    # Remove from manager first (disconnects and unregisters tools)
    await manager.remove_server(server_id)

    # Delete from database and vault
    deleted = await repository.delete(server_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_id}' not found",
        )

    logger.info("mcp_server_deleted", server_id=server_id)


# ========== Reconnect Endpoints ==========

# Map template IDs to OAuth service names
OAUTH_SERVICE_MAP = {
    "google-calendar": "calendar",
    "gmail": "gmail",
    "google-drive": "drive",
}


@router.post("/servers/{server_id}/reconnect")
async def reconnect_server(
    server_id: str,
    repository: MCPServerRepository = Depends(get_mcp_repository),
) -> dict:
    """Get OAuth URL to reconnect/re-authenticate an MCP server.

    For OAuth-based servers, returns an authorization URL.
    The user should be redirected to this URL to re-authenticate.
    After OAuth completes, call PUT /servers/{server_id}/credentials to update.
    """
    instance = await repository.get(server_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_id}' not found",
        )

    # Check if this is an OAuth-based template
    if not instance.template or instance.template not in OAUTH_SERVICE_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reconnect is only supported for OAuth-based integrations (Google Calendar, Gmail, Drive)",
        )

    service = OAUTH_SERVICE_MAP[instance.template]

    # Import here to avoid circular imports
    from src.api.routers.oauth import _create_google_flow, GOOGLE_SCOPES

    scopes = GOOGLE_SCOPES.get(service, [])
    flow = _create_google_flow(scopes)

    # Include server_id in state for the callback to know which server to update
    state = f"{service}:reconnect:{server_id}"

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state,
    )

    logger.info("mcp_server_reconnect_initiated", server_id=server_id, service=service)

    return {
        "authorization_url": auth_url,
        "server_id": server_id,
        "service": service,
    }


@router.put("/servers/{server_id}/credentials", response_model=MCPServerResponse)
async def update_server_credentials(
    server_id: str,
    oauth_token_ref: str = Query(..., description="New OAuth token reference from OAuth callback"),
    repository: MCPServerRepository = Depends(get_mcp_repository),
    manager: MCPManager = Depends(get_mcp_manager),
) -> MCPServerResponse:
    """Update server credentials after reconnection.

    Called by the frontend after OAuth reconnection completes.
    Updates the server's credentials in vault and reconnects.
    """
    instance = await repository.get(server_id)
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_id}' not found",
        )

    # Get the new OAuth token from vault
    try:
        secrets_manager = get_secrets_manager()
        oauth_data = await secrets_manager.retrieve(oauth_token_ref)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth token reference '{oauth_token_ref}' not found or expired",
        )

    # Get template to map credentials
    template = get_template(instance.template) if instance.template else None
    credentials = {}

    if template and "refresh_token" in oauth_data:
        for cred_spec in template.credentials_required:
            if "REFRESH_TOKEN" in cred_spec.name.upper():
                credentials[cred_spec.name] = oauth_data["refresh_token"]
                break

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not map OAuth token to server credentials",
        )

    # Update credentials in repository
    updated = await repository.update_credentials(
        server_id=server_id,
        credentials=credentials,
        oauth_token_ref=oauth_token_ref,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update server credentials",
        )

    # Reconnect to server
    try:
        await manager.remove_server(server_id)
        config = await repository.get_config(server_id)
        if config:
            await manager.add_server(config)
            updated = await repository.update_status(server_id, ServerStatus.ACTIVE)
        logger.info("mcp_server_reconnected", server_id=server_id)
    except Exception as e:
        updated = await repository.update_status(server_id, ServerStatus.ERROR, str(e))
        logger.error("mcp_server_reconnect_failed", server_id=server_id, error=str(e))

    return MCPServerResponse(
        id=updated.id,
        name=updated.name,
        template=updated.template,
        url=updated.url,
        status=updated.status,
        created_at=updated.created_at,
        last_used=updated.last_used,
        error_message=updated.error_message,
    )


# ========== Health Endpoints ==========


@router.get("/health", response_model=MCPHealthResponse)
async def check_health(
    repository: MCPServerRepository = Depends(get_mcp_repository),
    manager: MCPManager = Depends(get_mcp_manager),
) -> MCPHealthResponse:
    """Check health status of all MCP servers."""
    instances = await repository.list_all()
    health_status = await manager.health_check()

    servers = []
    total_active = 0
    total_error = 0
    total_disconnected = 0

    for instance in instances:
        status = health_status.get(instance.id, instance.status)

        if status == ServerStatus.ACTIVE:
            total_active += 1
        elif status == ServerStatus.ERROR:
            total_error += 1
        else:
            total_disconnected += 1

        servers.append(
            ServerHealthStatus(
                server_id=instance.id,
                name=instance.name,
                status=status,
                error=instance.error_message,
            )
        )

    return MCPHealthResponse(
        servers=servers,
        total_active=total_active,
        total_error=total_error,
        total_disconnected=total_disconnected,
    )
