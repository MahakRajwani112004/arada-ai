"""Safety and governance configuration."""
from typing import List

from pydantic import BaseModel, Field

from src.models.enums import SafetyLevel


class SafetyConfig(BaseModel):
    """Safety configuration for agent execution."""

    level: SafetyLevel = Field(
        default=SafetyLevel.STANDARD,
        description="Safety level for content filtering",
    )
    blocked_topics: List[str] = Field(
        default_factory=list,
        description="Topics to block in responses",
    )
    blocked_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns to block",
    )
    content_filtering: bool = Field(
        default=True,
        description="Enable content filtering",
    )
    pii_detection: bool = Field(
        default=True,
        description="Enable PII detection",
    )
    hallucination_check: bool = Field(
        default=True,
        description="Enable hallucination checking for RAG",
    )
    max_iterations: int = Field(
        default=10,
        gt=0,
        le=50,
        description="Maximum agent loop iterations",
    )
    timeout_seconds: int = Field(
        default=300,
        gt=0,
        description="Total execution timeout",
    )
    input_max_length: int = Field(
        default=10000,
        gt=0,
        description="Maximum input length in characters",
    )
    block_code_execution: bool = Field(
        default=True,
        description="Block arbitrary code execution",
    )


class GovernanceConfig(BaseModel):
    """Governance configuration for agent execution."""

    audit_logging: bool = Field(
        default=True,
        description="Enable audit logging",
    )
    require_confirmation_for: List[str] = Field(
        default_factory=list,
        description="Actions requiring user confirmation",
    )
    allowed_data_classifications: List[str] = Field(
        default_factory=lambda: ["public", "internal"],
        description="Allowed data classification levels",
    )
    rate_limit_per_minute: int = Field(
        default=60,
        gt=0,
        description="Rate limit per minute",
    )
    cost_limit_per_request: float = Field(
        default=1.0,
        gt=0,
        description="Maximum cost per request in USD",
    )
