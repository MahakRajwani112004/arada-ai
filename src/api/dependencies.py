"""API dependencies - database and repository injection."""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.mcp import MCPManager, get_mcp_manager as _get_mcp_manager
from src.mcp.repository import MCPServerRepository
from src.storage import PostgresAgentRepository, get_session
from src.storage.workflow_repository import WorkflowRepository


async def get_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[PostgresAgentRepository, None]:
    """Get agent repository with database session."""
    yield PostgresAgentRepository(session)


async def get_workflow_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[WorkflowRepository, None]:
    """Get workflow repository with database session."""
    yield WorkflowRepository(session)


async def get_mcp_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[MCPServerRepository, None]:
    """Get MCP server repository with database session."""
    yield MCPServerRepository(session)


def get_mcp_manager() -> MCPManager:
    """Get the MCP manager singleton."""
    return _get_mcp_manager()
