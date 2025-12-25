/**
 * Monitoring types for logs and analytics
 */

// ============================================
// Log Types
// ============================================

export interface LogEntry {
  timestamp: string;
  service: string;
  level: string | null;
  message: string;
  labels: Record<string, string>;
}

export interface LogsResponse {
  logs: LogEntry[];
  total: number;
}

export interface LogFilters {
  service?: string;
  level?: string;
  search?: string;
  limit?: number;
  start?: string;
  end?: string;
}

export interface LogService {
  id: string;
  name: string;
}

export interface LogServicesResponse {
  services: LogService[];
}

// ============================================
// LLM Analytics Types
// ============================================

export interface LLMUsageStats {
  total_requests: number;
  total_tokens: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_cost_cents: number;
  avg_latency_ms: number;
  success_rate: number;
  by_provider: Record<string, { count: number; cost_cents: number }>;
  by_model: Record<string, { count: number; tokens: number }>;
}

// ============================================
// Agent Analytics Types
// ============================================

export interface AgentStats {
  total_executions: number;
  success_rate: number;
  avg_latency_ms: number;
  by_type: Record<string, { count: number; avg_latency_ms: number }>;
}

// ============================================
// Time Series Types
// ============================================

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
}

export interface TimeSeriesResponse {
  metric: string;
  interval: string;
  data: TimeSeriesPoint[];
}

export interface TimeSeriesFilters {
  metric?: "requests" | "tokens" | "cost";
  interval?: "1h" | "6h" | "1d";
  start?: string;
  end?: string;
}

// ============================================
// Analytics Filters
// ============================================

export interface AnalyticsFilters {
  start?: string;
  end?: string;
}
