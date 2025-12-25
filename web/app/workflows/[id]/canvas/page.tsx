"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ReactFlow,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  type OnNodesChange,
  type NodeTypes,
  BackgroundVariant,
  Panel,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { TriggerNode, AgentNode, EndNode } from "@/components/workflows/canvas/nodes";
import { CanvasToolbar } from "@/components/workflows/canvas/canvas-toolbar";
import { CanvasStatusBar } from "@/components/workflows/canvas/canvas-status-bar";
import { NodeConfigPanel } from "@/components/workflows/canvas/node-config-panel";
import { CanvasPalette } from "@/components/workflows/canvas/canvas-palette";
import { CanvasExecutionPanel } from "@/components/workflows/canvas/canvas-execution-panel";
import { workflowToCanvas } from "@/lib/workflow-canvas";
import { useWorkflow, useUpdateWorkflow } from "@/lib/hooks/use-workflows";
import { useAgents, useCreateAgent } from "@/lib/hooks/use-agents";
import type { CanvasNode, CanvasEdge, AgentNodeData } from "@/lib/workflow-canvas/types";
import type { Agent, AgentCreate } from "@/types/agent";
import type { SuggestedAgent } from "@/types/workflow";
import { Loader2 } from "lucide-react";

// Custom node types
const nodeTypes: NodeTypes = {
  trigger: TriggerNode,
  agent: AgentNode,
  end: EndNode,
};

function CanvasEditor() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;
  const reactFlowInstance = useReactFlow();

  const { data: workflow, isLoading: isLoadingWorkflow, error } = useWorkflow(workflowId);
  const { data: agentsData } = useAgents();
  const updateWorkflow = useUpdateWorkflow();
  const createAgent = useCreateAgent();

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isPaletteOpen, setIsPaletteOpen] = useState(true);
  const [isExecutionPanelOpen, setIsExecutionPanelOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

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

  // Close config panel
  const handleClosePanel = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  // Handle nodes change (mark as dirty)
  const handleNodesChange: OnNodesChange<CanvasNode> = useCallback(
    (changes) => {
      onNodesChange(changes);
      // Mark as having unsaved changes (but not for selection changes)
      const hasRealChanges = changes.some(
        (c) => c.type !== "select" && c.type !== "position"
      );
      if (hasRealChanges) {
        setHasUnsavedChanges(true);
      }
    },
    [onNodesChange]
  );

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    reactFlowInstance.zoomIn();
  }, [reactFlowInstance]);

  const handleZoomOut = useCallback(() => {
    reactFlowInstance.zoomOut();
  }, [reactFlowInstance]);

  const handleFitView = useCallback(() => {
    reactFlowInstance.fitView({ padding: 0.2 });
  }, [reactFlowInstance]);

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
                  agentGoal: suggestion.goal, // Use the suggestion's goal
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
        // Continue with other agents even if one fails
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
                agentGoal: agent.description, // Use description as goal summary
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
      const agentNodes = nodes
        .filter((n): n is CanvasNode & { data: AgentNodeData } => n.type === "agent")
        .sort((a, b) => a.position.y - b.position.y);

      const steps = agentNodes.map((node) => {
        const originalStep = workflow.definition?.steps?.find(
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

  return (
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
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={handleNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            nodeTypes={nodeTypes}
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
                  case "end":
                    return "hsl(var(--muted-foreground))";
                  default:
                    return "hsl(var(--muted))";
                }
              }}
              className="!bg-card !border-border"
              maskColor="hsl(var(--background) / 0.8)"
              position="bottom-left"
            />

            {/* Zoom controls */}
            <Panel position="bottom-right" className="flex gap-1 mb-12 mr-2">
              <button
                onClick={handleZoomIn}
                className="h-8 w-8 flex items-center justify-center rounded border border-border bg-card hover:bg-accent transition-colors"
                title="Zoom in"
              >
                <span className="text-lg font-medium">+</span>
              </button>
              <button
                onClick={handleZoomOut}
                className="h-8 w-8 flex items-center justify-center rounded border border-border bg-card hover:bg-accent transition-colors"
                title="Zoom out"
              >
                <span className="text-lg font-medium">-</span>
              </button>
              <button
                onClick={handleFitView}
                className="h-8 w-8 flex items-center justify-center rounded border border-border bg-card hover:bg-accent transition-colors text-xs"
                title="Fit view"
              >
                Fit
              </button>
            </Panel>
          </ReactFlow>
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
  );
}

export default function CanvasPage() {
  return (
    <ReactFlowProvider>
      <CanvasEditor />
    </ReactFlowProvider>
  );
}
