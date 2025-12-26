"""Monitoring API - Logs and Analytics endpoints."""
import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.auth.dependencies import CurrentUser
from src.config import get_settings
from src.storage import get_async_session

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
settings = get_settings()


# ============================================
# Log Filtering Configuration
# ============================================

# Important events to show (whitelist approach)
IMPORTANT_EVENTS = {
    # Auth
    "user_logged_in", "user_logged_out", "login_failed", "user_registered", "invite_created",
    # Agents
    "agent_created", "agent_updated", "agent_deleted", "agent_generate_started",
    "agent_generate_completed", "agent_generate_failed",
    # MCP
    "mcp_server_created", "mcp_server_deleted", "mcp_server_reconnected",
    "mcp_server_connection_failed", "mcp_servers_reconnected",
    "mcp_server_connected", "mcp_server_added", "oauth_token_stored",
    # Knowledge Base
    "knowledge_base_created", "knowledge_base_updated", "knowledge_base_deleted",
    "document_upload_started", "document_upload_completed", "document_indexed",
    "document_indexing_failed", "knowledge_base_search_completed",
    # Workflow
    "workflow_execution_started", "workflow_execution_completed",
    # LLM & Agent execution
    "llm_call_completed", "agent_execution_completed",
    # Application
    "application_started",
    # Errors
    "http_exception", "database_transaction_failed",
    # HTTP Requests
    "request_started", "request_completed",
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
    current_user: CurrentUser,
    service: Optional[str] = Query(None, description="Filter by service (api, worker, etc.)"),
    level: Optional[str] = Query(None, description="Filter by level (info, error, warning)"),
    search: Optional[str] = Query(None, description="Search in log message"),
    limit: int = Query(100, le=1000, description="Max logs to return"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
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
        # Only match API and worker containers (not loki, grafana, etc.)
        label_selectors = ['container=~"magone-(api|worker)"']

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

                        # Only show important events (whitelist)
                        if event not in IMPORTANT_EVENTS:
                            continue

                        # Extract level
                        if not log_level and "level" in parsed:
                            log_level = parsed.get("level")

                        # Use human-readable message (added by structlog processor)
                        # Fall back to event name if message not present
                        display_message = parsed.get("message", event.replace("_", " ").capitalize())

                    except (json.JSONDecodeError, TypeError):
                        # Skip non-JSON logs (SQLAlchemy, etc.)
                        continue

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
    current_user: CurrentUser,
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
    current_user: CurrentUser,
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """
    Get LLM usage analytics for the current user.

    Returns token usage, costs, and latency statistics.
    """
    from sqlalchemy import Integer, func, select
    from src.monitoring.analytics.models import LLMUsageModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    async with get_async_session() as session:
        # Get totals filtered by user
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
                LLMUsageModel.user_id == current_user.id,
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
                LLMUsageModel.user_id == current_user.id,
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
                LLMUsageModel.user_id == current_user.id,
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
    current_user: CurrentUser,
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """
    Get agent execution analytics for the current user.

    Returns execution counts, success rates, and latency by agent type.
    """
    from sqlalchemy import Integer, func, select
    from src.monitoring.analytics.models import AgentExecutionModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    async with get_async_session() as session:
        # Get totals filtered by user
        totals = await session.execute(
            select(
                func.count(AgentExecutionModel.id).label("total"),
                func.avg(AgentExecutionModel.latency_ms).label("latency"),
                func.sum(func.cast(AgentExecutionModel.success, Integer)).label("successes"),
            ).where(
                AgentExecutionModel.user_id == current_user.id,
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
                AgentExecutionModel.user_id == current_user.id,
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
    current_user: CurrentUser,
    metric: str = Query("requests", description="Metric: requests, tokens, cost"),
    interval: str = Query("1h", description="Bucket interval: 1h, 6h, 1d"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """Get LLM usage as time series for charts for the current user."""
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
                LLMUsageModel.user_id == current_user.id,
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


# ============================================
# Workflow Analytics Endpoints
# ============================================

class WorkflowStats(BaseModel):
    """Workflow execution statistics."""
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_duration_ms: float
    total_duration_ms: int
    by_status: dict
    by_workflow: dict


@router.get("/analytics/workflows", response_model=WorkflowStats)
async def get_workflow_analytics(
    current_user: CurrentUser,
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """
    Get workflow execution analytics for the current user.

    Returns execution counts, success rates, and duration statistics.
    """
    from sqlalchemy import case, func, select
    from src.storage.models import WorkflowExecutionModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    async with get_async_session() as session:
        # Get totals filtered by user
        totals = await session.execute(
            select(
                func.count(WorkflowExecutionModel.id).label("total"),
                func.sum(case((WorkflowExecutionModel.status == "COMPLETED", 1), else_=0)).label("successful"),
                func.sum(case((WorkflowExecutionModel.status == "FAILED", 1), else_=0)).label("failed"),
                func.avg(WorkflowExecutionModel.duration_ms).label("avg_duration"),
                func.sum(WorkflowExecutionModel.duration_ms).label("total_duration"),
            ).where(
                WorkflowExecutionModel.user_id == current_user.id,
                WorkflowExecutionModel.started_at >= start,
                WorkflowExecutionModel.started_at <= end,
            )
        )
        row = totals.first()

        total_executions = row.total or 0
        successful = row.successful or 0
        success_rate = successful / total_executions if total_executions > 0 else 0

        # By status
        by_status_query = await session.execute(
            select(
                WorkflowExecutionModel.status,
                func.count(WorkflowExecutionModel.id).label("count"),
            ).where(
                WorkflowExecutionModel.user_id == current_user.id,
                WorkflowExecutionModel.started_at >= start,
                WorkflowExecutionModel.started_at <= end,
            ).group_by(WorkflowExecutionModel.status)
        )
        by_status = {r.status: r.count for r in by_status_query}

        # By workflow
        by_workflow_query = await session.execute(
            select(
                WorkflowExecutionModel.workflow_id,
                func.count(WorkflowExecutionModel.id).label("count"),
                func.avg(WorkflowExecutionModel.duration_ms).label("avg_duration"),
            ).where(
                WorkflowExecutionModel.user_id == current_user.id,
                WorkflowExecutionModel.started_at >= start,
                WorkflowExecutionModel.started_at <= end,
            ).group_by(WorkflowExecutionModel.workflow_id)
        )
        by_workflow = {
            r.workflow_id: {"count": r.count, "avg_duration_ms": float(r.avg_duration or 0)}
            for r in by_workflow_query
        }

        return WorkflowStats(
            total_executions=total_executions,
            successful_executions=successful,
            failed_executions=row.failed or 0,
            success_rate=success_rate,
            avg_duration_ms=float(row.avg_duration or 0),
            total_duration_ms=int(row.total_duration or 0),
            by_status=by_status,
            by_workflow=by_workflow,
        )


@router.get("/analytics/workflows/timeseries")
async def get_workflow_timeseries(
    current_user: CurrentUser,
    metric: str = Query("executions", description="Metric: executions, duration, success_rate"),
    interval: str = Query("1h", description="Bucket interval: 1h, 6h, 1d"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """Get workflow executions as time series for charts."""
    from sqlalchemy import case, func, select
    from src.storage.models import WorkflowExecutionModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    interval_map = {"1h": "hour", "6h": "hour", "1d": "day"}
    trunc_interval = interval_map.get(interval, "hour")

    async with get_async_session() as session:
        if metric == "success_rate":
            query = await session.execute(
                select(
                    func.date_trunc(trunc_interval, WorkflowExecutionModel.started_at).label("bucket"),
                    (func.sum(case((WorkflowExecutionModel.status == "COMPLETED", 1), else_=0)) * 100.0 /
                     func.nullif(func.count(WorkflowExecutionModel.id), 0)).label("value"),
                ).where(
                    WorkflowExecutionModel.user_id == current_user.id,
                    WorkflowExecutionModel.started_at >= start,
                    WorkflowExecutionModel.started_at <= end,
                ).group_by("bucket").order_by("bucket")
            )
        else:
            metric_map = {
                "executions": func.count(WorkflowExecutionModel.id),
                "duration": func.avg(WorkflowExecutionModel.duration_ms),
            }
            metric_col = metric_map.get(metric, func.count(WorkflowExecutionModel.id))

            query = await session.execute(
                select(
                    func.date_trunc(trunc_interval, WorkflowExecutionModel.started_at).label("bucket"),
                    metric_col.label("value"),
                ).where(
                    WorkflowExecutionModel.user_id == current_user.id,
                    WorkflowExecutionModel.started_at >= start,
                    WorkflowExecutionModel.started_at <= end,
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


# ============================================
# Dashboard Summary Endpoint
# ============================================

class DashboardSummary(BaseModel):
    """Overall dashboard summary statistics."""
    # Counts
    total_agents: int
    total_workflows: int
    total_mcp_servers: int
    total_knowledge_bases: int
    # Executions (last 24h)
    executions_24h: int
    llm_calls_24h: int
    tokens_used_24h: int
    cost_cents_24h: int
    # Success rates
    agent_success_rate_24h: float
    workflow_success_rate_24h: float
    # Active items
    active_mcp_servers: int
    # Recent activity
    recent_workflows: List[dict]
    recent_executions: List[dict]


@router.get("/analytics/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: CurrentUser,
):
    """
    Get comprehensive dashboard summary for the current user.

    Returns counts, recent activity, and key metrics.
    """
    from sqlalchemy import case, desc, func, select
    from src.monitoring.analytics.models import AgentExecutionModel, LLMUsageModel
    from src.storage.models import (
        AgentModel,
        KnowledgeBaseModel,
        MCPServerModel,
        WorkflowExecutionModel,
        WorkflowModel,
    )

    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    async with get_async_session() as session:
        # Count entities
        agents_count = await session.execute(
            select(func.count(AgentModel.id)).where(
                AgentModel.user_id == current_user.id,
                AgentModel.is_active == True,
            )
        )
        workflows_count = await session.execute(
            select(func.count(WorkflowModel.id)).where(
                WorkflowModel.user_id == current_user.id,
                WorkflowModel.is_active == True,
            )
        )
        mcp_count = await session.execute(
            select(func.count(MCPServerModel.id)).where(
                MCPServerModel.user_id == current_user.id,
            )
        )
        mcp_active_count = await session.execute(
            select(func.count(MCPServerModel.id)).where(
                MCPServerModel.user_id == current_user.id,
                MCPServerModel.status == "active",
            )
        )
        kb_count = await session.execute(
            select(func.count(KnowledgeBaseModel.id)).where(
                KnowledgeBaseModel.user_id == current_user.id,
            )
        )

        # LLM usage last 24h
        llm_stats = await session.execute(
            select(
                func.count(LLMUsageModel.id).label("calls"),
                func.sum(LLMUsageModel.total_tokens).label("tokens"),
                func.sum(LLMUsageModel.cost_cents).label("cost"),
            ).where(
                LLMUsageModel.user_id == current_user.id,
                LLMUsageModel.timestamp >= last_24h,
            )
        )
        llm_row = llm_stats.first()

        # Agent executions last 24h
        agent_stats = await session.execute(
            select(
                func.count(AgentExecutionModel.id).label("total"),
                func.sum(case((AgentExecutionModel.success == True, 1), else_=0)).label("successful"),
            ).where(
                AgentExecutionModel.user_id == current_user.id,
                AgentExecutionModel.timestamp >= last_24h,
            )
        )
        agent_row = agent_stats.first()

        # Workflow executions last 24h
        workflow_stats = await session.execute(
            select(
                func.count(WorkflowExecutionModel.id).label("total"),
                func.sum(case((WorkflowExecutionModel.status == "COMPLETED", 1), else_=0)).label("successful"),
            ).where(
                WorkflowExecutionModel.user_id == current_user.id,
                WorkflowExecutionModel.started_at >= last_24h,
            )
        )
        workflow_row = workflow_stats.first()

        # Recent workflows
        recent_workflows_query = await session.execute(
            select(WorkflowModel.id, WorkflowModel.name, WorkflowModel.updated_at)
            .where(
                WorkflowModel.user_id == current_user.id,
                WorkflowModel.is_active == True,
            )
            .order_by(desc(WorkflowModel.updated_at))
            .limit(5)
        )
        recent_workflows = [
            {"id": r.id, "name": r.name, "updated_at": r.updated_at.isoformat()}
            for r in recent_workflows_query
        ]

        # Recent executions
        recent_executions_query = await session.execute(
            select(
                WorkflowExecutionModel.id,
                WorkflowExecutionModel.workflow_id,
                WorkflowExecutionModel.status,
                WorkflowExecutionModel.started_at,
                WorkflowExecutionModel.duration_ms,
            )
            .where(WorkflowExecutionModel.user_id == current_user.id)
            .order_by(desc(WorkflowExecutionModel.started_at))
            .limit(5)
        )
        recent_executions = [
            {
                "id": r.id,
                "workflow_id": r.workflow_id,
                "status": r.status,
                "started_at": r.started_at.isoformat(),
                "duration_ms": r.duration_ms,
            }
            for r in recent_executions_query
        ]

        # Calculate success rates
        agent_total = agent_row.total or 0
        agent_success_rate = (agent_row.successful or 0) / agent_total if agent_total > 0 else 0
        workflow_total = workflow_row.total or 0
        workflow_success_rate = (workflow_row.successful or 0) / workflow_total if workflow_total > 0 else 0

        return DashboardSummary(
            total_agents=agents_count.scalar() or 0,
            total_workflows=workflows_count.scalar() or 0,
            total_mcp_servers=mcp_count.scalar() or 0,
            total_knowledge_bases=kb_count.scalar() or 0,
            executions_24h=workflow_total,
            llm_calls_24h=llm_row.calls or 0,
            tokens_used_24h=llm_row.tokens or 0,
            cost_cents_24h=llm_row.cost or 0,
            agent_success_rate_24h=agent_success_rate,
            workflow_success_rate_24h=workflow_success_rate,
            active_mcp_servers=mcp_active_count.scalar() or 0,
            recent_workflows=recent_workflows,
            recent_executions=recent_executions,
        )


# ============================================
# Top Entities Analytics
# ============================================

@router.get("/analytics/top/workflows")
async def get_top_workflows(
    current_user: CurrentUser,
    limit: int = Query(10, le=50, description="Number of workflows to return"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """Get top workflows by execution count."""
    from sqlalchemy import case, desc, func, select
    from src.storage.models import WorkflowExecutionModel, WorkflowModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    async with get_async_session() as session:
        query = await session.execute(
            select(
                WorkflowExecutionModel.workflow_id,
                func.count(WorkflowExecutionModel.id).label("execution_count"),
                func.sum(case((WorkflowExecutionModel.status == "COMPLETED", 1), else_=0)).label("successful"),
                func.avg(WorkflowExecutionModel.duration_ms).label("avg_duration"),
            )
            .where(
                WorkflowExecutionModel.user_id == current_user.id,
                WorkflowExecutionModel.started_at >= start,
                WorkflowExecutionModel.started_at <= end,
            )
            .group_by(WorkflowExecutionModel.workflow_id)
            .order_by(desc("execution_count"))
            .limit(limit)
        )

        workflows = []
        for row in query:
            # Get workflow name
            workflow = await session.execute(
                select(WorkflowModel.name).where(WorkflowModel.id == row.workflow_id)
            )
            name = workflow.scalar() or row.workflow_id
            success_rate = (row.successful or 0) / row.execution_count if row.execution_count > 0 else 0

            workflows.append({
                "workflow_id": row.workflow_id,
                "name": name,
                "execution_count": row.execution_count,
                "success_rate": success_rate,
                "avg_duration_ms": float(row.avg_duration or 0),
            })

        return {"workflows": workflows, "total": len(workflows)}


@router.get("/analytics/top/agents")
async def get_top_agents(
    current_user: CurrentUser,
    limit: int = Query(10, le=50, description="Number of agents to return"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """Get top agents by execution count."""
    from sqlalchemy import case, desc, func, select
    from src.monitoring.analytics.models import AgentExecutionModel
    from src.storage.models import AgentModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    async with get_async_session() as session:
        query = await session.execute(
            select(
                AgentExecutionModel.agent_id,
                AgentExecutionModel.agent_type,
                func.count(AgentExecutionModel.id).label("execution_count"),
                func.sum(case((AgentExecutionModel.success == True, 1), else_=0)).label("successful"),
                func.avg(AgentExecutionModel.latency_ms).label("avg_latency"),
                func.sum(AgentExecutionModel.llm_calls_count).label("total_llm_calls"),
                func.sum(AgentExecutionModel.tool_calls_count).label("total_tool_calls"),
            )
            .where(
                AgentExecutionModel.user_id == current_user.id,
                AgentExecutionModel.timestamp >= start,
                AgentExecutionModel.timestamp <= end,
            )
            .group_by(AgentExecutionModel.agent_id, AgentExecutionModel.agent_type)
            .order_by(desc("execution_count"))
            .limit(limit)
        )

        agents = []
        for row in query:
            # Get agent name
            agent = await session.execute(
                select(AgentModel.name).where(AgentModel.id == row.agent_id)
            )
            name = agent.scalar() or row.agent_id
            success_rate = (row.successful or 0) / row.execution_count if row.execution_count > 0 else 0

            agents.append({
                "agent_id": row.agent_id,
                "name": name,
                "agent_type": row.agent_type,
                "execution_count": row.execution_count,
                "success_rate": success_rate,
                "avg_latency_ms": float(row.avg_latency or 0),
                "total_llm_calls": row.total_llm_calls or 0,
                "total_tool_calls": row.total_tool_calls or 0,
            })

        return {"agents": agents, "total": len(agents)}


@router.get("/analytics/top/models")
async def get_top_models(
    current_user: CurrentUser,
    limit: int = Query(10, le=50, description="Number of models to return"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """Get top LLM models by usage."""
    from sqlalchemy import desc, func, select
    from src.monitoring.analytics.models import LLMUsageModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    async with get_async_session() as session:
        query = await session.execute(
            select(
                LLMUsageModel.provider,
                LLMUsageModel.model,
                func.count(LLMUsageModel.id).label("request_count"),
                func.sum(LLMUsageModel.total_tokens).label("total_tokens"),
                func.sum(LLMUsageModel.cost_cents).label("total_cost"),
                func.avg(LLMUsageModel.latency_ms).label("avg_latency"),
            )
            .where(
                LLMUsageModel.user_id == current_user.id,
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            )
            .group_by(LLMUsageModel.provider, LLMUsageModel.model)
            .order_by(desc("request_count"))
            .limit(limit)
        )

        models = [
            {
                "provider": row.provider,
                "model": row.model,
                "request_count": row.request_count,
                "total_tokens": row.total_tokens or 0,
                "total_cost_cents": row.total_cost or 0,
                "avg_latency_ms": float(row.avg_latency or 0),
            }
            for row in query
        ]

        return {"models": models, "total": len(models)}


# ============================================
# Error Analytics
# ============================================

class ErrorStats(BaseModel):
    """Error statistics."""
    total_errors: int
    error_rate: float
    by_type: dict
    by_agent: dict
    by_workflow: dict
    recent_errors: List[dict]


@router.get("/analytics/errors", response_model=ErrorStats)
async def get_error_analytics(
    current_user: CurrentUser,
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """Get error analytics for debugging and monitoring."""
    from sqlalchemy import desc, func, select
    from src.monitoring.analytics.models import AgentExecutionModel, LLMUsageModel
    from src.storage.models import WorkflowExecutionModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    async with get_async_session() as session:
        # LLM errors
        llm_errors = await session.execute(
            select(
                LLMUsageModel.error_type,
                func.count(LLMUsageModel.id).label("count"),
            )
            .where(
                LLMUsageModel.user_id == current_user.id,
                LLMUsageModel.success == False,
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            )
            .group_by(LLMUsageModel.error_type)
        )
        llm_error_counts = {r.error_type or "unknown": r.count for r in llm_errors}

        # Agent errors by type
        agent_errors_by_type = await session.execute(
            select(
                AgentExecutionModel.error_type,
                func.count(AgentExecutionModel.id).label("count"),
            )
            .where(
                AgentExecutionModel.user_id == current_user.id,
                AgentExecutionModel.success == False,
                AgentExecutionModel.timestamp >= start,
                AgentExecutionModel.timestamp <= end,
            )
            .group_by(AgentExecutionModel.error_type)
        )
        agent_error_type_counts = {r.error_type or "unknown": r.count for r in agent_errors_by_type}

        # Agent errors by agent
        agent_errors_by_agent = await session.execute(
            select(
                AgentExecutionModel.agent_id,
                func.count(AgentExecutionModel.id).label("count"),
            )
            .where(
                AgentExecutionModel.user_id == current_user.id,
                AgentExecutionModel.success == False,
                AgentExecutionModel.timestamp >= start,
                AgentExecutionModel.timestamp <= end,
            )
            .group_by(AgentExecutionModel.agent_id)
        )
        by_agent = {r.agent_id: r.count for r in agent_errors_by_agent}

        # Workflow errors
        workflow_errors = await session.execute(
            select(
                WorkflowExecutionModel.workflow_id,
                func.count(WorkflowExecutionModel.id).label("count"),
            )
            .where(
                WorkflowExecutionModel.user_id == current_user.id,
                WorkflowExecutionModel.status == "FAILED",
                WorkflowExecutionModel.started_at >= start,
                WorkflowExecutionModel.started_at <= end,
            )
            .group_by(WorkflowExecutionModel.workflow_id)
        )
        by_workflow = {r.workflow_id: r.count for r in workflow_errors}

        # Total errors and error rate
        total_llm = await session.execute(
            select(func.count(LLMUsageModel.id)).where(
                LLMUsageModel.user_id == current_user.id,
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            )
        )
        total_llm_count = total_llm.scalar() or 0
        total_llm_errors = sum(llm_error_counts.values())

        total_agent = await session.execute(
            select(func.count(AgentExecutionModel.id)).where(
                AgentExecutionModel.user_id == current_user.id,
                AgentExecutionModel.timestamp >= start,
                AgentExecutionModel.timestamp <= end,
            )
        )
        total_agent_count = total_agent.scalar() or 0
        total_agent_errors = sum(agent_error_type_counts.values())

        total_operations = total_llm_count + total_agent_count
        total_errors = total_llm_errors + total_agent_errors
        error_rate = total_errors / total_operations if total_operations > 0 else 0

        # Combine error types
        by_type = {**llm_error_counts}
        for k, v in agent_error_type_counts.items():
            by_type[k] = by_type.get(k, 0) + v

        # Recent errors
        recent_agent_errors = await session.execute(
            select(
                AgentExecutionModel.agent_id,
                AgentExecutionModel.error_type,
                AgentExecutionModel.error_message,
                AgentExecutionModel.timestamp,
            )
            .where(
                AgentExecutionModel.user_id == current_user.id,
                AgentExecutionModel.success == False,
            )
            .order_by(desc(AgentExecutionModel.timestamp))
            .limit(10)
        )
        recent_errors = [
            {
                "source": "agent",
                "agent_id": r.agent_id,
                "error_type": r.error_type,
                "error_message": r.error_message,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in recent_agent_errors
        ]

        return ErrorStats(
            total_errors=total_errors,
            error_rate=error_rate,
            by_type=by_type,
            by_agent=by_agent,
            by_workflow=by_workflow,
            recent_errors=recent_errors,
        )


# ============================================
# Knowledge Base Analytics
# ============================================

class KnowledgeBaseStats(BaseModel):
    """Knowledge base statistics."""
    total_knowledge_bases: int
    total_documents: int
    total_chunks: int
    by_status: dict
    by_knowledge_base: List[dict]


@router.get("/analytics/knowledge", response_model=KnowledgeBaseStats)
async def get_knowledge_analytics(
    current_user: CurrentUser,
):
    """Get knowledge base analytics."""
    from sqlalchemy import func, select
    from src.storage.models import KnowledgeBaseModel, KnowledgeDocumentModel

    async with get_async_session() as session:
        # Total counts
        kb_count = await session.execute(
            select(func.count(KnowledgeBaseModel.id)).where(
                KnowledgeBaseModel.user_id == current_user.id,
            )
        )

        doc_count = await session.execute(
            select(func.count(KnowledgeDocumentModel.id))
            .join(KnowledgeBaseModel, KnowledgeDocumentModel.knowledge_base_id == KnowledgeBaseModel.id)
            .where(KnowledgeBaseModel.user_id == current_user.id)
        )

        chunk_count = await session.execute(
            select(func.sum(KnowledgeDocumentModel.chunk_count))
            .join(KnowledgeBaseModel, KnowledgeDocumentModel.knowledge_base_id == KnowledgeBaseModel.id)
            .where(KnowledgeBaseModel.user_id == current_user.id)
        )

        # By status
        by_status_query = await session.execute(
            select(
                KnowledgeBaseModel.status,
                func.count(KnowledgeBaseModel.id).label("count"),
            )
            .where(KnowledgeBaseModel.user_id == current_user.id)
            .group_by(KnowledgeBaseModel.status)
        )
        by_status = {r.status: r.count for r in by_status_query}

        # Per knowledge base
        kb_details = await session.execute(
            select(
                KnowledgeBaseModel.id,
                KnowledgeBaseModel.name,
                KnowledgeBaseModel.document_count,
                KnowledgeBaseModel.chunk_count,
                KnowledgeBaseModel.status,
            ).where(KnowledgeBaseModel.user_id == current_user.id)
        )
        by_kb = [
            {
                "id": r.id,
                "name": r.name,
                "document_count": r.document_count,
                "chunk_count": r.chunk_count,
                "status": r.status,
            }
            for r in kb_details
        ]

        return KnowledgeBaseStats(
            total_knowledge_bases=kb_count.scalar() or 0,
            total_documents=doc_count.scalar() or 0,
            total_chunks=chunk_count.scalar() or 0,
            by_status=by_status,
            by_knowledge_base=by_kb,
        )


# ============================================
# Cost Analytics
# ============================================

@router.get("/analytics/cost/breakdown")
async def get_cost_breakdown(
    current_user: CurrentUser,
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """Get cost breakdown by provider, model, and agent."""
    from sqlalchemy import func, select
    from src.monitoring.analytics.models import LLMUsageModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=30)

    async with get_async_session() as session:
        # Total cost
        total_cost = await session.execute(
            select(func.sum(LLMUsageModel.cost_cents)).where(
                LLMUsageModel.user_id == current_user.id,
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            )
        )

        # By provider
        by_provider = await session.execute(
            select(
                LLMUsageModel.provider,
                func.sum(LLMUsageModel.cost_cents).label("cost"),
                func.sum(LLMUsageModel.total_tokens).label("tokens"),
            )
            .where(
                LLMUsageModel.user_id == current_user.id,
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            )
            .group_by(LLMUsageModel.provider)
        )
        provider_breakdown = [
            {"provider": r.provider, "cost_cents": r.cost or 0, "tokens": r.tokens or 0}
            for r in by_provider
        ]

        # By model
        by_model = await session.execute(
            select(
                LLMUsageModel.model,
                func.sum(LLMUsageModel.cost_cents).label("cost"),
                func.sum(LLMUsageModel.total_tokens).label("tokens"),
            )
            .where(
                LLMUsageModel.user_id == current_user.id,
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            )
            .group_by(LLMUsageModel.model)
        )
        model_breakdown = [
            {"model": r.model, "cost_cents": r.cost or 0, "tokens": r.tokens or 0}
            for r in by_model
        ]

        # By agent
        by_agent = await session.execute(
            select(
                LLMUsageModel.agent_id,
                func.sum(LLMUsageModel.cost_cents).label("cost"),
                func.count(LLMUsageModel.id).label("calls"),
            )
            .where(
                LLMUsageModel.user_id == current_user.id,
                LLMUsageModel.agent_id.isnot(None),
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            )
            .group_by(LLMUsageModel.agent_id)
        )
        agent_breakdown = [
            {"agent_id": r.agent_id, "cost_cents": r.cost or 0, "calls": r.calls}
            for r in by_agent
        ]

        return {
            "total_cost_cents": total_cost.scalar() or 0,
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "by_provider": provider_breakdown,
            "by_model": model_breakdown,
            "by_agent": agent_breakdown,
        }


@router.get("/analytics/cost/trend")
async def get_cost_trend(
    current_user: CurrentUser,
    interval: str = Query("1d", description="Bucket interval: 1h, 1d, 1w"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """Get cost trend over time."""
    from sqlalchemy import func, select
    from src.monitoring.analytics.models import LLMUsageModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=30)

    interval_map = {"1h": "hour", "1d": "day", "1w": "week"}
    trunc_interval = interval_map.get(interval, "day")

    async with get_async_session() as session:
        query = await session.execute(
            select(
                func.date_trunc(trunc_interval, LLMUsageModel.timestamp).label("bucket"),
                func.sum(LLMUsageModel.cost_cents).label("cost"),
                func.sum(LLMUsageModel.total_tokens).label("tokens"),
                func.count(LLMUsageModel.id).label("requests"),
            )
            .where(
                LLMUsageModel.user_id == current_user.id,
                LLMUsageModel.timestamp >= start,
                LLMUsageModel.timestamp <= end,
            )
            .group_by("bucket")
            .order_by("bucket")
        )

        return {
            "interval": interval,
            "data": [
                {
                    "timestamp": row.bucket.isoformat(),
                    "cost_cents": row.cost or 0,
                    "tokens": row.tokens or 0,
                    "requests": row.requests,
                }
                for row in query
            ]
        }


# ============================================
# Agent Timeseries Analytics
# ============================================

@router.get("/analytics/agents/timeseries")
async def get_agent_timeseries(
    current_user: CurrentUser,
    metric: str = Query("executions", description="Metric: executions, latency, success_rate"),
    interval: str = Query("1h", description="Bucket interval: 1h, 6h, 1d"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
):
    """Get agent execution metrics as time series for charts."""
    from sqlalchemy import case, func, select
    from src.monitoring.analytics.models import AgentExecutionModel

    if not end:
        end = datetime.now(timezone.utc)
    if not start:
        start = end - timedelta(days=7)

    interval_map = {"1h": "hour", "6h": "hour", "1d": "day"}
    trunc_interval = interval_map.get(interval, "hour")

    async with get_async_session() as session:
        if metric == "success_rate":
            query = await session.execute(
                select(
                    func.date_trunc(trunc_interval, AgentExecutionModel.timestamp).label("bucket"),
                    (func.sum(case((AgentExecutionModel.success == True, 1), else_=0)) * 100.0 /
                     func.nullif(func.count(AgentExecutionModel.id), 0)).label("value"),
                ).where(
                    AgentExecutionModel.user_id == current_user.id,
                    AgentExecutionModel.timestamp >= start,
                    AgentExecutionModel.timestamp <= end,
                ).group_by("bucket").order_by("bucket")
            )
        else:
            metric_map = {
                "executions": func.count(AgentExecutionModel.id),
                "latency": func.avg(AgentExecutionModel.latency_ms),
            }
            metric_col = metric_map.get(metric, func.count(AgentExecutionModel.id))

            query = await session.execute(
                select(
                    func.date_trunc(trunc_interval, AgentExecutionModel.timestamp).label("bucket"),
                    metric_col.label("value"),
                ).where(
                    AgentExecutionModel.user_id == current_user.id,
                    AgentExecutionModel.timestamp >= start,
                    AgentExecutionModel.timestamp <= end,
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
