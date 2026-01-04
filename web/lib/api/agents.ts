import { apiClient } from "./client";
import type {
  Agent,
  AgentCreate,
  AgentDetail,
  AgentExecutionsResponse,
  AgentListResponse,
  AgentStats,
  AgentUsageHistory,
  ExecutionDetail,
  GenerateAgentRequest,
  GenerateAgentResponse,
  TimeRange,
  WorkflowRequest,
  WorkflowResponse,
  WorkflowStatusResponse,
} from "@/types/agent";

export async function listAgents(): Promise<AgentListResponse> {
  const response = await apiClient.get<AgentListResponse>("/agents");
  return response.data;
}

export async function getAgent(agentId: string): Promise<AgentDetail> {
  const response = await apiClient.get<AgentDetail>(`/agents/${agentId}`);
  return response.data;
}

export async function createAgent(agent: AgentCreate): Promise<Agent> {
  const response = await apiClient.post<Agent>("/agents", agent);
  return response.data;
}

export async function updateAgent(agentId: string, agent: AgentCreate): Promise<Agent> {
  const response = await apiClient.put<Agent>(`/agents/${agentId}`, agent);
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

// ============================================================================
// Agent Overview Tab API Functions
// ============================================================================

export async function getAgentStats(
  agentId: string,
  timeRange: TimeRange = "7d"
): Promise<AgentStats> {
  const response = await apiClient.get<AgentStats>(
    `/agents/${agentId}/stats`,
    { params: { time_range: timeRange } }
  );
  return response.data;
}

export async function getAgentExecutions(
  agentId: string,
  options?: {
    limit?: number;
    offset?: number;
    status?: "completed" | "failed" | null;
  }
): Promise<AgentExecutionsResponse> {
  const response = await apiClient.get<AgentExecutionsResponse>(
    `/agents/${agentId}/executions`,
    {
      params: {
        limit: options?.limit ?? 20,
        offset: options?.offset ?? 0,
        status_filter: options?.status,
      },
    }
  );
  return response.data;
}

export async function getAgentUsageHistory(
  agentId: string,
  timeRange: TimeRange = "7d",
  granularity: "hour" | "day" = "day"
): Promise<AgentUsageHistory> {
  const response = await apiClient.get<AgentUsageHistory>(
    `/agents/${agentId}/usage-history`,
    { params: { time_range: timeRange, granularity } }
  );
  return response.data;
}

export async function getExecutionDetail(
  executionId: string
): Promise<ExecutionDetail> {
  const response = await apiClient.get<ExecutionDetail>(
    `/agents/executions/${executionId}`
  );
  return response.data;
}
