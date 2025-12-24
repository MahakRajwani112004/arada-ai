"use client";

import { Check, AlertTriangle, ArrowDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { GenerateWorkflowResponse } from "@/types/workflow";
import type { StepType } from "@/types/workflow";

interface AIReviewPanelProps {
  response: GenerateWorkflowResponse;
}

const stepTypeConfig: Record<
  StepType,
  { label: string; color: string }
> = {
  agent: {
    label: "Agent",
    color: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  },
  parallel: {
    label: "Parallel",
    color: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  },
  conditional: {
    label: "Conditional",
    color: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  },
  loop: {
    label: "Loop",
    color: "bg-teal-500/10 text-teal-400 border-teal-500/20",
  },
  tool: {
    label: "Tool",
    color: "bg-green-500/10 text-green-400 border-green-500/20",
  },
};

export function AIReviewPanel({ response }: AIReviewPanelProps) {
  const { workflow } = response;
  const ready_steps = response.ready_steps ?? [];
  const blocked_steps = response.blocked_steps ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{workflow.name || "Generated Workflow"}</CardTitle>
        {workflow.description && (
          <p className="text-sm text-muted-foreground">{workflow.description}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {(workflow.steps ?? []).map((step, index) => {
          const isReady = ready_steps.includes(step.id);
          const isBlocked = blocked_steps.includes(step.id);
          const config = stepTypeConfig[step.type] || stepTypeConfig.agent;

          return (
            <div key={step.id}>
              <div
                className={`flex items-center gap-3 rounded-lg border p-3 transition-colors ${
                  isBlocked
                    ? "border-amber-500/50 bg-amber-500/5"
                    : "border-border"
                }`}
              >
                {/* Status indicator */}
                <div
                  className={`flex h-7 w-7 items-center justify-center rounded-full ${
                    isBlocked
                      ? "bg-amber-500/20"
                      : "bg-gradient-to-br from-purple-500/20 to-blue-500/20"
                  }`}
                >
                  {isBlocked ? (
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                  ) : (
                    <Check className="h-3.5 w-3.5 text-green-400" />
                  )}
                </div>

                {/* Step info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      {index + 1}.
                    </span>
                    <span className="font-medium truncate">{step.id}</span>
                    <Badge variant="outline" className={`text-xs ${config.color}`}>
                      {config.label}
                    </Badge>
                  </div>
                  {step.type === "agent" && step.agent_id && (
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                      <span>agent: {step.agent_id}</span>
                      {isReady && (
                        <span className="text-green-400">exists</span>
                      )}
                      {isBlocked && (
                        <span className="text-amber-400">needs creation</span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Arrow connector */}
              {index < workflow.steps.length - 1 && (
                <div className="flex justify-center py-1">
                  <ArrowDown className="h-4 w-4 text-muted-foreground" />
                </div>
              )}
            </div>
          );
        })}

        {/* Summary */}
        <div className="mt-4 rounded-md bg-secondary/50 p-3 text-sm">
          <p className="text-muted-foreground">{response.explanation}</p>
        </div>

        {/* Warnings */}
        {response.warnings && response.warnings.length > 0 && (
          <div className="space-y-2">
            {response.warnings.map((warning, index) => (
              <div
                key={index}
                className="flex items-start gap-2 rounded-md bg-amber-500/10 px-3 py-2 text-sm text-amber-400"
              >
                <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                <span>{warning}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
