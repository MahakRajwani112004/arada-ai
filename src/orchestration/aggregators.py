"""Aggregation strategies for multi-agent results."""
import json
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any, Dict, List, Optional

from src.models.orchestrator_config import AggregationStrategy


class AgentResult:
    """Standardized result from an agent execution."""

    def __init__(
        self,
        agent_id: str,
        success: bool,
        content: str,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.agent_id = agent_id
        self.success = success
        self.content = content
        self.error = error
        self.metadata = metadata or {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResult":
        """Create AgentResult from dictionary."""
        return cls(
            agent_id=data.get("agent_id", "unknown"),
            success=data.get("success", False),
            content=data.get("content", ""),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


class BaseAggregator(ABC):
    """Base class for result aggregators."""

    @abstractmethod
    async def aggregate(self, results: List[AgentResult]) -> str:
        """
        Aggregate multiple agent results into a single output.

        Args:
            results: List of agent execution results

        Returns:
            Aggregated string output
        """
        pass


class FirstSuccessAggregator(BaseAggregator):
    """Returns the first successful result."""

    async def aggregate(self, results: List[AgentResult]) -> str:
        """Return first successful result."""
        for result in results:
            if result.success and result.content:
                return result.content

        # No successful results, return error summary
        errors = [r.error for r in results if r.error]
        if errors:
            return f"No successful results. Errors: {'; '.join(errors)}"
        return "No results available."


class AllResultsAggregator(BaseAggregator):
    """Combines all results into a formatted output."""

    def __init__(self, separator: str = "\n\n---\n\n"):
        """Initialize with optional separator."""
        self.separator = separator

    async def aggregate(self, results: List[AgentResult]) -> str:
        """Combine all results."""
        parts = []

        for result in results:
            header = f"[{result.agent_id}]"
            if result.success:
                parts.append(f"{header}\n{result.content}")
            else:
                parts.append(f"{header} (failed)\n{result.error or 'Unknown error'}")

        return self.separator.join(parts)


class VotingAggregator(BaseAggregator):
    """
    Returns the majority-voted result.

    Best for classification tasks where multiple agents return
    category labels.
    """

    async def aggregate(self, results: List[AgentResult]) -> str:
        """Return majority-voted result."""
        # Count successful results
        votes = Counter()

        for result in results:
            if result.success and result.content:
                # Normalize content for voting
                normalized = result.content.strip().lower()
                votes[normalized] += 1

        if not votes:
            return "No valid votes received."

        # Get the winner
        winner, count = votes.most_common(1)[0]
        total = sum(votes.values())

        # Find original (non-normalized) version
        for result in results:
            if result.success and result.content.strip().lower() == winner:
                return result.content

        return winner


class MergeAggregator(BaseAggregator):
    """
    Merges JSON results into a single object.

    Best for structured data where agents return complementary fields.
    """

    def __init__(self, conflict_strategy: str = "last"):
        """
        Initialize merge aggregator.

        Args:
            conflict_strategy: How to handle key conflicts
                - "last": Later values overwrite earlier
                - "first": Keep first value
                - "list": Collect all values in a list
        """
        self.conflict_strategy = conflict_strategy

    async def aggregate(self, results: List[AgentResult]) -> str:
        """Merge JSON results."""
        merged: Dict[str, Any] = {}

        for result in results:
            if not result.success:
                continue

            try:
                data = json.loads(result.content)
                if not isinstance(data, dict):
                    continue

                for key, value in data.items():
                    if key not in merged:
                        merged[key] = value
                    elif self.conflict_strategy == "last":
                        merged[key] = value
                    elif self.conflict_strategy == "first":
                        pass  # Keep existing
                    elif self.conflict_strategy == "list":
                        if not isinstance(merged[key], list):
                            merged[key] = [merged[key]]
                        merged[key].append(value)

            except json.JSONDecodeError:
                continue

        if not merged:
            return "{}"

        return json.dumps(merged, indent=2)


class LLMBestAggregator(BaseAggregator):
    """
    Uses an LLM to select and synthesize the best result.

    Best for nuanced decisions where automated selection isn't sufficient.
    """

    def __init__(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
        selection_prompt: Optional[str] = None,
    ):
        """
        Initialize LLM-based aggregator.

        Args:
            llm_config: LLM configuration (provider, model, etc.)
            selection_prompt: Custom prompt for selection
        """
        self.llm_config = llm_config or {}
        self.selection_prompt = selection_prompt or self._default_prompt()

    def _default_prompt(self) -> str:
        return """You are evaluating responses from multiple specialized agents.
Analyze each response for accuracy, completeness, and relevance.
Select and return the best response, or synthesize them into an improved answer.

Responses:
{responses}

Return only the final answer, no explanation of your selection process."""

    async def aggregate(self, results: List[AgentResult]) -> str:
        """Use LLM to select best result."""
        from src.llm import LLMClient
        from src.llm.providers.base import LLMMessage
        from src.models.llm_config import LLMConfig

        # Build responses text
        responses_text = "\n\n".join([
            f"--- Agent: {r.agent_id} ---\n{r.content}"
            for r in results
            if r.success and r.content
        ])

        if not responses_text:
            return "No successful results to evaluate."

        prompt = self.selection_prompt.format(responses=responses_text)

        # Get LLM config
        config = LLMConfig(
            provider=self.llm_config.get("provider", "openai"),
            model=self.llm_config.get("model", "gpt-4o-mini"),
            temperature=self.llm_config.get("temperature", 0.3),
            max_tokens=self.llm_config.get("max_tokens", 2048),
        )

        provider = LLMClient.get_provider(config)

        response = await provider.complete([
            LLMMessage(role="system", content="You are a result evaluator."),
            LLMMessage(role="user", content=prompt),
        ])

        return response.content


class WeightedAggregator(BaseAggregator):
    """
    Aggregates results based on agent weights/priorities.

    Best for scenarios where some agents are more authoritative.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize with agent weights.

        Args:
            weights: Dict of agent_id -> weight (higher = more priority)
        """
        self.weights = weights or {}

    async def aggregate(self, results: List[AgentResult]) -> str:
        """Return highest-weighted successful result."""
        successful = [r for r in results if r.success and r.content]

        if not successful:
            return "No successful results."

        # Sort by weight (descending), then by order
        sorted_results = sorted(
            successful,
            key=lambda r: self.weights.get(r.agent_id, 1.0),
            reverse=True,
        )

        return sorted_results[0].content


def create_aggregator(
    strategy: AggregationStrategy,
    config: Optional[Dict[str, Any]] = None,
) -> BaseAggregator:
    """
    Factory function to create an aggregator.

    Args:
        strategy: The aggregation strategy to use
        config: Optional configuration for the aggregator

    Returns:
        Configured aggregator instance
    """
    config = config or {}

    if strategy == AggregationStrategy.FIRST:
        return FirstSuccessAggregator()

    elif strategy == AggregationStrategy.ALL:
        return AllResultsAggregator(
            separator=config.get("separator", "\n\n---\n\n")
        )

    elif strategy == AggregationStrategy.VOTE:
        return VotingAggregator()

    elif strategy == AggregationStrategy.MERGE:
        return MergeAggregator(
            conflict_strategy=config.get("conflict_strategy", "last")
        )

    elif strategy == AggregationStrategy.BEST:
        return LLMBestAggregator(
            llm_config=config.get("llm_config"),
            selection_prompt=config.get("selection_prompt"),
        )

    else:
        raise ValueError(f"Unknown aggregation strategy: {strategy}")
