"""Schedule Repository - stores and retrieves workflow schedules for cron-based execution."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models import WorkflowScheduleModel, WorkflowModel
from src.utils import get_next_run, validate_cron, describe_cron


@dataclass
class ScheduleData:
    """Data for a workflow schedule."""
    id: str
    workflow_id: str
    user_id: str
    cron_expression: str
    cron_description: str
    timezone: str
    enabled: bool
    input_text: Optional[str]
    context: Dict[str, Any]
    temporal_schedule_id: Optional[str]
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    run_count: int
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ScheduleFilters:
    """Filters for listing schedules."""
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None
    enabled: Optional[bool] = None


class ScheduleRepository:
    """PostgreSQL-backed schedule repository."""

    def __init__(self, session: AsyncSession, user_id: str | None = None):
        """Initialize with database session and optional user_id for filtering."""
        self.session = session
        self.user_id = user_id

    async def create(
        self,
        workflow_id: str,
        cron_expression: str,
        user_id: Optional[str] = None,
        timezone_str: str = "UTC",
        enabled: bool = True,
        input_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ScheduleData:
        """Create a new schedule for a workflow."""
        # Validate cron expression
        is_valid, error = validate_cron(cron_expression)
        if not is_valid:
            raise ValueError(f"Invalid cron expression: {error}")

        schedule_id = str(uuid4())
        now = datetime.now(timezone.utc)
        owner_id = user_id or self.user_id

        if not owner_id:
            raise ValueError("user_id is required to create a schedule")

        # Calculate next run time
        next_run = get_next_run(cron_expression, timezone=timezone_str)

        model = WorkflowScheduleModel(
            id=schedule_id,
            workflow_id=workflow_id,
            user_id=owner_id,
            cron_expression=cron_expression,
            timezone=timezone_str,
            enabled=enabled,
            input_text=input_text,
            context_json=context or {},
            next_run_at=next_run,
            run_count=0,
            created_at=now,
            updated_at=now,
        )
        self.session.add(model)
        await self.session.flush()

        return self._model_to_data(model)

    async def get(self, schedule_id: str) -> Optional[ScheduleData]:
        """Get schedule by ID."""
        stmt = select(WorkflowScheduleModel).where(
            WorkflowScheduleModel.id == schedule_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_data(model)

    async def get_by_workflow(self, workflow_id: str) -> Optional[ScheduleData]:
        """Get schedule for a specific workflow (one schedule per workflow)."""
        stmt = select(WorkflowScheduleModel).where(
            WorkflowScheduleModel.workflow_id == workflow_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_data(model)

    async def list(
        self,
        filters: Optional[ScheduleFilters] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ScheduleData]:
        """List schedules with optional filters."""
        stmt = select(WorkflowScheduleModel)

        if filters:
            conditions = []
            if filters.workflow_id:
                conditions.append(WorkflowScheduleModel.workflow_id == filters.workflow_id)
            if filters.user_id:
                conditions.append(WorkflowScheduleModel.user_id == filters.user_id)
            if filters.enabled is not None:
                conditions.append(WorkflowScheduleModel.enabled == filters.enabled)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(WorkflowScheduleModel.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_data(m) for m in models]

    async def list_due(self, limit: int = 100) -> List[ScheduleData]:
        """List enabled schedules that are due for execution."""
        now = datetime.now(timezone.utc)
        stmt = select(WorkflowScheduleModel).where(
            and_(
                WorkflowScheduleModel.enabled == True,
                WorkflowScheduleModel.next_run_at <= now,
            )
        ).order_by(WorkflowScheduleModel.next_run_at.asc()).limit(limit)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_data(m) for m in models]

    async def update(
        self,
        schedule_id: str,
        cron_expression: Optional[str] = None,
        timezone_str: Optional[str] = None,
        enabled: Optional[bool] = None,
        input_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[ScheduleData]:
        """Update a schedule."""
        # First get the existing schedule
        existing = await self.get(schedule_id)
        if not existing:
            return None

        # Build update dict
        updates = {"updated_at": datetime.now(timezone.utc)}

        if cron_expression is not None:
            is_valid, error = validate_cron(cron_expression)
            if not is_valid:
                raise ValueError(f"Invalid cron expression: {error}")
            updates["cron_expression"] = cron_expression

        if timezone_str is not None:
            updates["timezone"] = timezone_str

        if enabled is not None:
            updates["enabled"] = enabled

        if input_text is not None:
            updates["input_text"] = input_text

        if context is not None:
            updates["context_json"] = context

        # Recalculate next_run_at if cron or timezone changed
        new_cron = cron_expression or existing.cron_expression
        new_tz = timezone_str or existing.timezone
        if cron_expression is not None or timezone_str is not None:
            updates["next_run_at"] = get_next_run(new_cron, timezone=new_tz)

        # Perform update
        stmt = (
            update(WorkflowScheduleModel)
            .where(WorkflowScheduleModel.id == schedule_id)
            .values(**updates)
        )
        await self.session.execute(stmt)
        await self.session.flush()

        return await self.get(schedule_id)

    async def delete(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        stmt = select(WorkflowScheduleModel).where(
            WorkflowScheduleModel.id == schedule_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        await self.session.flush()
        return True

    async def delete_by_workflow(self, workflow_id: str) -> bool:
        """Delete schedule for a workflow."""
        stmt = select(WorkflowScheduleModel).where(
            WorkflowScheduleModel.workflow_id == workflow_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        await self.session.flush()
        return True

    async def record_run(
        self,
        schedule_id: str,
        success: bool = True,
        error: Optional[str] = None,
    ) -> Optional[ScheduleData]:
        """Record that a scheduled run occurred."""
        existing = await self.get(schedule_id)
        if not existing:
            return None

        now = datetime.now(timezone.utc)
        next_run = get_next_run(
            existing.cron_expression,
            after=now,
            timezone=existing.timezone
        )

        updates = {
            "last_run_at": now,
            "next_run_at": next_run,
            "run_count": existing.run_count + 1,
            "updated_at": now,
        }

        if not success and error:
            updates["last_error"] = error
        elif success:
            updates["last_error"] = None

        stmt = (
            update(WorkflowScheduleModel)
            .where(WorkflowScheduleModel.id == schedule_id)
            .values(**updates)
        )
        await self.session.execute(stmt)
        await self.session.flush()

        return await self.get(schedule_id)

    async def set_temporal_schedule_id(
        self,
        schedule_id: str,
        temporal_schedule_id: str,
    ) -> Optional[ScheduleData]:
        """Set the Temporal schedule ID after creating a Temporal schedule."""
        stmt = (
            update(WorkflowScheduleModel)
            .where(WorkflowScheduleModel.id == schedule_id)
            .values(
                temporal_schedule_id=temporal_schedule_id,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

        return await self.get(schedule_id)

    def _model_to_data(self, model: WorkflowScheduleModel) -> ScheduleData:
        """Convert SQLAlchemy model to dataclass."""
        return ScheduleData(
            id=model.id,
            workflow_id=model.workflow_id,
            user_id=model.user_id,
            cron_expression=model.cron_expression,
            cron_description=describe_cron(model.cron_expression),
            timezone=model.timezone,
            enabled=model.enabled,
            input_text=model.input_text,
            context=model.context_json or {},
            temporal_schedule_id=model.temporal_schedule_id,
            next_run_at=model.next_run_at,
            last_run_at=model.last_run_at,
            run_count=model.run_count,
            last_error=model.last_error,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
