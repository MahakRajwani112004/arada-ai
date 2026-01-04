"use client";

import {
  Bot,
  Brain,
  Search,
  Wrench,
  Server,
  Sparkles,
  Loader2,
  Check,
  X,
  Circle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ProgressItem, ProgressStatus } from "@/types/conversation";

interface ThinkingIndicatorProps {
  progress: ProgressItem[];
}

function StatusIcon({ status }: { status: ProgressStatus }) {
  switch (status) {
    case "pending":
      return <Circle className="h-3 w-3 text-muted-foreground" />;
    case "active":
      return <Loader2 className="h-3 w-3 text-primary animate-spin" />;
    case "complete":
      return <Check className="h-3 w-3 text-green-500" />;
    case "error":
      return <X className="h-3 w-3 text-red-500" />;
  }
}

function TypeIcon({ type }: { type: ProgressItem["type"] }) {
  switch (type) {
    case "thinking":
      return <Brain className="h-3 w-3" />;
    case "retrieving":
      return <Search className="h-3 w-3" />;
    case "tool":
      return <Wrench className="h-3 w-3" />;
    case "mcp":
      return <Server className="h-3 w-3" />;
    case "skill":
      return <Sparkles className="h-3 w-3" />;
    case "generating":
      return <Bot className="h-3 w-3" />;
  }
}

function getLabel(item: ProgressItem): string {
  switch (item.type) {
    case "thinking":
      return item.detail || "Understanding your request";
    case "retrieving":
      return item.name
        ? `Searching ${item.name}`
        : "Searching knowledge base";
    case "tool":
      return item.name ? `Calling ${item.name}` : "Executing tool";
    case "mcp":
      return item.name ? `Connecting to ${item.name}` : "Connecting to service";
    case "skill":
      return item.name ? `Applying ${item.name}` : "Applying skill";
    case "generating":
      return "Generating response";
  }
}

function ProgressRow({ item }: { item: ProgressItem }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <StatusIcon status={item.status} />
      <TypeIcon type={item.type} />
      <span
        className={cn(
          item.status === "active" && "text-foreground",
          item.status === "complete" && "text-muted-foreground",
          item.status === "pending" && "text-muted-foreground/50",
          item.status === "error" && "text-destructive"
        )}
      >
        {getLabel(item)}
      </span>
      {item.detail && item.status === "complete" && (
        <span className="text-xs text-muted-foreground">({item.detail})</span>
      )}
    </div>
  );
}

export function ThinkingIndicator({ progress }: ThinkingIndicatorProps) {
  if (progress.length === 0) return null;

  return (
    <div className="flex gap-3 p-4">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
        <Bot className="h-4 w-4 animate-pulse text-muted-foreground" />
      </div>

      {/* Progress */}
      <div className="flex-1 space-y-2">
        <p className="text-sm font-medium">Agent is working...</p>

        <div className="space-y-1.5 rounded-lg border border-border bg-muted/30 p-3">
          {progress.map((item, i) => (
            <ProgressRow key={i} item={item} />
          ))}
        </div>
      </div>
    </div>
  );
}
