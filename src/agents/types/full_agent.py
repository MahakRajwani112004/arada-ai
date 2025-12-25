"""FullAgent - LLM with RAG and tool capabilities."""
import json
import re
from typing import Any, Dict, List

from src.agents.base import BaseAgent
from src.knowledge.knowledge_base import KnowledgeBase
from src.llm import LLMClient, LLMMessage
from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse
from src.tools.registry import get_registry


class FullAgent(BaseAgent):
    """
    Most capable agent: RAG + LLM + Tools.

    Use cases:
    - Complex research assistants
    - Enterprise knowledge + action systems
    - Multi-capability chatbots
    """

    MAX_TOOL_ITERATIONS = 10

    def __init__(self, config: AgentConfig):
        """Initialize FullAgent."""
        super().__init__(config)
        if not config.llm_config:
            raise ValueError("FullAgent requires llm_config")
        if not config.knowledge_base:
            raise ValueError("FullAgent requires knowledge_base config")

        self._provider = LLMClient.get_provider(config.llm_config)
        self._kb = KnowledgeBase(config.knowledge_base)
        self._registry = get_registry()
        self._enabled_tools = self.get_enabled_tools()
        self._kb_initialized = False

    async def _ensure_kb_initialized(self) -> None:
        """Ensure knowledge base is initialized."""
        if not self._kb_initialized:
            await self._kb.initialize()
            self._kb_initialized = True

    async def _execute_impl(self, context: AgentContext) -> AgentResponse:
        """Execute FullAgent: RAG + LLM + Tools."""
        await self._ensure_kb_initialized()

        # Step 1: Retrieve relevant documents
        retrieval_result = await self._kb.search(context.user_input)
        retrieved_docs = [doc.content for doc in retrieval_result.documents]

        # Step 2: Build initial messages with context
        messages = self._build_messages(context, retrieved_docs)

        # Step 3: Tool loop
        tool_calls_made = []
        iterations = 0

        while iterations < self.MAX_TOOL_ITERATIONS:
            iterations += 1

            response = await self._provider.complete(
                messages,
                user_id=context.user_id,
                agent_id=self.id,
                request_id=context.request_id,
                workflow_id=context.workflow_id,
            )
            tool_calls = self._extract_tool_calls(response)

            if not tool_calls:
                return AgentResponse(
                    content=response.content,
                    confidence=0.9,
                    metadata={
                        "model": response.model,
                        "usage": response.usage,
                        "retrieved_count": len(retrieved_docs),
                        "tool_calls": tool_calls_made,
                        "iterations": iterations,
                    },
                )

            # Execute tools
            for tool_call in tool_calls:
                result = await self._execute_tool(tool_call)
                tool_calls_made.append({
                    "tool": tool_call["name"],
                    "args": tool_call["arguments"],
                    "result": result,
                })

                messages.append(LLMMessage(
                    role="assistant",
                    content=f"[Tool: {tool_call['name']}({json.dumps(tool_call['arguments'])})]",
                ))
                messages.append(LLMMessage(
                    role="user",
                    content=f"[Result: {json.dumps(result)}]",
                ))

        return AgentResponse(
            content="Maximum iterations reached.",
            confidence=0.5,
            metadata={"tool_calls": tool_calls_made, "iterations": iterations},
        )

    def _build_messages(
        self,
        context: AgentContext,
        retrieved_docs: List[str],
    ) -> List[LLMMessage]:
        """Build messages with retrieved context."""
        messages = []

        system_prompt = self.build_system_prompt()
        if retrieved_docs:
            context_str = "\n\n".join([
                f"[Document {i+1}]\n{doc}"
                for i, doc in enumerate(retrieved_docs)
            ])
            system_prompt += f"\n\n## RETRIEVED CONTEXT\n{context_str}"

        messages.append(LLMMessage(role="system", content=system_prompt))

        for msg in context.conversation_history:
            messages.append(LLMMessage(role=msg.role, content=msg.content))

        messages.append(LLMMessage(role="user", content=context.user_input))
        return messages

    def _extract_tool_calls(self, response) -> List[Dict[str, Any]]:
        """Extract tool calls from response."""
        tool_calls = []
        pattern = r'\[TOOL:\s*(\w+)\((\{.*?\})\)\]'

        for match in re.finditer(pattern, response.content, re.DOTALL):
            try:
                tool_calls.append({
                    "name": match.group(1),
                    "arguments": json.loads(match.group(2)),
                })
            except json.JSONDecodeError:
                continue
        return tool_calls

    async def _execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call."""
        result = await self._registry.execute(
            tool_call["name"],
            **tool_call["arguments"],
        )
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
        }

    async def close(self) -> None:
        """Close connections."""
        if self._kb_initialized:
            await self._kb.close()
            self._kb_initialized = False
