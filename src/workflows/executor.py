"""Workflow executor - runs multi-step workflows."""
import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from src.api.schemas.workflows import StepExecutionResult
from src.config.logging import get_logger
from src.models.workflow_definition import (
    LoopMode,
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
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, str, List[StepExecutionResult], Optional[str], Optional[str]]:
        """
        Execute a stored workflow.

        Returns:
            Tuple of (execution_id, status, step_results, final_output, error)
        """
        start_time = datetime.now(timezone.utc)

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

        # Create Temporal workflow ID
        temporal_wf_id = f"workflow-{workflow_id}-{uuid4().hex[:8]}"

        # Initialize context
        self._context = context or {}
        self._context["user_input"] = user_input
        self._context["user_id"] = user_id
        self._context["session_id"] = session_id
        self._context["conversation_history"] = conversation_history or []
        self._context["workflow_id"] = workflow_id
        self._context["temporal_workflow_id"] = temporal_wf_id
        self._step_results = {}

        # Create execution record
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

        # Add execution_id to context for approval steps
        self._context["execution_id"] = execution_id

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
            step_start = datetime.now(timezone.utc)
            executed_step_ids.append(current_step.id)

            try:
                result = await self._execute_step(
                    current_step, workflow, user_input, user_id, session_id
                )
                step_end = datetime.now(timezone.utc)
                duration_ms = int((step_end - step_start).total_seconds() * 1000)

                # Determine step status
                step_status = "completed" if result.get("success") else "failed"
                if result.get("status") == "waiting_for_approval":
                    step_status = "waiting_for_approval"

                step_result = StepExecutionResult(
                    step_id=current_step.id,
                    status=step_status,
                    output=result.get("output"),
                    error=result.get("error"),
                    duration_ms=duration_ms,
                )
                step_results.append(step_result)
                self._step_results[current_step.id] = result

                # Handle waiting for approval - pause workflow
                if result.get("status") == "waiting_for_approval":
                    status = "waiting_for_approval"
                    final_output = result.get("output")
                    logger.info(
                        "workflow_waiting_for_approval",
                        step_id=current_step.id,
                        approval_id=result.get("approval_id"),
                    )
                    break

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
        end_time = datetime.now(timezone.utc)
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
        user_id: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        if step.type == StepType.AGENT:
            return await self._execute_agent_step(step, user_input, user_id, session_id)
        elif step.type == StepType.PARALLEL:
            return await self._execute_parallel_step(step, user_input, user_id, session_id)
        elif step.type == StepType.CONDITIONAL:
            return await self._execute_conditional_step(step, workflow)
        elif step.type == StepType.LOOP:
            return await self._execute_loop_step(step, user_input, user_id, session_id)
        elif step.type == StepType.APPROVAL:
            return await self._execute_approval_step(step, user_input, user_id)
        else:
            return {"success": False, "error": f"Unknown step type: {step.type}"}

    async def _execute_agent_step(
        self,
        step: WorkflowStep,
        user_input: str,
        user_id: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute an agent step."""
        # Check if agent_id is set (not a draft step with only suggested_agent)
        if not step.agent_id:
            step_name = step.name or step.id
            if step.suggested_agent:
                return {
                    "success": False,
                    "error": f"Step '{step_name}' has a suggested agent but no actual agent assigned. "
                    f"Please create the agent first or assign an existing agent.",
                }
            return {
                "success": False,
                "error": f"Step '{step_name}' has no agent_id configured.",
            }

        # Resolve input template
        input_text = self._resolve_template(step.input or "${user_input}", user_input)

        # Get agent config
        agent_config = await self.agent_repo.get(step.agent_id)
        if not agent_config:
            return {
                "success": False,
                "error": f"Agent '{step.agent_id}' not found. It may have been deleted.",
            }

        # Execute agent via Temporal
        if self.temporal_client:
            from datetime import timedelta

            from src.workflows.agent_workflow import AgentWorkflow, AgentWorkflowInput

            workflow_input = AgentWorkflowInput(
                agent_id=agent_config.id,
                agent_type=agent_config.agent_type.value,
                user_input=input_text,
                user_id=user_id,
                conversation_history=self._context.get("conversation_history", []),
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
        user_id: str,
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
                self._execute_agent_step(branch_step, user_input, user_id, session_id)
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
        user_id: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute a loop step with support for count, foreach, and until modes.

        Loop context variables available during execution:
        - ${loop.index}: Current iteration (1-based)
        - ${loop.item}: Current item (foreach mode only)
        - ${loop.previous}: Output from previous iteration
        - ${loop.total}: Total iterations (foreach mode) or max_iterations (count mode)
        - ${loop.first}: True if first iteration
        - ${loop.last}: True if last iteration (foreach mode only)
        """
        if not step.steps:
            return {"success": False, "error": "Loop step has no inner steps"}

        outputs: List[str] = []
        iteration_results: List[Dict[str, Any]] = []
        loop_mode = step.loop_mode or LoopMode.COUNT

        # Parse items for foreach mode
        items: List[Any] = []
        if loop_mode == LoopMode.FOREACH and step.over:
            items = self._parse_loop_items(step.over, user_input)
            if not items:
                logger.warning("loop_empty_collection", step_id=step.id, over=step.over)
                return {
                    "success": True,
                    "output": "",
                    "loop_results": [],
                }

        # Determine max iterations
        max_iters = len(items) if loop_mode == LoopMode.FOREACH else step.max_iterations
        total = len(items) if loop_mode == LoopMode.FOREACH else step.max_iterations
        iteration = 0

        while iteration < max_iters:
            iteration += 1

            # Set up loop context
            current_item = items[iteration - 1] if items else None
            loop_context = {
                "index": iteration,
                "item": current_item,
                "previous": outputs[-1] if outputs else "",
                "total": total,
                "first": iteration == 1,
                "last": iteration == max_iters if loop_mode == LoopMode.FOREACH else False,
            }
            self._context["loop"] = loop_context

            # Check continue condition (skip this iteration)
            if step.continue_condition:
                continue_value = self._resolve_template(step.continue_condition, user_input)
                if continue_value.lower() in ("true", "skip", "continue", "1"):
                    logger.debug("loop_continue", step_id=step.id, iteration=iteration)
                    continue

            # Execute all inner steps for this iteration
            iteration_output = ""
            for inner_step in step.steps:
                inner_workflow_step = WorkflowStep(
                    id=f"{inner_step.id}-iter{iteration}",
                    type=StepType.AGENT,
                    agent_id=inner_step.agent_id,
                    input=inner_step.input,
                    timeout=inner_step.timeout,
                )
                result = await self._execute_agent_step(
                    inner_workflow_step, user_input, user_id, session_id
                )
                if not result.get("success"):
                    # Store partial results before failure
                    if step.collect_results:
                        return {
                            "success": False,
                            "error": result.get("error"),
                            "loop_results": iteration_results,
                            "failed_iteration": iteration,
                        }
                    return result

                # Store step result
                self._step_results[inner_step.id] = result
                iteration_output = result.get("output", "")

            outputs.append(iteration_output)
            iteration_results.append({
                "iteration": iteration,
                "item": current_item,
                "output": iteration_output,
            })

            # Check break condition (exit loop early)
            if step.break_condition:
                break_value = self._resolve_template(step.break_condition, user_input)
                if break_value.lower() in ("true", "break", "stop", "1"):
                    logger.debug("loop_break", step_id=step.id, iteration=iteration)
                    break

            # Check exit condition (for until mode and backwards compatibility)
            if step.exit_condition:
                exit_value = self._resolve_template(step.exit_condition, user_input)
                if exit_value.lower() in ("true", "done", "complete", "exit", "1"):
                    logger.debug("loop_exit_condition", step_id=step.id, iteration=iteration)
                    break

        # Clear loop context
        self._context.pop("loop", None)

        # Build final output
        if step.collect_results:
            # Return structured results
            return {
                "success": True,
                "output": outputs[-1] if outputs else "",
                "loop_results": iteration_results,
                "iterations_completed": iteration,
            }
        else:
            # Return just the last output
            return {
                "success": True,
                "output": outputs[-1] if outputs else "",
            }

    async def _execute_approval_step(
        self,
        step: WorkflowStep,
        user_input: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Execute an approval step that waits for human approval.

        This step creates an approval request and waits for a human to approve/reject.

        In Temporal mode:
        - Creates an approval record in the database
        - Uses Temporal signals to wait for the approval response
        - Resumes workflow when approved or handles rejection

        In direct execution mode (testing):
        - Returns a "waiting_for_approval" status
        - Caller must poll for approval status
        """
        # Validate approval configuration
        if not step.approvers:
            return {
                "success": False,
                "error": "Approval step has no approvers configured",
            }

        # Resolve approval message template
        message = self._resolve_template(
            step.approval_message or "Please approve this workflow step.",
            user_input
        )

        # Build context for the approval
        approval_context = {
            "user_input": user_input,
            "triggered_by": user_id,
            "previous_steps": {
                step_id: result.get("output", "")
                for step_id, result in self._step_results.items()
            },
        }

        # Get execution context
        execution_id = self._context.get("execution_id", "")
        workflow_id = self._context.get("workflow_id", "")
        temporal_workflow_id = self._context.get("temporal_workflow_id", "")

        if self.temporal_client:
            # Temporal mode: Create approval and wait for signal
            try:
                from datetime import timedelta
                from src.storage.approval_repository import ApprovalRepository
                from src.storage.database import get_async_session

                # Calculate timeout
                timeout_at = None
                if step.approval_timeout_seconds:
                    from datetime import datetime, timezone
                    timeout_at = datetime.now(timezone.utc) + timedelta(
                        seconds=step.approval_timeout_seconds
                    )

                # Create approval record
                async with get_async_session() as session:
                    approval_repo = ApprovalRepository(session, user_id=user_id)
                    approval = await approval_repo.create(
                        workflow_id=workflow_id,
                        execution_id=execution_id,
                        step_id=step.id,
                        temporal_workflow_id=temporal_workflow_id,
                        title=step.name or f"Approval required: {step.id}",
                        message=message,
                        approvers=step.approvers,
                        required_approvals=step.required_approvals,
                        context=approval_context,
                        timeout_at=timeout_at,
                        created_by=user_id,
                    )
                    await session.commit()

                logger.info(
                    "approval_request_created",
                    approval_id=approval.id,
                    step_id=step.id,
                    approvers=step.approvers,
                )

                # Return waiting status - workflow will be resumed via signal
                return {
                    "success": True,
                    "output": f"Waiting for approval: {approval.id}",
                    "status": "waiting_for_approval",
                    "approval_id": approval.id,
                    "approvers": step.approvers,
                    "required_approvals": step.required_approvals,
                }

            except Exception as e:
                logger.error("approval_creation_failed", step_id=step.id, error=str(e))
                return {
                    "success": False,
                    "error": f"Failed to create approval request: {e}",
                }

        else:
            # Direct execution mode (testing): Auto-approve or simulate
            logger.warning(
                "approval_step_auto_approved",
                step_id=step.id,
                reason="No Temporal client available - auto-approving for testing",
            )
            return {
                "success": True,
                "output": "Approval auto-granted (testing mode)",
                "status": "auto_approved",
            }

    def _parse_loop_items(self, over_expression: str, user_input: str) -> List[Any]:
        """Parse the 'over' expression to get items for foreach loop.

        Supports:
        - JSON array literal: ["a", "b", "c"]
        - Template variable: ${steps.X.output}
        - Comma-separated string: "a, b, c"
        """
        import json

        resolved = self._resolve_template(over_expression, user_input)

        # Try parsing as JSON array
        try:
            parsed = json.loads(resolved)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                # If dict, iterate over values or key-value pairs
                return list(parsed.items())
        except (json.JSONDecodeError, TypeError):
            pass

        # Try splitting as comma-separated string
        if "," in resolved:
            return [item.strip() for item in resolved.split(",") if item.strip()]

        # Try splitting by newlines
        if "\n" in resolved:
            return [item.strip() for item in resolved.split("\n") if item.strip()]

        # Single item
        if resolved.strip():
            return [resolved.strip()]

        return []

    def _resolve_template(self, template: str, user_input: str) -> str:
        """Resolve template variables.

        Supported variables:
        - ${user_input}: The original user input
        - ${previous}: Output from the most recently executed step
        - ${context.X}: Context variables
        - ${steps.X.output}: Output from a specific step
        - ${loop.index}: Current loop iteration (1-based)
        - ${loop.item}: Current item in foreach loop
        - ${loop.previous}: Output from previous iteration
        - ${loop.total}: Total iterations
        - ${loop.first}: True if first iteration
        - ${loop.last}: True if last iteration
        """
        result = template

        # Replace ${user_input}
        result = result.replace("${user_input}", user_input)

        # Replace ${previous} - output from the most recently executed step
        if "${previous}" in result and self._step_results:
            # Get the last executed step's output
            last_step_id = list(self._step_results.keys())[-1]
            previous_output = self._step_results[last_step_id].get("output", "")
            result = result.replace("${previous}", str(previous_output) if previous_output else "")

        # Replace ${loop.X} - loop context variables
        loop_context = self._context.get("loop", {})
        if loop_context:
            loop_pattern = re.compile(r"\$\{loop\.([^}]+)\}")
            for match in loop_pattern.finditer(result):
                var_name = match.group(1)
                if var_name in loop_context:
                    value = loop_context[var_name]
                    # Handle special serialization for complex items
                    if isinstance(value, (dict, list, tuple)):
                        import json
                        str_value = json.dumps(value)
                    elif isinstance(value, bool):
                        str_value = "true" if value else "false"
                    else:
                        str_value = str(value) if value is not None else ""
                    result = result.replace(match.group(0), str_value)

        # Replace ${context.X} - skip loop context as it's handled above
        for key, value in self._context.items():
            if key != "loop":  # Skip loop context
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
        elif step.type == StepType.APPROVAL:
            # Validate approval step configuration
            if not step.approvers:
                errors.append({
                    "field": f"steps.{step.id}.approvers",
                    "message": f"Approval step '{step.id}' has no approvers configured",
                })
            if not step.approval_message:
                warnings.append({
                    "field": f"steps.{step.id}.approval_message",
                    "message": f"Approval step '{step.id}' has no custom message (will use default)",
                })

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
