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
import { Loader2, Trash2, Sparkles, Wand2, Save, XCircle } from "lucide-react";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { generateAgentConfig } from "@/lib/api/agents";

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
  const [showLeaveDialog, setShowLeaveDialog] = useState(false);

  // AI Step Generation state
  const [showAIStepDialog, setShowAIStepDialog] = useState(false);
  const [aiStepName, setAIStepName] = useState("");
  const [aiStepPrompt, setAIStepPrompt] = useState("");
  const [isGeneratingStep, setIsGeneratingStep] = useState(false);

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

  // Track if we've initialized the canvas
  const hasInitialized = useRef(false);
  // Track if we're currently saving (to prevent false "unsaved" states)
  const isSavingRef = useRef(false);
  // Ref to hold save function for callbacks that need it before it's defined
  const saveWorkflowRef = useRef<() => Promise<void>>();

  // Initialize nodes only once when workflow first loads
  // Don't reset on subsequent agentsData refetches to preserve user changes
  useEffect(() => {
    if (initialNodes.length > 0 && !hasInitialized.current) {
      setNodes(initialNodes as CanvasNode[]);
      setEdges(initialEdges as CanvasEdge[]);
      hasInitialized.current = true;
    }
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  // Reset initialization flag when workflow ID changes
  useEffect(() => {
    hasInitialized.current = false;
  }, [workflowId]);

  // Update agent info on existing nodes when agentsData changes (without resetting canvas)
  useEffect(() => {
    if (!hasInitialized.current || !agentsData?.agents) return;

    setNodes((currentNodes) =>
      currentNodes.map((node) => {
        if (node.type === "agent") {
          const data = node.data as AgentNodeData;
          if (data.agentId) {
            const agent = agentsData.agents.find((a) => a.id === data.agentId);
            if (agent && (!data.agentName || data.agentName !== agent.name)) {
              return {
                ...node,
                data: {
                  ...data,
                  agentName: agent.name,
                  agentGoal: agent.description || data.agentGoal,
                },
              };
            }
          }
        }
        return node;
      })
    );
  }, [agentsData?.agents, setNodes]);

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
      // Don't track changes during save (prevents false "unsaved" after save completes)
      if (isSavingRef.current) return;
      // Only track user-initiated changes (position, remove, add), not internal ReactFlow updates
      const userChanges = changes.filter(
        (c) => c.type === "position" || c.type === "remove" || c.type === "add"
      );
      if (userChanges.length > 0) {
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

  // Open AI dialog to add a new step
  const handleAddStep = useCallback(() => {
    setAIStepName("");
    setAIStepPrompt("");
    setShowAIStepDialog(true);
  }, []);

  // Generate agent from AI and add to canvas
  const handleGenerateAIStep = useCallback(async () => {
    if (!aiStepName.trim()) return;

    setIsGeneratingStep(true);

    try {
      // Generate agent config from AI
      const generatedConfig = await generateAgentConfig({
        name: aiStepName.trim(),
        context: aiStepPrompt.trim() || undefined,
      });

      // Create the agent
      const agentId = aiStepName
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^a-z0-9-]/g, "");

      const agentData: AgentCreate = {
        id: agentId,
        name: aiStepName.trim(),
        description: generatedConfig.description || `${aiStepName} agent`,
        agent_type: "LLMAgent",
        role: generatedConfig.role,
        goal: generatedConfig.goal,
        instructions: generatedConfig.instructions ? {
          steps: generatedConfig.instructions.steps || [],
          rules: generatedConfig.instructions.rules || [],
          prohibited_actions: (generatedConfig.instructions as { prohibited?: string[] }).prohibited || [],
          output_format: generatedConfig.instructions.output_format || "",
        } : {
          steps: [],
          rules: [],
          prohibited_actions: [],
          output_format: "",
        },
        examples: generatedConfig.examples || [],
        llm_config: {
          provider: "openai",
          model: "gpt-4o",
          temperature: 0.7,
        },
        tools: [],
        safety: {
          level: "standard",
          blocked_topics: [],
          blocked_patterns: [],
        },
      };

      const createdAgent = await createAgent.mutateAsync(agentData);

      // Calculate position - place near center of current viewport
      const position = reactFlowInstance.screenToFlowPosition({
        x: window.innerWidth / 2,
        y: window.innerHeight / 2,
      });

      // Offset slightly based on existing nodes to avoid overlap
      const existingAgentNodes = nodes.filter((n) => n.type === "agent");
      const offset = existingAgentNodes.length * 20;

      const stepId = `step-${Date.now()}`;

      const newNode: CanvasNode = {
        id: stepId,
        type: "agent",
        position: {
          x: position.x + offset,
          y: position.y + offset,
        },
        data: {
          type: "agent",
          stepId,
          name: createdAgent.name,
          agentId: createdAgent.id,
          agentName: createdAgent.name,
          agentGoal: createdAgent.description,
          status: "ready",
        } as AgentNodeData,
      };

      setNodes((nds) => [...nds, newNode]);
      setHasUnsavedChanges(true);
      setSelectedNodeId(stepId);
      setShowAIStepDialog(false);
      setAIStepName("");
      setAIStepPrompt("");
    } catch (error) {
      console.error("Failed to generate AI step:", error);
    } finally {
      setIsGeneratingStep(false);
    }
  }, [aiStepName, aiStepPrompt, createAgent, reactFlowInstance, nodes, setNodes]);

  // Create agent from suggestion (or use existing if already created)
  const handleCreateAgent = useCallback(
    async (nodeId: string, suggestion: SuggestedAgent) => {
      const agentId = suggestion.name
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^a-z0-9-]/g, "");

      // Check if agent already exists
      const existingAgent = agentsData?.agents?.find(a => a.id === agentId);
      if (existingAgent) {
        // Agent already exists - use it directly
        setNodes((nds) =>
          nds.map((n) => {
            if (n.id === nodeId && n.type === "agent") {
              return {
                ...n,
                data: {
                  ...n.data,
                  agentId: existingAgent.id,
                  agentName: existingAgent.name,
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
        // Auto-save workflow after assigning agent
        setTimeout(() => saveWorkflowRef.current?.(), 100);
        return existingAgent;
      }

      // Determine agent type based on tools/MCPs
      // - If agent has tools or MCPs, use ToolAgent (can call tools)
      // - Otherwise, use LLMAgent (simple LLM call)
      const hasTools = (suggestion.suggested_tools?.length ?? 0) > 0;
      const hasMcps = (suggestion.required_mcps?.length ?? 0) > 0;
      const agentType = (hasTools || hasMcps) ? "ToolAgent" : "LLMAgent";

      const agentData: AgentCreate = {
        id: agentId,
        name: suggestion.name,
        description: suggestion.description || `${suggestion.name} agent`,
        agent_type: agentType,
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
        // Auto-save workflow after creating agent
        setTimeout(() => saveWorkflowRef.current?.(), 100);
        return createdAgent;
      } catch (error: unknown) {
        // Handle 409 Conflict - agent already exists (created between our check and create)
        const errorMessage = error instanceof Error ? error.message : String(error);
        if (errorMessage.includes("already exists") || errorMessage.includes("409")) {
          // Refetch agents and try to use the existing one
          const existingAgentNow = agentsData?.agents?.find(a => a.id === agentId);
          if (existingAgentNow) {
            setNodes((nds) =>
              nds.map((n) => {
                if (n.id === nodeId && n.type === "agent") {
                  return {
                    ...n,
                    data: {
                      ...n.data,
                      agentId: existingAgentNow.id,
                      agentName: existingAgentNow.name,
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
            // Auto-save workflow after using existing agent
            setTimeout(() => saveWorkflowRef.current?.(), 100);
            return existingAgentNow;
          }
        }
        console.error("Failed to create agent:", error);
        throw error;
      }
    },
    [createAgent, setNodes, agentsData]
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
      // Auto-save workflow after assigning agent
      setTimeout(() => saveWorkflowRef.current?.(), 100);
    },
    [setNodes]
  );

  // Save workflow
  const handleSave = useCallback(async () => {
    if (!workflow) return;

    setIsSaving(true);
    isSavingRef.current = true;
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

      // Build canvas layout to save node positions
      const canvasLayout = {
        positions: nodes.reduce((acc, node) => {
          acc[node.id] = { x: node.position.x, y: node.position.y };
          return acc;
        }, {} as Record<string, { x: number; y: number }>),
        savedAt: new Date().toISOString(),
      };

      await updateWorkflow.mutateAsync({
        workflowId,
        request: {
          definition: {
            ...workflow.definition,
            steps,
            entry_step: steps[0]?.id,
            context: {
              ...workflow.definition?.context,
              canvas_layout: canvasLayout,
            },
          },
        },
      });

      setHasUnsavedChanges(false);
    } catch (error) {
      console.error("Failed to save workflow:", error);
    } finally {
      setIsSaving(false);
      // Reset saving flag after a brief delay to allow ReactFlow to settle
      setTimeout(() => {
        isSavingRef.current = false;
      }, 500);
    }
  }, [workflow, nodes, workflowId, updateWorkflow]);

  // Keep the ref updated with the latest handleSave
  useEffect(() => {
    saveWorkflowRef.current = handleSave;
  }, [handleSave]);

  // Navigate back
  const handleBack = useCallback(() => {
    if (hasUnsavedChanges) {
      setShowLeaveDialog(true);
    } else {
      router.push(`/workflows/${workflowId}`);
    }
  }, [router, workflowId, hasUnsavedChanges]);

  // Confirm leave without saving (discard changes)
  const handleDiscardAndLeave = useCallback(() => {
    setShowLeaveDialog(false);
    router.push(`/workflows/${workflowId}`);
  }, [router, workflowId]);

  // Save and then leave
  const handleSaveAndLeave = useCallback(async () => {
    if (!workflow) return;

    setIsSaving(true);
    try {
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

      // Build canvas layout to save node positions
      const canvasLayout = {
        positions: nodes.reduce((acc, node) => {
          acc[node.id] = { x: node.position.x, y: node.position.y };
          return acc;
        }, {} as Record<string, { x: number; y: number }>),
        savedAt: new Date().toISOString(),
      };

      await updateWorkflow.mutateAsync({
        workflowId,
        request: {
          definition: {
            ...workflow.definition,
            steps,
            entry_step: steps[0]?.id,
            context: {
              ...workflow.definition?.context,
              canvas_layout: canvasLayout,
            },
          },
        },
      });

      setShowLeaveDialog(false);
      router.push(`/workflows/${workflowId}`);
    } catch (error) {
      console.error("Failed to save workflow:", error);
    } finally {
      setIsSaving(false);
    }
  }, [workflow, nodes, workflowId, updateWorkflow, router]);

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
          onAddStep={handleAddStep}
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

      {/* Unsaved changes confirmation dialog */}
      <AlertDialog open={showLeaveDialog} onOpenChange={setShowLeaveDialog}>
        <AlertDialogContent className="sm:max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-orange-500/10">
                <Save className="h-4 w-4 text-orange-500" />
              </div>
              Unsaved Changes
            </AlertDialogTitle>
            <AlertDialogDescription className="text-muted-foreground">
              You have unsaved changes to this workflow. What would you like to do?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-col gap-2 sm:flex-row sm:justify-end">
            <AlertDialogCancel className="mt-0">
              Keep Editing
            </AlertDialogCancel>
            <Button
              variant="outline"
              onClick={handleDiscardAndLeave}
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
            >
              <XCircle className="h-4 w-4 mr-2" />
              Discard
            </Button>
            <Button
              onClick={handleSaveAndLeave}
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save & Exit
                </>
              )}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* AI Step Generation Dialog */}
      <Dialog open={showAIStepDialog} onOpenChange={setShowAIStepDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500/20 to-blue-500/20">
                <Wand2 className="h-4 w-4 text-purple-400" />
              </div>
              Add Step with AI
            </DialogTitle>
            <DialogDescription>
              Describe the step you want to add. AI will generate an agent for this step.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="stepName">Step Name *</Label>
              <Input
                id="stepName"
                value={aiStepName}
                onChange={(e) => setAIStepName(e.target.value)}
                placeholder="e.g., Data Analyzer, Content Writer..."
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="stepPrompt">What should this step do?</Label>
              <Textarea
                id="stepPrompt"
                value={aiStepPrompt}
                onChange={(e) => setAIStepPrompt(e.target.value)}
                placeholder="e.g., Analyze incoming data and extract key insights, then format them into a summary report..."
                rows={4}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground">
                Tip: Be specific about the task, inputs, and expected outputs.
              </p>
            </div>
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setShowAIStepDialog(false);
                setAIStepName("");
                setAIStepPrompt("");
              }}
              disabled={isGeneratingStep}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleGenerateAIStep}
              disabled={!aiStepName.trim() || isGeneratingStep}
            >
              {isGeneratingStep ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate Step
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
