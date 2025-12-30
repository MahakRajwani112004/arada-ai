"""Approval API routes for workflow human-in-the-loop approval gates."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies import get_approval_repository
from src.auth.dependencies import CurrentUser
from src.api.schemas.approvals import (
    ApprovalDecision,
    ApprovalDetailResponse,
    ApprovalListResponse,
    ApprovalReceivedItem,
    ApprovalRespondResponse,
    ApprovalStatsResponse,
    ApprovalStatus,
    ApprovalSummaryResponse,
    RespondToApprovalRequest,
)
from src.storage.approval_repository import ApprovalFilters, ApprovalRepository

router = APIRouter(prefix="/approvals", tags=["approvals"])


# ==================== Approval Inbox ====================


@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    current_user: CurrentUser,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    approval_repo: ApprovalRepository = Depends(get_approval_repository),
) -> ApprovalListResponse:
    """List approval requests for the current user.

    By default, shows pending approvals where the user is an approver.
    """
    # Build filters
    filters = ApprovalFilters(
        status=status_filter,
        workflow_id=workflow_id,
        approver_user_id=current_user.id,
    )

    approvals = await approval_repo.list(filters, limit=limit, offset=offset)
    pending_count = await approval_repo.count_pending(current_user.id)

    return ApprovalListResponse(
        approvals=[
            ApprovalSummaryResponse(
                id=a.id,
                workflow_id=a.workflow_id,
                workflow_name=a.workflow_name,
                execution_id=a.execution_id,
                step_id=a.step_id,
                title=a.title,
                message=a.message,
                status=ApprovalStatus(a.status),
                approvers=a.approvers,
                required_approvals=a.required_approvals,
                approvals_received_count=len(a.approvals_received),
                timeout_at=a.timeout_at,
                created_at=a.created_at,
                responded_at=a.responded_at,
            )
            for a in approvals
        ],
        total=len(approvals),
        pending_count=pending_count,
    )


@router.get("/pending", response_model=ApprovalListResponse)
async def list_pending_approvals(
    current_user: CurrentUser,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    approval_repo: ApprovalRepository = Depends(get_approval_repository),
) -> ApprovalListResponse:
    """List pending approval requests for the current user."""
    approvals = await approval_repo.list_pending_for_user(
        current_user.id, limit=limit, offset=offset
    )
    pending_count = await approval_repo.count_pending(current_user.id)

    return ApprovalListResponse(
        approvals=[
            ApprovalSummaryResponse(
                id=a.id,
                workflow_id=a.workflow_id,
                workflow_name=a.workflow_name,
                execution_id=a.execution_id,
                step_id=a.step_id,
                title=a.title,
                message=a.message,
                status=ApprovalStatus(a.status),
                approvers=a.approvers,
                required_approvals=a.required_approvals,
                approvals_received_count=len(a.approvals_received),
                timeout_at=a.timeout_at,
                created_at=a.created_at,
                responded_at=a.responded_at,
            )
            for a in approvals
        ],
        total=len(approvals),
        pending_count=pending_count,
    )


@router.get("/stats", response_model=ApprovalStatsResponse)
async def get_approval_stats(
    current_user: CurrentUser,
    approval_repo: ApprovalRepository = Depends(get_approval_repository),
) -> ApprovalStatsResponse:
    """Get approval statistics for the current user."""
    stats = await approval_repo.get_stats(current_user.id)

    return ApprovalStatsResponse(
        pending_count=stats.pending_count,
        approved_count=stats.approved_count,
        rejected_count=stats.rejected_count,
        expired_count=stats.expired_count,
        avg_response_time_hours=stats.avg_response_time_hours,
    )


# ==================== Individual Approval ====================


@router.get("/{approval_id}", response_model=ApprovalDetailResponse)
async def get_approval(
    approval_id: str,
    current_user: CurrentUser,
    approval_repo: ApprovalRepository = Depends(get_approval_repository),
) -> ApprovalDetailResponse:
    """Get approval details by ID."""
    approval = await approval_repo.get(approval_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval '{approval_id}' not found",
        )

    # Check if user is authorized to view (must be an approver or creator)
    if current_user.id not in approval.approvers and current_user.id != approval.created_by:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this approval",
        )

    return ApprovalDetailResponse(
        id=approval.id,
        workflow_id=approval.workflow_id,
        workflow_name=approval.workflow_name,
        execution_id=approval.execution_id,
        step_id=approval.step_id,
        temporal_workflow_id=approval.temporal_workflow_id,
        title=approval.title,
        message=approval.message,
        context=approval.context,
        approvers=approval.approvers,
        required_approvals=approval.required_approvals,
        status=ApprovalStatus(approval.status),
        approvals_received=[
            ApprovalReceivedItem(
                user_id=r["user_id"],
                user_email=r.get("user_email"),
                decision=ApprovalDecision(r["decision"]),
                comment=r.get("comment"),
                responded_at=r["responded_at"],
            )
            for r in approval.approvals_received
        ],
        rejection_reason=approval.rejection_reason,
        timeout_at=approval.timeout_at,
        created_at=approval.created_at,
        responded_at=approval.responded_at,
        created_by=approval.created_by,
        responded_by=approval.responded_by,
    )


@router.post("/{approval_id}/respond", response_model=ApprovalRespondResponse)
async def respond_to_approval(
    approval_id: str,
    request: RespondToApprovalRequest,
    current_user: CurrentUser,
    approval_repo: ApprovalRepository = Depends(get_approval_repository),
) -> ApprovalRespondResponse:
    """Respond to an approval request (approve or reject)."""
    approval = await approval_repo.get(approval_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval '{approval_id}' not found",
        )

    # Check if user is authorized to respond (must be an approver)
    if current_user.id not in approval.approvers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to respond to this approval",
        )

    # Check if approval is still pending
    if approval.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval is no longer pending (status: {approval.status})",
        )

    # Check if user has already responded
    for received in approval.approvals_received:
        if received.get("user_id") == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already responded to this approval",
            )

    # Record the response
    updated = await approval_repo.respond(
        approval_id=approval_id,
        user_id=current_user.id,
        decision=request.decision.value,
        comment=request.comment,
        user_email=current_user.email if hasattr(current_user, "email") else None,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record response",
        )

    # If status changed to approved/rejected, signal Temporal workflow
    workflow_resumed = False
    if updated.status in ("approved", "rejected"):
        try:
            await _signal_workflow_approval(
                temporal_workflow_id=updated.temporal_workflow_id,
                approval_id=approval_id,
                decision=updated.status,
                user_id=current_user.id,
                comment=request.comment,
            )
            workflow_resumed = True
        except Exception as e:
            # Log error but don't fail the response
            import logging
            logging.error(f"Failed to signal Temporal workflow: {e}")

    # Build response message
    if request.decision == ApprovalDecision.APPROVE:
        if updated.status == "approved":
            message = "Approval granted. Workflow will continue."
        else:
            remaining = updated.required_approvals - len([
                r for r in updated.approvals_received
                if r.get("decision") == "approve"
            ])
            message = f"Vote recorded. {remaining} more approval(s) needed."
    else:
        message = "Request rejected. Workflow will handle rejection."

    return ApprovalRespondResponse(
        id=updated.id,
        status=ApprovalStatus(updated.status),
        message=message,
        workflow_resumed=workflow_resumed,
    )


async def _signal_workflow_approval(
    temporal_workflow_id: str,
    approval_id: str,
    decision: str,
    user_id: str,
    comment: Optional[str] = None,
) -> None:
    """Signal the Temporal workflow with the approval decision.

    This sends a signal to the waiting workflow to resume execution.
    """
    try:
        from temporalio.client import Client
        from src.config.settings import get_settings

        settings = get_settings()
        client = await Client.connect(settings.temporal_host)

        # Get the workflow handle
        handle = client.get_workflow_handle(temporal_workflow_id)

        # Send the approval signal
        await handle.signal(
            "approval_response",
            {
                "approval_id": approval_id,
                "decision": decision,
                "user_id": user_id,
                "comment": comment,
            },
        )
    except ImportError:
        # Temporal not installed, skip signaling
        pass
    except Exception:
        # Re-raise to be caught by caller
        raise
