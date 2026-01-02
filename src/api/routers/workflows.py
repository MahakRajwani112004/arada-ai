"""Workflow API routes for CRUD, resource discovery, and AI generation."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies import (
    get_mcp_manager,
    get_mcp_repository,
    get_repository,
    get_schedule_repository,
    get_workflow_repository,
)
from src.auth.dependencies import CurrentUser
from src.api.schemas.workflows import (
    ApplyGeneratedWorkflowRequest,
    ApplyGeneratedWorkflowResponse,
    AvailableAgentResponse,
    AvailableAgentsResponse,
    AvailableMCPServerResponse,
    AvailableMCPsResponse,
    AvailableToolResponse,
    AvailableToolsResponse,
    CopyWorkflowRequest,
    CreateScheduleRequest,
    CreateWorkflowRequest,
    ExecuteWorkflowRequest,
    ExecuteWorkflowResponse,
    GenerateSkeletonRequest,
    GenerateSkeletonResponse,
    GenerateWorkflowRequest,
    GenerateWorkflowResponse,
    MCPToolResponse,
    ScheduleListResponse,
    SchedulePreviewRequest,
    ScheduleResponse,
    StepExecutionResult,
    UpdateScheduleRequest,
    UpdateWorkflowRequest,
    ValidateCronRequest,
    ValidateCronResponse,
    ValidateWorkflowRequest,
    ValidateWorkflowResponse,
    ValidationError,
    WorkflowExecutionListResponse,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowSummaryResponse,
)
from src.mcp.repository import MCPServerRepository
from src.models.workflow_definition import validate_workflow_definition as validate_definition
from src.storage import BaseAgentRepository
from src.storage.schedule_repository import ScheduleRepository
from src.storage.workflow_repository import (
    WorkflowFilters,
    WorkflowMetadata,
    WorkflowRepository,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


# ==================== Workflow CRUD ====================


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    request: CreateWorkflowRequest,
    current_user: CurrentUser,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowResponse:
    """Create a new workflow."""
    # Check if workflow already exists
    if await workflow_repo.exists(request.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow with ID '{request.id}' already exists",
        )

    # Validate the workflow definition
    try:
        # exclude_none to avoid passing None values to the strict validator
        definition_dict = request.definition.model_dump(exclude_none=True)
        validate_definition(definition_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow definition: {str(e)}",
        )

    # Save workflow
    metadata = WorkflowMetadata(
        name=request.name,
        description=request.description,
        category=request.category,
        tags=request.tags,
        created_by=request.created_by,
    )
    workflow = await workflow_repo.save(request.id, definition_dict, metadata)

    # Return the created workflow (save now returns the full workflow)
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        category=workflow.category,
        tags=workflow.tags,
        definition=workflow.definition,
        version=workflow.version,
        is_template=workflow.is_template,
        is_active=workflow.is_active,
        source_template_id=workflow.source_template_id,
        created_by=workflow.created_by,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    current_user: CurrentUser,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_template: Optional[bool] = Query(None, description="Filter templates only"),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowListResponse:
    """List all workflows with optional filters."""
    filters = WorkflowFilters(
        category=category,
        is_template=is_template,
        is_active=True,
    )
    workflows = await workflow_repo.list(filters)

    return WorkflowListResponse(
        workflows=[
            WorkflowSummaryResponse(
                id=w.id,
                name=w.name,
                description=w.description,
                category=w.category,
                tags=w.tags,
                version=w.version,
                is_template=w.is_template,
                created_at=w.created_at,
                updated_at=w.updated_at,
            )
            for w in workflows
        ],
        total=len(workflows),
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: CurrentUser,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowResponse:
    """Get workflow by ID."""
    workflow = await workflow_repo.get(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        category=workflow.category,
        tags=workflow.tags,
        definition=workflow.definition,
        version=workflow.version,
        is_template=workflow.is_template,
        is_active=workflow.is_active,
        source_template_id=workflow.source_template_id,
        created_by=workflow.created_by,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    request: UpdateWorkflowRequest,
    current_user: CurrentUser,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowResponse:
    """Update a workflow."""
    # Get existing workflow
    existing = await workflow_repo.get(workflow_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Prepare updated values
    definition = existing.definition
    if request.definition:
        try:
            definition = request.definition.model_dump(exclude_none=True)
            validate_definition(definition)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow definition: {str(e)}",
            )

    metadata = WorkflowMetadata(
        name=request.name if request.name else existing.name,
        description=request.description if request.description is not None else existing.description,
        category=request.category if request.category else existing.category,
        tags=request.tags if request.tags is not None else existing.tags,
        is_template=existing.is_template,
        source_template_id=existing.source_template_id,
        created_by=existing.created_by,
    )

    workflow = await workflow_repo.save(workflow_id, definition, metadata)

    # Return updated workflow (save now returns the full workflow)
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        category=workflow.category,
        tags=workflow.tags,
        definition=workflow.definition,
        version=workflow.version,
        is_template=workflow.is_template,
        is_active=workflow.is_active,
        source_template_id=workflow.source_template_id,
        created_by=workflow.created_by,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    current_user: CurrentUser,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> None:
    """Delete a workflow (soft delete)."""
    if not await workflow_repo.delete(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )


@router.post("/{workflow_id}/copy", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def copy_workflow(
    workflow_id: str,
    request: CopyWorkflowRequest,
    current_user: CurrentUser,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowResponse:
    """Copy a workflow to a new ID."""
    # Check if new ID already exists
    if await workflow_repo.exists(request.new_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow with ID '{request.new_id}' already exists",
        )

    # Copy the workflow
    new_id = await workflow_repo.copy(
        workflow_id,
        request.new_id,
        request.new_name,
        request.created_by,
    )
    if not new_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Fetch and return the copied workflow
    workflow = await workflow_repo.get(new_id)
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        category=workflow.category,
        tags=workflow.tags,
        definition=workflow.definition,
        version=workflow.version,
        is_template=workflow.is_template,
        is_active=workflow.is_active,
        source_template_id=workflow.source_template_id,
        created_by=workflow.created_by,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


# ==================== Workflow Execution ====================


@router.post("/{workflow_id}/execute", response_model=ExecuteWorkflowResponse)
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    current_user: CurrentUser,
    agent_repo: BaseAgentRepository = Depends(get_repository),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> ExecuteWorkflowResponse:
    """Execute a stored workflow."""
    from src.workflows.executor import WorkflowExecutor

    # Verify workflow exists
    if not await workflow_repo.exists(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Get Temporal client if available
    temporal_client = None
    try:
        from src.api.routers.workflow import get_temporal_client
        temporal_client = await get_temporal_client()
    except Exception:
        # Temporal not available, will use direct execution
        pass

    # Execute workflow
    executor = WorkflowExecutor(
        agent_repo=agent_repo,
        workflow_repo=workflow_repo,
        temporal_client=temporal_client,
    )

    # Convert conversation history to dict format
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in request.conversation_history
    ] if request.conversation_history else []

    execution_id, exec_status, step_results, final_output, error = await executor.execute(
        workflow_id=workflow_id,
        user_input=request.user_input,
        user_id=current_user.id,
        context=request.context,
        session_id=request.session_id,
        conversation_history=conversation_history,
    )

    # Calculate total duration
    total_duration_ms = sum(r.duration_ms or 0 for r in step_results)

    return ExecuteWorkflowResponse(
        execution_id=execution_id,
        workflow_id=workflow_id,
        status=exec_status,
        final_output=final_output,
        step_results=step_results,
        total_duration_ms=total_duration_ms,
        error=error,
    )


# ==================== Workflow Validation ====================


@router.post("/{workflow_id}/validate", response_model=ValidateWorkflowResponse)
async def validate_stored_workflow(
    workflow_id: str,
    current_user: CurrentUser,
    agent_repo: BaseAgentRepository = Depends(get_repository),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> ValidateWorkflowResponse:
    """Validate a stored workflow definition."""
    from src.workflows.executor import validate_workflow_with_resources

    # Get workflow
    workflow = await workflow_repo.get(workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Validate
    is_valid, errors, warnings, missing_agents = await validate_workflow_with_resources(
        workflow.definition, agent_repo
    )

    return ValidateWorkflowResponse(
        is_valid=is_valid,
        errors=[ValidationError(field=e["field"], message=e["message"]) for e in errors],
        warnings=[ValidationError(field=w["field"], message=w["message"], severity="warning") for w in warnings],
        missing_agents=missing_agents,
        missing_mcps=[],
    )


@router.post("/validate", response_model=ValidateWorkflowResponse)
async def validate_workflow_definition(
    request: ValidateWorkflowRequest,
    current_user: CurrentUser,
    agent_repo: BaseAgentRepository = Depends(get_repository),
) -> ValidateWorkflowResponse:
    """Validate a workflow definition before saving."""
    from src.workflows.executor import validate_workflow_with_resources

    # Convert to dict for validation
    definition_dict = request.definition.model_dump(exclude_none=True)

    # Validate
    is_valid, errors, warnings, missing_agents = await validate_workflow_with_resources(
        definition_dict, agent_repo
    )

    return ValidateWorkflowResponse(
        is_valid=is_valid,
        errors=[ValidationError(field=e["field"], message=e["message"]) for e in errors],
        warnings=[ValidationError(field=w["field"], message=w["message"], severity="warning") for w in warnings],
        missing_agents=missing_agents,
        missing_mcps=[],
    )


# ==================== Execution History ====================


@router.get("/{workflow_id}/executions", response_model=WorkflowExecutionListResponse)
async def list_executions(
    workflow_id: str,
    current_user: CurrentUser,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowExecutionListResponse:
    """List executions for a workflow."""
    # Verify workflow exists
    if not await workflow_repo.exists(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    executions = await workflow_repo.list_executions(workflow_id, limit, offset)

    return WorkflowExecutionListResponse(
        executions=[
            WorkflowExecutionResponse(
                id=e.id,
                workflow_id=e.workflow_id,
                temporal_workflow_id=e.temporal_workflow_id,
                status=e.status,
                started_at=e.started_at,
                completed_at=e.completed_at,
                duration_ms=e.duration_ms,
                input_data=e.input_data,
                output_data=e.output_data,
                error=e.error,
                steps_executed=e.steps_executed,
                step_results=e.step_results,
                triggered_by=e.triggered_by,
            )
            for e in executions
        ],
        total=len(executions),
    )


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: CurrentUser,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowExecutionResponse:
    """Get execution details by ID."""
    execution = await workflow_repo.get_execution(execution_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found",
        )

    return WorkflowExecutionResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        temporal_workflow_id=execution.temporal_workflow_id,
        status=execution.status,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        duration_ms=execution.duration_ms,
        input_data=execution.input_data,
        output_data=execution.output_data,
        error=execution.error,
        steps_executed=execution.steps_executed,
        step_results=execution.step_results,
        triggered_by=execution.triggered_by,
    )


# ==================== Resource Discovery ====================


@router.get("/resources/agents", response_model=AvailableAgentsResponse)
async def list_available_agents(
    current_user: CurrentUser,
    agent_repo: BaseAgentRepository = Depends(get_repository),
) -> AvailableAgentsResponse:
    """List agents available for use in workflows."""
    agents = await agent_repo.list()

    return AvailableAgentsResponse(
        agents=[
            AvailableAgentResponse(
                id=a.id,
                name=a.name,
                description=a.description,
                agent_type=a.agent_type.value,
            )
            for a in agents
        ],
        total=len(agents),
    )


@router.get("/resources/mcps", response_model=AvailableMCPsResponse)
async def list_available_mcps(
    current_user: CurrentUser,
    mcp_repo: MCPServerRepository = Depends(get_mcp_repository),
) -> AvailableMCPsResponse:
    """List MCP servers and their tools available for workflows."""
    servers = await mcp_repo.list_all()
    mcp_manager = get_mcp_manager()

    mcp_servers = []
    for server in servers:
        # Get tools from MCP manager if available
        tools = []
        try:
            server_tools = await mcp_manager.get_tools(server.id)
            tools = [
                MCPToolResponse(
                    id=f"{server.id}:{t.name}",
                    name=t.name,
                    description=t.description or "",
                )
                for t in server_tools
            ]
        except Exception:
            # If we can't get tools, continue with empty list
            pass

        mcp_servers.append(
            AvailableMCPServerResponse(
                id=server.id,
                name=server.name,
                template=server.template,
                status=server.status,
                tools=tools,
            )
        )

    return AvailableMCPsResponse(
        mcp_servers=mcp_servers,
        total=len(mcp_servers),
    )


@router.get("/resources/tools", response_model=AvailableToolsResponse)
async def list_available_tools(
    current_user: CurrentUser,
    mcp_repo: MCPServerRepository = Depends(get_mcp_repository),
) -> AvailableToolsResponse:
    """List all tools (native and MCP) available for workflows."""
    from src.tools import get_registry

    tools = []

    # Get native tools from registry
    try:
        registry = get_registry()
        for tool_name, tool_def in registry.tools.items():
            tools.append(
                AvailableToolResponse(
                    id=tool_name,
                    name=tool_def.name,
                    description=tool_def.description or "",
                    source="native",
                )
            )
    except Exception:
        pass

    # Get MCP tools
    try:
        servers = await mcp_repo.list_all()
        mcp_manager = get_mcp_manager()

        for server in servers:
            try:
                server_tools = await mcp_manager.get_tools(server.id)
                for t in server_tools:
                    tools.append(
                        AvailableToolResponse(
                            id=f"{server.id}:{t.name}",
                            name=t.name,
                            description=t.description or "",
                            source=f"mcp:{server.id}",
                        )
                    )
            except Exception:
                continue
    except Exception:
        pass

    return AvailableToolsResponse(
        tools=tools,
        total=len(tools),
    )


# ==================== AI Generation ====================


@router.post("/generate/skeleton", response_model=GenerateSkeletonResponse)
async def generate_workflow_skeleton(
    request: GenerateSkeletonRequest,
    current_user: CurrentUser,
    agent_repo: BaseAgentRepository = Depends(get_repository),
    mcp_repo: MCPServerRepository = Depends(get_mcp_repository),
) -> GenerateSkeletonResponse:
    """Generate a workflow skeleton from natural language (Phase 1 of two-phase creation).

    This generates just the workflow structure with step roles, without creating agents.
    The user can then edit the structure and configure each step in Phase 2.
    """
    from src.workflows.generator import WorkflowGenerator

    generator = WorkflowGenerator()

    # Get existing resources so AI can suggest reusing them
    existing_agents = await agent_repo.list()
    existing_mcps = await mcp_repo.list_all()

    return await generator.generate_skeleton(
        request=request,
        user_id=current_user.id,
        existing_agents=existing_agents,
        existing_mcps=existing_mcps,
    )


@router.post("/generate", response_model=GenerateWorkflowResponse)
async def generate_workflow(
    request: GenerateWorkflowRequest,
    current_user: CurrentUser,
    agent_repo: BaseAgentRepository = Depends(get_repository),
    mcp_repo: MCPServerRepository = Depends(get_mcp_repository),
) -> GenerateWorkflowResponse:
    """Generate a workflow from natural language prompt using AI."""
    # Import here to avoid circular imports
    from src.workflows.generator import WorkflowGenerator

    generator = WorkflowGenerator()

    # Get existing resources to pass to AI
    existing_agents = await agent_repo.list()
    existing_mcps = await mcp_repo.list_all()

    return await generator.generate(
        prompt=request.prompt,
        user_id=current_user.id,
        context=request.context,
        preferred_complexity=request.preferred_complexity,
        include_agents=request.include_agents,
        include_mcps=request.include_mcps,
        existing_agents=existing_agents,
        existing_mcps=existing_mcps,
    )


@router.post("/generate/apply", response_model=ApplyGeneratedWorkflowResponse)
async def apply_generated_workflow(
    request: ApplyGeneratedWorkflowRequest,
    current_user: CurrentUser,
    agent_repo: BaseAgentRepository = Depends(get_repository),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
) -> ApplyGeneratedWorkflowResponse:
    """Apply a generated workflow by creating agents and workflow."""
    from src.workflows.generator import WorkflowGenerator

    generator = WorkflowGenerator()

    return await generator.apply(
        request=request,
        agent_repo=agent_repo,
        workflow_repo=workflow_repo,
    )


# ==================== Workflow Schedules ====================


@router.post("/schedule/validate", response_model=ValidateCronResponse)
async def validate_cron_expression(
    request: ValidateCronRequest,
    current_user: CurrentUser,
) -> ValidateCronResponse:
    """Validate a cron expression and preview next run times."""
    from src.utils import validate_cron, describe_cron, get_next_runs

    is_valid, error = validate_cron(request.cron_expression)

    if not is_valid:
        return ValidateCronResponse(
            is_valid=False,
            error=error,
        )

    try:
        description = describe_cron(request.cron_expression)
        next_runs = get_next_runs(
            request.cron_expression,
            count=5,
            timezone=request.timezone,
        )
        return ValidateCronResponse(
            is_valid=True,
            description=description,
            next_runs=next_runs,
        )
    except Exception as e:
        return ValidateCronResponse(
            is_valid=False,
            error=str(e),
        )


@router.post("/schedule/preview", response_model=ValidateCronResponse)
async def preview_schedule(
    request: SchedulePreviewRequest,
    current_user: CurrentUser,
) -> ValidateCronResponse:
    """Preview the next run times for a cron expression."""
    from src.utils import validate_cron, describe_cron, get_next_runs

    is_valid, error = validate_cron(request.cron_expression)

    if not is_valid:
        return ValidateCronResponse(
            is_valid=False,
            error=error,
        )

    try:
        description = describe_cron(request.cron_expression)
        next_runs = get_next_runs(
            request.cron_expression,
            count=request.count,
            timezone=request.timezone,
        )
        return ValidateCronResponse(
            is_valid=True,
            description=description,
            next_runs=next_runs,
        )
    except Exception as e:
        return ValidateCronResponse(
            is_valid=False,
            error=str(e),
        )


@router.post("/{workflow_id}/schedule", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    workflow_id: str,
    request: CreateScheduleRequest,
    current_user: CurrentUser,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
    schedule_repo: ScheduleRepository = Depends(get_schedule_repository),
) -> ScheduleResponse:
    """Create a schedule for a workflow."""
    from src.workflows.schedule_service import ScheduleService

    # Verify workflow exists
    if not await workflow_repo.exists(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Check if schedule already exists for this workflow
    existing = await schedule_repo.get_by_workflow(workflow_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Schedule already exists for workflow '{workflow_id}'. Use PUT to update.",
        )

    try:
        # Create schedule in database
        schedule = await schedule_repo.create(
            workflow_id=workflow_id,
            cron_expression=request.cron_expression,
            user_id=current_user.id,
            timezone_str=request.timezone,
            enabled=request.enabled,
            input_text=request.input,
            context=request.context,
        )

        # Create Temporal schedule (if Temporal is available)
        try:
            schedule_service = ScheduleService()
            temporal_schedule_id = await schedule_service.create_schedule(
                schedule_id=schedule.id,
                workflow_id=workflow_id,
                cron_expression=request.cron_expression,
                timezone=request.timezone,
                input_text=request.input,
                context=request.context,
                user_id=current_user.id,
                enabled=request.enabled,
            )
            # Store the Temporal schedule ID
            await schedule_repo.set_temporal_schedule_id(schedule.id, temporal_schedule_id)
            # Refresh schedule data
            schedule = await schedule_repo.get(schedule.id)
        except Exception as temporal_error:
            # Log but don't fail - schedule is stored in DB and can be synced later
            import logging
            logging.warning(f"Failed to create Temporal schedule: {temporal_error}")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ScheduleResponse(
        id=schedule.id,
        workflow_id=schedule.workflow_id,
        cron_expression=schedule.cron_expression,
        cron_description=schedule.cron_description,
        timezone=schedule.timezone,
        enabled=schedule.enabled,
        input=schedule.input_text,
        context=schedule.context,
        next_run_at=schedule.next_run_at,
        last_run_at=schedule.last_run_at,
        run_count=schedule.run_count,
        last_error=schedule.last_error,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.get("/{workflow_id}/schedule", response_model=ScheduleResponse)
async def get_schedule(
    workflow_id: str,
    current_user: CurrentUser,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
    schedule_repo: ScheduleRepository = Depends(get_schedule_repository),
) -> ScheduleResponse:
    """Get the schedule for a workflow."""
    # Verify workflow exists
    if not await workflow_repo.exists(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    schedule = await schedule_repo.get_by_workflow(workflow_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No schedule found for workflow '{workflow_id}'",
        )

    return ScheduleResponse(
        id=schedule.id,
        workflow_id=schedule.workflow_id,
        cron_expression=schedule.cron_expression,
        cron_description=schedule.cron_description,
        timezone=schedule.timezone,
        enabled=schedule.enabled,
        input=schedule.input_text,
        context=schedule.context,
        next_run_at=schedule.next_run_at,
        last_run_at=schedule.last_run_at,
        run_count=schedule.run_count,
        last_error=schedule.last_error,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.put("/{workflow_id}/schedule", response_model=ScheduleResponse)
async def update_schedule(
    workflow_id: str,
    request: UpdateScheduleRequest,
    current_user: CurrentUser,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
    schedule_repo: ScheduleRepository = Depends(get_schedule_repository),
) -> ScheduleResponse:
    """Update the schedule for a workflow."""
    from src.workflows.schedule_service import ScheduleService

    # Verify workflow exists
    if not await workflow_repo.exists(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Get existing schedule
    existing = await schedule_repo.get_by_workflow(workflow_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No schedule found for workflow '{workflow_id}'",
        )

    try:
        # Update schedule in database
        schedule = await schedule_repo.update(
            schedule_id=existing.id,
            cron_expression=request.cron_expression,
            timezone_str=request.timezone,
            enabled=request.enabled,
            input_text=request.input,
            context=request.context,
        )

        # Update Temporal schedule (if it exists)
        if existing.temporal_schedule_id:
            try:
                schedule_service = ScheduleService()
                await schedule_service.update_schedule(
                    temporal_schedule_id=existing.temporal_schedule_id,
                    cron_expression=request.cron_expression,
                    timezone=request.timezone,
                    input_text=request.input,
                    context=request.context,
                    enabled=request.enabled,
                )
            except Exception as temporal_error:
                import logging
                logging.warning(f"Failed to update Temporal schedule: {temporal_error}")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule not found",
        )

    return ScheduleResponse(
        id=schedule.id,
        workflow_id=schedule.workflow_id,
        cron_expression=schedule.cron_expression,
        cron_description=schedule.cron_description,
        timezone=schedule.timezone,
        enabled=schedule.enabled,
        input=schedule.input_text,
        context=schedule.context,
        next_run_at=schedule.next_run_at,
        last_run_at=schedule.last_run_at,
        run_count=schedule.run_count,
        last_error=schedule.last_error,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.delete("/{workflow_id}/schedule", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    workflow_id: str,
    current_user: CurrentUser,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
    schedule_repo: ScheduleRepository = Depends(get_schedule_repository),
) -> None:
    """Delete the schedule for a workflow."""
    from src.workflows.schedule_service import ScheduleService

    # Verify workflow exists
    if not await workflow_repo.exists(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Get schedule to check for Temporal schedule ID
    existing = await schedule_repo.get_by_workflow(workflow_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No schedule found for workflow '{workflow_id}'",
        )

    # Delete Temporal schedule if it exists
    if existing.temporal_schedule_id:
        try:
            schedule_service = ScheduleService()
            await schedule_service.delete_schedule(existing.temporal_schedule_id)
        except Exception as temporal_error:
            import logging
            logging.warning(f"Failed to delete Temporal schedule: {temporal_error}")

    # Delete from database
    await schedule_repo.delete_by_workflow(workflow_id)


@router.get("/schedules", response_model=ScheduleListResponse)
async def list_schedules(
    current_user: CurrentUser,
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    schedule_repo: ScheduleRepository = Depends(get_schedule_repository),
) -> ScheduleListResponse:
    """List all schedules for the current user."""
    from src.storage.schedule_repository import ScheduleFilters

    filters = ScheduleFilters(
        user_id=current_user.id,
        enabled=enabled,
    )

    schedules = await schedule_repo.list(filters, limit, offset)

    return ScheduleListResponse(
        schedules=[
            ScheduleResponse(
                id=s.id,
                workflow_id=s.workflow_id,
                cron_expression=s.cron_expression,
                cron_description=s.cron_description,
                timezone=s.timezone,
                enabled=s.enabled,
                input=s.input_text,
                context=s.context,
                next_run_at=s.next_run_at,
                last_run_at=s.last_run_at,
                run_count=s.run_count,
                last_error=s.last_error,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in schedules
        ],
        total=len(schedules),
    )
