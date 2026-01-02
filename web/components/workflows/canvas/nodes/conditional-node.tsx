"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { GitBranch, Check, Clock, AlertCircle, ChevronRight } from "lucide-react";
import type { ConditionalNodeData, NodeStatus } from "@/lib/workflow-canvas/types";

interface ConditionalNodeProps {
  data: ConditionalNodeData;
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
    accentClass: "node-accent-blue",
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

function ConditionalNodeComponent({ data, selected }: ConditionalNodeProps) {
  const status = data.status || "draft";
  const config = statusConfig[status];
  const isDraft = status === "draft";
  const branchCount = data.branches.length + (data.defaultStepId ? 1 : 0);

  return (
    <div
      className={`
        workflow-node min-w-[280px] transition-shadow
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
            <div className="node-icon h-8 w-8 node-icon-blue">
              <GitBranch className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm truncate">{data.name}</span>
                <span className="node-type-badge-blue node-type-badge">Conditional</span>
              </div>
              {data.classifierAgentName ? (
                <div className="text-xs text-muted-foreground truncate">
                  {data.classifierAgentName}
                </div>
              ) : (
                <div className="text-xs text-blue-500">Select classifier</div>
              )}
            </div>
          </div>
          <span className={`node-badge shrink-0 ${config.badgeClass}`}>
            {config.icon}
            {config.label}
          </span>
        </div>

        {/* Branches Preview */}
        {data.branches.length > 0 && (
          <div className="space-y-1">
            {data.branches.slice(0, 3).map((branch, index) => (
              <div
                key={index}
                className="flex items-center gap-2 text-xs py-1 px-2 rounded bg-muted/50"
              >
                <ChevronRight className="h-3 w-3 text-blue-500 shrink-0" />
                <span className="font-medium">{branch.condition}</span>
                <span className="text-muted-foreground">→</span>
                <span className="truncate text-muted-foreground">
                  {branch.targetStepName || branch.targetStepId}
                </span>
              </div>
            ))}
            {data.branches.length > 3 && (
              <div className="text-xs text-muted-foreground pl-2">
                +{data.branches.length - 3} more
              </div>
            )}
            {data.defaultStepId && (
              <div className="flex items-center gap-2 text-xs py-1 px-2 rounded bg-muted/30">
                <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
                <span className="font-medium">default</span>
                <span className="text-muted-foreground">→</span>
                <span className="truncate text-muted-foreground">
                  {data.defaultStepName || data.defaultStepId}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Draft placeholder */}
        {isDraft && data.branches.length === 0 && (
          <div className="text-xs text-muted-foreground text-center py-2 border border-dashed border-border rounded">
            Click to configure branches
          </div>
        )}

        {/* Branch count */}
        {branchCount > 0 && (
          <div className="mt-2 text-[11px] text-muted-foreground">
            {branchCount} branch{branchCount !== 1 ? "es" : ""}
          </div>
        )}
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

export const ConditionalNode = memo(ConditionalNodeComponent);
