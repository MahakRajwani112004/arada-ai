/**
 * Approval Types for Workflow Human-in-the-Loop Gates
 */

export type ApprovalStatus = "pending" | "approved" | "rejected" | "expired";
export type ApprovalDecision = "approve" | "reject";

export interface ApprovalReceivedItem {
  user_id: string;
  user_email?: string;
  decision: ApprovalDecision;
  comment?: string;
  responded_at: string;
}

export interface ApprovalSummary {
  id: string;
  workflow_id: string;
  workflow_name?: string;
  execution_id: string;
  step_id: string;
  title: string;
  message: string;
  status: ApprovalStatus;
  approvers: string[];
  required_approvals: number;
  approvals_received_count: number;
  timeout_at?: string;
  created_at: string;
  responded_at?: string;
}

export interface ApprovalDetail {
  id: string;
  workflow_id: string;
  workflow_name?: string;
  execution_id: string;
  step_id: string;
  temporal_workflow_id: string;
  title: string;
  message: string;
  context: Record<string, unknown>;
  approvers: string[];
  required_approvals: number;
  status: ApprovalStatus;
  approvals_received: ApprovalReceivedItem[];
  rejection_reason?: string;
  timeout_at?: string;
  created_at: string;
  responded_at?: string;
  created_by: string;
  responded_by?: string;
}

export interface ApprovalListResponse {
  approvals: ApprovalSummary[];
  total: number;
  pending_count: number;
}

export interface ApprovalStatsResponse {
  pending_count: number;
  approved_count: number;
  rejected_count: number;
  expired_count: number;
  avg_response_time_hours?: number;
}

export interface ApprovalRespondRequest {
  decision: ApprovalDecision;
  comment?: string;
}

export interface ApprovalRespondResponse {
  id: string;
  status: ApprovalStatus;
  message: string;
  workflow_resumed: boolean;
}

export interface ApprovalFilters {
  status?: ApprovalStatus;
  workflow_id?: string;
  limit?: number;
  offset?: number;
}
