"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { Flag } from "lucide-react";

interface EndNodeProps {
  selected?: boolean;
}

function EndNodeComponent({ selected }: EndNodeProps) {
  return (
    <div
      className={`
        relative rounded-lg border-2 bg-card px-4 py-2.5 shadow-sm transition-all min-w-[120px]
        ${selected ? "border-primary ring-2 ring-primary/20" : "border-border"}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="!h-3 !w-3 !border-2 !border-background !bg-primary"
      />

      {/* Content */}
      <div className="flex items-center justify-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
          <Flag className="h-4 w-4 text-muted-foreground" />
        </div>
        <span className="text-sm font-medium text-muted-foreground">End</span>
      </div>
    </div>
  );
}

export const EndNode = memo(EndNodeComponent);
