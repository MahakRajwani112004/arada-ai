"""Temporal Schedule Service - manages cron-based workflow schedules via Temporal.

Temporal Schedules provide reliable, distributed cron-like scheduling with:
- Exactly-once execution semantics
- Timezone support
- Automatic catchup for missed runs
- Schedule pause/resume
"""
import os
from datetime import timedelta
from typing import Any, Dict, List, Optional

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleCalendarSpec,
    ScheduleHandle,
    ScheduleIntervalSpec,
    SchedulePolicy,
    ScheduleSpec,
    ScheduleState,
)
from temporalio.common import TypedSearchAttributes

from src.config.logging import get_logger
from src.utils import parse_cron

logger = get_logger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "agent-tasks")
WORKFLOW_TIMEOUT_SECONDS = int(os.getenv("WORKFLOW_TIMEOUT_SECONDS", "600"))


class ScheduleService:
    """Service for managing Temporal Schedules for workflow execution."""

    def __init__(self, client: Optional[Client] = None):
        """Initialize with optional Temporal client."""
        self._client = client

    async def get_client(self) -> Client:
        """Get or create Temporal client."""
        if self._client is None:
            self._client = await Client.connect(TEMPORAL_HOST)
        return self._client

    async def create_schedule(
        self,
        schedule_id: str,
        workflow_id: str,
        cron_expression: str,
        timezone: str = "UTC",
        input_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        enabled: bool = True,
    ) -> str:
        """Create a Temporal Schedule for a workflow.

        Args:
            schedule_id: Unique ID for the schedule (from our DB)
            workflow_id: The MagoneAI workflow ID to execute
            cron_expression: 5-field cron expression
            timezone: IANA timezone name
            input_text: Static input for each scheduled run
            context: Additional context for scheduled runs
            user_id: User who owns the schedule
            enabled: Whether the schedule is active

        Returns:
            Temporal schedule ID
        """
        client = await self.get_client()

        # Parse cron expression to get calendar spec
        cron = parse_cron(cron_expression)

        # Build Temporal schedule ID
        temporal_schedule_id = f"workflow-schedule-{schedule_id}"

        # Create workflow input for scheduled executions
        workflow_input = ScheduledWorkflowInput(
            workflow_id=workflow_id,
            schedule_id=schedule_id,
            user_input=input_text or "",
            user_id=user_id or "scheduler",
            context=context or {},
            triggered_by="schedule",
        )

        # Build calendar spec from cron expression
        calendar_specs = self._cron_to_calendar_specs(cron)

        # Create the schedule
        schedule = Schedule(
            action=ScheduleActionStartWorkflow(
                ScheduledWorkflowExecution.run,
                workflow_input,
                id=f"scheduled-{workflow_id}-{{workflow.scheduledTime}}",
                task_queue=TASK_QUEUE,
                execution_timeout=timedelta(seconds=WORKFLOW_TIMEOUT_SECONDS),
            ),
            spec=ScheduleSpec(
                calendars=calendar_specs,
                timezone_name=timezone,
            ),
            policy=SchedulePolicy(
                catchup_window=timedelta(hours=1),  # Catch up missed runs within 1 hour
                pause_on_failure=False,
            ),
            state=ScheduleState(
                paused=not enabled,
            ),
        )

        await client.create_schedule(
            temporal_schedule_id,
            schedule,
        )

        logger.info(
            "temporal_schedule_created",
            schedule_id=schedule_id,
            temporal_schedule_id=temporal_schedule_id,
            workflow_id=workflow_id,
            cron_expression=cron_expression,
        )

        return temporal_schedule_id

    async def update_schedule(
        self,
        temporal_schedule_id: str,
        cron_expression: Optional[str] = None,
        timezone: Optional[str] = None,
        input_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        """Update an existing Temporal Schedule.

        Args:
            temporal_schedule_id: The Temporal schedule ID
            cron_expression: New cron expression (optional)
            timezone: New timezone (optional)
            input_text: New input text (optional)
            context: New context (optional)
            enabled: New enabled state (optional)
        """
        client = await self.get_client()

        try:
            handle = client.get_schedule_handle(temporal_schedule_id)

            async def update_fn(input: Schedule) -> Schedule:
                """Update the schedule configuration."""
                if cron_expression is not None:
                    cron = parse_cron(cron_expression)
                    input.spec.calendars = self._cron_to_calendar_specs(cron)

                if timezone is not None:
                    input.spec.timezone_name = timezone

                if enabled is not None:
                    input.state.paused = not enabled

                # Update workflow input if needed
                if (input_text is not None or context is not None) and isinstance(
                    input.action, ScheduleActionStartWorkflow
                ):
                    # Update the workflow input args
                    if input.action.args:
                        workflow_input = input.action.args[0]
                        if isinstance(workflow_input, ScheduledWorkflowInput):
                            if input_text is not None:
                                workflow_input.user_input = input_text
                            if context is not None:
                                workflow_input.context = context
                            input.action.args = [workflow_input]

                return input

            await handle.update(update_fn)

            logger.info(
                "temporal_schedule_updated",
                temporal_schedule_id=temporal_schedule_id,
            )

        except Exception as e:
            logger.error(
                "temporal_schedule_update_failed",
                temporal_schedule_id=temporal_schedule_id,
                error=str(e),
            )
            raise

    async def delete_schedule(self, temporal_schedule_id: str) -> None:
        """Delete a Temporal Schedule.

        Args:
            temporal_schedule_id: The Temporal schedule ID
        """
        client = await self.get_client()

        try:
            handle = client.get_schedule_handle(temporal_schedule_id)
            await handle.delete()

            logger.info(
                "temporal_schedule_deleted",
                temporal_schedule_id=temporal_schedule_id,
            )

        except Exception as e:
            logger.error(
                "temporal_schedule_delete_failed",
                temporal_schedule_id=temporal_schedule_id,
                error=str(e),
            )
            raise

    async def pause_schedule(self, temporal_schedule_id: str) -> None:
        """Pause a Temporal Schedule."""
        client = await self.get_client()
        handle = client.get_schedule_handle(temporal_schedule_id)
        await handle.pause()
        logger.info("temporal_schedule_paused", temporal_schedule_id=temporal_schedule_id)

    async def resume_schedule(self, temporal_schedule_id: str) -> None:
        """Resume a paused Temporal Schedule."""
        client = await self.get_client()
        handle = client.get_schedule_handle(temporal_schedule_id)
        await handle.unpause()
        logger.info("temporal_schedule_resumed", temporal_schedule_id=temporal_schedule_id)

    async def get_schedule_info(self, temporal_schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a Temporal Schedule.

        Returns:
            Schedule info dict or None if not found
        """
        client = await self.get_client()

        try:
            handle = client.get_schedule_handle(temporal_schedule_id)
            desc = await handle.describe()

            return {
                "id": desc.id,
                "is_paused": desc.schedule.state.paused,
                "next_action_times": [t.isoformat() for t in desc.info.next_action_times[:5]],
                "recent_actions": [
                    {
                        "scheduled_at": a.scheduled_at.isoformat() if a.scheduled_at else None,
                        "started_at": a.started_at.isoformat() if a.started_at else None,
                    }
                    for a in desc.info.recent_actions[:10]
                ],
                "running_workflows": [
                    {
                        "workflow_id": r.workflow_id,
                        "run_id": r.first_execution_run_id,
                    }
                    for r in desc.info.running_workflows
                ],
            }

        except Exception as e:
            logger.warning(
                "temporal_schedule_info_failed",
                temporal_schedule_id=temporal_schedule_id,
                error=str(e),
            )
            return None

    def _cron_to_calendar_specs(self, cron) -> List[ScheduleCalendarSpec]:
        """Convert parsed cron expression to Temporal ScheduleCalendarSpec.

        Args:
            cron: Parsed CronExpression object

        Returns:
            List of ScheduleCalendarSpec
        """
        # Temporal uses different day_of_week values: 0=Sunday to 6=Saturday (same as cron)
        return [
            ScheduleCalendarSpec(
                minute=list(cron.minute),
                hour=list(cron.hour),
                day_of_month=list(cron.day),
                month=list(cron.month),
                day_of_week=list(cron.day_of_week),
            )
        ]


# Scheduled workflow input (separate from regular workflow input)
from dataclasses import dataclass


@dataclass
class ScheduledWorkflowInput:
    """Input for scheduled workflow executions."""
    workflow_id: str  # The MagoneAI workflow ID
    schedule_id: str  # The schedule ID for tracking
    user_input: str
    user_id: str
    context: Dict[str, Any]
    triggered_by: str = "schedule"


# Scheduled workflow execution wrapper
from temporalio import workflow


@workflow.defn(name="ScheduledWorkflowExecution")
class ScheduledWorkflowExecution:
    """Workflow that wraps scheduled execution of MagoneAI workflows.

    This workflow is triggered by Temporal Schedules and:
    1. Loads the workflow definition from the database
    2. Executes the workflow using the standard executor
    3. Records execution results
    """

    @workflow.run
    async def run(self, input: ScheduledWorkflowInput) -> Dict[str, Any]:
        """Execute a scheduled workflow run."""
        from temporalio import activity

        # Execute the scheduled workflow activity
        result = await workflow.execute_activity(
            "execute_scheduled_workflow",
            input,
            start_to_close_timeout=timedelta(seconds=WORKFLOW_TIMEOUT_SECONDS),
        )

        return result
