"use client";

import { AlertTriangle, Check, Loader2, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { SuggestedAgent } from "@/types/workflow";

interface DraftAgent {
  nodeId: string;
  suggestion: SuggestedAgent;
}

interface CanvasStatusBarProps {
  nodeCount: number;
  draftCount: number;
  draftAgents: DraftAgent[];
  onCreateAll: () => void;
  isCreating: boolean;
}

export function CanvasStatusBar({
  nodeCount,
  draftCount,
  draftAgents,
  onCreateAll,
  isCreating,
}: CanvasStatusBarProps) {
  const allReady = draftCount === 0;

  return (
    <div className="h-12 border-t border-border bg-card flex items-center justify-between px-4 shrink-0">
      {/* Left side - status */}
      <div className="flex items-center gap-4 text-sm">
        {allReady ? (
          <div className="flex items-center gap-2 text-green-500">
            <Check className="h-4 w-4" />
            <span>All agents ready</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-orange-500">
            <AlertTriangle className="h-4 w-4" />
            <span>{draftCount} agent{draftCount !== 1 ? "s" : ""} need to be created</span>
          </div>
        )}

        <div className="text-muted-foreground">
          {nodeCount} node{nodeCount !== 1 ? "s" : ""}
        </div>
      </div>

      {/* Right side - batch action */}
      {draftCount > 0 && draftAgents.length > 0 && (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {draftAgents.slice(0, 3).map((draft) => (
              <div
                key={draft.nodeId}
                className="flex items-center gap-1 px-2 py-1 rounded bg-secondary"
                title={draft.suggestion.goal}
              >
                <Bot className="h-3 w-3" />
                <span className="max-w-[120px] truncate">{draft.suggestion.name}</span>
              </div>
            ))}
            {draftAgents.length > 3 && (
              <span>+{draftAgents.length - 3} more</span>
            )}
          </div>
          <Button
            size="sm"
            onClick={onCreateAll}
            disabled={isCreating}
          >
            {isCreating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                Create All Agents
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
