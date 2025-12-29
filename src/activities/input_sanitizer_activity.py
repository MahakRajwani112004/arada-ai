"""Input Sanitization Activity for Temporal workflows.

Sanitizes user input and conversation history to protect against
prompt injection attacks before processing by agents.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List

from temporalio import activity

from src.agents.quality import InputSanitizer, SanitizationResult


@dataclass
class SanitizeInputInput:
    """Input for sanitization activity."""

    user_input: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    strict_mode: bool = False
    user_id: str = ""


@dataclass
class SanitizeInputOutput:
    """Output from sanitization activity."""

    sanitized_input: str
    sanitized_history: List[Dict[str, str]]
    is_safe: bool
    threats_detected: List[str]
    blocked: bool = False
    block_reason: str = ""


@activity.defn
async def sanitize_input(input: SanitizeInputInput) -> SanitizeInputOutput:
    """
    Sanitize user input and conversation history.

    This activity:
    1. Checks for prompt injection patterns
    2. Sanitizes dangerous sequences
    3. Returns sanitized input or blocks if threats detected in strict mode

    Args:
        input: Sanitization input with user text and history

    Returns:
        SanitizeInputOutput with sanitized content and threat info
    """
    sanitizer = InputSanitizer(strict_mode=input.strict_mode)

    # Sanitize user input
    input_result = sanitizer.sanitize(input.user_input)

    # Sanitize conversation history
    sanitized_history = sanitizer.sanitize_conversation(input.conversation_history)

    # Collect all threats
    all_threats = list(input_result.threats_detected)
    for msg in sanitized_history:
        if msg.get("threats"):
            all_threats.extend(msg["threats"])

    # Deduplicate threats
    all_threats = list(set(all_threats))

    # Determine if we should block
    blocked = False
    block_reason = ""

    if input.strict_mode and not input_result.is_safe:
        blocked = True
        block_reason = f"Prompt injection detected: {', '.join(input_result.threats_detected)}"

    activity.logger.info(
        f"Input sanitization: is_safe={input_result.is_safe}, "
        f"threats={all_threats}, blocked={blocked}"
    )

    return SanitizeInputOutput(
        sanitized_input=input_result.sanitized_text,
        sanitized_history=sanitized_history,
        is_safe=input_result.is_safe,
        threats_detected=all_threats,
        blocked=blocked,
        block_reason=block_reason,
    )


@dataclass
class SanitizeToolResultInput:
    """Input for tool result sanitization."""

    tool_result: Dict[str, Any]
    user_id: str = ""


@dataclass
class SanitizeToolResultOutput:
    """Output from tool result sanitization."""

    sanitized_result: Dict[str, Any]
    was_modified: bool


@activity.defn
async def sanitize_tool_result(input: SanitizeToolResultInput) -> SanitizeToolResultOutput:
    """
    Sanitize tool execution result before LLM consumption.

    Tool results can contain content that could manipulate the LLM.
    This activity sanitizes such content.

    Args:
        input: Tool result to sanitize

    Returns:
        SanitizeToolResultOutput with sanitized result
    """
    sanitizer = InputSanitizer()

    original_str = str(input.tool_result)
    sanitized = sanitizer.sanitize_tool_result(input.tool_result)
    sanitized_str = str(sanitized)

    was_modified = original_str != sanitized_str

    if was_modified:
        activity.logger.info("Tool result was sanitized")

    return SanitizeToolResultOutput(
        sanitized_result=sanitized,
        was_modified=was_modified,
    )
