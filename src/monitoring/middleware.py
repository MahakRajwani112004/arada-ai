"""Metrics middleware for HTTP request instrumentation."""
import re
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .metrics import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
)


def _normalize_path(path: str) -> str:
    """
    Normalize path to prevent high cardinality labels.

    Replaces dynamic path segments (UUIDs, IDs) with placeholders.
    Example: /api/v1/agents/abc-123-def -> /api/v1/agents/{id}
    """
    # Replace UUIDs (with or without hyphens)
    path = re.sub(
        r"/[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}",
        "/{id}",
        path,
    )
    # Replace numeric IDs
    path = re.sub(r"/\d+", "/{id}", path)

    return path


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus HTTP metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Record metrics for each HTTP request."""
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Skip health check to reduce noise
        if request.url.path == "/health":
            return await call_next(request)

        method = request.method
        path = _normalize_path(request.url.path)

        # Track in-progress requests
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).inc()

        start_time = time.perf_counter()
        status_code = 500  # Default to 500 in case of unhandled exception

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            # Record duration
            duration = time.perf_counter() - start_time
            HTTP_REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

            # Record request count
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=path,
                status_code=str(status_code),
            ).inc()

            # Decrement in-progress
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).dec()
