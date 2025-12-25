"""Base LLM provider interface with instrumentation."""
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

from src.config.logging import get_logger
from src.config.settings import get_settings
from src.models.llm_config import LLMConfig

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class LLMMessage:
    """Message for LLM conversation."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: Optional[str] = None  # For tool result messages
    tool_calls: Optional[List["ToolCall"]] = None  # For assistant messages with tool calls


@dataclass
class ToolCall:
    """A tool call from the LLM."""

    id: str  # Unique ID for the tool call
    name: str  # Tool name
    arguments: Dict[str, Any]  # Parsed arguments


@dataclass
class ToolDefinition:
    """Tool definition for LLM function calling."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    content: str
    model: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: str
    tool_calls: List[ToolCall] = field(default_factory=list)  # Tool calls if any
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers with automatic instrumentation."""

    # Override this in subclasses
    _provider_name: str = "unknown"

    def __init__(self, config: LLMConfig):
        """Initialize provider with config."""
        self.config = config
        self.model = config.model

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        tools: Optional[List[ToolDefinition]] = None,
        *,
        # Required for user-level analytics
        user_id: str,
        # Optional context for correlation (passed by agents)
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate a completion for the given messages.

        This is an instrumented wrapper that:
        1. Records timing
        2. Logs the call
        3. Sends metrics to Prometheus
        4. Saves analytics to PostgreSQL

        Args:
            messages: List of conversation messages
            temperature: Override config temperature
            max_tokens: Override config max_tokens
            stop_sequences: Sequences that stop generation
            tools: Optional list of tools the LLM can call
            agent_id: Optional agent ID for correlation
            request_id: Optional request ID for correlation
            workflow_id: Optional workflow ID for correlation

        Returns:
            LLMResponse with content and metadata (and tool_calls if any)
        """
        start_time = time.perf_counter()
        success = True
        error_type = None
        error_message = None
        response: Optional[LLMResponse] = None

        try:
            # Call the actual implementation
            response = await self._complete_impl(
                messages, temperature, max_tokens, stop_sequences, tools
            )
            return response

        except Exception as e:
            success = False
            error_type = type(e).__name__
            error_message = str(e)
            raise

        finally:
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Extract token counts (use 0 if response failed)
            prompt_tokens = 0
            completion_tokens = 0
            if response is not None:
                prompt_tokens = response.usage.get("prompt_tokens", 0)
                completion_tokens = response.usage.get("completion_tokens", 0)

            # Record Prometheus metrics
            if settings.monitoring_enabled:
                self._record_prometheus_metrics(
                    success=success,
                    latency_ms=latency_ms,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )

            # Record to PostgreSQL (async, non-blocking)
            if settings.analytics_enabled:
                asyncio.create_task(
                    self._record_analytics(
                        user_id=user_id,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        latency_ms=latency_ms,
                        success=success,
                        agent_id=agent_id,
                        request_id=request_id,
                        workflow_id=workflow_id,
                        error_type=error_type,
                        error_message=error_message,
                    )
                )

            # Log the call
            log_method = logger.info if success else logger.warning
            log_method(
                "llm_call_completed",
                provider=self._provider_name,
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                success=success,
                error_type=error_type,
            )

    def _record_prometheus_metrics(
        self,
        success: bool,
        latency_ms: int,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Record metrics to Prometheus."""
        try:
            from src.monitoring.metrics import (
                LLM_COST_CENTS_TOTAL,
                LLM_REQUEST_DURATION,
                LLM_REQUESTS_TOTAL,
                LLM_TOKENS_TOTAL,
            )
            from src.monitoring.analytics.cost_calculator import calculate_cost

            status = "success" if success else "failure"

            # Request count
            LLM_REQUESTS_TOTAL.labels(
                provider=self._provider_name,
                model=self.model,
                status=status,
            ).inc()

            # Request duration
            LLM_REQUEST_DURATION.labels(
                provider=self._provider_name,
                model=self.model,
            ).observe(latency_ms / 1000)  # Convert to seconds

            # Token counts
            if prompt_tokens > 0:
                LLM_TOKENS_TOTAL.labels(
                    provider=self._provider_name,
                    model=self.model,
                    token_type="prompt",
                ).inc(prompt_tokens)

            if completion_tokens > 0:
                LLM_TOKENS_TOTAL.labels(
                    provider=self._provider_name,
                    model=self.model,
                    token_type="completion",
                ).inc(completion_tokens)

            # Cost
            if prompt_tokens > 0 or completion_tokens > 0:
                cost_cents = calculate_cost(
                    self._provider_name, self.model, prompt_tokens, completion_tokens
                )
                LLM_COST_CENTS_TOTAL.labels(
                    provider=self._provider_name,
                    model=self.model,
                ).inc(cost_cents)

        except Exception as e:
            # Metrics should never break the main flow
            logger.debug("prometheus_metrics_failed", error=str(e))

    async def _record_analytics(
        self,
        user_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        success: bool,
        agent_id: Optional[str],
        request_id: Optional[str],
        workflow_id: Optional[str],
        error_type: Optional[str],
        error_message: Optional[str],
    ) -> None:
        """Record analytics to PostgreSQL."""
        try:
            from src.monitoring.analytics import get_analytics_service

            service = get_analytics_service()
            await service.record_llm_usage(
                user_id=user_id,
                provider=self._provider_name,
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                success=success,
                agent_id=agent_id,
                request_id=request_id,
                workflow_id=workflow_id,
                error_type=error_type,
                error_message=error_message,
            )
        except Exception as e:
            # Analytics should never break the main flow
            logger.debug("analytics_record_failed", error=str(e))

    @abstractmethod
    async def _complete_impl(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        tools: Optional[List[ToolDefinition]] = None,
    ) -> LLMResponse:
        """
        Actual implementation of completion.

        Subclasses implement this method instead of complete().
        The complete() method wraps this with instrumentation.
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Stream a completion for the given messages.

        Args:
            messages: List of conversation messages
            temperature: Override config temperature
            max_tokens: Override config max_tokens

        Yields:
            Content chunks as they're generated
        """
        pass

    def _get_temperature(self, override: Optional[float]) -> float:
        """Get temperature, using override if provided."""
        if override is not None:
            return override
        return self.config.temperature

    def _get_max_tokens(self, override: Optional[int]) -> int:
        """Get max_tokens, using override if provided."""
        if override is not None:
            return override
        return self.config.max_tokens
