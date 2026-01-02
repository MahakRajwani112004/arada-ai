"use client";

import { memo, useState } from "react";
import { Handle, Position } from "@xyflow/react";
import { Play, Zap, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { TriggerNodeData } from "@/lib/workflow-canvas/types";

interface TriggerNodeProps {
  data: TriggerNodeData;
  selected?: boolean;
}

function TriggerNodeComponent({ data, selected }: TriggerNodeProps) {
  const [copied, setCopied] = useState(false);
  const isWebhook = data.triggerType === "webhook";

  const handleCopyUrl = async () => {
    if (data.webhookUrl) {
      await navigator.clipboard.writeText(data.webhookUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div
      className={`
        workflow-node min-w-[240px] transition-shadow
        ${isWebhook ? "node-accent-yellow" : "node-accent-green"}
        ${selected ? "workflow-node-selected" : ""}
      `}
    >
      <div className="p-3">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className={`node-icon h-9 w-9 ${isWebhook ? "node-icon-yellow" : "node-icon-green"}`}>
            {isWebhook ? (
              <Zap className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-medium text-sm">
              {isWebhook ? "Webhook Trigger" : "Manual Trigger"}
            </div>
            <div className="text-xs text-muted-foreground">
              {isWebhook ? "HTTP endpoint" : "Run manually"}
            </div>
          </div>
        </div>

        {/* Webhook URL */}
        {isWebhook && data.webhookUrl && (
          <div className="mt-3 flex items-center gap-2">
            <code className="flex-1 truncate rounded bg-muted px-2 py-1 text-[11px] font-mono text-muted-foreground">
              {data.webhookUrl}
            </code>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 shrink-0"
              onClick={handleCopyUrl}
            >
              {copied ? (
                <Check className="h-3 w-3 text-green-500" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>
          </div>
        )}
      </div>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="workflow-handle !-bottom-1.5"
      />
    </div>
  );
}

export const TriggerNode = memo(TriggerNodeComponent);
