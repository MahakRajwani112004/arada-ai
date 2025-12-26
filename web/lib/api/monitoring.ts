/**
 * Monitoring API client - Logs and Analytics
 */
import { apiClient } from "./client";
import type {
  LogsResponse,
  LogFilters,
  LogServicesResponse,
  LLMUsageStats,
  AgentStats,
  TimeSeriesResponse,
  TimeSeriesFilters,
  AnalyticsFilters,
  WorkflowStats,
  DashboardSummary,
  TopWorkflowsResponse,
  TopAgentsResponse,
  TopModelsResponse,
  ErrorStats,
  KnowledgeBaseStats,
  CostBreakdown,
  CostTrendResponse,
} from "@/types/monitoring";

// ============================================
// Logs API
// ============================================

/**
 * Get logs from all containers
 */
export async function getLogs(filters?: LogFilters): Promise<LogsResponse> {
  const params = new URLSearchParams();

  if (filters?.service) params.append("service", filters.service);
  if (filters?.level) params.append("level", filters.level);
  if (filters?.search) params.append("search", filters.search);
  if (filters?.limit) params.append("limit", filters.limit.toString());
  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);

  const response = await apiClient.get<LogsResponse>(
    `/monitoring/logs?${params.toString()}`
  );
  return response.data;
}

/**
 * Get available log services for filtering
 */
export async function getLogServices(): Promise<LogServicesResponse> {
  const response = await apiClient.get<LogServicesResponse>(
    "/monitoring/logs/services"
  );
  return response.data;
}

// ============================================
// LLM Analytics API
// ============================================

/**
 * Get LLM usage analytics
 */
export async function getLLMAnalytics(
  filters?: AnalyticsFilters
): Promise<LLMUsageStats> {
  const params = new URLSearchParams();

  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);

  const response = await apiClient.get<LLMUsageStats>(
    `/monitoring/analytics/llm?${params.toString()}`
  );
  return response.data;
}

/**
 * Get LLM usage time series for charts
 */
export async function getLLMTimeSeries(
  filters?: TimeSeriesFilters
): Promise<TimeSeriesResponse> {
  const params = new URLSearchParams();

  if (filters?.metric) params.append("metric", filters.metric);
  if (filters?.interval) params.append("interval", filters.interval);
  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);

  const response = await apiClient.get<TimeSeriesResponse>(
    `/monitoring/analytics/llm/timeseries?${params.toString()}`
  );
  return response.data;
}

// ============================================
// Agent Analytics API
// ============================================

/**
 * Get agent execution analytics
 */
export async function getAgentAnalytics(
  filters?: AnalyticsFilters
): Promise<AgentStats> {
  const params = new URLSearchParams();

  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);

  const response = await apiClient.get<AgentStats>(
    `/monitoring/analytics/agents?${params.toString()}`
  );
  return response.data;
}

// ============================================
// Workflow Analytics API
// ============================================

/**
 * Get workflow execution analytics
 */
export async function getWorkflowAnalytics(
  filters?: AnalyticsFilters
): Promise<WorkflowStats> {
  const params = new URLSearchParams();

  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);

  const response = await apiClient.get<WorkflowStats>(
    `/monitoring/analytics/workflows?${params.toString()}`
  );
  return response.data;
}

/**
 * Get workflow time series data for charts
 */
export async function getWorkflowTimeSeries(
  filters?: TimeSeriesFilters & { metric?: "executions" | "duration" | "success_rate" }
): Promise<TimeSeriesResponse> {
  const params = new URLSearchParams();

  if (filters?.metric) params.append("metric", filters.metric);
  if (filters?.interval) params.append("interval", filters.interval);
  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);

  const response = await apiClient.get<TimeSeriesResponse>(
    `/monitoring/analytics/workflows/timeseries?${params.toString()}`
  );
  return response.data;
}

// ============================================
// Dashboard Summary API
// ============================================

/**
 * Get comprehensive dashboard summary
 */
export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await apiClient.get<DashboardSummary>(
    "/monitoring/analytics/dashboard"
  );
  return response.data;
}

// ============================================
// Top Entities API
// ============================================

/**
 * Get top workflows by execution count
 */
export async function getTopWorkflows(
  filters?: AnalyticsFilters & { limit?: number }
): Promise<TopWorkflowsResponse> {
  const params = new URLSearchParams();

  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);
  if (filters?.limit) params.append("limit", filters.limit.toString());

  const response = await apiClient.get<TopWorkflowsResponse>(
    `/monitoring/analytics/top/workflows?${params.toString()}`
  );
  return response.data;
}

/**
 * Get top agents by execution count
 */
export async function getTopAgents(
  filters?: AnalyticsFilters & { limit?: number }
): Promise<TopAgentsResponse> {
  const params = new URLSearchParams();

  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);
  if (filters?.limit) params.append("limit", filters.limit.toString());

  const response = await apiClient.get<TopAgentsResponse>(
    `/monitoring/analytics/top/agents?${params.toString()}`
  );
  return response.data;
}

/**
 * Get top LLM models by usage
 */
export async function getTopModels(
  filters?: AnalyticsFilters & { limit?: number }
): Promise<TopModelsResponse> {
  const params = new URLSearchParams();

  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);
  if (filters?.limit) params.append("limit", filters.limit.toString());

  const response = await apiClient.get<TopModelsResponse>(
    `/monitoring/analytics/top/models?${params.toString()}`
  );
  return response.data;
}

// ============================================
// Error Analytics API
// ============================================

/**
 * Get error analytics
 */
export async function getErrorAnalytics(
  filters?: AnalyticsFilters
): Promise<ErrorStats> {
  const params = new URLSearchParams();

  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);

  const response = await apiClient.get<ErrorStats>(
    `/monitoring/analytics/errors?${params.toString()}`
  );
  return response.data;
}

// ============================================
// Knowledge Base Analytics API
// ============================================

/**
 * Get knowledge base analytics
 */
export async function getKnowledgeAnalytics(): Promise<KnowledgeBaseStats> {
  const response = await apiClient.get<KnowledgeBaseStats>(
    "/monitoring/analytics/knowledge"
  );
  return response.data;
}

// ============================================
// Cost Analytics API
// ============================================

/**
 * Get cost breakdown by provider, model, and agent
 */
export async function getCostBreakdown(
  filters?: AnalyticsFilters
): Promise<CostBreakdown> {
  const params = new URLSearchParams();

  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);

  const response = await apiClient.get<CostBreakdown>(
    `/monitoring/analytics/cost/breakdown?${params.toString()}`
  );
  return response.data;
}

/**
 * Get cost trend over time
 */
export async function getCostTrend(
  filters?: { interval?: "1h" | "1d" | "1w"; start?: string; end?: string }
): Promise<CostTrendResponse> {
  const params = new URLSearchParams();

  if (filters?.interval) params.append("interval", filters.interval);
  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);

  const response = await apiClient.get<CostTrendResponse>(
    `/monitoring/analytics/cost/trend?${params.toString()}`
  );
  return response.data;
}

/**
 * Get agent time series data for charts
 */
export async function getAgentTimeSeries(
  filters?: TimeSeriesFilters & { metric?: "executions" | "latency" | "success_rate" }
): Promise<TimeSeriesResponse> {
  const params = new URLSearchParams();

  if (filters?.metric) params.append("metric", filters.metric);
  if (filters?.interval) params.append("interval", filters.interval);
  if (filters?.start) params.append("start", filters.start);
  if (filters?.end) params.append("end", filters.end);

  const response = await apiClient.get<TimeSeriesResponse>(
    `/monitoring/analytics/agents/timeseries?${params.toString()}`
  );
  return response.data;
}
