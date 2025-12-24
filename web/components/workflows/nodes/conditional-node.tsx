"use client";

import { memo } from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";
import { GitFork } from "lucide-react";
import { cn } from "@/lib/utils";
import { WorkflowNodeData } from "@/types/workflow";

function ConditionalNode({ data, selected }: NodeProps<WorkflowNodeData>) {
  const branchCount = Object.keys(data.conditionalBranches || {}).length;

  return (
    <div
      className={cn(
        "px-4 py-3 rounded-lg border-2 bg-card min-w-[180px] shadow-sm transition-all",
        selected ? "border-primary shadow-md" : "border-border hover:border-primary/40"
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-primary !w-3 !h-3 !border-2 !border-background"
      />

      <div className="flex items-center gap-3">
        <div className="p-2 rounded-md bg-amber-100 dark:bg-amber-900/30">
          <GitFork className="h-4 w-4 text-amber-600 dark:text-amber-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs text-muted-foreground font-medium">Conditional</div>
          <div className="font-medium text-sm">
            {branchCount} {branchCount === 1 ? "route" : "routes"}
          </div>
        </div>
      </div>

      {data.conditionSource && (
        <div className="mt-2 pt-2 border-t border-border/50">
          <div className="text-xs text-muted-foreground truncate">
            {data.conditionSource}
          </div>
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-primary !w-3 !h-3 !border-2 !border-background"
      />
    </div>
  );
}

export default memo(ConditionalNode);
