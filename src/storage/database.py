"""Database connection and session management."""
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import get_settings
from src.config.logging import get_logger
from src.storage.models import Base, DEFAULT_ORG_ID, OrganizationModel, UserModel

logger = get_logger(__name__)

# Global engine (initialized on startup)
_engine = None
_session_factory = None


async def _seed_default_org_and_superuser(session: AsyncSession) -> None:
    """Seed the default organization and superuser if they don't exist."""
    settings = get_settings()

    # Check if default org exists
    result = await session.execute(
        select(OrganizationModel).where(OrganizationModel.id == DEFAULT_ORG_ID)
    )
    org = result.scalar_one_or_none()

    if org is None:
        # Create default organization
        org = OrganizationModel(
            id=DEFAULT_ORG_ID,
            name="Default Organization",
            slug="default",
        )
        session.add(org)
        logger.info("default_org_created", org_id=DEFAULT_ORG_ID)

    # Check if superuser should be created
    if settings.superuser_email and settings.superuser_password:
        result = await session.execute(
            select(UserModel).where(UserModel.email == settings.superuser_email.lower())
        )
        existing_user = result.scalar_one_or_none()

        if existing_user is None:
            # Import here to avoid circular imports
            from src.auth.password import hash_password

            superuser = UserModel(
                email=settings.superuser_email.lower(),
                password_hash=hash_password(settings.superuser_password),
                display_name="Super Admin",
                is_superuser=True,
                org_id=DEFAULT_ORG_ID,
            )
            session.add(superuser)
            logger.info("superuser_created", email=settings.superuser_email)

    await session.commit()


async def init_database() -> None:
    """Initialize database engine and create tables."""
    global _engine, _session_factory

    settings = get_settings()

    # Use settings for pool configuration
    pool_size = settings.db_pool_size if settings.is_production else 5
    max_overflow = settings.db_max_overflow if settings.is_production else 10

    _engine = create_async_engine(
        settings.database_url,
        echo=settings.is_development,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=settings.db_pool_recycle,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Create tables if they don't exist
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default org and superuser
    async with _session_factory() as session:
        await _seed_default_org_and_superuser(session)

    logger.info(
        "database_initialized",
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=settings.db_pool_recycle,
    )


async def close_database() -> None:
    """Close database connections."""
    global _engine, _session_factory

    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(
                "database_transaction_failed",
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True,
            )
            await session.rollback()
            raise


from contextlib import asynccontextmanager


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session as async context manager (for non-DI use)."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
