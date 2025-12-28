"""Tests for storage models."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.storage.models import (
    UserModel,
    OrganizationModel,
    AgentModel,
    SkillModel,
    WorkflowModel,
    DEFAULT_ORG_ID,
)


class TestUserModel:
    """Tests for UserModel."""

    def test_create_user(self):
        """Test creating a user model."""
        user = UserModel(
            id=str(uuid4()),
            email="test@example.com",
            password_hash="hashed_password",
            display_name="Test User",
            org_id=DEFAULT_ORG_ID,
        )

        assert user.email == "test@example.com"
        assert user.display_name == "Test User"

    def test_superuser_flag(self):
        """Test superuser flag."""
        user = UserModel(
            id=str(uuid4()),
            email="admin@example.com",
            password_hash="hash",
            display_name="Admin",
            org_id=DEFAULT_ORG_ID,
            is_superuser=True,
        )

        assert user.is_superuser is True


class TestOrganizationModel:
    """Tests for OrganizationModel."""

    def test_create_organization(self):
        """Test creating an organization."""
        org = OrganizationModel(
            id=str(uuid4()),
            name="Test Org",
            slug="test-org",
        )

        assert org.name == "Test Org"
        assert org.slug == "test-org"

    def test_default_organization(self):
        """Test default organization ID constant."""
        assert DEFAULT_ORG_ID is not None
        assert isinstance(DEFAULT_ORG_ID, str)


class TestAgentModel:
    """Tests for AgentModel."""

    def test_create_agent(self):
        """Test creating an agent model."""
        user_id = str(uuid4())
        agent = AgentModel(
            id="agent-123",
            user_id=user_id,
            name="Test Agent",
            description="A test agent",
            agent_type="ToolAgent",
            config_json={
                "role": {"title": "Test"},
                "goal": {"objective": "Testing"},
            },
        )

        assert agent.id == "agent-123"
        assert agent.name == "Test Agent"
        assert agent.agent_type == "ToolAgent"
        assert agent.user_id == user_id

    def test_agent_config_stored_as_dict(self):
        """Test that agent config is stored as dict."""
        config = {
            "role": {"title": "Assistant"},
            "tools": ["tool1", "tool2"],
        }

        agent = AgentModel(
            id="agent-1",
            user_id=str(uuid4()),
            name="Agent",
            description="Test",
            agent_type="ToolAgent",
            config_json=config,
        )

        assert agent.config_json == config
        assert isinstance(agent.config_json, dict)


class TestSkillModel:
    """Tests for SkillModel."""

    def test_create_skill(self):
        """Test creating a skill model."""
        skill = SkillModel(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Test Skill",
            description="A test skill",
            category="domain_expertise",
            definition_json={
                "metadata": {"name": "Test"},
                "capability": {},
            },
        )

        assert skill.name == "Test Skill"
        assert skill.category == "domain_expertise"

    def test_skill_version_explicit(self):
        """Test skill version can be set explicitly."""
        skill = SkillModel(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Skill",
            description="Test",
            category="custom",
            definition_json={},
            version=1,
        )

        assert skill.version == 1

    def test_skill_tags(self):
        """Test skill tags."""
        skill = SkillModel(
            id=str(uuid4()),
            user_id=str(uuid4()),
            name="Skill",
            description="Test",
            category="coding",
            definition_json={},
            tags=["python", "testing"],
        )

        assert skill.tags == ["python", "testing"]


class TestWorkflowModel:
    """Tests for WorkflowModel."""

    def test_create_workflow(self):
        """Test creating a workflow model."""
        workflow = WorkflowModel(
            id="workflow-123",
            user_id=str(uuid4()),
            name="Test Workflow",
            description="A test workflow",
            definition_json={
                "id": "workflow-123",
                "steps": [],
            },
        )

        assert workflow.id == "workflow-123"
        assert workflow.name == "Test Workflow"

    def test_workflow_definition_stored(self):
        """Test workflow definition is stored correctly."""
        definition = {
            "id": "wf-1",
            "steps": [
                {"id": "step-1", "type": "agent", "agent_id": "agent-1"}
            ],
        }

        workflow = WorkflowModel(
            id="wf-1",
            user_id=str(uuid4()),
            name="Workflow",
            description="Test",
            definition_json=definition,
        )

        assert workflow.definition_json == definition

    def test_workflow_category_explicit(self):
        """Test workflow category can be set explicitly."""
        workflow = WorkflowModel(
            id="wf-1",
            user_id=str(uuid4()),
            name="Workflow",
            description="Test",
            definition_json={},
            category="ai-generated",
        )

        assert workflow.category == "ai-generated"
