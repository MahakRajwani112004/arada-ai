"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { UserCheck, Check, Clock, AlertCircle, Users, Timer } from "lucide-react";
import type { NodeStatus } from "@/lib/workflow-canvas/types";

export interface ApprovalNodeData extends Record<string, unknown> {
  type: "approval";
  stepId: string;
  name: string;
  approvalMessage: string;
  approvers: string[];
  requiredApprovals: number;
  timeoutSeconds?: number;
  onReject: "fail" | "skip" | string;
  status: NodeStatus;
}

interface ApprovalNodeProps {
  data: ApprovalNodeData;
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
    accentClass: "node-accent-amber",
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

function formatTimeout(seconds: number): string {
  if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}m`;
  } else if (seconds < 86400) {
    return `${Math.floor(seconds / 3600)}h`;
  } else {
    return `${Math.floor(seconds / 86400)}d`;
  }
}

function ApprovalNodeComponent({ data, selected }: ApprovalNodeProps) {
  const status = data.status || "draft";
  const config = statusConfig[status];
  const approverCount = data.approvers.length;

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
            <div className="node-icon h-8 w-8 node-icon-amber">
              <UserCheck className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm truncate">{data.name}</span>
                <span className="node-type-badge-amber node-type-badge">Approval</span>
              </div>
              <div className="text-xs text-muted-foreground flex items-center gap-1">
                <Users className="h-3 w-3" />
                <span>
                  {approverCount > 0
                    ? `${approverCount} approver${approverCount > 1 ? "s" : ""}`
                    : "Any user"}
                </span>
                {data.requiredApprovals > 1 && (
                  <>
                    <span className="text-muted-foreground/50">•</span>
                    <span>{data.requiredApprovals} required</span>
                  </>
                )}
              </div>
            </div>
          </div>
          <span className={`node-badge shrink-0 ${config.badgeClass}`}>
            {config.icon}
            {config.label}
          </span>
        </div>

        {/* Approval Message Preview */}
        {data.approvalMessage && (
          <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2 mb-2 line-clamp-2">
            {data.approvalMessage}
          </div>
        )}

        {/* Configuration Summary */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {data.timeoutSeconds && (
            <div className="flex items-center gap-1 text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 px-1.5 py-0.5 rounded">
              <Timer className="h-3 w-3" />
              <span>{formatTimeout(data.timeoutSeconds)}</span>
            </div>
          )}
          {data.onReject !== "fail" && (
            <div className="flex items-center gap-1 text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
              <span>On reject: {data.onReject === "skip" ? "Skip" : "Jump"}</span>
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

export const ApprovalNode = memo(ApprovalNodeComponent);
