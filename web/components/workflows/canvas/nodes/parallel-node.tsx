"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { Split, Check, Clock, AlertCircle, Bot, Layers } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ParallelNodeData, NodeStatus } from "@/lib/workflow-canvas/types";

interface ParallelNodeProps {
  data: ParallelNodeData;
  selected?: boolean;
}

const statusConfig: Record<
  NodeStatus,
  { borderClass: string; bgClass: string; icon: React.ReactNode; label: string }
> = {
  ready: {
    borderClass: "border-green-500/50",
    bgClass: "",
    icon: <Check className="h-3 w-3 text-green-500" />,
    label: "Ready",
  },
  draft: {
    borderClass: "border-dashed border-purple-500/50",
    bgClass: "bg-purple-500/5",
    icon: <Clock className="h-3 w-3 text-purple-500" />,
    label: "Draft",
  },
  warning: {
    borderClass: "border-yellow-500/50",
    bgClass: "",
    icon: <AlertCircle className="h-3 w-3 text-yellow-500" />,
    label: "Warning",
  },
  error: {
    borderClass: "border-red-500/50",
    bgClass: "",
    icon: <AlertCircle className="h-3 w-3 text-red-500" />,
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
        relative rounded-lg border-2 bg-card shadow-sm transition-all
        ${selected ? "border-primary ring-2 ring-primary/20" : config.borderClass}
        ${config.bgClass}
        min-w-[320px]
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="!h-4 !w-4 !border-2 !border-background !bg-primary hover:!bg-primary/80 hover:!scale-125 transition-all !-top-2"
      />

      {/* Status badge - top right */}
      <Badge
        variant="secondary"
        className={`absolute -top-2.5 right-3 text-[10px] px-1.5 py-0 h-5 gap-1
          ${status === "ready" ? "bg-green-500/10 text-green-600" : ""}
          ${status === "draft" ? "bg-purple-500/10 text-purple-600" : ""}
          ${status === "warning" ? "bg-yellow-500/10 text-yellow-600" : ""}
          ${status === "error" ? "bg-red-500/10 text-red-600" : ""}
        `}
      >
        {config.icon}
        {config.label}
      </Badge>

      {/* Type badge - top left */}
      <Badge
        variant="outline"
        className="absolute -top-2.5 left-3 text-[10px] px-1.5 py-0 h-5 gap-1 bg-card border-purple-500/30 text-purple-600"
      >
        <Split className="h-3 w-3" />
        Parallel
      </Badge>

      {/* Main Content */}
      <div className="px-4 py-3 pt-4">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-purple-500/10">
            <Split className="h-5 w-5 text-purple-500" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-medium text-sm truncate">
              {data.name}
            </div>
            <div className="text-xs text-muted-foreground">
              {branchCount} agent{branchCount !== 1 ? "s" : ""} in parallel
            </div>
          </div>
        </div>

        {/* Branches Grid (Grouped View) */}
        {data.viewMode === "grouped" && branchCount > 0 && (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {data.branches.slice(0, 4).map((branch, index) => (
              <div
                key={branch.id}
                className={`
                  flex items-center gap-2 px-2 py-1.5 rounded border text-xs
                  ${branch.agentId ? "border-purple-500/20 bg-purple-500/5" : "border-dashed border-gray-300"}
                `}
              >
                <Bot className={`h-3 w-3 ${branch.agentId ? "text-purple-500" : "text-gray-400"}`} />
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
          <div className="mt-3 text-xs text-muted-foreground text-center py-3 border border-dashed border-border rounded">
            Click to add parallel agents
          </div>
        )}

        {/* Aggregation Strategy */}
        <div className="mt-3 flex items-center gap-2 text-xs">
          <Layers className="h-3 w-3 text-muted-foreground" />
          <span className="text-muted-foreground">Results:</span>
          <Badge variant="secondary" className="text-[10px] h-4 px-1.5">
            {aggregationLabels[data.aggregation] || data.aggregation}
          </Badge>
        </div>
      </div>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-4 !w-4 !border-2 !border-background !bg-primary hover:!bg-primary/80 hover:!scale-125 transition-all !-bottom-2"
      />
    </div>
  );
}

export const ParallelNode = memo(ParallelNodeComponent);
