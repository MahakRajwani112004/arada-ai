"use client";

import { useEffect } from "react";
import { X, StopCircle, Loader2 } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ExecutionTimeline } from "./execution-timeline";
import { ExecutionComplete } from "./execution-complete";
import { useWorkflowExecution } from "@/lib/hooks/use-workflows";
import type { ExecutionStatus } from "@/types/workflow";

interface ExecutionPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  executionId: string | null;
  workflowName?: string;
  onRunAgain?: () => void;
}

function getStatusLabel(status: ExecutionStatus): string {
  switch (status) {
    case "RUNNING":
      return "Running";
    case "COMPLETED":
      return "Completed";
    case "FAILED":
      return "Failed";
    case "CANCELLED":
      return "Cancelled";
    default:
      return "Unknown";
  }
}

export function ExecutionPanel({
  open,
  onOpenChange,
  executionId,
  workflowName,
  onRunAgain,
}: ExecutionPanelProps) {
  const { data: execution, isLoading } = useWorkflowExecution(
    executionId || "",
    { poll: true }
  );

  // Stop polling when execution is complete
  const isComplete =
    execution?.status === "COMPLETED" ||
    execution?.status === "FAILED" ||
    execution?.status === "CANCELLED";

  // Calculate progress - step_results is a Record<string, StepResult>, not an array
  const stepResultsValues = execution?.step_results
    ? Object.values(execution.step_results)
    : [];
  const totalSteps = stepResultsValues.length;
  const completedSteps = stepResultsValues.filter(
    (s) => s.status === "COMPLETED"
  ).length;
  const progressPercent = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  // Auto-close polling if not needed
  useEffect(() => {
    if (!open) return;
    // Polling is handled by the hook
  }, [open, isComplete]);

  if (!executionId) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader className="space-y-1">
          <div className="flex items-center justify-between">
            <SheetTitle className="flex items-center gap-2">
              Workflow Execution
              {execution?.status === "RUNNING" && (
                <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
              )}
            </SheetTitle>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => onOpenChange(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          {workflowName && (
            <p className="text-sm text-muted-foreground">{workflowName}</p>
          )}
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {execution && (
            <>
              {/* Status & Progress */}
              {!isComplete && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                      {getStatusLabel(execution.status)}
                    </span>
                    <span className="text-muted-foreground">
                      Step {completedSteps + 1} of {totalSteps}
                    </span>
                  </div>
                  <Progress value={progressPercent} className="h-2" />
                </div>
              )}

              {/* Timeline */}
              {stepResultsValues.length > 0 && (
                <div className="border rounded-lg p-4">
                  <ExecutionTimeline
                    steps={stepResultsValues}
                    currentStepIndex={completedSteps}
                  />
                </div>
              )}

              {/* Complete State */}
              {isComplete && (
                <ExecutionComplete
                  status={execution.status}
                  durationMs={execution.duration_ms}
                  onRunAgain={onRunAgain}
                  onViewDetails={() => onOpenChange(false)}
                />
              )}

              {/* Stop Button */}
              {execution.status === "RUNNING" && (
                <Button
                  variant="destructive"
                  className="w-full gap-2"
                  onClick={() => {
                    // TODO: Implement cancel execution
                    console.log("Cancel execution");
                  }}
                >
                  <StopCircle className="h-4 w-4" />
                  Stop Execution
                </Button>
              )}

              {/* Duration */}
              {!isComplete && execution.started_at && (
                <p className="text-center text-xs text-muted-foreground">
                  Started {new Date(execution.started_at).toLocaleTimeString()}
                </p>
              )}
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
