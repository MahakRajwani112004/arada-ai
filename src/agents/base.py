"""Base agent class - all agent types inherit from this."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse


class BaseAgent(ABC):
    """
    Abstract base agent class.

    All agent types inherit from this and implement execute().
    The config determines behavior, not the class.
    """

    def __init__(self, config: AgentConfig):
        """Initialize agent with configuration."""
        self.config = config
        self.id = config.id
        self.name = config.name

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResponse:
        """
        Execute the agent's logic.

        This is implemented differently by each agent type:
        - SimpleAgent: Template/rule matching
        - LLMAgent: Single LLM call
        - RAGAgent: Retrieve + LLM
        - ToolAgent: LLM + Tool loop
        - FullAgent: Retrieve + LLM + Tool loop
        - RouterAgent: Classify + Route

        Args:
            context: Runtime context with user input and session info

        Returns:
            AgentResponse with content and metadata
        """
        pass

    def build_system_prompt(self) -> str:
        """Build system prompt from config."""
        parts = []

        # Current date/time context
        now = datetime.now()
        parts.append(
            f"## CURRENT DATE/TIME\n"
            f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Today is {now.strftime('%A, %B %d, %Y')}"
        )

        # Role section
        role = self.config.role
        parts.append(f"## ROLE\nYou are {role.title}.")
        if role.expertise:
            parts.append(f"Your expertise: {', '.join(role.expertise)}.")
        if role.personality:
            parts.append(f"Your personality: {', '.join(role.personality)}.")
        parts.append(f"Communication style: {role.communication_style}.")

        # Goal section
        goal = self.config.goal
        parts.append(f"\n## GOAL\n{goal.objective}")
        if goal.constraints:
            parts.append("\nConstraints:")
            for constraint in goal.constraints:
                parts.append(f"- {constraint}")

        # Instructions section
        instructions = self.config.instructions
        if instructions.steps:
            parts.append("\n## INSTRUCTIONS")
            for i, step in enumerate(instructions.steps, 1):
                parts.append(f"{i}. {step}")

        if instructions.rules:
            parts.append("\n## RULES")
            for rule in instructions.rules:
                parts.append(f"- {rule}")

        if instructions.prohibited:
            parts.append("\n## PROHIBITED")
            for prohibited in instructions.prohibited:
                parts.append(f"- DO NOT: {prohibited}")

        if instructions.output_format:
            parts.append(f"\n## OUTPUT FORMAT\n{instructions.output_format}")

        # Examples section
        if self.config.examples:
            parts.append("\n## EXAMPLES")
            for example in self.config.examples[:3]:  # Max 3 examples
                parts.append(f"\nInput: {example.input}")
                parts.append(f"Output: {example.output}")

        # Note: Tools are provided via native function calling, not in system prompt
        # The LLM receives tool definitions through the API's tool/function calling feature

        return "\n".join(parts)

    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tool IDs."""
        return [
            tool.tool_id for tool in self.config.tools if tool.enabled
        ]

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"
