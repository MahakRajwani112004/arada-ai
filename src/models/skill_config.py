"""Skill configuration for agents."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SkillConfig(BaseModel):
    """Configuration for a skill attached to an agent."""

    skill_id: str = Field(..., description="ID of the skill to use")
    enabled: bool = Field(default=True, description="Whether skill is enabled")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameter overrides for this skill",
    )
    priority: int = Field(
        default=0,
        description="Priority for skill selection (higher = more important)",
    )

    model_config = {"extra": "forbid"}
