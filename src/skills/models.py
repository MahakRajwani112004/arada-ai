"""Skill system data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SkillCategory(str, Enum):
    """Categories of skills."""

    DOMAIN_EXPERTISE = "domain_expertise"
    DOCUMENT_GENERATION = "document_generation"
    DATA_ANALYSIS = "data_analysis"
    COMMUNICATION = "communication"
    RESEARCH = "research"
    CODING = "coding"
    CUSTOM = "custom"


class FileType(str, Enum):
    """Types of files that can be attached to skills."""

    REFERENCE = "reference"  # Knowledge/context docs
    TEMPLATE = "template"  # Documents to fill in


class SkillStatus(str, Enum):
    """Status of a skill."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class Terminology:
    """A domain-specific term with its definition."""

    id: str
    term: str
    definition: str
    aliases: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "term": self.term,
            "definition": self.definition,
            "aliases": self.aliases,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Terminology":
        return cls(
            id=data["id"],
            term=data["term"],
            definition=data["definition"],
            aliases=data.get("aliases", []),
        )


@dataclass
class ReasoningPattern:
    """A step-by-step reasoning framework."""

    id: str
    name: str
    steps: List[str]
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "steps": self.steps,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReasoningPattern":
        return cls(
            id=data["id"],
            name=data["name"],
            steps=data["steps"],
            description=data.get("description"),
        )


@dataclass
class SkillExample:
    """An input/output example for the skill."""

    id: str
    input: str
    output: str
    context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "input": self.input,
            "output": self.output,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillExample":
        return cls(
            id=data["id"],
            input=data["input"],
            output=data["output"],
            context=data.get("context"),
        )


@dataclass
class SkillFile:
    """A file attached to a skill (reference or template)."""

    id: str
    name: str
    file_type: FileType
    mime_type: str
    storage_url: str
    content_preview: str  # First ~2000 chars for context injection
    size_bytes: int
    uploaded_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "file_type": self.file_type.value,
            "mime_type": self.mime_type,
            "storage_url": self.storage_url,
            "content_preview": self.content_preview,
            "size_bytes": self.size_bytes,
            "uploaded_at": self.uploaded_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillFile":
        uploaded_at = data.get("uploaded_at")
        if isinstance(uploaded_at, str):
            uploaded_at = datetime.fromisoformat(uploaded_at)
        elif uploaded_at is None:
            uploaded_at = datetime.now()

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            file_type=FileType(data.get("file_type", "reference")),
            mime_type=data.get("mime_type", "application/octet-stream"),
            storage_url=data.get("storage_url", ""),
            content_preview=data.get("content_preview"),
            size_bytes=data.get("size_bytes", 0),
            uploaded_at=uploaded_at,
        )


@dataclass
class CodeSnippet:
    """A code snippet included in the skill."""

    id: str
    language: str
    code: str
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "language": self.language,
            "code": self.code,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeSnippet":
        return cls(
            id=data["id"],
            language=data["language"],
            code=data["code"],
            description=data.get("description"),
        )


@dataclass
class SkillResources:
    """Files and code snippets attached to a skill."""

    files: List[SkillFile] = field(default_factory=list)
    code_snippets: List[CodeSnippet] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files": [f.to_dict() for f in self.files],
            "code_snippets": [s.to_dict() for s in self.code_snippets],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillResources":
        return cls(
            files=[SkillFile.from_dict(f) for f in data.get("files", [])],
            code_snippets=[
                CodeSnippet.from_dict(s) for s in data.get("code_snippets", [])
            ],
        )

    def get_reference_files(self) -> List[SkillFile]:
        """Get files marked as reference (knowledge/context)."""
        return [f for f in self.files if f.file_type == FileType.REFERENCE]

    def get_template_files(self) -> List[SkillFile]:
        """Get files marked as templates."""
        return [f for f in self.files if f.file_type == FileType.TEMPLATE]


@dataclass
class SkillParameter:
    """A configurable parameter for the skill."""

    id: str
    name: str
    type: str  # string, number, boolean, select
    description: Optional[str] = None
    required: bool = False
    default_value: Optional[Any] = None
    options: Optional[List[str]] = None  # For select type
    validation: Optional[Dict[str, Any]] = None  # min, max, pattern

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "options": self.options,
            "validation": self.validation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillParameter":
        return cls(
            id=data["id"],
            name=data["name"],
            type=data["type"],
            description=data.get("description"),
            required=data.get("required", False),
            default_value=data.get("default_value"),
            options=data.get("options"),
            validation=data.get("validation"),
        )


@dataclass
class SkillExpertise:
    """Domain expertise contained in the skill."""

    domain: str
    terminology: List[Terminology] = field(default_factory=list)
    reasoning_patterns: List[ReasoningPattern] = field(default_factory=list)
    examples: List[SkillExample] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "terminology": [t.to_dict() for t in self.terminology],
            "reasoning_patterns": [r.to_dict() for r in self.reasoning_patterns],
            "examples": [e.to_dict() for e in self.examples],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillExpertise":
        return cls(
            domain=data["domain"],
            terminology=[
                Terminology.from_dict(t) for t in data.get("terminology", [])
            ],
            reasoning_patterns=[
                ReasoningPattern.from_dict(r)
                for r in data.get("reasoning_patterns", [])
            ],
            examples=[SkillExample.from_dict(e) for e in data.get("examples", [])],
        )


@dataclass
class SkillCapability:
    """The capability definition of a skill."""

    expertise: SkillExpertise

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expertise": self.expertise.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillCapability":
        return cls(
            expertise=SkillExpertise.from_dict(data["expertise"]),
        )


@dataclass
class SkillPrompts:
    """Prompt templates for the skill."""

    system_enhancement: str
    variables: List[str] = field(default_factory=list)  # Extracted from template

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_enhancement": self.system_enhancement,
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillPrompts":
        return cls(
            system_enhancement=data["system_enhancement"],
            variables=data.get("variables", []),
        )


@dataclass
class SkillMetadata:
    """Metadata for a skill."""

    id: str
    name: str
    version: str
    category: SkillCategory
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "category": self.category.value,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillMetadata":
        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            category=SkillCategory(data["category"]),
            tags=data.get("tags", []),
        )


@dataclass
class SkillDefinition:
    """Complete definition of a skill (stored as JSON in database)."""

    metadata: SkillMetadata
    capability: SkillCapability
    resources: SkillResources = field(default_factory=SkillResources)
    parameters: List[SkillParameter] = field(default_factory=list)
    prompts: SkillPrompts = field(default_factory=lambda: SkillPrompts(""))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "capability": self.capability.to_dict(),
            "resources": self.resources.to_dict(),
            "parameters": [p.to_dict() for p in self.parameters],
            "prompts": self.prompts.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillDefinition":
        return cls(
            metadata=SkillMetadata.from_dict(data["metadata"]),
            capability=SkillCapability.from_dict(data["capability"]),
            resources=SkillResources.from_dict(data.get("resources", {})),
            parameters=[
                SkillParameter.from_dict(p) for p in data.get("parameters", [])
            ],
            prompts=SkillPrompts.from_dict(data.get("prompts", {"system_enhancement": ""})),
        )


@dataclass
class Skill:
    """A complete skill with all metadata and definition."""

    id: str
    tenant_id: str
    name: str
    description: str
    category: SkillCategory
    tags: List[str]
    definition: SkillDefinition
    version: int = 1
    status: SkillStatus = SkillStatus.DRAFT
    is_public: bool = False
    rating_avg: Optional[float] = None
    rating_count: int = 0
    install_count: int = 0
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "tags": self.tags,
            "definition": self.definition.to_dict(),
            "version": self.version,
            "status": self.status.value,
            "is_public": self.is_public,
            "rating_avg": self.rating_avg,
            "rating_count": self.rating_count,
            "install_count": self.install_count,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            id=data["id"],
            tenant_id=data["tenant_id"],
            name=data["name"],
            description=data["description"],
            category=SkillCategory(data["category"]),
            tags=data.get("tags", []),
            definition=SkillDefinition.from_dict(data["definition"]),
            version=data.get("version", 1),
            status=SkillStatus(data.get("status", "draft")),
            is_public=data.get("is_public", False),
            rating_avg=data.get("rating_avg"),
            rating_count=data.get("rating_count", 0),
            install_count=data.get("install_count", 0),
            created_by=data.get("created_by"),
            created_at=datetime.fromisoformat(data["created_at"])
            if isinstance(data.get("created_at"), str)
            else data.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if isinstance(data.get("updated_at"), str)
            else data.get("updated_at", datetime.utcnow()),
        )

    def build_context_injection(self, parameter_values: Dict[str, Any] = None) -> str:
        """
        Build the context string to inject into an agent's system prompt.

        Args:
            parameter_values: Override values for skill parameters

        Returns:
            Formatted context string for prompt injection
        """
        params = parameter_values or {}

        # Apply defaults for missing parameters
        for param in self.definition.parameters:
            if param.name not in params and param.default_value is not None:
                params[param.name] = param.default_value

        sections = []

        # Skill header
        sections.append(f"## ACTIVE SKILL: {self.name}")
        sections.append(f"Domain: {self.definition.capability.expertise.domain}")
        sections.append("")

        # Terminology
        terminology = self.definition.capability.expertise.terminology
        if terminology:
            sections.append("### Domain Terminology")
            for term in terminology:
                aliases = f" (also: {', '.join(term.aliases)})" if term.aliases else ""
                sections.append(f"- **{term.term}**{aliases}: {term.definition}")
            sections.append("")

        # Reasoning patterns
        patterns = self.definition.capability.expertise.reasoning_patterns
        if patterns:
            sections.append("### Reasoning Frameworks")
            for pattern in patterns:
                sections.append(f"**{pattern.name}**")
                if pattern.description:
                    sections.append(f"{pattern.description}")
                for i, step in enumerate(pattern.steps, 1):
                    sections.append(f"{i}. {step}")
                sections.append("")

        # Examples
        examples = self.definition.capability.expertise.examples
        if examples:
            sections.append("### Examples")
            for example in examples:
                sections.append(f"Input: {example.input}")
                sections.append(f"Output: {example.output}")
                sections.append("")

        # Reference files (knowledge)
        reference_files = self.definition.resources.get_reference_files()
        if reference_files:
            sections.append("### Reference Knowledge")
            for file in reference_files:
                sections.append(f"**{file.name}**:")
                if file.content_preview:
                    sections.append(file.content_preview)
                sections.append("")

        # Template files
        template_files = self.definition.resources.get_template_files()
        if template_files:
            sections.append("### Document Templates")
            sections.append("Use the fill_docx_template tool to generate documents from these templates.")
            sections.append("The tool preserves all formatting, headers, footers, and styles.")
            sections.append("")
            for file in template_files:
                sections.append(f"**Template: {file.name}**")
                sections.append(f"- Storage Key: `{file.storage_url}`")
                sections.append(f"- To use: `fill_docx_template(template_storage_key=\"{file.storage_url}\", values={{...}}, output_filename=\"...\")`")
                sections.append("")
                if file.content_preview:
                    sections.append("Template preview (placeholders shown in {{UPPERCASE}}):")
                    sections.append(file.content_preview)
                sections.append("")

        # Code snippets
        snippets = self.definition.resources.code_snippets
        if snippets:
            sections.append("### Code References")
            for snippet in snippets:
                desc = f" - {snippet.description}" if snippet.description else ""
                sections.append(f"**{snippet.language}{desc}**:")
                sections.append(f"```{snippet.language}")
                sections.append(snippet.code)
                sections.append("```")
                sections.append("")

        # System enhancement prompt
        if self.definition.prompts.system_enhancement:
            sections.append("### Guidelines")
            # Substitute parameters in the prompt
            prompt = self.definition.prompts.system_enhancement
            for key, value in params.items():
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
            sections.append(prompt)

        return "\n".join(sections)
