"""Workflow executor for Teams channel.

Provides a simple interface for executing agent workflows from Teams messages.
"""
import asyncio
import os
from dataclasses import asdict
from datetime import timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from temporalio.client import Client
from temporalio.exceptions import TimeoutError as TemporalTimeoutError

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.storage.models import AgentModel
from src.models.agent_config import AgentConfig
from src.workflows.agent_workflow import AgentWorkflow, AgentWorkflowInput
from src.skills.models import Skill
from src.skills.repository import SkillRepository
from src.agents.factory import AgentFactory

logger = structlog.get_logger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "agent-tasks")
WORKFLOW_TIMEOUT_SECONDS = int(os.getenv("WORKFLOW_TIMEOUT_SECONDS", "300"))  # 5 minutes for chat

# Temporal client cache
_temporal_client: Optional[Client] = None
_temporal_client_lock = asyncio.Lock()


async def get_temporal_client() -> Client:
    """Get or create Temporal client with proper locking."""
    global _temporal_client
    if _temporal_client is None:
        async with _temporal_client_lock:
            if _temporal_client is None:
                _temporal_client = await Client.connect(TEMPORAL_HOST)
    return _temporal_client


class TeamsWorkflowExecutor:
    """Simple workflow executor for Teams channel.

    Executes agent workflows and returns responses suitable for Teams messaging.
    """

    def __init__(self, session: AsyncSession, user_id: Optional[str] = None):
        """Initialize executor.

        Args:
            session: Database session for loading agent configs
            user_id: Optional user ID for agent lookup (uses config owner if not set)
        """
        self.session = session
        self.user_id = user_id

    async def execute(
        self,
        agent_id: str,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Execute an agent workflow.

        Args:
            agent_id: ID of the agent to execute
            user_input: User's message
            context: Optional execution context (channel info, etc.)
            conversation_history: Previous messages for context

        Returns:
            Dict with response and metadata
        """
        context = context or {}
        conversation_history = conversation_history or []

        try:
            # Load agent config from database
            stmt = select(AgentModel).where(
                AgentModel.id == agent_id,
                AgentModel.is_active == True,
            )
            result = await self.session.execute(stmt)
            agent_model = result.scalar_one_or_none()

            if not agent_model:
                logger.warning("teams_agent_not_found", agent_id=agent_id)
                return {
                    "response": f"Agent '{agent_id}' not found or is inactive.",
                    "success": False,
                    "error": "Agent not found",
                }

            # Parse agent config
            agent_config = AgentConfig.model_validate(agent_model.config_json)

            # Build workflow input
            workflow_input = await self._build_workflow_input(
                agent_config=agent_config,
                user_input=user_input,
                conversation_history=conversation_history,
                context=context,
            )

            # Execute workflow
            workflow_id = f"teams-{agent_id}-{uuid4().hex[:8]}"

            logger.info(
                "teams_workflow_starting",
                workflow_id=workflow_id,
                agent_id=agent_id,
                channel=context.get("channel", "teams"),
            )

            client = await get_temporal_client()
            result = await client.execute_workflow(
                AgentWorkflow.run,
                workflow_input,
                id=workflow_id,
                task_queue=TASK_QUEUE,
                execution_timeout=timedelta(seconds=WORKFLOW_TIMEOUT_SECONDS),
            )

            logger.info(
                "teams_workflow_completed",
                workflow_id=workflow_id,
                success=result.success,
            )

            return {
                "response": result.content,
                "success": result.success,
                "error": result.error,
                "metadata": result.metadata,
                "workflow_id": workflow_id,
            }

        except TemporalTimeoutError:
            logger.error("teams_workflow_timeout", agent_id=agent_id)
            return {
                "response": "I'm taking longer than expected. Please try again or simplify your request.",
                "success": False,
                "error": "Workflow timed out",
            }

        except ConnectionError as e:
            logger.error("teams_temporal_connection_error", error=str(e))
            return {
                "response": "I'm having trouble connecting to my processing service. Please try again later.",
                "success": False,
                "error": f"Connection error: {e}",
            }

        except Exception as e:
            logger.exception("teams_workflow_error", error=str(e))
            return {
                "response": f"I encountered an error: {str(e)}",
                "success": False,
                "error": str(e),
            }

    async def _build_workflow_input(
        self,
        agent_config: AgentConfig,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        context: Dict[str, Any],
    ) -> AgentWorkflowInput:
        """Build workflow input from agent config.

        Args:
            agent_config: Agent configuration
            user_input: User's message
            conversation_history: Previous messages
            context: Execution context

        Returns:
            AgentWorkflowInput for Temporal workflow
        """
        # Load skills for system prompt
        skills = await self._load_skills(agent_config)

        # Create agent to build system prompt
        agent = AgentFactory.create(agent_config, skills=skills)
        system_prompt = agent.build_system_prompt()

        # Build agent description
        agent_description = agent_config.description or agent_config.name
        if agent_config.goal and agent_config.goal.objective:
            agent_description = f"{agent_description}. Goal: {agent_config.goal.objective}"

        workflow_input = AgentWorkflowInput(
            agent_id=agent_config.id,
            agent_type=agent_config.agent_type.value,
            user_input=user_input,
            user_id=self.user_id or "teams-user",
            conversation_history=conversation_history,
            session_id=context.get("conversation_id"),
            system_prompt=system_prompt,
            safety_level=agent_config.safety.level.value if agent_config.safety else "standard",
            blocked_topics=agent_config.safety.blocked_topics if agent_config.safety else [],
            agent_description=agent_description,
        )

        # Add LLM config
        if agent_config.llm_config:
            workflow_input.llm_provider = agent_config.llm_config.provider
            workflow_input.llm_model = agent_config.llm_config.model
            workflow_input.llm_temperature = agent_config.llm_config.temperature
            workflow_input.llm_max_tokens = agent_config.llm_config.max_tokens

        # Add knowledge base config
        if agent_config.knowledge_base:
            workflow_input.knowledge_collection = agent_config.knowledge_base.collection_name
            workflow_input.embedding_model = agent_config.knowledge_base.embedding_model
            workflow_input.top_k = agent_config.knowledge_base.top_k
            workflow_input.similarity_threshold = agent_config.knowledge_base.similarity_threshold

        # Add enabled tools
        if agent_config.tools:
            workflow_input.enabled_tools = [t.tool_id for t in agent_config.tools if t.enabled]

        # Add routing table
        if agent_config.routing_table:
            workflow_input.routing_table = agent_config.routing_table

        # Add orchestrator config
        if agent_config.orchestrator_config:
            workflow_input.orchestrator_mode = agent_config.orchestrator_config.mode.value
            workflow_input.orchestrator_max_parallel = agent_config.orchestrator_config.max_parallel
            workflow_input.orchestrator_max_depth = agent_config.orchestrator_config.max_depth
            workflow_input.orchestrator_aggregation = agent_config.orchestrator_config.default_aggregation.value
            workflow_input.orchestrator_available_agents = [
                {
                    "agent_id": a.agent_id,
                    "alias": a.alias,
                    "description": a.description,
                }
                for a in agent_config.orchestrator_config.available_agents
            ]

        return workflow_input

    async def _load_skills(self, agent_config: AgentConfig) -> List[Skill]:
        """Load skills from database for agent config.

        Args:
            agent_config: Agent configuration with skills list

        Returns:
            List of Skill objects
        """
        if not agent_config.skills:
            return []

        skill_ids = [
            skill_config.skill_id
            for skill_config in agent_config.skills
            if skill_config.enabled
        ]

        if not skill_ids:
            return []

        try:
            skill_repo = SkillRepository(self.session)
            skills = await skill_repo.get_many(skill_ids)
            logger.debug("teams_skills_loaded", count=len(skills))
            return skills
        except Exception as e:
            logger.warning("teams_skills_load_failed", error=str(e))
            return []
