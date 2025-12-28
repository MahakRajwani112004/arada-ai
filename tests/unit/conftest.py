"""Unit test specific fixtures and configurations.

This module extends the root conftest.py with fixtures specific to unit testing,
including more granular mocking for repositories and services.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator
from uuid import uuid4

import pytest


# ============================================================================
# Repository Mocks
# ============================================================================


@pytest.fixture
def mock_agent_repository():
    """Create a mock agent repository."""
    mock_repo = AsyncMock()
    mock_repo.exists = AsyncMock(return_value=False)
    mock_repo.get = AsyncMock(return_value=None)
    mock_repo.list = AsyncMock(return_value=[])
    mock_repo.save = AsyncMock()
    mock_repo.delete = AsyncMock(return_value=True)
    return mock_repo


@pytest.fixture
def mock_skill_repository():
    """Create a mock skill repository."""
    mock_repo = AsyncMock()
    mock_repo.exists = AsyncMock(return_value=False)
    mock_repo.is_owner = AsyncMock(return_value=True)
    mock_repo.get = AsyncMock(return_value=None)
    mock_repo.list = AsyncMock(return_value=[])
    mock_repo.count = AsyncMock(return_value=0)
    mock_repo.create = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.delete = AsyncMock()
    mock_repo.get_versions = AsyncMock(return_value=[])
    mock_repo.rollback_to_version = AsyncMock()
    mock_repo.publish_to_marketplace = AsyncMock()
    mock_repo.get_stats = AsyncMock(return_value={
        "total_executions": 0,
        "success_rate": 0.0,
        "avg_duration_ms": 0.0,
    })
    mock_repo.add_file_atomically = AsyncMock()
    mock_repo.remove_file_atomically = AsyncMock(return_value=(None, None))
    return mock_repo


@pytest.fixture
def mock_workflow_repository():
    """Create a mock workflow repository."""
    mock_repo = AsyncMock()
    mock_repo.exists = AsyncMock(return_value=False)
    mock_repo.get = AsyncMock(return_value=None)
    mock_repo.list = AsyncMock(return_value=[])
    mock_repo.save = AsyncMock()
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.copy = AsyncMock()
    mock_repo.list_executions = AsyncMock(return_value=[])
    mock_repo.get_execution = AsyncMock(return_value=None)
    return mock_repo


@pytest.fixture
def mock_knowledge_repository():
    """Create a mock knowledge repository."""
    mock_repo = AsyncMock()
    mock_repo.create_knowledge_base = AsyncMock()
    mock_repo.get_knowledge_base = AsyncMock(return_value=None)
    mock_repo.list_knowledge_bases = AsyncMock(return_value=[])
    mock_repo.update_knowledge_base = AsyncMock()
    mock_repo.delete_knowledge_base = AsyncMock(return_value=True)
    mock_repo.create_document = AsyncMock()
    mock_repo.get_document = AsyncMock(return_value=None)
    mock_repo.list_documents = AsyncMock(return_value=[])
    mock_repo.update_document = AsyncMock()
    mock_repo.delete_document = AsyncMock()
    mock_repo.update_kb_stats = AsyncMock()
    return mock_repo


@pytest.fixture
def mock_mcp_repository():
    """Create a mock MCP server repository."""
    mock_repo = AsyncMock()
    mock_repo.create = AsyncMock()
    mock_repo.get = AsyncMock(return_value=None)
    mock_repo.list_all = AsyncMock(return_value=[])
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.get_config = AsyncMock(return_value=None)
    mock_repo.update_status = AsyncMock()
    mock_repo.update_credentials = AsyncMock(return_value=True)
    return mock_repo


# ============================================================================
# Service Mocks
# ============================================================================


@pytest.fixture
def mock_auth_service():
    """Create a mock auth service."""
    mock_service = AsyncMock()
    mock_service.authenticate_user = AsyncMock(return_value=None)
    mock_service.create_user = AsyncMock()
    mock_service.create_tokens = AsyncMock(return_value={
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
        "token_type": "bearer",
    })
    mock_service.refresh_tokens = AsyncMock()
    mock_service.revoke_refresh_token = AsyncMock()
    mock_service.get_user_by_email = AsyncMock(return_value=None)
    mock_service.update_email = AsyncMock()
    mock_service.update_password = AsyncMock()
    mock_service.update_display_name = AsyncMock()
    mock_service.create_invite = AsyncMock()
    mock_service.validate_invite = AsyncMock(return_value=None)
    mock_service.list_api_keys = AsyncMock(return_value=[])
    mock_service.create_api_key = AsyncMock()
    mock_service.delete_api_key = AsyncMock(return_value=True)
    mock_service.list_llm_credentials = AsyncMock(return_value=[])
    mock_service.create_llm_credential = AsyncMock()
    mock_service.update_llm_credential = AsyncMock()
    mock_service.delete_llm_credential = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def mock_mcp_manager():
    """Create a mock MCP manager."""
    mock_manager = AsyncMock()
    mock_manager.add_server = AsyncMock()
    mock_manager.remove_server = AsyncMock()
    mock_manager.get_tools = AsyncMock(return_value=[])
    mock_manager.health_check = AsyncMock(return_value={})
    return mock_manager


@pytest.fixture
def mock_secrets_manager():
    """Create a mock secrets manager."""
    mock_manager = AsyncMock()
    mock_manager.store = AsyncMock()
    mock_manager.retrieve = AsyncMock(return_value={})
    mock_manager.delete = AsyncMock()
    return mock_manager


# ============================================================================
# Storage Mocks
# ============================================================================


@pytest.fixture
def mock_object_storage():
    """Create a mock object storage (MinIO)."""
    mock_storage = AsyncMock()
    mock_storage.upload = AsyncMock()
    mock_storage.download = AsyncMock(return_value=b"test content")
    mock_storage.delete = AsyncMock()
    mock_storage.get_presigned_url = AsyncMock(
        return_value="https://presigned-url.example.com"
    )
    return mock_storage


# ============================================================================
# Dependency Override Helpers
# ============================================================================


@pytest.fixture
def override_skill_repo(app, mock_skill_repository):
    """Override skill repository dependency."""
    from src.api.dependencies import get_skill_repository

    async def override():
        yield mock_skill_repository

    app.dependency_overrides[get_skill_repository] = override
    yield mock_skill_repository
    app.dependency_overrides.pop(get_skill_repository, None)


@pytest.fixture
def override_agent_repo(app, mock_agent_repository):
    """Override agent repository dependency."""
    from src.api.dependencies import get_repository, get_user_repository

    async def override():
        yield mock_agent_repository

    app.dependency_overrides[get_repository] = override
    app.dependency_overrides[get_user_repository] = override
    yield mock_agent_repository
    app.dependency_overrides.pop(get_repository, None)
    app.dependency_overrides.pop(get_user_repository, None)


@pytest.fixture
def override_workflow_repo(app, mock_workflow_repository):
    """Override workflow repository dependency."""
    from src.api.dependencies import get_workflow_repository

    async def override():
        yield mock_workflow_repository

    app.dependency_overrides[get_workflow_repository] = override
    yield mock_workflow_repository
    app.dependency_overrides.pop(get_workflow_repository, None)


@pytest.fixture
def override_mcp_manager(app, mock_mcp_manager):
    """Override MCP manager dependency."""
    from src.api.dependencies import get_mcp_manager

    def override():
        return mock_mcp_manager

    app.dependency_overrides[get_mcp_manager] = override
    yield mock_mcp_manager
    app.dependency_overrides.pop(get_mcp_manager, None)
