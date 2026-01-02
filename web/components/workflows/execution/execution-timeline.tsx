"use client";

import {
  Check,
  X,
  Loader2,
  Clock,
  ChevronDown,
  AlertCircle,
  Coins,
  Activity,
  Zap,
} from "lucide-react";
import { useState, useMemo } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { StepResult, StepExecutionStatus } from "@/types/workflow";
import { cn } from "@/lib/utils";

interface ExecutionTimelineProps {
  steps: StepResult[];
  currentStepIndex?: number;
  showGanttView?: boolean;
  startTime?: string;
}

interface StepMetrics {
  tokens?: {
    input: number;
    output: number;
    total: number;
  };
  cost?: number;
  iterations?: number;
}

function getStepStatusIcon(status: StepExecutionStatus) {
  switch (status) {
    case "COMPLETED":
      return <Check className="h-4 w-4 text-green-400" />;
    case "FAILED":
      return <X className="h-4 w-4 text-red-400" />;
    case "RUNNING":
      return <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />;
    case "PENDING":
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />;
  }
}

function getStepStatusColor(status: StepExecutionStatus) {
  switch (status) {
    case "COMPLETED":
      return "bg-green-500";
    case "FAILED":
      return "bg-red-500";
    case "RUNNING":
      return "bg-blue-500";
    case "PENDING":
    default:
      return "bg-muted";
  }
}

function formatDuration(ms: number | undefined): string {
  if (ms === undefined) return "";
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const mins = Math.floor(ms / 60000);
  const secs = ((ms % 60000) / 1000).toFixed(0);
  return `${mins}m ${secs}s`;
}

function formatCost(cost: number): string {
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  return `$${cost.toFixed(2)}`;
}

function extractMetrics(step: StepResult): StepMetrics | null {
  const metadata = (step.metadata || {}) as {
    tokens_used?: number;
    input_tokens?: number;
    output_tokens?: number;
    cost?: number;
    iterations?: number;
  };
  const metrics: StepMetrics = {};

  // Extract token counts from metadata
  if (metadata.tokens_used || metadata.input_tokens || metadata.output_tokens) {
    const inputTokens = metadata.input_tokens || 0;
    const outputTokens = metadata.output_tokens || 0;
    metrics.tokens = {
      input: inputTokens,
      output: outputTokens,
      total: metadata.tokens_used || inputTokens + outputTokens,
    };
  }

  // Extract cost
  if (metadata.cost !== undefined) {
    metrics.cost = metadata.cost;
  }

  // Extract iterations for loop steps
  if (metadata.iterations !== undefined) {
    metrics.iterations = metadata.iterations;
  }

  return Object.keys(metrics).length > 0 ? metrics : null;
}

interface StepItemProps {
  step: StepResult;
  isLast: boolean;
  showGantt: boolean;
  totalDuration: number;
  startOffset: number;
}

function StepItem({ step, isLast, showGantt, totalDuration, startOffset }: StepItemProps) {
  const [isOpen, setIsOpen] = useState(false);
  const hasOutput = step.output !== undefined;
  const hasError = step.error !== undefined;
  const metrics = extractMetrics(step);

  // Calculate Gantt bar dimensions
  const barWidth = totalDuration > 0 && step.duration_ms
    ? (step.duration_ms / totalDuration) * 100
    : 0;
  const barOffset = totalDuration > 0
    ? (startOffset / totalDuration) * 100
    : 0;

  return (
    <div className="relative">
      {/* Connector line */}
      {!isLast && (
        <div className="absolute left-[15px] top-8 h-full w-px bg-border" />
      )}

      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger className="w-full">
          <div
            className={cn(
              "flex items-center gap-3 rounded-lg p-3 transition-colors hover:bg-secondary/50",
              step.status === "RUNNING" && "bg-blue-500/5",
              step.status === "FAILED" && "bg-red-500/5"
            )}
          >
            {/* Status icon */}
            <div
              className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                step.status === "COMPLETED" && "bg-green-500/20",
                step.status === "FAILED" && "bg-red-500/20",
                step.status === "RUNNING" && "bg-blue-500/20",
                step.status === "PENDING" && "bg-secondary"
              )}
            >
              {getStepStatusIcon(step.status)}
            </div>

            {/* Step info */}
            <div className="flex-1 min-w-0 text-left">
              <div className="flex items-center gap-2">
                <span className="font-medium truncate">{step.step_name || step.step_id}</span>
                {step.status === "RUNNING" && (
                  <Badge variant="outline" className="text-blue-400 border-blue-400/30">
                    running
                  </Badge>
                )}
                {step.status === "FAILED" && (
                  <Badge variant="outline" className="text-red-400 border-red-400/30">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    failed
                  </Badge>
                )}
              </div>

              {/* Duration and metrics row */}
              <div className="flex items-center gap-3 mt-1">
                {step.duration_ms !== undefined && (
                  <span className="text-xs text-muted-foreground">
                    <Clock className="inline h-3 w-3 mr-1" />
                    {formatDuration(step.duration_ms)}
                  </span>
                )}
                {metrics?.tokens && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="text-xs text-muted-foreground cursor-help">
                          <Zap className="inline h-3 w-3 mr-1" />
                          {metrics.tokens.total.toLocaleString()} tokens
                        </span>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Input: {metrics.tokens.input.toLocaleString()}</p>
                        <p>Output: {metrics.tokens.output.toLocaleString()}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
                {metrics?.cost !== undefined && (
                  <span className="text-xs text-muted-foreground">
                    <Coins className="inline h-3 w-3 mr-1" />
                    {formatCost(metrics.cost)}
                  </span>
                )}
                {metrics?.iterations !== undefined && (
                  <span className="text-xs text-muted-foreground">
                    <Activity className="inline h-3 w-3 mr-1" />
                    {metrics.iterations} iterations
                  </span>
                )}
              </div>

              {/* Gantt bar */}
              {showGantt && step.duration_ms && totalDuration > 0 && (
                <div className="mt-2 h-2 rounded-full bg-secondary relative">
                  <div
                    className={cn(
                      "absolute h-2 rounded-full transition-all",
                      getStepStatusColor(step.status)
                    )}
                    style={{
                      left: `${barOffset}%`,
                      width: `${Math.max(barWidth, 2)}%`,
                    }}
                  />
                </div>
              )}
            </div>

            {/* Expand indicator */}
            {(hasOutput || hasError) && (
              <ChevronDown
                className={cn(
                  "h-4 w-4 text-muted-foreground transition-transform",
                  isOpen && "rotate-180"
                )}
              />
            )}
          </div>
        </CollapsibleTrigger>

        {(hasOutput || hasError) && (
          <CollapsibleContent>
            <div className="ml-11 mt-1 space-y-2 pb-3">
              {hasOutput && (
                <div className="rounded-md bg-secondary/50 p-3">
                  <p className="text-xs text-muted-foreground mb-1">Output:</p>
                  <pre className="text-xs overflow-auto max-h-32 whitespace-pre-wrap break-words font-mono">
                    {typeof step.output === "string"
                      ? step.output.length > 500
                        ? step.output.slice(0, 500) + "..."
                        : step.output
                      : JSON.stringify(step.output, null, 2)}
                  </pre>
                </div>
              )}
              {hasError && (
                <div className="rounded-md bg-red-500/10 p-3 border border-red-500/20">
                  <p className="text-xs text-red-400 mb-1">Error:</p>
                  <pre className="text-xs text-red-300 overflow-auto max-h-32 whitespace-pre-wrap break-words font-mono">
                    {step.error}
                  </pre>
                </div>
              )}
            </div>
          </CollapsibleContent>
        )}
      </Collapsible>
    </div>
  );
}

interface ExecutionSummaryProps {
  steps: StepResult[];
  startTime?: string;
}

function ExecutionSummary({ steps, startTime: _startTime }: ExecutionSummaryProps) {
  const stats = useMemo(() => {
    const completed = steps.filter((s) => s.status === "COMPLETED").length;
    const failed = steps.filter((s) => s.status === "FAILED").length;
    const running = steps.filter((s) => s.status === "RUNNING").length;
    const pending = steps.filter((s) => s.status === "PENDING").length;

    const totalDuration = steps.reduce((acc, s) => acc + (s.duration_ms || 0), 0);
    const totalTokens = steps.reduce((acc, s) => {
      const metrics = extractMetrics(s);
      return acc + (metrics?.tokens?.total || 0);
    }, 0);
    const totalCost = steps.reduce((acc, s) => {
      const metrics = extractMetrics(s);
      return acc + (metrics?.cost || 0);
    }, 0);

    return { completed, failed, running, pending, totalDuration, totalTokens, totalCost };
  }, [steps]);

  const progressPercent = steps.length > 0
    ? Math.round((stats.completed / steps.length) * 100)
    : 0;

  return (
    <div className="space-y-3 mb-4 p-3 rounded-lg bg-secondary/30">
      {/* Progress bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>
            {stats.completed}/{steps.length} steps completed
            {stats.running > 0 && ` (${stats.running} running)`}
          </span>
          <span>{progressPercent}%</span>
        </div>
        <Progress value={progressPercent} className="h-2" />
      </div>

      {/* Stats row */}
      <div className="flex flex-wrap gap-4 text-xs">
        <div className="flex items-center gap-1">
          <Clock className="h-3 w-3 text-muted-foreground" />
          <span>{formatDuration(stats.totalDuration)}</span>
        </div>
        {stats.totalTokens > 0 && (
          <div className="flex items-center gap-1">
            <Zap className="h-3 w-3 text-muted-foreground" />
            <span>{stats.totalTokens.toLocaleString()} tokens</span>
          </div>
        )}
        {stats.totalCost > 0 && (
          <div className="flex items-center gap-1">
            <Coins className="h-3 w-3 text-muted-foreground" />
            <span>{formatCost(stats.totalCost)}</span>
          </div>
        )}
        {stats.failed > 0 && (
          <div className="flex items-center gap-1 text-red-400">
            <AlertCircle className="h-3 w-3" />
            <span>{stats.failed} failed</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function ExecutionTimeline({
  steps,
  currentStepIndex: _currentStepIndex,
  showGanttView = true,
  startTime,
}: ExecutionTimelineProps) {
  // Calculate total duration for Gantt view
  const totalDuration = useMemo(() => {
    return steps.reduce((acc, s) => acc + (s.duration_ms || 0), 0);
  }, [steps]);

  // Calculate start offsets for each step
  const stepOffsets = useMemo(() => {
    const offsets: number[] = [];
    let cumulative = 0;
    for (const step of steps) {
      offsets.push(cumulative);
      cumulative += step.duration_ms || 0;
    }
    return offsets;
  }, [steps]);

  if (steps.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
        Waiting to start...
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <ExecutionSummary steps={steps} startTime={startTime} />

      <div className="space-y-1">
        {steps.map((step, index) => (
          <StepItem
            key={step.step_id}
            step={step}
            isLast={index === steps.length - 1}
            showGantt={showGanttView}
            totalDuration={totalDuration}
            startOffset={stepOffsets[index]}
          />
        ))}
      </div>
    </div>
  );
}
