"use client";

import { ArrowDown } from "lucide-react";
import { StepCard } from "./step-card";
import type { WorkflowStep } from "@/types/workflow";

interface StepListProps {
  steps: WorkflowStep[];
  missingAgents?: string[];
  onCreateAgent?: (agentId: string) => void;
}

export function StepList({
  steps,
  missingAgents = [],
  onCreateAgent,
}: StepListProps) {
  return (
    <div className="space-y-2">
      {steps.map((step, index) => {
        const agentExists =
          step.type !== "agent" ||
          !step.agent_id ||
          !missingAgents.includes(step.agent_id);

        return (
          <div key={step.id}>
            <StepCard
              step={step}
              index={index}
              agentExists={agentExists}
              onCreateAgent={
                !agentExists && step.agent_id
                  ? () => onCreateAgent?.(step.agent_id!)
                  : undefined
              }
            />
            {index < steps.length - 1 && (
              <div className="flex justify-center py-1">
                <ArrowDown className="h-4 w-4 text-muted-foreground" />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
