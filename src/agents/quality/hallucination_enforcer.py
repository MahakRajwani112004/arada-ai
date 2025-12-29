"""Hallucination enforcement - applies fixes when hallucinations are detected.

This module ensures that when the hallucination checker detects ungrounded claims,
the suggested fix is actually applied instead of returning the original response.
"""
from typing import Optional

from src.activities.hallucination_checker_activity import HallucinationCheckerOutput
from src.config.logging import get_logger

logger = get_logger(__name__)


class HallucinationEnforcer:
    """
    Enforces hallucination corrections.

    When the hallucination checker detects issues, this class:
    1. Uses the suggested_fix if available
    2. Adds disclaimers if no fix is available
    3. Logs enforcement actions for monitoring

    Usage:
        enforcer = HallucinationEnforcer()
        final_response = enforcer.apply_fix(
            original_response=llm_output,
            checker_result=hallucination_check_result,
        )
    """

    # Disclaimer templates
    DISCLAIMER_TEMPLATES = {
        "unverified": (
            "\n\n---\n"
            "*Note: Some information in this response could not be verified against "
            "the available context. Please verify critical details independently.*"
        ),
        "partial": (
            "\n\n---\n"
            "*Note: The following claims could not be verified: {claims}. "
            "Please verify these details independently.*"
        ),
        "low_confidence": (
            "\n\n---\n"
            "*Note: This response has lower confidence due to limited context. "
            "Please verify important details.*"
        ),
    }

    def __init__(
        self,
        add_disclaimers: bool = True,
        disclaimer_threshold: float = 0.7,
        min_claims_for_rejection: int = 3,
    ):
        """
        Initialize enforcer.

        Args:
            add_disclaimers: Whether to add disclaimers when no fix available
            disclaimer_threshold: Confidence below which to add disclaimers
            min_claims_for_rejection: Number of ungrounded claims to consider response unreliable
        """
        self.add_disclaimers = add_disclaimers
        self.disclaimer_threshold = disclaimer_threshold
        self.min_claims_for_rejection = min_claims_for_rejection

    def apply_fix(
        self,
        original_response: str,
        checker_result: HallucinationCheckerOutput,
        context: Optional[str] = None,
    ) -> str:
        """
        Apply hallucination fix if needed.

        Args:
            original_response: The original LLM response
            checker_result: Output from hallucination checker
            context: Optional context for logging

        Returns:
            Fixed response (suggested_fix, original with disclaimer, or original)
        """
        # If grounded, return original
        if checker_result.is_grounded:
            logger.debug(
                "hallucination_enforcer_pass",
                confidence=checker_result.confidence,
                reason=checker_result.reason,
            )
            return original_response

        # Hallucination detected - apply fix
        logger.warning(
            "hallucination_enforcer_triggered",
            ungrounded_claims=checker_result.ungrounded_claims,
            has_suggested_fix=checker_result.suggested_fix is not None,
            confidence=checker_result.confidence,
            reason=checker_result.reason,
        )

        # Priority 1: Use suggested fix if available
        if checker_result.suggested_fix:
            logger.info(
                "hallucination_fix_applied",
                original_length=len(original_response),
                fixed_length=len(checker_result.suggested_fix),
                claims_fixed=len(checker_result.ungrounded_claims),
            )
            return checker_result.suggested_fix

        # Priority 2: Add disclaimer if configured
        if self.add_disclaimers:
            return self._add_disclaimer(original_response, checker_result)

        # Priority 3: Return original with warning logged
        logger.warning(
            "hallucination_not_fixed",
            reason="No suggested fix and disclaimers disabled",
            ungrounded_claims=checker_result.ungrounded_claims,
        )
        return original_response

    def _add_disclaimer(
        self,
        response: str,
        checker_result: HallucinationCheckerOutput,
    ) -> str:
        """Add appropriate disclaimer to response."""
        claims = checker_result.ungrounded_claims

        if len(claims) >= self.min_claims_for_rejection:
            # Many ungrounded claims - general disclaimer
            disclaimer = self.DISCLAIMER_TEMPLATES["unverified"]
        elif claims:
            # Specific claims ungrounded - list them
            claims_text = ", ".join(f"'{c}'" for c in claims[:3])
            if len(claims) > 3:
                claims_text += f" and {len(claims) - 3} more"
            disclaimer = self.DISCLAIMER_TEMPLATES["partial"].format(claims=claims_text)
        elif checker_result.confidence < self.disclaimer_threshold:
            # Low confidence - general caveat
            disclaimer = self.DISCLAIMER_TEMPLATES["low_confidence"]
        else:
            # No specific issue, skip disclaimer
            return response

        logger.info(
            "hallucination_disclaimer_added",
            claim_count=len(claims),
            confidence=checker_result.confidence,
        )

        return response + disclaimer

    def should_reject(self, checker_result: HallucinationCheckerOutput) -> bool:
        """
        Determine if response should be completely rejected.

        Use this for high-stakes applications where hallucinations are unacceptable.

        Args:
            checker_result: Hallucination checker output

        Returns:
            True if response should be rejected entirely
        """
        if checker_result.is_grounded:
            return False

        # Reject if too many ungrounded claims
        if len(checker_result.ungrounded_claims) >= self.min_claims_for_rejection:
            return True

        # Reject if confidence is very low
        if checker_result.confidence < 0.5:
            return True

        return False

    def get_rejection_message(
        self, checker_result: HallucinationCheckerOutput
    ) -> str:
        """
        Get a user-friendly rejection message.

        Args:
            checker_result: Hallucination checker output

        Returns:
            Message explaining why the response was rejected
        """
        if len(checker_result.ungrounded_claims) >= self.min_claims_for_rejection:
            return (
                "I apologize, but I cannot provide a reliable answer based on the "
                "available information. Several claims in my initial response could "
                "not be verified. Please try rephrasing your question or providing "
                "additional context."
            )

        return (
            "I apologize, but I'm not confident in my response based on the "
            "available information. Please try asking in a different way or "
            "provide more context."
        )


def enforce_hallucination_check(
    response: str,
    checker_result: HallucinationCheckerOutput,
    strict: bool = False,
) -> str:
    """
    Convenience function to enforce hallucination checks.

    Args:
        response: Original response
        checker_result: Hallucination check result
        strict: If True, reject responses with hallucinations entirely

    Returns:
        Fixed/validated response
    """
    enforcer = HallucinationEnforcer()

    if strict and enforcer.should_reject(checker_result):
        return enforcer.get_rejection_message(checker_result)

    return enforcer.apply_fix(response, checker_result)
