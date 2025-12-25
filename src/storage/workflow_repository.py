"""Workflow Repository - stores and retrieves workflow definitions and execution history."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models import WorkflowExecutionModel, WorkflowModel


@dataclass
class WorkflowMetadata:
    """Metadata for workflow storage."""

    name: str
    description: str = ""
    category: str = "general"
    tags: List[str] = None
    is_template: bool = False
    source_template_id: Optional[str] = None
    created_by: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class WorkflowSummary:
    """Summary of a workflow for listing."""

    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    version: int
    is_template: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class WorkflowWithMetadata:
    """Full workflow with definition and metadata."""

    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    definition: Dict[str, Any]
    version: int
    is_template: bool
    is_active: bool
    source_template_id: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class WorkflowExecution:
    """Workflow execution record."""

    id: str
    workflow_id: str
    temporal_workflow_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error: Optional[str]
    steps_executed: List[str]
    step_results: Dict[str, Any]
    triggered_by: Optional[str]


@dataclass
class WorkflowFilters:
    """Filters for listing workflows."""

    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_template: Optional[bool] = None
    is_active: bool = True


class WorkflowRepository:
    """PostgreSQL-backed workflow repository."""

    def __init__(self, session: AsyncSession, user_id: str | None = None):
        """Initialize with database session and optional user_id for filtering."""
        self.session = session
        self.user_id = user_id

    # ==================== Workflow CRUD ====================

    async def save(
        self,
        workflow_id: str,
        definition: Dict[str, Any],
        metadata: WorkflowMetadata,
    ) -> WorkflowWithMetadata:
        """Save workflow definition. Returns the saved workflow."""
        stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
        if self.user_id:
            stmt = stmt.where(WorkflowModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing workflow (re-activate if soft-deleted)
            existing.name = metadata.name
            existing.description = metadata.description
            existing.category = metadata.category
            existing.tags = metadata.tags or []
            existing.definition_json = definition
            existing.version = existing.version + 1
            existing.updated_at = datetime.now(timezone.utc)
            existing.is_active = True  # Re-activate if soft-deleted
            model = existing
        else:
            # Create new workflow
            now = datetime.utcnow()
            model = WorkflowModel(
                id=workflow_id,
                name=metadata.name,
                description=metadata.description,
                category=metadata.category,
                tags=metadata.tags or [],
                is_template=metadata.is_template,
                source_template_id=metadata.source_template_id,
                definition_json=definition,
                version=1,
                is_active=True,
                is_published=False,
                created_by=metadata.created_by,
                created_at=now,
                updated_at=now,
            )
            # Set user_id if available
            if self.user_id:
                model.user_id = self.user_id
            self.session.add(model)

        await self.session.flush()
        # Return the model directly to avoid identity map issues with async SQLAlchemy
        return self._to_workflow_with_metadata(model)

    async def get(self, workflow_id: str) -> Optional[WorkflowWithMetadata]:
        """Get workflow by ID (scoped to user if user_id is set)."""
        stmt = select(WorkflowModel).where(
            WorkflowModel.id == workflow_id,
            WorkflowModel.is_active == True,
        )
        if self.user_id:
            stmt = stmt.where(WorkflowModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_workflow_with_metadata(model)

    async def list(
        self, filters: Optional[WorkflowFilters] = None
    ) -> List[WorkflowSummary]:
        """List workflows with optional filters (scoped to user if user_id is set)."""
        stmt = select(WorkflowModel)

        if filters:
            if filters.is_active is not None:
                stmt = stmt.where(WorkflowModel.is_active == filters.is_active)
            if filters.category:
                stmt = stmt.where(WorkflowModel.category == filters.category)
            if filters.is_template is not None:
                stmt = stmt.where(WorkflowModel.is_template == filters.is_template)
        else:
            # Default: only active workflows
            stmt = stmt.where(WorkflowModel.is_active == True)

        # Filter by user_id if set
        if self.user_id:
            stmt = stmt.where(WorkflowModel.user_id == self.user_id)

        stmt = stmt.order_by(WorkflowModel.updated_at.desc())

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_summary(m) for m in models]

    async def delete(self, workflow_id: str) -> bool:
        """Soft delete workflow (scoped to user if user_id is set). Returns True if deleted."""
        stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
        if self.user_id:
            stmt = stmt.where(WorkflowModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        model.is_active = False
        model.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True

    async def exists(self, workflow_id: str) -> bool:
        """Check if workflow exists and is active (scoped to user if user_id is set)."""
        stmt = select(WorkflowModel).where(
            WorkflowModel.id == workflow_id,
            WorkflowModel.is_active == True,
        )
        if self.user_id:
            stmt = stmt.where(WorkflowModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model is not None

    async def copy(
        self,
        source_id: str,
        new_id: str,
        new_name: str,
        created_by: Optional[str] = None,
    ) -> Optional[str]:
        """Copy workflow to new ID (scoped to user if user_id is set). Returns new ID or None if source not found."""
        stmt = select(WorkflowModel).where(
            WorkflowModel.id == source_id,
            WorkflowModel.is_active == True,
        )
        if self.user_id:
            stmt = stmt.where(WorkflowModel.user_id == self.user_id)
        result = await self.session.execute(stmt)
        source = result.scalar_one_or_none()

        if source is None:
            return None

        new_model = WorkflowModel(
            id=new_id,
            name=new_name,
            description=source.description,
            category=source.category,
            tags=source.tags.copy() if source.tags else [],
            is_template=False,  # Copies are not templates
            source_template_id=source_id if source.is_template else source.source_template_id,
            definition_json=source.definition_json.copy(),
            version=1,
            is_active=True,
            is_published=False,
            created_by=created_by,
        )
        # Set user_id if available
        if self.user_id:
            new_model.user_id = self.user_id
        self.session.add(new_model)
        await self.session.flush()
        return new_id

    # ==================== Execution Tracking ====================

    async def create_execution(
        self,
        workflow_id: str,
        temporal_workflow_id: str,
        input_data: Dict[str, Any],
        triggered_by: Optional[str] = None,
    ) -> str:
        """Create execution record. Returns execution ID."""
        execution_id = f"execution-{uuid4().hex[:12]}"

        model = WorkflowExecutionModel(
            id=execution_id,
            workflow_id=workflow_id,
            temporal_workflow_id=temporal_workflow_id,
            status="RUNNING",
            input_json=input_data,
            steps_executed=[],
            step_results={},
            triggered_by=triggered_by,
        )
        # Set user_id if available
        if self.user_id:
            model.user_id = self.user_id
        self.session.add(model)
        await self.session.flush()
        return execution_id

    async def update_execution(
        self,
        execution_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        steps_executed: Optional[List[str]] = None,
        step_results: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update execution status and results. Returns True if updated."""
        model = await self.session.get(WorkflowExecutionModel, execution_id)
        if model is None:
            return False

        model.status = status
        if output_data is not None:
            model.output_json = output_data
        if error is not None:
            model.error = error
        if steps_executed is not None:
            model.steps_executed = steps_executed
        if step_results is not None:
            model.step_results = step_results

        # Calculate duration if completed
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            model.completed_at = datetime.now(timezone.utc)
            if model.started_at:
                delta = model.completed_at - model.started_at
                model.duration_ms = int(delta.total_seconds() * 1000)

        await self.session.flush()
        return True

    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID."""
        model = await self.session.get(WorkflowExecutionModel, execution_id)
        if model is None:
            return None
        return self._to_execution(model)

    async def list_executions(
        self,
        workflow_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkflowExecution]:
        """List executions for a workflow."""
        stmt = (
            select(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.workflow_id == workflow_id)
            .order_by(WorkflowExecutionModel.started_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_execution(m) for m in models]

    # ==================== Helpers ====================

    def _to_summary(self, model: WorkflowModel) -> WorkflowSummary:
        """Convert model to summary."""
        return WorkflowSummary(
            id=model.id,
            name=model.name,
            description=model.description,
            category=model.category,
            tags=model.tags or [],
            version=model.version,
            is_template=model.is_template,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_workflow_with_metadata(self, model: WorkflowModel) -> WorkflowWithMetadata:
        """Convert model to full workflow."""
        return WorkflowWithMetadata(
            id=model.id,
            name=model.name,
            description=model.description,
            category=model.category,
            tags=model.tags or [],
            definition=model.definition_json,
            version=model.version,
            is_template=model.is_template,
            is_active=model.is_active,
            source_template_id=model.source_template_id,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_execution(self, model: WorkflowExecutionModel) -> WorkflowExecution:
        """Convert model to execution."""
        return WorkflowExecution(
            id=model.id,
            workflow_id=model.workflow_id,
            temporal_workflow_id=model.temporal_workflow_id,
            status=model.status,
            started_at=model.started_at,
            completed_at=model.completed_at,
            duration_ms=model.duration_ms,
            input_data=model.input_json,
            output_data=model.output_json,
            error=model.error,
            steps_executed=model.steps_executed or [],
            step_results=model.step_results or {},
            triggered_by=model.triggered_by,
        )
