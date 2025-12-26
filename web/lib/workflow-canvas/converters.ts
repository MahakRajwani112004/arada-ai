import type { WorkflowDefinition, WorkflowStep, WorkflowTrigger, TriggerType } from "@/types/workflow";
import type { Agent } from "@/types/agent";
import type {
  CanvasNode,
  CanvasEdge,
  NodeStatus,
  TriggerNodeData,
  AgentNodeData,
  ConditionalNodeData,
  ParallelNodeData,
  EndNodeData
} from "./types";
import { createEdge, applyAutoLayout } from "./layout";

interface ConversionContext {
  agents?: Agent[];
  connectedMcps?: string[];
  baseWebhookUrl?: string;
}

// Canvas layout stored in workflow.definition.context
export interface CanvasLayout {
  positions: Record<string, { x: number; y: number }>;
  savedAt?: string;
}

/**
 * Convert a WorkflowDefinition to ReactFlow nodes and edges
 */
export function workflowToCanvas(
  definition: WorkflowDefinition,
  trigger?: WorkflowTrigger,
  context: ConversionContext = {}
): { nodes: CanvasNode[]; edges: CanvasEdge[] } {
  const nodes: CanvasNode[] = [];
  const edges: CanvasEdge[] = [];

  // 1. Create trigger node
  const triggerNode = createTriggerNode(trigger, context);
  nodes.push(triggerNode);

  // 2. Create nodes for each step based on type
  definition.steps.forEach((step, index) => {
    let node: CanvasNode;

    switch (step.type) {
      case "conditional":
        node = createConditionalNode(step, index, context, definition.steps);
        break;
      case "parallel":
        node = createParallelNode(step, index, context);
        break;
      case "agent":
      default:
        node = createAgentNode(step, index, context);
        break;
    }

    nodes.push(node);

    // Create edge from previous node
    if (index === 0) {
      // First step connects to trigger
      edges.push(createEdge("trigger", step.id));
    } else {
      // Connect to previous step (for linear flow)
      // Note: Conditional steps will have additional edges created below
      const prevStep = definition.steps[index - 1];
      if (prevStep.type !== "conditional") {
        edges.push(createEdge(prevStep.id, step.id));
      }
    }

    // Create edges for conditional branches
    if (step.type === "conditional" && step.conditional_branches) {
      Object.entries(step.conditional_branches).forEach(([condition, targetStepId]) => {
        edges.push(createEdge(step.id, targetStepId, { label: condition }));
      });
      // Add default branch edge
      if (step.default) {
        edges.push(createEdge(step.id, step.default, { label: "default" }));
      }
    }
  });

  // 3. Create end node
  const endNode = createEndNode();
  nodes.push(endNode);

  // Connect last step to end node
  if (definition.steps.length > 0) {
    const lastStep = definition.steps[definition.steps.length - 1];
    edges.push(createEdge(lastStep.id, "end"));
  } else {
    // No steps - connect trigger directly to end
    edges.push(createEdge("trigger", "end"));
  }

  // 4. Apply saved positions or auto-layout
  const savedLayout = definition.context?.canvas_layout as CanvasLayout | undefined;

  let layoutedNodes: CanvasNode[];
  if (savedLayout?.positions && Object.keys(savedLayout.positions).length > 0) {
    // Use saved positions
    layoutedNodes = nodes.map((node) => {
      const savedPosition = savedLayout.positions[node.id];
      if (savedPosition) {
        return { ...node, position: savedPosition };
      }
      return node;
    });
    // Apply auto-layout only for nodes without saved positions
    const nodesWithoutPosition = layoutedNodes.filter(
      (n) => !savedLayout.positions[n.id]
    );
    if (nodesWithoutPosition.length > 0) {
      layoutedNodes = applyAutoLayout(layoutedNodes, edges);
    }
  } else {
    // No saved layout - use auto-layout
    layoutedNodes = applyAutoLayout(nodes, edges);
  }

  return { nodes: layoutedNodes, edges };
}

/**
 * Create a trigger node
 */
function createTriggerNode(
  trigger?: WorkflowTrigger,
  context?: ConversionContext
): CanvasNode {
  const triggerType: TriggerType = trigger?.type || "manual";
  const webhookConfig = trigger?.webhook_config;

  const data: TriggerNodeData = {
    type: "trigger",
    triggerType,
    webhookUrl: webhookConfig?.token
      ? `${context?.baseWebhookUrl || "/api/v1/webhooks"}/${webhookConfig.token}`
      : undefined,
    webhookToken: webhookConfig?.token,
  };

  return {
    id: "trigger",
    type: "trigger",
    position: { x: 0, y: 0 },
    data,
  };
}

/**
 * Create an agent node from a workflow step
 */
function createAgentNode(
  step: WorkflowStep,
  index: number,
  context: ConversionContext = {}
): CanvasNode {
  // Find the agent if it exists by ID
  let agent = context.agents?.find((a) => a.id === step.agent_id);

  // If no agent by ID but we have a suggested_agent, check if an agent with matching name exists
  // This handles the case where agent was created but workflow wasn't saved with agent_id
  if (!agent && step.suggested_agent?.name) {
    const expectedAgentId = step.suggested_agent.name
      .toLowerCase()
      .replace(/\s+/g, "-")
      .replace(/[^a-z0-9-]/g, "");
    agent = context.agents?.find((a) => a.id === expectedAgentId);
  }

  // Determine node status
  const status = determineNodeStatus(step, agent);

  // Get the step name from the step itself, the agent, or generate default
  const stepName = step.name || agent?.name || `Step ${index + 1}`;

  const data: AgentNodeData = {
    type: "agent",
    stepId: step.id,
    name: stepName,
    role: step.input || undefined,
    // Use found agent's ID (even if it was found by name match)
    agentId: agent?.id || step.agent_id,
    agentName: agent?.name,
    agentGoal: agent?.description || step.suggested_agent?.goal,
    status,
    // Clear suggestedAgent if we found an existing agent
    suggestedAgent: agent ? undefined : step.suggested_agent,
    requiredMcps: step.suggested_agent?.required_mcps,
    requiredTools: step.suggested_agent?.suggested_tools,
  };

  return {
    id: step.id,
    type: "agent",
    position: { x: 0, y: 0 },
    data,
  };
}

/**
 * Create a conditional node from a workflow step
 */
function createConditionalNode(
  step: WorkflowStep,
  index: number,
  context: ConversionContext = {},
  allSteps: WorkflowStep[]
): CanvasNode {
  // Find the classifier agent
  const classifierAgent = context.agents?.find((a) => a.id === step.condition_source);

  // Build branches array from conditional_branches
  const branches = Object.entries(step.conditional_branches || {}).map(([condition, targetStepId]) => {
    const targetStep = allSteps.find((s) => s.id === targetStepId);
    return {
      condition,
      targetStepId,
      targetStepName: targetStep?.name || targetStepId,
    };
  });

  // Find default step
  const defaultStep = step.default ? allSteps.find((s) => s.id === step.default) : undefined;

  // Determine status
  const status: NodeStatus = step.condition_source && classifierAgent ? "ready" : "draft";

  const data: ConditionalNodeData = {
    type: "conditional",
    stepId: step.id,
    name: step.name || `Conditional ${index + 1}`,
    classifierAgentId: step.condition_source,
    classifierAgentName: classifierAgent?.name,
    branches,
    defaultStepId: step.default,
    defaultStepName: defaultStep?.name,
    status,
  };

  return {
    id: step.id,
    type: "conditional",
    position: { x: 0, y: 0 },
    data,
  };
}

/**
 * Create a parallel node from a workflow step
 */
function createParallelNode(
  step: WorkflowStep,
  index: number,
  context: ConversionContext = {}
): CanvasNode {
  // Build branches array
  const branches = (step.branches || []).map((branch, branchIndex) => {
    const branchData = branch as { id?: string; agent_id?: string; input?: string; timeout?: number };
    const agent = context.agents?.find((a) => a.id === branchData.agent_id);
    return {
      id: branchData.id || `branch-${branchIndex}`,
      agentId: branchData.agent_id,
      agentName: agent?.name,
      input: branchData.input,
      timeout: branchData.timeout,
    };
  });

  // Determine status - ready if all branches have agents
  const allBranchesReady = branches.every((b) => b.agentId && context.agents?.some((a) => a.id === b.agentId));
  const status: NodeStatus = branches.length > 0 && allBranchesReady ? "ready" : "draft";

  const data: ParallelNodeData = {
    type: "parallel",
    stepId: step.id,
    name: step.name || `Parallel ${index + 1}`,
    branches,
    aggregation: step.aggregation || "all",
    status,
    viewMode: "grouped", // Default to grouped view
  };

  return {
    id: step.id,
    type: "parallel",
    position: { x: 0, y: 0 },
    data,
  };
}

/**
 * Create the end node
 */
function createEndNode(): CanvasNode {
  const data: EndNodeData = {
    type: "end",
  };

  return {
    id: "end",
    type: "end",
    position: { x: 0, y: 0 },
    data,
  };
}

/**
 * Determine the status of a node based on its dependencies
 */
function determineNodeStatus(
  step: WorkflowStep,
  agent?: Agent
): NodeStatus {
  // If we found an agent (by ID or by name match), it's ready
  if (agent) {
    return "ready";
  }

  // No agent assigned and no agent found
  if (!step.agent_id) {
    return "draft";
  }

  // Agent ID is set but agent doesn't exist (deleted?)
  return "error";
}

/**
 * Convert canvas nodes back to WorkflowDefinition
 * (For saving changes made in the canvas)
 */
export function canvasToWorkflow(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  originalDefinition: WorkflowDefinition
): WorkflowDefinition {
  // Get all workflow nodes (exclude trigger and end)
  const workflowNodes = nodes
    .filter((n) => n.type !== "trigger" && n.type !== "end")
    .sort((a, b) => a.position.y - b.position.y);

  // Build new steps array
  const steps: WorkflowStep[] = workflowNodes.map((node) => {
    // Find original step to preserve properties
    const originalStep = originalDefinition.steps.find(
      (s) => s.id === (node.data as { stepId?: string }).stepId
    );

    if (node.type === "conditional") {
      const data = node.data as ConditionalNodeData;
      // Convert branches array back to conditional_branches object
      const conditionalBranches: Record<string, string> = {};
      data.branches.forEach((branch) => {
        conditionalBranches[branch.condition] = branch.targetStepId;
      });

      return {
        id: data.stepId,
        type: "conditional" as const,
        name: data.name,
        condition_source: data.classifierAgentId,
        conditional_branches: conditionalBranches,
        default: data.defaultStepId,
        timeout: originalStep?.timeout || 120,
        retries: originalStep?.retries || 0,
        on_error: originalStep?.on_error || "fail",
      };
    }

    if (node.type === "parallel") {
      const data = node.data as ParallelNodeData;
      // Convert branches array back to workflow format
      const branches = data.branches.map((branch) => ({
        id: branch.id,
        agent_id: branch.agentId,
        input: branch.input || "${user_input}",
        timeout: branch.timeout || 120,
      }));

      return {
        id: data.stepId,
        type: "parallel" as const,
        name: data.name,
        branches,
        aggregation: data.aggregation,
        timeout: originalStep?.timeout || 120,
        retries: originalStep?.retries || 0,
        on_error: originalStep?.on_error || "fail",
      };
    }

    // Default: Agent node
    const data = node.data as AgentNodeData;
    return {
      id: data.stepId,
      type: "agent" as const,
      name: data.name,
      agent_id: data.agentId,
      suggested_agent: data.suggestedAgent,
      input: data.role || originalStep?.input || "${user_input}",
      timeout: originalStep?.timeout || 120,
      retries: originalStep?.retries || 0,
      on_error: originalStep?.on_error || "fail",
    };
  });

  return {
    ...originalDefinition,
    steps,
    entry_step: steps[0]?.id,
  };
}
