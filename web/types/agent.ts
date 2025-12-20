// Backend agent types - must match src/models/enums.py
export type AgentType = "SimpleAgent" | "LLMAgent" | "RAGAgent" | "ToolAgent" | "FullAgent" | "RouterAgent";

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
  prohibited_actions: string[];
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
  tools: ToolReference[];
  safety: SafetyConfig;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  agent_type: AgentType;
  created: boolean;
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

export interface WorkflowResponse {
  content: string;
  agent_id: string;
  agent_type: AgentType;
  success: boolean;
  error: string | null;
  metadata: {
    tools_used: string[];
    execution_time_ms: number;
  };
  workflow_id: string;
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
