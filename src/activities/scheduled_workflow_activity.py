"""Activity for executing scheduled workflows.

This activity is called by ScheduledWorkflowExecution when a Temporal Schedule triggers.
It loads the workflow definition and executes it using the standard workflow executor.
"""
from datetime import datetime, timezone
from typing import Any, Dict

from temporalio import activity

from src.config.logging import get_logger
from src.workflows.schedule_service import ScheduledWorkflowInput

logger = get_logger(__name__)


@activity.defn(name="execute_scheduled_workflow")
async def execute_scheduled_workflow(input: ScheduledWorkflowInput) -> Dict[str, Any]:
    """Execute a scheduled workflow.

    Args:
        input: ScheduledWorkflowInput with workflow_id, schedule_id, user_input, etc.

    Returns:
        Execution result dict with status, output, and error information
    """
    from src.storage.database import get_async_session
    from src.storage.workflow_repository import WorkflowRepository
    from src.storage.schedule_repository import ScheduleRepository
    from src.storage import PostgresAgentRepository
    from src.workflows.executor import WorkflowExecutor

    logger.info(
        "scheduled_workflow_execution_started",
        workflow_id=input.workflow_id,
        schedule_id=input.schedule_id,
        triggered_by=input.triggered_by,
    )

    execution_result = {
        "workflow_id": input.workflow_id,
        "schedule_id": input.schedule_id,
        "status": "unknown",
        "output": None,
        "error": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }

    try:
        async with get_async_session() as session:
            # Initialize repositories
            workflow_repo = WorkflowRepository(session)
            schedule_repo = ScheduleRepository(session, user_id=input.user_id)
            agent_repo = PostgresAgentRepository(session, user_id=input.user_id)

            # Verify workflow exists
            workflow = await workflow_repo.get(input.workflow_id)
            if not workflow:
                error_msg = f"Workflow '{input.workflow_id}' not found"
                logger.error(
                    "scheduled_workflow_not_found",
                    workflow_id=input.workflow_id,
                    schedule_id=input.schedule_id,
                )
                # Record error in schedule
                await schedule_repo.record_run(
                    schedule_id=input.schedule_id,
                    success=False,
                    error=error_msg,
                )
                execution_result["status"] = "failed"
                execution_result["error"] = error_msg
                execution_result["completed_at"] = datetime.now(timezone.utc).isoformat()
                return execution_result

            # Execute the workflow
            executor = WorkflowExecutor(
                agent_repo=agent_repo,
                workflow_repo=workflow_repo,
                temporal_client=None,  # Don't use Temporal for inner execution
            )

            execution_id, exec_status, step_results, final_output, error = await executor.execute(
                workflow_id=input.workflow_id,
                user_input=input.user_input,
                user_id=input.user_id,
                context=input.context,
                session_id=f"scheduled-{input.schedule_id}",
                conversation_history=[],
            )

            # Record successful run
            success = exec_status in ["completed", "COMPLETED"]
            await schedule_repo.record_run(
                schedule_id=input.schedule_id,
                success=success,
                error=error if not success else None,
            )

            execution_result["status"] = exec_status
            execution_result["output"] = final_output
            execution_result["error"] = error
            execution_result["execution_id"] = execution_id
            execution_result["step_count"] = len(step_results)
            execution_result["completed_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(
                "scheduled_workflow_execution_completed",
                workflow_id=input.workflow_id,
                schedule_id=input.schedule_id,
                execution_id=execution_id,
                status=exec_status,
            )

            await session.commit()

            return execution_result

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        logger.error(
            "scheduled_workflow_execution_failed",
            workflow_id=input.workflow_id,
            schedule_id=input.schedule_id,
            error=error_msg,
            exc_info=True,
        )

        # Try to record the error
        try:
            async with get_async_session() as session:
                schedule_repo = ScheduleRepository(session, user_id=input.user_id)
                await schedule_repo.record_run(
                    schedule_id=input.schedule_id,
                    success=False,
                    error=error_msg,
                )
                await session.commit()
        except Exception as record_error:
            logger.error(
                "scheduled_workflow_record_error_failed",
                schedule_id=input.schedule_id,
                error=str(record_error),
            )

        execution_result["status"] = "failed"
        execution_result["error"] = error_msg
        execution_result["completed_at"] = datetime.now(timezone.utc).isoformat()

        return execution_result
