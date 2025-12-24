import { apiClient } from "./client";
import {
  WorkflowDefinition,
  WorkflowDefinitionResponse,
  WorkflowListResponse,
  WorkflowValidationResponse,
  CreateWorkflowRequest,
} from "@/types/workflow";

/**
 * List all workflow definitions.
 */
export async function listWorkflows(): Promise<WorkflowListResponse> {
  const response = await apiClient.get<WorkflowListResponse>("/workflow-definitions");
  return response.data;
}

/**
 * Get a workflow definition by ID.
 */
export async function getWorkflow(id: string): Promise<WorkflowDefinitionResponse> {
  const response = await apiClient.get<WorkflowDefinitionResponse>(`/workflow-definitions/${id}`);
  return response.data;
}

/**
 * Create a new workflow definition.
 */
export async function createWorkflow(
  data: CreateWorkflowRequest
): Promise<WorkflowDefinitionResponse> {
  const response = await apiClient.post<WorkflowDefinitionResponse>("/workflow-definitions", data);
  return response.data;
}

/**
 * Update an existing workflow definition.
 */
export async function updateWorkflow(
  id: string,
  data: Partial<WorkflowDefinition>
): Promise<WorkflowDefinitionResponse> {
  const response = await apiClient.put<WorkflowDefinitionResponse>(
    `/workflow-definitions/${id}`,
    data
  );
  return response.data;
}

/**
 * Delete a workflow definition.
 */
export async function deleteWorkflow(id: string): Promise<void> {
  await apiClient.delete(`/workflow-definitions/${id}`);
}

/**
 * Validate a workflow definition.
 */
export async function validateWorkflow(id: string): Promise<WorkflowValidationResponse> {
  const response = await apiClient.post<WorkflowValidationResponse>(
    `/workflow-definitions/${id}/validate`
  );
  return response.data;
}
