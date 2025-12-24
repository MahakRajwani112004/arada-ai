"use client";

import { Check, X, Clock, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { WorkflowExecutionSummary, ExecutionStatus } from "@/types/workflow";
import { formatDistanceToNow } from "date-fns";

interface ExecutionHistoryProps {
  executions: WorkflowExecutionSummary[];
  isLoading?: boolean;
  onSelect?: (executionId: string) => void;
}

function getStatusIcon(status: ExecutionStatus) {
  switch (status) {
    case "COMPLETED":
      return <Check className="h-4 w-4 text-green-400" />;
    case "FAILED":
      return <X className="h-4 w-4 text-red-400" />;
    case "RUNNING":
      return <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />;
    case "CANCELLED":
      return <X className="h-4 w-4 text-gray-400" />;
    default:
      return <Clock className="h-4 w-4 text-gray-400" />;
  }
}

function getStatusColor(status: ExecutionStatus) {
  switch (status) {
    case "COMPLETED":
      return "text-green-400";
    case "FAILED":
      return "text-red-400";
    case "RUNNING":
      return "text-blue-400";
    case "CANCELLED":
      return "text-gray-400";
    default:
      return "text-gray-400";
  }
}

function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return "-";
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
}

export function ExecutionHistory({
  executions,
  isLoading,
  onSelect,
}: ExecutionHistoryProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Runs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-12" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  if (executions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-4">
            No executions yet
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Recent Runs</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {executions.slice(0, 5).map((execution) => (
          <button
            key={execution.id}
            onClick={() => onSelect?.(execution.id)}
            className="w-full flex items-center justify-between rounded-md px-3 py-2 hover:bg-secondary/50 transition-colors text-left"
          >
            <div className="flex items-center gap-2">
              {getStatusIcon(execution.status)}
              <span className="text-sm">
                {formatDistanceToNow(new Date(execution.started_at), {
                  addSuffix: true,
                })}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-xs ${getStatusColor(execution.status)}`}>
                {execution.status.toLowerCase()}
              </span>
              <span className="text-xs text-muted-foreground">
                {formatDuration(execution.duration_ms)}
              </span>
            </div>
          </button>
        ))}
      </CardContent>
    </Card>
  );
}
