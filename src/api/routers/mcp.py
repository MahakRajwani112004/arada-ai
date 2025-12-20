"""MCP (Model Context Protocol) API routes."""
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status
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

        # Validate required credentials
        required_creds = {c.name for c in template.credentials_required}
        provided_creds = set(request.credentials.keys())
        missing = required_creds - provided_creds
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required credentials: {', '.join(missing)}",
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
            credentials=request.credentials,
            template=request.template,
            headers=request.headers,
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
