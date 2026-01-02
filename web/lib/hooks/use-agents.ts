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
} from "@/lib/api/agents";
import type { AgentCreate, WorkflowRequest } from "@/types/agent";

export const agentKeys = {
  all: ["agents"] as const,
  list: () => [...agentKeys.all, "list"] as const,
  detail: (id: string) => [...agentKeys.all, "detail", id] as const,
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
