"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listWorkflows,
  getWorkflow,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
  copyWorkflow,
  executeWorkflowById,
  getWorkflowExecutions,
  getExecution,
  validateWorkflow,
  getAvailableAgents,
  getAvailableMCPs,
  getAvailableTools,
  generateWorkflow,
  generateWorkflowSkeleton,
  saveGeneratedWorkflow,
  checkWorkflowReadiness,
} from "@/lib/api/workflows";
import type {
  CreateWorkflowRequest,
  UpdateWorkflowRequest,
  CopyWorkflowRequest,
  ExecuteWorkflowRequest,
  WorkflowFilters,
  GenerateSkeletonRequest,
} from "@/types/workflow";
import type {
  GenerateWorkflowRequest,
  SaveGeneratedWorkflowRequest,
} from "@/types/agent-suggestion";

// ==================== Query Keys ====================

export const workflowKeys = {
  all: ["workflows"] as const,
  lists: () => [...workflowKeys.all, "list"] as const,
  list: (filters?: WorkflowFilters) =>
    [...workflowKeys.lists(), filters] as const,
  details: () => [...workflowKeys.all, "detail"] as const,
  detail: (id: string) => [...workflowKeys.details(), id] as const,
  executions: (workflowId: string) =>
    [...workflowKeys.detail(workflowId), "executions"] as const,
  execution: (executionId: string) =>
    [...workflowKeys.all, "execution", executionId] as const,
  validation: (id: string) => [...workflowKeys.detail(id), "validation"] as const,
  readiness: (id: string) => [...workflowKeys.detail(id), "readiness"] as const,
};

export const resourceKeys = {
  agents: ["resources", "agents"] as const,
  mcps: ["resources", "mcps"] as const,
  tools: ["resources", "tools"] as const,
};

// ==================== Workflow CRUD Hooks ====================

export function useWorkflows(filters?: WorkflowFilters) {
  return useQuery({
    queryKey: workflowKeys.list(filters),
    queryFn: () => listWorkflows(filters),
  });
}

export function useWorkflow(workflowId: string) {
  return useQuery({
    queryKey: workflowKeys.detail(workflowId),
    queryFn: () => getWorkflow(workflowId),
    enabled: !!workflowId,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateWorkflowRequest) => createWorkflow(request),
    onSuccess: (workflow) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      toast.success(`Workflow "${workflow.name}" created`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workflowId,
      request,
    }: {
      workflowId: string;
      request: UpdateWorkflowRequest;
    }) => updateWorkflow(workflowId, request),
    onSuccess: (workflow) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: workflowKeys.detail(workflow.id),
      });
      toast.success("Workflow updated");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workflowId: string) => deleteWorkflow(workflowId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      toast.success("Workflow deleted");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useCopyWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workflowId,
      request,
    }: {
      workflowId: string;
      request: CopyWorkflowRequest;
    }) => copyWorkflow(workflowId, request),
    onSuccess: (workflow) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      toast.success(`Workflow copied as "${workflow.name}"`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ==================== Execution Hooks ====================

export function useExecuteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workflowId,
      request,
    }: {
      workflowId: string;
      request: ExecuteWorkflowRequest;
    }) => executeWorkflowById(workflowId, request),
    onSuccess: (response, { workflowId }) => {
      // Invalidate executions list after new execution
      queryClient.invalidateQueries({
        queryKey: workflowKeys.executions(workflowId),
      });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useWorkflowExecutions(workflowId: string) {
  return useQuery({
    queryKey: workflowKeys.executions(workflowId),
    queryFn: () => getWorkflowExecutions(workflowId),
    enabled: !!workflowId,
  });
}

export function useExecution(executionId: string, options?: { poll?: boolean }) {
  return useQuery({
    queryKey: workflowKeys.execution(executionId),
    queryFn: () => getExecution(executionId),
    enabled: !!executionId,
    refetchInterval: options?.poll ? 1000 : false, // Poll every second if enabled
  });
}

// Alias for useExecution with clearer naming
export const useWorkflowExecution = useExecution;

// ==================== Validation Hooks ====================

export function useValidateWorkflow(workflowId: string) {
  return useQuery({
    queryKey: workflowKeys.validation(workflowId),
    queryFn: () => validateWorkflow(workflowId),
    enabled: !!workflowId,
  });
}

export function useWorkflowReadiness(workflowId: string) {
  return useQuery({
    queryKey: workflowKeys.readiness(workflowId),
    queryFn: () => checkWorkflowReadiness(workflowId),
    enabled: !!workflowId,
  });
}

// ==================== Resource Discovery Hooks ====================

export function useAvailableAgents() {
  return useQuery({
    queryKey: resourceKeys.agents,
    queryFn: getAvailableAgents,
  });
}

export function useAvailableMCPs() {
  return useQuery({
    queryKey: resourceKeys.mcps,
    queryFn: getAvailableMCPs,
  });
}

export function useAvailableTools() {
  return useQuery({
    queryKey: resourceKeys.tools,
    queryFn: getAvailableTools,
  });
}

// ==================== AI Generation Hooks ====================

export function useGenerateWorkflowSkeleton() {
  return useMutation({
    mutationFn: (request: GenerateSkeletonRequest) => generateWorkflowSkeleton(request),
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useGenerateWorkflow() {
  return useMutation({
    mutationFn: (request: GenerateWorkflowRequest) => generateWorkflow(request),
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useSaveGeneratedWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SaveGeneratedWorkflowRequest) =>
      saveGeneratedWorkflow(request),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      if (response.can_execute) {
        toast.success("Workflow created and ready to run!");
      } else {
        toast.success("Workflow saved. Create missing agents to enable execution.");
      }
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
