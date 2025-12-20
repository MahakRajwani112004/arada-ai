"""Tool binding configuration."""
from typing import Any, Dict

from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Tool binding configuration."""

    tool_id: str = Field(
        ...,
        description="Unique tool identifier",
    )
    enabled: bool = Field(
        default=True,
        description="Whether tool is enabled",
    )
    requires_confirmation: bool = Field(
        default=False,
        description="Require user confirmation before execution",
    )
    timeout_seconds: int = Field(
        default=30,
        gt=0,
        description="Tool execution timeout",
    )
    retry_count: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Number of retries on failure",
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific configuration",
    )
