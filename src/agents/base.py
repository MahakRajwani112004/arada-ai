"""Base agent class - all agent types inherit from this with instrumentation."""
import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.config.logging import get_logger
from src.config.settings import get_settings
from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse

logger = get_logger(__name__)
settings = get_settings()


class BaseAgent(ABC):
    """
    Abstract base agent class with automatic instrumentation.

    All agent types inherit from this and implement _execute_impl().
    The execute() method wraps _execute_impl() with monitoring.
    The config determines behavior, not the class.
    """

    def __init__(self, config: AgentConfig):
        """Initialize agent with configuration."""
        self.config = config
        self.id = config.id
        self.name = config.name

    async def execute(self, context: AgentContext) -> AgentResponse:
        """
        Execute the agent's logic with instrumentation.

        This is an instrumented wrapper that:
        1. Records timing
        2. Logs the execution
        3. Sends metrics to Prometheus
        4. Saves analytics to PostgreSQL

        Args:
            context: Runtime context with user input and session info

        Returns:
            AgentResponse with content and metadata
        """
        start_time = time.perf_counter()
        success = True
        error_type = None
        error_message = None

        try:
            # Call the actual implementation
            response = await self._execute_impl(context)
            return response

        except Exception as e:
            success = False
            error_type = type(e).__name__
            error_message = str(e)
            raise

        finally:
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # Get agent type from config
            agent_type = self.config.type.value if hasattr(self.config.type, "value") else str(self.config.type)

            # Extract request_id and workflow_id from context if available
            request_id = getattr(context, "request_id", None)
            workflow_id = getattr(context, "workflow_id", None)

            # Record Prometheus metrics
            if settings.monitoring_enabled:
                self._record_prometheus_metrics(
                    agent_type=agent_type,
                    success=success,
                    latency_ms=latency_ms,
                )

            # Record to PostgreSQL (async, non-blocking)
            if settings.analytics_enabled:
                asyncio.create_task(
                    self._record_analytics(
                        agent_type=agent_type,
                        latency_ms=latency_ms,
                        success=success,
                        request_id=request_id,
                        workflow_id=workflow_id,
                        error_type=error_type,
                        error_message=error_message,
                    )
                )

            # Log the execution
            log_method = logger.info if success else logger.warning
            log_method(
                "agent_execution_completed",
                agent_id=self.id,
                agent_type=agent_type,
                latency_ms=latency_ms,
                success=success,
                error_type=error_type,
            )

    def _record_prometheus_metrics(
        self,
        agent_type: str,
        success: bool,
        latency_ms: int,
    ) -> None:
        """Record metrics to Prometheus."""
        try:
            from src.monitoring.metrics import (
                AGENT_EXECUTION_DURATION,
                AGENT_EXECUTIONS_TOTAL,
            )

            status = "success" if success else "failure"

            # Execution count
            AGENT_EXECUTIONS_TOTAL.labels(
                agent_id=self.id,
                agent_type=agent_type,
                status=status,
            ).inc()

            # Execution duration
            AGENT_EXECUTION_DURATION.labels(
                agent_id=self.id,
                agent_type=agent_type,
            ).observe(latency_ms / 1000)  # Convert to seconds

        except Exception as e:
            # Metrics should never break the main flow
            logger.debug("prometheus_metrics_failed", error=str(e))

    async def _record_analytics(
        self,
        agent_type: str,
        latency_ms: int,
        success: bool,
        request_id: Optional[str],
        workflow_id: Optional[str],
        error_type: Optional[str],
        error_message: Optional[str],
    ) -> None:
        """Record analytics to PostgreSQL."""
        try:
            from src.monitoring.analytics import get_analytics_service

            service = get_analytics_service()
            await service.record_agent_execution(
                agent_id=self.id,
                agent_type=agent_type,
                latency_ms=latency_ms,
                success=success,
                request_id=request_id,
                workflow_id=workflow_id,
                error_type=error_type,
                error_message=error_message,
            )
        except Exception as e:
            # Analytics should never break the main flow
            logger.debug("analytics_record_failed", error=str(e))

    @abstractmethod
    async def _execute_impl(self, context: AgentContext) -> AgentResponse:
        """
        Actual implementation of agent execution.

        Subclasses implement this method instead of execute().
        The execute() method wraps this with instrumentation.

        This is implemented differently by each agent type:
        - SimpleAgent: Template/rule matching
        - LLMAgent: Single LLM call
        - RAGAgent: Retrieve + LLM
        - ToolAgent: LLM + Tool loop
        - FullAgent: Retrieve + LLM + Tool loop
        - RouterAgent: Classify + Route

        Args:
            context: Runtime context with user input and session info

        Returns:
            AgentResponse with content and metadata
        """
        pass

    def build_system_prompt(self) -> str:
        """Build system prompt from config."""
        parts = []

        # Current date/time context
        now = datetime.now()
        parts.append(
            f"## CURRENT DATE/TIME\n"
            f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Today is {now.strftime('%A, %B %d, %Y')}"
        )

        # Role section
        role = self.config.role
        parts.append(f"## ROLE\nYou are {role.title}.")
        if role.expertise:
            parts.append(f"Your expertise: {', '.join(role.expertise)}.")
        if role.personality:
            parts.append(f"Your personality: {', '.join(role.personality)}.")
        parts.append(f"Communication style: {role.communication_style}.")

        # Goal section
        goal = self.config.goal
        parts.append(f"\n## GOAL\n{goal.objective}")
        if goal.constraints:
            parts.append("\nConstraints:")
            for constraint in goal.constraints:
                parts.append(f"- {constraint}")

        # Instructions section
        instructions = self.config.instructions
        if instructions.steps:
            parts.append("\n## INSTRUCTIONS")
            for i, step in enumerate(instructions.steps, 1):
                parts.append(f"{i}. {step}")

        if instructions.rules:
            parts.append("\n## RULES")
            for rule in instructions.rules:
                parts.append(f"- {rule}")

        if instructions.prohibited:
            parts.append("\n## PROHIBITED")
            for prohibited in instructions.prohibited:
                parts.append(f"- DO NOT: {prohibited}")

        if instructions.output_format:
            parts.append(f"\n## OUTPUT FORMAT\n{instructions.output_format}")

        # Examples section
        if self.config.examples:
            parts.append("\n## EXAMPLES")
            for example in self.config.examples[:3]:  # Max 3 examples
                parts.append(f"\nInput: {example.input}")
                parts.append(f"Output: {example.output}")

        # Note: Tools are provided via native function calling, not in system prompt
        # The LLM receives tool definitions through the API's tool/function calling feature

        return "\n".join(parts)

    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tool IDs."""
        return [
            tool.tool_id for tool in self.config.tools if tool.enabled
        ]

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"
