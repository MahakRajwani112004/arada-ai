"""Workflow executor - runs multi-step workflows."""
import asyncio
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from src.api.schemas.workflows import StepExecutionResult
from src.config.logging import get_logger
from src.models.workflow_definition import (
    StepType,
    WorkflowDefinition,
    WorkflowStep,
    validate_workflow_definition,
)
from src.storage import BaseAgentRepository
from src.storage.workflow_repository import WorkflowRepository

logger = get_logger(__name__)


def _clean_none_values(data: Any) -> Any:
    """Recursively remove None values from a dict to allow defaults to apply."""
    if isinstance(data, dict):
        return {k: _clean_none_values(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [_clean_none_values(item) for item in data]
    return data


class WorkflowExecutor:
    """Executes multi-step workflows."""

    def __init__(
        self,
        agent_repo: BaseAgentRepository,
        workflow_repo: WorkflowRepository,
        temporal_client: Optional[Any] = None,
    ):
        self.agent_repo = agent_repo
        self.workflow_repo = workflow_repo
        self.temporal_client = temporal_client
        self._step_results: Dict[str, Any] = {}
        self._context: Dict[str, Any] = {}

    async def execute(
        self,
        workflow_id: str,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[str, str, List[StepExecutionResult], Optional[str], Optional[str]]:
        """
        Execute a stored workflow.

        Returns:
            Tuple of (execution_id, status, step_results, final_output, error)
        """
        start_time = datetime.utcnow()

        # Load workflow
        workflow_data = await self.workflow_repo.get(workflow_id)
        if not workflow_data:
            return (
                f"execution-{uuid4().hex[:12]}",
                "failed",
                [],
                None,
                f"Workflow '{workflow_id}' not found",
            )

        # Parse workflow definition (clean None values first)
        try:
            cleaned_def = _clean_none_values(workflow_data.definition)
            workflow = validate_workflow_definition(cleaned_def)
        except ValueError as e:
            return (
                f"execution-{uuid4().hex[:12]}",
                "failed",
                [],
                None,
                f"Invalid workflow definition: {e}",
            )

        # Initialize context
        self._context = context or {}
        self._context["user_input"] = user_input
        self._context["session_id"] = session_id
        self._step_results = {}

        # Create execution record
        temporal_wf_id = f"workflow-{workflow_id}-{uuid4().hex[:8]}"
        try:
            execution_id = await self.workflow_repo.create_execution(
                workflow_id=workflow_id,
                temporal_workflow_id=temporal_wf_id,
                input_data={
                    "user_input": user_input,
                    "context": context,
                    "session_id": session_id,
                },
                triggered_by="api",
            )
        except Exception as e:
            logger.warning("execution_record_creation_failed", error=str(e))
            execution_id = f"execution-{uuid4().hex[:12]}"  # Fallback ID

        # Execute workflow steps
        step_results: List[StepExecutionResult] = []
        final_output: Optional[str] = None
        error: Optional[str] = None
        status = "completed"

        # Determine entry step
        entry_step_id = workflow.entry_step or workflow.steps[0].id
        current_step = workflow.get_step_by_id(entry_step_id)

        # Track executed steps to avoid infinite loops
        executed_step_ids: List[str] = []
        max_total_steps = len(workflow.steps) * 5  # Allow some re-execution for loops

        while current_step and len(executed_step_ids) < max_total_steps:
            step_start = datetime.utcnow()
            executed_step_ids.append(current_step.id)

            try:
                result = await self._execute_step(
                    current_step, workflow, user_input, session_id
                )
                step_end = datetime.utcnow()
                duration_ms = int((step_end - step_start).total_seconds() * 1000)

                step_result = StepExecutionResult(
                    step_id=current_step.id,
                    status="completed" if result.get("success") else "failed",
                    output=result.get("output"),
                    error=result.get("error"),
                    duration_ms=duration_ms,
                )
                step_results.append(step_result)
                self._step_results[current_step.id] = result

                # Check for error handling
                if not result.get("success"):
                    if current_step.on_error == "fail":
                        status = "failed"
                        error = result.get("error", "Step failed")
                        break
                    elif current_step.on_error == "skip":
                        pass  # Continue to next step
                    else:
                        # on_error is a step ID to jump to
                        current_step = workflow.get_step_by_id(current_step.on_error)
                        continue

                # Determine next step
                next_step_id = result.get("next_step")
                if next_step_id:
                    current_step = workflow.get_step_by_id(next_step_id)
                else:
                    # Get next sequential step
                    current_step = self._get_next_step(workflow, current_step.id)

                # Store final output from last successful step
                if result.get("output"):
                    final_output = result.get("output")

            except Exception as e:
                logger.error(
                    "step_execution_error",
                    step_id=current_step.id,
                    error=str(e),
                    exc_info=True,
                )
                step_result = StepExecutionResult(
                    step_id=current_step.id,
                    status="failed",
                    error=str(e),
                )
                step_results.append(step_result)

                if current_step.on_error == "fail":
                    status = "failed"
                    error = str(e)
                    break
                elif current_step.on_error == "skip":
                    current_step = self._get_next_step(workflow, current_step.id)
                else:
                    current_step = workflow.get_step_by_id(current_step.on_error)

        # Calculate total duration
        end_time = datetime.utcnow()
        total_duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Update execution record
        try:
            await self.workflow_repo.update_execution(
                execution_id=execution_id,
                status=status.upper(),
                output_data={"final_output": final_output} if final_output else None,
                error=error,
                steps_executed=[r.step_id for r in step_results],
                step_results={
                    r.step_id: {"status": r.status, "output": r.output, "error": r.error}
                    for r in step_results
                },
            )
        except Exception as e:
            logger.warning("execution_record_update_failed", error=str(e))

        return execution_id, status, step_results, final_output, error

    async def _execute_step(
        self,
        step: WorkflowStep,
        workflow: WorkflowDefinition,
        user_input: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        if step.type == StepType.AGENT:
            return await self._execute_agent_step(step, user_input, session_id)
        elif step.type == StepType.PARALLEL:
            return await self._execute_parallel_step(step, user_input, session_id)
        elif step.type == StepType.CONDITIONAL:
            return await self._execute_conditional_step(step, workflow)
        elif step.type == StepType.LOOP:
            return await self._execute_loop_step(step, user_input, session_id)
        else:
            return {"success": False, "error": f"Unknown step type: {step.type}"}

    async def _execute_agent_step(
        self,
        step: WorkflowStep,
        user_input: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute an agent step."""
        # Resolve input template
        input_text = self._resolve_template(step.input or "${user_input}", user_input)

        # Get agent config
        agent_config = await self.agent_repo.get(step.agent_id)
        if not agent_config:
            return {
                "success": False,
                "error": f"Agent '{step.agent_id}' not found",
            }

        # Execute agent via Temporal
        if self.temporal_client:
            from datetime import timedelta

            from src.workflows.agent_workflow import AgentWorkflow, AgentWorkflowInput

            workflow_input = AgentWorkflowInput(
                agent_id=agent_config.id,
                agent_type=agent_config.agent_type.value,
                user_input=input_text,
                conversation_history=[],
                session_id=session_id,
                system_prompt=self._build_system_prompt(agent_config),
                safety_level=agent_config.safety.level.value,
                blocked_topics=agent_config.safety.blocked_topics,
            )

            # Add LLM config if present
            if agent_config.llm_config:
                workflow_input.llm_provider = agent_config.llm_config.provider
                workflow_input.llm_model = agent_config.llm_config.model
                workflow_input.llm_temperature = agent_config.llm_config.temperature
                workflow_input.llm_max_tokens = agent_config.llm_config.max_tokens

            # Add tool config if present
            workflow_input.enabled_tools = [
                t.tool_id for t in agent_config.tools if t.enabled
            ]

            try:
                workflow_id = f"step-{step.id}-{uuid4().hex[:8]}"
                result = await self.temporal_client.execute_workflow(
                    AgentWorkflow.run,
                    workflow_input,
                    id=workflow_id,
                    task_queue="agent-tasks",
                    execution_timeout=timedelta(seconds=step.timeout),
                )
                return {
                    "success": result.success,
                    "output": result.content,
                    "error": result.error,
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            # Direct execution without Temporal (for testing)
            from src.agents.factory import AgentFactory

            agent = AgentFactory.create(agent_config)
            try:
                response = await agent.run(input_text, [], session_id)
                return {
                    "success": True,
                    "output": response.content,
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def _execute_parallel_step(
        self,
        step: WorkflowStep,
        user_input: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute a parallel step with multiple branches."""
        if not step.branches:
            return {"success": False, "error": "Parallel step has no branches"}

        # Create tasks for all branches
        tasks = []
        for branch in step.branches:
            # Create a pseudo step for each branch
            branch_step = WorkflowStep(
                id=branch.id or f"branch-{uuid4().hex[:6]}",
                type=StepType.AGENT,
                agent_id=branch.agent_id,
                input=branch.input,
                timeout=branch.timeout,
            )
            tasks.append(
                self._execute_agent_step(branch_step, user_input, session_id)
            )

        # Execute all branches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results based on aggregation type
        successful_results = []
        errors = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(str(result))
            elif result.get("success"):
                successful_results.append(result.get("output", ""))
            else:
                errors.append(result.get("error", "Unknown error"))

        # Apply aggregation
        if step.aggregation.value == "all":
            output = "\n---\n".join(successful_results)
            success = len(errors) == 0
        elif step.aggregation.value == "first":
            output = successful_results[0] if successful_results else ""
            success = len(successful_results) > 0
        elif step.aggregation.value == "merge":
            output = " ".join(successful_results)
            success = len(successful_results) > 0
        elif step.aggregation.value == "best":
            # For now, just take the first successful result
            # In a real implementation, this could use LLM to pick best
            output = successful_results[0] if successful_results else ""
            success = len(successful_results) > 0
        else:
            output = "\n---\n".join(successful_results)
            success = len(errors) == 0

        return {
            "success": success,
            "output": output,
            "error": "; ".join(errors) if errors and not success else None,
        }

    async def _execute_conditional_step(
        self,
        step: WorkflowStep,
        workflow: WorkflowDefinition,
    ) -> Dict[str, Any]:
        """Execute a conditional step that routes to different branches."""
        if not step.condition_source or not step.conditional_branches:
            return {"success": False, "error": "Conditional step missing configuration"}

        # Resolve condition value
        condition_value = self._resolve_template(step.condition_source, "")

        # Find matching branch
        next_step_id = None
        for pattern, target_step in step.conditional_branches.items():
            if pattern.lower() in condition_value.lower():
                next_step_id = target_step
                break

        # Use default if no match
        if not next_step_id and step.default:
            next_step_id = step.default

        if next_step_id:
            return {
                "success": True,
                "output": f"Routing to {next_step_id}",
                "next_step": next_step_id,
            }
        else:
            return {
                "success": False,
                "error": f"No matching branch for condition: {condition_value}",
            }

    async def _execute_loop_step(
        self,
        step: WorkflowStep,
        user_input: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute a loop step that iterates until a condition is met."""
        if not step.steps:
            return {"success": False, "error": "Loop step has no inner steps"}

        outputs = []
        iteration = 0

        while iteration < step.max_iterations:
            iteration += 1

            # Execute all inner steps
            for inner_step in step.steps:
                inner_workflow_step = WorkflowStep(
                    id=inner_step.id,
                    type=StepType.AGENT,
                    agent_id=inner_step.agent_id,
                    input=inner_step.input,
                    timeout=inner_step.timeout,
                )
                result = await self._execute_agent_step(
                    inner_workflow_step, user_input, session_id
                )
                if not result.get("success"):
                    return result
                self._step_results[inner_step.id] = result
                outputs.append(result.get("output", ""))

            # Check exit condition
            if step.exit_condition:
                exit_value = self._resolve_template(step.exit_condition, "")
                if exit_value.lower() in ("true", "done", "complete", "exit"):
                    break

        return {
            "success": True,
            "output": outputs[-1] if outputs else "",
        }

    def _resolve_template(self, template: str, user_input: str) -> str:
        """Resolve template variables like ${user_input} and ${steps.X.output}."""
        result = template

        # Replace ${user_input}
        result = result.replace("${user_input}", user_input)

        # Replace ${context.X}
        for key, value in self._context.items():
            result = result.replace(f"${{context.{key}}}", str(value))

        # Replace ${steps.X.output}
        step_pattern = re.compile(r"\$\{steps\.([^.]+)\.output\}")
        for match in step_pattern.finditer(result):
            step_id = match.group(1)
            if step_id in self._step_results:
                step_output = self._step_results[step_id].get("output", "")
                result = result.replace(match.group(0), str(step_output))

        return result

    def _get_next_step(
        self, workflow: WorkflowDefinition, current_step_id: str
    ) -> Optional[WorkflowStep]:
        """Get the next sequential step in the workflow."""
        for i, step in enumerate(workflow.steps):
            if step.id == current_step_id and i + 1 < len(workflow.steps):
                return workflow.steps[i + 1]
        return None

    def _build_system_prompt(self, config) -> str:
        """Build system prompt from agent config."""
        from src.agents.factory import AgentFactory

        agent = AgentFactory.create(config)
        return agent.build_system_prompt()


async def validate_workflow_with_resources(
    definition_dict: Dict[str, Any],
    agent_repo: BaseAgentRepository,
) -> Tuple[bool, List[Dict[str, str]], List[Dict[str, str]], List[str]]:
    """
    Validate workflow definition and check resource availability.

    Returns:
        Tuple of (is_valid, errors, warnings, missing_agents)
    """
    errors = []
    warnings = []
    missing_agents = []

    # Clean None values to allow Pydantic defaults
    cleaned_dict = _clean_none_values(definition_dict)

    # Validate definition structure
    try:
        workflow = validate_workflow_definition(cleaned_dict)
    except ValueError as e:
        errors.append({"field": "definition", "message": str(e)})
        return False, errors, warnings, missing_agents

    # Collect all agent IDs referenced in the workflow
    agent_ids = set()
    for step in workflow.steps:
        if step.type == StepType.AGENT and step.agent_id:
            agent_ids.add(step.agent_id)
        elif step.type == StepType.PARALLEL and step.branches:
            for branch in step.branches:
                agent_ids.add(branch.agent_id)
        elif step.type == StepType.LOOP and step.steps:
            for inner_step in step.steps:
                agent_ids.add(inner_step.agent_id)

    # Check if all referenced agents exist
    for agent_id in agent_ids:
        agent = await agent_repo.get(agent_id)
        if not agent:
            missing_agents.append(agent_id)
            errors.append({
                "field": f"steps.*.agent_id",
                "message": f"Agent '{agent_id}' not found",
            })

    is_valid = len(errors) == 0
    return is_valid, errors, warnings, missing_agents
