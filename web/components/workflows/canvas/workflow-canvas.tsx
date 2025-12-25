"use client";

import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type OnNodesChange,
  type OnEdgesChange,
  type NodeTypes,
  BackgroundVariant,
  Panel,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { TriggerNode, AgentNode, EndNode } from "./nodes";
import { workflowToCanvas } from "@/lib/workflow-canvas";
import type { CanvasNode, CanvasEdge } from "@/lib/workflow-canvas/types";
import type { WorkflowDefinition, WorkflowTrigger } from "@/types/workflow";
import type { Agent } from "@/types/agent";
import { Layers, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";

// Custom node types
const nodeTypes: NodeTypes = {
  trigger: TriggerNode,
  agent: AgentNode,
  end: EndNode,
};

interface WorkflowCanvasProps {
  definition: WorkflowDefinition;
  trigger?: WorkflowTrigger;
  agents?: Agent[];
  connectedMcps?: string[];
  baseWebhookUrl?: string;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
  readOnly?: boolean;
}

export function WorkflowCanvas({
  definition,
  trigger,
  agents,
  connectedMcps,
  baseWebhookUrl,
  onNodeClick,
  className = "",
  readOnly = true,
}: WorkflowCanvasProps) {
  // Convert workflow definition to canvas format
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    return workflowToCanvas(definition, trigger, {
      agents,
      connectedMcps,
      baseWebhookUrl,
    });
  }, [definition, trigger, agents, connectedMcps, baseWebhookUrl]);

  // Node and edge state
  const [nodes, , onNodesChange] = useNodesState<CanvasNode>(
    initialNodes as CanvasNode[]
  );
  const [edges, , onEdgesChange] = useEdgesState<CanvasEdge>(
    initialEdges as CanvasEdge[]
  );

  // Handle node click
  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: CanvasNode) => {
      if (onNodeClick) {
        onNodeClick(node.id);
      }
    },
    [onNodeClick]
  );

  // Disable editing in read-only mode
  const handleNodesChange: OnNodesChange<CanvasNode> = useCallback(
    (changes) => {
      if (!readOnly) {
        onNodesChange(changes);
      }
    },
    [readOnly, onNodesChange]
  );

  const handleEdgesChange: OnEdgesChange<CanvasEdge> = useCallback(
    (changes) => {
      if (!readOnly) {
        onEdgesChange(changes);
      }
    },
    [readOnly, onEdgesChange]
  );

  return (
    <div className={`h-full w-full ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{
          padding: 0.2,
          maxZoom: 1.5,
        }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={!readOnly}
        nodesConnectable={!readOnly}
        elementsSelectable={true}
        panOnDrag={true}
        zoomOnScroll={true}
        className="bg-background"
      >
        {/* Background pattern */}
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="hsl(var(--muted-foreground) / 0.2)"
        />

        {/* Zoom controls */}
        <Controls
          showZoom={false}
          showFitView={false}
          showInteractive={false}
          className="!bg-transparent !shadow-none"
        />

        {/* Custom control panel */}
        <Panel position="bottom-right" className="flex gap-1">
          <Button variant="outline" size="icon" className="h-8 w-8 bg-card">
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8 bg-card">
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8 bg-card">
            <Maximize2 className="h-4 w-4" />
          </Button>
        </Panel>

        {/* Info panel */}
        <Panel position="top-left" className="flex items-center gap-2 text-xs text-muted-foreground">
          <Layers className="h-4 w-4" />
          <span>{definition.steps.length} steps</span>
        </Panel>

        {/* Minimap */}
        <MiniMap
          nodeStrokeWidth={3}
          nodeColor={(node) => {
            switch (node.type) {
              case "trigger":
                return "hsl(var(--primary))";
              case "agent":
                return "hsl(270, 60%, 60%)";
              case "end":
                return "hsl(var(--muted-foreground))";
              default:
                return "hsl(var(--muted))";
            }
          }}
          className="!bg-card !border-border"
          maskColor="hsl(var(--background) / 0.8)"
        />
      </ReactFlow>
    </div>
  );
}
