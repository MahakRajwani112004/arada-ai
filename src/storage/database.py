"""Database connection and session management."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import get_settings
from src.config.logging import get_logger
from src.storage.models import Base

logger = get_logger(__name__)

# Global engine (initialized on startup)
_engine = None
_session_factory = None


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
