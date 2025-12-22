import { apiClient } from "./client";
import type {
  Agent,
  AgentCreate,
  AgentListResponse,
  GenerateAgentRequest,
  GenerateAgentResponse,
  WorkflowRequest,
  WorkflowResponse,
  WorkflowStatusResponse,
} from "@/types/agent";

export async function listAgents(): Promise<AgentListResponse> {
  const response = await apiClient.get<AgentListResponse>("/agents");
  return response.data;
}

export async function getAgent(agentId: string): Promise<Agent> {
  const response = await apiClient.get<Agent>(`/agents/${agentId}`);
  return response.data;
}

export async function createAgent(agent: AgentCreate): Promise<Agent> {
  const response = await apiClient.post<Agent>("/agents", agent);
  return response.data;
}

export async function deleteAgent(agentId: string): Promise<void> {
  await apiClient.delete(`/agents/${agentId}`);
}

export async function generateAgentConfig(request: GenerateAgentRequest): Promise<GenerateAgentResponse> {
  const response = await apiClient.post<GenerateAgentResponse>("/agents/generate", request);
  return response.data;
}

export async function executeWorkflow(request: WorkflowRequest): Promise<WorkflowResponse> {
  const response = await apiClient.post<WorkflowResponse>("/workflow/execute", request);
  return response.data;
}

export async function getWorkflowStatus(workflowId: string): Promise<WorkflowStatusResponse> {
  const response = await apiClient.get<WorkflowStatusResponse>(`/workflow/status/${workflowId}`);
  return response.data;
}
