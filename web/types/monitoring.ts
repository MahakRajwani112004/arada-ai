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

// ============================================
// Workflow Analytics Types
// ============================================

export interface WorkflowStats {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number;
  avg_duration_ms: number;
  total_duration_ms: number;
  by_status: Record<string, number>;
  by_workflow: Record<string, { count: number; avg_duration_ms: number }>;
}

// ============================================
// Dashboard Summary Types
// ============================================

export interface DashboardSummary {
  total_agents: number;
  total_workflows: number;
  total_mcp_servers: number;
  total_knowledge_bases: number;
  executions_24h: number;
  llm_calls_24h: number;
  tokens_used_24h: number;
  cost_cents_24h: number;
  agent_success_rate_24h: number;
  workflow_success_rate_24h: number;
  active_mcp_servers: number;
  recent_workflows: Array<{ id: string; name: string; updated_at: string }>;
  recent_executions: Array<{
    id: string;
    workflow_id: string;
    status: string;
    started_at: string;
    duration_ms: number | null;
  }>;
}

// ============================================
// Top Entities Types
// ============================================

export interface TopWorkflow {
  workflow_id: string;
  name: string;
  execution_count: number;
  success_rate: number;
  avg_duration_ms: number;
}

export interface TopWorkflowsResponse {
  workflows: TopWorkflow[];
  total: number;
}

export interface TopAgent {
  agent_id: string;
  name: string;
  agent_type: string;
  execution_count: number;
  success_rate: number;
  avg_latency_ms: number;
  total_llm_calls: number;
  total_tool_calls: number;
}

export interface TopAgentsResponse {
  agents: TopAgent[];
  total: number;
}

export interface TopModel {
  provider: string;
  model: string;
  request_count: number;
  total_tokens: number;
  total_cost_cents: number;
  avg_latency_ms: number;
}

export interface TopModelsResponse {
  models: TopModel[];
  total: number;
}

// ============================================
// Error Analytics Types
// ============================================

export interface ErrorStats {
  total_errors: number;
  error_rate: number;
  by_type: Record<string, number>;
  by_agent: Record<string, number>;
  by_workflow: Record<string, number>;
  recent_errors: Array<{
    source: string;
    agent_id: string;
    error_type: string | null;
    error_message: string | null;
    timestamp: string;
  }>;
}

// ============================================
// Knowledge Base Analytics Types
// ============================================

export interface KnowledgeBaseStats {
  total_knowledge_bases: number;
  total_documents: number;
  total_chunks: number;
  by_status: Record<string, number>;
  by_knowledge_base: Array<{
    id: string;
    name: string;
    document_count: number;
    chunk_count: number;
    status: string;
  }>;
}

// ============================================
// Cost Analytics Types
// ============================================

export interface CostBreakdown {
  total_cost_cents: number;
  period: { start: string; end: string };
  by_provider: Array<{ provider: string; cost_cents: number; tokens: number }>;
  by_model: Array<{ model: string; cost_cents: number; tokens: number }>;
  by_agent: Array<{ agent_id: string; cost_cents: number; calls: number }>;
}

export interface CostTrendPoint {
  timestamp: string;
  cost_cents: number;
  tokens: number;
  requests: number;
}

export interface CostTrendResponse {
  interval: string;
  data: CostTrendPoint[];
}
