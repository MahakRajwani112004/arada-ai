"""FullAgent - LLM with RAG and native tool calling capabilities."""
import asyncio
import json
from typing import Any, Dict, List, Optional

from src.agents.base import BaseAgent
from src.agents.confidence import ConfidenceCalculator, ConfidenceSignals
from src.knowledge.knowledge_base import KnowledgeBase
from src.llm import LLMClient, LLMMessage
from src.llm.providers.base import ToolCall
from src.models.agent_config import AgentConfig
from src.models.responses import AgentContext, AgentResponse
from src.skills.models import Skill
from src.tools.registry import get_registry


class FullAgent(BaseAgent):
    """
    Most capable agent: RAG + LLM + Native Tool Calling.

    Components Used:
    - Skills: YES (injected into system prompt via build_system_prompt)
    - Tools: YES (native LLM function calling)
    - Knowledge Base: YES (retrieval before LLM call)

    Use cases:
    - Complex research assistants
    - Enterprise knowledge + action systems
    - Multi-capability chatbots

    Execution Flow:
    1. Initialize KB if not ready
    2. Retrieve relevant documents from KB
    3. Build system prompt with skills + retrieved context
    4. Call LLM with tool definitions (native function calling)
    5. Execute tools if requested
    6. Loop until LLM returns final response
    """

    MAX_TOOL_ITERATIONS = 10
    TOOL_TIMEOUT_SECONDS = 30  # Timeout for individual tool execution

    def __init__(
        self,
        config: AgentConfig,
        skills: Optional[List[Skill]] = None,
    ):
        """
        Initialize FullAgent.

        Args:
            config: Agent configuration
            skills: List of Skill objects for domain expertise
        """
        super().__init__(config, skills=skills)

        if not config.llm_config:
            raise ValueError("FullAgent requires llm_config")
        if not config.knowledge_base:
            raise ValueError("FullAgent requires knowledge_base config")

        self._provider = LLMClient.get_provider(config.llm_config)
        self._kb = KnowledgeBase(config.knowledge_base)
        self._registry = get_registry()
        self._enabled_tools = self.get_enabled_tools()
        self._kb_initialized = False

        # Validate enabled tools exist in registry
        self._validate_tools()

    def _validate_tools(self) -> None:
        """Validate that enabled tools exist in the registry."""
        import structlog
        logger = structlog.get_logger(__name__)

        if not self._enabled_tools:
            return

        available = set(self._registry.available_tools)
        missing = [t for t in self._enabled_tools if t not in available]

        if missing:
            logger.warning(
                "tools_not_found_in_registry",
                agent_id=self.id,
                missing_tools=missing,
                available_tools=list(available),
            )

    async def _ensure_kb_initialized(self) -> None:
        """Ensure knowledge base is initialized."""
        if not self._kb_initialized:
            await self._kb.initialize()
            self._kb_initialized = True

    async def _execute_impl(self, context: AgentContext) -> AgentResponse:
        """
        Execute FullAgent: RAG + LLM + Native Tool Calling.

        This uses the same native function calling pattern as ToolAgent,
        combined with knowledge base retrieval from RAGAgent.
        """
        import structlog
        logger = structlog.get_logger(__name__)

        await self._ensure_kb_initialized()

        try:
            # Step 0: Select relevant skills for this query
            selected_skills = await self._select_skills_for_query(
                context.user_input,
                user_id=context.user_id,
            )

            # Step 1: Retrieve relevant documents
            retrieval_result = await self._kb.search(context.user_input)
            retrieved_docs = [doc.content for doc in retrieval_result.documents]

            logger.info(
                "full_agent_kb_retrieval",
                agent_id=self.id,
                docs_retrieved=len(retrieved_docs),
                skills_selected=len(selected_skills),
            )

            # Step 2: Build initial messages with retrieved context and skills
            messages = self._build_messages(
                context, retrieved_docs, selected_skills=selected_skills
            )

            # Step 3: Get tool definitions for native function calling
            tool_definitions = self._registry.get_openai_tools(self._enabled_tools)

            logger.info(
                "full_agent_tools",
                agent_id=self.id,
                enabled_tools=self._enabled_tools,
                tool_count=len(tool_definitions),
            )

            # Step 4: Tool loop with native function calling
            tool_calls_made: List[Dict[str, Any]] = []
            iterations = 0

            while iterations < self.MAX_TOOL_ITERATIONS:
                iterations += 1

                # Call LLM with tools (native function calling)
                response = await self._provider.complete(
                    messages,
                    tools=tool_definitions if tool_definitions else None,
                    user_id=context.user_id,
                    agent_id=self.id,
                    request_id=context.request_id,
                    workflow_id=context.workflow_id,
                )

                # Check if LLM wants to call tools
                if not response.tool_calls:
                    # No more tool calls, return final response
                    confidence = ConfidenceCalculator.from_llm_response(
                        response,
                        tool_calls_made=tool_calls_made,
                        retrieved_docs=retrieval_result.documents,
                        iterations=iterations,
                        max_iterations_reached=False,
                    )
                    return AgentResponse(
                        content=response.content,
                        confidence=confidence,
                        metadata={
                            "model": response.model,
                            "usage": response.usage,
                            "retrieved_count": len(retrieved_docs),
                            "tool_calls": tool_calls_made,
                            "iterations": iterations,
                        },
                    )

                # Build ToolCall objects for the assistant message
                tc_objects = [
                    ToolCall(
                        id=tc.id,
                        name=tc.name,
                        arguments=tc.arguments,
                    )
                    for tc in response.tool_calls
                ]

                # Add assistant message with tool calls
                messages.append(LLMMessage(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=tc_objects,
                ))

                # Execute tools and add results to messages
                for tc in response.tool_calls:
                    tool_result = await self._execute_tool(tc)
                    tool_calls_made.append({
                        "tool": tc.name,
                        "args": tc.arguments,
                        "result": tool_result,
                    })

                    # Add tool result message
                    messages.append(LLMMessage(
                        role="tool",
                        content=json.dumps(tool_result),
                        tool_call_id=tc.id,
                    ))

            # Max iterations reached - calculate confidence with penalty
            signals = ConfidenceSignals(
                tool_calls_total=len(tool_calls_made),
                tool_calls_succeeded=sum(1 for tc in tool_calls_made if tc.get("result", {}).get("success", False)),
                tool_calls_failed=sum(1 for tc in tool_calls_made if not tc.get("result", {}).get("success", False)),
                documents_retrieved=len(retrieved_docs),
                iterations_used=iterations,
                max_iterations_reached=True,
            )
            confidence = ConfidenceCalculator.calculate(signals)

            return AgentResponse(
                content="I've reached the maximum number of tool operations.",
                confidence=confidence,
                metadata={
                    "retrieved_count": len(retrieved_docs),
                    "tool_calls": tool_calls_made,
                    "iterations": iterations,
                    "max_iterations_reached": True,
                },
            )
        finally:
            # Always cleanup KB connection on exit (success or error)
            try:
                await self.close()
            except Exception as cleanup_error:
                logger.warning(
                    "kb_cleanup_error",
                    agent_id=self.id,
                    error=str(cleanup_error),
                )

    def _build_messages(
        self,
        context: AgentContext,
        retrieved_docs: List[str],
        selected_skills: List = None,
    ) -> List[LLMMessage]:
        """Build messages with retrieved context and selected skills."""
        messages = []

        # Build system prompt with selected skills
        system_prompt = self.build_system_prompt(selected_skills=selected_skills)

        # Add retrieved documents to system prompt
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

    async def _execute_tool(self, tool_call: ToolCall) -> Dict[str, Any]:
        """Execute a single tool call with error handling and timeout."""
        import structlog
        logger = structlog.get_logger(__name__)

        tool_name = tool_call.name
        arguments = tool_call.arguments

        # Validate arguments is a dict
        if not isinstance(arguments, dict):
            logger.warning(
                "tool_invalid_arguments",
                tool=tool_name,
                arguments_type=type(arguments).__name__,
            )
            return {
                "success": False,
                "output": None,
                "error": f"Invalid arguments type: expected dict, got {type(arguments).__name__}",
            }

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._registry.execute(tool_name, **arguments),
                timeout=self.TOOL_TIMEOUT_SECONDS,
            )
            return {
                "success": result.success,
                "output": result.output,
                "error": result.error,
            }
        except asyncio.TimeoutError:
            logger.warning(
                "tool_timeout",
                tool=tool_name,
                timeout_seconds=self.TOOL_TIMEOUT_SECONDS,
            )
            return {
                "success": False,
                "output": None,
                "error": f"Tool execution timed out after {self.TOOL_TIMEOUT_SECONDS} seconds",
            }
        except TypeError as e:
            # Argument mismatch (missing required args, unexpected args)
            logger.warning(
                "tool_argument_error",
                tool=tool_name,
                error=str(e),
            )
            return {
                "success": False,
                "output": None,
                "error": f"Tool argument error: {e}",
            }
        except Exception as e:
            # Catch-all for tool execution failures
            logger.error(
                "tool_execution_error",
                tool=tool_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "success": False,
                "output": None,
                "error": f"Tool execution failed: {type(e).__name__}: {e}",
            }

    async def close(self) -> None:
        """Close connections."""
        if self._kb_initialized:
            await self._kb.close()
            self._kb_initialized = False
