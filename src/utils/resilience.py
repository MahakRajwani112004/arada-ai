"""Resilience utilities for external service calls.

Provides circuit breaker and retry decorators for handling failures
in external services (LLM providers, MCP servers, etc.).
"""
import asyncio
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from circuitbreaker import CircuitBreakerError, circuit
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exceptions: tuple = (Exception,),
    name: Optional[str] = None,
) -> Callable[[F], F]:
    """Circuit breaker decorator for external service calls.

    Opens the circuit after `failure_threshold` failures, preventing
    further calls for `recovery_timeout` seconds. This allows the
    external service time to recover.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exceptions: Exceptions that trigger the circuit
        name: Optional name for the circuit (for logging)

    Returns:
        Decorated function with circuit breaker protection

    Example:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30)
        async def call_external_api():
            ...
    """
    def decorator(func: F) -> F:
        circuit_name = name or func.__name__

        # Use the library's circuit decorator directly
        protected = circuit(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exceptions,
            name=circuit_name,
        )(func)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await protected(*args, **kwargs)
            except CircuitBreakerError as e:
                logger.warning(
                    "circuit_breaker_open",
                    circuit=circuit_name,
                    error=str(e),
                )
                raise
            except expected_exceptions as e:
                logger.warning(
                    "circuit_breaker_failure",
                    circuit=circuit_name,
                    error=str(e),
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return protected(*args, **kwargs)
            except CircuitBreakerError as e:
                logger.warning(
                    "circuit_breaker_open",
                    circuit=circuit_name,
                    error=str(e),
                )
                raise
            except expected_exceptions as e:
                logger.warning(
                    "circuit_breaker_failure",
                    circuit=circuit_name,
                    error=str(e),
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
    multiplier: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """Retry decorator with exponential backoff.

    Automatically retries failed calls with increasing delays.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        multiplier: Multiplier for exponential backoff
        retryable_exceptions: Exceptions that trigger retry

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff(max_attempts=3, min_wait=1, max_wait=10)
        async def call_flaky_service():
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(
                        multiplier=multiplier,
                        min=min_wait,
                        max=max_wait,
                    ),
                    retry=retry_if_exception_type(retryable_exceptions),
                    reraise=True,
                ):
                    with attempt:
                        if attempt.retry_state.attempt_number > 1:
                            logger.info(
                                "retry_attempt",
                                function=func.__name__,
                                attempt=attempt.retry_state.attempt_number,
                                max_attempts=max_attempts,
                            )
                        return await func(*args, **kwargs)
            except RetryError as e:
                logger.error(
                    "retry_exhausted",
                    function=func.__name__,
                    max_attempts=max_attempts,
                    error=str(e.last_attempt.exception()),
                )
                raise e.last_attempt.exception()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            from tenacity import Retrying

            try:
                for attempt in Retrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(
                        multiplier=multiplier,
                        min=min_wait,
                        max=max_wait,
                    ),
                    retry=retry_if_exception_type(retryable_exceptions),
                    reraise=True,
                ):
                    with attempt:
                        if attempt.retry_state.attempt_number > 1:
                            logger.info(
                                "retry_attempt",
                                function=func.__name__,
                                attempt=attempt.retry_state.attempt_number,
                            )
                        return func(*args, **kwargs)
            except RetryError as e:
                raise e.last_attempt.exception()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def resilient(
    circuit_failure_threshold: int = 5,
    circuit_recovery_timeout: int = 60,
    retry_max_attempts: int = 3,
    retry_min_wait: float = 1.0,
    retry_max_wait: float = 30.0,
    expected_exceptions: tuple = (Exception,),
    name: Optional[str] = None,
) -> Callable[[F], F]:
    """Combined circuit breaker and retry decorator.

    First applies retry with backoff, then circuit breaker.
    This means retries happen first, and if they all fail,
    it counts as a circuit breaker failure.

    Args:
        circuit_failure_threshold: Failures before opening circuit
        circuit_recovery_timeout: Seconds to wait before recovery
        retry_max_attempts: Maximum retry attempts per call
        retry_min_wait: Minimum wait between retries
        retry_max_wait: Maximum wait between retries
        expected_exceptions: Exceptions that trigger both retry and circuit
        name: Optional name for the circuit

    Returns:
        Decorated function with both protections

    Example:
        @resilient(circuit_failure_threshold=3, retry_max_attempts=2)
        async def call_llm_provider():
            ...
    """
    def decorator(func: F) -> F:
        # Apply retry first (inner), then circuit breaker (outer)
        retried = retry_with_backoff(
            max_attempts=retry_max_attempts,
            min_wait=retry_min_wait,
            max_wait=retry_max_wait,
            retryable_exceptions=expected_exceptions,
        )(func)

        protected = circuit_breaker(
            failure_threshold=circuit_failure_threshold,
            recovery_timeout=circuit_recovery_timeout,
            expected_exceptions=expected_exceptions,
            name=name,
        )(retried)

        return protected  # type: ignore

    return decorator


# Re-export CircuitBreakerError for consumers
__all__ = [
    "circuit_breaker",
    "retry_with_backoff",
    "resilient",
    "CircuitBreakerError",
]
