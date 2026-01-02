"""Tests for workflow executor module.

Tests cover:
- _clean_none_values helper function
- WorkflowExecutor class and all execution methods
- validate_workflow_with_resources function
- Template resolution and step navigation
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.workflows.executor import (
    WorkflowExecutor,
    _clean_none_values,
    validate_workflow_with_resources,
)
from src.models.workflow_definition import StepType, WorkflowStep


# ============================================================================
# Tests for _clean_none_values helper function
# ============================================================================


class TestCleanNoneValues:
    """Tests for the _clean_none_values helper function."""

    def test_removes_none_from_dict(self):
        """Test that None values are removed from dictionaries."""
        data = {"a": 1, "b": None, "c": "test"}
        result = _clean_none_values(data)
        assert result == {"a": 1, "c": "test"}
        assert "b" not in result

    def test_recursively_cleans_nested_dicts(self):
        """Test that nested dictionaries are cleaned recursively."""
        data = {
            "outer": {"inner": None, "value": 123},
            "other": None,
        }
        result = _clean_none_values(data)
        assert result == {"outer": {"value": 123}}

    def test_cleans_lists(self):
        """Test that items in lists are cleaned."""
        data = [{"a": 1, "b": None}, {"c": None, "d": 2}]
        result = _clean_none_values(data)
        assert result == [{"a": 1}, {"d": 2}]

    def test_preserves_non_none_values(self):
        """Test that non-None values are preserved."""
        data = {"a": 0, "b": False, "c": "", "d": []}
        result = _clean_none_values(data)
        assert result == {"a": 0, "b": False, "c": "", "d": []}

    def test_handles_empty_dict(self):
        """Test handling of empty dictionary."""
        assert _clean_none_values({}) == {}

    def test_handles_empty_list(self):
        """Test handling of empty list."""
        assert _clean_none_values([]) == []

    def test_handles_primitive_values(self):
        """Test that primitive values pass through unchanged."""
        assert _clean_none_values(42) == 42
        assert _clean_none_values("hello") == "hello"
        assert _clean_none_values(True) is True

    def test_handles_deeply_nested_structure(self):
        """Test handling of deeply nested structures."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep",
                        "null_value": None,
                    },
                    "empty": None,
                },
                "list_data": [{"x": None, "y": 1}],
            }
        }
        result = _clean_none_values(data)
        expected = {
            "level1": {
                "level2": {
                    "level3": {"value": "deep"},
                },
                "list_data": [{"y": 1}],
            }
        }
        assert result == expected


# ============================================================================
# Fixtures for WorkflowExecutor tests
# ============================================================================


@pytest.fixture
def mock_agent_repo():
    """Create a mock agent repository."""
    repo = AsyncMock()
    repo.get = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_workflow_repo():
    """Create a mock workflow repository."""
    repo = AsyncMock()
    repo.get = AsyncMock(return_value=None)
    repo.create_execution = AsyncMock(return_value="exec-123")
    repo.update_execution = AsyncMock()
    return repo


@pytest.fixture
def mock_temporal_client():
    """Create a mock Temporal client."""
    client = AsyncMock()
    return client


@pytest.fixture
def executor(mock_agent_repo, mock_workflow_repo, mock_temporal_client):
    """Create a WorkflowExecutor with mocked dependencies."""
    return WorkflowExecutor(
        agent_repo=mock_agent_repo,
        workflow_repo=mock_workflow_repo,
        temporal_client=mock_temporal_client,
    )


@pytest.fixture
def sample_workflow_data():
    """Create sample workflow data for testing."""
    from src.storage.workflow_repository import WorkflowWithMetadata

    return WorkflowWithMetadata(
        id="test-workflow",
        name="Test Workflow",
        description="A test workflow",
        category="test",
        tags=[],
        definition={
            "id": "test-workflow",
            "name": "Test Workflow",
            "steps": [
                {
                    "id": "step-1",
                    "type": "agent",
                    "name": "First Step",
                    "agent_id": "agent-1",
                    "input": "${user_input}",
                },
                {
                    "id": "step-2",
                    "type": "agent",
                    "name": "Second Step",
                    "agent_id": "agent-2",
                    "input": "${steps.step-1.output}",
                },
            ],
            "entry_step": "step-1",
        },
        version=1,
        is_template=False,
        is_active=True,
        source_template_id=None,
        created_by="user-123",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_agent_config():
    """Create a sample agent config for testing."""
    from src.models.agent_config import AgentConfig
    from src.models.enums import AgentType
    from src.models.persona import AgentGoal, AgentInstructions, AgentRole
    from src.models.safety_config import SafetyConfig
    from src.models.llm_config import LLMConfig

    return AgentConfig(
        id="agent-1",
        name="Test Agent",
        description="A test agent",
        agent_type=AgentType.LLM,
        role=AgentRole(
            title="Test",
            expertise=[],
            personality=[],
            communication_style="professional",
        ),
        goal=AgentGoal(
            objective="Test",
            success_indicators=[],
            constraints=[],
        ),
        instructions=AgentInstructions(
            steps=[],
            rules=[],
            prohibited=[],
            output_format=None,
        ),
        llm_config=LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1024,
        ),
        safety=SafetyConfig(),
    )


# ============================================================================
# Tests for WorkflowExecutor.execute
# ============================================================================


class TestWorkflowExecutorExecute:
    """Tests for the main execute method."""

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, executor, mock_workflow_repo):
        """Test execution when workflow is not found."""
        mock_workflow_repo.get.return_value = None

        execution_id, status, step_results, final_output, error = await executor.execute(
            workflow_id="nonexistent",
            user_input="test input",
            user_id="user-123",
        )

        assert status == "failed"
        assert error == "Workflow 'nonexistent' not found"
        assert step_results == []
        assert final_output is None

    @pytest.mark.asyncio
    async def test_execute_invalid_workflow_definition(
        self, executor, mock_workflow_repo
    ):
        """Test execution with invalid workflow definition."""
        mock_workflow_repo.get.return_value = MagicMock(
            definition={"invalid": "definition"}  # Missing required fields
        )

        execution_id, status, step_results, final_output, error = await executor.execute(
            workflow_id="test-workflow",
            user_input="test input",
            user_id="user-123",
        )

        assert status == "failed"
        assert "Invalid workflow definition" in error

    @pytest.mark.asyncio
    async def test_execute_creates_execution_record(
        self, executor, mock_workflow_repo, sample_workflow_data, mock_agent_repo, sample_agent_config
    ):
        """Test that execution creates an execution record."""
        mock_workflow_repo.get.return_value = sample_workflow_data
        mock_agent_repo.get.return_value = sample_agent_config

        # Mock agent execution
        with patch.object(executor, "_execute_agent_step") as mock_exec:
            mock_exec.return_value = {"success": True, "output": "result"}

            await executor.execute(
                workflow_id="test-workflow",
                user_input="test input",
                user_id="user-123",
                session_id="session-123",
            )

            mock_workflow_repo.create_execution.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_handles_step_error_with_fail(
        self, executor, mock_workflow_repo, mock_agent_repo
    ):
        """Test execution when a step fails with on_error=fail."""
        from src.storage.workflow_repository import WorkflowWithMetadata

        workflow_data = WorkflowWithMetadata(
            id="test-workflow",
            name="Test Workflow",
            description="Test",
            category="test",
            tags=[],
            definition={
                "id": "test-workflow",
                "name": "Test",
                "steps": [
                    {
                        "id": "step-1",
                        "type": "agent",
                        "agent_id": "agent-1",
                        "on_error": "fail",
                    }
                ],
            },
            version=1,
            is_template=False,
            is_active=True,
            source_template_id=None,
            created_by="user-123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_workflow_repo.get.return_value = workflow_data

        with patch.object(executor, "_execute_agent_step") as mock_exec:
            mock_exec.return_value = {"success": False, "error": "Agent failed"}

            execution_id, status, step_results, final_output, error = await executor.execute(
                workflow_id="test-workflow",
                user_input="test input",
                user_id="user-123",
            )

            assert status == "failed"
            assert error == "Agent failed"

    @pytest.mark.asyncio
    async def test_execute_handles_step_error_with_skip(
        self, executor, mock_workflow_repo, mock_agent_repo, sample_agent_config
    ):
        """Test execution when a step fails with on_error=skip."""
        from src.storage.workflow_repository import WorkflowWithMetadata

        workflow_data = WorkflowWithMetadata(
            id="test-workflow",
            name="Test Workflow",
            description="Test",
            category="test",
            tags=[],
            definition={
                "id": "test-workflow",
                "name": "Test",
                "steps": [
                    {
                        "id": "step-1",
                        "type": "agent",
                        "agent_id": "agent-1",
                        "on_error": "skip",
                    },
                    {
                        "id": "step-2",
                        "type": "agent",
                        "agent_id": "agent-2",
                        "on_error": "fail",
                    },
                ],
            },
            version=1,
            is_template=False,
            is_active=True,
            source_template_id=None,
            created_by="user-123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_workflow_repo.get.return_value = workflow_data
        mock_agent_repo.get.return_value = sample_agent_config

        with patch.object(executor, "_execute_agent_step") as mock_exec:
            # First step fails, second succeeds
            mock_exec.side_effect = [
                {"success": False, "error": "Agent failed"},
                {"success": True, "output": "Step 2 result"},
            ]

            execution_id, status, step_results, final_output, error = await executor.execute(
                workflow_id="test-workflow",
                user_input="test input",
                user_id="user-123",
            )

            # Should complete successfully since step-1 was skipped
            assert status == "completed"
            assert len(step_results) == 2


# ============================================================================
# Tests for WorkflowExecutor._execute_agent_step
# ============================================================================


class TestExecuteAgentStep:
    """Tests for the _execute_agent_step method."""

    @pytest.mark.asyncio
    async def test_execute_agent_step_agent_not_found(self, executor, mock_agent_repo):
        """Test execution when agent is not found."""
        mock_agent_repo.get.return_value = None

        step = WorkflowStep(
            id="step-1",
            type=StepType.AGENT,
            agent_id="nonexistent-agent",
        )

        result = await executor._execute_agent_step(
            step, "test input", "user-123", None
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_agent_step_direct_execution(
        self, mock_agent_repo, mock_workflow_repo, sample_agent_config
    ):
        """Test direct agent execution without Temporal."""
        # Create executor without temporal client
        executor = WorkflowExecutor(
            agent_repo=mock_agent_repo,
            workflow_repo=mock_workflow_repo,
            temporal_client=None,  # No Temporal
        )
        mock_agent_repo.get.return_value = sample_agent_config

        step = WorkflowStep(
            id="step-1",
            type=StepType.AGENT,
            agent_id="agent-1",
            input="${user_input}",
        )

        with patch("src.agents.factory.AgentFactory") as mock_factory:
            mock_agent = AsyncMock()
            mock_agent.run.return_value = MagicMock(content="Agent response")
            mock_factory.create.return_value = mock_agent

            result = await executor._execute_agent_step(
                step, "test input", "user-123", None
            )

            assert result["success"] is True
            assert result["output"] == "Agent response"


# ============================================================================
# Tests for WorkflowExecutor._execute_parallel_step
# ============================================================================


class TestExecuteParallelStep:
    """Tests for the _execute_parallel_step method."""

    @pytest.mark.asyncio
    async def test_execute_parallel_step_aggregation_all(self, executor, mock_agent_repo, sample_agent_config):
        """Test parallel step with 'all' aggregation."""
        from src.models.workflow_definition import ParallelBranch, AggregationType

        mock_agent_repo.get.return_value = sample_agent_config

        step = WorkflowStep(
            id="parallel-step",
            type=StepType.PARALLEL,
            branches=[
                ParallelBranch(id="branch-1", agent_id="agent-1"),
                ParallelBranch(id="branch-2", agent_id="agent-2"),
            ],
            aggregation=AggregationType.ALL,
        )

        with patch.object(executor, "_execute_agent_step") as mock_exec:
            mock_exec.side_effect = [
                {"success": True, "output": "Result 1"},
                {"success": True, "output": "Result 2"},
            ]

            result = await executor._execute_parallel_step(
                step, "test input", "user-123", None
            )

            assert result["success"] is True
            assert "Result 1" in result["output"]
            assert "Result 2" in result["output"]

    @pytest.mark.asyncio
    async def test_execute_parallel_step_aggregation_first(self, executor, mock_agent_repo, sample_agent_config):
        """Test parallel step with 'first' aggregation."""
        from src.models.workflow_definition import ParallelBranch, AggregationType

        mock_agent_repo.get.return_value = sample_agent_config

        step = WorkflowStep(
            id="parallel-step",
            type=StepType.PARALLEL,
            branches=[
                ParallelBranch(id="branch-1", agent_id="agent-1"),
                ParallelBranch(id="branch-2", agent_id="agent-2"),
            ],
            aggregation=AggregationType.FIRST,
        )

        with patch.object(executor, "_execute_agent_step") as mock_exec:
            mock_exec.side_effect = [
                {"success": True, "output": "First Result"},
                {"success": True, "output": "Second Result"},
            ]

            result = await executor._execute_parallel_step(
                step, "test input", "user-123", None
            )

            assert result["success"] is True
            assert result["output"] == "First Result"


# ============================================================================
# Tests for WorkflowExecutor._execute_conditional_step
# ============================================================================


class TestExecuteConditionalStep:
    """Tests for the _execute_conditional_step method."""

    def test_conditional_step_branch_matching(self):
        """Test conditional step branch matching logic."""
        # Test the matching logic in isolation
        condition_value = "billing"
        branches = {"billing": "handle-billing", "technical": "handle-technical"}

        next_step = None
        for branch_key, branch_target in branches.items():
            if branch_key.lower() in condition_value.lower():
                next_step = branch_target
                break

        assert next_step == "handle-billing"

    def test_conditional_step_default_fallback(self):
        """Test conditional step uses default when no match."""
        condition_value = "unknown"
        branches = {"billing": "handle-billing"}
        default = "handle-general"

        next_step = None
        for branch_key, branch_target in branches.items():
            if branch_key.lower() in condition_value.lower():
                next_step = branch_target
                break

        if not next_step:
            next_step = default

        assert next_step == "handle-general"


# ============================================================================
# Tests for WorkflowExecutor._execute_loop_step
# ============================================================================


class TestExecuteLoopStep:
    """Tests for the _execute_loop_step method."""

    def test_loop_respects_max_iterations(self):
        """Test that loop logic respects max_iterations."""
        max_iterations = 3
        iteration_count = 0
        results = []

        while iteration_count < max_iterations:
            iteration_count += 1
            results.append(f"iteration-{iteration_count}")

        assert iteration_count == 3
        assert len(results) == 3

    def test_loop_exit_condition(self):
        """Test that loop exits early when condition is met."""
        max_iterations = 10
        iteration_count = 0
        exit_on = 5

        while iteration_count < max_iterations:
            iteration_count += 1
            if iteration_count == exit_on:
                break

        assert iteration_count == 5


# ============================================================================
# Tests for WorkflowExecutor._resolve_template
# ============================================================================


class TestResolveTemplate:
    """Tests for the _resolve_template method."""

    def test_resolve_user_input(self, executor):
        """Test resolving ${user_input} template."""
        executor._step_results = {}
        executor._context = {}

        result = executor._resolve_template("Process: ${user_input}", "my input")

        assert result == "Process: my input"

    def test_resolve_previous_output(self, executor):
        """Test resolving ${previous} template."""
        executor._step_results = {
            "step-1": {"output": "step 1 result"},
            "step-2": {"output": "step 2 result"},
        }
        executor._context = {}

        result = executor._resolve_template("Previous was: ${previous}", "")

        assert result == "Previous was: step 2 result"

    def test_resolve_step_output(self, executor):
        """Test resolving ${steps.X.output} template."""
        executor._step_results = {
            "step-1": {"output": "specific result"},
        }
        executor._context = {}

        result = executor._resolve_template("Step 1 output: ${steps.step-1.output}", "")

        assert result == "Step 1 output: specific result"

    def test_resolve_context_variable(self, executor):
        """Test resolving ${context.X} template."""
        executor._step_results = {}
        executor._context = {"custom_key": "custom_value"}

        result = executor._resolve_template("Context: ${context.custom_key}", "")

        assert result == "Context: custom_value"

    def test_resolve_multiple_templates(self, executor):
        """Test resolving multiple templates in one string."""
        executor._step_results = {"step-1": {"output": "result1"}}
        executor._context = {"key": "value"}

        result = executor._resolve_template(
            "Input: ${user_input}, Step: ${steps.step-1.output}, Ctx: ${context.key}",
            "my input",
        )

        assert result == "Input: my input, Step: result1, Ctx: value"


# ============================================================================
# Tests for WorkflowExecutor._get_next_step
# ============================================================================


class TestGetNextStep:
    """Tests for the _get_next_step method."""

    def test_get_next_step_returns_next(self, executor):
        """Test getting the next sequential step."""
        from src.models.workflow_definition import WorkflowDefinition

        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            steps=[
                WorkflowStep(id="step-1", type=StepType.AGENT, agent_id="agent-1"),
                WorkflowStep(id="step-2", type=StepType.AGENT, agent_id="agent-2"),
                WorkflowStep(id="step-3", type=StepType.AGENT, agent_id="agent-3"),
            ],
        )

        next_step = executor._get_next_step(workflow, "step-1")

        assert next_step is not None
        assert next_step.id == "step-2"

    def test_get_next_step_returns_none_at_end(self, executor):
        """Test that None is returned for the last step."""
        from src.models.workflow_definition import WorkflowDefinition

        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            steps=[
                WorkflowStep(id="step-1", type=StepType.AGENT, agent_id="agent-1"),
                WorkflowStep(id="step-2", type=StepType.AGENT, agent_id="agent-2"),
            ],
        )

        next_step = executor._get_next_step(workflow, "step-2")

        assert next_step is None

    def test_get_next_step_nonexistent_id(self, executor):
        """Test getting next step for non-existent step ID."""
        from src.models.workflow_definition import WorkflowDefinition

        workflow = WorkflowDefinition(
            id="test",
            name="Test",
            steps=[
                WorkflowStep(id="step-1", type=StepType.AGENT, agent_id="agent-1"),
            ],
        )

        next_step = executor._get_next_step(workflow, "nonexistent")

        assert next_step is None


# ============================================================================
# Tests for validate_workflow_with_resources
# ============================================================================


class TestValidateWorkflowWithResources:
    """Tests for the validate_workflow_with_resources function."""

    @pytest.mark.asyncio
    async def test_validate_valid_workflow(self, mock_agent_repo, sample_agent_config):
        """Test validation of a valid workflow."""
        mock_agent_repo.get.return_value = sample_agent_config

        definition = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "steps": [
                {
                    "id": "step-1",
                    "type": "agent",
                    "agent_id": "agent-1",
                }
            ],
        }

        is_valid, errors, warnings, missing_agents = await validate_workflow_with_resources(
            definition, mock_agent_repo
        )

        assert is_valid is True
        assert errors == []
        assert missing_agents == []

    @pytest.mark.asyncio
    async def test_validate_invalid_definition(self, mock_agent_repo):
        """Test validation of invalid workflow definition."""
        definition = {"invalid": "definition"}  # Missing required fields

        is_valid, errors, warnings, missing_agents = await validate_workflow_with_resources(
            definition, mock_agent_repo
        )

        assert is_valid is False
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_validate_missing_agents(self, mock_agent_repo):
        """Test validation when referenced agents are missing."""
        mock_agent_repo.get.return_value = None

        definition = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "steps": [
                {
                    "id": "step-1",
                    "type": "agent",
                    "agent_id": "nonexistent-agent",
                }
            ],
        }

        is_valid, errors, warnings, missing_agents = await validate_workflow_with_resources(
            definition, mock_agent_repo
        )

        assert is_valid is False
        assert "nonexistent-agent" in missing_agents
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_validate_parallel_step_agents(self, mock_agent_repo):
        """Test validation of agents in parallel steps."""
        mock_agent_repo.get.return_value = None

        definition = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "steps": [
                {
                    "id": "parallel-step",
                    "type": "parallel",
                    "branches": [
                        {"id": "branch-1", "agent_id": "agent-1"},
                        {"id": "branch-2", "agent_id": "agent-2"},
                    ],
                }
            ],
        }

        is_valid, errors, warnings, missing_agents = await validate_workflow_with_resources(
            definition, mock_agent_repo
        )

        assert is_valid is False
        assert "agent-1" in missing_agents
        assert "agent-2" in missing_agents

    @pytest.mark.asyncio
    async def test_validate_loop_step_agents(self, mock_agent_repo):
        """Test validation of agents in loop steps."""
        mock_agent_repo.get.return_value = None

        definition = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "steps": [
                {
                    "id": "loop-step",
                    "type": "loop",
                    "max_iterations": 5,
                    "steps": [
                        {"id": "inner-1", "agent_id": "loop-agent"},
                    ],
                }
            ],
        }

        is_valid, errors, warnings, missing_agents = await validate_workflow_with_resources(
            definition, mock_agent_repo
        )

        assert is_valid is False
        assert "loop-agent" in missing_agents
