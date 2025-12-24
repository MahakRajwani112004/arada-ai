import { apiClient } from "./client";
import type {
  Workflow,
  WorkflowListResponse,
  CreateWorkflowRequest,
  UpdateWorkflowRequest,
  CopyWorkflowRequest,
  ExecuteWorkflowRequest,
  ExecuteWorkflowResponse,
  WorkflowExecution,
  WorkflowExecutionListResponse,
  AvailableAgentsResponse,
  AvailableMCPsResponse,
  AvailableToolsResponse,
  ValidateWorkflowRequest,
  ValidateWorkflowResponse,
  WorkflowFilters,
} from "@/types/workflow";
import type {
  GenerateWorkflowRequest,
  GenerateWorkflowResponse,
  SaveGeneratedWorkflowRequest,
  SaveGeneratedWorkflowResponse,
} from "@/types/agent-suggestion";

// ==================== Workflow CRUD ====================

export async function listWorkflows(
  filters?: WorkflowFilters
): Promise<WorkflowListResponse> {
  const params = new URLSearchParams();
  if (filters?.category) params.append("category", filters.category);
  if (filters?.is_template !== undefined)
    params.append("is_template", String(filters.is_template));
  if (filters?.search) params.append("search", filters.search);
  if (filters?.tags?.length)
    filters.tags.forEach((tag) => params.append("tags", tag));

  const url = params.toString() ? `/workflows?${params}` : "/workflows";
  const response = await apiClient.get<WorkflowListResponse>(url);
  return response.data;
}

export async function getWorkflow(workflowId: string): Promise<Workflow> {
  const response = await apiClient.get<Workflow>(`/workflows/${workflowId}`);
  return response.data;
}

export async function createWorkflow(
  request: CreateWorkflowRequest
): Promise<Workflow> {
  const response = await apiClient.post<Workflow>("/workflows", request);
  return response.data;
}

export async function updateWorkflow(
  workflowId: string,
  request: UpdateWorkflowRequest
): Promise<Workflow> {
  const response = await apiClient.put<Workflow>(
    `/workflows/${workflowId}`,
    request
  );
  return response.data;
}

export async function deleteWorkflow(workflowId: string): Promise<void> {
  await apiClient.delete(`/workflows/${workflowId}`);
}

export async function copyWorkflow(
  workflowId: string,
  request: CopyWorkflowRequest
): Promise<Workflow> {
  const response = await apiClient.post<Workflow>(
    `/workflows/${workflowId}/copy`,
    request
  );
  return response.data;
}

// ==================== Workflow Execution ====================

export async function executeWorkflowById(
  workflowId: string,
  request: ExecuteWorkflowRequest
): Promise<ExecuteWorkflowResponse> {
  const response = await apiClient.post<ExecuteWorkflowResponse>(
    `/workflows/${workflowId}/execute`,
    request
  );
  return response.data;
}

export async function getWorkflowExecutions(
  workflowId: string
): Promise<WorkflowExecutionListResponse> {
  const response = await apiClient.get<WorkflowExecutionListResponse>(
    `/workflows/${workflowId}/executions`
  );
  return response.data;
}

export async function getExecution(
  executionId: string
): Promise<WorkflowExecution> {
  const response = await apiClient.get<WorkflowExecution>(
    `/workflows/executions/${executionId}`
  );
  return response.data;
}

// ==================== Validation ====================

export async function validateWorkflow(
  workflowId: string,
  request?: ValidateWorkflowRequest
): Promise<ValidateWorkflowResponse> {
  const response = await apiClient.post<ValidateWorkflowResponse>(
    `/workflows/${workflowId}/validate`,
    request || {}
  );
  return response.data;
}

// ==================== Resource Discovery ====================

export async function getAvailableAgents(): Promise<AvailableAgentsResponse> {
  const response = await apiClient.get<AvailableAgentsResponse>(
    "/workflows/resources/agents"
  );
  return response.data;
}

export async function getAvailableMCPs(): Promise<AvailableMCPsResponse> {
  const response = await apiClient.get<AvailableMCPsResponse>(
    "/workflows/resources/mcps"
  );
  return response.data;
}

export async function getAvailableTools(): Promise<AvailableToolsResponse> {
  const response = await apiClient.get<AvailableToolsResponse>(
    "/workflows/resources/tools"
  );
  return response.data;
}

// ==================== AI Generation ====================

export async function generateWorkflow(
  request: GenerateWorkflowRequest
): Promise<GenerateWorkflowResponse> {
  const response = await apiClient.post<GenerateWorkflowResponse>(
    "/workflows/generate",
    request
  );
  return response.data;
}

export async function saveGeneratedWorkflow(
  request: SaveGeneratedWorkflowRequest
): Promise<SaveGeneratedWorkflowResponse> {
  const response = await apiClient.post<SaveGeneratedWorkflowResponse>(
    "/workflows/generate/apply",
    request
  );
  return response.data;
}

// ==================== Helper Functions ====================

/**
 * Check if a workflow can be executed (no missing agents)
 */
export async function checkWorkflowReadiness(
  workflowId: string
): Promise<{ can_execute: boolean; missing_agents: string[] }> {
  const validation = await validateWorkflow(workflowId);
  return {
    can_execute: validation.is_valid && validation.missing_agents.length === 0,
    missing_agents: validation.missing_agents,
  };
}
