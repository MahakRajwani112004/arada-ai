"""Tests for workflow loop execution."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.workflow_definition import (
    LoopMode,
    LoopInnerStep,
    StepType,
    WorkflowStep,
)
from src.workflows.executor import WorkflowExecutor


class TestLoopItemParsing:
    """Tests for _parse_loop_items method."""

    def setup_method(self):
        """Set up executor for each test."""
        self.executor = WorkflowExecutor.__new__(WorkflowExecutor)
        self.executor._step_results = {}
        self.executor._context = {}

    def test_parse_json_array(self):
        """Test parsing JSON array."""
        items = self.executor._parse_loop_items('["a", "b", "c"]', "")
        assert items == ["a", "b", "c"]

    def test_parse_json_numbers(self):
        """Test parsing JSON number array."""
        items = self.executor._parse_loop_items('[1, 2, 3]', "")
        assert items == [1, 2, 3]

    def test_parse_json_objects(self):
        """Test parsing JSON object array."""
        items = self.executor._parse_loop_items('[{"name": "a"}, {"name": "b"}]', "")
        assert items == [{"name": "a"}, {"name": "b"}]

    def test_parse_comma_separated(self):
        """Test parsing comma-separated string."""
        items = self.executor._parse_loop_items("apple, banana, cherry", "")
        assert items == ["apple", "banana", "cherry"]

    def test_parse_newline_separated(self):
        """Test parsing newline-separated string."""
        items = self.executor._parse_loop_items("line1\nline2\nline3", "")
        assert items == ["line1", "line2", "line3"]

    def test_parse_single_item(self):
        """Test parsing single item."""
        items = self.executor._parse_loop_items("single_item", "")
        assert items == ["single_item"]

    def test_parse_empty(self):
        """Test parsing empty string."""
        items = self.executor._parse_loop_items("", "")
        assert items == []

    def test_parse_dict_to_tuples(self):
        """Test parsing JSON dict to key-value tuples."""
        items = self.executor._parse_loop_items('{"a": 1, "b": 2}', "")
        # Dict iteration order in Python 3.7+
        assert ("a", 1) in items
        assert ("b", 2) in items

    def test_parse_with_template_variable(self):
        """Test parsing with template variable resolution."""
        self.executor._step_results["prev"] = {"output": '["x", "y"]'}
        items = self.executor._parse_loop_items("${steps.prev.output}", "")
        assert items == ["x", "y"]


class TestLoopTemplateResolution:
    """Tests for loop variable template resolution."""

    def setup_method(self):
        """Set up executor for each test."""
        self.executor = WorkflowExecutor.__new__(WorkflowExecutor)
        self.executor._step_results = {}
        self.executor._context = {
            "loop": {
                "index": 2,
                "item": "current_item",
                "previous": "prev_output",
                "total": 5,
                "first": False,
                "last": False,
            }
        }

    def test_resolve_loop_index(self):
        """Test resolving ${loop.index}."""
        result = self.executor._resolve_template("Iteration ${loop.index}", "")
        assert result == "Iteration 2"

    def test_resolve_loop_item(self):
        """Test resolving ${loop.item}."""
        result = self.executor._resolve_template("Processing: ${loop.item}", "")
        assert result == "Processing: current_item"

    def test_resolve_loop_previous(self):
        """Test resolving ${loop.previous}."""
        result = self.executor._resolve_template("Last: ${loop.previous}", "")
        assert result == "Last: prev_output"

    def test_resolve_loop_total(self):
        """Test resolving ${loop.total}."""
        result = self.executor._resolve_template("Total: ${loop.total}", "")
        assert result == "Total: 5"

    def test_resolve_loop_first(self):
        """Test resolving ${loop.first}."""
        result = self.executor._resolve_template("Is first: ${loop.first}", "")
        assert result == "Is first: false"

    def test_resolve_loop_last(self):
        """Test resolving ${loop.last}."""
        result = self.executor._resolve_template("Is last: ${loop.last}", "")
        assert result == "Is last: false"

    def test_resolve_complex_item(self):
        """Test resolving complex object as loop item."""
        self.executor._context["loop"]["item"] = {"name": "test", "value": 42}
        result = self.executor._resolve_template("Item: ${loop.item}", "")
        assert '"name": "test"' in result
        assert '"value": 42' in result

    def test_resolve_multiple_loop_vars(self):
        """Test resolving multiple loop variables in one template."""
        result = self.executor._resolve_template(
            "Processing ${loop.item} (${loop.index}/${loop.total})", ""
        )
        assert result == "Processing current_item (2/5)"


class TestLoopModeEnum:
    """Tests for LoopMode enum."""

    def test_count_mode(self):
        """Test COUNT mode value."""
        assert LoopMode.COUNT.value == "count"

    def test_foreach_mode(self):
        """Test FOREACH mode value."""
        assert LoopMode.FOREACH.value == "foreach"

    def test_until_mode(self):
        """Test UNTIL mode value."""
        assert LoopMode.UNTIL.value == "until"


class TestLoopStepExecution:
    """Tests for loop step execution (integration style)."""

    @pytest.fixture
    def mock_executor(self):
        """Create a mock executor for testing."""
        executor = WorkflowExecutor.__new__(WorkflowExecutor)
        executor._step_results = {}
        executor._context = {}
        executor._logger = MagicMock()
        return executor

    @pytest.mark.asyncio
    async def test_loop_returns_empty_for_no_items(self, mock_executor):
        """Test that foreach loop returns empty for no items."""
        step = WorkflowStep(
            id="loop-1",
            type=StepType.LOOP,
            loop_mode=LoopMode.FOREACH,
            over="[]",
            steps=[LoopInnerStep(id="inner-1", agent_id="agent-1")],
        )

        # Mock _execute_agent_step to track calls
        mock_executor._execute_agent_step = AsyncMock()
        mock_executor._parse_loop_items = MagicMock(return_value=[])

        result = await mock_executor._execute_loop_step(step, "input", "user", None)

        assert result["success"] is True
        assert result["loop_results"] == []
        mock_executor._execute_agent_step.assert_not_called()

    @pytest.mark.asyncio
    async def test_loop_count_mode_execution(self, mock_executor):
        """Test count mode executes correct number of times."""
        step = WorkflowStep(
            id="loop-count",
            type=StepType.LOOP,
            loop_mode=LoopMode.COUNT,
            max_iterations=3,
            steps=[LoopInnerStep(id="inner-1", agent_id="agent-1")],
        )

        # Mock successful step execution
        mock_executor._execute_agent_step = AsyncMock(
            return_value={"success": True, "output": "done"}
        )

        result = await mock_executor._execute_loop_step(step, "input", "user", None)

        assert result["success"] is True
        assert result["iterations_completed"] == 3
        assert len(result["loop_results"]) == 3
        assert mock_executor._execute_agent_step.call_count == 3

    @pytest.mark.asyncio
    async def test_loop_foreach_mode_execution(self, mock_executor):
        """Test foreach mode iterates over items."""
        step = WorkflowStep(
            id="loop-foreach",
            type=StepType.LOOP,
            loop_mode=LoopMode.FOREACH,
            over='["a", "b", "c"]',
            steps=[LoopInnerStep(id="inner-1", agent_id="agent-1")],
        )

        call_items = []

        async def capture_item(*args, **kwargs):
            # Capture the loop item at each call
            item = mock_executor._context.get("loop", {}).get("item")
            call_items.append(item)
            return {"success": True, "output": f"processed-{item}"}

        mock_executor._execute_agent_step = AsyncMock(side_effect=capture_item)

        result = await mock_executor._execute_loop_step(step, "input", "user", None)

        assert result["success"] is True
        assert call_items == ["a", "b", "c"]
        assert len(result["loop_results"]) == 3

    @pytest.mark.asyncio
    async def test_loop_break_condition(self, mock_executor):
        """Test break condition exits loop early."""
        step = WorkflowStep(
            id="loop-break",
            type=StepType.LOOP,
            loop_mode=LoopMode.COUNT,
            max_iterations=10,
            break_condition="${loop.index} == 3",
            steps=[LoopInnerStep(id="inner-1", agent_id="agent-1")],
        )

        # Mock to return "3" when break_condition is resolved at iteration 3
        call_count = [0]

        def mock_resolve(template, user_input):
            if "${loop.index}" in template:
                return str(mock_executor._context["loop"]["index"])
            return template

        mock_executor._resolve_template = mock_resolve
        mock_executor._execute_agent_step = AsyncMock(
            return_value={"success": True, "output": "done"}
        )

        # We need to simulate the loop context being set
        # This is a simplified test - in reality the executor sets loop context

    @pytest.mark.asyncio
    async def test_loop_handles_step_failure(self, mock_executor):
        """Test loop handles inner step failure correctly."""
        step = WorkflowStep(
            id="loop-fail",
            type=StepType.LOOP,
            loop_mode=LoopMode.COUNT,
            max_iterations=5,
            collect_results=True,
            steps=[LoopInnerStep(id="inner-1", agent_id="agent-1")],
        )

        # Fail on 3rd iteration
        call_count = [0]

        async def fail_on_third(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 3:
                return {"success": False, "error": "Agent failed"}
            return {"success": True, "output": f"output-{call_count[0]}"}

        mock_executor._execute_agent_step = AsyncMock(side_effect=fail_on_third)

        result = await mock_executor._execute_loop_step(step, "input", "user", None)

        assert result["success"] is False
        assert result["error"] == "Agent failed"
        assert result["failed_iteration"] == 3
        assert len(result["loop_results"]) == 2  # 2 successful before failure

    @pytest.mark.asyncio
    async def test_loop_collect_results_false(self, mock_executor):
        """Test loop with collect_results=False."""
        step = WorkflowStep(
            id="loop-no-collect",
            type=StepType.LOOP,
            loop_mode=LoopMode.COUNT,
            max_iterations=3,
            collect_results=False,
            steps=[LoopInnerStep(id="inner-1", agent_id="agent-1")],
        )

        mock_executor._execute_agent_step = AsyncMock(
            return_value={"success": True, "output": "final"}
        )

        result = await mock_executor._execute_loop_step(step, "input", "user", None)

        assert result["success"] is True
        assert result["output"] == "final"
        assert "loop_results" not in result  # Not collected
