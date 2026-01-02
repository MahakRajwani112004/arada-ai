"""API schemas for workflow approval management."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalDecision(str, Enum):
    """Decision for responding to an approval request."""
    APPROVE = "approve"
    REJECT = "reject"


class ApprovalReceivedItem(BaseModel):
    """Record of an individual approval response."""
    user_id: str
    user_email: Optional[str] = None
    decision: ApprovalDecision
    comment: Optional[str] = None
    responded_at: datetime


# ==================== Request Schemas ====================


class RespondToApprovalRequest(BaseModel):
    """Request to respond to an approval request."""
    decision: ApprovalDecision = Field(..., description="Approve or reject")
    comment: Optional[str] = Field(None, max_length=2000, description="Optional comment explaining decision")


# ==================== Response Schemas ====================


class ApprovalSummaryResponse(BaseModel):
    """Summary of an approval request for list views."""
    id: str
    workflow_id: str
    workflow_name: Optional[str] = None
    execution_id: str
    step_id: str
    title: str
    message: str
    status: ApprovalStatus
    approvers: List[str]
    required_approvals: int
    approvals_received_count: int
    timeout_at: Optional[datetime] = None
    created_at: datetime
    responded_at: Optional[datetime] = None


class ApprovalDetailResponse(BaseModel):
    """Detailed approval request with full context."""
    id: str
    workflow_id: str
    workflow_name: Optional[str] = None
    execution_id: str
    step_id: str
    temporal_workflow_id: str
    title: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    approvers: List[str]
    required_approvals: int
    status: ApprovalStatus
    approvals_received: List[ApprovalReceivedItem] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    timeout_at: Optional[datetime] = None
    created_at: datetime
    responded_at: Optional[datetime] = None
    created_by: str
    responded_by: Optional[str] = None


class ApprovalListResponse(BaseModel):
    """List of approval requests with pagination."""
    approvals: List[ApprovalSummaryResponse]
    total: int
    pending_count: int


class ApprovalRespondResponse(BaseModel):
    """Response after submitting an approval decision."""
    id: str
    status: ApprovalStatus
    message: str
    workflow_resumed: bool = False


class ApprovalStatsResponse(BaseModel):
    """Statistics about user's approval activity."""
    pending_count: int
    approved_count: int
    rejected_count: int
    expired_count: int
    avg_response_time_hours: Optional[float] = None
