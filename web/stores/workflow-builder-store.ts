import { create } from "zustand";
import {
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  XYPosition,
} from "@xyflow/react";
import { nanoid } from "nanoid";
import {
  WorkflowNodeData,
  WorkflowDefinition,
  WorkflowStep,
  StepType,
  DEFAULT_STEP_VALUES,
  nodeDataToStep,
  stepToNodeData,
} from "@/types/workflow";

interface WorkflowBuilderState {
  // Workflow metadata
  workflowId: string;
  workflowName: string;
  workflowDescription: string;
  entryStep: string | null;
  context: Record<string, unknown>;

  // React Flow state
  nodes: Node<WorkflowNodeData>[];
  edges: Edge[];

  // UI state
  selectedNodeId: string | null;
  isDirty: boolean;
  validationErrors: string[];

  // Actions
  setWorkflowMetadata: (id: string, name: string, description: string) => void;
  setEntryStep: (stepId: string | null) => void;
  setContext: (context: Record<string, unknown>) => void;
  addNode: (type: StepType, position: XYPosition) => string;
  updateNode: (nodeId: string, data: Partial<WorkflowNodeData>) => void;
  removeNode: (nodeId: string) => void;
  setSelectedNode: (nodeId: string | null) => void;
  setNodes: (nodes: Node<WorkflowNodeData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: OnNodesChange<Node<WorkflowNodeData>>;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  setValidationErrors: (errors: string[]) => void;
  markClean: () => void;

  // Conversion
  toWorkflowDefinition: () => WorkflowDefinition;
  fromWorkflowDefinition: (def: WorkflowDefinition) => void;

  // Reset
  reset: () => void;
}

const initialState = {
  workflowId: "",
  workflowName: "",
  workflowDescription: "",
  entryStep: null,
  context: {},
  nodes: [],
  edges: [],
  selectedNodeId: null,
  isDirty: false,
  validationErrors: [],
};

export const useWorkflowBuilderStore = create<WorkflowBuilderState>((set, get) => ({
  ...initialState,

  setWorkflowMetadata: (id: string, name: string, description: string) => {
    set({
      workflowId: id,
      workflowName: name,
      workflowDescription: description,
      isDirty: true,
    });
  },

  setEntryStep: (stepId: string | null) => {
    set({ entryStep: stepId, isDirty: true });
  },

  setContext: (context: Record<string, unknown>) => {
    set({ context, isDirty: true });
  },

  addNode: (type: StepType, position: XYPosition) => {
    const id = `${type}-${nanoid(6)}`;
    const defaults = DEFAULT_STEP_VALUES[type];

    const newNode: Node<WorkflowNodeData> = {
      id,
      type: `${type}Node`,
      position,
      data: {
        ...defaults,
        stepType: type,
        label: `${type.charAt(0).toUpperCase() + type.slice(1)} Step`,
      } as WorkflowNodeData,
    };

    set((state) => ({
      nodes: [...state.nodes, newNode],
      selectedNodeId: id,
      isDirty: true,
      // Set as entry step if it's the first node
      entryStep: state.nodes.length === 0 ? id : state.entryStep,
    }));

    return id;
  },

  updateNode: (nodeId: string, data: Partial<WorkflowNodeData>) => {
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...data } }
          : node
      ),
      isDirty: true,
    }));
  },

  removeNode: (nodeId: string) => {
    set((state) => {
      const newNodes = state.nodes.filter((node) => node.id !== nodeId);
      const newEdges = state.edges.filter(
        (edge) => edge.source !== nodeId && edge.target !== nodeId
      );

      return {
        nodes: newNodes,
        edges: newEdges,
        selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
        entryStep: state.entryStep === nodeId ? (newNodes[0]?.id || null) : state.entryStep,
        isDirty: true,
      };
    });
  },

  setSelectedNode: (nodeId: string | null) => {
    set({ selectedNodeId: nodeId });
  },

  setNodes: (nodes: Node<WorkflowNodeData>[]) => {
    set({ nodes, isDirty: true });
  },

  setEdges: (edges: Edge[]) => {
    set({ edges, isDirty: true });
  },

  onNodesChange: (changes) => {
    set((state) => ({
      nodes: applyNodeChanges(changes, state.nodes),
      isDirty: true,
    }));
  },

  onEdgesChange: (changes) => {
    set((state) => ({
      edges: applyEdgeChanges(changes, state.edges),
      isDirty: true,
    }));
  },

  onConnect: (connection) => {
    set((state) => ({
      edges: addEdge(
        {
          ...connection,
          type: "smoothstep",
          animated: true,
        },
        state.edges
      ),
      isDirty: true,
    }));
  },

  setValidationErrors: (errors: string[]) => {
    set({ validationErrors: errors });
  },

  markClean: () => {
    set({ isDirty: false });
  },

  toWorkflowDefinition: () => {
    const state = get();

    // Convert nodes to steps, maintaining order based on edges
    const steps: WorkflowStep[] = [];
    const visited = new Set<string>();

    // Build adjacency list from edges
    const adjacency = new Map<string, string[]>();
    state.edges.forEach((edge) => {
      if (!adjacency.has(edge.source)) {
        adjacency.set(edge.source, []);
      }
      adjacency.get(edge.source)!.push(edge.target);
    });

    // DFS to get ordered steps (or just iterate if no edges)
    const processNode = (nodeId: string) => {
      if (visited.has(nodeId)) return;
      visited.add(nodeId);

      const node = state.nodes.find((n) => n.id === nodeId);
      if (node) {
        steps.push(nodeDataToStep(node.id, node.data));
      }

      const children = adjacency.get(nodeId) || [];
      children.forEach(processNode);
    };

    // Start from entry step or first node
    const startNodeId = state.entryStep || state.nodes[0]?.id;
    if (startNodeId) {
      processNode(startNodeId);
    }

    // Add any unvisited nodes (disconnected)
    state.nodes.forEach((node) => {
      if (!visited.has(node.id)) {
        steps.push(nodeDataToStep(node.id, node.data));
      }
    });

    return {
      id: state.workflowId,
      name: state.workflowName || undefined,
      description: state.workflowDescription || undefined,
      steps,
      entry_step: state.entryStep || undefined,
      context: Object.keys(state.context).length > 0 ? state.context : undefined,
    };
  },

  fromWorkflowDefinition: (def: WorkflowDefinition) => {
    const nodes: Node<WorkflowNodeData>[] = [];
    const edges: Edge[] = [];

    // Position nodes in a grid
    const SPACING_X = 250;
    const SPACING_Y = 150;
    const COLUMNS = 3;

    def.steps.forEach((step, index) => {
      const col = index % COLUMNS;
      const row = Math.floor(index / COLUMNS);

      nodes.push({
        id: step.id,
        type: `${step.type}Node`,
        position: {
          x: 100 + col * SPACING_X,
          y: 100 + row * SPACING_Y,
        },
        data: stepToNodeData(step),
      });
    });

    // Create edges based on step order (simple sequential)
    for (let i = 0; i < def.steps.length - 1; i++) {
      edges.push({
        id: `edge-${def.steps[i].id}-${def.steps[i + 1].id}`,
        source: def.steps[i].id,
        target: def.steps[i + 1].id,
        type: "smoothstep",
        animated: true,
      });
    }

    // Add conditional branch edges
    def.steps.forEach((step) => {
      if (step.type === "conditional" && step.conditional_branches) {
        Object.values(step.conditional_branches).forEach((targetId) => {
          if (!edges.find((e) => e.source === step.id && e.target === targetId)) {
            edges.push({
              id: `edge-${step.id}-${targetId}`,
              source: step.id,
              target: targetId,
              type: "smoothstep",
              animated: true,
              style: { strokeDasharray: "5,5" },
            });
          }
        });
        if (step.default) {
          if (!edges.find((e) => e.source === step.id && e.target === step.default)) {
            edges.push({
              id: `edge-${step.id}-${step.default}`,
              source: step.id,
              target: step.default,
              type: "smoothstep",
              animated: true,
              style: { strokeDasharray: "5,5" },
            });
          }
        }
      }
    });

    set({
      workflowId: def.id,
      workflowName: def.name || "",
      workflowDescription: def.description || "",
      entryStep: def.entry_step || def.steps[0]?.id || null,
      context: def.context || {},
      nodes,
      edges,
      selectedNodeId: null,
      isDirty: false,
      validationErrors: [],
    });
  },

  reset: () => {
    set(initialState);
  },
}));
