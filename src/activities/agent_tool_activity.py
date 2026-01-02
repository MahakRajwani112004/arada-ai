"""Agent Tool Activity - executes agents as tools within workflows."""
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from temporalio import activity
from temporalio.client import Client

from src.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AgentToolExecutionInput:
    """Input for agent tool execution."""

    agent_id: str
    query: str
    user_id: str  # Required for user-level analytics
    context: Dict[str, Any] = field(default_factory=dict)
    current_depth: int = 0
    max_depth: int = 3
    parent_session_id: Optional[str] = None


@dataclass
class AgentToolExecutionOutput:
    """Output from agent tool execution."""

    success: bool
    content: str
    agent_id: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@activity.defn
async def execute_agent_as_tool(
    input: AgentToolExecutionInput,
) -> AgentToolExecutionOutput:
    """
    Execute an agent as a tool via Temporal workflow.

    This activity:
    1. Checks depth limit to prevent infinite recursion
    2. Loads the agent configuration
    3. Starts a new AgentWorkflow as a child execution
    4. Returns the result

    Args:
        input: Agent execution input with query and context

    Returns:
        AgentToolExecutionOutput with agent's response
    """
    activity.logger.info(
        f"Executing agent as tool: {input.agent_id}, "
        f"depth={input.current_depth}/{input.max_depth}"
    )

    # Check depth limit
    if input.current_depth >= input.max_depth:
        return AgentToolExecutionOutput(
            success=False,
            content="",
            agent_id=input.agent_id,
            error=f"Maximum agent nesting depth ({input.max_depth}) exceeded",
        )

    # Temporal client reference for cleanup
    client = None

    try:
        # Import here to avoid circular dependencies
        from src.storage import PostgresAgentRepository
        from src.storage.database import get_session

        # Get agent configuration using async context manager properly
        config = None
        async for session in get_session():
            try:
                repository = PostgresAgentRepository(session)
                config = await repository.get(input.agent_id)
            finally:
                # Session cleanup handled by async generator
                break

        if not config:
            return AgentToolExecutionOutput(
                success=False,
                content="",
                agent_id=input.agent_id,
                error=f"Agent not found: {input.agent_id}",
            )

        # Connect to Temporal (will be closed in finally block)
        temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
        client = await Client.connect(temporal_host)

        # Build workflow input
        from src.agents.factory import AgentFactory
        from src.workflows.agent_workflow import AgentWorkflow, AgentWorkflowInput

        # Create agent instance to build system prompt
        agent = AgentFactory.create(config)
        system_prompt = agent.build_system_prompt()

        # Build conversation history from context
        conversation_history = input.context.get("conversation_history", [])

        # Add additional context to the query if provided
        additional_context = input.context.get("additional_context", "")
        full_query = input.query
        if additional_context:
            full_query = f"{input.query}\n\nContext: {additional_context}"

        workflow_input = AgentWorkflowInput(
            agent_id=config.id,
            agent_type=config.agent_type.value,
            user_input=full_query,
            user_id=input.user_id,
            conversation_history=conversation_history,
            session_id=input.parent_session_id,
            system_prompt=system_prompt,
            safety_level=config.safety.level.value if config.safety else "standard",
            blocked_topics=config.safety.blocked_topics if config.safety else [],
        )

        # Add LLM config
        if config.llm_config:
            workflow_input.llm_provider = config.llm_config.provider
            workflow_input.llm_model = config.llm_config.model
            workflow_input.llm_temperature = config.llm_config.temperature
            workflow_input.llm_max_tokens = config.llm_config.max_tokens

        # Add knowledge base config
        if config.knowledge_base:
            workflow_input.knowledge_collection = config.knowledge_base.collection_name
            workflow_input.embedding_model = config.knowledge_base.embedding_model
            workflow_input.top_k = config.knowledge_base.top_k
            workflow_input.similarity_threshold = config.knowledge_base.similarity_threshold

        # Add tool config - but filter out agent: tools to prevent infinite loops
        if config.tools:
            enabled_tools = [
                t.tool_id
                for t in config.tools
                if t.enabled and not t.tool_id.startswith("agent:")
            ]
            workflow_input.enabled_tools = enabled_tools

        # Add routing table
        if config.routing_table:
            workflow_input.routing_table = config.routing_table

        # Generate unique workflow ID for this agent execution
        workflow_id = f"agent-tool-{input.agent_id}-{uuid.uuid4().hex[:8]}"

        # Execute the workflow
        task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "agent-tasks")

        activity.logger.info(f"Starting child workflow: {workflow_id}")

        result = await client.execute_workflow(
            AgentWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue=task_queue,
        )

        activity.logger.info(
            f"Agent tool execution completed: {input.agent_id}, "
            f"success={result.success}"
        )

        return AgentToolExecutionOutput(
            success=result.success,
            content=result.content,
            agent_id=input.agent_id,
            error=result.error,
            metadata=result.metadata,
        )

    except Exception as e:
        activity.logger.error(f"Agent tool execution failed: {e}")
        return AgentToolExecutionOutput(
            success=False,
            content="",
            agent_id=input.agent_id,
            error=str(e),
        )
    finally:
        # Always close the Temporal client to prevent resource leaks
        if client is not None:
            try:
                await client.close()
            except Exception as close_error:
                activity.logger.warning(f"Failed to close Temporal client: {close_error}")


@dataclass
class GetAgentToolDefinitionsInput:
    """Input for getting agent tool definitions."""

    agent_ids: List[str]


@dataclass
class AgentToolDefinitionInfo:
    """Agent tool definition for serialization."""

    name: str  # agent:{agent_id}
    agent_id: str
    description: str
    parameters: List[Dict[str, Any]]


@dataclass
class GetAgentToolDefinitionsOutput:
    """Output with agent tool definitions."""

    definitions: List[AgentToolDefinitionInfo]


@activity.defn
async def get_agent_tool_definitions(
    input: GetAgentToolDefinitionsInput,
) -> GetAgentToolDefinitionsOutput:
    """
    Get tool definitions for agents.

    This allows agents to be included in tool lists for LLM function calling.
    """
    from src.storage import PostgresAgentRepository
    from src.storage.database import get_session
    from src.tools.agent_tool import AgentTool

    definitions = []

    # Get repository via session context manager
    async for session in get_session():
        repository = PostgresAgentRepository(session)
        for agent_id in input.agent_ids:
            config = await repository.get(agent_id)
            if config:
                agent_tool = AgentTool(config)
                defn = agent_tool.definition

                definitions.append(
                    AgentToolDefinitionInfo(
                        name=defn.name,
                        agent_id=agent_id,
                        description=defn.description,
                        parameters=[
                            {
                                "name": p.name,
                                "type": p.type,
                                "description": p.description,
                                "required": p.required,
                            }
                            for p in defn.parameters
                        ],
                    )
                )
        break  # Only need one iteration

    return GetAgentToolDefinitionsOutput(definitions=definitions)
