"""Input sanitization to protect against prompt injection.

This module provides protection against:
1. Instruction override attacks ("ignore previous instructions")
2. System prompt extraction attempts
3. Role/persona manipulation
4. Hidden/encoded instructions
5. Malicious tool result injection
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SanitizationResult:
    """Result of input sanitization."""

    is_safe: bool
    sanitized_text: str
    threats_detected: List[str] = field(default_factory=list)
    original_text: str = ""
    confidence: float = 1.0


class InputSanitizer:
    """
    Sanitizes user inputs to prevent prompt injection attacks.

    This is a defense-in-depth layer that:
    1. Detects known injection patterns
    2. Sanitizes potentially dangerous content
    3. Logs threats for monitoring

    Usage:
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize(user_input)
        if not result.is_safe:
            # Handle threat - reject or use sanitized version
            logger.warning(f"Threats detected: {result.threats_detected}")
    """

    # Patterns that indicate instruction override attempts
    INSTRUCTION_OVERRIDE_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?|guidelines?|context)",
        r"(?i)disregard\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?|guidelines?)",
        r"(?i)forget\s+(all\s+)?(previous|prior|your)\s+(instructions?|rules?|training)",
        r"(?i)override\s+(your\s+)?(instructions?|rules?|guidelines?)",
        r"(?i)new\s+instructions?:\s*",
        r"(?i)you\s+are\s+now\s+(?!going|about)",  # "you are now X" but not "you are now going to"
        r"(?i)from\s+now\s+on,?\s+you\s+(are|will|must|should)",
        r"(?i)stop\s+being\s+an?\s+ai",
        r"(?i)pretend\s+(to\s+be|you\s+are|you're)",
    ]

    # Patterns for system prompt extraction
    PROMPT_EXTRACTION_PATTERNS = [
        r"(?i)what\s+(is|are)\s+your\s+(system\s+)?(prompt|instructions?|rules?|guidelines?)",
        r"(?i)show\s+(me\s+)?your\s+(system\s+)?(prompt|instructions?|configuration)",
        r"(?i)output\s+your\s+(initial|system|original)\s+(prompt|instructions?|message)",
        r"(?i)repeat\s+your\s+(system\s+)?(prompt|instructions?|message)",
        r"(?i)print\s+your\s+(system\s+)?(prompt|instructions?)",
        r"(?i)reveal\s+your\s+(system\s+)?(prompt|instructions?|programming)",
        r"(?i)display\s+your\s+(hidden|secret|internal)\s+(prompt|instructions?)",
    ]

    # Patterns for role manipulation
    ROLE_MANIPULATION_PATTERNS = [
        r"(?i)you\s+are\s+(dan|dude|evil|unfiltered|jailbroken)",
        r"(?i)act\s+as\s+if\s+you\s+have\s+no\s+(restrictions?|filters?|limitations?|ethics?)",
        r"(?i)roleplay\s+as\s+an?\s+(evil|unrestricted|unfiltered)",
        r"(?i)pretend\s+you\s+have\s+no\s+(ethical|safety|content)\s+(guidelines?|filters?)",
        r"(?i)respond\s+without\s+(any\s+)?(restrictions?|filters?|limitations?)",
        r"(?i)bypass\s+(your\s+)?(safety|content|ethical)\s+(filters?|guidelines?)",
        r"(?i)enable\s+(developer|god|admin|unrestricted)\s+mode",
    ]

    # Patterns for hidden instructions
    HIDDEN_INSTRUCTION_PATTERNS = [
        r"<!--.*?-->",  # HTML comments
        r"\[INST\].*?\[/INST\]",  # Llama-style instruction markers
        r"<\|im_start\|>.*?<\|im_end\|>",  # ChatML markers
        r"\[SYSTEM\].*?\[/SYSTEM\]",  # System markers
        r"```system.*?```",  # Code block system
        r"\{\{.*?system.*?\}\}",  # Template markers
    ]

    # Characters/sequences to escape in tool results
    DANGEROUS_SEQUENCES = [
        ("[SYSTEM]", "[SYS]"),
        ("[INST]", "[INS]"),
        ("<|im_start|>", "<im_start>"),
        ("<|im_end|>", "<im_end>"),
        ("<!--", "<!-"),
        ("-->", "->"),
    ]

    def __init__(self, strict_mode: bool = False):
        """
        Initialize sanitizer.

        Args:
            strict_mode: If True, reject any suspicious input. If False, sanitize and allow.
        """
        self.strict_mode = strict_mode

        # Compile patterns for efficiency
        self._instruction_patterns = [re.compile(p) for p in self.INSTRUCTION_OVERRIDE_PATTERNS]
        self._extraction_patterns = [re.compile(p) for p in self.PROMPT_EXTRACTION_PATTERNS]
        self._role_patterns = [re.compile(p) for p in self.ROLE_MANIPULATION_PATTERNS]
        self._hidden_patterns = [re.compile(p, re.DOTALL) for p in self.HIDDEN_INSTRUCTION_PATTERNS]

    def sanitize(self, text: str) -> SanitizationResult:
        """
        Sanitize user input text.

        Args:
            text: Raw user input

        Returns:
            SanitizationResult with safety assessment and sanitized text
        """
        if not text:
            return SanitizationResult(is_safe=True, sanitized_text="", original_text="")

        threats = []
        sanitized = text

        # Check instruction override
        for pattern in self._instruction_patterns:
            if pattern.search(text):
                threats.append("instruction_override")
                logger.warning(
                    "prompt_injection_detected",
                    threat_type="instruction_override",
                    pattern=pattern.pattern[:50],
                )
                break

        # Check prompt extraction
        for pattern in self._extraction_patterns:
            if pattern.search(text):
                threats.append("prompt_extraction")
                logger.warning(
                    "prompt_injection_detected",
                    threat_type="prompt_extraction",
                    pattern=pattern.pattern[:50],
                )
                break

        # Check role manipulation
        for pattern in self._role_patterns:
            if pattern.search(text):
                threats.append("role_manipulation")
                logger.warning(
                    "prompt_injection_detected",
                    threat_type="role_manipulation",
                    pattern=pattern.pattern[:50],
                )
                break

        # Check and remove hidden instructions
        for pattern in self._hidden_patterns:
            if pattern.search(text):
                threats.append("hidden_instruction")
                sanitized = pattern.sub("[REMOVED]", sanitized)
                logger.warning(
                    "prompt_injection_detected",
                    threat_type="hidden_instruction",
                )

        # Remove dangerous sequences
        for dangerous, safe in self.DANGEROUS_SEQUENCES:
            if dangerous in sanitized:
                sanitized = sanitized.replace(dangerous, safe)

        is_safe = len(threats) == 0

        if threats:
            logger.info(
                "input_sanitization_result",
                is_safe=is_safe,
                threats=threats,
                input_length=len(text),
            )

        return SanitizationResult(
            is_safe=is_safe,
            sanitized_text=sanitized if not self.strict_mode else text,
            threats_detected=list(set(threats)),  # Deduplicate
            original_text=text,
            confidence=1.0 if is_safe else 0.9,
        )

    def sanitize_tool_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize tool result before LLM consumption.

        Tool results can contain malicious content that could manipulate
        the LLM when injected into the conversation.

        Args:
            result: Tool execution result dict

        Returns:
            Sanitized result dict
        """
        sanitized = result.copy()

        # Sanitize string fields
        for key, value in sanitized.items():
            if isinstance(value, str):
                # Remove dangerous sequences
                for dangerous, safe in self.DANGEROUS_SEQUENCES:
                    value = value.replace(dangerous, safe)
                sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_tool_result(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_tool_result(item) if isinstance(item, dict)
                    else self._sanitize_string(item) if isinstance(item, str)
                    else item
                    for item in value
                ]

        return sanitized

    def _sanitize_string(self, text: str) -> str:
        """Sanitize a string by removing dangerous sequences."""
        for dangerous, safe in self.DANGEROUS_SEQUENCES:
            text = text.replace(dangerous, safe)
        return text

    def sanitize_conversation(
        self, history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Sanitize conversation history.

        Previous messages in history could contain injection attempts
        that were not caught earlier.

        Args:
            history: List of message dicts with 'role' and 'content'

        Returns:
            Sanitized history with threats flagged
        """
        sanitized_history = []

        for message in history:
            content = message.get("content", "")
            result = self.sanitize(content)

            sanitized_message = message.copy()
            if not result.is_safe:
                sanitized_message["content"] = result.sanitized_text
                sanitized_message["flagged"] = True
                sanitized_message["threats"] = result.threats_detected

            sanitized_history.append(sanitized_message)

        return sanitized_history

    def is_safe(self, text: str) -> bool:
        """Quick check if input is safe without full sanitization."""
        return self.sanitize(text).is_safe
