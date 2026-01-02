/**
 * Approval API client functions
 */
import { apiClient } from "./client";
import type {
  ApprovalDetail,
  ApprovalFilters,
  ApprovalListResponse,
  ApprovalRespondRequest,
  ApprovalRespondResponse,
  ApprovalStatsResponse,
} from "@/types/approval";

/**
 * List approvals with optional filters
 */
export async function listApprovals(
  filters?: ApprovalFilters
): Promise<ApprovalListResponse> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.workflow_id) params.set("workflow_id", filters.workflow_id);
  if (filters?.limit) params.set("limit", filters.limit.toString());
  if (filters?.offset) params.set("offset", filters.offset.toString());

  const { data } = await apiClient.get<ApprovalListResponse>(
    `/approvals?${params.toString()}`
  );
  return data;
}

/**
 * List pending approvals for current user
 */
export async function listPendingApprovals(
  limit = 50,
  offset = 0
): Promise<ApprovalListResponse> {
  const { data } = await apiClient.get<ApprovalListResponse>(
    `/approvals/pending?limit=${limit}&offset=${offset}`
  );
  return data;
}

/**
 * Get approval details by ID
 */
export async function getApproval(approvalId: string): Promise<ApprovalDetail> {
  const { data } = await apiClient.get<ApprovalDetail>(
    `/approvals/${approvalId}`
  );
  return data;
}

/**
 * Get approval statistics for current user
 */
export async function getApprovalStats(): Promise<ApprovalStatsResponse> {
  const { data } = await apiClient.get<ApprovalStatsResponse>("/approvals/stats");
  return data;
}

/**
 * Respond to an approval request (approve or reject)
 */
export async function respondToApproval(
  approvalId: string,
  request: ApprovalRespondRequest
): Promise<ApprovalRespondResponse> {
  const { data } = await apiClient.post<ApprovalRespondResponse>(
    `/approvals/${approvalId}/respond`,
    request
  );
  return data;
}
