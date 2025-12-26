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
        relative rounded-lg border-2 bg-card px-4 py-3 shadow-sm transition-all min-w-[260px]
        ${selected ? "border-primary ring-2 ring-primary/20" : "border-border"}
        ${isWebhook ? "border-yellow-500/50" : "border-green-500/50"}
      `}
    >
      {/* Icon and Title */}
      <div className="flex items-center gap-3">
        <div
          className={`
            flex h-10 w-10 shrink-0 items-center justify-center rounded-lg
            ${isWebhook ? "bg-yellow-500/10" : "bg-green-500/10"}
          `}
        >
          {isWebhook ? (
            <Zap className="h-5 w-5 text-yellow-500" />
          ) : (
            <Play className="h-5 w-5 text-green-500" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="font-medium text-sm">
            {isWebhook ? "Webhook Trigger" : "Manual Trigger"}
          </div>
          <div className="text-xs text-muted-foreground">
            {isWebhook ? "Activated by external HTTP call" : "Run manually"}
          </div>
        </div>
      </div>

      {/* Webhook URL display */}
      {isWebhook && data.webhookUrl && (
        <div className="mt-3 flex items-center gap-2">
          <code className="flex-1 truncate rounded bg-muted px-2 py-1 text-xs">
            {data.webhookUrl}
          </code>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 shrink-0"
            onClick={handleCopyUrl}
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      )}

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-4 !w-4 !border-2 !border-background !bg-primary hover:!bg-primary/80 hover:!scale-125 transition-all !-bottom-2"
      />
    </div>
  );
}

export const TriggerNode = memo(TriggerNodeComponent);
