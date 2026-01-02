// AI Generation types for workflow creation
// These types support the user-controlled agent creation flow

// Re-export types from workflow.ts
export type {
  GeneratedAgentConfig,
  GeneratedAgentRole,
  GeneratedAgentGoal,
  GeneratedAgentInstructions,
  AgentSuggestion,
  MCPSuggestion,
  GenerateWorkflowRequest,
  GenerateWorkflowResponse,
  SaveGeneratedWorkflowRequest,
  SaveGeneratedWorkflowResponse,
} from "./workflow";

// ==================== Agent Creation Progress ====================

/** Tracks progress through multi-agent creation wizard */
export interface AgentCreationProgress {
  /** Total agents to create */
  total: number;
  /** How many created so far */
  created: number;
  /** Agents that were skipped */
  skipped: string[];
  /** Currently creating (index) */
  current_index: number;
}

/** State for the AI generation wizard */
export type GenerationWizardStep =
  | "describe"
  | "loading"
  | "review"
  | "create_agents"
  | "save";

export interface GenerationWizardState {
  /** Current wizard step */
  step: GenerationWizardStep;
  /** User's original prompt */
  prompt: string;
  /** Generated response from AI */
  generated?: import("./workflow").GenerateWorkflowResponse;
  /** Progress through agent creation */
  agent_progress?: AgentCreationProgress;
  /** Final workflow name (set in save step) */
  workflow_name?: string;
  /** Final workflow description */
  workflow_description?: string;
  /** Final workflow category */
  workflow_category?: string;
}
