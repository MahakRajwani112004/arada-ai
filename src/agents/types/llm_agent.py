"""LLMAgent - Uses LLM for generating responses."""
from typing import List

from src.agents.base import BaseAgent
from src.llm import LLMClient, LLMMessage
from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse, Message


class LLMAgent(BaseAgent):
    """
    Agent that uses LLM for responses.

    Use cases:
    - Conversational AI
    - Content generation
    - Text analysis
    - Creative writing
    - General purpose chat
    """

    def __init__(self, config: AgentConfig):
        """Initialize LLMAgent."""
        super().__init__(config)
        if not config.llm_config:
            raise ValueError("LLMAgent requires llm_config")
        self._provider = LLMClient.get_provider(config.llm_config)

    def _build_messages(self, context: AgentContext) -> List[LLMMessage]:
        """Build LLM messages from context."""
        messages = []

        # Add system prompt
        system_prompt = self.build_system_prompt()
        messages.append(LLMMessage(role="system", content=system_prompt))

        # Add conversation history
        for msg in context.conversation_history:
            messages.append(LLMMessage(role=msg.role, content=msg.content))

        # Add current user input
        messages.append(LLMMessage(role="user", content=context.user_input))

        return messages

    async def execute(self, context: AgentContext) -> AgentResponse:
        """Execute LLM completion."""
        messages = self._build_messages(context)

        response = await self._provider.complete(messages)

        return AgentResponse(
            content=response.content,
            confidence=self._calculate_confidence(response),
            metadata={
                "model": response.model,
                "usage": response.usage,
                "finish_reason": response.finish_reason,
            },
        )

    def _calculate_confidence(self, response) -> float:
        """Calculate confidence based on response characteristics."""
        # Base confidence for LLM responses
        confidence = 0.85

        # Reduce confidence if response was cut off
        if response.finish_reason == "length":
            confidence -= 0.1

        # Very short responses might be less reliable
        if len(response.content) < 20:
            confidence -= 0.05

        return max(0.0, min(1.0, confidence))
