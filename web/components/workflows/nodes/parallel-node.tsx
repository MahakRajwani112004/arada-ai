"use client";

import { memo } from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";
import { GitBranch } from "lucide-react";
import { cn } from "@/lib/utils";
import { WorkflowNodeData } from "@/types/workflow";

function ParallelNode({ data, selected }: NodeProps<WorkflowNodeData>) {
  const branchCount = data.branches?.length || 0;

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
        <div className="p-2 rounded-md bg-purple-100 dark:bg-purple-900/30">
          <GitBranch className="h-4 w-4 text-purple-600 dark:text-purple-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs text-muted-foreground font-medium">Parallel</div>
          <div className="font-medium text-sm">
            {branchCount} {branchCount === 1 ? "branch" : "branches"}
          </div>
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-border/50">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Aggregation:</span>
          <span className="font-medium capitalize">{data.aggregation || "all"}</span>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-primary !w-3 !h-3 !border-2 !border-background"
      />
    </div>
  );
}

export default memo(ParallelNode);
