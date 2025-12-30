"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listApprovals,
  listPendingApprovals,
  getApproval,
  getApprovalStats,
  respondToApproval,
} from "@/lib/api/approvals";
import type {
  ApprovalFilters,
  ApprovalRespondRequest,
} from "@/types/approval";

// ==================== Query Keys ====================

export const approvalKeys = {
  all: ["approvals"] as const,
  lists: () => [...approvalKeys.all, "list"] as const,
  list: (filters?: ApprovalFilters) => [...approvalKeys.lists(), filters] as const,
  pending: () => [...approvalKeys.all, "pending"] as const,
  details: () => [...approvalKeys.all, "detail"] as const,
  detail: (id: string) => [...approvalKeys.details(), id] as const,
  stats: () => [...approvalKeys.all, "stats"] as const,
};

// ==================== Query Hooks ====================

export function useApprovals(filters?: ApprovalFilters) {
  return useQuery({
    queryKey: approvalKeys.list(filters),
    queryFn: () => listApprovals(filters),
    // Refetch every 30 seconds for near-real-time updates
    refetchInterval: 30000,
  });
}

export function usePendingApprovals(limit = 50, offset = 0) {
  return useQuery({
    queryKey: approvalKeys.pending(),
    queryFn: () => listPendingApprovals(limit, offset),
    // Refetch every 30 seconds for near-real-time updates
    refetchInterval: 30000,
  });
}

export function useApproval(approvalId: string) {
  return useQuery({
    queryKey: approvalKeys.detail(approvalId),
    queryFn: () => getApproval(approvalId),
    enabled: !!approvalId,
  });
}

export function useApprovalStats() {
  return useQuery({
    queryKey: approvalKeys.stats(),
    queryFn: () => getApprovalStats(),
    // Refetch every minute
    refetchInterval: 60000,
  });
}

// ==================== Mutation Hooks ====================

export function useRespondToApproval() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      approvalId,
      request,
    }: {
      approvalId: string;
      request: ApprovalRespondRequest;
    }) => respondToApproval(approvalId, request),
    onSuccess: (response, { approvalId, request }) => {
      // Invalidate all approval queries
      queryClient.invalidateQueries({ queryKey: approvalKeys.all });

      const action = request.decision === "approve" ? "approved" : "rejected";
      toast.success(`Request ${action}. ${response.message}`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
