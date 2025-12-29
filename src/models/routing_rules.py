"""Routing rules for hybrid orchestrator mode.

Enables explicit pattern-based routing to agents before falling back to LLM decision.
This provides deterministic routing for common cases while allowing flexibility for edge cases.
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RoutingCondition(str, Enum):
    """Types of routing conditions."""

    CONTAINS = "contains"  # Input contains keyword (case-insensitive)
    STARTS_WITH = "starts_with"  # Input starts with pattern
    ENDS_WITH = "ends_with"  # Input ends with pattern
    REGEX = "regex"  # Full regex pattern match
    EXACT = "exact"  # Exact match (case-insensitive)


class RoutingRule(BaseModel):
    """A single routing rule for deterministic agent selection."""

    id: str = Field(..., description="Unique rule ID for tracking")

    condition: RoutingCondition = Field(
        default=RoutingCondition.CONTAINS,
        description="Type of pattern matching to use",
    )

    pattern: str = Field(
        ...,
        description="Pattern to match against user input",
    )

    target_agent: str = Field(
        ...,
        description="Agent ID to route to when pattern matches",
    )

    priority: int = Field(
        default=0,
        description="Higher priority rules are checked first",
    )

    description: Optional[str] = Field(
        None,
        description="Human-readable description of what this rule handles",
    )

    enabled: bool = Field(
        default=True,
        description="Whether this rule is active",
    )


class RoutingRules(BaseModel):
    """Collection of routing rules for hybrid orchestrator mode."""

    rules: List[RoutingRule] = Field(
        default_factory=list,
        description="List of routing rules, checked in priority order",
    )

    fallback_to_llm: bool = Field(
        default=True,
        description="If no rule matches, use LLM to decide routing",
    )

    default_agent: Optional[str] = Field(
        None,
        description="Default agent if no match and LLM fallback is disabled",
    )

    case_sensitive: bool = Field(
        default=False,
        description="Whether pattern matching is case-sensitive",
    )

    def get_sorted_rules(self) -> List[RoutingRule]:
        """Get rules sorted by priority (highest first), excluding disabled."""
        return sorted(
            [r for r in self.rules if r.enabled],
            key=lambda r: r.priority,
            reverse=True,
        )
