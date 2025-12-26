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

export interface EndNodeData extends Record<string, unknown> {
  type: "end";
}

export type CanvasNodeData = TriggerNodeData | AgentNodeData | ConditionalNodeData | ParallelNodeData | EndNodeData;

// Canvas node types
export type TriggerNode = Node<TriggerNodeData, "trigger">;
export type AgentNode = Node<AgentNodeData, "agent">;
export type ConditionalNode = Node<ConditionalNodeData, "conditional">;
export type ParallelNode = Node<ParallelNodeData, "parallel">;
export type EndNode = Node<EndNodeData, "end">;

export type CanvasNode = TriggerNode | AgentNode | ConditionalNode | ParallelNode | EndNode;

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
