"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { Bot, Check, AlertCircle, Clock, X, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { AgentNodeData, NodeStatus } from "@/lib/workflow-canvas/types";

interface AgentNodeProps {
  data: AgentNodeData;
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
    borderClass: "border-dashed border-orange-500/50",
    bgClass: "bg-orange-500/5",
    icon: <Clock className="h-3 w-3 text-orange-500" />,
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
    icon: <X className="h-3 w-3 text-red-500" />,
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
        relative rounded-lg border-2 bg-card shadow-sm transition-all
        ${selected ? "border-primary ring-2 ring-primary/20" : config.borderClass}
        ${config.bgClass}
        ${isDraft ? "min-w-[300px]" : "min-w-[260px]"}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="!h-3 !w-3 !border-2 !border-background !bg-primary"
      />

      {/* Status badge - top right */}
      <Badge
        variant="secondary"
        className={`absolute -top-2.5 right-3 text-[10px] px-1.5 py-0 h-5 gap-1
          ${status === "ready" ? "bg-green-500/10 text-green-600" : ""}
          ${status === "draft" ? "bg-orange-500/10 text-orange-600" : ""}
          ${status === "warning" ? "bg-yellow-500/10 text-yellow-600" : ""}
          ${status === "error" ? "bg-red-500/10 text-red-600" : ""}
        `}
      >
        {config.icon}
        {config.label}
      </Badge>

      {/* Main Content */}
      <div className="px-4 py-3">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
            isDraft ? "bg-orange-500/10" : "bg-purple-500/10"
          }`}>
            <Bot className={`h-5 w-5 ${isDraft ? "text-orange-500" : "text-purple-500"}`} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-medium text-sm truncate">
              {data.name}
            </div>
            {data.agentName ? (
              <div className="text-xs text-muted-foreground truncate">
                Agent: {data.agentName}
              </div>
            ) : (
              <div className="text-xs text-orange-500">
                No agent assigned
              </div>
            )}
          </div>
        </div>

        {/* Agent Goal (for ready state) */}
        {!isDraft && data.agentGoal && (
          <div className="mt-2 text-xs text-muted-foreground line-clamp-2">
            {data.agentGoal}
          </div>
        )}

        {/* AI Suggestion (for draft state) */}
        {isDraft && hasSuggestion && (
          <div className="mt-3 rounded-md border border-orange-500/20 bg-orange-500/5 p-3">
            <div className="flex items-center gap-1.5 text-xs font-medium text-orange-600 mb-2">
              <Sparkles className="h-3 w-3" />
              AI Suggested
            </div>
            <div className="space-y-1 text-xs">
              <div className="font-medium truncate">
                {data.suggestedAgent?.name}
              </div>
              <div className="text-muted-foreground line-clamp-2">
                {data.suggestedAgent?.goal}
              </div>
            </div>
            <div className="mt-3 text-[10px] text-muted-foreground text-center">
              Click node to configure
            </div>
          </div>
        )}

        {/* Draft without suggestion */}
        {isDraft && !hasSuggestion && (
          <div className="mt-3 text-xs text-muted-foreground text-center py-2 border border-dashed border-border rounded">
            Click to assign agent
          </div>
        )}
      </div>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-3 !w-3 !border-2 !border-background !bg-primary"
      />
    </div>
  );
}

export const AgentNode = memo(AgentNodeComponent);
