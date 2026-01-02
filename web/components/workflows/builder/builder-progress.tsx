"use client";

import { Check } from "lucide-react";
import type { GenerationWizardStep } from "@/types/agent-suggestion";

interface BuilderProgressProps {
  currentStep: GenerationWizardStep;
  hasAgentsToCreate: boolean;
}

const steps: { id: GenerationWizardStep; label: string }[] = [
  { id: "describe", label: "Describe" },
  { id: "review", label: "Review" },
  { id: "create_agents", label: "Create Agents" },
  { id: "save", label: "Save" },
];

export function BuilderProgress({ currentStep, hasAgentsToCreate }: BuilderProgressProps) {
  // Filter out "loading" as it's not a visible step
  // Also filter out "create_agents" if there are no agents to create
  const visibleSteps = steps.filter((step) => {
    if (step.id === "create_agents" && !hasAgentsToCreate) {
      return false;
    }
    return true;
  });

  const currentIndex = visibleSteps.findIndex((step) => step.id === currentStep);

  return (
    <div className="flex items-center justify-center gap-2">
      {visibleSteps.map((step, index) => {
        const isCompleted = index < currentIndex;
        const isCurrent = step.id === currentStep || (currentStep === "loading" && step.id === "describe");

        return (
          <div key={step.id} className="flex items-center">
            <div className="flex items-center gap-2">
              <div
                className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium transition-colors ${
                  isCompleted
                    ? "bg-green-500 text-white"
                    : isCurrent
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-muted-foreground"
                }`}
              >
                {isCompleted ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  index + 1
                )}
              </div>
              <span
                className={`text-sm ${
                  isCurrent ? "font-medium text-foreground" : "text-muted-foreground"
                }`}
              >
                {step.label}
              </span>
            </div>
            {index < visibleSteps.length - 1 && (
              <div
                className={`mx-3 h-px w-8 ${
                  isCompleted ? "bg-green-500" : "bg-border"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
