"use client";

import { useState, useCallback, useMemo, useEffect, useRef, DragEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ReactFlow,
  Background,
  MiniMap,
  Controls,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  addEdge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
  type NodeTypes,
  type EdgeTypes,
  type Connection,
  BackgroundVariant,
  Panel,
  MarkerType,
  ConnectionMode,
  ConnectionLineType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { TriggerNode, AgentNode, ConditionalNode, ParallelNode, EndNode } from "@/components/workflows/canvas/nodes";
import { LabeledEdge } from "@/components/workflows/canvas/edges";
import { CanvasContext } from "@/components/workflows/canvas/canvas-context";
import { CanvasToolbar } from "@/components/workflows/canvas/canvas-toolbar";
import { CanvasStatusBar } from "@/components/workflows/canvas/canvas-status-bar";
import { NodeConfigPanel } from "@/components/workflows/canvas/node-config-panel";
import { CanvasPalette } from "@/components/workflows/canvas/canvas-palette";
import { CanvasExecutionPanel } from "@/components/workflows/canvas/canvas-execution-panel";
import { workflowToCanvas } from "@/lib/workflow-canvas";
import { useWorkflow, useUpdateWorkflow } from "@/lib/hooks/use-workflows";
import { useAgents, useCreateAgent } from "@/lib/hooks/use-agents";
import type { CanvasNode, CanvasEdge, AgentNodeData, ConditionalNodeData, ParallelNodeData } from "@/lib/workflow-canvas/types";
import type { Agent, AgentCreate } from "@/types/agent";
import type { SuggestedAgent } from "@/types/workflow";
import { Loader2, Trash2 } from "lucide-react";

// Custom node types
const nodeTypes: NodeTypes = {
  trigger: TriggerNode,
  agent: AgentNode,
  conditional: ConditionalNode,
  parallel: ParallelNode,
  end: EndNode,
};

// Custom edge types
const edgeTypes: EdgeTypes = {
  labeled: LabeledEdge,
};

// Default edge options for better visuals - using bezier for smooth flowing curves
const defaultEdgeOptions = {
  type: "default", // "default" = bezier curves (smooth flowing lines)
  animated: false,
  style: { strokeWidth: 2, stroke: "hsl(var(--muted-foreground))" },
  markerEnd: {
    type: MarkerType.ArrowClosed,
    width: 16,
    height: 16,
    color: "hsl(var(--muted-foreground))",
  },
};

// Connection line style when dragging
const connectionLineStyle = {
  strokeWidth: 2,
  stroke: "hsl(var(--primary))",
};

function CanvasEditor() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;
  const reactFlowInstance = useReactFlow();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  const { data: workflow, isLoading: isLoadingWorkflow, error } = useWorkflow(workflowId);
  const { data: agentsData } = useAgents();
  const updateWorkflow = useUpdateWorkflow();
  const createAgent = useCreateAgent();

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isPaletteOpen, setIsPaletteOpen] = useState(true);
  const [isExecutionPanelOpen, setIsExecutionPanelOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  // Convert workflow definition to canvas format
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!workflow?.definition) {
      return { nodes: [], edges: [] };
    }
    return workflowToCanvas(workflow.definition, undefined, {
      agents: agentsData?.agents,
    });
  }, [workflow, agentsData]);

  // Node and edge state
  const [nodes, setNodes, onNodesChange] = useNodesState<CanvasNode>(
    initialNodes as CanvasNode[]
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState<CanvasEdge>(
    initialEdges as CanvasEdge[]
  );

  // Update nodes when workflow or agents change
  useEffect(() => {
    if (initialNodes.length > 0) {
      setNodes(initialNodes as CanvasNode[]);
      setEdges(initialEdges as CanvasEdge[]);
    }
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  // Find selected node
  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return nodes.find((n) => n.id === selectedNodeId) || null;
  }, [nodes, selectedNodeId]);

  // Get selected agent info for execution panel
  const selectedAgentInfo = useMemo(() => {
    if (!selectedNode || selectedNode.type !== "agent") return null;
    const data = selectedNode.data as AgentNodeData;
    if (data.status !== "ready" || !data.agentId) return null;
    return {
      id: data.agentId,
      name: data.agentName || data.name,
    };
  }, [selectedNode]);

  // Count draft nodes
  const draftCount = useMemo(() => {
    return nodes.filter(
      (n) => n.type === "agent" && (n.data as AgentNodeData).status === "draft"
    ).length;
  }, [nodes]);

  // Get all draft agents for batch creation
  const draftAgents = useMemo(() => {
    return nodes
      .filter(
        (n) =>
          n.type === "agent" &&
          (n.data as AgentNodeData).status === "draft" &&
          (n.data as AgentNodeData).suggestedAgent
      )
      .map((n) => ({
        nodeId: n.id,
        suggestion: (n.data as AgentNodeData).suggestedAgent!,
      }));
  }, [nodes]);

  // Handle node click
  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: CanvasNode) => {
      setSelectedNodeId(node.id);
    },
    []
  );

  // Handle pane click (deselect)
  const handlePaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  // Close config panel
  const handleClosePanel = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  // Handle nodes change (track all changes including position)
  const handleNodesChange: OnNodesChange<CanvasNode> = useCallback(
    (changes) => {
      onNodesChange(changes);
      // Track any change as unsaved (including position changes now!)
      const hasRealChanges = changes.some((c) => c.type !== "select");
      if (hasRealChanges) {
        setHasUnsavedChanges(true);
      }
    },
    [onNodesChange]
  );

  // Handle edges change
  const handleEdgesChange: OnEdgesChange<CanvasEdge> = useCallback(
    (changes) => {
      onEdgesChange(changes);
      // Mark as having unsaved changes
      const hasRealChanges = changes.some((c) => c.type !== "select");
      if (hasRealChanges) {
        setHasUnsavedChanges(true);
      }
    },
    [onEdgesChange]
  );

  // Handle new connections (drag from handle to handle)
  const handleConnect: OnConnect = useCallback(
    (connection: Connection) => {
      // Don't allow self-connections
      if (connection.source === connection.target) return;

      // Add the new edge with styling - using bezier for smooth curves
      const newEdge: CanvasEdge = {
        id: `edge-${connection.source}-${connection.target}`,
        source: connection.source!,
        target: connection.target!,
        sourceHandle: connection.sourceHandle,
        targetHandle: connection.targetHandle,
        type: "labeled",
        animated: false,
        style: { strokeWidth: 2, stroke: "hsl(var(--muted-foreground))" },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 16,
          height: 16,
          color: "hsl(var(--muted-foreground))",
        },
        data: { label: "" },
      };

      setEdges((eds) => addEdge(newEdge, eds));
      setHasUnsavedChanges(true);
    },
    [setEdges]
  );

  // Handle drag over (from palette)
  const handleDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    setIsDraggingOver(true);
  }, []);

  // Handle drag leave
  const handleDragLeave = useCallback(() => {
    setIsDraggingOver(false);
  }, []);

  // Handle drop (from palette)
  const handleDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDraggingOver(false);

      const agentData = event.dataTransfer.getData("application/agent");
      if (!agentData) return;

      try {
        const agent: Agent = JSON.parse(agentData);

        // Get the drop position in flow coordinates
        const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
        if (!reactFlowBounds) return;

        const position = reactFlowInstance.screenToFlowPosition({
          x: event.clientX - reactFlowBounds.left,
          y: event.clientY - reactFlowBounds.top,
        });

        // Create a unique step ID
        const stepId = `step-${Date.now()}`;

        // Create a new agent node
        const newNode: CanvasNode = {
          id: stepId,
          type: "agent",
          position,
          data: {
            type: "agent",
            stepId,
            name: agent.name,
            agentId: agent.id,
            agentName: agent.name,
            agentGoal: agent.description,
            status: "ready",
          } as AgentNodeData,
        };

        setNodes((nds) => [...nds, newNode]);
        setHasUnsavedChanges(true);

        // Select the new node
        setSelectedNodeId(stepId);
      } catch (e) {
        console.error("Failed to parse dropped agent:", e);
      }
    },
    [reactFlowInstance, setNodes]
  );

  // Keyboard shortcuts disabled for now to prevent accidental deletions while typing
  // TODO: Re-enable with proper focus management (only when canvas is focused, not input fields)

  // Delete selected node
  const handleDeleteNode = useCallback(() => {
    if (!selectedNodeId) return;
    const node = nodes.find((n) => n.id === selectedNodeId);
    if (node && node.type !== "trigger" && node.type !== "end") {
      setNodes((nds) => nds.filter((n) => n.id !== selectedNodeId));
      setEdges((eds) =>
        eds.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId)
      );
      setSelectedNodeId(null);
      setHasUnsavedChanges(true);
    }
  }, [selectedNodeId, nodes, setNodes, setEdges]);

  // Create agent from suggestion
  const handleCreateAgent = useCallback(
    async (nodeId: string, suggestion: SuggestedAgent) => {
      const agentId = suggestion.name
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^a-z0-9-]/g, "");

      const agentData: AgentCreate = {
        id: agentId,
        name: suggestion.name,
        description: suggestion.description || `${suggestion.name} agent`,
        agent_type: "SimpleAgent",
        role: {
          title: suggestion.name,
          expertise: [],
          personality: ["helpful", "professional"],
          communication_style: "Clear and concise",
        },
        goal: {
          objective: suggestion.goal,
          success_criteria: ["Task completed successfully"],
          constraints: [],
        },
        instructions: {
          steps: ["Analyze the input", "Execute the task", "Return results"],
          rules: ["Be accurate", "Be concise"],
          prohibited_actions: [],
          output_format: "Natural language response",
        },
        examples: [],
        llm_config: {
          provider: "openai",
          model: suggestion.model || "gpt-4o",
          temperature: 0.7,
        },
        tools: suggestion.suggested_tools?.map((id) => ({ tool_id: id })) || [],
        safety: {
          level: "standard",
          blocked_topics: [],
          blocked_patterns: [],
        },
      };

      try {
        const createdAgent = await createAgent.mutateAsync(agentData);

        // Update the node to show as ready
        setNodes((nds) =>
          nds.map((n) => {
            if (n.id === nodeId && n.type === "agent") {
              return {
                ...n,
                data: {
                  ...n.data,
                  agentId: createdAgent.id,
                  agentName: createdAgent.name,
                  agentGoal: suggestion.goal,
                  status: "ready" as const,
                  suggestedAgent: undefined,
                },
              };
            }
            return n;
          })
        );

        setHasUnsavedChanges(true);
        return createdAgent;
      } catch (error) {
        console.error("Failed to create agent:", error);
        throw error;
      }
    },
    [createAgent, setNodes]
  );

  // Batch create all draft agents
  const handleCreateAllAgents = useCallback(async () => {
    for (const { nodeId, suggestion } of draftAgents) {
      try {
        await handleCreateAgent(nodeId, suggestion);
      } catch (error) {
        console.error(`Failed to create agent for node ${nodeId}:`, error);
      }
    }
  }, [draftAgents, handleCreateAgent]);

  // Assign existing agent to node
  const handleAssignAgent = useCallback(
    (nodeId: string, agent: Agent) => {
      setNodes((nds) =>
        nds.map((n) => {
          if (n.id === nodeId && n.type === "agent") {
            return {
              ...n,
              data: {
                ...n.data,
                agentId: agent.id,
                agentName: agent.name,
                agentGoal: agent.description,
                status: "ready" as const,
                suggestedAgent: undefined,
              },
            };
          }
          return n;
        })
      );
      setHasUnsavedChanges(true);
    },
    [setNodes]
  );

  // Save workflow
  const handleSave = useCallback(async () => {
    if (!workflow) return;

    setIsSaving(true);
    try {
      // Convert canvas back to workflow definition
      // Filter out trigger and end nodes, keep agent/conditional/parallel
      const stepNodes = nodes
        .filter((n): n is CanvasNode =>
          n.type === "agent" || n.type === "conditional" || n.type === "parallel"
        )
        .sort((a, b) => a.position.y - b.position.y);

      const steps = stepNodes.map((node) => {
        if (node.type === "agent") {
          const data = node.data as AgentNodeData;
          const originalStep = workflow.definition?.steps?.find(
            (s) => s.id === data.stepId
          );
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
        }
        // Handle other step types (conditional, parallel)
        const nodeData = node.data as ConditionalNodeData | ParallelNodeData;
        const originalStep = workflow.definition?.steps?.find(
          (s) => s.id === nodeData.stepId
        );
        return originalStep || {
          id: nodeData.stepId,
          type: node.type as "conditional" | "parallel",
          timeout: 120,
          retries: 0,
          on_error: "fail" as const,
        };
      });

      await updateWorkflow.mutateAsync({
        workflowId,
        request: {
          definition: {
            ...workflow.definition,
            steps,
            entry_step: steps[0]?.id,
          },
        },
      });

      setHasUnsavedChanges(false);
    } catch (error) {
      console.error("Failed to save workflow:", error);
    } finally {
      setIsSaving(false);
    }
  }, [workflow, nodes, workflowId, updateWorkflow]);

  // Navigate back
  const handleBack = useCallback(() => {
    if (hasUnsavedChanges) {
      if (confirm("You have unsaved changes. Are you sure you want to leave?")) {
        router.push(`/workflows/${workflowId}`);
      }
    } else {
      router.push(`/workflows/${workflowId}`);
    }
  }, [router, workflowId, hasUnsavedChanges]);

  // Mark as having unsaved changes (for edge label edits)
  const markUnsaved = useCallback(() => {
    setHasUnsavedChanges(true);
  }, []);

  // Context value for edge components
  const canvasContextValue = useMemo(() => ({
    markUnsaved,
  }), [markUnsaved]);

  if (isLoadingWorkflow) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !workflow) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-background">
        <div className="text-center">
          <h2 className="text-lg font-semibold">Workflow not found</h2>
          <p className="mt-2 text-muted-foreground">
            The workflow you&apos;re looking for doesn&apos;t exist.
          </p>
        </div>
      </div>
    );
  }

  const canDeleteNode = selectedNode && selectedNode.type !== "trigger" && selectedNode.type !== "end";

  return (
    <CanvasContext.Provider value={canvasContextValue}>
      <div className="h-full w-full flex flex-col bg-background overflow-hidden">
        {/* Top Toolbar */}
        <CanvasToolbar
        workflowName={workflow.name}
        hasUnsavedChanges={hasUnsavedChanges}
        isSaving={isSaving}
        canRun={draftCount === 0}
        isExecutionPanelOpen={isExecutionPanelOpen}
        onBack={handleBack}
        onSave={handleSave}
        onToggleExecution={() => setIsExecutionPanelOpen(!isExecutionPanelOpen)}
      />

      {/* Main Canvas Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Palette */}
        <CanvasPalette
          isOpen={isPaletteOpen}
          onToggle={() => setIsPaletteOpen(!isPaletteOpen)}
          agents={agentsData?.agents || []}
          onAgentCreated={() => {
            // Agent created - React Query will auto-refetch agents list
          }}
        />

        {/* Canvas */}
        <div
          ref={reactFlowWrapper}
          className={`flex-1 relative transition-all ${
            isDraggingOver ? "ring-2 ring-primary ring-inset bg-primary/5" : ""
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={handleNodesChange}
            onEdgesChange={handleEdgesChange}
            onConnect={handleConnect}
            onNodeClick={handleNodeClick}
            onPaneClick={handlePaneClick}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
            connectionLineStyle={connectionLineStyle}
            connectionLineType={ConnectionLineType.Bezier}
            connectionMode={ConnectionMode.Loose}
            fitView
            fitViewOptions={{
              padding: 0.2,
              maxZoom: 1.5,
            }}
            proOptions={{ hideAttribution: true }}
            nodesDraggable={true}
            nodesConnectable={true}
            elementsSelectable={true}
            panOnDrag={true}
            zoomOnScroll={true}
            selectNodesOnDrag={false}
            snapToGrid={true}
            snapGrid={[15, 15]}
            className="bg-background"
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={20}
              size={1}
              color="hsl(var(--muted-foreground) / 0.2)"
            />

            {/* Minimap in bottom-left */}
            <MiniMap
              nodeStrokeWidth={3}
              nodeColor={(node) => {
                switch (node.type) {
                  case "trigger":
                    return "hsl(var(--primary))";
                  case "agent":
                    return "hsl(270, 60%, 60%)";
                  case "conditional":
                    return "hsl(210, 80%, 55%)";
                  case "parallel":
                    return "hsl(280, 60%, 60%)";
                  case "end":
                    return "hsl(var(--muted-foreground))";
                  default:
                    return "hsl(var(--muted))";
                }
              }}
              className="!bg-card !border-border"
              maskColor="hsl(var(--background) / 0.8)"
              position="bottom-left"
              pannable
              zoomable
            />

            {/* Controls (zoom in/out/fit) */}
            <Controls
              showInteractive={false}
              className="!bg-card !border-border !shadow-sm"
              position="bottom-right"
            />

            {/* Delete button when node selected */}
            {canDeleteNode && (
              <Panel position="top-right" className="mr-2 mt-2">
                <button
                  onClick={handleDeleteNode}
                  className="flex items-center gap-2 px-3 py-2 rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors text-sm font-medium"
                  title="Delete node"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete
                </button>
              </Panel>
            )}
          </ReactFlow>

          {/* Drop zone indicator */}
          {isDraggingOver && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
              <div className="bg-primary/10 border-2 border-dashed border-primary rounded-lg p-8">
                <p className="text-primary font-medium">Drop agent here</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Config Panel */}
        {selectedNode && !isExecutionPanelOpen && (
          <NodeConfigPanel
            node={selectedNode}
            agents={agentsData?.agents || []}
            onClose={handleClosePanel}
            onCreateAgent={handleCreateAgent}
            onAssignAgent={handleAssignAgent}
          />
        )}

        {/* Right Execution Panel */}
        {isExecutionPanelOpen && (
          <CanvasExecutionPanel
            workflowId={workflowId}
            workflowName={workflow.name}
            selectedAgentId={selectedAgentInfo?.id}
            selectedAgentName={selectedAgentInfo?.name}
            canRun={draftCount === 0}
            onClose={() => setIsExecutionPanelOpen(false)}
          />
        )}
        </div>

        {/* Bottom Status Bar */}
        <CanvasStatusBar
          nodeCount={nodes.length}
          draftCount={draftCount}
          draftAgents={draftAgents}
          onCreateAll={handleCreateAllAgents}
          isCreating={createAgent.isPending}
        />
      </div>
    </CanvasContext.Provider>
  );
}

export default function CanvasPage() {
  return (
    <ReactFlowProvider>
      <CanvasEditor />
    </ReactFlowProvider>
  );
}
