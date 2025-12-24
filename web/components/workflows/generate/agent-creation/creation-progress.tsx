"use client";

import { Check, Circle } from "lucide-react";

interface CreationProgressProps {
  totalAgents: number;
  createdCount: number;
  skippedCount: number;
  currentAgentName?: string;
}

export function CreationProgress({
  totalAgents,
  createdCount,
  skippedCount,
  currentAgentName,
}: CreationProgressProps) {
  const processedCount = createdCount + skippedCount;
  const progressPercent = totalAgents > 0 ? (processedCount / totalAgents) * 100 : 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          {processedCount} of {totalAgents} agents processed
        </span>
        <div className="flex items-center gap-4">
          {createdCount > 0 && (
            <span className="flex items-center gap-1 text-green-400">
              <Check className="h-3 w-3" />
              {createdCount} created
            </span>
          )}
          {skippedCount > 0 && (
            <span className="flex items-center gap-1 text-muted-foreground">
              <Circle className="h-3 w-3" />
              {skippedCount} skipped
            </span>
          )}
        </div>
      </div>

      <div className="h-2 rounded-full bg-secondary overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-300"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {currentAgentName && processedCount < totalAgents && (
        <p className="text-sm text-muted-foreground">
          Currently creating: <span className="font-medium text-foreground">{currentAgentName}</span>
        </p>
      )}
    </div>
  );
}
