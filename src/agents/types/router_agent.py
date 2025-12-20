"""RouterAgent - Classifies input and routes to appropriate agent."""
from typing import Dict, List, Optional

from src.agents.base import BaseAgent
from src.llm import LLMClient, LLMMessage
from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse


class RouterAgent(BaseAgent):
    """
    Agent that classifies input and routes to target agents.

    Use cases:
    - Multi-agent orchestration
    - Intent classification
    - Query routing
    - Agent selection based on context
    """

    def __init__(self, config: AgentConfig):
        """Initialize RouterAgent."""
        super().__init__(config)
        if not config.llm_config:
            raise ValueError("RouterAgent requires llm_config")
        if not config.routing_table:
            raise ValueError("RouterAgent requires routing_table")

        self._provider = LLMClient.get_provider(config.llm_config)
        self._routing_table = config.routing_table
        self._default_route = config.routing_table.get("default")

    async def execute(self, context: AgentContext) -> AgentResponse:
        """Classify input and return routing decision."""
        # Build classification prompt
        messages = self._build_classification_messages(context)

        # Get classification from LLM
        response = await self._provider.complete(messages)

        # Parse classification
        classification = self._parse_classification(response.content)
        target_agent = self._routing_table.get(classification)

        if not target_agent and self._default_route:
            target_agent = self._default_route
            classification = "default"

        if not target_agent:
            return AgentResponse(
                content=f"Could not determine routing for: {context.user_input[:50]}",
                confidence=0.3,
                metadata={
                    "classification": classification,
                    "routing_failed": True,
                },
            )

        return AgentResponse(
            content=f"Routing to: {target_agent}",
            confidence=0.9,
            metadata={
                "classification": classification,
                "target_agent": target_agent,
                "routing_table": self._routing_table,
            },
        )

    def _build_classification_messages(
        self, context: AgentContext
    ) -> List[LLMMessage]:
        """Build messages for classification."""
        categories = list(self._routing_table.keys())
        categories_str = ", ".join([c for c in categories if c != "default"])

        system_prompt = f"""You are a routing classifier. Classify the user's input into exactly one category.

Available categories: {categories_str}

Rules:
{self._format_rules()}

Respond with ONLY the category name, nothing else.
"""

        return [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=context.user_input),
        ]

    def _format_rules(self) -> str:
        """Format routing rules for the prompt."""
        rules = []
        for category, agent_id in self._routing_table.items():
            if category != "default":
                rules.append(f"- {category}: Route to {agent_id}")
        return "\n".join(rules)

    def _parse_classification(self, content: str) -> str:
        """Parse classification from LLM response."""
        # Clean up response
        classification = content.strip().lower()

        # Check if it matches a known category
        for category in self._routing_table.keys():
            if category.lower() in classification:
                return category

        # Return raw classification if no exact match
        return classification

    def get_routing_table(self) -> Dict[str, str]:
        """Get the routing table."""
        return self._routing_table.copy()
