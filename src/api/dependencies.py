"""API dependencies - database and repository injection."""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.mcp import MCPManager, get_mcp_manager as _get_mcp_manager
from src.mcp.repository import MCPServerRepository
from src.skills.repository import SkillRepository
from src.storage import PostgresAgentRepository, get_session
from src.storage.workflow_repository import WorkflowRepository
from src.storage.approval_repository import ApprovalRepository
from src.storage.schedule_repository import ScheduleRepository


async def get_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
) -> AsyncGenerator[PostgresAgentRepository, None]:
    """Get agent repository with database session, scoped to current user."""
    user_id = current_user.id if current_user else None
    yield PostgresAgentRepository(session, user_id=user_id)


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
) -> AsyncGenerator[PostgresAgentRepository, None]:
    """Get agent repository scoped to current user (requires auth)."""
    if current_user is None:
        raise ValueError("Authentication required")
    yield PostgresAgentRepository(session, user_id=current_user.id)


async def get_workflow_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
) -> AsyncGenerator[WorkflowRepository, None]:
    """Get workflow repository with database session, scoped to current user."""
    user_id = current_user.id if current_user else None
    yield WorkflowRepository(session, user_id=user_id)


async def get_mcp_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
) -> AsyncGenerator[MCPServerRepository, None]:
    """Get MCP server repository with database session, scoped to current user."""
    user_id = current_user.id if current_user else None
    yield MCPServerRepository(session, user_id=user_id)


def get_mcp_manager() -> MCPManager:
    """Get the MCP manager singleton."""
    return _get_mcp_manager()


async def get_skill_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
) -> AsyncGenerator[SkillRepository, None]:
    """Get skill repository with database session, scoped to current user."""
    user_id = current_user.id if current_user else None
    yield SkillRepository(session, user_id=user_id)


async def get_approval_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
) -> AsyncGenerator[ApprovalRepository, None]:
    """Get approval repository with database session, scoped to current user."""
    user_id = current_user.id if current_user else None
    yield ApprovalRepository(session, user_id=user_id)


async def get_schedule_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = None,
) -> AsyncGenerator[ScheduleRepository, None]:
    """Get schedule repository with database session, scoped to current user."""
    user_id = current_user.id if current_user else None
    yield ScheduleRepository(session, user_id=user_id)
