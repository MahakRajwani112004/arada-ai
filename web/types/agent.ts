// Backend agent types - must match src/models/enums.py
export type AgentType = "SimpleAgent" | "LLMAgent" | "RAGAgent" | "ToolAgent" | "FullAgent" | "RouterAgent" | "OrchestratorAgent";

// RouterAgent configuration - maps intent categories to target agents
export interface RouterConfig {
  routing_table: Record<string, RoutingEntry>;
  confidence_threshold?: number;
}

export interface RoutingEntry {
  target_agent: string;
  description?: string;
}

export interface AgentRole {
  title: string;
  expertise: string[];
  personality: string[];  // API expects array
  communication_style: string;
}

export interface AgentGoal {
  objective: string;
  success_criteria: string[];
  constraints: string[];
}

export interface AgentInstructions {
  steps: string[];
  rules: string[];
  prohibited: string[];  // Must match backend field name
  output_format: string;
}

export interface AgentExample {
  input: string;
  output: string;
}

export interface LLMConfig {
  provider: "openai" | "anthropic";
  model: string;
  temperature: number;
}

export interface ToolReference {
  tool_id: string;
}

export interface SkillConfig {
  skill_id: string;
  enabled: boolean;
  parameters: Record<string, unknown>;
  priority: number;
}

export interface KnowledgeBaseConfig {
  collection_name: string;
  embedding_model?: string;
  top_k?: number;
  similarity_threshold?: number;
}

// API expects lowercase
export type SafetyLevel = "low" | "standard" | "high" | "maximum";

export interface SafetyConfig {
  level: SafetyLevel;
  blocked_topics: string[];
  blocked_patterns: string[];
}

export interface AgentCreate {
  id: string;
  name: string;
  description: string;
  agent_type: AgentType;
  role: AgentRole;
  goal: AgentGoal;
  instructions: AgentInstructions;
  examples: AgentExample[];
  llm_config: LLMConfig;
  knowledge_base?: KnowledgeBaseConfig;
  tools: ToolReference[];
  skills?: SkillConfig[];
  safety: SafetyConfig;
  // RouterAgent specific
  router_config?: RouterConfig;
  // OrchestratorAgent specific
  orchestrator_config?: OrchestratorConfig;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  agent_type: AgentType;
  created: boolean;
}

// Full agent details for editing
export interface AgentDetail {
  id: string;
  name: string;
  description: string;
  agent_type: AgentType;
  role: AgentRole;
  goal: AgentGoal;
  instructions: {
    steps: string[];
    rules: string[];
    prohibited: string[];
    output_format: string | null;
  };
  examples: AgentExample[];
  llm_config: LLMConfig | null;
  knowledge_base: KnowledgeBaseConfig | null;
  tools: ToolReference[];
  skills?: SkillConfig[];
  routing_table: Record<string, string> | null;
  orchestrator_config: OrchestratorConfig | null;
  safety: SafetyConfig;
}

export interface OrchestratorConfig {
  mode: string;
  available_agents: AgentReference[];
  workflow_definition: string | null;
  default_aggregation: string;
  max_parallel: number;
  max_depth: number;
  allow_self_reference: boolean;
}

export interface AgentReference {
  agent_id: string;
  alias: string | null;
  description: string | null;
}

export interface AgentListResponse {
  agents: Agent[];
  total: number;
}

export interface WorkflowRequest {
  agent_id: string;
  user_input: string;
  conversation_history?: { role: "user" | "assistant"; content: string }[];
  session_id?: string;
}

// Tool call result returned in metadata
export interface ToolCallResult {
  tool: string;
  args: Record<string, unknown>;
  result: {
    success: boolean;
    output: unknown;
    error?: string;
  };
}

// Matches backend ExecuteAgentResponse schema
export interface WorkflowResponse {
  content: string;
  agent_id: string;
  agent_type: AgentType;
  success: boolean;
  error: string | null;
  metadata: {
    model?: string;
    usage?: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
    tool_calls?: ToolCallResult[];
    iterations?: number;
    validation_retries?: number;
    finish_reason?: string;
    loop_detected?: boolean;
    execution_time_ms?: number;
    // Orchestrator specific
    agent_results?: Record<string, unknown>[];
    mode?: string;
  };
  workflow_id: string | null;

  // Clarification fields - for interactive follow-up questions
  requires_clarification?: boolean;
  clarification_question?: string;
  clarification_options?: string[];
}

export type WorkflowStatus = "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";

export interface WorkflowStatusResponse {
  workflow_id: string;
  status: WorkflowStatus;
  result?: {
    content: string;
    success: boolean;
  };
}

// AI Generation types
export interface GenerateAgentRequest {
  name: string;
  context?: string;
}

export interface GenerateAgentResponse {
  description: string;
  role: AgentRole;
  goal: AgentGoal;
  instructions: {
    steps: string[];
    rules: string[];
    prohibited: string[];
    output_format: string | null;
  };
  examples: AgentExample[];
  suggested_agent_type: AgentType;
}

// ============================================================================
// Agent Overview Tab Types
// ============================================================================

export type TimeRange = "24h" | "7d" | "30d" | "90d";

export interface AgentStats {
  agent_id: string;
  time_range: TimeRange;

  // Performance metrics
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number; // 0.0 to 1.0
  avg_latency_ms: number;
  p95_latency_ms: number;

  // Cost metrics
  total_cost_cents: number;
  total_tokens: number;

  // Trends (percentage change vs previous period)
  executions_trend: number;
  success_trend: number;
  latency_trend: number;
  cost_trend: number;
}

export interface ExecutionSummary {
  id: string;
  status: "completed" | "failed";
  timestamp: string; // ISO format
  duration_ms: number;
  input_preview: string | null;
  output_preview: string | null;
  error_type: string | null;
  error_message: string | null;
  total_tokens: number;
  total_cost_cents: number;
}

export interface AgentExecutionsResponse {
  executions: ExecutionSummary[];
  total: number;
  has_more: boolean;
}

export interface UsageDataPoint {
  timestamp: string; // ISO format
  executions: number;
  successful: number;
  failed: number;
  avg_latency_ms: number;
  total_cost_cents: number;
}

export interface AgentUsageHistory {
  data: UsageDataPoint[];
  granularity: "hour" | "day";
  time_range: TimeRange;
}

// Full execution details with metadata
export interface ExecutionDetail {
  id: string;
  agent_id: string;
  agent_type: AgentType;
  timestamp: string;
  status: "completed" | "failed";
  duration_ms: number;
  input_preview: string | null;
  output_preview: string | null;
  total_tokens: number;
  total_cost_cents: number;
  llm_calls_count: number;
  tool_calls_count: number;
  error_type: string | null;
  error_message: string | null;
  workflow_id: string | null;
  execution_metadata: ExecutionMetadata | null;
}

export interface ExecutionMetadata {
  model?: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  tool_calls?: ToolCallDetail[];
  agent_results?: AgentCallResult[];
  iterations?: number;
  mode?: string;
  // Add other potential fields
  [key: string]: unknown;
}

export interface ToolCallDetail {
  tool: string;
  args: Record<string, unknown>;
  result: {
    success: boolean;
    output: unknown;
    error?: string;
  };
}

export interface AgentCallResult {
  agent_id: string;
  content: string;
  success: boolean;
  error?: string;
  metadata?: Record<string, unknown>;
}
