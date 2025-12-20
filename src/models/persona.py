"""Agent persona configuration - role, goal, instructions."""
from typing import List, Optional

from pydantic import BaseModel, Field


class AgentRole(BaseModel):
    """WHO the agent is - defines identity and expertise."""

    title: str = Field(
        ...,
        description="Agent's role title, e.g., 'Senior Data Analyst'",
    )
    expertise: List[str] = Field(
        default_factory=list,
        description="Areas of expertise",
    )
    personality: List[str] = Field(
        default_factory=list,
        description="Personality traits",
    )
    communication_style: str = Field(
        default="professional",
        description="Communication style: professional, casual, technical",
    )


class AgentGoal(BaseModel):
    """WHAT the agent achieves - defines objectives and constraints."""

    objective: str = Field(
        ...,
        description="Primary goal of the agent",
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Constraints the agent must follow",
    )
    success_indicators: List[str] = Field(
        default_factory=list,
        description="What defines success",
    )


class AgentInstructions(BaseModel):
    """HOW the agent operates - defines behavior and rules."""

    steps: List[str] = Field(
        default_factory=list,
        description="Step-by-step instructions",
    )
    rules: List[str] = Field(
        default_factory=list,
        description="Rules to follow",
    )
    prohibited: List[str] = Field(
        default_factory=list,
        description="Things the agent must NOT do",
    )
    output_format: Optional[str] = Field(
        default=None,
        description="Expected output format",
    )


class AgentExample(BaseModel):
    """Few-shot example for agent behavior."""

    input: str = Field(
        ...,
        description="Example input",
    )
    output: str = Field(
        ...,
        description="Expected output",
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Explanation of why this output",
    )
