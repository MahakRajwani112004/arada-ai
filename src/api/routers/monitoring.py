"""Monitoring API - Logs and Analytics endpoints."""
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.auth.dependencies import get_current_user
from src.config import get_settings
from src.storage import get_async_session

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
settings = get_settings()


# ============================================
# Log Filtering Configuration
# ============================================

# Events to filter out (noise)
FILTERED_EVENTS = {
    "request_started",  # Only show completed requests
}

# Paths to filter out from request_completed logs
FILTERED_PATHS = {
    "/metrics",
    "/health",
    "/api/v1/monitoring/logs",
    "/api/v1/monitoring/analytics/llm",
    "/api/v1/monitoring/analytics/agents",
}


# ============================================
# Response Models
# ============================================

class LogEntry(BaseModel):
    """Single log entry."""
    timestamp: str
    service: str
    level: Optional[str] = None
    message: str
    labels: dict = {}


class LogsResponse(BaseModel):
    """Response for logs query."""
    logs: List[LogEntry]
    total: int


class LLMUsageStats(BaseModel):
    """LLM usage statistics."""
    total_requests: int
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost_cents: int
    avg_latency_ms: float
    success_rate: float
    by_provider: dict
    by_model: dict


class AgentStats(BaseModel):
    """Agent execution statistics."""
    total_executions: int
    success_rate: float
    avg_latency_ms: float
    by_type: dict


class TimeSeriesPoint(BaseModel):
    """Single point in time series."""
    timestamp: str
    value: float


# ============================================
# Logs Endpoints (from Loki)
# ============================================

@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    service: Optional[str] = Query(None, description="Filter by service (api, worker, etc.)"),
    level: Optional[str] = Query(None, description="Filter by level (info, error, warning)"),
    search: Optional[str] = Query(None, description="Search in log message"),
    limit: int = Query(100, le=1000, description="Max logs to return"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
    _user=Depends(get_current_user),
):
    """
    Get logs from Loki.

    Query all container logs with optional filters.
    """
    # Build LogQL query - use container label which matches container names
    # Promtail sets: container="magone-api", job="api", etc.
    if service:
        # Map service name to container name
        container_name = f"magone-{service}"
        label_selectors = [f'container="{container_name}"']
    else:
        # Match all magone containers
        label_selectors = ['container=~"magone-.*"']

    query = "{" + ",".join(label_selectors) + "}"

    # Add line filters
    if level:
        query += f' | json | level="{level}"'
    if search:
        query += f' |= "{search}"'

    # Time range
    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(hours=1)

    # Query Loki
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.loki_url}/loki/api/v1/query_range",
                params={
                    "query": query,
                    "start": int(start.timestamp() * 1e9),
                    "end": int(end.timestamp() * 1e9),
                    "limit": limit,
                },
                timeout=10.0,
            )

            if response.status_code != 200:
                return LogsResponse(logs=[], total=0)

            data = response.json()
            logs = []

            for stream in data.get("data", {}).get("result", []):
                labels = stream.get("stream", {})
                # Extract service from container name (magone-api -> api)
                container = labels.get("container", "")
                service_name = container.replace("magone-", "") if container.startswith("magone-") else labels.get("job", "unknown")

                for value in stream.get("values", []):
                    timestamp_ns, raw_message = value
                    # Try to parse JSON log message
                    log_level = labels.get("level")
                    try:
                        parsed = json.loads(raw_message)
                        event = parsed.get("event", "")

                        # Filter out noise events
                        if event in FILTERED_EVENTS:
                            continue

                        # Filter out noise paths
                        path = parsed.get("path", "")
                        if event == "request_completed" and path in FILTERED_PATHS:
                            continue

                        # Extract level
                        if not log_level and "level" in parsed:
                            log_level = parsed.get("level")

                        # Use human-readable message (added by structlog processor)
                        # Fall back to event name if message not present
                        display_message = parsed.get("message", event.replace("_", " ").capitalize())

                    except (json.JSONDecodeError, TypeError):
                        display_message = raw_message

                    logs.append(LogEntry(
                        timestamp=datetime.fromtimestamp(int(timestamp_ns) / 1e9).isoformat(),
                        service=service_name,
                        level=log_level,
                        message=display_message,
                        labels=labels,
                    ))

            # Sort by timestamp descending
            logs.sort(key=lambda x: x.timestamp, reverse=True)

            return LogsResponse(logs=logs[:limit], total=len(logs))

    except Exception as e:
        # Return empty if Loki is not available
        return LogsResponse(logs=[], total=0)


@router.get("/logs/services")
async def get_log_services(
    _user=Depends(get_current_user),
):
    """Get list of available services for log filtering."""
    return {
        "services": [
            {"id": "api", "name": "API Server"},
            {"id": "worker", "name": "Temporal Worker"},
            {"id": "web", "name": "Web Frontend"},
            {"id": "temporal", "name": "Temporal Server"},
            {"id": "postgres", "name": "PostgreSQL"},
            {"id": "redis", "name": "Redis"},
        ]
    }


# ============================================
# Analytics Endpoints (from PostgreSQL)
# ============================================

@router.get("/analytics/llm", response_model=LLMUsageStats)
async def get_llm_analytics(
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
    _user=Depends(get_current_user),
):
    """
    Get LLM usage analytics.

    Returns token usage, costs, and latency statistics.
    """
    from sqlalchemy import func, select
    from src.monitoring.analytics.models import LLMUsageModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    async with get_async_session() as session:
        # Base query with time filter
        base_query = select(LLMUsageModel).where(
            LLMUsageModel.timestamp >= start,
            LLMUsageModel.timestamp <= end,
        )

        # Get totals
        from sqlalchemy import Integer
        totals = await session.execute(
            select(
                func.count(LLMUsageModel.id).label("total"),
                func.sum(LLMUsageModel.total_tokens).label("tokens"),
                func.sum(LLMUsageModel.prompt_tokens).label("prompt"),
                func.sum(LLMUsageModel.completion_tokens).label("completion"),
                func.sum(LLMUsageModel.cost_cents).label("cost"),
                func.avg(LLMUsageModel.latency_ms).label("latency"),
                func.sum(func.cast(LLMUsageModel.success, Integer)).label("successes"),
            ).where(
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            )
        )
        row = totals.first()

        total_requests = row.total or 0
        success_rate = (row.successes or 0) / total_requests if total_requests > 0 else 0

        # By provider
        by_provider_query = await session.execute(
            select(
                LLMUsageModel.provider,
                func.count(LLMUsageModel.id).label("count"),
                func.sum(LLMUsageModel.cost_cents).label("cost"),
            ).where(
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            ).group_by(LLMUsageModel.provider)
        )
        by_provider = {r.provider: {"count": r.count, "cost_cents": r.cost or 0} for r in by_provider_query}

        # By model
        by_model_query = await session.execute(
            select(
                LLMUsageModel.model,
                func.count(LLMUsageModel.id).label("count"),
                func.sum(LLMUsageModel.total_tokens).label("tokens"),
            ).where(
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            ).group_by(LLMUsageModel.model)
        )
        by_model = {r.model: {"count": r.count, "tokens": r.tokens or 0} for r in by_model_query}

        return LLMUsageStats(
            total_requests=total_requests,
            total_tokens=row.tokens or 0,
            total_prompt_tokens=row.prompt or 0,
            total_completion_tokens=row.completion or 0,
            total_cost_cents=row.cost or 0,
            avg_latency_ms=float(row.latency or 0),
            success_rate=success_rate,
            by_provider=by_provider,
            by_model=by_model,
        )


@router.get("/analytics/agents", response_model=AgentStats)
async def get_agent_analytics(
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
    _user=Depends(get_current_user),
):
    """
    Get agent execution analytics.

    Returns execution counts, success rates, and latency by agent type.
    """
    from sqlalchemy import Integer, func, select
    from src.monitoring.analytics.models import AgentExecutionModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    async with get_async_session() as session:
        # Get totals
        totals = await session.execute(
            select(
                func.count(AgentExecutionModel.id).label("total"),
                func.avg(AgentExecutionModel.latency_ms).label("latency"),
                func.sum(func.cast(AgentExecutionModel.success, Integer)).label("successes"),
            ).where(
                AgentExecutionModel.timestamp >= start,
                AgentExecutionModel.timestamp <= end,
            )
        )
        row = totals.first()

        total_executions = row.total or 0
        success_rate = (row.successes or 0) / total_executions if total_executions > 0 else 0

        # By type
        by_type_query = await session.execute(
            select(
                AgentExecutionModel.agent_type,
                func.count(AgentExecutionModel.id).label("count"),
                func.avg(AgentExecutionModel.latency_ms).label("latency"),
            ).where(
                AgentExecutionModel.timestamp >= start,
                AgentExecutionModel.timestamp <= end,
            ).group_by(AgentExecutionModel.agent_type)
        )
        by_type = {
            r.agent_type: {"count": r.count, "avg_latency_ms": float(r.latency or 0)}
            for r in by_type_query
        }

        return AgentStats(
            total_executions=total_executions,
            success_rate=success_rate,
            avg_latency_ms=float(row.latency or 0),
            by_type=by_type,
        )


@router.get("/analytics/llm/timeseries")
async def get_llm_timeseries(
    metric: str = Query("requests", description="Metric: requests, tokens, cost"),
    interval: str = Query("1h", description="Bucket interval: 1h, 6h, 1d"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
    _user=Depends(get_current_user),
):
    """Get LLM usage as time series for charts."""
    from sqlalchemy import func, select
    from src.monitoring.analytics.models import LLMUsageModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    # Map interval to PostgreSQL date_trunc
    interval_map = {"1h": "hour", "6h": "hour", "1d": "day"}
    trunc_interval = interval_map.get(interval, "hour")

    # Map metric to column
    metric_map = {
        "requests": func.count(LLMUsageModel.id),
        "tokens": func.sum(LLMUsageModel.total_tokens),
        "cost": func.sum(LLMUsageModel.cost_cents),
    }
    metric_col = metric_map.get(metric, func.count(LLMUsageModel.id))

    async with get_async_session() as session:
        query = await session.execute(
            select(
                func.date_trunc(trunc_interval, LLMUsageModel.timestamp).label("bucket"),
                metric_col.label("value"),
            ).where(
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            ).group_by("bucket").order_by("bucket")
        )

        return {
            "metric": metric,
            "interval": interval,
            "data": [
                {"timestamp": row.bucket.isoformat(), "value": float(row.value or 0)}
                for row in query
            ]
        }
