"""Safety Check Activities for Temporal workflows."""
import re
from dataclasses import dataclass, field
from typing import List, Optional

from temporalio import activity

from src.models.enums import SafetyLevel


@dataclass
class SafetyCheckInput:
    """Input for safety check activity."""

    content: str
    safety_level: str = "standard"  # low, standard, high, maximum
    blocked_topics: List[str] = field(default_factory=list)
    blocked_patterns: List[str] = field(default_factory=list)


@dataclass
class SafetyCheckOutput:
    """Output from safety check activity."""

    is_safe: bool
    violations: List[str]
    confidence: float
    filtered_content: Optional[str] = None


@activity.defn
async def check_input_safety(input: SafetyCheckInput) -> SafetyCheckOutput:
    """
    Check input content for safety violations.

    This is a basic rule-based check. In production, you might
    integrate with more sophisticated content moderation APIs.
    """
    activity.logger.info(f"Checking input safety: level={input.safety_level}")

    violations = []
    content_lower = input.content.lower()

    # Check blocked topics
    for topic in input.blocked_topics:
        if topic.lower() in content_lower:
            violations.append(f"Blocked topic: {topic}")

    # Check blocked patterns (regex)
    for pattern in input.blocked_patterns:
        try:
            if re.search(pattern, input.content, re.IGNORECASE):
                violations.append(f"Blocked pattern: {pattern}")
        except re.error:
            activity.logger.warning(f"Invalid regex pattern: {pattern}")

    # Basic content checks based on safety level
    safety_level = SafetyLevel(input.safety_level)

    if safety_level in [SafetyLevel.HIGH, SafetyLevel.MAXIMUM]:
        # Stricter checks for high/maximum levels
        suspicious_patterns = [
            r"\b(hack|exploit|bypass|inject)\b",
            r"(?:password|secret|api.?key)\s*[:=]",
        ]
        for pattern in suspicious_patterns:
            if re.search(pattern, input.content, re.IGNORECASE):
                violations.append(f"Suspicious content pattern detected")
                break

    is_safe = len(violations) == 0
    confidence = 1.0 if is_safe else 0.9  # High confidence in violations

    activity.logger.info(
        f"Safety check complete: safe={is_safe}, violations={len(violations)}"
    )

    return SafetyCheckOutput(
        is_safe=is_safe,
        violations=violations,
        confidence=confidence,
    )


@activity.defn
async def check_output_safety(input: SafetyCheckInput) -> SafetyCheckOutput:
    """
    Check output content for safety violations.

    Similar to input check but may apply different rules
    for generated content.
    """
    activity.logger.info(f"Checking output safety: level={input.safety_level}")

    violations = []
    content_lower = input.content.lower()

    # Check blocked topics in output
    for topic in input.blocked_topics:
        if topic.lower() in content_lower:
            violations.append(f"Output contains blocked topic: {topic}")

    # Check for potential data leakage patterns
    sensitive_patterns = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
        r"\b\d{16}\b",  # Credit card pattern
        r"(?:password|secret|key)[\s:=]+\S+",  # Credential patterns
    ]

    safety_level = SafetyLevel(input.safety_level)
    if safety_level in [SafetyLevel.HIGH, SafetyLevel.MAXIMUM]:
        for pattern in sensitive_patterns:
            if re.search(pattern, input.content, re.IGNORECASE):
                violations.append("Potential sensitive data in output")
                break

    is_safe = len(violations) == 0

    activity.logger.info(
        f"Output safety check: safe={is_safe}, violations={len(violations)}"
    )

    return SafetyCheckOutput(
        is_safe=is_safe,
        violations=violations,
        confidence=1.0 if is_safe else 0.85,
    )
