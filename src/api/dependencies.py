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
    current_user: CurrentUser = ...,  # Required - no default
) -> AsyncGenerator[PostgresAgentRepository, None]:
    """Get agent repository with database session, scoped to current user.

    Authentication is required - all agent operations are user-scoped.
    """
    yield PostgresAgentRepository(session, user_id=current_user.id)


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = ...,  # Required - no default
) -> AsyncGenerator[PostgresAgentRepository, None]:
    """Get agent repository scoped to current user (requires auth).

    Alias for get_repository - kept for backward compatibility.
    """
    yield PostgresAgentRepository(session, user_id=current_user.id)


async def get_workflow_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = ...,  # Required - no default
) -> AsyncGenerator[WorkflowRepository, None]:
    """Get workflow repository with database session, scoped to current user.

    Authentication is required - all workflow operations are user-scoped.
    """
    yield WorkflowRepository(session, user_id=current_user.id)


async def get_mcp_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = ...,  # Required - no default
) -> AsyncGenerator[MCPServerRepository, None]:
    """Get MCP server repository with database session, scoped to current user.

    Authentication is required - all MCP server operations are user-scoped.
    """
    yield MCPServerRepository(session, user_id=current_user.id)


def get_mcp_manager() -> MCPManager:
    """Get the MCP manager singleton."""
    return _get_mcp_manager()


async def get_skill_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = ...,  # Required - no default
) -> AsyncGenerator[SkillRepository, None]:
    """Get skill repository with database session, scoped to current user.

    Authentication is required - all skill operations are user-scoped.
    """
    yield SkillRepository(session, user_id=current_user.id)


async def get_authenticated_skill_repository(
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = ...,  # Required - no default
) -> AsyncGenerator[SkillRepository, None]:
    """Get skill repository that requires authentication.

    Use this for endpoints that modify skills (create, update, delete, upload files).
    """
    yield SkillRepository(session, user_id=current_user.id)


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
