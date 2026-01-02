"""Root test configuration with core fixtures for the entire test suite.

This module provides:
- Async database session fixtures (SQLite in-memory)
- FastAPI test client fixtures
- Mock fixtures for external services (LLM, Qdrant, Redis, MinIO, Vault)
- Test data factories for agents, skills, workflows
- Authentication fixtures for user/superuser contexts
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.storage.models import Base, DEFAULT_ORG_ID, OrganizationModel, UserModel
from src.auth.schemas import UserMe
from src.auth.password import hash_password


# ============================================================================
# SQLite Compatibility for PostgreSQL-specific columns
# ============================================================================


def _replace_pg_types_for_sqlite(metadata):
    """Replace PostgreSQL-specific column types for SQLite compatibility.

    Converts:
    - JSONB -> JSON
    - ARRAY -> JSON (stores as JSON array)
    """
    for table in metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()
            elif isinstance(column.type, ARRAY):
                column.type = JSON()


# ============================================================================
# Event Loop Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Async Database Session (SQLite in-memory)
# ============================================================================


@pytest.fixture
async def async_engine():
    """Create an async SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Replace PostgreSQL-specific types for SQLite compatibility
    _replace_pg_types_for_sqlite(Base.metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async session for testing with seeded data."""
    async_session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_factory() as session:
        # Seed default organization
        org = OrganizationModel(
            id=DEFAULT_ORG_ID,
            name="Test Organization",
            slug="test-org",
        )
        session.add(org)
        await session.commit()

        yield session
        await session.rollback()


# ============================================================================
# Mock User Fixtures
# ============================================================================


@pytest.fixture
def mock_user_id() -> str:
    """Generate a consistent test user ID."""
    return str(uuid4())


@pytest.fixture
def mock_org_id() -> str:
    """Use the default organization ID."""
    return DEFAULT_ORG_ID


@pytest.fixture
def mock_current_user(mock_user_id: str, mock_org_id: str) -> UserMe:
    """Create a mock authenticated user."""
    return UserMe(
        id=mock_user_id,
        email="testuser@example.com",
        display_name="Test User",
        is_superuser=False,
        org_id=mock_org_id,
    )


@pytest.fixture
def mock_superuser(mock_user_id: str, mock_org_id: str) -> UserMe:
    """Create a mock superuser."""
    return UserMe(
        id=mock_user_id,
        email="admin@example.com",
        display_name="Admin User",
        is_superuser=True,
        org_id=mock_org_id,
    )


@pytest.fixture
async def test_user(async_session: AsyncSession, mock_org_id: str) -> UserModel:
    """Create a real test user in the database."""
    user = UserModel(
        id=str(uuid4()),
        email="testuser@example.com",
        password_hash=hash_password("TestPassword1!"),
        display_name="Test User",
        org_id=mock_org_id,
        is_active=True,
        is_superuser=False,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def test_superuser(async_session: AsyncSession, mock_org_id: str) -> UserModel:
    """Create a real superuser in the database."""
    user = UserModel(
        id=str(uuid4()),
        email="admin@example.com",
        password_hash=hash_password("AdminPassword1!"),
        display_name="Admin User",
        org_id=mock_org_id,
        is_active=True,
        is_superuser=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================


@pytest.fixture
def app(async_session: AsyncSession, mock_current_user: UserMe) -> FastAPI:
    """Create a FastAPI app with overridden dependencies for testing."""
    from src.api.app import app as main_app
    from src.storage.database import get_session
    from src.auth.dependencies import get_current_user, get_current_superuser

    # Override database session
    async def override_get_session():
        yield async_session

    # Override auth dependencies
    async def override_get_current_user():
        return mock_current_user

    async def override_get_current_superuser():
        return mock_current_user

    main_app.dependency_overrides[get_session] = override_get_session
    main_app.dependency_overrides[get_current_user] = override_get_current_user
    main_app.dependency_overrides[get_current_superuser] = override_get_current_superuser

    yield main_app

    # Clean up overrides
    main_app.dependency_overrides.clear()


@pytest.fixture
def app_no_auth(async_session: AsyncSession) -> FastAPI:
    """Create a FastAPI app without auth overrides (for testing auth endpoints)."""
    from src.api.app import app as main_app
    from src.storage.database import get_session

    async def override_get_session():
        yield async_session

    main_app.dependency_overrides[get_session] = override_get_session

    yield main_app

    main_app.dependency_overrides.clear()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing with auth."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def client_no_auth(app_no_auth: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client without auth for testing auth endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app_no_auth),
        base_url="http://test",
    ) as client:
        yield client


# ============================================================================
# LLM Provider Mocks
# ============================================================================


@pytest.fixture
def mock_openai_response() -> Dict[str, Any]:
    """Standard mock response for OpenAI API calls."""
    return {
        "content": "This is a test response from the mock OpenAI API.",
        "model": "gpt-4o-mini",
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "total_tokens": 70,
        },
        "finish_reason": "stop",
        "tool_calls": [],
    }


@pytest.fixture
def mock_anthropic_response() -> Dict[str, Any]:
    """Standard mock response for Anthropic API calls."""
    return {
        "content": "This is a test response from the mock Anthropic API.",
        "model": "claude-3-sonnet-20240229",
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 25,
            "total_tokens": 75,
        },
        "finish_reason": "end_turn",
        "tool_calls": [],
    }


@pytest.fixture
def mock_llm_provider(mock_openai_response: Dict[str, Any]):
    """Create a mock LLM provider."""
    mock_provider = AsyncMock()

    # Create a proper response object
    mock_response = MagicMock()
    mock_response.content = mock_openai_response["content"]
    mock_response.model = mock_openai_response["model"]
    mock_response.usage = mock_openai_response["usage"]
    mock_response.finish_reason = mock_openai_response["finish_reason"]
    mock_response.tool_calls = []

    mock_provider.complete.return_value = mock_response
    return mock_provider


@pytest.fixture
def patch_llm_client(mock_llm_provider):
    """Patch LLMClient.get_provider to return mock provider."""
    with patch("src.llm.client.LLMClient.get_provider", return_value=mock_llm_provider):
        yield mock_llm_provider


# ============================================================================
# Temporal Client Mocks
# ============================================================================


@pytest.fixture
def mock_temporal_client():
    """Create a mock Temporal client."""
    mock_client = AsyncMock()
    mock_client.execute_workflow = AsyncMock()
    mock_client.get_workflow_handle = MagicMock()
    return mock_client


@pytest.fixture
def patch_temporal_client(mock_temporal_client):
    """Patch get_temporal_client to return mock client."""
    with patch(
        "src.api.routers.workflow.get_temporal_client",
        return_value=mock_temporal_client,
    ):
        yield mock_temporal_client


# ============================================================================
# External Service Mocks
# ============================================================================


@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client."""
    mock_client = AsyncMock()
    mock_client.get_collections = AsyncMock(return_value=MagicMock(collections=[]))
    mock_client.create_collection = AsyncMock()
    mock_client.upsert = AsyncMock()
    mock_client.query_points = AsyncMock(return_value=MagicMock(points=[]))
    mock_client.delete_collection = AsyncMock()
    return mock_client


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.exists = AsyncMock(return_value=0)
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()
    return mock_client


@pytest.fixture
def mock_minio_client():
    """Create a mock MinIO client."""
    mock_client = AsyncMock()
    mock_client.put_object = AsyncMock()
    mock_client.get_object = AsyncMock()
    mock_client.remove_object = AsyncMock()
    mock_client.presigned_get_object = AsyncMock(
        return_value="https://presigned-url.example.com/file"
    )
    return mock_client


@pytest.fixture
def mock_vault_client():
    """Create a mock HashiCorp Vault client."""
    mock_client = MagicMock()
    mock_client.secrets.kv.v2.read_secret_version = MagicMock(
        return_value={"data": {"data": {"api_key": "test-api-key"}}}
    )
    mock_client.secrets.kv.v2.create_or_update_secret = MagicMock()
    mock_client.secrets.kv.v2.delete_metadata_and_all_versions = MagicMock()
    return mock_client


# ============================================================================
# Test Data Factories
# ============================================================================


@pytest.fixture
def agent_config_factory():
    """Factory to create test agent configurations."""

    def create_agent(
        agent_id: str = None,
        name: str = "Test Agent",
        agent_type: str = "ToolAgent",
        **kwargs,
    ) -> Dict[str, Any]:
        return {
            "id": agent_id or f"agent-{uuid4().hex[:8]}",
            "name": name,
            "description": "A test agent for unit testing",
            "agent_type": agent_type,
            "role": {
                "title": "Test Assistant",
                "expertise": ["testing", "automation"],
                "personality": ["helpful", "precise"],
                "communication_style": "professional",
            },
            "goal": {
                "objective": "Help with testing",
                "success_criteria": ["Complete tests successfully"],
                "constraints": [],
            },
            "instructions": {
                "steps": ["Analyze the request", "Provide response"],
                "rules": ["Be helpful", "Be accurate"],
                "prohibited": [],
                "output_format": None,
            },
            "examples": [],
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 1024,
            },
            "tools": [],
            "safety": {
                "level": "standard",
                "blocked_topics": [],
                "blocked_patterns": [],
            },
            **kwargs,
        }

    return create_agent


@pytest.fixture
def skill_definition_factory():
    """Factory to create test skill definitions."""

    def create_skill(
        name: str = "Test Skill",
        category: str = "general",
        **kwargs,
    ) -> Dict[str, Any]:
        return {
            "name": name,
            "description": "A test skill for unit testing",
            "category": category,
            "tags": ["test", "automation"],
            "definition": {
                "metadata": {
                    "id": f"skill_{uuid4().hex[:12]}",
                    "name": name,
                    "description": "A test skill",
                    "version": "1.0.0",
                    "category": category,
                    "tags": ["test"],
                },
                "capability": {
                    "expertise": {
                        "terminology": [],
                        "reasoning_patterns": [],
                        "examples": [],
                    },
                },
                "resources": {
                    "files": [],
                    "urls": [],
                    "code_snippets": [],
                },
                "prompts": {
                    "system_enhancement": "You are an expert in testing.",
                },
                "parameters": [],
                "constraints": {
                    "max_tokens": 1000,
                },
            },
            **kwargs,
        }

    return create_skill


@pytest.fixture
def workflow_definition_factory():
    """Factory to create test workflow definitions."""

    def create_workflow(
        workflow_id: str = None,
        name: str = "Test Workflow",
        **kwargs,
    ) -> Dict[str, Any]:
        return {
            "id": workflow_id or f"workflow-{uuid4().hex[:8]}",
            "name": name,
            "description": "A test workflow for unit testing",
            "category": "test",
            "tags": ["test", "automation"],
            "definition": {
                "name": name,
                "description": "Test workflow",
                "steps": [
                    {
                        "id": "step-1",
                        "name": "First Step",
                        "agent_id": "test-agent-1",
                        "input_template": "{{user_input}}",
                    }
                ],
                "variables": {},
            },
            **kwargs,
        }

    return create_workflow


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def auth_headers(mock_user_id: str) -> Dict[str, str]:
    """Generate mock authorization headers."""
    return {"Authorization": "Bearer mock-token-for-testing"}


@pytest.fixture
def current_timestamp() -> datetime:
    """Get the current timestamp in UTC."""
    return datetime.now(timezone.utc)
