"""Tests for Workflows API router.

Tests for all 17 workflow endpoints:
- POST /workflows (create)
- GET /workflows (list)
- GET /workflows/{workflow_id} (get)
- PUT /workflows/{workflow_id} (update)
- DELETE /workflows/{workflow_id} (delete)
- POST /workflows/{workflow_id}/copy (copy)
- POST /workflows/{workflow_id}/execute (execute)
- POST /workflows/{workflow_id}/validate (validate stored)
- POST /workflows/validate (validate definition)
- GET /workflows/{workflow_id}/executions (list executions)
- GET /workflows/executions/{execution_id} (get execution)
- GET /workflows/resources/agents (list agents)
- GET /workflows/resources/mcps (list MCPs)
- GET /workflows/resources/tools (list tools)
- POST /workflows/generate/skeleton (generate skeleton)
- POST /workflows/generate (generate workflow)
- POST /workflows/generate/apply (apply generated)
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.storage.workflow_repository import WorkflowWithMetadata, WorkflowExecution


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_workflow():
    """Create a sample workflow object using the actual dataclass."""
    return WorkflowWithMetadata(
        id="workflow-123",
        name="Test Workflow",
        description="A test workflow",
        category="test",
        tags=["test", "sample"],
        definition={
            "id": "def-123",
            "name": "Test Workflow",
            "description": "Test workflow description",
            "steps": [
                {
                    "id": "step-1",
                    "type": "agent",
                    "name": "First Step",
                    "agent_id": "test-agent-1",
                    "input": "${user_input}",
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


@pytest.fixture
def sample_execution():
    """Create a sample workflow execution object using the actual dataclass."""
    return WorkflowExecution(
        id="exec-123",
        workflow_id="workflow-123",
        temporal_workflow_id="temporal-123",
        status="completed",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_ms=1500,
        input_data={"user_input": "test"},
        output_data={"result": "success"},
        error=None,
        steps_executed=["step-1"],
        step_results={"step-1": {"output": "success"}},
        triggered_by="user-123",
    )


@pytest.fixture
def create_workflow_request():
    """Create a sample CreateWorkflowRequest payload."""
    return {
        "id": "workflow-123",
        "name": "Test Workflow",
        "description": "A test workflow",
        "category": "test",
        "tags": ["test"],
        "definition": {
            "id": "def-123",
            "name": "Test Workflow",
            "description": "Test workflow",
            "steps": [
                {
                    "id": "step-1",
                    "type": "agent",
                    "name": "First Step",
                    "agent_id": "test-agent-1",
                    "input": "${user_input}",
                }
            ],
        },
    }


# ============================================================================
# CRUD Endpoint Tests
# ============================================================================


class TestCreateWorkflow:
    """Tests for POST /workflows"""

    @pytest.mark.asyncio
    async def test_create_workflow_success(
        self, client: AsyncClient, override_workflow_repo, sample_workflow, create_workflow_request
    ):
        """Test successful workflow creation."""
        override_workflow_repo.exists.return_value = False
        override_workflow_repo.save.return_value = sample_workflow

        response = await client.post(
            "/api/v1/workflows",
            json=create_workflow_request,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "workflow-123"
        assert data["name"] == "Test Workflow"

    @pytest.mark.asyncio
    async def test_create_workflow_duplicate_id(
        self, client: AsyncClient, override_workflow_repo, create_workflow_request
    ):
        """Test creating workflow with existing ID fails."""
        override_workflow_repo.exists.return_value = True

        response = await client.post(
            "/api/v1/workflows",
            json=create_workflow_request,
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_create_workflow_invalid_definition(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test creating workflow with invalid definition (missing required fields)."""
        override_workflow_repo.exists.return_value = False

        response = await client.post(
            "/api/v1/workflows",
            json={
                "id": "workflow-123",
                "name": "Test",
                "description": "Test",
                "category": "test",
                "tags": [],
                "definition": {
                    "name": "Test",
                    # Missing required 'id' and 'steps' fields
                },
            },
        )

        # Pydantic validation rejects missing required fields with 422
        assert response.status_code == 422


class TestListWorkflows:
    """Tests for GET /workflows"""

    @pytest.mark.asyncio
    async def test_list_workflows_success(
        self, client: AsyncClient, override_workflow_repo, sample_workflow
    ):
        """Test listing workflows."""
        override_workflow_repo.list.return_value = [sample_workflow]

        response = await client.get("/api/v1/workflows")

        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert "total" in data
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_workflows_with_filters(
        self, client: AsyncClient, override_workflow_repo, sample_workflow
    ):
        """Test listing workflows with category filter."""
        override_workflow_repo.list.return_value = [sample_workflow]

        response = await client.get(
            "/api/v1/workflows",
            params={"category": "test", "is_template": False},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_workflows_empty(self, client: AsyncClient, override_workflow_repo):
        """Test listing workflows when none exist."""
        override_workflow_repo.list.return_value = []

        response = await client.get("/api/v1/workflows")

        assert response.status_code == 200
        data = response.json()
        assert data["workflows"] == []
        assert data["total"] == 0


class TestGetWorkflow:
    """Tests for GET /workflows/{workflow_id}"""

    @pytest.mark.asyncio
    async def test_get_workflow_success(
        self, client: AsyncClient, override_workflow_repo, sample_workflow
    ):
        """Test getting a workflow by ID."""
        override_workflow_repo.get.return_value = sample_workflow

        response = await client.get("/api/v1/workflows/workflow-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "workflow-123"
        assert data["name"] == "Test Workflow"

    @pytest.mark.asyncio
    async def test_get_workflow_not_found(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test getting non-existent workflow."""
        override_workflow_repo.get.return_value = None

        response = await client.get("/api/v1/workflows/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["message"]


class TestUpdateWorkflow:
    """Tests for PUT /workflows/{workflow_id}"""

    @pytest.mark.asyncio
    async def test_update_workflow_success(
        self, client: AsyncClient, override_workflow_repo, sample_workflow
    ):
        """Test updating a workflow."""
        override_workflow_repo.get.return_value = sample_workflow
        updated_workflow = sample_workflow
        updated_workflow.name = "Updated Workflow"
        override_workflow_repo.save.return_value = updated_workflow

        response = await client.put(
            "/api/v1/workflows/workflow-123",
            json={"name": "Updated Workflow"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_workflow_not_found(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test updating non-existent workflow."""
        override_workflow_repo.get.return_value = None

        response = await client.put(
            "/api/v1/workflows/nonexistent",
            json={"name": "Updated"},
        )

        assert response.status_code == 404


class TestDeleteWorkflow:
    """Tests for DELETE /workflows/{workflow_id}"""

    @pytest.mark.asyncio
    async def test_delete_workflow_success(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test deleting a workflow."""
        override_workflow_repo.delete.return_value = True

        response = await client.delete("/api/v1/workflows/workflow-123")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_workflow_not_found(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test deleting non-existent workflow."""
        override_workflow_repo.delete.return_value = False

        response = await client.delete("/api/v1/workflows/nonexistent")

        assert response.status_code == 404


class TestCopyWorkflow:
    """Tests for POST /workflows/{workflow_id}/copy"""

    @pytest.mark.asyncio
    async def test_copy_workflow_success(
        self, client: AsyncClient, override_workflow_repo, sample_workflow
    ):
        """Test copying a workflow."""
        override_workflow_repo.exists.return_value = False
        override_workflow_repo.copy.return_value = "new-workflow-id"
        copied_workflow = sample_workflow
        copied_workflow.id = "new-workflow-id"
        override_workflow_repo.get.return_value = copied_workflow

        response = await client.post(
            "/api/v1/workflows/workflow-123/copy",
            json={
                "new_id": "new-workflow-id",
                "new_name": "Copied Workflow",
            },
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_copy_workflow_duplicate_target(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test copying to existing ID fails."""
        override_workflow_repo.exists.return_value = True

        response = await client.post(
            "/api/v1/workflows/workflow-123/copy",
            json={
                "new_id": "existing-id",
                "new_name": "Copy",
            },
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_copy_workflow_source_not_found(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test copying non-existent workflow."""
        override_workflow_repo.exists.return_value = False
        override_workflow_repo.copy.return_value = None

        response = await client.post(
            "/api/v1/workflows/nonexistent/copy",
            json={
                "new_id": "new-id",
                "new_name": "Copy",
            },
        )

        assert response.status_code == 404


# ============================================================================
# Execution Tests
# ============================================================================


class TestExecuteWorkflow:
    """Tests for POST /workflows/{workflow_id}/execute"""

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test executing non-existent workflow."""
        override_workflow_repo.exists.return_value = False

        response = await client.post(
            "/api/v1/workflows/nonexistent/execute",
            json={"user_input": "test"},
        )

        assert response.status_code == 404


# ============================================================================
# Validation Tests
# ============================================================================


class TestValidateStoredWorkflow:
    """Tests for POST /workflows/{workflow_id}/validate"""

    @pytest.mark.asyncio
    async def test_validate_stored_workflow_not_found(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test validating non-existent workflow."""
        override_workflow_repo.get.return_value = None

        response = await client.post("/api/v1/workflows/nonexistent/validate")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validate_stored_workflow_success(
        self, client: AsyncClient, override_workflow_repo, override_agent_repo, sample_workflow
    ):
        """Test validating stored workflow."""
        override_workflow_repo.get.return_value = sample_workflow

        with patch("src.workflows.executor.validate_workflow_with_resources") as mock_validate:
            mock_validate.return_value = (True, [], [], [])

            response = await client.post("/api/v1/workflows/workflow-123/validate")

            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert data["errors"] == []


class TestValidateDefinition:
    """Tests for POST /workflows/validate"""

    @pytest.mark.asyncio
    async def test_validate_definition_success(
        self, client: AsyncClient, override_agent_repo
    ):
        """Test validating workflow definition."""
        with patch("src.workflows.executor.validate_workflow_with_resources") as mock_validate:
            mock_validate.return_value = (True, [], [], [])

            response = await client.post(
                "/api/v1/workflows/validate",
                json={
                    "definition": {
                        "id": "def-123",
                        "name": "Test",
                        "description": "Test",
                        "steps": [
                            {
                                "id": "step-1",
                                "type": "agent",
                                "name": "Step 1",
                                "agent_id": "agent-1",
                                "input": "${input}",
                            }
                        ],
                    }
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True


# ============================================================================
# Execution History Tests
# ============================================================================


class TestListExecutions:
    """Tests for GET /workflows/{workflow_id}/executions"""

    @pytest.mark.asyncio
    async def test_list_executions_success(
        self, client: AsyncClient, override_workflow_repo, sample_execution
    ):
        """Test listing workflow executions."""
        override_workflow_repo.exists.return_value = True
        override_workflow_repo.list_executions.return_value = [sample_execution]

        response = await client.get("/api/v1/workflows/workflow-123/executions")

        assert response.status_code == 200
        data = response.json()
        assert "executions" in data
        assert "total" in data
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_executions_workflow_not_found(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test listing executions for non-existent workflow."""
        override_workflow_repo.exists.return_value = False

        response = await client.get("/api/v1/workflows/nonexistent/executions")

        assert response.status_code == 404


class TestGetExecution:
    """Tests for GET /workflows/executions/{execution_id}"""

    @pytest.mark.asyncio
    async def test_get_execution_success(
        self, client: AsyncClient, override_workflow_repo, sample_execution
    ):
        """Test getting execution details."""
        override_workflow_repo.get_execution.return_value = sample_execution

        response = await client.get("/api/v1/workflows/executions/exec-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "exec-123"
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_execution_not_found(
        self, client: AsyncClient, override_workflow_repo
    ):
        """Test getting non-existent execution."""
        override_workflow_repo.get_execution.return_value = None

        response = await client.get("/api/v1/workflows/executions/nonexistent")

        assert response.status_code == 404


# ============================================================================
# Resource Discovery Tests
# ============================================================================


class TestListAvailableAgents:
    """Tests for GET /workflows/resources/agents"""

    @pytest.mark.asyncio
    async def test_list_available_agents_success(
        self, client: AsyncClient, override_agent_repo, sample_agent_config
    ):
        """Test listing available agents."""
        from src.models.agent_config import AgentConfig
        from src.models.enums import AgentType
        from src.models.persona import AgentGoal, AgentInstructions, AgentRole

        agent = AgentConfig(
            id="agent-1",
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.TOOL,
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
        )
        override_agent_repo.list.return_value = [agent]

        response = await client.get("/api/v1/workflows/resources/agents")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_available_agents_empty(
        self, client: AsyncClient, override_agent_repo
    ):
        """Test listing available agents when none exist."""
        override_agent_repo.list.return_value = []

        response = await client.get("/api/v1/workflows/resources/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["agents"] == []
        assert data["total"] == 0


class TestListAvailableMCPs:
    """Tests for GET /workflows/resources/mcps"""

    @pytest.mark.asyncio
    async def test_list_available_mcps_success(
        self, client: AsyncClient, override_mcp_manager, mock_mcp_repository
    ):
        """Test listing available MCP servers."""
        # Create mock MCP server
        mock_server = MagicMock(
            id="mcp-1",
            name="Test MCP",
            template="test-template",
            status="connected",
        )
        mock_mcp_repository.list_all.return_value = [mock_server]

        with patch("src.api.dependencies.get_mcp_repository", return_value=mock_mcp_repository):
            response = await client.get("/api/v1/workflows/resources/mcps")

            assert response.status_code == 200
            data = response.json()
            assert "mcp_servers" in data
            assert "total" in data


class TestListAvailableTools:
    """Tests for GET /workflows/resources/tools"""

    @pytest.mark.asyncio
    async def test_list_available_tools_success(
        self, client: AsyncClient, override_mcp_manager
    ):
        """Test listing available tools."""
        with patch("src.tools.get_registry") as mock_registry:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_tool.description = "A test tool"
            mock_registry.return_value.tools = {"test_tool": mock_tool}

            response = await client.get("/api/v1/workflows/resources/tools")

            assert response.status_code == 200
            data = response.json()
            assert "tools" in data
            assert "total" in data


# ============================================================================
# AI Generation Tests
# ============================================================================


class TestGenerateSkeleton:
    """Tests for POST /workflows/generate/skeleton"""

    @pytest.mark.asyncio
    async def test_generate_skeleton_success(
        self, client: AsyncClient, override_agent_repo, mock_mcp_repository
    ):
        """Test generating workflow skeleton."""
        from src.api.schemas.workflows import (
            GenerateSkeletonResponse,
            WorkflowSkeleton,
            WorkflowTrigger,
            TriggerType,
            SkeletonStep,
        )

        override_agent_repo.list.return_value = []

        # Create a proper response matching the schema
        mock_response = GenerateSkeletonResponse(
            skeleton=WorkflowSkeleton(
                name="Generated Workflow",
                description="AI generated workflow",
                trigger=WorkflowTrigger(type=TriggerType.MANUAL),
                steps=[
                    SkeletonStep(id="step-1", name="Step 1", role="Process data", order=0)
                ],
            ),
            step_suggestions=[],
            mcp_dependencies=[],
            explanation="Test explanation",
            warnings=[],
        )

        with patch("src.api.dependencies.get_mcp_repository", return_value=mock_mcp_repository):
            with patch("src.workflows.generator.WorkflowGenerator") as mock_generator:
                mock_generator_instance = MagicMock()
                mock_generator_instance.generate_skeleton = AsyncMock(return_value=mock_response)
                mock_generator.return_value = mock_generator_instance

                response = await client.post(
                    "/api/v1/workflows/generate/skeleton",
                    json={
                        "prompt": "Create a comprehensive data analysis workflow for processing CSV files",
                    },
                )

                assert response.status_code == 200


class TestGenerateWorkflow:
    """Tests for POST /workflows/generate"""

    @pytest.mark.asyncio
    async def test_generate_workflow_success(
        self, client: AsyncClient, override_agent_repo, mock_mcp_repository
    ):
        """Test generating workflow from prompt."""
        from src.api.schemas.workflows import (
            GenerateWorkflowResponse,
            WorkflowDefinitionSchema,
            WorkflowStepSchema,
        )

        override_agent_repo.list.return_value = []

        # Create a proper response matching the schema
        mock_response = GenerateWorkflowResponse(
            workflow=WorkflowDefinitionSchema(
                id="gen-workflow",
                name="Generated Workflow",
                description="AI generated workflow",
                steps=[
                    WorkflowStepSchema(
                        id="step-1",
                        type="agent",
                        name="Step 1",
                        agent_id="agent-1",
                    )
                ],
            ),
            agents_to_create=[],
            existing_agents_used=[],
            mcps_suggested=[],
            existing_mcps_used=[],
            explanation="Generated workflow for testing",
            warnings=[],
            estimated_complexity="simple",
        )

        with patch("src.api.dependencies.get_mcp_repository", return_value=mock_mcp_repository):
            with patch("src.workflows.generator.WorkflowGenerator") as mock_generator:
                mock_generator_instance = MagicMock()
                mock_generator_instance.generate = AsyncMock(return_value=mock_response)
                mock_generator.return_value = mock_generator_instance

                response = await client.post(
                    "/api/v1/workflows/generate",
                    json={
                        "prompt": "Create a comprehensive data analysis workflow for processing CSV files",
                        "preferred_complexity": "simple",
                    },
                )

                assert response.status_code == 200


class TestApplyGeneratedWorkflow:
    """Tests for POST /workflows/generate/apply"""

    @pytest.mark.asyncio
    async def test_apply_generated_workflow_success(
        self, client: AsyncClient, override_agent_repo, override_workflow_repo
    ):
        """Test applying generated workflow."""
        from src.api.schemas.workflows import ApplyGeneratedWorkflowResponse

        # Create a proper response matching the schema
        mock_response = ApplyGeneratedWorkflowResponse(
            workflow_id="applied-workflow",
            blocked_steps=[],
            missing_agents=[],
            can_execute=True,
            next_action="ready_to_run",
        )

        with patch("src.workflows.generator.WorkflowGenerator") as mock_generator:
            mock_generator_instance = MagicMock()
            mock_generator_instance.apply = AsyncMock(return_value=mock_response)
            mock_generator.return_value = mock_generator_instance

            # Request must match ApplyGeneratedWorkflowRequest schema
            response = await client.post(
                "/api/v1/workflows/generate/apply",
                json={
                    "workflow": {
                        "id": "gen-workflow",
                        "name": "Applied Workflow",
                        "description": "Test workflow",
                        "steps": [
                            {
                                "id": "step-1",
                                "type": "agent",
                                "name": "Step 1",
                                "agent_id": "agent-1",
                            }
                        ],
                    },
                    "workflow_name": "Applied Workflow",
                    "workflow_description": "Test workflow description",
                    "workflow_category": "ai-generated",
                },
            )

            assert response.status_code == 200


# ============================================================================
# Additional Fixture for Agent Config
# ============================================================================


@pytest.fixture
def sample_agent_config():
    """Create a sample agent config for workflow resource tests."""
    from src.models.agent_config import AgentConfig
    from src.models.enums import AgentType
    from src.models.persona import AgentGoal, AgentInstructions, AgentRole

    return AgentConfig(
        id="test-agent-1",
        name="Test Agent",
        description="A test agent",
        agent_type=AgentType.TOOL,
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
    )
