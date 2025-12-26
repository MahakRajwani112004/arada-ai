/**
 * React Query hooks for monitoring - Logs and Analytics
 */
import { useQuery } from "@tanstack/react-query";
import {
  getLogs,
  getLogServices,
  getLLMAnalytics,
  getLLMTimeSeries,
  getAgentAnalytics,
  getAgentTimeSeries,
  getWorkflowAnalytics,
  getWorkflowTimeSeries,
  getDashboardSummary,
  getTopWorkflows,
  getTopAgents,
  getTopModels,
  getErrorAnalytics,
  getKnowledgeAnalytics,
  getCostBreakdown,
  getCostTrend,
} from "@/lib/api/monitoring";
import { useAuth } from "@/lib/auth";
import type {
  LogFilters,
  AnalyticsFilters,
  TimeSeriesFilters,
} from "@/types/monitoring";

// ============================================
// Query Keys
// ============================================

export const monitoringKeys = {
  all: ["monitoring"] as const,
  logs: () => [...monitoringKeys.all, "logs"] as const,
  logsList: (filters?: LogFilters) =>
    [...monitoringKeys.logs(), filters] as const,
  logServices: () => [...monitoringKeys.logs(), "services"] as const,
  analytics: () => [...monitoringKeys.all, "analytics"] as const,
  llm: (filters?: AnalyticsFilters) =>
    [...monitoringKeys.analytics(), "llm", filters] as const,
  llmTimeSeries: (filters?: TimeSeriesFilters) =>
    [...monitoringKeys.analytics(), "llm", "timeseries", filters] as const,
  agents: (filters?: AnalyticsFilters) =>
    [...monitoringKeys.analytics(), "agents", filters] as const,
  agentsTimeSeries: (filters?: TimeSeriesFilters) =>
    [...monitoringKeys.analytics(), "agents", "timeseries", filters] as const,
  workflows: (filters?: AnalyticsFilters) =>
    [...monitoringKeys.analytics(), "workflows", filters] as const,
  workflowsTimeSeries: (filters?: TimeSeriesFilters) =>
    [...monitoringKeys.analytics(), "workflows", "timeseries", filters] as const,
  dashboard: () => [...monitoringKeys.analytics(), "dashboard"] as const,
  topWorkflows: (filters?: AnalyticsFilters) =>
    [...monitoringKeys.analytics(), "top", "workflows", filters] as const,
  topAgents: (filters?: AnalyticsFilters) =>
    [...monitoringKeys.analytics(), "top", "agents", filters] as const,
  topModels: (filters?: AnalyticsFilters) =>
    [...monitoringKeys.analytics(), "top", "models", filters] as const,
  errors: (filters?: AnalyticsFilters) =>
    [...monitoringKeys.analytics(), "errors", filters] as const,
  knowledge: () => [...monitoringKeys.analytics(), "knowledge"] as const,
  costBreakdown: (filters?: AnalyticsFilters) =>
    [...monitoringKeys.analytics(), "cost", "breakdown", filters] as const,
  costTrend: (filters?: { interval?: string }) =>
    [...monitoringKeys.analytics(), "cost", "trend", filters] as const,
};

// ============================================
// Logs Hooks
// ============================================

/**
 * Fetch logs with optional filters
 */
export function useLogs(filters?: LogFilters) {
  const { hasHydrated, accessToken } = useAuth();
  const isReady = hasHydrated && !!accessToken;

  return useQuery({
    queryKey: monitoringKeys.logsList(filters),
    queryFn: () => getLogs(filters),
    refetchInterval: isReady ? 10000 : false,
    enabled: isReady,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000),
    staleTime: 0,
    refetchOnMount: "always",
  });
}

/**
 * Fetch available log services
 */
export function useLogServices() {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.logServices(),
    queryFn: getLogServices,
    staleTime: 60000, // Cache for 1 minute
    enabled: hasHydrated && !!accessToken,
  });
}

// ============================================
// LLM Analytics Hooks
// ============================================

/**
 * Fetch LLM usage analytics
 */
export function useLLMAnalytics(filters?: AnalyticsFilters) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.llm(filters),
    queryFn: () => getLLMAnalytics(filters),
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: hasHydrated && !!accessToken,
  });
}

/**
 * Fetch LLM time series data for charts
 */
export function useLLMTimeSeries(filters?: TimeSeriesFilters) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.llmTimeSeries(filters),
    queryFn: () => getLLMTimeSeries(filters),
    refetchInterval: 30000,
    enabled: hasHydrated && !!accessToken,
  });
}

// ============================================
// Agent Analytics Hooks
// ============================================

/**
 * Fetch agent execution analytics
 */
export function useAgentAnalytics(filters?: AnalyticsFilters) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.agents(filters),
    queryFn: () => getAgentAnalytics(filters),
    refetchInterval: 30000,
    enabled: hasHydrated && !!accessToken,
  });
}

/**
 * Fetch agent time series data for charts
 */
export function useAgentTimeSeries(filters?: TimeSeriesFilters & { metric?: "executions" | "latency" | "success_rate" }) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.agentsTimeSeries(filters),
    queryFn: () => getAgentTimeSeries(filters),
    refetchInterval: 30000,
    enabled: hasHydrated && !!accessToken,
  });
}

// ============================================
// Workflow Analytics Hooks
// ============================================

/**
 * Fetch workflow execution analytics
 */
export function useWorkflowAnalytics(filters?: AnalyticsFilters) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.workflows(filters),
    queryFn: () => getWorkflowAnalytics(filters),
    refetchInterval: 30000,
    enabled: hasHydrated && !!accessToken,
  });
}

/**
 * Fetch workflow time series data for charts
 */
export function useWorkflowTimeSeries(filters?: TimeSeriesFilters & { metric?: "executions" | "duration" | "success_rate" }) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.workflowsTimeSeries(filters),
    queryFn: () => getWorkflowTimeSeries(filters),
    refetchInterval: 30000,
    enabled: hasHydrated && !!accessToken,
  });
}

// ============================================
// Dashboard Summary Hook
// ============================================

/**
 * Fetch comprehensive dashboard summary
 */
export function useDashboardSummary() {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.dashboard(),
    queryFn: getDashboardSummary,
    refetchInterval: 30000,
    enabled: hasHydrated && !!accessToken,
  });
}

// ============================================
// Top Entities Hooks
// ============================================

/**
 * Fetch top workflows by execution count
 */
export function useTopWorkflows(filters?: AnalyticsFilters & { limit?: number }) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.topWorkflows(filters),
    queryFn: () => getTopWorkflows(filters),
    refetchInterval: 30000,
    enabled: hasHydrated && !!accessToken,
  });
}

/**
 * Fetch top agents by execution count
 */
export function useTopAgents(filters?: AnalyticsFilters & { limit?: number }) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.topAgents(filters),
    queryFn: () => getTopAgents(filters),
    refetchInterval: 30000,
    enabled: hasHydrated && !!accessToken,
  });
}

/**
 * Fetch top LLM models by usage
 */
export function useTopModels(filters?: AnalyticsFilters & { limit?: number }) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.topModels(filters),
    queryFn: () => getTopModels(filters),
    refetchInterval: 30000,
    enabled: hasHydrated && !!accessToken,
  });
}

// ============================================
// Error Analytics Hook
// ============================================

/**
 * Fetch error analytics
 */
export function useErrorAnalytics(filters?: AnalyticsFilters) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.errors(filters),
    queryFn: () => getErrorAnalytics(filters),
    refetchInterval: 30000,
    enabled: hasHydrated && !!accessToken,
  });
}

// ============================================
// Knowledge Base Analytics Hook
// ============================================

/**
 * Fetch knowledge base analytics
 */
export function useKnowledgeAnalytics() {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.knowledge(),
    queryFn: getKnowledgeAnalytics,
    refetchInterval: 60000, // Refresh every minute
    enabled: hasHydrated && !!accessToken,
  });
}

// ============================================
// Cost Analytics Hooks
// ============================================

/**
 * Fetch cost breakdown by provider, model, and agent
 */
export function useCostBreakdown(filters?: AnalyticsFilters) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.costBreakdown(filters),
    queryFn: () => getCostBreakdown(filters),
    refetchInterval: 60000,
    enabled: hasHydrated && !!accessToken,
  });
}

/**
 * Fetch cost trend over time
 */
export function useCostTrend(filters?: { interval?: "1h" | "1d" | "1w"; start?: string; end?: string }) {
  const { hasHydrated, accessToken } = useAuth();

  return useQuery({
    queryKey: monitoringKeys.costTrend(filters),
    queryFn: () => getCostTrend(filters),
    refetchInterval: 60000,
    enabled: hasHydrated && !!accessToken,
  });
}
