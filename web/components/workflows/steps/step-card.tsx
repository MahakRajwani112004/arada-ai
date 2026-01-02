"use client";

import {
  Bot,
  GitBranch,
  Repeat,
  Split,
  Wrench,
  Check,
  AlertTriangle,
  ChevronDown,
  UserCheck,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { WorkflowStep, StepType } from "@/types/workflow";
import { useState } from "react";

interface StepCardProps {
  step: WorkflowStep;
  index: number;
  agentExists?: boolean;
  onCreateAgent?: () => void;
}

const stepTypeConfig: Record<
  StepType,
  { label: string; icon: React.ReactNode; color: string }
> = {
  agent: {
    label: "Agent",
    icon: <Bot className="h-4 w-4" />,
    color: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  },
  parallel: {
    label: "Parallel",
    icon: <Split className="h-4 w-4" />,
    color: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  },
  conditional: {
    label: "Conditional",
    icon: <GitBranch className="h-4 w-4" />,
    color: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  },
  loop: {
    label: "Loop",
    icon: <Repeat className="h-4 w-4" />,
    color: "bg-teal-500/10 text-teal-400 border-teal-500/20",
  },
  tool: {
    label: "Tool",
    icon: <Wrench className="h-4 w-4" />,
    color: "bg-green-500/10 text-green-400 border-green-500/20",
  },
  approval: {
    label: "Approval",
    icon: <UserCheck className="h-4 w-4" />,
    color: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  },
};

export function StepCard({
  step,
  index,
  agentExists = true,
  onCreateAgent,
}: StepCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const config = stepTypeConfig[step.type] || stepTypeConfig.agent;
  const isBlocked = step.type === "agent" && !agentExists;

  return (
    <Card
      className={`transition-all ${
        isBlocked
          ? "border-amber-500/50 bg-amber-500/5"
          : "hover:border-primary/30"
      }`}
    >
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <CardContent className="flex cursor-pointer items-center justify-between p-4">
            <div className="flex items-center gap-3">
              {/* Status indicator */}
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full ${
                  isBlocked
                    ? "bg-amber-500/20"
                    : "bg-gradient-to-br from-purple-500/20 to-blue-500/20"
                }`}
              >
                {isBlocked ? (
                  <AlertTriangle className="h-4 w-4 text-amber-400" />
                ) : (
                  <Check className="h-4 w-4 text-green-400" />
                )}
              </div>

              {/* Step info */}
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    {index + 1}.
                  </span>
                  <span className="font-medium">{step.id}</span>
                  <Badge variant="outline" className={`gap-1 ${config.color}`}>
                    {config.icon}
                    {config.label}
                  </Badge>
                </div>
                {step.type === "agent" && step.agent_id && (
                  <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
                    <span>agent: {step.agent_id}</span>
                    {agentExists ? (
                      <span className="text-green-400">exists</span>
                    ) : (
                      <span className="text-amber-400">not found</span>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              {isBlocked && onCreateAgent && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    onCreateAgent();
                  }}
                  className="text-amber-400 border-amber-500/30 hover:bg-amber-500/10"
                >
                  Create Agent
                </Button>
              )}
              <ChevronDown
                className={`h-4 w-4 text-muted-foreground transition-transform ${
                  isOpen ? "rotate-180" : ""
                }`}
              />
            </div>
          </CardContent>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="border-t border-border px-4 py-3">
            <div className="grid gap-3 text-sm">
              {step.input && (
                <div>
                  <span className="text-muted-foreground">Input: </span>
                  <code className="rounded bg-secondary px-1.5 py-0.5 text-xs">
                    {step.input}
                  </code>
                </div>
              )}
              <div className="flex gap-4">
                <div>
                  <span className="text-muted-foreground">Timeout: </span>
                  <span>{step.timeout}s</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Retries: </span>
                  <span>{step.retries}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">On error: </span>
                  <span>{step.on_error}</span>
                </div>
              </div>
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
