"""SimpleAgent - No LLM, rule-based responses."""
import re
from typing import List, Tuple

from src.agents.base import BaseAgent
from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse


class SimpleAgent(BaseAgent):
    """
    Simple rule-based agent without LLM.

    Use cases:
    - Greeting/welcome messages
    - Simple FAQ with exact matches
    - Keyword-based routing
    - Template responses
    """

    def __init__(self, config: AgentConfig):
        """Initialize SimpleAgent."""
        super().__init__(config)
        self._patterns: List[Tuple[re.Pattern, str]] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns from examples."""
        for example in self.config.examples:
            # Convert input to regex pattern
            # Replace * with .* for wildcard matching
            pattern_str = re.escape(example.input).replace(r"\*", ".*")
            pattern = re.compile(pattern_str, re.IGNORECASE)
            self._patterns.append((pattern, example.output))

    async def execute(self, context: AgentContext) -> AgentResponse:
        """Execute simple pattern matching."""
        user_input = context.user_input.lower().strip()

        # Try exact patterns first
        for pattern, response in self._patterns:
            if pattern.search(user_input):
                return AgentResponse(
                    content=response,
                    confidence=1.0,
                    metadata={"match_type": "pattern"},
                )

        # Try keyword matching from instructions.rules
        # Format: "keyword: response"
        for rule in self.config.instructions.rules:
            if ":" in rule:
                keyword, response = rule.split(":", 1)
                if keyword.strip().lower() in user_input:
                    return AgentResponse(
                        content=response.strip(),
                        confidence=0.8,
                        metadata={"match_type": "keyword"},
                    )

        # Default response based on goal
        default_response = self.config.goal.objective
        return AgentResponse(
            content=f"I can help you with: {default_response}",
            confidence=0.5,
            metadata={"match_type": "default"},
        )
