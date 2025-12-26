import dagre from "dagre";
import type { CanvasNode, CanvasEdge } from "./types";

// Node dimensions
const NODE_WIDTH = 280;
const NODE_HEIGHT = 100;
const TRIGGER_NODE_HEIGHT = 80;
const END_NODE_HEIGHT = 60;

interface LayoutOptions {
  direction?: "TB" | "LR"; // Top-to-bottom or Left-to-right
  nodeSpacing?: number;
  rankSpacing?: number;
}

/**
 * Apply dagre auto-layout to canvas nodes and edges
 * Returns new nodes with calculated positions
 */
export function applyAutoLayout(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  options: LayoutOptions = {}
): CanvasNode[] {
  const {
    direction = "TB",
    nodeSpacing = 50,
    rankSpacing = 80,
  } = options;

  // Create dagre graph
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: nodeSpacing,
    ranksep: rankSpacing,
    marginx: 50,
    marginy: 50,
  });

  // Add nodes to dagre graph
  nodes.forEach((node) => {
    const height = getNodeHeight(node);
    dagreGraph.setNode(node.id, {
      width: NODE_WIDTH,
      height,
    });
  });

  // Add edges to dagre graph
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Calculate layout
  dagre.layout(dagreGraph);

  // Apply calculated positions to nodes
  return nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    const height = getNodeHeight(node);

    return {
      ...node,
      position: {
        // Center the node
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - height / 2,
      },
    };
  });
}

// Height for conditional and parallel nodes (slightly taller to show branches)
const CONDITIONAL_NODE_HEIGHT = 140;
const PARALLEL_NODE_HEIGHT = 160;

/**
 * Get node height based on type
 */
function getNodeHeight(node: CanvasNode): number {
  switch (node.type) {
    case "trigger":
      return TRIGGER_NODE_HEIGHT;
    case "end":
      return END_NODE_HEIGHT;
    case "conditional":
      return CONDITIONAL_NODE_HEIGHT;
    case "parallel":
      return PARALLEL_NODE_HEIGHT;
    case "agent":
    default:
      return NODE_HEIGHT;
  }
}

interface EdgeOptions {
  animated?: boolean;
  label?: string;
}

/**
 * Create an edge between two nodes
 */
export function createEdge(
  sourceId: string,
  targetId: string,
  options: EdgeOptions | boolean = false
): CanvasEdge {
  // Handle backwards compatibility with boolean animated param
  const opts: EdgeOptions = typeof options === "boolean" ? { animated: options } : options;

  return {
    id: `${sourceId}-${targetId}${opts.label ? `-${opts.label}` : ""}`,
    source: sourceId,
    target: targetId,
    type: "labeled", // Use custom labeled edge type with bezier curves
    animated: opts.animated ?? false,
    data: {
      label: opts.label || "",
    },
    style: {
      strokeWidth: 2,
      stroke: "hsl(var(--muted-foreground))",
    },
    markerEnd: {
      type: "arrowclosed" as const,
      width: 16,
      height: 16,
      color: "hsl(var(--muted-foreground))",
    },
  };
}
