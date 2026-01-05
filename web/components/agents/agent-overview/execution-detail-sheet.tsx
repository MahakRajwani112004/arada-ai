"use client";

import { useState } from "react";
import {
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Code2,
  Coins,
  XCircle,
  Wrench,
  Zap,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import type { ExecutionDetail, ToolCallDetail, AgentCallResult } from "@/types/agent";

interface ExecutionDetailSheetProps {
  execution: ExecutionDetail | null;
  isLoading: boolean;
  isOpen: boolean;
  onClose: () => void;
}

function formatDuration(ms: number) {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function formatCost(cents: number) {
  const dollars = cents / 100;
  if (dollars < 0.01) return `$${dollars.toFixed(4)}`;
  return `$${dollars.toFixed(2)}`;
}

function ToolCallCard({ call }: { call: ToolCallDetail }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-3 p-3 text-left hover:bg-muted/50 transition-colors"
      >
        <div
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded",
            call.result.success ? "bg-emerald-500/10" : "bg-red-500/10"
          )}
        >
          <Wrench
            className={cn(
              "h-3.5 w-3.5",
              call.result.success ? "text-emerald-500" : "text-red-500"
            )}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{call.tool}</span>
            <Badge
              variant="outline"
              className={cn(
                "text-[10px]",
                call.result.success
                  ? "bg-emerald-500/10 text-emerald-500"
                  : "bg-red-500/10 text-red-500"
              )}
            >
              {call.result.success ? "Success" : "Failed"}
            </Badge>
          </div>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {isExpanded && (
        <div className="border-t p-3 bg-muted/30 space-y-3">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Arguments</p>
            <pre className="text-xs bg-background p-2 rounded overflow-x-auto">
              <code>{JSON.stringify(call.args, null, 2)}</code>
            </pre>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">Result</p>
            <pre className="text-xs bg-background p-2 rounded overflow-x-auto max-h-40 overflow-y-auto">
              <code>
                {typeof call.result.output === "string"
                  ? call.result.output
                  : JSON.stringify(call.result.output, null, 2)}
              </code>
            </pre>
          </div>
          {call.result.error && (
            <div>
              <p className="text-xs text-red-500 mb-1">Error</p>
              <pre className="text-xs bg-red-500/10 text-red-500 p-2 rounded overflow-x-auto">
                <code>{call.result.error}</code>
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AgentCallCard({ result }: { result: AgentCallResult }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-3 p-3 text-left hover:bg-muted/50 transition-colors"
      >
        <div
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded",
            result.success ? "bg-blue-500/10" : "bg-red-500/10"
          )}
        >
          <Bot
            className={cn(
              "h-3.5 w-3.5",
              result.success ? "text-blue-500" : "text-red-500"
            )}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{result.agent_id}</span>
            <Badge
              variant="outline"
              className={cn(
                "text-[10px]",
                result.success
                  ? "bg-emerald-500/10 text-emerald-500"
                  : "bg-red-500/10 text-red-500"
              )}
            >
              {result.success ? "Success" : "Failed"}
            </Badge>
          </div>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {isExpanded && (
        <div className="border-t p-3 bg-muted/30 space-y-3">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Response</p>
            <pre className="text-xs bg-background p-2 rounded overflow-x-auto max-h-40 overflow-y-auto whitespace-pre-wrap">
              <code>{result.content}</code>
            </pre>
          </div>
          {result.error && (
            <div>
              <p className="text-xs text-red-500 mb-1">Error</p>
              <pre className="text-xs bg-red-500/10 text-red-500 p-2 rounded overflow-x-auto">
                <code>{result.error}</code>
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ExecutionDetailSheet({
  execution,
  isLoading,
  isOpen,
  onClose,
}: ExecutionDetailSheetProps) {
  const isSuccess = execution?.status === "completed";

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <div
              className={cn(
                "flex h-6 w-6 items-center justify-center rounded-full",
                isSuccess ? "bg-emerald-500/10" : "bg-red-500/10"
              )}
            >
              {isSuccess ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              ) : (
                <XCircle className="h-3.5 w-3.5 text-red-500" />
              )}
            </div>
            Execution Details
          </SheetTitle>
          <SheetDescription>
            {execution
              ? `${isSuccess ? "Completed" : "Failed"} ${formatDistanceToNow(
                  new Date(execution.timestamp),
                  { addSuffix: true }
                )}`
              : "Loading..."}
          </SheetDescription>
        </SheetHeader>

        {isLoading ? (
          <div className="mt-6 space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : execution ? (
          <ScrollArea className="h-[calc(100vh-8rem)] mt-6 pr-4">
            <div className="space-y-6">
              {/* Summary Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg border bg-card">
                  <div className="flex items-center gap-2 text-muted-foreground mb-1">
                    <Clock className="h-3.5 w-3.5" />
                    <span className="text-xs">Duration</span>
                  </div>
                  <p className="text-lg font-semibold">
                    {formatDuration(execution.duration_ms)}
                  </p>
                </div>
                <div className="p-3 rounded-lg border bg-card">
                  <div className="flex items-center gap-2 text-muted-foreground mb-1">
                    <Zap className="h-3.5 w-3.5" />
                    <span className="text-xs">Tokens</span>
                  </div>
                  <p className="text-lg font-semibold">
                    {execution.total_tokens.toLocaleString()}
                  </p>
                </div>
                <div className="p-3 rounded-lg border bg-card">
                  <div className="flex items-center gap-2 text-muted-foreground mb-1">
                    <Coins className="h-3.5 w-3.5" />
                    <span className="text-xs">Cost</span>
                  </div>
                  <p className="text-lg font-semibold">
                    {formatCost(execution.total_cost_cents)}
                  </p>
                </div>
                <div className="p-3 rounded-lg border bg-card">
                  <div className="flex items-center gap-2 text-muted-foreground mb-1">
                    <Code2 className="h-3.5 w-3.5" />
                    <span className="text-xs">Model</span>
                  </div>
                  <p className="text-sm font-medium truncate">
                    {execution.execution_metadata?.model || "N/A"}
                  </p>
                </div>
              </div>

              {/* Input */}
              {execution.input_preview && (
                <div>
                  <h3 className="text-sm font-medium mb-2">Input</h3>
                  <div className="p-3 rounded-lg border bg-muted/30">
                    <p className="text-sm">{execution.input_preview}</p>
                  </div>
                </div>
              )}

              {/* Output */}
              {execution.output_preview && (
                <div>
                  <h3 className="text-sm font-medium mb-2">Output</h3>
                  <div className="p-3 rounded-lg border bg-muted/30">
                    <p className="text-sm whitespace-pre-wrap">
                      {execution.output_preview}
                    </p>
                  </div>
                </div>
              )}

              {/* Error */}
              {execution.error_message && (
                <div>
                  <h3 className="text-sm font-medium mb-2 text-red-500">Error</h3>
                  <div className="p-3 rounded-lg border border-red-500/20 bg-red-500/10">
                    <p className="text-xs text-red-400 mb-1">
                      {execution.error_type}
                    </p>
                    <p className="text-sm text-red-500">
                      {execution.error_message}
                    </p>
                  </div>
                </div>
              )}

              {/* Tool Calls */}
              {execution.execution_metadata?.tool_calls &&
                execution.execution_metadata.tool_calls.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
                      <Wrench className="h-4 w-4 text-muted-foreground" />
                      Tool Calls ({execution.execution_metadata.tool_calls.length})
                    </h3>
                    <div className="space-y-2">
                      {execution.execution_metadata.tool_calls.map((call, i) => (
                        <ToolCallCard key={i} call={call} />
                      ))}
                    </div>
                  </div>
                )}

              {/* Agent Results (for orchestrators) */}
              {execution.execution_metadata?.agent_results &&
                execution.execution_metadata.agent_results.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
                      <Bot className="h-4 w-4 text-muted-foreground" />
                      Sub-Agent Calls (
                      {execution.execution_metadata.agent_results.length})
                    </h3>
                    <div className="space-y-2">
                      {execution.execution_metadata.agent_results.map(
                        (result, i) => (
                          <AgentCallCard
                            key={i}
                            result={result as AgentCallResult}
                          />
                        )
                      )}
                    </div>
                  </div>
                )}

              {/* Raw Metadata (collapsible) */}
              {execution.execution_metadata && (
                <details className="group">
                  <summary className="text-sm font-medium cursor-pointer list-none flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 transition-transform group-open:rotate-90" />
                    Raw Metadata
                  </summary>
                  <pre className="mt-2 text-xs bg-muted p-3 rounded-lg overflow-x-auto">
                    <code>
                      {JSON.stringify(execution.execution_metadata, null, 2)}
                    </code>
                  </pre>
                </details>
              )}
            </div>
          </ScrollArea>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
