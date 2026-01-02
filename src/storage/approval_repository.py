"""Approval Repository - stores and retrieves workflow approval requests."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models import WorkflowApprovalModel, WorkflowModel


@dataclass
class ApprovalData:
    """Data for a workflow approval request."""
    id: str
    workflow_id: str
    workflow_name: Optional[str]
    execution_id: str
    step_id: str
    temporal_workflow_id: str
    title: str
    message: str
    context: Dict[str, Any]
    approvers: List[str]
    required_approvals: int
    status: str
    approvals_received: List[Dict[str, Any]]
    rejection_reason: Optional[str]
    timeout_at: Optional[datetime]
    created_at: datetime
    responded_at: Optional[datetime]
    created_by: str
    responded_by: Optional[str]


@dataclass
class ApprovalFilters:
    """Filters for listing approvals."""
    status: Optional[str] = None
    workflow_id: Optional[str] = None
    approver_user_id: Optional[str] = None


@dataclass
class ApprovalStats:
    """Statistics for approval activity."""
    pending_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    expired_count: int = 0
    avg_response_time_hours: Optional[float] = None


class ApprovalRepository:
    """PostgreSQL-backed approval repository."""

    def __init__(self, session: AsyncSession, user_id: str | None = None):
        """Initialize with database session and optional user_id for filtering."""
        self.session = session
        self.user_id = user_id

    async def create(
        self,
        workflow_id: str,
        execution_id: str,
        step_id: str,
        temporal_workflow_id: str,
        title: str,
        message: str,
        approvers: List[str],
        required_approvals: int = 1,
        context: Optional[Dict[str, Any]] = None,
        timeout_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
    ) -> ApprovalData:
        """Create a new approval request."""
        approval_id = str(uuid4())
        now = datetime.now(timezone.utc)

        model = WorkflowApprovalModel(
            id=approval_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            step_id=step_id,
            temporal_workflow_id=temporal_workflow_id,
            title=title,
            message=message,
            context=context or {},
            approvers=approvers,
            required_approvals=required_approvals,
            status="pending",
            approvals_received=[],
            timeout_at=timeout_at,
            created_at=now,
            created_by=created_by or self.user_id or "system",
        )
        self.session.add(model)
        await self.session.flush()

        return await self._model_to_data(model)

    async def get(self, approval_id: str) -> Optional[ApprovalData]:
        """Get approval by ID."""
        stmt = select(WorkflowApprovalModel).where(WorkflowApprovalModel.id == approval_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return await self._model_to_data(model)

    async def get_by_execution(self, execution_id: str, step_id: str) -> Optional[ApprovalData]:
        """Get approval by execution ID and step ID."""
        stmt = select(WorkflowApprovalModel).where(
            and_(
                WorkflowApprovalModel.execution_id == execution_id,
                WorkflowApprovalModel.step_id == step_id,
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return await self._model_to_data(model)

    async def list(
        self,
        filters: Optional[ApprovalFilters] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ApprovalData]:
        """List approvals with optional filters."""
        stmt = select(WorkflowApprovalModel)

        if filters:
            if filters.status:
                stmt = stmt.where(WorkflowApprovalModel.status == filters.status)
            if filters.workflow_id:
                stmt = stmt.where(WorkflowApprovalModel.workflow_id == filters.workflow_id)
            if filters.approver_user_id:
                # Check if user is in approvers list (using PostgreSQL ARRAY contains)
                stmt = stmt.where(WorkflowApprovalModel.approvers.contains([filters.approver_user_id]))

        stmt = stmt.order_by(WorkflowApprovalModel.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        approvals = []
        for model in models:
            approvals.append(await self._model_to_data(model))
        return approvals

    async def list_pending_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[ApprovalData]:
        """List pending approvals where user is an approver."""
        stmt = select(WorkflowApprovalModel).where(
            and_(
                WorkflowApprovalModel.status == "pending",
                WorkflowApprovalModel.approvers.contains([user_id]),
            )
        )
        stmt = stmt.order_by(WorkflowApprovalModel.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        approvals = []
        for model in models:
            approvals.append(await self._model_to_data(model))
        return approvals

    async def respond(
        self,
        approval_id: str,
        user_id: str,
        decision: str,
        comment: Optional[str] = None,
        user_email: Optional[str] = None,
    ) -> Optional[ApprovalData]:
        """Record a response to an approval request."""
        stmt = select(WorkflowApprovalModel).where(WorkflowApprovalModel.id == approval_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        if model.status != "pending":
            return await self._model_to_data(model)

        # Record the approval/rejection
        now = datetime.now(timezone.utc)
        approval_record = {
            "user_id": user_id,
            "user_email": user_email,
            "decision": decision,
            "comment": comment,
            "responded_at": now.isoformat(),
        }

        # Update approvals_received
        approvals_received = list(model.approvals_received) if model.approvals_received else []
        approvals_received.append(approval_record)
        model.approvals_received = approvals_received

        # Determine if approval is complete
        if decision == "reject":
            model.status = "rejected"
            model.rejection_reason = comment
            model.responded_at = now
            model.responded_by = user_id
        elif len([a for a in approvals_received if a["decision"] == "approve"]) >= model.required_approvals:
            model.status = "approved"
            model.responded_at = now
            model.responded_by = user_id

        await self.session.flush()
        return await self._model_to_data(model)

    async def mark_expired(self, approval_id: str) -> Optional[ApprovalData]:
        """Mark an approval as expired."""
        stmt = select(WorkflowApprovalModel).where(WorkflowApprovalModel.id == approval_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        if model.status == "pending":
            model.status = "expired"
            model.responded_at = datetime.now(timezone.utc)
            await self.session.flush()

        return await self._model_to_data(model)

    async def get_stats(self, user_id: Optional[str] = None) -> ApprovalStats:
        """Get approval statistics."""
        base_stmt = select(func.count(WorkflowApprovalModel.id))

        if user_id:
            base_stmt = base_stmt.where(WorkflowApprovalModel.approvers.contains([user_id]))

        # Pending count
        pending_stmt = base_stmt.where(WorkflowApprovalModel.status == "pending")
        pending_result = await self.session.execute(pending_stmt)
        pending_count = pending_result.scalar() or 0

        # Approved count
        approved_stmt = base_stmt.where(WorkflowApprovalModel.status == "approved")
        approved_result = await self.session.execute(approved_stmt)
        approved_count = approved_result.scalar() or 0

        # Rejected count
        rejected_stmt = base_stmt.where(WorkflowApprovalModel.status == "rejected")
        rejected_result = await self.session.execute(rejected_stmt)
        rejected_count = rejected_result.scalar() or 0

        # Expired count
        expired_stmt = base_stmt.where(WorkflowApprovalModel.status == "expired")
        expired_result = await self.session.execute(expired_stmt)
        expired_count = expired_result.scalar() or 0

        return ApprovalStats(
            pending_count=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
            expired_count=expired_count,
        )

    async def count_pending(self, user_id: Optional[str] = None) -> int:
        """Count pending approvals for a user."""
        stmt = select(func.count(WorkflowApprovalModel.id)).where(
            WorkflowApprovalModel.status == "pending"
        )
        if user_id:
            stmt = stmt.where(WorkflowApprovalModel.approvers.contains([user_id]))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def _model_to_data(self, model: WorkflowApprovalModel) -> ApprovalData:
        """Convert database model to data class."""
        # Get workflow name if available
        workflow_name = None
        if model.workflow_id:
            workflow_stmt = select(WorkflowModel.name).where(WorkflowModel.id == model.workflow_id)
            result = await self.session.execute(workflow_stmt)
            workflow_name = result.scalar_one_or_none()

        return ApprovalData(
            id=model.id,
            workflow_id=model.workflow_id,
            workflow_name=workflow_name,
            execution_id=model.execution_id,
            step_id=model.step_id,
            temporal_workflow_id=model.temporal_workflow_id,
            title=model.title,
            message=model.message,
            context=model.context or {},
            approvers=list(model.approvers) if model.approvers else [],
            required_approvals=model.required_approvals,
            status=model.status,
            approvals_received=model.approvals_received or [],
            rejection_reason=model.rejection_reason,
            timeout_at=model.timeout_at,
            created_at=model.created_at,
            responded_at=model.responded_at,
            created_by=model.created_by,
            responded_by=model.responded_by,
        )
