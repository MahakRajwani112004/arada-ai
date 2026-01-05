"use client";

import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { AgentUsageHistory, UsageDataPoint } from "@/types/agent";

interface UsageChartProps {
  data: AgentUsageHistory | undefined;
  isLoading: boolean;
}

function SimpleBarChart({ data }: { data: UsageDataPoint[] }) {
  if (data.length === 0) {
    return (
      <div className="flex h-[200px] items-center justify-center text-muted-foreground">
        <div className="text-center">
          <BarChart3 className="mx-auto h-10 w-10 mb-2 opacity-50" />
          <p className="text-sm">No execution data yet</p>
          <p className="text-xs">Run your agent to see usage trends</p>
        </div>
      </div>
    );
  }

  const maxExecutions = Math.max(...data.map((d) => d.executions), 1);

  return (
    <div className="h-[200px] flex items-end gap-1">
      {data.map((point, index) => {
        const height = (point.executions / maxExecutions) * 100;
        const successHeight = (point.successful / maxExecutions) * 100;
        const date = new Date(point.timestamp);
        const label = date.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        });

        return (
          <div key={index} className="flex-1 flex flex-col items-center group">
            <div className="relative w-full flex-1 flex items-end justify-center">
              {/* Failed bar (background) */}
              <div
                className="absolute bottom-0 w-full max-w-[40px] rounded-t bg-red-500/20 transition-all"
                style={{ height: `${height}%` }}
              />
              {/* Success bar (foreground) */}
              <div
                className="absolute bottom-0 w-full max-w-[40px] rounded-t bg-emerald-500/80 transition-all"
                style={{ height: `${successHeight}%` }}
              />
              {/* Tooltip */}
              <div className="absolute -top-16 left-1/2 -translate-x-1/2 bg-popover border rounded-md px-2 py-1 text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 shadow-md">
                <p className="font-medium">{label}</p>
                <p className="text-emerald-500">{point.successful} successful</p>
                <p className="text-red-500">{point.failed} failed</p>
              </div>
            </div>
            {/* X-axis label - show every other one on small screens */}
            <span
              className={cn(
                "text-[10px] text-muted-foreground mt-1",
                index % 2 !== 0 && data.length > 10 && "hidden sm:block"
              )}
            >
              {date.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function UsageChart({ data, isLoading }: UsageChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Usage Trend</CardTitle>
          <CardDescription>Executions over time</CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[200px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const totalExecutions = data?.data.reduce((sum, d) => sum + d.executions, 0) ?? 0;
  const totalSuccessful = data?.data.reduce((sum, d) => sum + d.successful, 0) ?? 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Usage Trend</CardTitle>
            <CardDescription>
              {totalExecutions} executions ({totalSuccessful} successful)
            </CardDescription>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-muted-foreground">Successful</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="h-2 w-2 rounded-full bg-red-500/50" />
              <span className="text-muted-foreground">Failed</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <SimpleBarChart data={data?.data ?? []} />
      </CardContent>
    </Card>
  );
}
