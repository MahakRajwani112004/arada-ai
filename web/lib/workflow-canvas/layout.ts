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

/**
 * Get node height based on type
 */
function getNodeHeight(node: CanvasNode): number {
  switch (node.type) {
    case "trigger":
      return TRIGGER_NODE_HEIGHT;
    case "end":
      return END_NODE_HEIGHT;
    case "agent":
    default:
      return NODE_HEIGHT;
  }
}

/**
 * Create an edge between two nodes
 */
export function createEdge(
  sourceId: string,
  targetId: string,
  animated = false
): CanvasEdge {
  return {
    id: `${sourceId}-${targetId}`,
    source: sourceId,
    target: targetId,
    type: "smoothstep",
    animated,
    style: {
      strokeWidth: 2,
    },
  };
}
