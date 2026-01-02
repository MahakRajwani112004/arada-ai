"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { Bot, Check, AlertCircle, Clock, X, Sparkles } from "lucide-react";
import type { AgentNodeData, NodeStatus } from "@/lib/workflow-canvas/types";

interface AgentNodeProps {
  data: AgentNodeData;
  selected?: boolean;
}

const statusConfig: Record<
  NodeStatus,
  {
    accentClass: string;
    iconClass: string;
    badgeClass: string;
    icon: React.ReactNode;
    label: string;
  }
> = {
  ready: {
    accentClass: "node-accent-green",
    iconClass: "node-icon-purple",
    badgeClass: "node-badge-ready",
    icon: <Check className="h-3 w-3" />,
    label: "Ready",
  },
  draft: {
    accentClass: "node-accent-orange",
    iconClass: "node-icon-orange",
    badgeClass: "node-badge-draft",
    icon: <Clock className="h-3 w-3" />,
    label: "Draft",
  },
  warning: {
    accentClass: "node-accent-yellow",
    iconClass: "node-icon-yellow",
    badgeClass: "node-badge-warning",
    icon: <AlertCircle className="h-3 w-3" />,
    label: "Warning",
  },
  error: {
    accentClass: "node-accent-red",
    iconClass: "node-icon-orange",
    badgeClass: "node-badge-error",
    icon: <X className="h-3 w-3" />,
    label: "Error",
  },
};

function AgentNodeComponent({ data, selected }: AgentNodeProps) {
  const status = data.status || "draft";
  const config = statusConfig[status];
  const isDraft = status === "draft";
  const hasSuggestion = !!data.suggestedAgent;

  return (
    <div
      className={`
        workflow-node min-w-[260px] transition-shadow
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
        {/* Header row with status badge */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-2.5">
            <div className={`node-icon h-8 w-8 ${config.iconClass}`}>
              <Bot className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="font-medium text-sm truncate">{data.name}</div>
              {data.agentName ? (
                <div className="text-xs text-muted-foreground truncate">
                  {data.agentName}
                </div>
              ) : (
                <div className="text-xs text-orange-500">No agent assigned</div>
              )}
            </div>
          </div>
          <span className={`node-badge shrink-0 ${config.badgeClass}`}>
            {config.icon}
            {config.label}
          </span>
        </div>

        {/* Agent Goal (ready state) */}
        {!isDraft && data.agentGoal && (
          <p className="text-xs text-muted-foreground line-clamp-2 mt-2">
            {data.agentGoal}
          </p>
        )}

        {/* AI Suggestion (draft state) */}
        {isDraft && hasSuggestion && (
          <div className="mt-2 rounded border border-orange-200 dark:border-orange-500/20 bg-orange-50 dark:bg-orange-500/5 p-2.5">
            <div className="flex items-center gap-1.5 text-xs font-medium text-orange-600 dark:text-orange-400 mb-1.5">
              <Sparkles className="h-3 w-3" />
              Suggested Agent
            </div>
            <div className="text-xs">
              <div className="font-medium truncate">{data.suggestedAgent?.name}</div>
              <div className="text-muted-foreground line-clamp-2 mt-0.5">
                {data.suggestedAgent?.goal}
              </div>
            </div>
          </div>
        )}

        {/* Draft placeholder */}
        {isDraft && !hasSuggestion && (
          <div className="mt-2 text-xs text-muted-foreground text-center py-2 border border-dashed border-border rounded">
            Click to assign agent
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

export const AgentNode = memo(AgentNodeComponent);
