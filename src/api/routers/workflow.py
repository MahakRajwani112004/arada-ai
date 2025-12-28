"""Workflow execution API routes."""
import os
from datetime import timedelta
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio.client import Client, WorkflowFailureError
from temporalio.exceptions import TimeoutError as TemporalTimeoutError

from src.api.dependencies import get_repository, get_workflow_repository
from src.auth.dependencies import CurrentUser
from src.api.errors import (
    ExternalServiceError,
    NotFoundError,
    WorkflowError,
    WorkflowTimeoutError,
)
from src.api.schemas.workflow import (
    ExecuteAgentRequest,
    ExecuteAgentResponse,
    WorkflowStatusResponse,
)
from src.config.logging import get_logger
from src.skills.models import Skill
from src.skills.repository import SkillRepository
from src.storage import BaseAgentRepository
from src.storage.database import get_session
from src.storage.workflow_repository import WorkflowRepository
from src.workflows.agent_workflow import AgentWorkflow, AgentWorkflowInput

router = APIRouter(prefix="/workflow", tags=["workflow"])
logger = get_logger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "agent-tasks")
WORKFLOW_TIMEOUT_SECONDS = int(os.getenv("WORKFLOW_TIMEOUT_SECONDS", "600"))  # 10 minutes default

# Temporal client (lazy initialization)
_temporal_client = None


async def get_temporal_client() -> Client:
    """Get or create Temporal client."""
    global _temporal_client
    if _temporal_client is None:
        _temporal_client = await Client.connect(TEMPORAL_HOST)
    return _temporal_client


@router.post("/execute", response_model=ExecuteAgentResponse)
async def execute_agent(
    request: ExecuteAgentRequest,
    current_user: CurrentUser,
    http_request: Request,
    repository: BaseAgentRepository = Depends(get_repository),
    workflow_repo: Optional[WorkflowRepository] = Depends(get_workflow_repository),
    session: AsyncSession = Depends(get_session),
) -> ExecuteAgentResponse:
    """Execute an agent workflow."""
    request_id = getattr(http_request.state, "request_id", None)
    execution_id: Optional[str] = None

    # Get agent config
    config = await repository.get(request.agent_id)
    if not config:
        raise NotFoundError(resource="Agent", identifier=request.agent_id)

    # Build workflow input with skills loaded from DB
    system_prompt = await _build_system_prompt_async(config, session)

    # Build agent description for action validator
    agent_description = config.description or config.name
    if config.goal and config.goal.objective:
        agent_description = f"{agent_description}. Goal: {config.goal.objective}"

    workflow_input = AgentWorkflowInput(
        agent_id=config.id,
        agent_type=config.agent_type.value,
        user_input=request.user_input,
        user_id=current_user.id,
        conversation_history=[
            {"role": m.role, "content": m.content}
            for m in request.conversation_history
        ],
        session_id=request.session_id,
        system_prompt=system_prompt,
        safety_level=config.safety.level.value,
        blocked_topics=config.safety.blocked_topics,
        agent_description=agent_description,
    )

    # Add LLM config if present
    if config.llm_config:
        workflow_input.llm_provider = config.llm_config.provider
        workflow_input.llm_model = config.llm_config.model
        workflow_input.llm_temperature = config.llm_config.temperature
        workflow_input.llm_max_tokens = config.llm_config.max_tokens

    # Add knowledge base config if present
    if config.knowledge_base:
        workflow_input.knowledge_collection = config.knowledge_base.collection_name
        workflow_input.embedding_model = config.knowledge_base.embedding_model
        workflow_input.top_k = config.knowledge_base.top_k
        workflow_input.similarity_threshold = config.knowledge_base.similarity_threshold

    # Add tool config if present
    workflow_input.enabled_tools = [t.tool_id for t in config.tools if t.enabled]

    # Add routing table if present
    if config.routing_table:
        workflow_input.routing_table = config.routing_table

    # Add orchestrator config if present
    if config.orchestrator_config:
        workflow_input.orchestrator_mode = config.orchestrator_config.mode.value
        workflow_input.orchestrator_available_agents = [
            {
                "agent_id": a.agent_id,
                "alias": a.alias,
                "description": a.description,
            }
            for a in config.orchestrator_config.available_agents
        ]
        workflow_input.orchestrator_max_parallel = config.orchestrator_config.max_parallel
        workflow_input.orchestrator_max_depth = config.orchestrator_config.max_depth
        workflow_input.orchestrator_aggregation = config.orchestrator_config.default_aggregation.value

    # Add workflow definition if provided in request (for WORKFLOW mode)
    if request.workflow_definition:
        workflow_input.workflow_definition = request.workflow_definition
        # Override mode to workflow if definition is provided
        workflow_input.orchestrator_mode = "workflow"

    # Execute workflow
    workflow_id = f"agent-{config.id}-{uuid4().hex[:8]}"

    logger.info(
        "workflow_execution_started",
        workflow_id=workflow_id,
        agent_id=config.id,
        request_id=request_id,
    )

    # Create execution record if tracking a saved workflow
    if request.source_workflow_id and workflow_repo:
        try:
            execution_id = await workflow_repo.create_execution(
                workflow_id=request.source_workflow_id,
                temporal_workflow_id=workflow_id,
                input_data={
                    "agent_id": request.agent_id,
                    "user_input": request.user_input,
                    "session_id": request.session_id,
                },
                triggered_by="api",
            )
            logger.info(
                "execution_record_created",
                execution_id=execution_id,
                source_workflow_id=request.source_workflow_id,
            )
        except Exception as e:
            # Log but don't fail if execution tracking fails
            logger.warning(
                "execution_record_creation_failed",
                source_workflow_id=request.source_workflow_id,
                error=str(e),
            )

    try:
        client = await get_temporal_client()

        result = await client.execute_workflow(
            AgentWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue=TASK_QUEUE,
            execution_timeout=timedelta(seconds=WORKFLOW_TIMEOUT_SECONDS),
        )

        logger.info(
            "workflow_execution_completed",
            workflow_id=workflow_id,
            success=result.success,
            request_id=request_id,
        )

        # Update execution record on success
        if execution_id and workflow_repo:
            try:
                await workflow_repo.update_execution(
                    execution_id=execution_id,
                    status="COMPLETED" if result.success else "FAILED",
                    output_data={
                        "content": result.content,
                        "metadata": result.metadata,
                    },
                    error=result.error,
                    steps_executed=[config.id],
                    step_results={config.id: {"success": result.success}},
                )
            except Exception as e:
                logger.warning(
                    "execution_record_update_failed",
                    execution_id=execution_id,
                    error=str(e),
                )

        return ExecuteAgentResponse(
            content=result.content,
            agent_id=result.agent_id,
            agent_type=result.agent_type,
            success=result.success,
            error=result.error,
            metadata=result.metadata,
            workflow_id=workflow_id,
        )

    except TemporalTimeoutError:
        logger.error(
            "workflow_timeout",
            workflow_id=workflow_id,
            timeout_seconds=WORKFLOW_TIMEOUT_SECONDS,
            request_id=request_id,
        )
        # Update execution record on timeout
        if execution_id and workflow_repo:
            try:
                await workflow_repo.update_execution(
                    execution_id=execution_id,
                    status="FAILED",
                    error=f"Workflow timed out after {WORKFLOW_TIMEOUT_SECONDS} seconds",
                )
            except Exception:
                pass
        raise WorkflowTimeoutError(
            workflow_id=workflow_id,
            timeout_seconds=WORKFLOW_TIMEOUT_SECONDS,
        )

    except WorkflowFailureError as e:
        logger.error(
            "workflow_failed",
            workflow_id=workflow_id,
            error=str(e),
            request_id=request_id,
        )
        # Update execution record on failure
        if execution_id and workflow_repo:
            try:
                await workflow_repo.update_execution(
                    execution_id=execution_id,
                    status="FAILED",
                    error=str(e),
                )
            except Exception:
                pass
        raise WorkflowError(
            message="Workflow execution failed",
            workflow_id=workflow_id,
        )

    except ConnectionError as e:
        logger.error(
            "temporal_connection_error",
            workflow_id=workflow_id,
            error=str(e),
            request_id=request_id,
        )
        # Update execution record on connection error
        if execution_id and workflow_repo:
            try:
                await workflow_repo.update_execution(
                    execution_id=execution_id,
                    status="FAILED",
                    error=f"Temporal connection error: {e}",
                )
            except Exception:
                pass
        raise ExternalServiceError(
            service="Temporal",
            message="Failed to connect to workflow service",
        )

    except Exception as e:
        logger.error(
            "workflow_unexpected_error",
            workflow_id=workflow_id,
            error_type=type(e).__name__,
            error=str(e),
            request_id=request_id,
            exc_info=True,
        )
        # Update execution record on unexpected error
        if execution_id and workflow_repo:
            try:
                await workflow_repo.update_execution(
                    execution_id=execution_id,
                    status="FAILED",
                    error=f"{type(e).__name__}: {e}",
                )
            except Exception:
                pass
        raise WorkflowError(
            message="An unexpected error occurred during workflow execution",
            workflow_id=workflow_id,
        )


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str) -> WorkflowStatusResponse:
    """Get workflow status."""
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        description = await handle.describe()

        status_str = description.status.name

        result = None
        if status_str == "COMPLETED":
            workflow_result = await handle.result()
            result = ExecuteAgentResponse(
                content=workflow_result.content,
                agent_id=workflow_result.agent_id,
                agent_type=workflow_result.agent_type,
                success=workflow_result.success,
                error=workflow_result.error,
                metadata=workflow_result.metadata,
                workflow_id=workflow_id,
            )

        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status=status_str,
            result=result,
        )

    except ConnectionError:
        raise ExternalServiceError(
            service="Temporal",
            message="Failed to connect to workflow service",
        )

    except Exception as e:
        logger.warning(
            "workflow_status_lookup_failed",
            workflow_id=workflow_id,
            error=str(e),
        )
        raise NotFoundError(resource="Workflow", identifier=workflow_id)


async def _load_skills_for_agent(config, session: AsyncSession) -> List[Skill]:
    """Load skills from database for an agent config.

    Args:
        config: Agent configuration with skills list
        session: Database session

    Returns:
        List of loaded Skill objects
    """
    if not config.skills:
        return []

    skills = []
    skill_repo = SkillRepository(session)

    for skill_config in config.skills:
        if not skill_config.enabled:
            continue
        try:
            skill = await skill_repo.get(skill_config.skill_id)
            if skill:
                skills.append(skill)
                logger.debug("skill_loaded", skill_id=skill_config.skill_id)
            else:
                logger.warning("skill_not_found", skill_id=skill_config.skill_id)
        except Exception as e:
            logger.error("skill_load_failed", skill_id=skill_config.skill_id, error=str(e))

    return skills


async def _build_system_prompt_async(config, session: AsyncSession) -> str:
    """Build system prompt from agent config with skills loaded from DB.

    Args:
        config: Agent configuration
        session: Database session for loading skills

    Returns:
        Complete system prompt string
    """
    from src.agents.factory import AgentFactory

    # Load skills from database
    skills = await _load_skills_for_agent(config, session)

    # Create agent with skills
    agent = AgentFactory.create(config, skills=skills)
    return agent.build_system_prompt()


def _build_system_prompt(config) -> str:
    """Build system prompt from agent config (without skills - legacy).

    DEPRECATED: Use _build_system_prompt_async for full skill support.
    """
    from src.agents.factory import AgentFactory

    agent = AgentFactory.create(config)
    return agent.build_system_prompt()
