"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { LogEntry } from "@/types/monitoring";

interface LogsTableProps {
  logs: LogEntry[];
  isLoading?: boolean;
}

const levelColors: Record<string, string> = {
  error: "bg-red-500/10 text-red-500 border-red-500/20",
  warning: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
  info: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  debug: "bg-gray-500/10 text-gray-500 border-gray-500/20",
};

const serviceColors: Record<string, string> = {
  api: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  worker: "bg-green-500/10 text-green-500 border-green-500/20",
  web: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  temporal: "bg-orange-500/10 text-orange-500 border-orange-500/20",
  postgres: "bg-cyan-500/10 text-cyan-500 border-cyan-500/20",
  redis: "bg-red-500/10 text-red-500 border-red-500/20",
};

function LogRow({ log }: { log: LogEntry }) {
  const [isOpen, setIsOpen] = useState(false);
  const timestamp = new Date(log.timestamp).toLocaleString();
  const levelColor = levelColors[log.level || "info"] || levelColors.info;
  const serviceColor = serviceColors[log.service] || "bg-gray-500/10 text-gray-500 border-gray-500/20";

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <div
          className={cn(
            "flex items-start gap-3 p-3 hover:bg-accent/50 cursor-pointer border-b border-border/50 transition-colors",
            isOpen && "bg-accent/30"
          )}
        >
          <div className="mt-1">
            {isOpen ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-muted-foreground font-mono">
                {timestamp}
              </span>
              <Badge variant="outline" className={cn("text-xs", serviceColor)}>
                {log.service}
              </Badge>
              {log.level && (
                <Badge variant="outline" className={cn("text-xs", levelColor)}>
                  {log.level}
                </Badge>
              )}
            </div>
            <p className="text-sm font-mono truncate text-foreground">
              {log.message}
            </p>
          </div>
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div className="px-10 py-3 bg-accent/20 border-b border-border">
          <pre className="text-xs font-mono whitespace-pre-wrap break-all text-muted-foreground">
            {log.message}
          </pre>
          {Object.keys(log.labels).length > 0 && (
            <div className="mt-3 pt-3 border-t border-border/50">
              <p className="text-xs font-medium text-muted-foreground mb-2">
                Labels
              </p>
              <div className="flex flex-wrap gap-1">
                {Object.entries(log.labels).map(([key, value]) => (
                  <Badge
                    key={key}
                    variant="secondary"
                    className="text-xs font-mono"
                  >
                    {key}: {value}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

export function LogsTable({ logs, isLoading }: LogsTableProps) {
  if (isLoading) {
    return (
      <Card className="overflow-hidden">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="flex items-start gap-3 p-3 border-b border-border/50">
            <Skeleton className="h-4 w-4 mt-1" />
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-5 w-16" />
                <Skeleton className="h-5 w-12" />
              </div>
              <Skeleton className="h-4 w-full" />
            </div>
          </div>
        ))}
      </Card>
    );
  }

  if (logs.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-muted-foreground">No logs found</p>
        <p className="text-sm text-muted-foreground mt-1">
          Try adjusting your filters or time range
        </p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      {logs.map((log, index) => (
        <LogRow key={`${log.timestamp}-${index}`} log={log} />
      ))}
    </Card>
  );
}
