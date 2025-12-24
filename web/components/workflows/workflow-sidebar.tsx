"use client";

import { Bot, GitBranch, GitFork, RefreshCw } from "lucide-react";
import { StepType } from "@/types/workflow";

interface StepTypeItem {
  type: StepType;
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
}

const stepTypes: StepTypeItem[] = [
  {
    type: "agent",
    label: "Agent",
    description: "Execute a single agent",
    icon: <Bot className="h-4 w-4" />,
    color: "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
  },
  {
    type: "parallel",
    label: "Parallel",
    description: "Run agents in parallel",
    icon: <GitBranch className="h-4 w-4" />,
    color: "bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400",
  },
  {
    type: "conditional",
    label: "Conditional",
    description: "Route based on condition",
    icon: <GitFork className="h-4 w-4" />,
    color: "bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400",
  },
  {
    type: "loop",
    label: "Loop",
    description: "Repeat steps",
    icon: <RefreshCw className="h-4 w-4" />,
    color: "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400",
  },
];

export function WorkflowSidebar() {
  const onDragStart = (event: React.DragEvent, nodeType: StepType) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <div className="w-56 border-r bg-muted/30 p-4 flex flex-col">
      <h3 className="font-semibold text-sm mb-4">Step Types</h3>
      <p className="text-xs text-muted-foreground mb-4">
        Drag and drop to add steps
      </p>

      <div className="space-y-2">
        {stepTypes.map((step) => (
          <div
            key={step.type}
            draggable
            onDragStart={(e) => onDragStart(e, step.type)}
            className="p-3 border rounded-lg cursor-grab bg-card hover:bg-accent hover:border-primary/40 transition-colors active:cursor-grabbing"
          >
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-md ${step.color}`}>{step.icon}</div>
              <div>
                <div className="font-medium text-sm">{step.label}</div>
                <div className="text-xs text-muted-foreground">
                  {step.description}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-auto pt-4 border-t">
        <div className="text-xs text-muted-foreground">
          <p className="font-medium mb-1">Tips:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Click node to configure</li>
            <li>Connect nodes by dragging</li>
            <li>Delete with Backspace</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
