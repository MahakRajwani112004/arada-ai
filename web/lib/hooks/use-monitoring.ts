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
} from "@/lib/api/monitoring";
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
};

// ============================================
// Logs Hooks
// ============================================

/**
 * Fetch logs with optional filters
 */
export function useLogs(filters?: LogFilters) {
  return useQuery({
    queryKey: monitoringKeys.logsList(filters),
    queryFn: () => getLogs(filters),
    refetchInterval: 10000, // Auto-refresh every 10 seconds
  });
}

/**
 * Fetch available log services
 */
export function useLogServices() {
  return useQuery({
    queryKey: monitoringKeys.logServices(),
    queryFn: getLogServices,
    staleTime: 60000, // Cache for 1 minute
  });
}

// ============================================
// LLM Analytics Hooks
// ============================================

/**
 * Fetch LLM usage analytics
 */
export function useLLMAnalytics(filters?: AnalyticsFilters) {
  return useQuery({
    queryKey: monitoringKeys.llm(filters),
    queryFn: () => getLLMAnalytics(filters),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

/**
 * Fetch LLM time series data for charts
 */
export function useLLMTimeSeries(filters?: TimeSeriesFilters) {
  return useQuery({
    queryKey: monitoringKeys.llmTimeSeries(filters),
    queryFn: () => getLLMTimeSeries(filters),
    refetchInterval: 30000,
  });
}

// ============================================
// Agent Analytics Hooks
// ============================================

/**
 * Fetch agent execution analytics
 */
export function useAgentAnalytics(filters?: AnalyticsFilters) {
  return useQuery({
    queryKey: monitoringKeys.agents(filters),
    queryFn: () => getAgentAnalytics(filters),
    refetchInterval: 30000,
  });
}
