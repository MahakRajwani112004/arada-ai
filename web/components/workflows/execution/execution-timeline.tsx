"use client";

import { Check, X, Loader2, Clock, ChevronDown } from "lucide-react";
import { useState } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { StepResult, StepExecutionStatus } from "@/types/workflow";

interface ExecutionTimelineProps {
  steps: StepResult[];
  currentStepIndex?: number;
}

function getStepStatusIcon(status: StepExecutionStatus) {
  switch (status) {
    case "completed":
      return <Check className="h-4 w-4 text-green-400" />;
    case "failed":
      return <X className="h-4 w-4 text-red-400" />;
    case "running":
      return <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />;
    case "pending":
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />;
  }
}

function formatDuration(ms: number | undefined): string {
  if (ms === undefined) return "";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function StepItem({ step, isLast }: { step: StepResult; isLast: boolean }) {
  const [isOpen, setIsOpen] = useState(false);
  const hasOutput = step.output !== undefined;
  const hasError = step.error !== undefined;

  return (
    <div className="relative">
      {/* Connector line */}
      {!isLast && (
        <div className="absolute left-[15px] top-8 h-full w-px bg-border" />
      )}

      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger className="w-full">
          <div
            className={`flex items-center gap-3 rounded-lg p-3 transition-colors hover:bg-secondary/50 ${
              step.status === "running" ? "bg-blue-500/5" : ""
            }`}
          >
            {/* Status icon */}
            <div
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                step.status === "completed"
                  ? "bg-green-500/20"
                  : step.status === "failed"
                  ? "bg-red-500/20"
                  : step.status === "running"
                  ? "bg-blue-500/20"
                  : "bg-secondary"
              }`}
            >
              {getStepStatusIcon(step.status)}
            </div>

            {/* Step info */}
            <div className="flex-1 min-w-0 text-left">
              <div className="flex items-center gap-2">
                <span className="font-medium truncate">{step.step_id}</span>
                {step.status === "running" && (
                  <span className="text-xs text-blue-400">(running)</span>
                )}
              </div>
              {step.duration_ms !== undefined && (
                <span className="text-xs text-muted-foreground">
                  {formatDuration(step.duration_ms)}
                </span>
              )}
            </div>

            {/* Expand indicator */}
            {(hasOutput || hasError) && (
              <ChevronDown
                className={`h-4 w-4 text-muted-foreground transition-transform ${
                  isOpen ? "rotate-180" : ""
                }`}
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
                  <pre className="text-xs overflow-auto max-h-32 whitespace-pre-wrap break-words">
                    {typeof step.output === "string"
                      ? step.output
                      : JSON.stringify(step.output, null, 2)}
                  </pre>
                </div>
              )}
              {hasError && (
                <div className="rounded-md bg-red-500/10 p-3 border border-red-500/20">
                  <p className="text-xs text-red-400 mb-1">Error:</p>
                  <pre className="text-xs text-red-300 overflow-auto max-h-32 whitespace-pre-wrap break-words">
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

export function ExecutionTimeline({ steps }: ExecutionTimelineProps) {
  if (steps.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        Waiting to start...
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {steps.map((step, index) => (
        <StepItem
          key={step.step_id}
          step={step}
          isLast={index === steps.length - 1}
        />
      ))}
    </div>
  );
}
