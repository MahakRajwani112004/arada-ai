"""RAGAgent - LLM with knowledge base retrieval."""
from typing import List, Optional

from src.agents.base import BaseAgent
from src.knowledge.knowledge_base import KnowledgeBase
from src.llm import LLMClient, LLMMessage
from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse
from src.skills.models import Skill


class RAGAgent(BaseAgent):
    """
    Agent that retrieves context before generating response.

    Components Used:
    - Skills: YES (injected into system prompt via build_system_prompt)
    - Tools: NO
    - Knowledge Base: YES (retrieval before LLM call)

    Use cases:
    - Question answering over documents
    - Customer support with knowledge base
    - Research assistants
    - Documentation helpers
    """

    def __init__(
        self,
        config: AgentConfig,
        skills: Optional[List[Skill]] = None,
    ):
        """
        Initialize RAGAgent.

        Args:
            config: Agent configuration
            skills: List of Skill objects for domain expertise
        """
        super().__init__(config, skills=skills)
        if not config.llm_config:
            raise ValueError("RAGAgent requires llm_config")
        if not config.knowledge_base:
            raise ValueError("RAGAgent requires knowledge_base config")

        self._provider = LLMClient.get_provider(config.llm_config)
        self._kb = KnowledgeBase(config.knowledge_base)
        self._kb_initialized = False

    async def _ensure_kb_initialized(self) -> None:
        """Ensure knowledge base is initialized."""
        if not self._kb_initialized:
            await self._kb.initialize()
            self._kb_initialized = True

    def _build_messages_with_context(
        self,
        context: AgentContext,
        retrieved_docs: List[str],
        selected_skills: List = None,
    ) -> List[LLMMessage]:
        """Build LLM messages with retrieved context."""
        messages = []

        # Build enhanced system prompt with context and selected skills
        system_prompt = self.build_system_prompt(selected_skills=selected_skills)

        if retrieved_docs:
            context_str = "\n\n".join([
                f"[Document {i+1}]\n{doc}"
                for i, doc in enumerate(retrieved_docs)
            ])
            system_prompt += f"\n\n## RETRIEVED CONTEXT\n{context_str}"

        messages.append(LLMMessage(role="system", content=system_prompt))

        # Add conversation history
        for msg in context.conversation_history:
            messages.append(LLMMessage(role=msg.role, content=msg.content))

        # Add current user input
        messages.append(LLMMessage(role="user", content=context.user_input))

        return messages

    async def _execute_impl(self, context: AgentContext) -> AgentResponse:
        """Execute RAG: retrieve then generate."""
        await self._ensure_kb_initialized()

        # Select relevant skills for this query
        selected_skills = await self._select_skills_for_query(
            context.user_input,
            user_id=context.user_id,
        )

        # Retrieve relevant documents
        retrieval_result = await self._kb.search(context.user_input)

        retrieved_docs = [
            doc.content for doc in retrieval_result.documents
        ]

        # Build messages with context and selected skills
        messages = self._build_messages_with_context(
            context, retrieved_docs, selected_skills=selected_skills
        )

        # Generate response
        response = await self._provider.complete(
            messages,
            user_id=context.user_id,
            agent_id=self.id,
            request_id=context.request_id,
            workflow_id=context.workflow_id,
        )

        return AgentResponse(
            content=response.content,
            confidence=self._calculate_confidence(response, retrieval_result),
            metadata={
                "model": response.model,
                "usage": response.usage,
                "retrieved_count": len(retrieved_docs),
                "retrieval_scores": [
                    doc.score for doc in retrieval_result.documents
                ],
            },
        )

    def _calculate_confidence(self, response, retrieval_result) -> float:
        """Calculate confidence based on response and retrieval."""
        base_confidence = 0.85

        # Boost confidence if good retrieval results
        if retrieval_result.documents:
            avg_score = sum(
                d.score for d in retrieval_result.documents
            ) / len(retrieval_result.documents)
            base_confidence += avg_score * 0.1

        # Reduce if response was cut off
        if response.finish_reason == "length":
            base_confidence -= 0.1

        return max(0.0, min(1.0, base_confidence))

    async def close(self) -> None:
        """Close knowledge base connection."""
        if self._kb_initialized:
            await self._kb.close()
            self._kb_initialized = False
