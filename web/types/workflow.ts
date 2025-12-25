// Workflow types - must match src/api/schemas/workflows.py

// ==================== Step Types ====================

export type StepType = "agent" | "parallel" | "conditional" | "loop" | "tool";

export type AggregationType = "all" | "first" | "merge" | "best";

export type OnErrorAction = "fail" | "skip" | string; // string for step_id jump

export interface WorkflowStep {
  id: string;
  type: StepType;
  name?: string; // Display name for the step
  agent_id?: string;
  suggested_agent?: SuggestedAgent; // AI suggestion (before agent is created)
  input?: string;
  timeout: number;
  retries: number;
  on_error: OnErrorAction;

  // Parallel step fields
  branches?: Record<string, unknown>[];
  aggregation?: AggregationType;

  // Conditional step fields
  condition_source?: string;
  conditional_branches?: Record<string, string>;
  default?: string;

  // Loop step fields
  max_iterations?: number;
  exit_condition?: string;
  steps?: Record<string, unknown>[];
}

export interface WorkflowDefinition {
  id: string;
  name?: string;
  description?: string;
  steps: WorkflowStep[];
  entry_step?: string;
  context?: Record<string, unknown>;
}

// ==================== Workflow CRUD ====================

export interface CreateWorkflowRequest {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  definition: WorkflowDefinition;
  created_by?: string;
}

export interface UpdateWorkflowRequest {
  name?: string;
  description?: string;
  category?: string;
  tags?: string[];
  definition?: WorkflowDefinition;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  definition: WorkflowDefinition;
  version: number;
  is_template: boolean;
  is_active: boolean;
  source_template_id?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowSummary {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  version: number;
  is_template: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkflowListResponse {
  workflows: WorkflowSummary[];
  total: number;
}

export interface CopyWorkflowRequest {
  new_id: string;
  new_name: string;
  created_by?: string;
}

// ==================== Execution ====================

export type ExecutionStatus = "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";

export type StepExecutionStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "SKIPPED";

export interface StepResult {
  step_id: string;
  status: StepExecutionStatus;
  output?: unknown;
  error?: string;
  duration_ms?: number;
}

// Legacy alias for backwards compatibility
export interface StepExecutionResult {
  step_id: string;
  status: "completed" | "failed" | "skipped";
  output?: string;
  error?: string;
  duration_ms?: number;
}

export interface ExecuteWorkflowRequest {
  user_input: string;
  context?: Record<string, unknown>;
  session_id?: string;
}

export interface ExecuteWorkflowResponse {
  execution_id: string;
  workflow_id: string;
  status: ExecutionStatus;
  final_output?: string;
  step_results: StepExecutionResult[];
  total_duration_ms?: number;
  error?: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  temporal_workflow_id: string;
  status: ExecutionStatus;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  input_data: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  error?: string;
  steps_executed: string[];
  step_results: StepResult[];
  triggered_by?: string;
}

export interface WorkflowExecutionSummary {
  id: string;
  workflow_id: string;
  status: ExecutionStatus;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  triggered_by?: string;
}

export interface WorkflowExecutionListResponse {
  executions: WorkflowExecutionSummary[];
  total: number;
}

// ==================== Resource Discovery ====================

export interface AvailableAgent {
  id: string;
  name: string;
  description: string;
  agent_type: string;
}

export interface AvailableAgentsResponse {
  agents: AvailableAgent[];
  total: number;
}

export interface MCPTool {
  id: string;
  name: string;
  description: string;
}

export interface AvailableMCPServer {
  id: string;
  name: string;
  template?: string;
  status: string;
  tools: MCPTool[];
}

export interface AvailableMCPsResponse {
  mcp_servers: AvailableMCPServer[];
  total: number;
}

export interface AvailableTool {
  id: string;
  name: string;
  description: string;
  source: string; // "native" or "mcp:{server_id}"
}

export interface AvailableToolsResponse {
  tools: AvailableTool[];
  total: number;
}

// ==================== Validation ====================

export interface ValidationError {
  field: string;
  message: string;
  severity: "error" | "warning";
}

export interface ValidateWorkflowRequest {
  definition: WorkflowDefinition;
}

export interface ValidateWorkflowResponse {
  is_valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  missing_agents: string[];
  missing_mcps: string[];
}

// ==================== Filters ====================

export interface WorkflowFilters {
  category?: string;
  tags?: string[];
  is_template?: boolean;
  search?: string;
}

// ==================== Workflow Detail ====================

// Alias for workflow detail page (same as Workflow but explicit)
export type WorkflowDetail = Workflow;

// ==================== Trigger Types ====================

export type TriggerType = "manual" | "webhook";

export interface ManualTriggerConfig {
  // No additional config needed for manual triggers
}

export interface WebhookTriggerConfig {
  token: string;
  secret?: string;
  rate_limit: number;
  max_payload_kb: number;
  expected_fields: string[];
}

export interface WorkflowTrigger {
  type: TriggerType;
  manual_config?: ManualTriggerConfig;
  webhook_config?: WebhookTriggerConfig;
}

// ==================== Workflow Skeleton (Two-Phase Creation) ====================

export interface SkeletonStep {
  id: string;
  name: string;
  role: string;
  order: number;
}

export interface WorkflowSkeleton {
  name: string;
  description: string;
  trigger: WorkflowTrigger;
  steps: SkeletonStep[];
}

export interface GenerateSkeletonRequest {
  prompt: string;
  context?: string;
}

export interface SuggestedAgent {
  name: string;
  description?: string;
  goal: string;
  model?: string;
  required_mcps: string[];
  suggested_tools: string[];
}

export interface SkeletonStepWithSuggestion extends SkeletonStep {
  suggestion?: SuggestedAgent;
}

export interface MCPDependency {
  template: string;
  name: string;
  reason: string;
  connected: boolean;
}

export interface GenerateSkeletonResponse {
  skeleton: WorkflowSkeleton;
  step_suggestions: SkeletonStepWithSuggestion[];
  mcp_dependencies: MCPDependency[];
  explanation: string;
  warnings: string[];
}

export interface StepConfiguration {
  step_id: string;
  agent_id?: string;
  create_agent?: SuggestedAgent;
  skipped: boolean;
  input_template: string;
}

export interface ConfigureStepsRequest {
  skeleton: WorkflowSkeleton;
  configurations: StepConfiguration[];
}

export interface ConfigureStepsResponse {
  workflow_id: string;
  agents_created: string[];
  agents_missing: string[];
  can_execute: boolean;
  warnings: string[];
}

// ==================== AI Generation ====================

export interface GenerateWorkflowRequest {
  prompt: string;
  context?: string;
  preferred_complexity?: "simple" | "moderate" | "complex" | "auto";
  include_agents?: boolean;
  include_mcps?: boolean;
}

export interface GeneratedAgentRole {
  title: string;
  expertise?: string[];
}

export interface GeneratedAgentGoal {
  objective: string;
}

export interface GeneratedAgentInstructions {
  steps?: string[];
}

export interface GeneratedAgentConfig {
  id: string;
  name: string;
  description?: string;
  agent_type: string;
  role?: GeneratedAgentRole;
  goal?: GeneratedAgentGoal;
  instructions?: GeneratedAgentInstructions;
}

// AgentSuggestion is just GeneratedAgentConfig from the backend
// The backend returns GeneratedAgentConfig directly in agents_to_create
export type AgentSuggestion = GeneratedAgentConfig;

export interface MCPSuggestion {
  template: string;
  reason: string;
  note?: string;
}

export interface GenerateWorkflowResponse {
  workflow: WorkflowDefinition;
  existing_agents_used: string[];
  existing_mcps_used: string[];
  agents_to_create: AgentSuggestion[];
  mcps_suggested: MCPSuggestion[];
  ready_steps: string[];
  blocked_steps: string[];
  explanation: string;
  warnings?: string[];
  estimated_complexity?: string;
  can_execute: boolean;
}

export interface SaveGeneratedWorkflowRequest {
  workflow: WorkflowDefinition;
  workflow_name: string;
  workflow_description?: string;
  workflow_category?: string;
}

export interface SaveGeneratedWorkflowResponse {
  workflow_id: string;
  blocked_steps: string[];
  missing_agents: string[];
  can_execute: boolean;
  next_action: "create_agents" | "ready_to_run";
}
