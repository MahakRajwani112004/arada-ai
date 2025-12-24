"use client";

import { X, Trash2, Bot, GitBranch, GitFork, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useWorkflowBuilderStore } from "@/stores/workflow-builder-store";
import { WorkflowNodeData, StepType } from "@/types/workflow";
import {
  AgentStepConfig,
  ParallelStepConfig,
  ConditionalStepConfig,
  LoopStepConfig,
} from "./config";

const stepTypeConfig: Record<
  StepType,
  { icon: React.ReactNode; label: string; color: string }
> = {
  agent: {
    icon: <Bot className="h-4 w-4" />,
    label: "Agent Step",
    color: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  },
  parallel: {
    icon: <GitBranch className="h-4 w-4" />,
    label: "Parallel Step",
    color: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  },
  conditional: {
    icon: <GitFork className="h-4 w-4" />,
    label: "Conditional Step",
    color: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  },
  loop: {
    icon: <RefreshCw className="h-4 w-4" />,
    label: "Loop Step",
    color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  },
};

export function WorkflowConfigPanel() {
  const { nodes, selectedNodeId, setSelectedNode, updateNode, removeNode } =
    useWorkflowBuilderStore();

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  if (!selectedNode) {
    return (
      <div className="w-80 border-l bg-muted/30 p-4 flex items-center justify-center">
        <p className="text-sm text-muted-foreground text-center">
          Select a step to configure
        </p>
      </div>
    );
  }

  const data = selectedNode.data;
  const config = stepTypeConfig[data.stepType];

  const handleChange = (updates: Partial<WorkflowNodeData>) => {
    updateNode(selectedNode.id, updates);
  };

  const handleDelete = () => {
    removeNode(selectedNode.id);
  };

  return (
    <div className="w-80 border-l bg-muted/30 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded ${config.color}`}>{config.icon}</div>
            <span className="font-medium text-sm">{config.label}</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setSelectedNode(null)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs">
            {selectedNode.id}
          </Badge>
        </div>
      </div>

      {/* Config Form */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {data.stepType === "agent" && (
            <AgentStepConfig data={data} onChange={handleChange} />
          )}
          {data.stepType === "parallel" && (
            <ParallelStepConfig data={data} onChange={handleChange} />
          )}
          {data.stepType === "conditional" && (
            <ConditionalStepConfig data={data} onChange={handleChange} />
          )}
          {data.stepType === "loop" && (
            <LoopStepConfig data={data} onChange={handleChange} />
          )}
        </div>
      </ScrollArea>

      {/* Footer with Delete */}
      <div className="p-4 border-t">
        <Button
          variant="destructive"
          className="w-full"
          onClick={handleDelete}
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Delete Step
        </Button>
      </div>
    </div>
  );
}
