"""Tests for workflow definition models and validation."""

import pytest
from pydantic import ValidationError

from src.models.workflow_definition import (
    StepType,
    ErrorHandling,
    AggregationType,
    ParallelBranch,
    LoopInnerStep,
    WorkflowStep,
    WorkflowDefinition,
    SuggestedAgent,
    validate_workflow_definition,
)


class TestStepType:
    """Tests for StepType enum."""

    def test_agent_value(self):
        """Test AGENT value."""
        assert StepType.AGENT.value == "agent"

    def test_parallel_value(self):
        """Test PARALLEL value."""
        assert StepType.PARALLEL.value == "parallel"

    def test_conditional_value(self):
        """Test CONDITIONAL value."""
        assert StepType.CONDITIONAL.value == "conditional"

    def test_loop_value(self):
        """Test LOOP value."""
        assert StepType.LOOP.value == "loop"


class TestWorkflowStep:
    """Tests for WorkflowStep model."""

    def test_create_agent_step(self):
        """Test creating a basic agent step."""
        step = WorkflowStep(
            id="step-1",
            type=StepType.AGENT,
            agent_id="agent-1",
        )

        assert step.id == "step-1"
        assert step.type == StepType.AGENT
        assert step.agent_id == "agent-1"
        assert step.timeout == 120  # default
        assert step.retries == 0  # default

    def test_agent_step_with_suggested_agent(self):
        """Test agent step with suggested_agent instead of agent_id."""
        step = WorkflowStep(
            id="step-1",
            type=StepType.AGENT,
            suggested_agent=SuggestedAgent(
                name="Data Analyst",
                goal="Analyze the data",
            ),
        )

        assert step.suggested_agent is not None
        assert step.suggested_agent.name == "Data Analyst"
        assert step.agent_id is None

    def test_agent_step_requires_agent(self):
        """Test that agent step requires agent_id or suggested_agent."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowStep(
                id="step-1",
                type=StepType.AGENT,
            )
        assert "agent step requires agent_id or suggested_agent" in str(exc_info.value)

    def test_create_parallel_step(self):
        """Test creating a parallel step."""
        step = WorkflowStep(
            id="parallel-1",
            type=StepType.PARALLEL,
            branches=[
                ParallelBranch(agent_id="agent-1"),
                ParallelBranch(agent_id="agent-2"),
            ],
        )

        assert step.type == StepType.PARALLEL
        assert len(step.branches) == 2
        assert step.aggregation == AggregationType.ALL

    def test_parallel_step_requires_branches(self):
        """Test that parallel step requires branches."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowStep(
                id="parallel-1",
                type=StepType.PARALLEL,
            )
        assert "parallel step requires branches" in str(exc_info.value)

    def test_parallel_step_max_branches(self):
        """Test that parallel step has max 10 branches."""
        branches = [ParallelBranch(agent_id=f"agent-{i}") for i in range(11)]

        with pytest.raises(ValidationError) as exc_info:
            WorkflowStep(
                id="parallel-1",
                type=StepType.PARALLEL,
                branches=branches,
            )
        # Pydantic validates with max_length=10
        assert "too_long" in str(exc_info.value) or "10 items" in str(exc_info.value)

    def test_create_conditional_step(self):
        """Test creating a conditional step."""
        step = WorkflowStep(
            id="cond-1",
            type=StepType.CONDITIONAL,
            condition_source="user_type",
            conditional_branches={
                "premium": "premium-step",
                "basic": "basic-step",
            },
            default="default-step",
        )

        assert step.type == StepType.CONDITIONAL
        assert step.condition_source == "user_type"
        assert step.conditional_branches["premium"] == "premium-step"

    def test_conditional_step_requires_source(self):
        """Test that conditional step requires condition_source."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowStep(
                id="cond-1",
                type=StepType.CONDITIONAL,
                conditional_branches={"a": "b"},
            )
        assert "conditional step requires condition_source" in str(exc_info.value)

    def test_conditional_step_requires_branches(self):
        """Test that conditional step requires conditional_branches."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowStep(
                id="cond-1",
                type=StepType.CONDITIONAL,
                condition_source="test",
            )
        assert "conditional step requires conditional_branches" in str(exc_info.value)

    def test_create_loop_step(self):
        """Test creating a loop step."""
        step = WorkflowStep(
            id="loop-1",
            type=StepType.LOOP,
            max_iterations=3,
            exit_condition="task_complete == true",
            steps=[
                LoopInnerStep(id="inner-1", agent_id="agent-1"),
            ],
        )

        assert step.type == StepType.LOOP
        assert step.max_iterations == 3
        assert len(step.steps) == 1

    def test_loop_step_requires_inner_steps(self):
        """Test that loop step requires inner steps."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowStep(
                id="loop-1",
                type=StepType.LOOP,
            )
        assert "loop step requires inner steps" in str(exc_info.value)

    def test_on_error_validation(self):
        """Test on_error field validation."""
        # Valid values
        step1 = WorkflowStep(id="s1", type=StepType.AGENT, agent_id="a1", on_error="fail")
        assert step1.on_error == "fail"

        step2 = WorkflowStep(id="s2", type=StepType.AGENT, agent_id="a1", on_error="skip")
        assert step2.on_error == "skip"

        # Step ID reference (validated at workflow level)
        step3 = WorkflowStep(id="s3", type=StepType.AGENT, agent_id="a1", on_error="error-step")
        assert step3.on_error == "error-step"

    def test_invalid_step_id(self):
        """Test that invalid step IDs are rejected."""
        with pytest.raises(ValidationError):
            WorkflowStep(
                id="123-invalid",  # Must start with letter
                type=StepType.AGENT,
                agent_id="agent-1",
            )


class TestWorkflowDefinition:
    """Tests for WorkflowDefinition model."""

    def test_create_simple_workflow(self):
        """Test creating a simple workflow."""
        workflow = WorkflowDefinition(
            id="workflow-1",
            name="Test Workflow",
            steps=[
                WorkflowStep(id="step-1", type=StepType.AGENT, agent_id="agent-1"),
            ],
        )

        assert workflow.id == "workflow-1"
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 1

    def test_workflow_requires_steps(self):
        """Test that workflow requires at least one step."""
        with pytest.raises(ValidationError):
            WorkflowDefinition(
                id="workflow-1",
                steps=[],
            )

    def test_workflow_validates_entry_step(self):
        """Test that entry_step must exist in steps."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(
                id="workflow-1",
                entry_step="nonexistent",
                steps=[
                    WorkflowStep(id="step-1", type=StepType.AGENT, agent_id="agent-1"),
                ],
            )
        assert "entry_step" in str(exc_info.value)

    def test_workflow_detects_duplicate_ids(self):
        """Test that duplicate step IDs are detected."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(
                id="workflow-1",
                steps=[
                    WorkflowStep(id="step-1", type=StepType.AGENT, agent_id="agent-1"),
                    WorkflowStep(id="step-1", type=StepType.AGENT, agent_id="agent-2"),
                ],
            )
        assert "Duplicate step IDs" in str(exc_info.value)

    def test_workflow_validates_on_error_references(self):
        """Test that on_error step references are validated."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(
                id="workflow-1",
                steps=[
                    WorkflowStep(
                        id="step-1",
                        type=StepType.AGENT,
                        agent_id="agent-1",
                        on_error="nonexistent-step",
                    ),
                ],
            )
        assert "on_error references unknown step" in str(exc_info.value)

    def test_workflow_validates_conditional_targets(self):
        """Test that conditional branch targets are validated."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDefinition(
                id="workflow-1",
                steps=[
                    WorkflowStep(
                        id="cond-1",
                        type=StepType.CONDITIONAL,
                        condition_source="test",
                        conditional_branches={"a": "nonexistent"},
                    ),
                ],
            )
        assert "branch targets unknown step" in str(exc_info.value)

    def test_get_step_by_id(self):
        """Test get_step_by_id method."""
        workflow = WorkflowDefinition(
            id="workflow-1",
            steps=[
                WorkflowStep(id="step-1", type=StepType.AGENT, agent_id="agent-1"),
                WorkflowStep(id="step-2", type=StepType.AGENT, agent_id="agent-2"),
            ],
        )

        step = workflow.get_step_by_id("step-1")
        assert step is not None
        assert step.id == "step-1"

        missing = workflow.get_step_by_id("nonexistent")
        assert missing is None

    def test_is_ready_to_run_with_agent_ids(self):
        """Test is_ready_to_run when all steps have agent_ids."""
        workflow = WorkflowDefinition(
            id="workflow-1",
            steps=[
                WorkflowStep(id="step-1", type=StepType.AGENT, agent_id="agent-1"),
                WorkflowStep(id="step-2", type=StepType.AGENT, agent_id="agent-2"),
            ],
        )

        assert workflow.is_ready_to_run() is True

    def test_is_ready_to_run_with_suggested_agents(self):
        """Test is_ready_to_run when steps have suggested_agents only."""
        workflow = WorkflowDefinition(
            id="workflow-1",
            steps=[
                WorkflowStep(
                    id="step-1",
                    type=StepType.AGENT,
                    suggested_agent=SuggestedAgent(name="Test", goal="Test goal"),
                ),
            ],
        )

        assert workflow.is_ready_to_run() is False

    def test_get_draft_steps(self):
        """Test get_draft_steps method."""
        workflow = WorkflowDefinition(
            id="workflow-1",
            steps=[
                WorkflowStep(id="ready", type=StepType.AGENT, agent_id="agent-1"),
                WorkflowStep(
                    id="draft",
                    type=StepType.AGENT,
                    suggested_agent=SuggestedAgent(name="Draft", goal="Draft goal"),
                ),
            ],
        )

        draft_steps = workflow.get_draft_steps()
        assert len(draft_steps) == 1
        assert draft_steps[0].id == "draft"

    def test_get_missing_agent_ids(self):
        """Test get_missing_agent_ids method."""
        workflow = WorkflowDefinition(
            id="workflow-1",
            steps=[
                WorkflowStep(id="ready", type=StepType.AGENT, agent_id="agent-1"),
                WorkflowStep(
                    id="draft-1",
                    type=StepType.AGENT,
                    suggested_agent=SuggestedAgent(name="D1", goal="G1"),
                ),
                WorkflowStep(
                    id="draft-2",
                    type=StepType.AGENT,
                    suggested_agent=SuggestedAgent(name="D2", goal="G2"),
                ),
            ],
        )

        missing = workflow.get_missing_agent_ids()
        assert len(missing) == 2
        assert "draft-1" in missing
        assert "draft-2" in missing


class TestValidateWorkflowDefinition:
    """Tests for validate_workflow_definition function."""

    def test_validate_valid_definition(self):
        """Test validating a valid workflow definition dict."""
        data = {
            "id": "workflow-1",
            "name": "Test",
            "steps": [
                {"id": "step-1", "type": "agent", "agent_id": "agent-1"},
            ],
        }

        result = validate_workflow_definition(data)
        assert isinstance(result, WorkflowDefinition)
        assert result.id == "workflow-1"

    def test_validate_maps_conditional_branches(self):
        """Test that 'branches' is mapped to 'conditional_branches' for conditional steps."""
        data = {
            "id": "workflow-1",
            "steps": [
                {
                    "id": "cond-1",
                    "type": "conditional",
                    "condition_source": "test",
                    "branches": {"a": "step-2"},  # Should be mapped
                    "default": "step-2",
                },
                {"id": "step-2", "type": "agent", "agent_id": "agent-1"},
            ],
        }

        result = validate_workflow_definition(data)
        assert result.steps[0].conditional_branches == {"a": "step-2"}

    def test_validate_invalid_definition(self):
        """Test validating an invalid definition raises error."""
        data = {
            "id": "123-invalid",  # Invalid ID format
            "steps": [],
        }

        with pytest.raises(ValidationError):
            validate_workflow_definition(data)
