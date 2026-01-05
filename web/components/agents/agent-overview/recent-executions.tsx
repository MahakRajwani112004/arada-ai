"use client";

import { useState } from "react";
import { CheckCircle2, Clock, XCircle, MessageSquare, ChevronRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ExecutionSummary, ExecutionDetail } from "@/types/agent";
import { formatDistanceToNow } from "date-fns";
import { getExecutionDetail } from "@/lib/api/agents";
import { ExecutionDetailSheet } from "./execution-detail-sheet";

interface RecentExecutionsProps {
  executions: ExecutionSummary[] | undefined;
  isLoading: boolean;
  total: number;
}

function ExecutionRow({
  execution,
  onClick,
}: {
  execution: ExecutionSummary;
  onClick: () => void;
}) {
  const isSuccess = execution.status === "completed";
  const date = new Date(execution.timestamp);

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatCost = (cents: number) => {
    const dollars = cents / 100;
    if (dollars < 0.01) return `$${dollars.toFixed(4)}`;
    return `$${dollars.toFixed(2)}`;
  };

  return (
    <button
      onClick={onClick}
      className="w-full flex items-start gap-3 py-3 border-b last:border-0 text-left hover:bg-muted/50 transition-colors rounded-lg px-2 -mx-2"
    >
      <div
        className={cn(
          "mt-0.5 flex h-6 w-6 items-center justify-center rounded-full shrink-0",
          isSuccess ? "bg-emerald-500/10" : "bg-red-500/10"
        )}
      >
        {isSuccess ? (
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
        ) : (
          <XCircle className="h-3.5 w-3.5 text-red-500" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium truncate">
            {execution.input_preview || "No input recorded"}
          </p>
          <Badge
            variant="outline"
            className={cn(
              "text-[10px] shrink-0",
              isSuccess
                ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                : "bg-red-500/10 text-red-500 border-red-500/20"
            )}
          >
            {isSuccess ? "Success" : "Failed"}
          </Badge>
        </div>

        {execution.output_preview && (
          <p className="mt-1 text-xs text-muted-foreground line-clamp-1">
            {execution.output_preview}
          </p>
        )}

        {!isSuccess && execution.error_message && (
          <p className="mt-1 text-xs text-red-400 line-clamp-1">
            {execution.error_type}: {execution.error_message}
          </p>
        )}

        <div className="mt-1.5 flex items-center gap-3 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDuration(execution.duration_ms)}
          </span>
          {execution.total_tokens > 0 && (
            <span>{execution.total_tokens.toLocaleString()} tokens</span>
          )}
          {execution.total_cost_cents > 0 && (
            <span>{formatCost(execution.total_cost_cents)}</span>
          )}
          <span className="text-muted-foreground/60">
            {formatDistanceToNow(date, { addSuffix: true })}
          </span>
        </div>
      </div>

      <ChevronRight className="h-4 w-4 text-muted-foreground mt-1 shrink-0" />
    </button>
  );
}

function ExecutionSkeleton() {
  return (
    <div className="flex items-start gap-3 py-3 border-b last:border-0">
      <Skeleton className="h-6 w-6 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <div className="flex gap-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 w-20" />
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
      <MessageSquare className="h-10 w-10 mb-2 opacity-50" />
      <p className="text-sm font-medium">No executions yet</p>
      <p className="text-xs">Start chatting with your agent to see history here</p>
    </div>
  );
}

export function RecentExecutions({
  executions,
  isLoading,
  total,
}: RecentExecutionsProps) {
  const [selectedExecution, setSelectedExecution] = useState<ExecutionDetail | null>(null);
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const handleExecutionClick = async (executionId: string) => {
    setIsSheetOpen(true);
    setIsLoadingDetail(true);
    try {
      const detail = await getExecutionDetail(executionId);
      setSelectedExecution(detail);
    } catch (error) {
      console.error("Failed to load execution detail:", error);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleSheetClose = () => {
    setIsSheetOpen(false);
    setSelectedExecution(null);
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Executions</CardTitle>
          <CardDescription>Latest agent interactions</CardDescription>
        </CardHeader>
        <CardContent>
          {Array.from({ length: 5 }).map((_, i) => (
            <ExecutionSkeleton key={i} />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Recent Executions</CardTitle>
              <CardDescription>
                {total > 0
                  ? `Showing ${executions?.length ?? 0} of ${total} total • Click to view details`
                  : "No executions recorded"}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {!executions || executions.length === 0 ? (
            <EmptyState />
          ) : (
            <div>
              {executions.map((execution) => (
                <ExecutionRow
                  key={execution.id}
                  execution={execution}
                  onClick={() => handleExecutionClick(execution.id)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <ExecutionDetailSheet
        execution={selectedExecution}
        isLoading={isLoadingDetail}
        isOpen={isSheetOpen}
        onClose={handleSheetClose}
      />
    </>
  );
}
