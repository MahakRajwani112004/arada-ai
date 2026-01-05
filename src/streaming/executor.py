"""Streaming executor for agent workflow execution with progress events."""
import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

from src.streaming.events import (
    StreamEvent,
    StreamEventType,
    chunk_event,
    complete_event,
    error_event,
    generating_event,
    message_saved_event,
    mcp_end_event,
    mcp_start_event,
    retrieved_event,
    retrieving_event,
    skill_end_event,
    skill_start_event,
    thinking_event,
    tool_end_event,
    tool_start_event,
)
from src.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StreamingExecutionContext:
    """Context for a streaming execution."""

    conversation_id: str
    user_id: str
    agent_id: str
    user_input: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # Execution tracking
    execution_id: Optional[str] = None
    workflow_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Result
    response_content: str = ""
    success: bool = False
    error: Optional[str] = None


class StreamingExecutor:
    """Executes agent workflows with streaming progress events.

    This executor wraps the Temporal workflow execution and emits
    progress events that can be streamed to the client via SSE.

    Since Temporal workflows are durable and don't support direct streaming,
    this executor provides simulated progress events based on typical
    agent execution patterns, with the actual response delivered at the end.
    """

    def __init__(self, user_id: str):
        """Initialize with user context."""
        self.user_id = user_id

    async def execute(
        self,
        agent_id: str,
        user_input: str,
        conversation_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Execute agent workflow with streaming events.

        Args:
            agent_id: The agent to execute
            user_input: User's message
            conversation_id: Conversation to add message to
            conversation_history: Previous messages for context

        Yields:
            StreamEvent: Progress events during execution
        """
        context = StreamingExecutionContext(
            conversation_id=conversation_id,
            user_id=self.user_id,
            agent_id=agent_id,
            user_input=user_input,
            conversation_history=conversation_history or [],
            execution_id=f"exec-{uuid.uuid4().hex[:12]}",
            started_at=datetime.now(timezone.utc),
        )

        try:
            # Emit user message saved
            yield message_saved_event(role="user")

            # Emit thinking event
            yield thinking_event(step="Understanding your request")

            # Execute the actual workflow
            async for event in self._execute_workflow(context):
                yield event

        except Exception as e:
            logger.exception("streaming_execution_error", error=str(e))
            yield error_event(
                error=str(e),
                error_type=type(e).__name__,
                recoverable=False,
            )

    async def _execute_workflow(
        self, context: StreamingExecutionContext
    ) -> AsyncIterator[StreamEvent]:
        """Execute the workflow and yield events.

        This method wraps the actual Temporal workflow execution.
        """
        from temporalio.client import Client
        from src.workflows.agent_workflow import AgentWorkflowInput, AgentWorkflowOutput

        try:
            # Get agent config to determine execution path
            from sqlalchemy import select
            from src.storage import get_async_session
            from src.storage.models import AgentModel
            from src.models.agent_config import AgentConfig

            async with get_async_session() as session:
                stmt = select(AgentModel).where(
                    AgentModel.id == context.agent_id,
                    AgentModel.user_id == context.user_id,
                    AgentModel.is_active == True,
                )
                result = await session.execute(stmt)
                agent_model = result.scalar_one_or_none()

                if not agent_model:
                    yield error_event(
                        error=f"Agent '{context.agent_id}' not found",
                        error_type="NotFoundError",
                        recoverable=False,
                    )
                    return

                agent_config = AgentConfig.model_validate(agent_model.config_json)

            # Emit events based on agent capabilities
            agent_type = agent_config.agent_type.value

            # RAG retrieval events
            if agent_config.knowledge_base:
                yield retrieving_event(
                    knowledge_base_name=agent_config.knowledge_base.name
                    if hasattr(agent_config.knowledge_base, "name")
                    else "Knowledge Base",
                    query_preview=context.user_input[:100],
                )
                # Small delay for UX
                await asyncio.sleep(0.1)
                yield retrieved_event(document_count=0, chunks_used=0)

            # Skill events
            if agent_config.skills:
                for skill in agent_config.skills[:3]:  # Limit shown skills
                    skill_name = skill.skill_id if hasattr(skill, "skill_id") else str(skill)
                    yield skill_start_event(skill_name=skill_name, skill_id=skill_name)
                    await asyncio.sleep(0.05)
                    yield skill_end_event(skill_name=skill_name, skill_id=skill_name)

            # Tool events (preview - actual tools may be called during execution)
            if agent_config.tools:
                for tool in agent_config.tools[:2]:  # Preview first 2 tools
                    tool_id = tool.tool_id if hasattr(tool, "tool_id") else str(tool)
                    if ":" in tool_id:
                        # MCP tool
                        parts = tool_id.split(":", 1)
                        server_name = parts[0]
                        tool_name = parts[1] if len(parts) > 1 else tool_id
                        yield mcp_start_event(server_name=server_name, tool_name=tool_name)
                    else:
                        yield tool_start_event(tool_name=tool_id)

            # Generate response event
            yield generating_event()

            # Execute workflow via Temporal
            from src.config.settings import get_settings

            settings = get_settings()
            client = await Client.connect(settings.temporal_host)

            # Build workflow input
            workflow_input = self._build_workflow_input(agent_config, context)

            # Generate workflow ID
            workflow_id = f"agent-{context.agent_id}-{uuid.uuid4().hex[:8]}"
            context.workflow_id = workflow_id

            # Start and wait for workflow
            result = await client.execute_workflow(
                "AgentWorkflow",
                workflow_input,
                id=workflow_id,
                task_queue="agent-tasks",
            )

            # Complete tool events if we started any
            if agent_config.tools:
                for tool in agent_config.tools[:2]:
                    tool_id = tool.tool_id if hasattr(tool, "tool_id") else str(tool)
                    if ":" in tool_id:
                        parts = tool_id.split(":", 1)
                        server_name = parts[0]
                        tool_name = parts[1] if len(parts) > 1 else tool_id
                        yield mcp_end_event(
                            server_name=server_name, tool_name=tool_name, success=True
                        )
                    else:
                        yield tool_end_event(tool_name=tool_id, success=True)

            # Parse result
            if isinstance(result, dict):
                output = AgentWorkflowOutput(**result)
            else:
                output = result

            context.response_content = output.content
            context.success = output.success
            context.completed_at = datetime.now(timezone.utc)

            if not output.success:
                yield error_event(
                    error=output.error or "Workflow execution failed",
                    error_type="WorkflowError",
                    recoverable=False,
                )
                return

            # Stream the response in chunks for natural feel
            content = output.content
            chunk_size = 50  # Characters per chunk
            for i in range(0, len(content), chunk_size):
                chunk = content[i : i + chunk_size]
                yield chunk_event(content=chunk)
                await asyncio.sleep(0.02)  # 20ms delay between chunks

            # Complete event
            yield complete_event(
                message_id="",  # Will be set by caller after saving
                total_tokens=output.metadata.get("total_tokens") if output.metadata else None,
                execution_id=context.execution_id,
            )

        except Exception as e:
            logger.exception("workflow_execution_error", error=str(e))
            yield error_event(
                error=str(e),
                error_type=type(e).__name__,
                recoverable=False,
            )

    def _build_workflow_input(
        self, agent_config: Any, context: StreamingExecutionContext
    ) -> Dict[str, Any]:
        """Build workflow input from agent config and context."""
        from src.models.enums import AgentType

        # Build system prompt from role, goal, and instructions
        system_prompt_parts = []

        # Role section
        if agent_config.role:
            role = agent_config.role
            system_prompt_parts.append(f"You are a {role.title}.")
            if role.expertise:
                system_prompt_parts.append(f"Areas of expertise: {', '.join(role.expertise)}.")
            if role.personality:
                system_prompt_parts.append(f"Personality: {', '.join(role.personality)}.")
            if role.communication_style:
                system_prompt_parts.append(f"Communication style: {role.communication_style}.")

        # Goal section
        if agent_config.goal:
            goal = agent_config.goal
            system_prompt_parts.append(f"\nObjective: {goal.objective}")
            if goal.constraints:
                system_prompt_parts.append(f"Constraints: {'; '.join(goal.constraints)}")

        # Instructions section
        if agent_config.instructions:
            instructions = agent_config.instructions
            if instructions.steps:
                system_prompt_parts.append("\nSteps to follow:")
                for i, step in enumerate(instructions.steps, 1):
                    system_prompt_parts.append(f"{i}. {step}")
            if instructions.rules:
                system_prompt_parts.append("\nRules:")
                for rule in instructions.rules:
                    system_prompt_parts.append(f"- {rule}")
            if instructions.prohibited:
                system_prompt_parts.append("\nDo NOT:")
                for item in instructions.prohibited:
                    system_prompt_parts.append(f"- {item}")
            if instructions.output_format:
                system_prompt_parts.append(f"\nOutput format: {instructions.output_format}")

        system_prompt = "\n".join(system_prompt_parts)

        # Build workflow input
        input_data = {
            "agent_id": context.agent_id,
            "agent_type": agent_config.agent_type.value,
            "user_input": context.user_input,
            "user_id": context.user_id,
            "conversation_history": context.conversation_history,
            "llm_provider": agent_config.llm_config.provider if agent_config.llm_config else "openai",
            "llm_model": agent_config.llm_config.model if agent_config.llm_config else "gpt-4o",
            "llm_temperature": agent_config.llm_config.temperature if agent_config.llm_config else 0.0,
            "llm_max_tokens": agent_config.llm_config.max_tokens if agent_config.llm_config else 1024,
            "system_prompt": system_prompt,
            "safety_level": agent_config.safety.level.value if agent_config.safety else "standard",
            "blocked_topics": agent_config.safety.blocked_topics if agent_config.safety else [],
        }

        # RAG config
        if agent_config.knowledge_base:
            kb = agent_config.knowledge_base
            input_data["knowledge_collection"] = kb.collection_name if hasattr(kb, "collection_name") else None
            input_data["embedding_model"] = kb.embedding_model if hasattr(kb, "embedding_model") else "text-embedding-3-small"
            input_data["top_k"] = kb.top_k if hasattr(kb, "top_k") else 5
            input_data["similarity_threshold"] = kb.similarity_threshold if hasattr(kb, "similarity_threshold") else None

        # Tools config
        if agent_config.tools:
            input_data["enabled_tools"] = [
                t.tool_id if hasattr(t, "tool_id") else str(t) for t in agent_config.tools
            ]

        return input_data


async def execute_with_streaming(
    agent_id: str,
    user_input: str,
    user_id: str,
    conversation_id: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> AsyncIterator[StreamEvent]:
    """Convenience function to execute agent with streaming.

    Args:
        agent_id: The agent to execute
        user_input: User's message
        user_id: The user making the request
        conversation_id: Conversation to add messages to
        conversation_history: Previous messages for context

    Yields:
        StreamEvent: Progress events during execution
    """
    executor = StreamingExecutor(user_id)
    async for event in executor.execute(
        agent_id=agent_id,
        user_input=user_input,
        conversation_id=conversation_id,
        conversation_history=conversation_history,
    ):
        yield event
