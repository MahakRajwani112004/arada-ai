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
        workflow-node min-w-[100px] node-accent-muted transition-shadow
        ${selected ? "workflow-node-selected" : ""}
      `}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="workflow-handle !-top-1.5"
      />

      {/* Content */}
      <div className="p-2.5 flex items-center justify-center gap-2">
        <div className="node-icon h-7 w-7 node-icon-muted">
          <Flag className="h-3.5 w-3.5" />
        </div>
        <span className="text-sm font-medium text-muted-foreground">End</span>
      </div>
    </div>
  );
}

export const EndNode = memo(EndNodeComponent);
