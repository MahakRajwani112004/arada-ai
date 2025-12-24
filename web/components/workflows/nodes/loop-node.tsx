"use client";

import { memo } from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { WorkflowNodeData } from "@/types/workflow";

function LoopNode({ data, selected }: NodeProps<WorkflowNodeData>) {
  const stepCount = data.loopSteps?.length || 0;

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
        <div className="p-2 rounded-md bg-emerald-100 dark:bg-emerald-900/30">
          <RefreshCw className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs text-muted-foreground font-medium">Loop</div>
          <div className="font-medium text-sm">
            Max {data.maxIterations || 5} iterations
          </div>
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-border/50">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Inner steps:</span>
          <span className="font-medium">{stepCount}</span>
        </div>
        {data.exitCondition && (
          <div className="mt-1 text-xs text-muted-foreground truncate">
            Exit: {data.exitCondition}
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-primary !w-3 !h-3 !border-2 !border-background"
      />
    </div>
  );
}

export default memo(LoopNode);
