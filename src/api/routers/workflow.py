"""Workflow execution API routes."""
import os
from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, status
from temporalio.client import Client, WorkflowFailureError
from temporalio.exceptions import TimeoutError as TemporalTimeoutError

from src.api.dependencies import get_repository
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
from src.storage import BaseAgentRepository
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
    http_request: Request,
    repository: BaseAgentRepository = Depends(get_repository),
) -> ExecuteAgentResponse:
    """Execute an agent workflow."""
    request_id = getattr(http_request.state, "request_id", None)

    # Get agent config
    config = await repository.get(request.agent_id)
    if not config:
        raise NotFoundError(resource="Agent", identifier=request.agent_id)

    # Build workflow input
    workflow_input = AgentWorkflowInput(
        agent_id=config.id,
        agent_type=config.agent_type.value,
        user_input=request.user_input,
        conversation_history=[
            {"role": m.role, "content": m.content}
            for m in request.conversation_history
        ],
        session_id=request.session_id,
        system_prompt=_build_system_prompt(config),
        safety_level=config.safety.level.value,
        blocked_topics=config.safety.blocked_topics,
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


def _build_system_prompt(config) -> str:
    """Build system prompt from agent config."""
    from src.agents.factory import AgentFactory

    agent = AgentFactory.create(config)
    return agent.build_system_prompt()
