"""Tests for Agents API router.

Tests for all 6 agent endpoints:
- POST /agents/generate (AI generate)
- POST /agents (create)
- GET /agents (list)
- GET /agents/{agent_id} (get)
- PUT /agents/{agent_id} (update)
- DELETE /agents/{agent_id} (delete)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from src.models.agent_config import AgentConfig
from src.models.enums import AgentType
from src.models.persona import AgentGoal, AgentInstructions, AgentRole


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_agent_config():
    """Create a sample AgentConfig for testing."""
    return AgentConfig(
        id="test-agent-1",
        name="Test Agent",
        description="A test agent for unit testing",
        agent_type=AgentType.TOOL,
        role=AgentRole(
            title="Test Assistant",
            expertise=["testing", "automation"],
            personality=["helpful", "precise"],
            communication_style="professional",
        ),
        goal=AgentGoal(
            objective="Help with testing",
            success_indicators=["Complete tests successfully"],
            constraints=[],
        ),
        instructions=AgentInstructions(
            steps=["Analyze the request", "Provide response"],
            rules=["Be helpful", "Be accurate"],
            prohibited=[],
            output_format=None,
        ),
        examples=[],
        tools=[],
    )


@pytest.fixture
def create_agent_request():
    """Create a sample CreateAgentRequest payload."""
    return {
        "id": "test-agent-1",
        "name": "Test Agent",
        "description": "A test agent",
        "agent_type": "ToolAgent",
        "role": {
            "title": "Test Assistant",
            "expertise": ["testing"],
            "personality": ["helpful"],
            "communication_style": "professional",
        },
        "goal": {
            "objective": "Help with testing",
            "success_criteria": ["Tests pass"],
            "constraints": [],
        },
        "instructions": {
            "steps": ["Step 1", "Step 2"],
            "rules": ["Be helpful"],
            "prohibited": [],
            "output_format": None,
        },
        "examples": [],
        "tools": [],
        "safety": {
            "level": "standard",
            "blocked_topics": [],
            "blocked_patterns": [],
        },
    }


# ============================================================================
# Generate Endpoint Tests
# ============================================================================


class TestGenerateAgent:
    """Tests for POST /agents/generate"""

    @pytest.mark.asyncio
    async def test_generate_agent_success(self, client: AsyncClient, patch_llm_client):
        """Test successful agent generation."""
        # Mock LLM response with valid JSON
        mock_response = MagicMock()
        mock_response.content = '''{
            "description": "A helpful assistant",
            "role": {
                "title": "Assistant",
                "expertise": ["general"],
                "personality": ["helpful"],
                "communication_style": "friendly"
            },
            "goal": {
                "objective": "Help users",
                "success_criteria": ["User satisfied"],
                "constraints": []
            },
            "instructions": {
                "steps": ["Understand", "Respond"],
                "rules": ["Be helpful"],
                "prohibited": [],
                "output_format": null
            },
            "examples": [],
            "suggested_agent_type": "ToolAgent"
        }'''
        patch_llm_client.complete.return_value = mock_response

        response = await client.post(
            "/api/v1/agents/generate",
            json={
                "name": "My Assistant",
                "context": "A helpful chatbot",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "description" in data
        assert "role" in data
        assert "goal" in data
        assert "instructions" in data
        assert data["suggested_agent_type"] == "ToolAgent"

    @pytest.mark.asyncio
    async def test_generate_agent_with_markdown_response(
        self, client: AsyncClient, patch_llm_client
    ):
        """Test agent generation when LLM returns markdown-wrapped JSON."""
        mock_response = MagicMock()
        mock_response.content = '''```json
{
    "description": "A data analyst",
    "role": {"title": "Analyst", "expertise": [], "personality": [], "communication_style": "analytical"},
    "goal": {"objective": "Analyze data", "success_criteria": [], "constraints": []},
    "instructions": {"steps": [], "rules": [], "prohibited": [], "output_format": null},
    "examples": [],
    "suggested_agent_type": "RAGAgent"
}
```'''
        patch_llm_client.complete.return_value = mock_response

        response = await client.post(
            "/api/v1/agents/generate",
            json={"name": "Data Analyst"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["suggested_agent_type"] == "RAGAgent"

    @pytest.mark.asyncio
    async def test_generate_agent_llm_error(self, client: AsyncClient, patch_llm_client):
        """Test agent generation when LLM fails."""
        patch_llm_client.complete.side_effect = Exception("LLM API error")

        response = await client.post(
            "/api/v1/agents/generate",
            json={"name": "Test Agent"},
        )

        assert response.status_code == 500
        assert "Failed to generate" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_generate_agent_invalid_json_response(
        self, client: AsyncClient, patch_llm_client
    ):
        """Test agent generation when LLM returns invalid JSON."""
        mock_response = MagicMock()
        mock_response.content = "This is not valid JSON"
        patch_llm_client.complete.return_value = mock_response

        response = await client.post(
            "/api/v1/agents/generate",
            json={"name": "Test Agent"},
        )

        assert response.status_code == 500
        assert "Failed to parse" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_generate_agent_legacy_type_mapping(
        self, client: AsyncClient, patch_llm_client
    ):
        """Test that legacy agent types are mapped correctly."""
        mock_response = MagicMock()
        mock_response.content = '''{
            "description": "Test",
            "role": {"title": "Test", "expertise": [], "personality": [], "communication_style": ""},
            "goal": {"objective": "", "success_criteria": [], "constraints": []},
            "instructions": {"steps": [], "rules": [], "prohibited": [], "output_format": null},
            "examples": [],
            "suggested_agent_type": "ChatAgent"
        }'''
        patch_llm_client.complete.return_value = mock_response

        response = await client.post(
            "/api/v1/agents/generate",
            json={"name": "Chat Agent"},
        )

        assert response.status_code == 200
        # ChatAgent should be mapped to LLMAgent
        assert response.json()["suggested_agent_type"] == "LLMAgent"


# ============================================================================
# Create Endpoint Tests
# ============================================================================


class TestCreateAgent:
    """Tests for POST /agents"""

    @pytest.mark.asyncio
    async def test_create_agent_success(
        self, client: AsyncClient, override_agent_repo, create_agent_request
    ):
        """Test successful agent creation."""
        override_agent_repo.exists.return_value = False
        override_agent_repo.save.return_value = None

        response = await client.post(
            "/api/v1/agents",
            json=create_agent_request,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test-agent-1"
        assert data["name"] == "Test Agent"
        assert data["agent_type"] == "ToolAgent"

    @pytest.mark.asyncio
    async def test_create_agent_duplicate_id(
        self, client: AsyncClient, override_agent_repo, create_agent_request
    ):
        """Test creating agent with existing ID fails."""
        override_agent_repo.exists.return_value = True

        response = await client.post(
            "/api/v1/agents",
            json=create_agent_request,
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_create_agent_missing_fields(self, client: AsyncClient):
        """Test creating agent with missing required fields."""
        response = await client.post(
            "/api/v1/agents",
            json={
                "id": "test-agent",
                "name": "Test Agent",
                # Missing required fields
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_agent_invalid_type(
        self, client: AsyncClient, create_agent_request
    ):
        """Test creating agent with invalid agent type."""
        create_agent_request["agent_type"] = "InvalidType"

        response = await client.post(
            "/api/v1/agents",
            json=create_agent_request,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_agent_with_tools(
        self, client: AsyncClient, override_agent_repo, create_agent_request
    ):
        """Test creating agent with tool configurations."""
        override_agent_repo.exists.return_value = False
        override_agent_repo.save.return_value = None

        create_agent_request["tools"] = [
            {
                "tool_id": "web_search",
                "enabled": True,
                "requires_confirmation": False,
            }
        ]

        response = await client.post(
            "/api/v1/agents",
            json=create_agent_request,
        )

        assert response.status_code == 201


# ============================================================================
# List Endpoint Tests
# ============================================================================


class TestListAgents:
    """Tests for GET /agents"""

    @pytest.mark.asyncio
    async def test_list_agents_success(
        self, client: AsyncClient, override_agent_repo, sample_agent_config
    ):
        """Test listing agents."""
        override_agent_repo.list.return_value = [sample_agent_config]

        response = await client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["agents"]) == 1
        assert data["agents"][0]["id"] == "test-agent-1"

    @pytest.mark.asyncio
    async def test_list_agents_empty(self, client: AsyncClient, override_agent_repo):
        """Test listing agents when none exist."""
        override_agent_repo.list.return_value = []

        response = await client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["agents"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_agents_multiple(
        self, client: AsyncClient, override_agent_repo, sample_agent_config
    ):
        """Test listing multiple agents."""
        agent2 = AgentConfig(
            id="test-agent-2",
            name="Another Agent",
            description="Another test agent",
            agent_type=AgentType.LLM,
            role=sample_agent_config.role,
            goal=sample_agent_config.goal,
            instructions=sample_agent_config.instructions,
        )
        override_agent_repo.list.return_value = [sample_agent_config, agent2]

        response = await client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


# ============================================================================
# Get Endpoint Tests
# ============================================================================


class TestGetAgent:
    """Tests for GET /agents/{agent_id}"""

    @pytest.mark.asyncio
    async def test_get_agent_success(
        self, client: AsyncClient, override_agent_repo, sample_agent_config
    ):
        """Test getting an agent by ID."""
        override_agent_repo.get.return_value = sample_agent_config

        response = await client.get("/api/v1/agents/test-agent-1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-agent-1"
        assert data["name"] == "Test Agent"
        assert "role" in data
        assert "goal" in data
        assert "instructions" in data

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, client: AsyncClient, override_agent_repo):
        """Test getting non-existent agent."""
        override_agent_repo.get.return_value = None

        response = await client.get("/api/v1/agents/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_get_agent_with_full_config(
        self, client: AsyncClient, override_agent_repo, sample_agent_config
    ):
        """Test getting agent with all optional fields."""
        from src.models.llm_config import LLMConfig
        from src.models.knowledge_config import KnowledgeBaseConfig

        sample_agent_config.llm_config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1024,
        )
        sample_agent_config.knowledge_base = KnowledgeBaseConfig(
            collection_name="test-kb",
            embedding_model="text-embedding-3-small",
            top_k=5,
        )
        override_agent_repo.get.return_value = sample_agent_config

        response = await client.get("/api/v1/agents/test-agent-1")

        assert response.status_code == 200
        data = response.json()
        assert data["llm_config"] is not None
        assert data["llm_config"]["provider"] == "openai"
        assert data["knowledge_base"] is not None


# ============================================================================
# Update Endpoint Tests
# ============================================================================


class TestUpdateAgent:
    """Tests for PUT /agents/{agent_id}"""

    @pytest.mark.asyncio
    async def test_update_agent_success(
        self, client: AsyncClient, override_agent_repo, sample_agent_config, create_agent_request
    ):
        """Test updating an agent."""
        override_agent_repo.get.return_value = sample_agent_config
        override_agent_repo.save.return_value = None

        create_agent_request["name"] = "Updated Agent"

        response = await client.put(
            "/api/v1/agents/test-agent-1",
            json=create_agent_request,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Agent"

    @pytest.mark.asyncio
    async def test_update_agent_not_found(
        self, client: AsyncClient, override_agent_repo, create_agent_request
    ):
        """Test updating non-existent agent."""
        override_agent_repo.get.return_value = None

        response = await client.put(
            "/api/v1/agents/nonexistent",
            json=create_agent_request,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_agent_id_mismatch_corrected(
        self, client: AsyncClient, override_agent_repo, sample_agent_config, create_agent_request
    ):
        """Test that mismatched ID in body is corrected to path ID."""
        override_agent_repo.get.return_value = sample_agent_config
        override_agent_repo.save.return_value = None

        # ID in body doesn't match path
        create_agent_request["id"] = "different-id"

        response = await client.put(
            "/api/v1/agents/test-agent-1",
            json=create_agent_request,
        )

        # Should succeed, using path ID
        assert response.status_code == 200
        assert response.json()["id"] == "test-agent-1"


# ============================================================================
# Delete Endpoint Tests
# ============================================================================


class TestDeleteAgent:
    """Tests for DELETE /agents/{agent_id}"""

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, client: AsyncClient, override_agent_repo):
        """Test deleting an agent."""
        override_agent_repo.delete.return_value = True

        response = await client.delete("/api/v1/agents/test-agent-1")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, client: AsyncClient, override_agent_repo):
        """Test deleting non-existent agent."""
        override_agent_repo.delete.return_value = False

        response = await client.delete("/api/v1/agents/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["message"]
