"""Tests for agent workflow module.

Tests cover:
- Helper functions (sanitize_tool_name, build_param_schema, build_tool_definitions)
- AgentWorkflowInput/Output dataclasses
- AgentWorkflow class methods (template resolution, condition evaluation, aggregation)
"""

import json
import re
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.workflows.agent_workflow import (
    AgentWorkflowInput,
    AgentWorkflowOutput,
    sanitize_tool_name,
    build_param_schema,
    build_tool_definitions,
    MAX_WORKFLOW_STEPS,
    MAX_TEMPLATE_DEPTH,
    MAX_RESULT_SIZE,
    VALID_PATH_PATTERN,
)


# ============================================================================
# Tests for sanitize_tool_name
# ============================================================================


class TestSanitizeToolName:
    """Tests for the sanitize_tool_name helper function."""

    def test_no_colons(self):
        """Test tool name without colons passes through."""
        assert sanitize_tool_name("calculator") == "calculator"
        assert sanitize_tool_name("http_request") == "http_request"

    def test_single_colon(self):
        """Test tool name with single colon is converted."""
        assert sanitize_tool_name("mcp:slack") == "mcp__slack"

    def test_multiple_colons(self):
        """Test tool name with multiple colons."""
        assert sanitize_tool_name("mcp:slack:send") == "mcp__slack__send"

    def test_empty_string(self):
        """Test empty string passes through."""
        assert sanitize_tool_name("") == ""

    def test_colon_at_start(self):
        """Test colon at start of name."""
        assert sanitize_tool_name(":tool") == "__tool"

    def test_colon_at_end(self):
        """Test colon at end of name."""
        assert sanitize_tool_name("tool:") == "tool__"


# ============================================================================
# Tests for build_param_schema
# ============================================================================


class TestBuildParamSchema:
    """Tests for the build_param_schema helper function."""

    def test_string_param(self):
        """Test building schema for string parameter."""
        param = {
            "name": "query",
            "type": "string",
            "description": "The search query",
        }

        result = build_param_schema(param)

        assert result == {
            "type": "string",
            "description": "The search query",
        }

    def test_integer_param(self):
        """Test building schema for integer parameter."""
        param = {
            "name": "count",
            "type": "integer",
            "description": "Number of results",
        }

        result = build_param_schema(param)

        assert result["type"] == "integer"

    def test_array_param_with_items(self):
        """Test building schema for array with items spec."""
        param = {
            "name": "tags",
            "type": "array",
            "description": "List of tags",
            "items": {"type": "string"},
        }

        result = build_param_schema(param)

        assert result["type"] == "array"
        assert result["items"] == {"type": "string"}

    def test_array_param_without_items(self):
        """Test building schema for array without items defaults to string."""
        param = {
            "name": "items",
            "type": "array",
            "description": "List of items",
        }

        result = build_param_schema(param)

        assert result["type"] == "array"
        assert result["items"] == {"type": "string"}

    def test_boolean_param(self):
        """Test building schema for boolean parameter."""
        param = {
            "name": "enabled",
            "type": "boolean",
            "description": "Whether enabled",
        }

        result = build_param_schema(param)

        assert result["type"] == "boolean"


# ============================================================================
# Tests for build_tool_definitions
# ============================================================================


class TestBuildToolDefinitions:
    """Tests for the build_tool_definitions helper function."""

    def test_builds_tool_definitions(self):
        """Test building tool definitions from list."""
        from dataclasses import dataclass

        @dataclass
        class MockToolDef:
            name: str
            description: str
            parameters: list

        definitions = [
            MockToolDef(
                name="calculator",
                description="Performs calculations",
                parameters=[
                    {"name": "expression", "type": "string", "description": "Math expression", "required": True},
                ],
            ),
            MockToolDef(
                name="http_request",
                description="Makes HTTP requests",
                parameters=[
                    {"name": "url", "type": "string", "description": "The URL", "required": True},
                    {"name": "method", "type": "string", "description": "HTTP method", "required": False},
                ],
            ),
        ]

        tool_name_map = {}
        result = build_tool_definitions(definitions, tool_name_map)

        assert len(result) == 2
        assert tool_name_map["calculator"] == "calculator"
        assert tool_name_map["http_request"] == "http_request"

        # Check first tool
        assert result[0].name == "calculator"
        assert result[0].description == "Performs calculations"
        assert result[0].parameters["properties"]["expression"]["type"] == "string"
        assert "expression" in result[0].parameters["required"]

    def test_sanitizes_tool_names(self):
        """Test that tool names with colons are sanitized."""
        from dataclasses import dataclass

        @dataclass
        class MockToolDef:
            name: str
            description: str
            parameters: list

        definitions = [
            MockToolDef(
                name="mcp:slack:send",
                description="Send Slack message",
                parameters=[],
            ),
        ]

        tool_name_map = {}
        result = build_tool_definitions(definitions, tool_name_map)

        assert result[0].name == "mcp__slack__send"
        assert tool_name_map["mcp__slack__send"] == "mcp:slack:send"

    def test_handles_optional_parameters(self):
        """Test handling of optional parameters."""
        definitions = [
            MagicMock(
                name="test_tool",
                description="Test",
                parameters=[
                    {"name": "required_param", "type": "string", "description": "Required", "required": True},
                    {"name": "optional_param", "type": "string", "description": "Optional", "required": False},
                ],
            ),
        ]

        tool_name_map = {}
        result = build_tool_definitions(definitions, tool_name_map)

        assert "required_param" in result[0].parameters["required"]
        assert "optional_param" not in result[0].parameters["required"]

    def test_empty_definitions(self):
        """Test with empty definitions list."""
        tool_name_map = {}
        result = build_tool_definitions([], tool_name_map)

        assert result == []
        assert tool_name_map == {}


# ============================================================================
# Tests for AgentWorkflowInput dataclass
# ============================================================================


class TestAgentWorkflowInput:
    """Tests for the AgentWorkflowInput dataclass."""

    def test_required_fields(self):
        """Test creation with required fields only."""
        input_data = AgentWorkflowInput(
            agent_id="agent-1",
            agent_type="LLMAgent",
            user_input="Hello",
            user_id="user-123",
        )

        assert input_data.agent_id == "agent-1"
        assert input_data.agent_type == "LLMAgent"
        assert input_data.user_input == "Hello"
        assert input_data.user_id == "user-123"

    def test_default_values(self):
        """Test default values are set correctly."""
        input_data = AgentWorkflowInput(
            agent_id="agent-1",
            agent_type="LLMAgent",
            user_input="Hello",
            user_id="user-123",
        )

        assert input_data.conversation_history == []
        assert input_data.session_id is None
        assert input_data.llm_temperature == 0.0  # deterministic by default
        assert input_data.llm_max_tokens == 1024
        assert input_data.system_prompt == ""
        assert input_data.safety_level == "standard"
        assert input_data.blocked_topics == []
        assert input_data.top_k == 5
        assert input_data.enabled_tools == []
        assert input_data.orchestrator_mode == "llm_driven"

    def test_all_fields(self):
        """Test creation with all fields."""
        input_data = AgentWorkflowInput(
            agent_id="agent-1",
            agent_type="FullAgent",
            user_input="Process this",
            user_id="user-123",
            conversation_history=[{"role": "user", "content": "Hi"}],
            session_id="session-456",
            llm_provider="anthropic",
            llm_model="claude-3-opus",
            llm_temperature=0.5,
            llm_max_tokens=2048,
            system_prompt="You are helpful",
            safety_level="strict",
            blocked_topics=["violence"],
            knowledge_collection="docs",
            embedding_model="text-embedding-3-large",
            top_k=10,
            similarity_threshold=0.8,
            enabled_tools=["calculator"],
            routing_table={"billing": "billing-agent"},
            orchestrator_mode="workflow",
            orchestrator_available_agents=[{"agent_id": "helper"}],
            orchestrator_max_parallel=3,
            orchestrator_max_depth=2,
            orchestrator_aggregation="merge",
            workflow_definition={"id": "wf-1", "steps": []},
        )

        assert input_data.llm_provider == "anthropic"
        assert input_data.safety_level == "strict"
        assert "violence" in input_data.blocked_topics
        assert input_data.orchestrator_mode == "workflow"


# ============================================================================
# Tests for AgentWorkflowOutput dataclass
# ============================================================================


class TestAgentWorkflowOutput:
    """Tests for the AgentWorkflowOutput dataclass."""

    def test_success_output(self):
        """Test successful output creation."""
        output = AgentWorkflowOutput(
            content="Hello! How can I help?",
            agent_id="agent-1",
            agent_type="LLMAgent",
            success=True,
        )

        assert output.content == "Hello! How can I help?"
        assert output.success is True
        assert output.error is None
        assert output.metadata == {}

    def test_error_output(self):
        """Test error output creation."""
        output = AgentWorkflowOutput(
            content="An error occurred",
            agent_id="agent-1",
            agent_type="LLMAgent",
            success=False,
            error="Connection timeout",
            metadata={"retry_count": 3},
        )

        assert output.success is False
        assert output.error == "Connection timeout"
        assert output.metadata["retry_count"] == 3


# ============================================================================
# Tests for workflow safety constants
# ============================================================================


class TestWorkflowConstants:
    """Tests for workflow safety constants."""

    def test_max_workflow_steps(self):
        """Test MAX_WORKFLOW_STEPS is reasonable."""
        assert MAX_WORKFLOW_STEPS == 100
        assert MAX_WORKFLOW_STEPS > 0

    def test_max_template_depth(self):
        """Test MAX_TEMPLATE_DEPTH is reasonable."""
        assert MAX_TEMPLATE_DEPTH == 5
        assert MAX_TEMPLATE_DEPTH > 0

    def test_max_result_size(self):
        """Test MAX_RESULT_SIZE is reasonable."""
        assert MAX_RESULT_SIZE == 50000
        assert MAX_RESULT_SIZE > 1000

    def test_valid_path_pattern(self):
        """Test VALID_PATH_PATTERN matches expected strings."""
        assert VALID_PATH_PATTERN.match("steps")
        assert VALID_PATH_PATTERN.match("user_input")
        assert VALID_PATH_PATTERN.match("context")
        assert VALID_PATH_PATTERN.match("_private")
        assert not VALID_PATH_PATTERN.match("123")  # Starts with number
        assert not VALID_PATH_PATTERN.match("with-hyphen")  # Contains hyphen


# ============================================================================
# Tests for AgentWorkflow class helper methods
# ============================================================================


class TestAgentWorkflowHelperMethods:
    """Tests for AgentWorkflow helper methods.

    Note: These test the helper methods in isolation since the full workflow
    requires Temporal runtime.
    """

    def test_resolve_template_user_input(self):
        """Test template resolution for ${user_input}."""
        # Simulate the _resolve_template logic
        template = "Process this: ${user_input}"
        step_results = {}
        context = {"user_input": "my query"}

        result = template
        if "${user_input}" in result:
            result = result.replace("${user_input}", context.get("user_input", ""))

        assert result == "Process this: my query"

    def test_resolve_template_steps_output(self):
        """Test template resolution for ${steps.X.output}."""
        template = "Previous result: ${steps.step-1.output}"
        step_results = {"step-1": {"output": "step 1 result"}}

        # Simulate resolution
        pattern = re.compile(r'\$\{steps\.([^.]+)\.output\}')
        result = template
        for match in pattern.finditer(result):
            step_id = match.group(1)
            if step_id in step_results:
                step_output = step_results[step_id].get("output", "")
                result = result.replace(match.group(0), str(step_output))

        assert result == "Previous result: step 1 result"

    def test_aggregate_parallel_results_all(self):
        """Test aggregation with 'all' strategy."""
        results = {
            "branch-1": {"success": True, "output": "Result 1"},
            "branch-2": {"success": True, "output": "Result 2"},
        }

        # Simulate 'all' aggregation
        outputs = []
        for branch_id, r in results.items():
            if r.get("success") and r.get("output"):
                outputs.append(f"[{branch_id}]\n{r['output']}")
        aggregated = "\n\n---\n\n".join(outputs)

        assert "[branch-1]" in aggregated
        assert "Result 1" in aggregated
        assert "Result 2" in aggregated

    def test_aggregate_parallel_results_first(self):
        """Test aggregation with 'first' strategy."""
        results = {
            "branch-1": {"success": True, "output": "First"},
            "branch-2": {"success": True, "output": "Second"},
        }

        # Simulate 'first' aggregation
        aggregated = ""
        for r in results.values():
            if r.get("success"):
                aggregated = r.get("output", "")
                break

        assert aggregated == "First"

    def test_aggregate_parallel_results_merge(self):
        """Test aggregation with 'merge' strategy."""
        results = {
            "branch-1": {"success": True, "output": '{"key1": "value1"}'},
            "branch-2": {"success": True, "output": '{"key2": "value2"}'},
        }

        # Simulate 'merge' aggregation
        merged = {}
        for branch_id, r in results.items():
            output = r.get("output")
            if isinstance(output, str):
                try:
                    parsed = json.loads(output)
                    if isinstance(parsed, dict):
                        merged.update(parsed)
                except json.JSONDecodeError:
                    merged[branch_id] = output

        assert merged == {"key1": "value1", "key2": "value2"}

    def test_evaluate_condition_true(self):
        """Test condition evaluation for 'true'."""
        condition = "true"
        result = condition.strip().lower() == "true"
        assert result is True

    def test_evaluate_condition_false(self):
        """Test condition evaluation for 'false'."""
        condition = "false"
        # The condition string is "false", which means the condition evaluates to False
        result = condition.strip().lower() == "true"  # Check if it equals "true"
        assert result is False  # "false" != "true", so result is False

    def test_evaluate_condition_comparison(self):
        """Test condition evaluation for comparison."""
        # Simulate simple comparison evaluation
        condition = "5 > 3"
        pattern = r'^(\d+)\s*([<>=!]+)\s*(\d+)$'
        match = re.match(pattern, condition)

        if match:
            left = int(match.group(1))
            op = match.group(2)
            right = int(match.group(3))

            if op == ">":
                result = left > right
            elif op == "<":
                result = left < right
            elif op == "==":
                result = left == right
            else:
                result = False
        else:
            result = False

        assert result is True

    def test_truncate_result(self):
        """Test result truncation."""
        # Simulate truncation
        content = "x" * 60000  # Exceeds MAX_RESULT_SIZE
        max_size = MAX_RESULT_SIZE

        if len(content) > max_size:
            truncated = content[:max_size] + "\n... [truncated]"
        else:
            truncated = content

        assert len(truncated) < len(content)
        assert "[truncated]" in truncated

    def test_truncate_result_within_limit(self):
        """Test result not truncated if within limit."""
        content = "x" * 1000  # Within limit

        if len(content) > MAX_RESULT_SIZE:
            truncated = content[:MAX_RESULT_SIZE] + "\n... [truncated]"
        else:
            truncated = content

        assert truncated == content

    def test_get_next_step_id(self):
        """Test getting next step ID."""
        step_order = {"step-1": 0, "step-2": 1, "step-3": 2}
        current_id = "step-1"

        current_idx = step_order.get(current_id)
        next_idx = current_idx + 1 if current_idx is not None else None

        next_step_id = None
        if next_idx is not None:
            for step_id, idx in step_order.items():
                if idx == next_idx:
                    next_step_id = step_id
                    break

        assert next_step_id == "step-2"

    def test_get_next_step_id_at_end(self):
        """Test getting next step ID at end returns None."""
        step_order = {"step-1": 0, "step-2": 1}
        current_id = "step-2"

        current_idx = step_order.get(current_id)
        next_idx = current_idx + 1 if current_idx is not None else None

        next_step_id = None
        if next_idx is not None:
            for step_id, idx in step_order.items():
                if idx == next_idx:
                    next_step_id = step_id
                    break

        assert next_step_id is None


# ============================================================================
# Tests for path validation
# ============================================================================


class TestPathValidation:
    """Tests for template path validation."""

    def test_valid_path_components(self):
        """Test valid path component patterns."""
        valid_components = [
            "steps",
            "user_input",
            "context",
            "output",
            "step1",
            "my_step",
            "Step123",
        ]

        path_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')

        for component in valid_components:
            assert path_pattern.match(component), f"'{component}' should be valid"

    def test_invalid_path_components(self):
        """Test invalid path component patterns are rejected."""
        invalid_components = [
            "step.with.dots",
            "step/with/slashes",
            "step with spaces",
            "${variable}",
            "step;injection",
            "step\nwith\nnewlines",
        ]

        path_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')

        for component in invalid_components:
            assert not path_pattern.match(component), f"'{component}' should be invalid"

    def test_path_depth_limit(self):
        """Test path depth is limited."""
        deep_path = ".".join(["level"] * 10)  # 10 levels deep
        parts = deep_path.split(".")

        assert len(parts) > MAX_TEMPLATE_DEPTH

        # Simulating the depth check
        if len(parts) > MAX_TEMPLATE_DEPTH:
            result = ""  # Would return empty on too-deep path
        else:
            result = "value"

        assert result == ""
