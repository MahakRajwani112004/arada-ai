"""Skills API routes for CRUD, generation, testing, and marketplace."""

import time
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from src.api.dependencies import get_skill_repository
from src.skills.file_service import (
    FileUploadResult,
    get_supported_extensions,
    is_supported_file,
    upload_skill_file,
    delete_skill_file,
    get_file_download_url,
)
from src.auth.dependencies import CurrentUser
from src.api.schemas.skills import (
    CreateSkillRequest,
    GenerateSkillRequest,
    GenerateSkillResponse,
    ImportSkillRequest,
    ImportSkillResponse,
    MarketplaceListResponse,
    MarketplaceSkillSchema,
    PreviewSkillRequest,
    PreviewSkillResponse,
    PublishSkillRequest,
    PublishSkillResponse,
    RateSkillRequest,
    RateSkillResponse,
    RecommendSkillsRequest,
    RecommendSkillsResponse,
    RefineSkillRequest,
    RefineSkillResponse,
    RollbackSkillRequest,
    SearchSkillsRequest,
    SearchSkillsResponse,
    SkillCategoryEnum,
    SkillListResponse,
    SkillMatchSchema,
    SkillResponse,
    SkillStatsResponse,
    SkillStatusEnum,
    SkillSummaryResponse,
    SkillVersionSchema,
    SkillVersionsResponse,
    TestSkillRequest,
    TestSkillResponse,
    UpdateSkillRequest,
)
from src.skills.models import (
    Skill,
    SkillCategory,
    SkillDefinition,
    SkillStatus,
)
from src.skills.repository import SkillRepository

router = APIRouter(prefix="/skills", tags=["skills"])


# ==================== Helper Functions ====================


def _to_response(skill: Skill) -> SkillResponse:
    """Convert Skill domain object to API response."""
    return SkillResponse(
        id=skill.id,
        tenant_id=skill.tenant_id,
        name=skill.name,
        description=skill.description,
        category=skill.category.value,
        tags=skill.tags,
        definition=skill.definition.to_dict(),
        version=skill.version,
        status=skill.status.value,
        is_public=skill.is_public,
        rating_avg=skill.rating_avg,
        rating_count=skill.rating_count,
        install_count=skill.install_count,
        created_by=skill.created_by,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


def _to_summary(skill: Skill) -> SkillSummaryResponse:
    """Convert Skill domain object to summary response."""
    return SkillSummaryResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        category=skill.category.value,
        tags=skill.tags,
        version=skill.version,
        status=skill.status.value,
        is_public=skill.is_public,
        rating_avg=skill.rating_avg,
        rating_count=skill.rating_count,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


# ==================== Skill CRUD ====================


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    request: CreateSkillRequest,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> SkillResponse:
    """Create a new skill."""
    # Convert API schema to domain model
    definition = SkillDefinition.from_dict(request.definition.model_dump())

    skill = await skill_repo.create(
        name=request.name,
        description=request.description,
        category=SkillCategory(request.category.value),
        tags=request.tags,
        definition=definition,
        created_by=current_user.id,
    )

    return _to_response(skill)


@router.get("", response_model=SkillListResponse)
async def list_skills(
    current_user: CurrentUser,
    category: Optional[SkillCategoryEnum] = Query(None, description="Filter by category"),
    status_filter: Optional[SkillStatusEnum] = Query(None, alias="status", description="Filter by status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    include_public: bool = Query(True, description="Include public marketplace skills"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> SkillListResponse:
    """List skills with optional filters."""
    # Parse tags if provided
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    skills = await skill_repo.list(
        category=SkillCategory(category.value) if category else None,
        tags=tag_list,
        status=SkillStatus(status_filter.value) if status_filter else None,
        search=search,
        include_public=include_public,
        limit=limit,
        offset=offset,
    )

    return SkillListResponse(
        skills=[_to_summary(s) for s in skills],
        total=len(skills),
    )


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> SkillResponse:
    """Get skill by ID."""
    skill = await skill_repo.get(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )

    return _to_response(skill)


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    request: UpdateSkillRequest,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> SkillResponse:
    """Update a skill."""
    # Convert definition if provided
    definition = None
    if request.definition:
        definition = SkillDefinition.from_dict(request.definition.model_dump())

    skill = await skill_repo.update(
        skill_id=skill_id,
        name=request.name,
        description=request.description,
        category=SkillCategory(request.category.value) if request.category else None,
        tags=request.tags,
        definition=definition,
        status=SkillStatus(request.status.value) if request.status else None,
        changelog=request.changelog,
    )

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )

    return _to_response(skill)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> None:
    """Delete a skill."""
    if not await skill_repo.delete(skill_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )


# ==================== File Management ====================


@router.post("/{skill_id}/files")
async def upload_file_to_skill(
    skill_id: str,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    file_type: str = Query("reference", description="File type: 'reference' or 'template'"),
    skill_repo: SkillRepository = Depends(get_skill_repository),
):
    """Upload a file to a skill.

    Supported file types:
    - Documents: pdf, txt, md, docx
    - Code: py, js, ts, json, yaml, xml, html, css, sql, sh
    - Data: csv, tsv
    - Config: env, ini, toml, conf

    Files are stored in MinIO and text is extracted for prompt injection.
    """
    # Check skill exists
    skill = await skill_repo.get(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )

    # Validate file type
    if not is_supported_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {', '.join(get_supported_extensions())}",
        )

    # Validate file_type parameter
    from src.skills.models import FileType as SkillFileType
    try:
        skill_file_type = SkillFileType(file_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_type must be 'reference' or 'template'",
        )

    # Read file content
    file_data = await file.read()

    # Upload file
    result = await upload_skill_file(
        skill_id=skill_id,
        filename=file.filename,
        file_data=file_data,
        file_type=skill_file_type,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    # Add file to skill's resources
    skill.definition.resources.files.append(result.skill_file)
    await skill_repo.update(
        skill_id=skill_id,
        definition=skill.definition,
    )

    return {
        "file_id": result.skill_file.id,
        "filename": result.skill_file.name,
        "file_type": result.skill_file.file_type.value,
        "mime_type": result.skill_file.mime_type,
        "size_bytes": result.skill_file.size_bytes,
        "preview_length": len(result.skill_file.content_preview),
        "message": "File uploaded successfully",
    }


@router.get("/{skill_id}/files")
async def list_skill_files(
    skill_id: str,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
):
    """List all files attached to a skill."""
    skill = await skill_repo.get(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )

    files = skill.definition.resources.files
    return {
        "files": [
            {
                "id": f.id,
                "name": f.name,
                "file_type": f.file_type.value,
                "mime_type": f.mime_type,
                "size_bytes": f.size_bytes,
                "uploaded_at": f.uploaded_at.isoformat(),
            }
            for f in files
        ],
        "total": len(files),
    }


@router.get("/{skill_id}/files/{file_id}/download")
async def get_file_download(
    skill_id: str,
    file_id: str,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
):
    """Get a presigned download URL for a skill file."""
    skill = await skill_repo.get(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )

    # Find the file
    target_file = None
    for f in skill.definition.resources.files:
        if f.id == file_id:
            target_file = f
            break

    if not target_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_id}' not found in skill",
        )

    # Get presigned URL
    download_url = await get_file_download_url(target_file.storage_url)

    return {
        "download_url": download_url,
        "filename": target_file.name,
        "expires_in_seconds": 3600,
    }


@router.delete("/{skill_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_from_skill(
    skill_id: str,
    file_id: str,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
):
    """Delete a file from a skill."""
    skill = await skill_repo.get(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )

    # Find and remove the file
    target_file = None
    updated_files = []
    for f in skill.definition.resources.files:
        if f.id == file_id:
            target_file = f
        else:
            updated_files.append(f)

    if not target_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_id}' not found in skill",
        )

    # Delete from MinIO
    await delete_skill_file(target_file.storage_url)

    # Update skill
    skill.definition.resources.files = updated_files
    await skill_repo.update(
        skill_id=skill_id,
        definition=skill.definition,
    )


@router.get("/supported-file-types")
async def get_supported_file_types():
    """Get list of supported file types for skill uploads."""
    return {
        "supported_extensions": get_supported_extensions(),
        "categories": {
            "documents": ["pdf", "txt", "md", "docx"],
            "code": ["py", "js", "ts", "jsx", "tsx", "json", "yaml", "yml", "xml", "html", "css", "sql", "sh", "bash"],
            "data": ["csv", "tsv"],
            "config": ["env", "ini", "toml", "conf"],
        },
    }


# ==================== AI Generation ====================


@router.post("/generate", response_model=GenerateSkillResponse)
async def generate_skill(
    request: GenerateSkillRequest,
    current_user: CurrentUser,
) -> GenerateSkillResponse:
    """Generate a skill from natural language description.

    This uses AI to create a complete skill definition from a natural language prompt.
    The generated skill can then be refined or saved directly.
    """
    # TODO: Implement skill generation using LLM
    # For now, return a placeholder response indicating the feature is not yet implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Skill generation is coming soon. Please create skills manually for now.",
    )


@router.post("/generate/refine", response_model=RefineSkillResponse)
async def refine_skill(
    request: RefineSkillRequest,
    current_user: CurrentUser,
) -> RefineSkillResponse:
    """Refine a generated skill based on user feedback.

    Takes the current skill definition and user feedback to improve it.
    """
    # TODO: Implement skill refinement using LLM
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Skill refinement is coming soon.",
    )


# ==================== Search & Discovery ====================


@router.post("/search", response_model=SearchSkillsResponse)
async def search_skills(
    request: SearchSkillsRequest,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> SearchSkillsResponse:
    """Semantic search for skills.

    Uses embeddings and semantic matching to find relevant skills.
    """
    # For now, use text-based search from the list method
    # TODO: Implement semantic search with embeddings
    skills = await skill_repo.list(
        category=SkillCategory(request.categories[0].value) if request.categories else None,
        tags=request.tags if request.tags else None,
        search=request.query,
        include_public=request.include_public,
        limit=request.limit,
    )

    return SearchSkillsResponse(
        matches=[
            SkillMatchSchema(
                skill=_to_summary(s),
                relevance_score=0.8,  # Placeholder score
                match_reason=f"Matched search query: {request.query}",
            )
            for s in skills
        ],
        query_understanding=f"Searching for skills related to: {request.query}",
    )


@router.post("/recommendations", response_model=RecommendSkillsResponse)
async def recommend_skills(
    request: RecommendSkillsRequest,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> RecommendSkillsResponse:
    """Get skill recommendations for a task.

    Uses AI to analyze the task and recommend relevant skills.
    """
    # TODO: Implement AI-based recommendations
    # For now, return top skills from a basic search
    skills = await skill_repo.list(
        search=request.task_description[:50],  # Use first 50 chars as search
        include_public=True,
        limit=request.max_skills,
    )

    return RecommendSkillsResponse(
        recommendations=[
            SkillMatchSchema(
                skill=_to_summary(s),
                relevance_score=0.7,
                match_reason="Potential match based on task description",
            )
            for s in skills
        ],
        reasoning=f"Found {len(skills)} potentially relevant skills for your task.",
    )


# ==================== Testing ====================


@router.post("/{skill_id}/test", response_model=TestSkillResponse)
async def test_skill(
    skill_id: str,
    request: TestSkillRequest,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> TestSkillResponse:
    """Test a skill with sample input.

    Generates the context injection that would be added to an agent's prompt.
    """
    skill = await skill_repo.get(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )

    start_time = time.time()

    # Build the context injection
    enhanced_prompt = skill.build_context_injection(request.parameters)

    execution_time_ms = (time.time() - start_time) * 1000

    # Estimate token count (rough approximation: 1 token ≈ 4 chars)
    token_count = len(enhanced_prompt) // 4

    # Identify sections included
    sections = []
    if skill.definition.capability.expertise.terminology:
        sections.append("terminology")
    if skill.definition.capability.expertise.reasoning_patterns:
        sections.append("reasoning_patterns")
    if skill.definition.capability.expertise.examples:
        sections.append("examples")
    if skill.definition.resources.get_reference_files():
        sections.append("reference_files")
    if skill.definition.resources.get_template_files():
        sections.append("template_files")
    if skill.definition.resources.code_snippets:
        sections.append("code_snippets")
    if skill.definition.prompts.system_enhancement:
        sections.append("system_enhancement")

    return TestSkillResponse(
        enhanced_prompt=enhanced_prompt,
        prompt_token_count=token_count,
        execution_time_ms=execution_time_ms,
        preview_sections=sections,
    )


@router.post("/preview", response_model=PreviewSkillResponse)
async def preview_skill(
    request: PreviewSkillRequest,
    current_user: CurrentUser,
) -> PreviewSkillResponse:
    """Preview a skill without saving.

    Generates the context injection for a skill definition without persisting it.
    """
    start_time = time.time()

    # Convert to domain model and build context
    definition = SkillDefinition.from_dict(request.definition.model_dump())

    # Create a temporary skill to use build_context_injection
    from src.skills.models import Skill

    temp_skill = Skill(
        id="preview",
        tenant_id="preview",
        name=request.definition.metadata.name,
        description="Preview skill",
        category=SkillCategory(request.definition.metadata.category.value),
        tags=request.definition.metadata.tags,
        definition=definition,
    )

    enhanced_prompt = temp_skill.build_context_injection(request.parameters)

    execution_time_ms = (time.time() - start_time) * 1000
    token_count = len(enhanced_prompt) // 4

    return PreviewSkillResponse(
        enhanced_prompt=enhanced_prompt,
        prompt_token_count=token_count,
        execution_time_ms=execution_time_ms,
    )


# ==================== Versioning ====================


@router.get("/{skill_id}/versions", response_model=SkillVersionsResponse)
async def list_skill_versions(
    skill_id: str,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> SkillVersionsResponse:
    """List version history for a skill."""
    # First check skill exists
    skill = await skill_repo.get(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )

    versions = await skill_repo.get_versions(skill_id)

    return SkillVersionsResponse(
        versions=[
            SkillVersionSchema(
                version=v["version"],
                changelog=v["changelog"],
                created_at=v["created_at"],
            )
            for v in versions
        ],
        current_version=skill.version,
    )


@router.post("/{skill_id}/versions/{version}/rollback", response_model=SkillResponse)
async def rollback_skill_version(
    skill_id: str,
    version: int,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> SkillResponse:
    """Rollback a skill to a previous version."""
    skill = await skill_repo.rollback_to_version(skill_id, version)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' or version {version} not found",
        )

    return _to_response(skill)


# ==================== Marketplace ====================


@router.get("/marketplace", response_model=MarketplaceListResponse)
async def browse_marketplace(
    current_user: CurrentUser,
    category: Optional[SkillCategoryEnum] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    search: Optional[str] = Query(None),
    sort_by: str = Query("popular", description="popular, recent, rating"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> MarketplaceListResponse:
    """Browse public skills in the marketplace."""
    # Parse tags if provided
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    # Get public skills only
    skills = await skill_repo.list(
        category=SkillCategory(category.value) if category else None,
        tags=tag_list,
        status=SkillStatus.PUBLISHED,
        search=search,
        include_public=True,
        limit=limit,
        offset=offset,
    )

    # Filter to only public skills
    public_skills = [s for s in skills if s.is_public]

    # Get unique categories and popular tags
    categories = list(set(s.category.value for s in public_skills))
    all_tags = []
    for s in public_skills:
        all_tags.extend(s.tags)
    popular_tags = list(set(all_tags))[:20]  # Top 20 tags

    return MarketplaceListResponse(
        skills=[
            MarketplaceSkillSchema(
                id=s.id,
                marketplace_id=s.id,  # Use skill ID as marketplace ID for now
                name=s.name,
                description=s.description,
                category=s.category.value,
                tags=s.tags,
                version=s.version,
                rating_avg=s.rating_avg,
                rating_count=s.rating_count,
                install_count=s.install_count,
                author=s.created_by,
                created_at=s.created_at,
            )
            for s in public_skills
        ],
        total=len(public_skills),
        categories=categories,
        popular_tags=popular_tags,
    )


@router.post("/{skill_id}/publish", response_model=PublishSkillResponse)
async def publish_skill(
    skill_id: str,
    request: PublishSkillRequest,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> PublishSkillResponse:
    """Publish a skill to the marketplace."""
    skill = await skill_repo.publish_to_marketplace(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )

    return PublishSkillResponse(
        marketplace_id=skill.id,
        status="published",
    )


@router.post("/marketplace/{marketplace_id}/import", response_model=ImportSkillResponse)
async def import_skill(
    marketplace_id: str,
    request: ImportSkillRequest,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> ImportSkillResponse:
    """Import a skill from the marketplace to your workspace."""
    # Get the marketplace skill
    source_skill = await skill_repo.get(marketplace_id)
    if not source_skill or not source_skill.is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Marketplace skill '{marketplace_id}' not found",
        )

    # Create a copy for the user
    imported_skill = await skill_repo.create(
        name=request.customize_name or source_skill.name,
        description=source_skill.description,
        category=source_skill.category,
        tags=source_skill.tags,
        definition=source_skill.definition,
        created_by=current_user.id,
    )

    return ImportSkillResponse(
        skill_id=imported_skill.id,
        original_marketplace_id=marketplace_id,
        status="imported",
    )


@router.post("/marketplace/{marketplace_id}/rate", response_model=RateSkillResponse)
async def rate_skill(
    marketplace_id: str,
    request: RateSkillRequest,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> RateSkillResponse:
    """Rate a marketplace skill."""
    # TODO: Implement rating storage and aggregation
    # For now, return a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Skill rating is coming soon.",
    )


# ==================== Stats ====================


@router.get("/{skill_id}/stats", response_model=SkillStatsResponse)
async def get_skill_stats(
    skill_id: str,
    current_user: CurrentUser,
    skill_repo: SkillRepository = Depends(get_skill_repository),
) -> SkillStatsResponse:
    """Get execution statistics for a skill."""
    # Check skill exists
    skill = await skill_repo.get(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found",
        )

    stats = await skill_repo.get_stats(skill_id)

    return SkillStatsResponse(
        total_executions=stats["total_executions"],
        success_rate=stats["success_rate"],
        avg_duration_ms=stats["avg_duration_ms"],
    )
