import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listWorkflows,
  getWorkflow,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
  validateWorkflow,
} from "@/lib/api/workflows";
import {
  WorkflowDefinition,
  CreateWorkflowRequest,
} from "@/types/workflow";

// Query keys
export const workflowKeys = {
  all: ["workflows"] as const,
  list: () => [...workflowKeys.all, "list"] as const,
  detail: (id: string) => [...workflowKeys.all, "detail", id] as const,
};

/**
 * Hook to fetch all workflows.
 */
export function useWorkflows() {
  return useQuery({
    queryKey: workflowKeys.list(),
    queryFn: listWorkflows,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch a single workflow.
 */
export function useWorkflow(id: string | undefined) {
  return useQuery({
    queryKey: workflowKeys.detail(id || ""),
    queryFn: () => getWorkflow(id!),
    enabled: !!id,
    staleTime: 60 * 1000,
  });
}

/**
 * Hook to create a workflow.
 */
export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateWorkflowRequest) => createWorkflow(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.list() });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create workflow");
    },
  });
}

/**
 * Hook to update a workflow.
 */
export function useUpdateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<WorkflowDefinition> }) =>
      updateWorkflow(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.list() });
      queryClient.invalidateQueries({ queryKey: workflowKeys.detail(id) });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update workflow");
    },
  });
}

/**
 * Hook to delete a workflow.
 */
export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteWorkflow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.list() });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to delete workflow");
    },
  });
}

/**
 * Hook to validate a workflow.
 */
export function useValidateWorkflow() {
  return useMutation({
    mutationFn: (id: string) => validateWorkflow(id),
    onError: (error: Error) => {
      toast.error(error.message || "Failed to validate workflow");
    },
  });
}
