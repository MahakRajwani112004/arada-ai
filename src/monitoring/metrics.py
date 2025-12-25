"""Prometheus metric definitions for the Magure AI Platform."""
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from fastapi import APIRouter, Response

from src.config.settings import get_settings

settings = get_settings()
PREFIX = settings.metrics_prefix

# =============================================================================
# HTTP Metrics
# =============================================================================

HTTP_REQUESTS_TOTAL = Counter(
    f"{PREFIX}_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    f"{PREFIX}_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    f"{PREFIX}_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# =============================================================================
# Agent Metrics
# =============================================================================

AGENT_EXECUTIONS_TOTAL = Counter(
    f"{PREFIX}_agent_executions_total",
    "Total number of agent executions",
    ["agent_id", "agent_type", "status"],
)

AGENT_EXECUTION_DURATION = Histogram(
    f"{PREFIX}_agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_id", "agent_type"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
)

# =============================================================================
# LLM Metrics
# =============================================================================

LLM_REQUESTS_TOTAL = Counter(
    f"{PREFIX}_llm_requests_total",
    "Total number of LLM API requests",
    ["provider", "model", "status"],
)

LLM_REQUEST_DURATION = Histogram(
    f"{PREFIX}_llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["provider", "model"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

LLM_TOKENS_TOTAL = Counter(
    f"{PREFIX}_llm_tokens_total",
    "Total number of tokens used",
    ["provider", "model", "token_type"],  # token_type: prompt, completion
)

LLM_COST_CENTS_TOTAL = Counter(
    f"{PREFIX}_llm_cost_cents_total",
    "Total cost in cents",
    ["provider", "model"],
)

# =============================================================================
# Workflow Metrics
# =============================================================================

WORKFLOW_EXECUTIONS_TOTAL = Counter(
    f"{PREFIX}_workflow_executions_total",
    "Total number of workflow executions",
    ["workflow_id", "status"],
)

WORKFLOW_DURATION = Histogram(
    f"{PREFIX}_workflow_duration_seconds",
    "Workflow execution duration in seconds",
    ["workflow_id"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
)

WORKFLOWS_ACTIVE = Gauge(
    f"{PREFIX}_workflows_active",
    "Number of currently active workflows",
)


# =============================================================================
# Metrics Endpoint Router
# =============================================================================


def get_metrics_router() -> APIRouter:
    """Create a router for the /metrics endpoint."""
    router = APIRouter(tags=["Monitoring"])

    @router.get("/metrics")
    async def metrics() -> Response:
        """Expose Prometheus metrics for scraping."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    return router
