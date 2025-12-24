// Workflow types - mirrors src/models/workflow_definition.py

export type StepType = "agent" | "parallel" | "conditional" | "loop";

export type ErrorHandling = "fail" | "skip";

export type AggregationType = "all" | "first" | "merge" | "best";

// ID pattern: starts with letter, alphanumeric + underscore/hyphen, max 100 chars
export const ID_PATTERN = /^[a-zA-Z][a-zA-Z0-9_-]{0,99}$/;

export interface ParallelBranch {
  id?: string;
  agent_id: string;
  input: string;
  timeout: number;
}

export interface LoopInnerStep {
  id: string;
  agent_id: string;
  input: string;
  timeout: number;
}

export interface WorkflowStep {
  id: string;
  type: StepType;

  // Agent step fields
  agent_id?: string;
  input?: string;
  timeout: number;
  retries: number;
  on_error: string;

  // Parallel step fields
  branches?: ParallelBranch[];
  aggregation: AggregationType;

  // Conditional step fields
  condition_source?: string;
  conditional_branches?: Record<string, string>;
  default?: string;

  // Loop step fields
  max_iterations: number;
  exit_condition?: string;
  steps?: LoopInnerStep[];
}

export interface WorkflowDefinition {
  id: string;
  name?: string;
  description?: string;
  steps: WorkflowStep[];
  entry_step?: string;
  context?: Record<string, unknown>;
}

// API response types
export interface WorkflowDefinitionResponse extends WorkflowDefinition {
  created_at: string;
  updated_at: string;
}

export interface WorkflowListResponse {
  workflows: WorkflowDefinitionResponse[];
  total: number;
}

export interface WorkflowValidationResponse {
  valid: boolean;
  errors: string[];
}

// Create/Update request types
export interface CreateWorkflowRequest {
  id: string;
  name?: string;
  description?: string;
  steps: WorkflowStep[];
  entry_step?: string;
  context?: Record<string, unknown>;
}

export interface UpdateWorkflowRequest {
  name?: string;
  description?: string;
  steps?: WorkflowStep[];
  entry_step?: string;
  context?: Record<string, unknown>;
}

// React Flow node data types
export interface WorkflowNodeData {
  stepType: StepType;
  label: string;

  // Agent fields
  agentId?: string;
  agentName?: string;
  input?: string;
  timeout: number;
  retries: number;
  onError: string;

  // Parallel fields
  branches?: ParallelBranch[];
  aggregation: AggregationType;

  // Conditional fields
  conditionSource?: string;
  conditionalBranches?: Record<string, string>;
  defaultStep?: string;

  // Loop fields
  maxIterations: number;
  exitCondition?: string;
  loopSteps?: LoopInnerStep[];
}

// Default values for new steps
export const DEFAULT_STEP_VALUES: Record<StepType, Partial<WorkflowNodeData>> = {
  agent: {
    stepType: "agent",
    label: "Agent Step",
    agentId: "",
    input: "${user_input}",
    timeout: 120,
    retries: 0,
    onError: "fail",
    aggregation: "all",
    maxIterations: 5,
  },
  parallel: {
    stepType: "parallel",
    label: "Parallel Step",
    branches: [],
    aggregation: "all",
    timeout: 120,
    retries: 0,
    onError: "fail",
    maxIterations: 5,
  },
  conditional: {
    stepType: "conditional",
    label: "Conditional Step",
    conditionSource: "",
    conditionalBranches: {},
    defaultStep: "",
    timeout: 120,
    retries: 0,
    onError: "fail",
    aggregation: "all",
    maxIterations: 5,
  },
  loop: {
    stepType: "loop",
    label: "Loop Step",
    maxIterations: 5,
    exitCondition: "",
    loopSteps: [],
    timeout: 120,
    retries: 0,
    onError: "fail",
    aggregation: "all",
  },
};

// Convert React Flow node data to WorkflowStep
export function nodeDataToStep(nodeId: string, data: WorkflowNodeData): WorkflowStep {
  const step: WorkflowStep = {
    id: nodeId,
    type: data.stepType,
    timeout: data.timeout,
    retries: data.retries,
    on_error: data.onError,
    aggregation: data.aggregation,
    max_iterations: data.maxIterations,
  };

  switch (data.stepType) {
    case "agent":
      step.agent_id = data.agentId;
      step.input = data.input;
      break;
    case "parallel":
      step.branches = data.branches;
      step.aggregation = data.aggregation;
      break;
    case "conditional":
      step.condition_source = data.conditionSource;
      step.conditional_branches = data.conditionalBranches;
      step.default = data.defaultStep;
      break;
    case "loop":
      step.max_iterations = data.maxIterations;
      step.exit_condition = data.exitCondition;
      step.steps = data.loopSteps;
      break;
  }

  return step;
}

// Convert WorkflowStep to React Flow node data
export function stepToNodeData(step: WorkflowStep): WorkflowNodeData {
  return {
    stepType: step.type,
    label: `${step.type.charAt(0).toUpperCase() + step.type.slice(1)} Step`,
    agentId: step.agent_id,
    input: step.input,
    timeout: step.timeout,
    retries: step.retries,
    onError: step.on_error,
    branches: step.branches,
    aggregation: step.aggregation,
    conditionSource: step.condition_source,
    conditionalBranches: step.conditional_branches,
    defaultStep: step.default,
    maxIterations: step.max_iterations,
    exitCondition: step.exit_condition,
    loopSteps: step.steps,
  };
}
