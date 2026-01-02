"use client";

import { Play, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TriggerType } from "@/types/workflow";

interface TriggerSelectorProps {
  value: TriggerType;
  onChange: (type: TriggerType) => void;
}

const triggers: { type: TriggerType; label: string; description: string; icon: typeof Play }[] = [
  {
    type: "manual",
    label: "Manual",
    description: "Started via chat, API, or Run button",
    icon: Play,
  },
  {
    type: "webhook",
    label: "Webhook",
    description: "Triggered by external HTTP POST",
    icon: Zap,
  },
];

export function TriggerSelector({ value, onChange }: TriggerSelectorProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {triggers.map(({ type, label, description, icon: Icon }) => (
        <button
          key={type}
          onClick={() => onChange(type)}
          className={cn(
            "flex items-start gap-3 p-3 rounded-lg border text-left transition-colors",
            value === type
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/50 hover:bg-muted/50"
          )}
        >
          <div
            className={cn(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-md",
              value === type ? "bg-primary text-primary-foreground" : "bg-muted"
            )}
          >
            <Icon className="h-4 w-4" />
          </div>
          <div className="space-y-0.5">
            <p className="font-medium text-sm">{label}</p>
            <p className="text-xs text-muted-foreground">{description}</p>
          </div>
        </button>
      ))}
    </div>
  );
}
