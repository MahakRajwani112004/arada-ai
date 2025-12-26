"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { GitBranch, Check, Clock, AlertCircle, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ConditionalNodeData, NodeStatus } from "@/lib/workflow-canvas/types";

interface ConditionalNodeProps {
  data: ConditionalNodeData;
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
    borderClass: "border-dashed border-blue-500/50",
    bgClass: "bg-blue-500/5",
    icon: <Clock className="h-3 w-3 text-blue-500" />,
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

function ConditionalNodeComponent({ data, selected }: ConditionalNodeProps) {
  const status = data.status || "draft";
  const config = statusConfig[status];
  const isDraft = status === "draft";
  const branchCount = data.branches.length + (data.defaultStepId ? 1 : 0);

  return (
    <div
      className={`
        relative rounded-lg border-2 bg-card shadow-sm transition-all
        ${selected ? "border-primary ring-2 ring-primary/20" : config.borderClass}
        ${config.bgClass}
        min-w-[300px]
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
          ${status === "draft" ? "bg-blue-500/10 text-blue-600" : ""}
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
        className="absolute -top-2.5 left-3 text-[10px] px-1.5 py-0 h-5 gap-1 bg-card border-blue-500/30 text-blue-600"
      >
        <GitBranch className="h-3 w-3" />
        Conditional
      </Badge>

      {/* Main Content */}
      <div className="px-4 py-3 pt-4">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-500/10">
            <GitBranch className="h-5 w-5 text-blue-500" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-medium text-sm truncate">
              {data.name}
            </div>
            {data.classifierAgentName ? (
              <div className="text-xs text-muted-foreground truncate">
                Classifier: {data.classifierAgentName}
              </div>
            ) : (
              <div className="text-xs text-blue-500">
                Select classifier agent
              </div>
            )}
          </div>
        </div>

        {/* Branches Preview */}
        <div className="mt-3 space-y-1">
          {data.branches.slice(0, 3).map((branch, index) => (
            <div
              key={index}
              className="flex items-center gap-2 text-xs text-muted-foreground"
            >
              <ChevronRight className="h-3 w-3 text-blue-500" />
              <span className="font-medium text-foreground">{branch.condition}</span>
              <span className="text-muted-foreground">→</span>
              <span className="truncate">{branch.targetStepName || branch.targetStepId}</span>
            </div>
          ))}
          {data.branches.length > 3 && (
            <div className="text-xs text-muted-foreground pl-5">
              +{data.branches.length - 3} more...
            </div>
          )}
          {data.defaultStepId && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <ChevronRight className="h-3 w-3 text-gray-400" />
              <span className="font-medium text-foreground">default</span>
              <span className="text-muted-foreground">→</span>
              <span className="truncate">{data.defaultStepName || data.defaultStepId}</span>
            </div>
          )}
        </div>

        {/* Draft state placeholder */}
        {isDraft && data.branches.length === 0 && (
          <div className="mt-3 text-xs text-muted-foreground text-center py-2 border border-dashed border-border rounded">
            Click to configure branches
          </div>
        )}

        {/* Branch count indicator */}
        {branchCount > 0 && (
          <div className="mt-2 text-[10px] text-muted-foreground">
            {branchCount} branch{branchCount !== 1 ? "es" : ""} configured
          </div>
        )}
      </div>

      {/* Output handle - single for now, branches are handled by edges */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-4 !w-4 !border-2 !border-background !bg-primary hover:!bg-primary/80 hover:!scale-125 transition-all !-bottom-2"
      />
    </div>
  );
}

export const ConditionalNode = memo(ConditionalNodeComponent);
