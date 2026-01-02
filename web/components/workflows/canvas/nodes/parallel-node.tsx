"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { Split, Check, Clock, AlertCircle, Bot, Layers } from "lucide-react";
import type { ParallelNodeData, NodeStatus } from "@/lib/workflow-canvas/types";

interface ParallelNodeProps {
  data: ParallelNodeData;
  selected?: boolean;
}

const statusConfig: Record<
  NodeStatus,
  {
    accentClass: string;
    badgeClass: string;
    icon: React.ReactNode;
    label: string;
  }
> = {
  ready: {
    accentClass: "node-accent-green",
    badgeClass: "node-badge-ready",
    icon: <Check className="h-3 w-3" />,
    label: "Ready",
  },
  draft: {
    accentClass: "node-accent-purple",
    badgeClass: "node-badge-draft",
    icon: <Clock className="h-3 w-3" />,
    label: "Draft",
  },
  warning: {
    accentClass: "node-accent-yellow",
    badgeClass: "node-badge-warning",
    icon: <AlertCircle className="h-3 w-3" />,
    label: "Warning",
  },
  error: {
    accentClass: "node-accent-red",
    badgeClass: "node-badge-error",
    icon: <AlertCircle className="h-3 w-3" />,
    label: "Error",
  },
};

const aggregationLabels: Record<string, string> = {
  all: "Collect All",
  first: "First Completed",
  merge: "Merge Results",
  best: "LLM Selects Best",
};

function ParallelNodeComponent({ data, selected }: ParallelNodeProps) {
  const status = data.status || "draft";
  const config = statusConfig[status];
  const branchCount = data.branches.length;

  return (
    <div
      className={`
        workflow-node min-w-[300px] transition-shadow
        ${config.accentClass}
        ${selected ? "workflow-node-selected" : ""}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="workflow-handle !-top-1.5"
      />

      <div className="p-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-2.5">
            <div className="node-icon h-8 w-8 node-icon-purple">
              <Split className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm truncate">{data.name}</span>
                <span className="node-type-badge-purple node-type-badge">Parallel</span>
              </div>
              <div className="text-xs text-muted-foreground">
                {branchCount} agent{branchCount !== 1 ? "s" : ""} in parallel
              </div>
            </div>
          </div>
          <span className={`node-badge shrink-0 ${config.badgeClass}`}>
            {config.icon}
            {config.label}
          </span>
        </div>

        {/* Branches Grid */}
        {data.viewMode === "grouped" && branchCount > 0 && (
          <div className="grid grid-cols-2 gap-1.5">
            {data.branches.slice(0, 4).map((branch, index) => (
              <div
                key={branch.id}
                className={`
                  flex items-center gap-1.5 px-2 py-1.5 rounded text-xs
                  ${branch.agentId
                    ? "bg-purple-50 dark:bg-purple-500/10 text-purple-700 dark:text-purple-300"
                    : "bg-muted text-muted-foreground border border-dashed border-border"
                  }
                `}
              >
                <Bot className="h-3 w-3 shrink-0" />
                <span className="truncate">
                  {branch.agentName || `Branch ${index + 1}`}
                </span>
              </div>
            ))}
            {branchCount > 4 && (
              <div className="flex items-center justify-center text-xs text-muted-foreground">
                +{branchCount - 4} more
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {branchCount === 0 && (
          <div className="text-xs text-muted-foreground text-center py-2 border border-dashed border-border rounded">
            Click to add agents
          </div>
        )}

        {/* Aggregation Strategy */}
        <div className="mt-2.5 flex items-center gap-2 text-xs text-muted-foreground">
          <Layers className="h-3 w-3" />
          <span>Results:</span>
          <span className="font-medium text-foreground">
            {aggregationLabels[data.aggregation] || data.aggregation}
          </span>
        </div>
      </div>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="workflow-handle !-bottom-1.5"
      />
    </div>
  );
}

export const ParallelNode = memo(ParallelNodeComponent);
