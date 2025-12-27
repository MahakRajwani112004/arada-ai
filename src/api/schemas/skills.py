"""API schemas for skill management, generation, and marketplace."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== Enums ====================


class SkillCategoryEnum(str, Enum):
    """Categories of skills."""

    DOMAIN_EXPERTISE = "domain_expertise"
    DOCUMENT_GENERATION = "document_generation"
    DATA_ANALYSIS = "data_analysis"
    COMMUNICATION = "communication"
    RESEARCH = "research"
    CODING = "coding"
    CUSTOM = "custom"


class SkillStatusEnum(str, Enum):
    """Status of a skill."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class FileTypeEnum(str, Enum):
    """Types of files attached to skills."""

    REFERENCE = "reference"  # Knowledge/context docs
    TEMPLATE = "template"  # Documents to fill in


# ==================== Component Schemas ====================


class TerminologySchema(BaseModel):
    """A domain-specific term with its definition."""

    id: str = Field(..., description="Unique identifier")
    term: str = Field(..., min_length=1, max_length=200, description="The term")
    definition: str = Field(..., min_length=1, max_length=1000, description="Definition")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")


class ReasoningPatternSchema(BaseModel):
    """A step-by-step reasoning framework."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Pattern name")
    steps: List[str] = Field(..., min_length=1, description="Ordered reasoning steps")
    description: Optional[str] = Field(None, max_length=500, description="Pattern description")


class SkillExampleSchema(BaseModel):
    """An input/output example for the skill."""

    id: str = Field(..., description="Unique identifier")
    input: str = Field(..., min_length=1, max_length=2000, description="Example input")
    output: str = Field(..., min_length=1, max_length=5000, description="Example output")
    context: Optional[str] = Field(None, max_length=1000, description="Additional context")


class SkillFileSchema(BaseModel):
    """A file attached to a skill."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=255, description="File name")
    file_type: FileTypeEnum = Field(..., description="reference or template")
    mime_type: str = Field(..., description="MIME type")
    storage_url: str = Field(..., description="Storage URL")
    content_preview: str = Field(..., max_length=2000, description="Content preview for context")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class CodeSnippetSchema(BaseModel):
    """A code snippet included in the skill."""

    id: str = Field(..., description="Unique identifier")
    language: str = Field(..., min_length=1, max_length=50, description="Programming language")
    code: str = Field(..., min_length=1, max_length=10000, description="The code")
    description: Optional[str] = Field(None, max_length=500, description="Description")


class SkillResourcesSchema(BaseModel):
    """Files and code snippets attached to a skill."""

    files: List[SkillFileSchema] = Field(default_factory=list)
    code_snippets: List[CodeSnippetSchema] = Field(default_factory=list)


class SkillParameterSchema(BaseModel):
    """A configurable parameter for the skill."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Parameter name")
    type: str = Field(..., description="string, number, boolean, or select")
    description: Optional[str] = Field(None, max_length=500, description="Parameter description")
    required: bool = Field(False, description="Whether parameter is required")
    default_value: Optional[Any] = Field(None, description="Default value")
    options: Optional[List[str]] = Field(None, description="Options for select type")
    validation: Optional[Dict[str, Any]] = Field(None, description="Validation rules")


class SkillExpertiseSchema(BaseModel):
    """Domain expertise contained in the skill."""

    domain: str = Field(..., min_length=1, max_length=200, description="Domain name")
    terminology: List[TerminologySchema] = Field(default_factory=list)
    reasoning_patterns: List[ReasoningPatternSchema] = Field(default_factory=list)
    examples: List[SkillExampleSchema] = Field(default_factory=list)


class SkillCapabilitySchema(BaseModel):
    """The capability definition of a skill."""

    expertise: SkillExpertiseSchema


class SkillPromptsSchema(BaseModel):
    """Prompt templates for the skill."""

    system_enhancement: str = Field(..., max_length=10000, description="System prompt enhancement")
    variables: List[str] = Field(default_factory=list, description="Extracted template variables")


class SkillMetadataSchema(BaseModel):
    """Metadata for a skill."""

    id: str = Field("", description="Skill ID (assigned by system)")
    name: str = Field(..., min_length=1, max_length=200, description="Skill name")
    version: str = Field("1.0.0", description="Semantic version")
    category: SkillCategoryEnum = Field(..., description="Skill category")
    tags: List[str] = Field(default_factory=list, description="Skill tags")


class SkillDefinitionSchema(BaseModel):
    """Complete definition of a skill."""

    metadata: SkillMetadataSchema
    capability: SkillCapabilitySchema
    resources: SkillResourcesSchema = Field(default_factory=SkillResourcesSchema)
    parameters: List[SkillParameterSchema] = Field(default_factory=list)
    prompts: SkillPromptsSchema = Field(default_factory=lambda: SkillPromptsSchema(system_enhancement=""))


# ==================== CRUD Schemas ====================


class CreateSkillRequest(BaseModel):
    """Request to create a new skill."""

    name: str = Field(..., min_length=1, max_length=200, description="Skill name")
    description: str = Field(..., min_length=1, max_length=1000, description="Description")
    category: SkillCategoryEnum = Field(..., description="Skill category")
    tags: List[str] = Field(default_factory=list, description="Skill tags")
    definition: SkillDefinitionSchema = Field(..., description="Full skill definition")


class UpdateSkillRequest(BaseModel):
    """Request to update a skill."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    category: Optional[SkillCategoryEnum] = None
    tags: Optional[List[str]] = None
    definition: Optional[SkillDefinitionSchema] = None
    status: Optional[SkillStatusEnum] = None
    changelog: Optional[str] = Field(None, max_length=500, description="Change description")


class SkillResponse(BaseModel):
    """Response containing skill details."""

    id: str
    tenant_id: str
    name: str
    description: str
    category: str
    tags: List[str]
    definition: Dict[str, Any]
    version: int
    status: str
    is_public: bool
    rating_avg: Optional[float]
    rating_count: int
    install_count: int
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class SkillSummaryResponse(BaseModel):
    """Summary of a skill for listing."""

    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    version: int
    status: str
    is_public: bool
    rating_avg: Optional[float]
    rating_count: int
    created_at: datetime
    updated_at: datetime


class SkillListResponse(BaseModel):
    """Response containing list of skills."""

    skills: List[SkillSummaryResponse]
    total: int


# ==================== AI Generation Schemas ====================


class GenerateSkillRequest(BaseModel):
    """Request to generate a skill from natural language."""

    prompt: str = Field(..., min_length=10, max_length=2000, description="Natural language description")
    domain: Optional[str] = Field(None, max_length=200, description="Target domain")
    context: Optional[str] = Field(None, max_length=2000, description="Additional context")
    include_examples: bool = Field(True, description="Generate example input/outputs")
    include_terminology: bool = Field(True, description="Generate domain terminology")


class GenerateSkillResponse(BaseModel):
    """Response from AI skill generation."""

    skill: SkillDefinitionSchema
    explanation: str = Field(..., description="AI explanation of the generated skill")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    warnings: List[str] = Field(default_factory=list)


class RefineSkillRequest(BaseModel):
    """Request to refine a generated skill."""

    skill: SkillDefinitionSchema = Field(..., description="Current skill definition")
    feedback: str = Field(..., min_length=1, max_length=2000, description="User feedback")
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Areas to focus on: terminology, patterns, examples, prompts"
    )


class RefineSkillResponse(BaseModel):
    """Response from skill refinement."""

    skill: SkillDefinitionSchema
    changes_made: List[str] = Field(default_factory=list, description="Description of changes")
    explanation: str


# ==================== Search & Discovery Schemas ====================


class SearchSkillsRequest(BaseModel):
    """Request to search skills semantically."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    categories: List[SkillCategoryEnum] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    include_public: bool = Field(True, description="Include marketplace skills")
    limit: int = Field(20, ge=1, le=100)


class SkillMatchSchema(BaseModel):
    """A skill match from semantic search."""

    skill: SkillSummaryResponse
    relevance_score: float = Field(..., ge=0, le=1)
    match_reason: str


class SearchSkillsResponse(BaseModel):
    """Response from skill search."""

    matches: List[SkillMatchSchema]
    query_understanding: str = Field(..., description="How the query was interpreted")


class RecommendSkillsRequest(BaseModel):
    """Request skill recommendations for a task."""

    task_description: str = Field(..., min_length=1, max_length=2000)
    agent_context: Optional[str] = Field(None, max_length=1000, description="Agent context")
    max_skills: int = Field(3, ge=1, le=10)


class RecommendSkillsResponse(BaseModel):
    """Response with skill recommendations."""

    recommendations: List[SkillMatchSchema]
    reasoning: str


# ==================== Testing Schemas ====================


class TestSkillRequest(BaseModel):
    """Request to test a skill with sample input."""

    input: str = Field(..., min_length=1, max_length=5000, description="Test input")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameter values")


class TestSkillResponse(BaseModel):
    """Response from skill test."""

    enhanced_prompt: str = Field(..., description="The generated context injection")
    prompt_token_count: int = Field(..., description="Token count of injected context")
    execution_time_ms: float
    preview_sections: List[str] = Field(
        default_factory=list,
        description="Sections included in the injection"
    )


class PreviewSkillRequest(BaseModel):
    """Request to preview a skill without saving."""

    definition: SkillDefinitionSchema
    input: str = Field(..., min_length=1, max_length=5000)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class PreviewSkillResponse(BaseModel):
    """Response from skill preview."""

    enhanced_prompt: str
    prompt_token_count: int
    execution_time_ms: float


# ==================== Versioning Schemas ====================


class SkillVersionSchema(BaseModel):
    """A version in the skill's history."""

    version: int
    changelog: str
    created_at: datetime


class SkillVersionsResponse(BaseModel):
    """Response containing version history."""

    versions: List[SkillVersionSchema]
    current_version: int


class RollbackSkillRequest(BaseModel):
    """Request to rollback to a previous version."""

    version: int = Field(..., ge=1, description="Version to rollback to")


# ==================== Marketplace Schemas ====================


class MarketplaceSkillSchema(BaseModel):
    """A skill in the marketplace."""

    id: str
    marketplace_id: str
    name: str
    description: str
    category: str
    tags: List[str]
    version: int
    rating_avg: Optional[float]
    rating_count: int
    install_count: int
    author: Optional[str]
    created_at: datetime
    preview_available: bool = True


class MarketplaceListResponse(BaseModel):
    """Response containing marketplace skills."""

    skills: List[MarketplaceSkillSchema]
    total: int
    categories: List[str] = Field(default_factory=list, description="Available categories")
    popular_tags: List[str] = Field(default_factory=list, description="Popular tags")


class PublishSkillRequest(BaseModel):
    """Request to publish a skill to marketplace."""

    make_public: bool = Field(True, description="Make skill publicly visible")


class PublishSkillResponse(BaseModel):
    """Response after publishing to marketplace."""

    marketplace_id: str
    url: Optional[str] = None
    status: str


class ImportSkillRequest(BaseModel):
    """Request to import a skill from marketplace."""

    marketplace_id: str = Field(..., description="Marketplace skill ID")
    customize_name: Optional[str] = Field(None, max_length=200, description="Custom name for imported skill")


class ImportSkillResponse(BaseModel):
    """Response after importing from marketplace."""

    skill_id: str
    original_marketplace_id: str
    status: str


class RateSkillRequest(BaseModel):
    """Request to rate a marketplace skill."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    review: Optional[str] = Field(None, max_length=1000, description="Optional review text")


class RateSkillResponse(BaseModel):
    """Response after rating a skill."""

    new_average: float
    total_ratings: int


# ==================== File Management Schemas ====================


class SkillFileUploadResponse(BaseModel):
    """Response after uploading a file to a skill."""

    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type: reference or template")
    mime_type: str = Field(..., description="MIME type of the file")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    preview_length: int = Field(..., ge=0, description="Length of extracted preview")
    message: str = Field(..., description="Success message")


class SkillFileInfoResponse(BaseModel):
    """Information about a single skill file."""

    id: str = Field(..., description="Unique file identifier")
    name: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type: reference or template")
    mime_type: str = Field(..., description="MIME type of the file")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    uploaded_at: str = Field(..., description="Upload timestamp (ISO format)")


class SkillFilesListResponse(BaseModel):
    """Response listing all files attached to a skill."""

    files: List[SkillFileInfoResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0, description="Total number of files")


class SkillFileDownloadResponse(BaseModel):
    """Response with a presigned download URL for a skill file."""

    download_url: str = Field(..., description="Presigned URL for file download")
    filename: str = Field(..., description="Original filename")
    expires_in_seconds: int = Field(..., description="URL expiration time in seconds")


class SupportedFileTypesResponse(BaseModel):
    """Response listing supported file types for skill uploads."""

    extensions: List[str] = Field(..., description="List of supported file extensions")
    categories: Dict[str, List[str]] = Field(..., description="Extensions grouped by category")
    max_size_mb: float = Field(..., description="Maximum file size in megabytes")


# ==================== Stats Schemas ====================


class SkillStatsResponse(BaseModel):
    """Execution statistics for a skill."""

    total_executions: int
    success_rate: float
    avg_duration_ms: float
