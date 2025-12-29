"""Confidence calculation for agent responses.

This module provides real confidence scoring based on actual signals,
replacing hardcoded values across all agent types.

Confidence is calculated from multiple signals:
1. LLM signals: finish_reason, response length, token usage
2. Tool signals: success rate, execution errors
3. Retrieval signals: relevance scores, document coverage
4. Response signals: completeness, coherence indicators
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConfidenceSignals:
    """Signals used to calculate confidence score."""

    # LLM signals
    finish_reason: Optional[str] = None  # "stop", "length", "tool_calls", etc.
    response_length: int = 0
    max_tokens_used: bool = False  # True if response was truncated

    # Tool signals
    tool_calls_total: int = 0
    tool_calls_succeeded: int = 0
    tool_calls_failed: int = 0

    # Retrieval signals (for RAG)
    documents_retrieved: int = 0
    avg_relevance_score: float = 0.0
    min_relevance_score: float = 0.0

    # Response signals
    has_uncertainty_language: bool = False  # "I'm not sure", "might be", etc.
    is_refusal: bool = False  # "I can't", "I'm unable to"
    iterations_used: int = 1
    max_iterations_reached: bool = False

    # Child agent signals (for orchestrator)
    child_confidences: List[float] = field(default_factory=list)
    child_failures: int = 0


class ConfidenceCalculator:
    """
    Calculates confidence scores from actual signals.

    Usage:
        signals = ConfidenceSignals(
            finish_reason="stop",
            tool_calls_total=2,
            tool_calls_succeeded=2,
        )
        confidence = ConfidenceCalculator.calculate(signals)
    """

    # Weights for different signal categories
    WEIGHTS = {
        "llm": 0.3,
        "tools": 0.25,
        "retrieval": 0.25,
        "response": 0.2,
    }

    # Uncertainty phrases that reduce confidence
    UNCERTAINTY_PHRASES = [
        "i'm not sure",
        "i'm not certain",
        "might be",
        "could be",
        "possibly",
        "perhaps",
        "i think",
        "it seems",
        "appears to be",
        "may not be accurate",
        "i don't have enough information",
    ]

    # Refusal phrases that indicate inability
    REFUSAL_PHRASES = [
        "i can't",
        "i cannot",
        "i'm unable",
        "i am unable",
        "i don't have access",
        "beyond my capabilities",
        "outside my scope",
    ]

    @classmethod
    def calculate(cls, signals: ConfidenceSignals) -> float:
        """
        Calculate confidence score from signals.

        Returns:
            Float between 0.0 and 1.0
        """
        scores = {
            "llm": cls._calculate_llm_confidence(signals),
            "tools": cls._calculate_tool_confidence(signals),
            "retrieval": cls._calculate_retrieval_confidence(signals),
            "response": cls._calculate_response_confidence(signals),
        }

        # Weighted average
        total_weight = 0.0
        weighted_sum = 0.0

        for category, score in scores.items():
            if score is not None:  # Only include categories with data
                weight = cls.WEIGHTS[category]
                weighted_sum += score * weight
                total_weight += weight

        if total_weight == 0:
            return 0.5  # Default if no signals

        confidence = weighted_sum / total_weight

        # Apply penalties for critical issues
        if signals.max_iterations_reached:
            confidence *= 0.7  # 30% penalty for hitting limits

        if signals.is_refusal:
            confidence *= 0.5  # 50% penalty for refusals

        return max(0.0, min(1.0, confidence))

    @classmethod
    def _calculate_llm_confidence(cls, signals: ConfidenceSignals) -> Optional[float]:
        """Calculate confidence from LLM signals."""
        if signals.finish_reason is None:
            return None

        base_score = 0.85

        # Finish reason adjustments
        if signals.finish_reason == "stop":
            base_score = 0.9  # Natural completion
        elif signals.finish_reason == "length":
            base_score = 0.6  # Truncated
            signals.max_tokens_used = True
        elif signals.finish_reason == "tool_calls":
            base_score = 0.85  # Tool use is expected
        elif signals.finish_reason == "content_filter":
            base_score = 0.3  # Content was filtered

        # Response length adjustments
        if signals.response_length < 20:
            base_score *= 0.8  # Very short response
        elif signals.response_length > 50:
            base_score *= 1.05  # Substantive response

        return min(1.0, base_score)

    @classmethod
    def _calculate_tool_confidence(cls, signals: ConfidenceSignals) -> Optional[float]:
        """Calculate confidence from tool execution signals."""
        if signals.tool_calls_total == 0:
            return None  # No tools used, skip this category

        success_rate = signals.tool_calls_succeeded / signals.tool_calls_total

        # Base confidence from success rate
        base_score = 0.5 + (success_rate * 0.5)

        # Penalty for multiple failures
        if signals.tool_calls_failed > 2:
            base_score *= 0.8

        return base_score

    @classmethod
    def _calculate_retrieval_confidence(cls, signals: ConfidenceSignals) -> Optional[float]:
        """Calculate confidence from retrieval signals."""
        if signals.documents_retrieved == 0:
            return None  # No retrieval, skip this category

        # Base score from relevance
        if signals.avg_relevance_score > 0:
            base_score = 0.5 + (signals.avg_relevance_score * 0.4)
        else:
            base_score = 0.6  # No relevance scores available

        # Boost for multiple relevant documents
        if signals.documents_retrieved >= 3 and signals.min_relevance_score > 0.7:
            base_score *= 1.1

        # Penalty for low relevance
        if signals.min_relevance_score < 0.3:
            base_score *= 0.85

        return min(1.0, base_score)

    @classmethod
    def _calculate_response_confidence(cls, signals: ConfidenceSignals) -> float:
        """Calculate confidence from response characteristics."""
        base_score = 0.85

        # Penalty for uncertainty language
        if signals.has_uncertainty_language:
            base_score *= 0.85

        # Penalty for many iterations (might indicate difficulty)
        if signals.iterations_used > 5:
            base_score *= 0.9
        elif signals.iterations_used > 8:
            base_score *= 0.8

        # Child agent aggregation (for orchestrator)
        if signals.child_confidences:
            avg_child = sum(signals.child_confidences) / len(signals.child_confidences)
            min_child = min(signals.child_confidences)

            # Blend with child confidences
            base_score = (base_score * 0.4) + (avg_child * 0.4) + (min_child * 0.2)

            # Penalty for child failures
            if signals.child_failures > 0:
                failure_ratio = signals.child_failures / (len(signals.child_confidences) + signals.child_failures)
                base_score *= (1 - failure_ratio * 0.5)

        return base_score

    @classmethod
    def detect_uncertainty(cls, text: str) -> bool:
        """Detect if response contains uncertainty language."""
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in cls.UNCERTAINTY_PHRASES)

    @classmethod
    def detect_refusal(cls, text: str) -> bool:
        """Detect if response is a refusal."""
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in cls.REFUSAL_PHRASES)

    @classmethod
    def from_llm_response(
        cls,
        response,
        tool_calls_made: Optional[List[Dict[str, Any]]] = None,
        retrieved_docs: Optional[List] = None,
        iterations: int = 1,
        max_iterations_reached: bool = False,
    ) -> float:
        """
        Convenience method to calculate confidence from LLM response.

        Args:
            response: LLM response object with content, finish_reason, etc.
            tool_calls_made: List of tool call results
            retrieved_docs: List of retrieved documents (for RAG)
            iterations: Number of tool loop iterations
            max_iterations_reached: Whether max iterations was hit

        Returns:
            Confidence score between 0.0 and 1.0
        """
        content = response.content or ""

        signals = ConfidenceSignals(
            finish_reason=response.finish_reason,
            response_length=len(content),
            has_uncertainty_language=cls.detect_uncertainty(content),
            is_refusal=cls.detect_refusal(content),
            iterations_used=iterations,
            max_iterations_reached=max_iterations_reached,
        )

        # Tool signals
        if tool_calls_made:
            signals.tool_calls_total = len(tool_calls_made)
            signals.tool_calls_succeeded = sum(
                1 for tc in tool_calls_made
                if tc.get("result", {}).get("success", False)
            )
            signals.tool_calls_failed = signals.tool_calls_total - signals.tool_calls_succeeded

        # Retrieval signals
        if retrieved_docs:
            signals.documents_retrieved = len(retrieved_docs)
            # Extract relevance scores if available
            scores = [
                doc.score if hasattr(doc, "score") else 0.0
                for doc in retrieved_docs
            ]
            if scores:
                signals.avg_relevance_score = sum(scores) / len(scores)
                signals.min_relevance_score = min(scores)

        return cls.calculate(signals)
