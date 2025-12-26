"""SimpleAgent Activity - executes SimpleAgent pattern matching."""
from dataclasses import dataclass, field
from typing import Any, Dict

from temporalio import activity

from src.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SimpleAgentInput:
    """Input for SimpleAgent execution."""

    agent_id: str
    user_input: str
    user_id: str


@dataclass
class SimpleAgentOutput:
    """Output from SimpleAgent execution."""

    success: bool
    content: str
    agent_id: str
    error: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@activity.defn
async def execute_simple_agent(input: SimpleAgentInput) -> SimpleAgentOutput:
    """
    Execute SimpleAgent pattern matching.

    This activity loads the agent config and runs the SimpleAgent's
    rule-based pattern matching logic.
    """
    activity.logger.info(f"Executing SimpleAgent: {input.agent_id}")

    try:
        # Import here to avoid circular dependencies
        from src.agents.factory import AgentFactory
        from src.models.responses import AgentContext
        from src.storage import PostgresAgentRepository
        from src.storage.database import get_session

        # Get agent configuration
        async for session in get_session():
            repository = PostgresAgentRepository(session)
            config = await repository.get(input.agent_id)
            break

        if not config:
            return SimpleAgentOutput(
                success=False,
                content="",
                agent_id=input.agent_id,
                error=f"Agent '{input.agent_id}' not found",
            )

        # Create and execute the agent
        agent = AgentFactory.create(config)
        context = AgentContext(
            user_input=input.user_input,
            conversation_history=[],
            session_id=None,
        )

        response = await agent._execute_impl(context)

        activity.logger.info(
            f"SimpleAgent execution completed: {input.agent_id}, "
            f"match_type={response.metadata.get('match_type', 'unknown')}"
        )

        return SimpleAgentOutput(
            success=True,
            content=response.content,
            agent_id=input.agent_id,
            metadata=response.metadata,
        )

    except Exception as e:
        activity.logger.error(f"SimpleAgent execution failed: {e}")
        return SimpleAgentOutput(
            success=False,
            content="",
            agent_id=input.agent_id,
            error=str(e),
        )
