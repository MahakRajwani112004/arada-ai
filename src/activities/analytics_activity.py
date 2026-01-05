"""Analytics Activity - records agent execution analytics."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from temporalio import activity

from src.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RecordAgentExecutionInput:
    """Input for recording agent execution."""

    user_id: str
    agent_id: str
    agent_type: str
    latency_ms: int
    success: bool
    request_id: Optional[str] = None
    workflow_id: Optional[str] = None
    llm_calls_count: int = 0
    tool_calls_count: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    input_preview: Optional[str] = None
    output_preview: Optional[str] = None
    total_tokens: int = 0
    total_cost_cents: int = 0
    parent_execution_id: Optional[str] = None
    execution_metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class RecordAgentExecutionOutput:
    """Output from recording agent execution."""

    success: bool
    error: Optional[str] = None


@activity.defn
async def record_agent_execution(
    input: RecordAgentExecutionInput,
) -> RecordAgentExecutionOutput:
    """
    Record agent execution analytics to PostgreSQL.

    This activity is called at the end of agent workflows to record
    execution metrics for the Overview tab.
    """
    try:
        from src.monitoring.analytics import get_analytics_service

        service = get_analytics_service()
        await service.record_agent_execution(
            user_id=input.user_id,
            agent_id=input.agent_id,
            agent_type=input.agent_type,
            latency_ms=input.latency_ms,
            success=input.success,
            request_id=input.request_id,
            workflow_id=input.workflow_id,
            llm_calls_count=input.llm_calls_count,
            tool_calls_count=input.tool_calls_count,
            error_type=input.error_type,
            error_message=input.error_message,
            input_preview=input.input_preview,
            output_preview=input.output_preview,
            total_tokens=input.total_tokens,
            total_cost_cents=input.total_cost_cents,
            parent_execution_id=input.parent_execution_id,
            execution_metadata=input.execution_metadata,
        )

        activity.logger.debug(
            f"Recorded agent execution: {input.agent_id}, success={input.success}"
        )

        return RecordAgentExecutionOutput(success=True)

    except Exception as e:
        activity.logger.error(f"Failed to record agent execution: {e}")
        return RecordAgentExecutionOutput(success=False, error=str(e))
