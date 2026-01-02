"""Tests for Skills API router.

Tests for all 22 skill endpoints:
- POST /skills (create)
- GET /skills (list)
- GET /skills/{skill_id} (get)
- PUT /skills/{skill_id} (update)
- DELETE /skills/{skill_id} (delete)
- POST /skills/{skill_id}/files (upload)
- GET /skills/{skill_id}/files (list files)
- GET /skills/{skill_id}/files/{file_id}/download (download)
- DELETE /skills/{skill_id}/files/{file_id} (delete file)
- GET /skills/supported-file-types (supported types)
- POST /skills/generate (AI generate)
- POST /skills/generate/refine (refine)
- POST /skills/search (semantic search)
- POST /skills/recommendations (get recommendations)
- POST /skills/{skill_id}/test (test skill)
- POST /skills/preview (preview skill)
- GET /skills/{skill_id}/versions (list versions)
- POST /skills/{skill_id}/versions/{v}/rollback (rollback)
- GET /skills/marketplace (browse)
- POST /skills/{skill_id}/publish (publish)
- POST /skills/marketplace/{id}/import (import)
- POST /skills/marketplace/{id}/rate (rate)
- GET /skills/{skill_id}/stats (stats)
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

# Note: SkillCategory values are: DOMAIN_EXPERTISE, DOCUMENT_GENERATION, DATA_ANALYSIS,
# COMMUNICATION, RESEARCH, CODING, CUSTOM


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_skill_definition():
    """Create a sample skill definition dict for API requests."""
    return {
        "metadata": {
            "id": "skill_test123",
            "name": "Test Skill",
            "description": "A test skill",
            "version": "1.0.0",
            "category": "domain_expertise",
            "tags": ["test"],
        },
        "capability": {
            "expertise": {
                "domain": "testing",
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
            "system_enhancement": "You are an expert tester.",
        },
        "parameters": [],
        "constraints": {
            "max_tokens": 1000,
        },
    }


@pytest.fixture
def mock_skill():
    """Create a mock Skill domain object."""
    from src.skills.models import Skill, SkillCategory, SkillDefinition, SkillStatus

    return Skill(
        id="skill-123",
        tenant_id="org-123",
        name="Test Skill",
        description="A test skill",
        category=SkillCategory.DOMAIN_EXPERTISE,
        tags=["test", "sample"],
        definition=SkillDefinition.from_dict({
            "metadata": {
                "id": "skill_test123",
                "name": "Test Skill",
                "description": "A test skill",
                "version": "1.0.0",
                "category": "domain_expertise",
                "tags": ["test"],
            },
            "capability": {
                "expertise": {
                    "domain": "testing",
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
                "system_enhancement": "You are an expert.",
            },
            "parameters": [],
            "constraints": {"max_tokens": 1000},
        }),
        version=1,
        status=SkillStatus.DRAFT,
        is_public=False,
        rating_avg=0.0,
        rating_count=0,
        install_count=0,
        created_by="user-123",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_public_skill(mock_skill):
    """Create a mock public skill for marketplace tests."""
    from src.skills.models import SkillStatus

    mock_skill.is_public = True
    mock_skill.status = SkillStatus.PUBLISHED
    mock_skill.rating_avg = 4.5
    mock_skill.rating_count = 10
    mock_skill.install_count = 100
    return mock_skill


# ============================================================================
# CRUD Endpoint Tests
# ============================================================================


class TestCreateSkill:
    """Tests for POST /skills"""

    @pytest.mark.asyncio
    async def test_create_skill_success(
        self, client: AsyncClient, override_skill_repo, sample_skill_definition, mock_skill
    ):
        """Test successful skill creation."""
        override_skill_repo.create.return_value = mock_skill

        response = await client.post(
            "/api/v1/skills",
            json={
                "name": "Test Skill",
                "description": "A test skill",
                "category": "domain_expertise",
                "tags": ["test"],
                "definition": sample_skill_definition,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Skill"
        assert data["id"] == "skill-123"
        assert "definition" in data

    @pytest.mark.asyncio
    async def test_create_skill_invalid_category(
        self, client: AsyncClient, sample_skill_definition
    ):
        """Test creating skill with invalid category."""
        response = await client.post(
            "/api/v1/skills",
            json={
                "name": "Test Skill",
                "description": "A test skill",
                "category": "invalid_category",  # Invalid
                "tags": ["test"],
                "definition": sample_skill_definition,
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_skill_missing_fields(self, client: AsyncClient):
        """Test creating skill with missing required fields."""
        response = await client.post(
            "/api/v1/skills",
            json={
                "name": "Test Skill",
                # Missing description, category, definition
            },
        )

        assert response.status_code == 422


class TestListSkills:
    """Tests for GET /skills"""

    @pytest.mark.asyncio
    async def test_list_skills_success(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test listing skills."""
        override_skill_repo.list.return_value = [mock_skill]
        override_skill_repo.count.return_value = 1

        response = await client.get("/api/v1/skills")

        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["skills"]) == 1

    @pytest.mark.asyncio
    async def test_list_skills_with_filters(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test listing skills with category filter."""
        override_skill_repo.list.return_value = [mock_skill]
        override_skill_repo.count.return_value = 1

        response = await client.get(
            "/api/v1/skills",
            params={
                "category": "domain_expertise",
                "tags": "test,sample",
                "search": "test",
                "limit": 10,
                "offset": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_skills_empty(self, client: AsyncClient, override_skill_repo):
        """Test listing skills when none exist."""
        override_skill_repo.list.return_value = []
        override_skill_repo.count.return_value = 0

        response = await client.get("/api/v1/skills")

        assert response.status_code == 200
        data = response.json()
        assert data["skills"] == []
        assert data["total"] == 0


class TestGetSkill:
    """Tests for GET /skills/{skill_id}"""

    @pytest.mark.asyncio
    async def test_get_skill_success(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test getting a skill by ID."""
        override_skill_repo.get.return_value = mock_skill

        response = await client.get("/api/v1/skills/skill-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "skill-123"
        assert data["name"] == "Test Skill"

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, client: AsyncClient, override_skill_repo):
        """Test getting non-existent skill."""
        override_skill_repo.get.return_value = None

        response = await client.get("/api/v1/skills/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["message"]


class TestUpdateSkill:
    """Tests for PUT /skills/{skill_id}"""

    @pytest.mark.asyncio
    async def test_update_skill_success(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test updating a skill."""
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = True
        updated_skill = mock_skill
        updated_skill.name = "Updated Skill"
        override_skill_repo.update.return_value = updated_skill

        response = await client.put(
            "/api/v1/skills/skill-123",
            json={
                "name": "Updated Skill",
                "description": "Updated description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Skill"

    @pytest.mark.asyncio
    async def test_update_skill_not_found(self, client: AsyncClient, override_skill_repo):
        """Test updating non-existent skill."""
        override_skill_repo.exists.return_value = False

        response = await client.put(
            "/api/v1/skills/nonexistent",
            json={"name": "Updated"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_skill_not_owner(self, client: AsyncClient, override_skill_repo):
        """Test updating skill without ownership."""
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = False

        response = await client.put(
            "/api/v1/skills/skill-123",
            json={"name": "Updated"},
        )

        assert response.status_code == 403
        assert "permission" in response.json()["message"].lower()


class TestDeleteSkill:
    """Tests for DELETE /skills/{skill_id}"""

    @pytest.mark.asyncio
    async def test_delete_skill_success(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test deleting a skill."""
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = True
        override_skill_repo.delete.return_value = None

        response = await client.delete("/api/v1/skills/skill-123")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_skill_not_found(self, client: AsyncClient, override_skill_repo):
        """Test deleting non-existent skill."""
        override_skill_repo.exists.return_value = False

        response = await client.delete("/api/v1/skills/nonexistent")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_skill_not_owner(self, client: AsyncClient, override_skill_repo):
        """Test deleting skill without ownership."""
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = False

        response = await client.delete("/api/v1/skills/skill-123")

        assert response.status_code == 403


# ============================================================================
# File Management Tests
# ============================================================================


class TestFileUpload:
    """Tests for POST /skills/{skill_id}/files"""

    @pytest.mark.asyncio
    async def test_upload_file_skill_not_found(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test uploading file to non-existent skill."""
        override_skill_repo.exists.return_value = False

        response = await client.post(
            "/api/v1/skills/nonexistent/files",
            files={"file": ("test.txt", b"test content", "text/plain")},
            params={"file_type": "reference"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_file_not_owner(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test uploading file without ownership.

        Note: Returns 404 (not 403) because user-scoped repository doesn't
        expose skills from other users - more secure (no information leakage).
        """
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = False

        response = await client.post(
            "/api/v1/skills/skill-123/files",
            files={"file": ("test.txt", b"test content", "text/plain")},
            params={"file_type": "reference"},
        )

        # Returns 404 because skill is not visible to non-owner
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_unsupported_file_type(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test uploading unsupported file type."""
        response = await client.post(
            "/api/v1/skills/skill-123/files",
            files={"file": ("test.exe", b"binary", "application/octet-stream")},
            params={"file_type": "reference"},
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type_param(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test uploading with invalid file_type parameter."""
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = True

        response = await client.post(
            "/api/v1/skills/skill-123/files",
            files={"file": ("test.txt", b"test content", "text/plain")},
            params={"file_type": "invalid"},
        )

        assert response.status_code == 400
        assert "file_type must be" in response.json()["message"]


class TestListFiles:
    """Tests for GET /skills/{skill_id}/files"""

    @pytest.mark.asyncio
    async def test_list_files_success(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test listing skill files."""
        override_skill_repo.get.return_value = mock_skill

        response = await client.get("/api/v1/skills/skill-123/files")

        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_files_skill_not_found(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test listing files for non-existent skill."""
        override_skill_repo.get.return_value = None

        response = await client.get("/api/v1/skills/nonexistent/files")

        assert response.status_code == 404


class TestFileDownload:
    """Tests for GET /skills/{skill_id}/files/{file_id}/download"""

    @pytest.mark.asyncio
    async def test_download_file_skill_not_found(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test downloading file from non-existent skill."""
        override_skill_repo.get.return_value = None

        response = await client.get("/api/v1/skills/nonexistent/files/file-1/download")

        assert response.status_code == 404


class TestDeleteFile:
    """Tests for DELETE /skills/{skill_id}/files/{file_id}"""

    @pytest.mark.asyncio
    async def test_delete_file_skill_not_found(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test deleting file from non-existent skill."""
        override_skill_repo.remove_file_atomically.return_value = (None, None)
        override_skill_repo.exists.return_value = False

        response = await client.delete("/api/v1/skills/nonexistent/files/file-1")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_file_not_owner(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test deleting file without ownership.

        Note: Returns 404 (not 403) because user-scoped repository doesn't
        expose skills from other users - more secure (no information leakage).
        """
        override_skill_repo.remove_file_atomically.return_value = (None, None)
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = False

        response = await client.delete("/api/v1/skills/skill-123/files/file-1")

        # Returns 404 because skill is not visible to non-owner
        assert response.status_code == 404


class TestSupportedFileTypes:
    """Tests for GET /skills/supported-file-types"""

    @pytest.mark.asyncio
    async def test_get_supported_file_types(self, client: AsyncClient):
        """Test getting supported file types."""
        response = await client.get("/api/v1/skills/supported-file-types")

        assert response.status_code == 200
        data = response.json()
        assert "extensions" in data
        assert "categories" in data
        assert "max_size_mb" in data
        assert isinstance(data["extensions"], list)


# ============================================================================
# AI Generation Tests
# ============================================================================


class TestGenerateSkill:
    """Tests for POST /skills/generate"""

    @pytest.mark.asyncio
    async def test_generate_skill_not_implemented(self, client: AsyncClient):
        """Test skill generation returns 501 (not implemented)."""
        response = await client.post(
            "/api/v1/skills/generate",
            json={
                "prompt": "Create a skill for data analysis",
                "category": "analysis",
            },
        )

        assert response.status_code == 501
        assert "coming soon" in response.json()["message"].lower()


class TestRefineSkill:
    """Tests for POST /skills/generate/refine"""

    @pytest.mark.asyncio
    async def test_refine_skill_not_implemented(
        self, client: AsyncClient, sample_skill_definition
    ):
        """Test skill refinement returns 501 (not implemented)."""
        response = await client.post(
            "/api/v1/skills/generate/refine",
            json={
                "skill": sample_skill_definition,
                "feedback": "Make it more detailed",
            },
        )

        assert response.status_code == 501
        assert "coming soon" in response.json()["message"].lower()


# ============================================================================
# Search & Discovery Tests
# ============================================================================


class TestSearchSkills:
    """Tests for POST /skills/search"""

    @pytest.mark.asyncio
    async def test_search_skills_success(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test semantic skill search."""
        override_skill_repo.list.return_value = [mock_skill]

        response = await client.post(
            "/api/v1/skills/search",
            json={
                "query": "data analysis skill",
                "limit": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert "query_understanding" in data

    @pytest.mark.asyncio
    async def test_search_skills_with_filters(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test skill search with filters."""
        override_skill_repo.list.return_value = [mock_skill]

        response = await client.post(
            "/api/v1/skills/search",
            json={
                "query": "analysis",
                "categories": ["domain_expertise"],
                "tags": ["test"],
                "include_public": True,
                "limit": 5,
            },
        )

        assert response.status_code == 200


class TestRecommendSkills:
    """Tests for POST /skills/recommendations"""

    @pytest.mark.asyncio
    async def test_recommend_skills_success(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test skill recommendations."""
        override_skill_repo.list.return_value = [mock_skill]

        response = await client.post(
            "/api/v1/skills/recommendations",
            json={
                "task_description": "I need to analyze sales data",
                "max_skills": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "reasoning" in data


# ============================================================================
# Testing & Preview Tests
# ============================================================================


class TestTestSkill:
    """Tests for POST /skills/{skill_id}/test"""

    @pytest.mark.asyncio
    async def test_test_skill_success(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test skill testing endpoint."""
        override_skill_repo.get.return_value = mock_skill

        response = await client.post(
            "/api/v1/skills/skill-123/test",
            json={"input": "Test input for the skill", "parameters": {}},
        )

        assert response.status_code == 200
        data = response.json()
        assert "enhanced_prompt" in data
        assert "prompt_token_count" in data
        assert "execution_time_ms" in data

    @pytest.mark.asyncio
    async def test_test_skill_not_found(self, client: AsyncClient, override_skill_repo):
        """Test testing non-existent skill."""
        override_skill_repo.get.return_value = None

        response = await client.post(
            "/api/v1/skills/nonexistent/test",
            json={"input": "Test input", "parameters": {}},
        )

        assert response.status_code == 404


class TestPreviewSkill:
    """Tests for POST /skills/preview"""

    @pytest.mark.asyncio
    async def test_preview_skill_success(
        self, client: AsyncClient, sample_skill_definition
    ):
        """Test skill preview without saving."""
        response = await client.post(
            "/api/v1/skills/preview",
            json={
                "definition": sample_skill_definition,
                "input": "Preview test input",
                "parameters": {},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "enhanced_prompt" in data
        assert "prompt_token_count" in data
        assert "execution_time_ms" in data


# ============================================================================
# Versioning Tests
# ============================================================================


class TestListVersions:
    """Tests for GET /skills/{skill_id}/versions"""

    @pytest.mark.asyncio
    async def test_list_versions_success(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test listing skill versions."""
        override_skill_repo.get.return_value = mock_skill
        override_skill_repo.get_versions.return_value = [
            {"version": 1, "changelog": "Initial version", "created_at": "2024-01-01"},
        ]

        response = await client.get("/api/v1/skills/skill-123/versions")

        assert response.status_code == 200
        data = response.json()
        assert "versions" in data
        assert "current_version" in data

    @pytest.mark.asyncio
    async def test_list_versions_skill_not_found(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test listing versions for non-existent skill."""
        override_skill_repo.get.return_value = None

        response = await client.get("/api/v1/skills/nonexistent/versions")

        assert response.status_code == 404


class TestRollbackVersion:
    """Tests for POST /skills/{skill_id}/versions/{version}/rollback"""

    @pytest.mark.asyncio
    async def test_rollback_success(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test rolling back to a previous version."""
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = True
        override_skill_repo.rollback_to_version.return_value = mock_skill

        response = await client.post("/api/v1/skills/skill-123/versions/1/rollback")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rollback_skill_not_found(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test rollback for non-existent skill."""
        override_skill_repo.exists.return_value = False

        response = await client.post("/api/v1/skills/nonexistent/versions/1/rollback")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_rollback_not_owner(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test rollback without ownership."""
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = False

        response = await client.post("/api/v1/skills/skill-123/versions/1/rollback")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_rollback_version_not_found(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test rollback to non-existent version."""
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = True
        override_skill_repo.rollback_to_version.return_value = None

        response = await client.post("/api/v1/skills/skill-123/versions/99/rollback")

        assert response.status_code == 404


# ============================================================================
# Marketplace Tests
# ============================================================================


class TestBrowseMarketplace:
    """Tests for GET /skills/marketplace"""

    @pytest.mark.asyncio
    async def test_browse_marketplace_success(
        self, client: AsyncClient, override_skill_repo, mock_public_skill
    ):
        """Test browsing marketplace skills."""
        override_skill_repo.list.return_value = [mock_public_skill]

        response = await client.get("/api/v1/skills/marketplace")

        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "total" in data
        assert "categories" in data
        assert "popular_tags" in data

    @pytest.mark.asyncio
    async def test_browse_marketplace_with_filters(
        self, client: AsyncClient, override_skill_repo, mock_public_skill
    ):
        """Test browsing marketplace with filters."""
        override_skill_repo.list.return_value = [mock_public_skill]

        response = await client.get(
            "/api/v1/skills/marketplace",
            params={
                "category": "domain_expertise",
                "tags": "test",
                "search": "skill",
                "sort_by": "popular",
                "limit": 10,
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_marketplace_empty(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test browsing empty marketplace."""
        override_skill_repo.list.return_value = []

        response = await client.get("/api/v1/skills/marketplace")

        assert response.status_code == 200
        data = response.json()
        assert data["skills"] == []
        assert data["total"] == 0


class TestPublishSkill:
    """Tests for POST /skills/{skill_id}/publish"""

    @pytest.mark.asyncio
    async def test_publish_skill_success(
        self, client: AsyncClient, override_skill_repo, mock_public_skill
    ):
        """Test publishing a skill to marketplace."""
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = True
        override_skill_repo.publish_to_marketplace.return_value = mock_public_skill

        response = await client.post(
            "/api/v1/skills/skill-123/publish",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert "marketplace_id" in data

    @pytest.mark.asyncio
    async def test_publish_skill_not_found(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test publishing non-existent skill."""
        override_skill_repo.exists.return_value = False

        response = await client.post(
            "/api/v1/skills/nonexistent/publish",
            json={},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_publish_skill_not_owner(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test publishing without ownership."""
        override_skill_repo.exists.return_value = True
        override_skill_repo.is_owner.return_value = False

        response = await client.post(
            "/api/v1/skills/skill-123/publish",
            json={},
        )

        assert response.status_code == 403


class TestImportSkill:
    """Tests for POST /skills/marketplace/{marketplace_id}/import"""

    @pytest.mark.asyncio
    async def test_import_skill_success(
        self, client: AsyncClient, override_skill_repo, mock_public_skill, mock_skill
    ):
        """Test importing skill from marketplace."""
        override_skill_repo.get.return_value = mock_public_skill
        override_skill_repo.create.return_value = mock_skill

        response = await client.post(
            "/api/v1/skills/marketplace/skill-123/import",
            json={"marketplace_id": "skill-123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "imported"
        assert "skill_id" in data

    @pytest.mark.asyncio
    async def test_import_skill_not_found(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test importing non-existent marketplace skill."""
        override_skill_repo.get.return_value = None

        response = await client.post(
            "/api/v1/skills/marketplace/nonexistent/import",
            json={"marketplace_id": "nonexistent"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_import_private_skill_fails(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test importing private skill fails."""
        mock_skill.is_public = False
        override_skill_repo.get.return_value = mock_skill

        response = await client.post(
            "/api/v1/skills/marketplace/skill-123/import",
            json={"marketplace_id": "skill-123"},
        )

        assert response.status_code == 404


class TestRateSkill:
    """Tests for POST /skills/marketplace/{marketplace_id}/rate"""

    @pytest.mark.asyncio
    async def test_rate_skill_not_implemented(self, client: AsyncClient):
        """Test skill rating returns 501 (not implemented)."""
        response = await client.post(
            "/api/v1/skills/marketplace/skill-123/rate",
            json={"rating": 5, "review": "Great skill!"},
        )

        assert response.status_code == 501
        assert "coming soon" in response.json()["message"].lower()


# ============================================================================
# Stats Tests
# ============================================================================


class TestGetSkillStats:
    """Tests for GET /skills/{skill_id}/stats"""

    @pytest.mark.asyncio
    async def test_get_stats_success(
        self, client: AsyncClient, override_skill_repo, mock_skill
    ):
        """Test getting skill statistics."""
        override_skill_repo.get.return_value = mock_skill
        override_skill_repo.get_stats.return_value = {
            "total_executions": 100,
            "success_rate": 0.95,
            "avg_duration_ms": 150.5,
        }

        response = await client.get("/api/v1/skills/skill-123/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_executions"] == 100
        assert data["success_rate"] == 0.95
        assert data["avg_duration_ms"] == 150.5

    @pytest.mark.asyncio
    async def test_get_stats_skill_not_found(
        self, client: AsyncClient, override_skill_repo
    ):
        """Test getting stats for non-existent skill."""
        override_skill_repo.get.return_value = None

        response = await client.get("/api/v1/skills/nonexistent/stats")

        assert response.status_code == 404
