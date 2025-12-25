"""Analytics Repository - stores monitoring data to PostgreSQL."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AgentExecutionModel, LLMUsageModel


class AnalyticsRepository:
    """Repository for storing and querying analytics data."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    # =========================================================================
    # LLM Usage
    # =========================================================================

    async def save_llm_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_cents: int,
        latency_ms: int,
        success: bool,
        request_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> str:
        """Save LLM usage record. Returns record ID."""
        record = LLMUsageModel(
            request_id=request_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_cents=cost_cents,
            latency_ms=latency_ms,
            success=success,
            error_type=error_type,
            error_message=error_message[:500] if error_message else None,
        )
        self.session.add(record)
        await self.session.flush()
        return record.id

    async def get_llm_usage_stats(
        self,
        hours: int = 24,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> dict:
        """Get aggregated LLM usage stats for the given time period."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = select(
            func.count(LLMUsageModel.id).label("total_calls"),
            func.sum(LLMUsageModel.prompt_tokens).label("total_prompt_tokens"),
            func.sum(LLMUsageModel.completion_tokens).label("total_completion_tokens"),
            func.sum(LLMUsageModel.total_tokens).label("total_tokens"),
            func.sum(LLMUsageModel.cost_cents).label("total_cost_cents"),
            func.avg(LLMUsageModel.latency_ms).label("avg_latency_ms"),
            func.sum(func.cast(LLMUsageModel.success, type_=int)).label("success_count"),
        ).where(LLMUsageModel.timestamp >= since)

        if provider:
            query = query.where(LLMUsageModel.provider == provider)
        if model:
            query = query.where(LLMUsageModel.model == model)

        result = await self.session.execute(query)
        row = result.one()

        total_calls = row.total_calls or 0
        success_count = row.success_count or 0

        return {
            "total_calls": total_calls,
            "total_prompt_tokens": row.total_prompt_tokens or 0,
            "total_completion_tokens": row.total_completion_tokens or 0,
            "total_tokens": row.total_tokens or 0,
            "total_cost_cents": row.total_cost_cents or 0,
            "avg_latency_ms": float(row.avg_latency_ms or 0),
            "success_rate": (success_count / total_calls * 100) if total_calls > 0 else 0,
        }

    async def get_llm_usage_by_model(
        self,
        hours: int = 24,
    ) -> List[dict]:
        """Get LLM usage grouped by provider and model."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = (
            select(
                LLMUsageModel.provider,
                LLMUsageModel.model,
                func.count(LLMUsageModel.id).label("calls"),
                func.sum(LLMUsageModel.total_tokens).label("tokens"),
                func.sum(LLMUsageModel.cost_cents).label("cost_cents"),
            )
            .where(LLMUsageModel.timestamp >= since)
            .group_by(LLMUsageModel.provider, LLMUsageModel.model)
            .order_by(func.sum(LLMUsageModel.cost_cents).desc())
        )

        result = await self.session.execute(query)

        return [
            {
                "provider": row.provider,
                "model": row.model,
                "calls": row.calls,
                "tokens": row.tokens or 0,
                "cost_cents": row.cost_cents or 0,
            }
            for row in result.all()
        ]

    # =========================================================================
    # Agent Executions
    # =========================================================================

    async def save_agent_execution(
        self,
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
    ) -> str:
        """Save agent execution record. Returns record ID."""
        record = AgentExecutionModel(
            request_id=request_id,
            workflow_id=workflow_id,
            agent_id=agent_id,
            agent_type=agent_type,
            latency_ms=latency_ms,
            llm_calls_count=llm_calls_count,
            tool_calls_count=tool_calls_count,
            success=success,
            error_type=error_type,
            error_message=error_message[:500] if error_message else None,
        )
        self.session.add(record)
        await self.session.flush()
        return record.id

    async def get_agent_stats(
        self,
        hours: int = 24,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
    ) -> dict:
        """Get aggregated agent execution stats for the given time period."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = select(
            func.count(AgentExecutionModel.id).label("total_executions"),
            func.avg(AgentExecutionModel.latency_ms).label("avg_latency_ms"),
            func.sum(AgentExecutionModel.llm_calls_count).label("total_llm_calls"),
            func.sum(AgentExecutionModel.tool_calls_count).label("total_tool_calls"),
            func.sum(func.cast(AgentExecutionModel.success, type_=int)).label("success_count"),
        ).where(AgentExecutionModel.timestamp >= since)

        if agent_id:
            query = query.where(AgentExecutionModel.agent_id == agent_id)
        if agent_type:
            query = query.where(AgentExecutionModel.agent_type == agent_type)

        result = await self.session.execute(query)
        row = result.one()

        total = row.total_executions or 0
        success_count = row.success_count or 0

        return {
            "total_executions": total,
            "avg_latency_ms": float(row.avg_latency_ms or 0),
            "total_llm_calls": row.total_llm_calls or 0,
            "total_tool_calls": row.total_tool_calls or 0,
            "success_rate": (success_count / total * 100) if total > 0 else 0,
        }

    async def get_agent_stats_by_type(
        self,
        hours: int = 24,
    ) -> List[dict]:
        """Get agent execution stats grouped by agent type."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = (
            select(
                AgentExecutionModel.agent_type,
                func.count(AgentExecutionModel.id).label("executions"),
                func.avg(AgentExecutionModel.latency_ms).label("avg_latency_ms"),
                func.sum(func.cast(AgentExecutionModel.success, type_=int)).label("success_count"),
            )
            .where(AgentExecutionModel.timestamp >= since)
            .group_by(AgentExecutionModel.agent_type)
            .order_by(func.count(AgentExecutionModel.id).desc())
        )

        result = await self.session.execute(query)

        return [
            {
                "agent_type": row.agent_type,
                "executions": row.executions,
                "avg_latency_ms": float(row.avg_latency_ms or 0),
                "success_rate": (
                    (row.success_count / row.executions * 100) if row.executions > 0 else 0
                ),
            }
            for row in result.all()
        ]
