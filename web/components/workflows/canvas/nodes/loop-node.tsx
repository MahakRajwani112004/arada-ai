"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { RefreshCw, Check, Clock, AlertCircle, Bot, Hash, ListOrdered, Target } from "lucide-react";
import type { LoopNodeData, NodeStatus } from "@/lib/workflow-canvas/types";

interface LoopNodeProps {
  data: LoopNodeData;
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
    accentClass: "node-accent-cyan",
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

const loopModeConfig: Record<
  string,
  {
    label: string;
    description: string;
    icon: React.ReactNode;
  }
> = {
  count: {
    label: "Count",
    description: "Fixed iterations",
    icon: <Hash className="h-3 w-3" />,
  },
  foreach: {
    label: "For Each",
    description: "Iterate collection",
    icon: <ListOrdered className="h-3 w-3" />,
  },
  until: {
    label: "Until",
    description: "Until condition met",
    icon: <Target className="h-3 w-3" />,
  },
};

function LoopNodeComponent({ data, selected }: LoopNodeProps) {
  const status = data.status || "draft";
  const config = statusConfig[status];
  const modeConfig = loopModeConfig[data.loopMode] || loopModeConfig.count;
  const stepCount = data.innerSteps.length;

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
            <div className="node-icon h-8 w-8 node-icon-cyan">
              <RefreshCw className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm truncate">{data.name}</span>
                <span className="node-type-badge-cyan node-type-badge">Loop</span>
              </div>
              <div className="text-xs text-muted-foreground flex items-center gap-1">
                {modeConfig.icon}
                <span>{modeConfig.label}</span>
                <span className="text-muted-foreground/50">•</span>
                <span>
                  {data.loopMode === "foreach"
                    ? `${data.itemVariable || "item"}`
                    : `${data.maxIterations} max`}
                </span>
              </div>
            </div>
          </div>
          <span className={`node-badge shrink-0 ${config.badgeClass}`}>
            {config.icon}
            {config.label}
          </span>
        </div>

        {/* Inner Steps Preview */}
        {stepCount > 0 && (
          <div className="space-y-1.5">
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Inner Steps ({stepCount})
            </div>
            <div className="space-y-1">
              {data.innerSteps.slice(0, 3).map((step, index) => (
                <div
                  key={step.id}
                  className={`
                    flex items-center gap-1.5 px-2 py-1.5 rounded text-xs
                    ${step.agentId
                      ? "bg-cyan-50 dark:bg-cyan-500/10 text-cyan-700 dark:text-cyan-300"
                      : "bg-muted text-muted-foreground border border-dashed border-border"
                    }
                  `}
                >
                  <Bot className="h-3 w-3 shrink-0" />
                  <span className="truncate">
                    {step.agentName || `Step ${index + 1}`}
                  </span>
                </div>
              ))}
              {stepCount > 3 && (
                <div className="text-xs text-muted-foreground text-center py-1">
                  +{stepCount - 3} more
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty state */}
        {stepCount === 0 && (
          <div className="text-xs text-muted-foreground text-center py-2 border border-dashed border-border rounded">
            Click to add loop steps
          </div>
        )}

        {/* Loop Configuration Summary */}
        <div className="mt-2.5 flex flex-wrap items-center gap-2 text-xs">
          {data.loopMode === "foreach" && data.over && (
            <div className="flex items-center gap-1 text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
              <span className="font-mono text-[10px] truncate max-w-[120px]">
                {data.over.length > 20 ? `${data.over.slice(0, 20)}...` : data.over}
              </span>
            </div>
          )}
          {data.exitCondition && (
            <div className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
              <Target className="h-3 w-3" />
              <span>Exit condition</span>
            </div>
          )}
          {data.collectResults && (
            <div className="flex items-center gap-1 text-cyan-600 dark:text-cyan-400">
              <ListOrdered className="h-3 w-3" />
              <span>Collect results</span>
            </div>
          )}
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

export const LoopNode = memo(LoopNodeComponent);
