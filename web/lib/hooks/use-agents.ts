"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listAgents,
  getAgent,
  createAgent,
  updateAgent,
  deleteAgent,
  executeWorkflow,
  getAgentStats,
  getAgentExecutions,
  getAgentUsageHistory,
} from "@/lib/api/agents";
import type { AgentCreate, TimeRange, WorkflowRequest } from "@/types/agent";

export const agentKeys = {
  all: ["agents"] as const,
  list: () => [...agentKeys.all, "list"] as const,
  detail: (id: string) => [...agentKeys.all, "detail", id] as const,
  // Overview tab keys
  stats: (id: string, timeRange: TimeRange) =>
    [...agentKeys.all, "stats", id, timeRange] as const,
  executions: (id: string, options?: { limit?: number; offset?: number; status?: string }) =>
    [...agentKeys.all, "executions", id, options] as const,
  usageHistory: (id: string, timeRange: TimeRange, granularity: string) =>
    [...agentKeys.all, "usage-history", id, timeRange, granularity] as const,
};

export function useAgents() {
  return useQuery({
    queryKey: agentKeys.list(),
    queryFn: listAgents,
  });
}

export function useAgent(agentId: string) {
  return useQuery({
    queryKey: agentKeys.detail(agentId),
    queryFn: () => getAgent(agentId),
    enabled: !!agentId,
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (agent: AgentCreate) => createAgent(agent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentKeys.list() });
      toast.success("Agent created successfully");
    },
    onError: (error: Error) => {
      // Don't show error toast for "already exists" - this is handled gracefully in components
      if (error.message.includes("already exists")) {
        // Invalidate the list so the existing agent shows up
        queryClient.invalidateQueries({ queryKey: agentKeys.list() });
        toast.info("Agent already exists - using existing agent");
        return;
      }
      toast.error(error.message);
    },
  });
}

export function useUpdateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, agent }: { agentId: string; agent: AgentCreate }) =>
      updateAgent(agentId, agent),
    onSuccess: (_, { agentId }) => {
      queryClient.invalidateQueries({ queryKey: agentKeys.list() });
      queryClient.invalidateQueries({ queryKey: agentKeys.detail(agentId) });
      toast.success("Agent updated successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (agentId: string) => deleteAgent(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentKeys.list() });
      toast.success("Agent deleted");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useExecuteWorkflow() {
  return useMutation({
    mutationFn: (request: WorkflowRequest) => executeWorkflow(request),
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ============================================================================
// Agent Overview Tab Hooks
// ============================================================================

export function useAgentStats(agentId: string, timeRange: TimeRange = "7d") {
  return useQuery({
    queryKey: agentKeys.stats(agentId, timeRange),
    queryFn: () => getAgentStats(agentId, timeRange),
    enabled: !!agentId,
    staleTime: 30 * 1000, // Consider fresh for 30 seconds
    refetchInterval: 60 * 1000, // Refresh every minute
  });
}

export function useAgentExecutions(
  agentId: string,
  options?: {
    limit?: number;
    offset?: number;
    status?: "completed" | "failed";
  }
) {
  return useQuery({
    queryKey: agentKeys.executions(agentId, options),
    queryFn: () => getAgentExecutions(agentId, options),
    enabled: !!agentId,
    staleTime: 30 * 1000,
  });
}

export function useAgentUsageHistory(
  agentId: string,
  timeRange: TimeRange = "7d",
  granularity: "hour" | "day" = "day"
) {
  return useQuery({
    queryKey: agentKeys.usageHistory(agentId, timeRange, granularity),
    queryFn: () => getAgentUsageHistory(agentId, timeRange, granularity),
    enabled: !!agentId,
    staleTime: 60 * 1000, // Consider fresh for 1 minute
  });
}
