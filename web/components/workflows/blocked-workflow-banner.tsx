"use client";

import { AlertTriangle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface BlockedWorkflowBannerProps {
  missingAgents: string[];
  onCreateAgents?: () => void;
}

export function BlockedWorkflowBanner({
  missingAgents,
  onCreateAgents,
}: BlockedWorkflowBannerProps) {
  if (missingAgents.length === 0) return null;

  return (
    <div className="rounded-lg border border-amber-500/50 bg-amber-500/10 p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-500/20">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
        </div>
        <div className="flex-1">
          <h4 className="font-medium text-amber-400">
            This workflow cannot run yet
          </h4>
          <p className="mt-1 text-sm text-muted-foreground">
            {missingAgents.length} agent
            {missingAgents.length > 1 ? "s need" : " needs"} to be created:
          </p>
          <ul className="mt-2 space-y-1">
            {missingAgents.map((agentId) => (
              <li key={agentId} className="text-sm text-muted-foreground">
                <span className="mr-2">-</span>
                <code className="rounded bg-secondary px-1.5 py-0.5 text-xs">
                  {agentId}
                </code>
              </li>
            ))}
          </ul>
        </div>
        {onCreateAgents && (
          <Button
            variant="outline"
            size="sm"
            onClick={onCreateAgents}
            className="shrink-0 gap-2 border-amber-500/30 text-amber-400 hover:bg-amber-500/10"
          >
            Create Missing Agent{missingAgents.length > 1 ? "s" : ""}
            <ArrowRight className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
