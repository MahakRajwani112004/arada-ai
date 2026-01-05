"""Analytics Repository - stores monitoring data to PostgreSQL."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, Integer
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
        user_id: str,
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
            user_id=user_id,
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
        user_id: str,
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
            func.sum(LLMUsageModel.success.cast(Integer)).label("success_count"),
        ).where(
            LLMUsageModel.user_id == user_id,
            LLMUsageModel.timestamp >= since,
        )

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
        user_id: str,
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
            .where(
                LLMUsageModel.user_id == user_id,
                LLMUsageModel.timestamp >= since,
            )
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
        # Overview tab fields (MVP)
        input_preview: Optional[str] = None,
        output_preview: Optional[str] = None,
        total_tokens: int = 0,
        total_cost_cents: int = 0,
        parent_execution_id: Optional[str] = None,
        # Full execution metadata
        execution_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save agent execution record. Returns record ID."""
        record = AgentExecutionModel(
            user_id=user_id,
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
            # Overview tab fields (MVP)
            input_preview=input_preview[:200] if input_preview else None,
            output_preview=output_preview[:500] if output_preview else None,
            total_tokens=total_tokens,
            total_cost_cents=total_cost_cents,
            parent_execution_id=parent_execution_id,
            execution_metadata=execution_metadata,
        )
        self.session.add(record)
        await self.session.flush()
        return record.id

    async def get_execution_detail(
        self,
        execution_id: str,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get full execution details including metadata."""
        query = select(AgentExecutionModel).where(
            AgentExecutionModel.id == execution_id,
            AgentExecutionModel.user_id == user_id,
        )
        result = await self.session.execute(query)
        record = result.scalar_one_or_none()

        if not record:
            return None

        return {
            "id": record.id,
            "agent_id": record.agent_id,
            "agent_type": record.agent_type,
            "timestamp": record.timestamp.isoformat(),
            "status": "completed" if record.success else "failed",
            "duration_ms": record.latency_ms,
            "input_preview": record.input_preview,
            "output_preview": record.output_preview,
            "total_tokens": record.total_tokens,
            "total_cost_cents": record.total_cost_cents,
            "llm_calls_count": record.llm_calls_count,
            "tool_calls_count": record.tool_calls_count,
            "error_type": record.error_type,
            "error_message": record.error_message,
            "workflow_id": record.workflow_id,
            "execution_metadata": record.execution_metadata,
        }

    async def get_agent_stats(
        self,
        user_id: str,
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
            func.sum(AgentExecutionModel.success.cast(Integer)).label("success_count"),
        ).where(
            AgentExecutionModel.user_id == user_id,
            AgentExecutionModel.timestamp >= since,
        )

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
        user_id: str,
        hours: int = 24,
    ) -> List[dict]:
        """Get agent execution stats grouped by agent type."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = (
            select(
                AgentExecutionModel.agent_type,
                func.count(AgentExecutionModel.id).label("executions"),
                func.avg(AgentExecutionModel.latency_ms).label("avg_latency_ms"),
                func.sum(AgentExecutionModel.success.cast(Integer)).label("success_count"),
            )
            .where(
                AgentExecutionModel.user_id == user_id,
                AgentExecutionModel.timestamp >= since,
            )
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

    # =========================================================================
    # Agent Overview Tab - New Methods
    # =========================================================================

    async def get_agent_overview_stats(
        self,
        user_id: str,
        agent_id: str,
        hours: int = 168,  # 7 days default
    ) -> dict:
        """Get detailed agent stats for overview tab with trends.

        Args:
            user_id: User ID for scoping
            agent_id: Agent ID to get stats for
            hours: Time range in hours (24, 168, 720, 2160 for 24h, 7d, 30d, 90d)

        Returns:
            Dict with current stats and trends vs previous period
        """
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(hours=hours)
        previous_start = current_start - timedelta(hours=hours)

        # Current period stats
        current_query = select(
            func.count(AgentExecutionModel.id).label("total"),
            func.sum(AgentExecutionModel.success.cast(Integer)).label("success_count"),
            func.avg(AgentExecutionModel.latency_ms).label("avg_latency"),
            func.sum(AgentExecutionModel.total_tokens).label("total_tokens"),
            func.sum(AgentExecutionModel.total_cost_cents).label("total_cost"),
        ).where(
            AgentExecutionModel.user_id == user_id,
            AgentExecutionModel.agent_id == agent_id,
            AgentExecutionModel.timestamp >= current_start,
        )
        current_result = await self.session.execute(current_query)
        current = current_result.one()

        # Previous period stats (for trends)
        previous_query = select(
            func.count(AgentExecutionModel.id).label("total"),
            func.sum(AgentExecutionModel.success.cast(Integer)).label("success_count"),
            func.avg(AgentExecutionModel.latency_ms).label("avg_latency"),
            func.sum(AgentExecutionModel.total_cost_cents).label("total_cost"),
        ).where(
            AgentExecutionModel.user_id == user_id,
            AgentExecutionModel.agent_id == agent_id,
            AgentExecutionModel.timestamp >= previous_start,
            AgentExecutionModel.timestamp < current_start,
        )
        previous_result = await self.session.execute(previous_query)
        previous = previous_result.one()

        # P95 latency (separate query for percentile)
        p95_query = select(AgentExecutionModel.latency_ms).where(
            AgentExecutionModel.user_id == user_id,
            AgentExecutionModel.agent_id == agent_id,
            AgentExecutionModel.timestamp >= current_start,
        ).order_by(AgentExecutionModel.latency_ms.desc())
        p95_result = await self.session.execute(p95_query)
        latencies = [row[0] for row in p95_result.all()]
        p95_latency = 0.0
        if latencies:
            p95_index = max(0, int(len(latencies) * 0.05))
            p95_latency = float(latencies[p95_index])

        # Calculate trends
        def calc_trend(current_val: float, previous_val: float) -> float:
            if previous_val == 0:
                return 100.0 if current_val > 0 else 0.0
            return ((current_val - previous_val) / previous_val) * 100

        total = current.total or 0
        success_count = current.success_count or 0
        prev_total = previous.total or 0
        prev_success = previous.success_count or 0

        current_success_rate = (success_count / total) if total > 0 else 0
        prev_success_rate = (prev_success / prev_total) if prev_total > 0 else 0

        return {
            "total_executions": total,
            "successful_executions": success_count,
            "failed_executions": total - success_count,
            "success_rate": current_success_rate,
            "avg_latency_ms": float(current.avg_latency or 0),
            "p95_latency_ms": p95_latency,
            "total_tokens": current.total_tokens or 0,
            "total_cost_cents": current.total_cost or 0,
            "executions_trend": calc_trend(total, prev_total),
            "success_trend": calc_trend(current_success_rate * 100, prev_success_rate * 100),
            "latency_trend": calc_trend(
                float(current.avg_latency or 0),
                float(previous.avg_latency or 0)
            ),
            "cost_trend": calc_trend(
                current.total_cost or 0,
                previous.total_cost or 0
            ),
        }

    async def get_agent_executions(
        self,
        user_id: str,
        agent_id: str,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[str] = None,  # "completed", "failed", or None for all
    ) -> tuple[List[dict], int]:
        """Get paginated list of agent executions.

        Returns:
            Tuple of (executions list, total count)
        """
        # Base query conditions
        conditions = [
            AgentExecutionModel.user_id == user_id,
            AgentExecutionModel.agent_id == agent_id,
        ]

        if status_filter == "completed":
            conditions.append(AgentExecutionModel.success == True)
        elif status_filter == "failed":
            conditions.append(AgentExecutionModel.success == False)

        # Get total count
        count_query = select(func.count(AgentExecutionModel.id)).where(*conditions)
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Get executions
        query = (
            select(AgentExecutionModel)
            .where(*conditions)
            .order_by(AgentExecutionModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        rows = result.scalars().all()

        executions = [
            {
                "id": row.id,
                "status": "completed" if row.success else "failed",
                "timestamp": row.timestamp.isoformat(),
                "duration_ms": row.latency_ms,
                "input_preview": row.input_preview,
                "output_preview": row.output_preview,
                "error_type": row.error_type,
                "error_message": row.error_message,
                "total_tokens": row.total_tokens,
                "total_cost_cents": row.total_cost_cents,
            }
            for row in rows
        ]

        return executions, total

    async def get_agent_usage_history(
        self,
        user_id: str,
        agent_id: str,
        hours: int = 168,  # 7 days
        granularity: str = "day",  # "hour" or "day"
    ) -> List[dict]:
        """Get usage history for charts.

        Args:
            user_id: User ID
            agent_id: Agent ID
            hours: Time range in hours
            granularity: "hour" or "day"

        Returns:
            List of data points with timestamp, executions, etc.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Use date_trunc for grouping
        if granularity == "hour":
            time_bucket = func.date_trunc("hour", AgentExecutionModel.timestamp)
        else:
            time_bucket = func.date_trunc("day", AgentExecutionModel.timestamp)

        query = (
            select(
                time_bucket.label("bucket"),
                func.count(AgentExecutionModel.id).label("executions"),
                func.sum(AgentExecutionModel.success.cast(Integer)).label("successful"),
                func.avg(AgentExecutionModel.latency_ms).label("avg_latency"),
                func.sum(AgentExecutionModel.total_cost_cents).label("total_cost"),
            )
            .where(
                AgentExecutionModel.user_id == user_id,
                AgentExecutionModel.agent_id == agent_id,
                AgentExecutionModel.timestamp >= since,
            )
            .group_by(time_bucket)
            .order_by(time_bucket)
        )

        result = await self.session.execute(query)

        return [
            {
                "timestamp": row.bucket.isoformat() if row.bucket else "",
                "executions": row.executions or 0,
                "successful": row.successful or 0,
                "failed": (row.executions or 0) - (row.successful or 0),
                "avg_latency_ms": float(row.avg_latency or 0),
                "total_cost_cents": row.total_cost or 0,
            }
            for row in result.all()
        ]
