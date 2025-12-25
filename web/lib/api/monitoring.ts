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
