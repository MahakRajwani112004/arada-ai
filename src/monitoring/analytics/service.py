"""Analytics Service - high-level interface for recording and querying analytics."""
import asyncio
from functools import lru_cache
from typing import List, Optional

from src.config.logging import get_logger
from src.config.settings import get_settings
from src.storage.database import get_async_session

from .cost_calculator import calculate_cost
from .repository import AnalyticsRepository

logger = get_logger(__name__)
settings = get_settings()


class AnalyticsService:
    """
    Service for recording analytics data.

    Uses fire-and-forget pattern for recording to avoid blocking
    the main request flow. Errors are logged but not raised.
    """

    async def record_llm_usage(
        self,
        user_id: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        success: bool,
        request_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Record LLM usage to database.

        This method is designed to be called via asyncio.create_task()
        for non-blocking recording.
        """
        if not settings.analytics_enabled:
            return

        try:
            # Calculate cost
            cost_cents = calculate_cost(provider, model, prompt_tokens, completion_tokens)

            async with get_async_session() as session:
                repo = AnalyticsRepository(session)
                await repo.save_llm_usage(
                    user_id=user_id,
                    provider=provider,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost_cents=cost_cents,
                    latency_ms=latency_ms,
                    success=success,
                    request_id=request_id,
                    agent_id=agent_id,
                    workflow_id=workflow_id,
                    error_type=error_type,
                    error_message=error_message,
                )

            logger.debug(
                "llm_usage_recorded",
                user_id=user_id,
                provider=provider,
                model=model,
                tokens=prompt_tokens + completion_tokens,
                cost_cents=cost_cents,
            )

        except Exception as e:
            # Log but don't raise - analytics should never break the main flow
            logger.error(
                "llm_usage_record_failed",
                error_type=type(e).__name__,
                error=str(e),
                provider=provider,
                model=model,
            )

    async def record_agent_execution(
        self,
        user_id: str,
        agent_id: str,
        agent_type: str,
        latency_ms: int,
        success: bool,
        request_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        llm_calls_count: int = 0,
        tool_calls_count: int = 0,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Record agent execution to database.

        This method is designed to be called via asyncio.create_task()
        for non-blocking recording.
        """
        if not settings.analytics_enabled:
            return

        try:
            async with get_async_session() as session:
                repo = AnalyticsRepository(session)
                await repo.save_agent_execution(
                    user_id=user_id,
                    agent_id=agent_id,
                    agent_type=agent_type,
                    latency_ms=latency_ms,
                    success=success,
                    request_id=request_id,
                    workflow_id=workflow_id,
                    llm_calls_count=llm_calls_count,
                    tool_calls_count=tool_calls_count,
                    error_type=error_type,
                    error_message=error_message,
                )

            logger.debug(
                "agent_execution_recorded",
                user_id=user_id,
                agent_id=agent_id,
                agent_type=agent_type,
                latency_ms=latency_ms,
                success=success,
            )

        except Exception as e:
            # Log but don't raise - analytics should never break the main flow
            logger.error(
                "agent_execution_record_failed",
                error_type=type(e).__name__,
                error=str(e),
                agent_id=agent_id,
            )

    # =========================================================================
    # Query Methods (for API endpoints)
    # =========================================================================

    async def get_llm_usage_stats(
        self,
        user_id: str,
        hours: int = 24,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> dict:
        """Get aggregated LLM usage statistics for a user."""
        async with get_async_session() as session:
            repo = AnalyticsRepository(session)
            return await repo.get_llm_usage_stats(user_id, hours, provider, model)

    async def get_llm_usage_by_model(self, user_id: str, hours: int = 24) -> List[dict]:
        """Get LLM usage grouped by provider and model for a user."""
        async with get_async_session() as session:
            repo = AnalyticsRepository(session)
            return await repo.get_llm_usage_by_model(user_id, hours)

    async def get_agent_stats(
        self,
        user_id: str,
        hours: int = 24,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
    ) -> dict:
        """Get aggregated agent execution statistics for a user."""
        async with get_async_session() as session:
            repo = AnalyticsRepository(session)
            return await repo.get_agent_stats(user_id, hours, agent_id, agent_type)

    async def get_agent_stats_by_type(self, user_id: str, hours: int = 24) -> List[dict]:
        """Get agent execution stats grouped by type for a user."""
        async with get_async_session() as session:
            repo = AnalyticsRepository(session)
            return await repo.get_agent_stats_by_type(user_id, hours)


# Singleton instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get or create the analytics service singleton."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
