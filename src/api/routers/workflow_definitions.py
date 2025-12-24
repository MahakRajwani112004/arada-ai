"""Workflow Definitions API routes - CRUD for workflow definitions."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.workflow_definition import (
    CreateWorkflowDefinitionRequest,
    UpdateWorkflowDefinitionRequest,
    WorkflowDefinitionListResponse,
    WorkflowDefinitionResponse,
    WorkflowValidationResponse,
)
from src.models.workflow_definition import WorkflowDefinition, validate_workflow_definition
from src.storage.database import get_session
from src.storage.workflow_repository import WorkflowRepository

router = APIRouter(prefix="/workflow-definitions", tags=["workflow-definitions"])


async def get_workflow_repository(
    session: AsyncSession = Depends(get_session),
) -> WorkflowRepository:
    """Get workflow repository with database session."""
    return WorkflowRepository(session)


def _request_to_definition(request: CreateWorkflowDefinitionRequest) -> WorkflowDefinition:
    """Convert API request to WorkflowDefinition model."""
    return WorkflowDefinition(
        id=request.id,
        name=request.name,
        description=request.description,
        steps=[step.model_dump() for step in request.steps],
        entry_step=request.entry_step,
        context=request.context or {},
    )


def _dict_to_response(data: Dict[str, Any]) -> WorkflowDefinitionResponse:
    """Convert dictionary to response schema."""
    return WorkflowDefinitionResponse(
        id=data["id"],
        name=data.get("name"),
        description=data.get("description"),
        steps=data.get("steps", []),
        entry_step=data.get("entry_step"),
        context=data.get("context"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


@router.post("", response_model=WorkflowDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_definition(
    request: CreateWorkflowDefinitionRequest,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowDefinitionResponse:
    """Create a new workflow definition."""
    # Check if ID already exists
    if await repository.exists(request.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow with ID '{request.id}' already exists",
        )

    # Validate workflow structure
    try:
        workflow = _request_to_definition(request)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow definition: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow definition: {str(e)}",
        )

    # Save to database
    await repository.save(workflow)

    # Get with timestamps
    result = await repository.get_with_timestamps(request.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve saved workflow",
        )

    return _dict_to_response(result)


@router.get("", response_model=WorkflowDefinitionListResponse)
async def list_workflow_definitions(
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowDefinitionListResponse:
    """List all workflow definitions."""
    workflows = await repository.list()
    return WorkflowDefinitionListResponse(
        workflows=[_dict_to_response(w) for w in workflows],
        total=len(workflows),
    )


@router.get("/{workflow_id}", response_model=WorkflowDefinitionResponse)
async def get_workflow_definition(
    workflow_id: str,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowDefinitionResponse:
    """Get a workflow definition by ID."""
    result = await repository.get_with_timestamps(workflow_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    return _dict_to_response(result)


@router.put("/{workflow_id}", response_model=WorkflowDefinitionResponse)
async def update_workflow_definition(
    workflow_id: str,
    request: UpdateWorkflowDefinitionRequest,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowDefinitionResponse:
    """Update a workflow definition."""
    # Check if exists
    existing = await repository.get(workflow_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    # Build updated workflow
    update_data = request.model_dump(exclude_unset=True)

    workflow_dict = existing.model_dump()
    workflow_dict.update(update_data)

    # Handle steps conversion if provided
    if "steps" in update_data and update_data["steps"] is not None:
        workflow_dict["steps"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in update_data["steps"]]

    # Validate updated workflow
    try:
        workflow = validate_workflow_definition(workflow_dict)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow definition: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow definition: {str(e)}",
        )

    # Save updated workflow
    await repository.save(workflow)

    # Get with timestamps
    result = await repository.get_with_timestamps(workflow_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated workflow",
        )

    return _dict_to_response(result)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_definition(
    workflow_id: str,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> None:
    """Delete a workflow definition."""
    if not await repository.delete(workflow_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )


@router.post("/{workflow_id}/validate", response_model=WorkflowValidationResponse)
async def validate_workflow(
    workflow_id: str,
    repository: WorkflowRepository = Depends(get_workflow_repository),
) -> WorkflowValidationResponse:
    """Validate a workflow definition."""
    result = await repository.get_with_timestamps(workflow_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    errors: list[str] = []

    try:
        # Use the existing validation function
        validate_workflow_definition(result)
    except ValidationError as e:
        errors = [str(err) for err in e.errors()]
    except ValueError as e:
        errors = [str(e)]

    return WorkflowValidationResponse(
        valid=len(errors) == 0,
        errors=errors,
    )
