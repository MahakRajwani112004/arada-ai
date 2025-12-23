"""Centralized error handling for the API."""
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.config.logging import get_logger

logger = get_logger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier},
        )


class ValidationError(AppException):
    """Input validation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class WorkflowError(AppException):
    """Workflow execution error."""

    def __init__(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if workflow_id:
            error_details["workflow_id"] = workflow_id
        super().__init__(
            message=message,
            error_code="WORKFLOW_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details,
        )


class WorkflowTimeoutError(AppException):
    """Workflow execution timeout error."""

    def __init__(self, workflow_id: str, timeout_seconds: int):
        super().__init__(
            message=f"Workflow execution timed out after {timeout_seconds} seconds",
            error_code="WORKFLOW_TIMEOUT",
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            details={"workflow_id": workflow_id, "timeout_seconds": timeout_seconds},
        )


class ExternalServiceError(AppException):
    """Error from external service (LLM, MCP, etc.)."""

    def __init__(
        self,
        service: str,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        error_details["service"] = service
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=error_details,
        )


class RateLimitError(AppException):
    """Rate limit exceeded error."""

    def __init__(self, limit: str):
        super().__init__(
            message=f"Rate limit exceeded: {limit}",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"limit": limit},
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    request_id = getattr(request.state, "request_id", None)

    # Log the error with context
    logger.error(
        "app_exception",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
        path=str(request.url.path),
        details=exc.details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions without exposing internal details."""
    request_id = getattr(request.state, "request_id", None)

    # Log the full error internally
    logger.error(
        "unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        request_id=request_id,
        path=str(request.url.path),
        exc_info=True,
    )

    # Return generic message to client (don't expose internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
            request_id=request_id,
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException."""
    request_id = getattr(request.state, "request_id", None)

    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=request_id,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=str(exc.detail),
            request_id=request_id,
        ).model_dump(),
    )
