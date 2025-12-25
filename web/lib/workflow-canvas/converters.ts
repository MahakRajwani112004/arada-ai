import type { WorkflowDefinition, WorkflowStep, WorkflowTrigger, TriggerType } from "@/types/workflow";
import type { Agent } from "@/types/agent";
import type { CanvasNode, CanvasEdge, NodeStatus, TriggerNodeData, AgentNodeData, EndNodeData } from "./types";
import { createEdge, applyAutoLayout } from "./layout";

interface ConversionContext {
  agents?: Agent[];
  connectedMcps?: string[];
  baseWebhookUrl?: string;
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

  // 2. Create agent nodes for each step
  definition.steps.forEach((step, index) => {
    const agentNode = createAgentNode(step, index, context);
    nodes.push(agentNode);

    // Create edge from previous node
    if (index === 0) {
      // First step connects to trigger
      edges.push(createEdge("trigger", step.id));
    } else {
      // Connect to previous step
      const prevStep = definition.steps[index - 1];
      edges.push(createEdge(prevStep.id, step.id));
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

  // 4. Apply auto-layout
  const layoutedNodes = applyAutoLayout(nodes, edges);

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
  // Find the agent if it exists
  const agent = context.agents?.find((a) => a.id === step.agent_id);

  // Determine node status
  const status = determineNodeStatus(step, agent);

  // Get the step name from the step itself, the agent, or generate default
  const stepName = step.name || agent?.name || `Step ${index + 1}`;

  const data: AgentNodeData = {
    type: "agent",
    stepId: step.id,
    name: stepName,
    role: step.input || undefined,
    agentId: step.agent_id,
    agentName: agent?.name,
    agentGoal: agent?.description || step.suggested_agent?.goal,
    status,
    suggestedAgent: step.suggested_agent,
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
  // No agent assigned
  if (!step.agent_id) {
    return "draft";
  }

  // Agent doesn't exist
  if (!agent) {
    return "error";
  }

  // Agent exists - ready to go
  return "ready";
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
  // Get agent nodes in order
  const agentNodes = nodes
    .filter((n): n is CanvasNode & { data: AgentNodeData } => n.type === "agent")
    .sort((a, b) => {
      // Sort by y position (top to bottom)
      return a.position.y - b.position.y;
    });

  // Build new steps array
  const steps: WorkflowStep[] = agentNodes.map((node) => {
    // Find original step to preserve properties
    const originalStep = originalDefinition.steps.find(
      (s) => s.id === node.data.stepId
    );

    return {
      id: node.data.stepId,
      type: "agent" as const,
      name: node.data.name,
      agent_id: node.data.agentId,
      suggested_agent: node.data.suggestedAgent,
      input: node.data.role || originalStep?.input || "${user_input}",
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
