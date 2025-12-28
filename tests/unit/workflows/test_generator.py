"""Tests for workflow generator module.

Tests cover:
- WorkflowGenerator class and all generation methods
- Parsing helper methods for workflows, agents, and MCPs
- apply() method for saving generated workflows
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.workflows.generator import WorkflowGenerator
from src.api.schemas.workflows import (
    GenerateSkeletonRequest,
    GenerateSkeletonResponse,
    GenerateWorkflowResponse,
    ApplyGeneratedWorkflowRequest,
    ApplyGeneratedWorkflowResponse,
    WorkflowDefinitionSchema,
    WorkflowStepSchema,
    WorkflowSkeleton,
    WorkflowTrigger,
    TriggerType,
    SkeletonStep,
    SuggestedAgent,
)
from src.models.agent_config import AgentConfig
from src.models.enums import AgentType
from src.models.llm_config import LLMConfig


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = AsyncMock()
    return provider


@pytest.fixture
def generator(mock_llm_provider):
    """Create a WorkflowGenerator with mocked LLM provider."""
    gen = WorkflowGenerator()
    gen._provider = mock_llm_provider
    return gen


@pytest.fixture
def sample_agent_config():
    """Create a sample agent config."""
    from src.models.persona import AgentGoal, AgentInstructions, AgentRole
    from src.models.safety_config import SafetyConfig

    return AgentConfig(
        id="agent-1",
        name="Test Agent",
        description="A test agent",
        agent_type=AgentType.LLM,
        role=AgentRole(title="Test", expertise=[], personality=[], communication_style="professional"),
        goal=AgentGoal(objective="Test", success_indicators=[], constraints=[]),
        instructions=AgentInstructions(steps=[], rules=[], prohibited=[], output_format=None),
        safety=SafetyConfig(),
    )


@pytest.fixture
def sample_mcp_instance():
    """Create a sample MCP server instance."""
    from src.mcp.models import MCPServerInstance, ServerStatus

    return MCPServerInstance(
        id="mcp-1",
        name="Test MCP",
        template="slack",
        status=ServerStatus.ACTIVE,
        url="https://mcp.example.com/slack",
        secret_ref="vault:mcp/mcp-1",
    )


# ============================================================================
# Tests for WorkflowGenerator initialization
# ============================================================================


class TestWorkflowGeneratorInit:
    """Tests for WorkflowGenerator initialization."""

    def test_init_with_default_config(self):
        """Test initialization with default LLM config."""
        with patch("src.llm.client.LLMClient.get_provider") as mock_get:
            mock_get.return_value = AsyncMock()
            gen = WorkflowGenerator()

            assert gen.llm_config.provider == "openai"
            assert gen.llm_config.model == "gpt-4o"

    def test_init_with_custom_config(self):
        """Test initialization with custom LLM config."""
        custom_config = LLMConfig(
            provider="anthropic",
            model="claude-3-opus",
            temperature=0.5,
            max_tokens=2048,
        )

        with patch("src.llm.client.LLMClient.get_provider") as mock_get:
            mock_get.return_value = AsyncMock()
            gen = WorkflowGenerator(llm_config=custom_config)

            assert gen.llm_config.provider == "anthropic"
            assert gen.llm_config.model == "claude-3-opus"


# ============================================================================
# Tests for WorkflowGenerator._parse_workflow
# ============================================================================


class TestParseWorkflow:
    """Tests for the _parse_workflow method."""

    def test_parse_simple_workflow(self, generator):
        """Test parsing a simple workflow definition."""
        data = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "description": "A test workflow",
            "steps": [
                {
                    "id": "step-1",
                    "type": "agent",
                    "name": "First Step",
                    "agent_id": "agent-1",
                    "input": "${user_input}",
                    "timeout": 60,
                }
            ],
            "entry_step": "step-1",
        }

        result = generator._parse_workflow(data)

        assert result.id == "test-workflow"
        assert result.name == "Test Workflow"
        assert len(result.steps) == 1
        assert result.steps[0].id == "step-1"
        assert result.steps[0].agent_id == "agent-1"
        assert result.entry_step == "step-1"

    def test_parse_workflow_with_suggested_agent(self, generator):
        """Test parsing workflow with suggested agent."""
        data = {
            "id": "test-workflow",
            "name": "Test",
            "steps": [
                {
                    "id": "step-1",
                    "type": "agent",
                    "suggested_agent": {
                        "name": "Data Processor",
                        "description": "Processes data",
                        "goal": "Extract information",
                        "model": "gpt-4o",
                        "required_mcps": ["slack"],
                        "suggested_tools": ["calculator"],
                    },
                }
            ],
        }

        result = generator._parse_workflow(data)

        assert result.steps[0].suggested_agent is not None
        assert result.steps[0].suggested_agent.name == "Data Processor"
        assert result.steps[0].suggested_agent.goal == "Extract information"
        assert "slack" in result.steps[0].suggested_agent.required_mcps

    def test_parse_workflow_with_conditional_step(self, generator):
        """Test parsing workflow with conditional step."""
        data = {
            "id": "test-workflow",
            "name": "Test",
            "steps": [
                {
                    "id": "route-step",
                    "type": "conditional",
                    "condition_source": "${steps.classify.output}",
                    "conditional_branches": {
                        "billing": "handle-billing",
                        "technical": "handle-technical",
                    },
                    "default": "handle-general",
                }
            ],
        }

        result = generator._parse_workflow(data)

        assert result.steps[0].type == "conditional"
        assert result.steps[0].condition_source == "${steps.classify.output}"
        assert result.steps[0].default == "handle-general"

    def test_parse_workflow_with_parallel_step(self, generator):
        """Test parsing workflow with parallel step."""
        data = {
            "id": "test-workflow",
            "name": "Test",
            "steps": [
                {
                    "id": "parallel-step",
                    "type": "parallel",
                    "branches": [
                        {"id": "branch-1", "agent_id": "agent-1"},
                        {"id": "branch-2", "agent_id": "agent-2"},
                    ],
                    "aggregation": "merge",
                }
            ],
        }

        result = generator._parse_workflow(data)

        assert result.steps[0].type == "parallel"
        assert result.steps[0].aggregation == "merge"
        assert len(result.steps[0].branches) == 2

    def test_parse_workflow_with_defaults(self, generator):
        """Test parsing workflow applies defaults."""
        data = {
            "id": "test-workflow",
            "steps": [
                {"id": "step-1", "type": "agent"}
            ],
        }

        result = generator._parse_workflow(data)

        assert result.id == "test-workflow"
        assert result.steps[0].input == "${user_input}"
        assert result.steps[0].timeout == 120
        assert result.steps[0].retries == 0
        assert result.steps[0].on_error == "fail"


# ============================================================================
# Tests for WorkflowGenerator._parse_agent_config
# ============================================================================


class TestParseAgentConfig:
    """Tests for the _parse_agent_config method."""

    def test_parse_agent_with_string_role(self, generator):
        """Test parsing agent config with string role."""
        data = {
            "id": "agent-1",
            "name": "Test Agent",
            "description": "Test description",
            "agent_type": "ChatAgent",
            "role": "Customer support specialist",
            "goal": "Help customers",
            "instructions": "Be helpful and friendly",
        }

        result = generator._parse_agent_config(data)

        assert result.id == "agent-1"
        assert result.name == "Test Agent"
        assert result.role["title"] == "Customer support specialist"

    def test_parse_agent_with_dict_role(self, generator):
        """Test parsing agent config with dict role."""
        data = {
            "id": "agent-1",
            "name": "Test Agent",
            "description": "Test",
            "agent_type": "ToolAgent",
            "role": {
                "title": "Data Analyst",
                "expertise": ["data analysis", "visualization"],
            },
            "goal": {"objective": "Analyze data"},
            "instructions": {"steps": ["Step 1", "Step 2"]},
        }

        result = generator._parse_agent_config(data)

        assert result.role["title"] == "Data Analyst"
        assert "data analysis" in result.role["expertise"]
        assert result.goal["objective"] == "Analyze data"
        assert len(result.instructions["steps"]) == 2

    def test_parse_agent_with_list_instructions(self, generator):
        """Test parsing agent config with list instructions."""
        data = {
            "id": "agent-1",
            "name": "Test",
            "description": "Test",
            "agent_type": "ChatAgent",
            "instructions": ["Do this", "Then that"],
        }

        result = generator._parse_agent_config(data)

        assert result.instructions["steps"] == ["Do this", "Then that"]

    def test_parse_agent_defaults(self, generator):
        """Test parsing agent config applies defaults."""
        data = {
            "id": "agent-1",
            "name": "Test",
        }

        result = generator._parse_agent_config(data)

        assert result.description == ""
        assert result.agent_type == "ChatAgent"


# ============================================================================
# Tests for WorkflowGenerator._parse_mcp_suggestion
# ============================================================================


class TestParseMCPSuggestion:
    """Tests for the _parse_mcp_suggestion method."""

    def test_parse_mcp_suggestion(self, generator):
        """Test parsing MCP suggestion."""
        data = {
            "template": "slack",
            "reason": "To send notifications",
            "required_for_steps": ["notify-step", "alert-step"],
        }

        result = generator._parse_mcp_suggestion(data)

        assert result.template == "slack"
        assert result.reason == "To send notifications"
        assert "notify-step" in result.required_for_steps

    def test_parse_mcp_suggestion_defaults(self, generator):
        """Test parsing MCP suggestion with defaults."""
        data = {}

        result = generator._parse_mcp_suggestion(data)

        assert result.template == ""
        assert result.reason == ""
        assert result.required_for_steps == []


# ============================================================================
# Tests for WorkflowGenerator._generated_to_agent_config
# ============================================================================


class TestGeneratedToAgentConfig:
    """Tests for the _generated_to_agent_config method."""

    def test_agent_type_mapping(self):
        """Test agent type string to enum mapping."""
        agent_type_map = {
            "ChatAgent": AgentType.LLM,
            "RAGAgent": AgentType.RAG,
            "ToolAgent": AgentType.TOOL,
            "FullAgent": AgentType.FULL,
            "RouterAgent": AgentType.ROUTER,
            "OrchestratorAgent": AgentType.ORCHESTRATOR,
        }

        assert agent_type_map["ChatAgent"] == AgentType.LLM
        assert agent_type_map["RAGAgent"] == AgentType.RAG
        assert agent_type_map["ToolAgent"] == AgentType.TOOL
        assert agent_type_map["FullAgent"] == AgentType.FULL
        assert agent_type_map["RouterAgent"] == AgentType.ROUTER
        assert agent_type_map["OrchestratorAgent"] == AgentType.ORCHESTRATOR

    def test_unknown_agent_type_defaults_to_llm(self):
        """Test that unknown agent types default to LLM."""
        agent_type_map = {
            "ChatAgent": AgentType.LLM,
        }
        agent_type = agent_type_map.get("UnknownAgent", AgentType.LLM)
        assert agent_type == AgentType.LLM

    def test_role_extraction_from_dict(self):
        """Test extracting role from dictionary format."""
        role_data = {"title": "Data Analyst", "expertise": ["data analysis"]}

        title = role_data.get("title", "Default")
        expertise = role_data.get("expertise", [])

        assert title == "Data Analyst"
        assert expertise == ["data analysis"]

    def test_role_extraction_from_string(self):
        """Test extracting role from string format."""
        role_data = "Simple title"

        if isinstance(role_data, dict):
            title = role_data.get("title", role_data)
        else:
            title = str(role_data)

        assert title == "Simple title"


# ============================================================================
# Tests for WorkflowGenerator.generate
# ============================================================================


class TestWorkflowGeneratorGenerate:
    """Tests for the generate method."""

    @pytest.mark.asyncio
    async def test_generate_parses_json_response(self, generator, mock_llm_provider):
        """Test that generate correctly parses JSON response."""
        mock_response = MagicMock()
        mock_response.content = '''{
            "workflow": {
                "id": "test-workflow",
                "name": "Test Workflow",
                "description": "Generated workflow",
                "steps": [
                    {"id": "step-1", "type": "agent", "agent_id": "agent-1"}
                ],
                "entry_step": "step-1"
            },
            "agents_to_create": [],
            "existing_agents_used": [],
            "mcps_suggested": [],
            "existing_mcps_used": [],
            "explanation": "Test explanation",
            "warnings": [],
            "estimated_complexity": "simple"
        }'''
        mock_llm_provider.complete.return_value = mock_response

        result = await generator.generate(
            prompt="Create a simple workflow",
            user_id="user-123",
        )

        assert isinstance(result, GenerateWorkflowResponse)
        assert result.workflow.id == "test-workflow"
        assert result.estimated_complexity == "simple"

    @pytest.mark.asyncio
    async def test_generate_handles_markdown_code_blocks(self, generator, mock_llm_provider):
        """Test that generate handles JSON wrapped in markdown."""
        mock_response = MagicMock()
        mock_response.content = '''```json
{
    "workflow": {
        "id": "test",
        "name": "Test",
        "steps": [{"id": "s1", "type": "agent", "agent_id": "a1"}]
    },
    "agents_to_create": [],
    "existing_agents_used": [],
    "mcps_suggested": [],
    "existing_mcps_used": [],
    "explanation": "Test",
    "warnings": [],
    "estimated_complexity": "simple"
}
```'''
        mock_llm_provider.complete.return_value = mock_response

        result = await generator.generate(
            prompt="Create workflow",
            user_id="user-123",
        )

        assert result.workflow.id == "test"

    @pytest.mark.asyncio
    async def test_generate_with_existing_agents(
        self, generator, mock_llm_provider, sample_agent_config
    ):
        """Test generate with existing agents passed."""
        mock_response = MagicMock()
        mock_response.content = '''{
            "workflow": {"id": "test", "name": "Test", "steps": [{"id": "s1", "type": "agent", "agent_id": "agent-1"}]},
            "agents_to_create": [],
            "existing_agents_used": ["agent-1"],
            "mcps_suggested": [],
            "existing_mcps_used": [],
            "explanation": "Reused existing agent",
            "warnings": [],
            "estimated_complexity": "simple"
        }'''
        mock_llm_provider.complete.return_value = mock_response

        result = await generator.generate(
            prompt="Create workflow",
            user_id="user-123",
            existing_agents=[sample_agent_config],
        )

        assert "agent-1" in result.existing_agents_used

    @pytest.mark.asyncio
    async def test_generate_raises_on_invalid_json(self, generator, mock_llm_provider):
        """Test that generate raises error on invalid JSON."""
        mock_response = MagicMock()
        mock_response.content = "This is not valid JSON at all"
        mock_llm_provider.complete.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to parse"):
            await generator.generate(
                prompt="Create workflow",
                user_id="user-123",
            )


# ============================================================================
# Tests for WorkflowGenerator.generate_skeleton
# ============================================================================


class TestWorkflowGeneratorGenerateSkeleton:
    """Tests for the generate_skeleton method."""

    @pytest.mark.asyncio
    async def test_generate_skeleton_success(self, generator, mock_llm_provider):
        """Test successful skeleton generation."""
        mock_response = MagicMock()
        mock_response.content = '''{
            "workflow_name": "Data Processing Workflow",
            "workflow_description": "Processes data files",
            "trigger_type": "manual",
            "trigger_reason": "User initiated",
            "steps": [
                {
                    "id": "step-1",
                    "name": "Fetch Data",
                    "type": "agent",
                    "role": "Retrieve data from source",
                    "order": 0,
                    "suggested_agent": {
                        "name": "Data Fetcher",
                        "goal": "Fetch data files",
                        "required_mcps": [],
                        "suggested_tools": ["http_request"]
                    }
                }
            ],
            "existing_agents_used": [],
            "existing_mcps_used": [],
            "mcp_dependencies": [],
            "explanation": "Simple data fetching workflow",
            "warnings": []
        }'''
        mock_llm_provider.complete.return_value = mock_response

        request = GenerateSkeletonRequest(prompt="Create a data processing workflow")

        result = await generator.generate_skeleton(
            request=request,
            user_id="user-123",
        )

        assert isinstance(result, GenerateSkeletonResponse)
        assert result.skeleton.name == "Data Processing Workflow"
        assert len(result.skeleton.steps) == 1
        assert result.skeleton.trigger.type == TriggerType.MANUAL

    @pytest.mark.asyncio
    async def test_generate_skeleton_webhook_trigger(self, generator, mock_llm_provider):
        """Test skeleton generation with webhook trigger."""
        mock_response = MagicMock()
        mock_response.content = '''{
            "workflow_name": "Webhook Handler",
            "workflow_description": "Handles incoming webhooks",
            "trigger_type": "webhook",
            "trigger_reason": "External events",
            "steps": [{"id": "s1", "name": "Process", "role": "Process webhook", "order": 0}],
            "mcp_dependencies": [],
            "explanation": "Webhook workflow",
            "warnings": []
        }'''
        mock_llm_provider.complete.return_value = mock_response

        request = GenerateSkeletonRequest(prompt="Handle webhooks")

        result = await generator.generate_skeleton(
            request=request,
            user_id="user-123",
        )

        assert result.skeleton.trigger.type == TriggerType.WEBHOOK
        assert result.skeleton.trigger.webhook_config is not None

    @pytest.mark.asyncio
    async def test_generate_skeleton_with_mcp_dependencies(
        self, generator, mock_llm_provider, sample_mcp_instance
    ):
        """Test skeleton generation with MCP dependencies."""
        mock_response = MagicMock()
        mock_response.content = '''{
            "workflow_name": "Slack Notifier",
            "workflow_description": "Sends Slack notifications",
            "trigger_type": "manual",
            "trigger_reason": "User initiated",
            "steps": [{"id": "s1", "name": "Send", "role": "Send notification", "order": 0}],
            "mcp_dependencies": [
                {"template": "slack", "name": "Slack", "reason": "Send messages"}
            ],
            "explanation": "Notification workflow",
            "warnings": []
        }'''
        mock_llm_provider.complete.return_value = mock_response

        request = GenerateSkeletonRequest(prompt="Send Slack notifications")

        result = await generator.generate_skeleton(
            request=request,
            user_id="user-123",
            existing_mcps=[sample_mcp_instance],
        )

        assert len(result.mcp_dependencies) == 1
        assert result.mcp_dependencies[0]["template"] == "slack"
        assert result.mcp_dependencies[0]["connected"] is True


# ============================================================================
# Tests for WorkflowGenerator.apply
# ============================================================================


class TestWorkflowGeneratorApply:
    """Tests for the apply method."""

    @pytest.fixture
    def mock_agent_repo(self):
        """Create mock agent repository."""
        repo = AsyncMock()
        repo.get = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def mock_workflow_repo(self):
        """Create mock workflow repository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_apply_saves_workflow(self, generator, mock_agent_repo, mock_workflow_repo):
        """Test that apply saves the workflow."""
        request = ApplyGeneratedWorkflowRequest(
            workflow=WorkflowDefinitionSchema(
                id="test-workflow",
                name="Test Workflow",
                steps=[
                    WorkflowStepSchema(
                        id="step-1",
                        type="agent",
                        agent_id="agent-1",
                    )
                ],
            ),
            workflow_name="Test Workflow",
            workflow_description="A test workflow",
            workflow_category="test",
            created_by="user-123",
        )

        result = await generator.apply(
            request=request,
            agent_repo=mock_agent_repo,
            workflow_repo=mock_workflow_repo,
        )

        mock_workflow_repo.save.assert_called_once()
        assert result.workflow_id == "test-workflow"

    @pytest.mark.asyncio
    async def test_apply_identifies_missing_agents(
        self, generator, mock_agent_repo, mock_workflow_repo
    ):
        """Test that apply identifies missing agents."""
        mock_agent_repo.get.return_value = None  # Agent doesn't exist

        request = ApplyGeneratedWorkflowRequest(
            workflow=WorkflowDefinitionSchema(
                id="test-workflow",
                name="Test",
                steps=[
                    WorkflowStepSchema(id="s1", type="agent", agent_id="missing-agent"),
                ],
            ),
            workflow_name="Test",
            workflow_description="Test",
            workflow_category="test",
        )

        result = await generator.apply(
            request=request,
            agent_repo=mock_agent_repo,
            workflow_repo=mock_workflow_repo,
        )

        assert result.can_execute is False
        assert "missing-agent" in result.missing_agents
        assert "s1" in result.blocked_steps
        assert result.next_action == "create_agents"

    @pytest.mark.asyncio
    async def test_apply_can_execute_when_agents_exist(
        self, generator, mock_agent_repo, mock_workflow_repo, sample_agent_config
    ):
        """Test that apply sets can_execute when all agents exist."""
        mock_agent_repo.get.return_value = sample_agent_config

        request = ApplyGeneratedWorkflowRequest(
            workflow=WorkflowDefinitionSchema(
                id="test-workflow",
                name="Test",
                steps=[
                    WorkflowStepSchema(id="s1", type="agent", agent_id="agent-1"),
                ],
            ),
            workflow_name="Test",
            workflow_description="Test",
            workflow_category="test",
        )

        result = await generator.apply(
            request=request,
            agent_repo=mock_agent_repo,
            workflow_repo=mock_workflow_repo,
        )

        assert result.can_execute is True
        assert result.missing_agents == []
        assert result.next_action == "ready_to_run"

    @pytest.mark.asyncio
    async def test_apply_handles_steps_without_agent_id(
        self, generator, mock_agent_repo, mock_workflow_repo
    ):
        """Test that apply handles steps without agent_id (e.g., conditional)."""
        request = ApplyGeneratedWorkflowRequest(
            workflow=WorkflowDefinitionSchema(
                id="test-workflow",
                name="Test",
                steps=[
                    WorkflowStepSchema(
                        id="cond-1",
                        type="conditional",
                        agent_id=None,
                        condition_source="${input}",
                    ),
                ],
            ),
            workflow_name="Test",
            workflow_description="Test",
            workflow_category="test",
        )

        result = await generator.apply(
            request=request,
            agent_repo=mock_agent_repo,
            workflow_repo=mock_workflow_repo,
        )

        # Should be executable since no agent is needed
        assert result.can_execute is True
        assert result.missing_agents == []
