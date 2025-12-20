"""API dependencies - database and repository injection."""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage import PostgresAgentRepository, get_session


async def get_repository(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[PostgresAgentRepository, None]:
    """Get agent repository with database session."""
    yield PostgresAgentRepository(session)
