import type { Node, Edge } from "@xyflow/react";
import type { WorkflowStep, TriggerType, SuggestedAgent } from "@/types/workflow";

// Node status for validation visualization
export type NodeStatus = "ready" | "draft" | "warning" | "error";

// Node data types - use Record to satisfy ReactFlow
export interface TriggerNodeData extends Record<string, unknown> {
  type: "trigger";
  triggerType: TriggerType;
  webhookUrl?: string;
  webhookToken?: string;
}

export interface AgentNodeData extends Record<string, unknown> {
  type: "agent";
  stepId: string;
  name: string;
  role?: string;
  agentId?: string;
  agentName?: string;
  agentGoal?: string;
  status: NodeStatus;
  suggestedAgent?: SuggestedAgent; // AI suggestion for draft nodes
  requiredMcps?: string[];
  requiredTools?: string[];
}

// Conditional node data - for intent classification/routing
export interface ConditionalNodeData extends Record<string, unknown> {
  type: "conditional";
  stepId: string;
  name: string;
  classifierAgentId?: string; // RouterAgent that classifies input
  classifierAgentName?: string;
  branches: {
    condition: string; // e.g., "calendar", "email"
    targetStepId: string; // Step to route to
    targetStepName?: string;
  }[];
  defaultStepId?: string; // Default step if no match
  defaultStepName?: string;
  status: NodeStatus;
}

// Parallel node data - for concurrent execution
export interface ParallelNodeData extends Record<string, unknown> {
  type: "parallel";
  stepId: string;
  name: string;
  branches: {
    id: string;
    agentId?: string;
    agentName?: string;
    input?: string;
    timeout?: number;
  }[];
  aggregation: "all" | "first" | "merge" | "best";
  status: NodeStatus;
  viewMode: "grouped" | "expanded"; // Toggle between container and separate nodes
}

// Loop node data - for iteration steps
export type LoopMode = "count" | "foreach" | "until";

export interface LoopInnerStepData {
  id: string;
  agentId?: string;
  agentName?: string;
  input?: string;
  timeout?: number;
}

export interface LoopNodeData extends Record<string, unknown> {
  type: "loop";
  stepId: string;
  name: string;
  loopMode: LoopMode;
  maxIterations: number;
  over?: string; // Expression to iterate over (foreach mode)
  itemVariable?: string; // Variable name for current item
  exitCondition?: string; // Exit condition
  breakCondition?: string; // Break condition
  continueCondition?: string; // Continue condition
  collectResults: boolean;
  innerSteps: LoopInnerStepData[];
  status: NodeStatus;
}

// Approval node data - for human-in-the-loop approval gates
export interface ApprovalNodeData extends Record<string, unknown> {
  type: "approval";
  stepId: string;
  name: string;
  approvalMessage: string;
  approvers: string[]; // User IDs, emails, or role patterns (e.g., "role:admin")
  requiredApprovals: number;
  timeoutSeconds?: number;
  onReject: "fail" | "skip" | string; // "fail", "skip", or step_id to jump to
  status: NodeStatus;
}

export interface EndNodeData extends Record<string, unknown> {
  type: "end";
}

export type CanvasNodeData = TriggerNodeData | AgentNodeData | ConditionalNodeData | ParallelNodeData | LoopNodeData | ApprovalNodeData | EndNodeData;

// Canvas node types
export type TriggerNode = Node<TriggerNodeData, "trigger">;
export type AgentNode = Node<AgentNodeData, "agent">;
export type ConditionalNode = Node<ConditionalNodeData, "conditional">;
export type ParallelNode = Node<ParallelNodeData, "parallel">;
export type LoopNode = Node<LoopNodeData, "loop">;
export type ApprovalNode = Node<ApprovalNodeData, "approval">;
export type EndNode = Node<EndNodeData, "end">;

export type CanvasNode = TriggerNode | AgentNode | ConditionalNode | ParallelNode | LoopNode | ApprovalNode | EndNode;

// Edge types - use Record to satisfy ReactFlow
export interface DataFlowEdgeData extends Record<string, unknown> {
  animated?: boolean;
  label?: string;
}

export type CanvasEdge = Edge<DataFlowEdgeData>;

// Canvas state
export interface CanvasState {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  selectedNodeId: string | null;
}

// Validation types
export interface WorkflowValidation {
  isValid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
}

export interface ValidationIssue {
  nodeId: string;
  type: "error" | "warning";
  message: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
}

// Workflow step with enhanced data for canvas
export interface EnhancedStep extends WorkflowStep {
  name?: string;
  role?: string;
  status?: NodeStatus;
  agentName?: string;
  agentExists?: boolean;
}
