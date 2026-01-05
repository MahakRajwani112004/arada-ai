"use client";

import { Activity, CheckCircle2, Clock, Coins, TrendingDown, TrendingUp, Zap } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { AgentStats } from "@/types/agent";

interface StatsCardsProps {
  stats: AgentStats | undefined;
  isLoading: boolean;
}

function TrendBadge({ value, inverted = false }: { value: number; inverted?: boolean }) {
  // For latency, down is good (inverted)
  const isPositive = inverted ? value < 0 : value > 0;
  const isNeutral = Math.abs(value) < 1;

  if (isNeutral) {
    return (
      <span className="text-xs text-muted-foreground">
        —
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 text-xs font-medium",
        isPositive ? "text-emerald-500" : "text-red-500"
      )}
    >
      {isPositive ? (
        <TrendingUp className="h-3 w-3" />
      ) : (
        <TrendingDown className="h-3 w-3" />
      )}
      {Math.abs(value).toFixed(1)}%
    </span>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  trendInverted,
  className,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  trend?: number;
  trendInverted?: boolean;
  className?: string;
}) {
  return (
    <Card className={cn("relative overflow-hidden", className)}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
            <Icon className="h-4 w-4 text-muted-foreground" />
          </div>
          {trend !== undefined && (
            <TrendBadge value={trend} inverted={trendInverted} />
          )}
        </div>
        <div className="mt-3">
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          <p className="text-xs text-muted-foreground">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-8 rounded-lg" />
          <Skeleton className="h-4 w-12" />
        </div>
        <div className="mt-3 space-y-1">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-3 w-24" />
        </div>
      </CardContent>
    </Card>
  );
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard icon={Activity} label="Total Executions" value="0" />
        <StatCard icon={CheckCircle2} label="Success Rate" value="—" />
        <StatCard icon={Clock} label="Avg Latency" value="—" />
        <StatCard icon={Zap} label="Total Tokens" value="0" />
        <StatCard icon={Coins} label="Total Cost" value="$0.00" />
      </div>
    );
  }

  const formatLatency = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatCost = (cents: number) => {
    const dollars = cents / 100;
    if (dollars < 0.01) return `$${dollars.toFixed(4)}`;
    if (dollars < 1) return `$${dollars.toFixed(2)}`;
    return `$${dollars.toFixed(2)}`;
  };

  const formatTokens = (tokens: number) => {
    if (tokens < 1000) return tokens.toString();
    if (tokens < 1000000) return `${(tokens / 1000).toFixed(1)}k`;
    return `${(tokens / 1000000).toFixed(2)}M`;
  };

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <StatCard
        icon={Activity}
        label="Total Executions"
        value={stats.total_executions.toString()}
        trend={stats.executions_trend}
      />
      <StatCard
        icon={CheckCircle2}
        label="Success Rate"
        value={`${(stats.success_rate * 100).toFixed(1)}%`}
        trend={stats.success_trend}
        className={
          stats.success_rate >= 0.95
            ? "ring-1 ring-emerald-500/20"
            : stats.success_rate < 0.8
            ? "ring-1 ring-red-500/20"
            : undefined
        }
      />
      <StatCard
        icon={Clock}
        label="Avg Latency"
        value={formatLatency(stats.avg_latency_ms)}
        trend={stats.latency_trend}
        trendInverted
      />
      <StatCard
        icon={Zap}
        label="Total Tokens"
        value={formatTokens(stats.total_tokens)}
      />
      <StatCard
        icon={Coins}
        label="Total Cost"
        value={formatCost(stats.total_cost_cents)}
        trend={stats.cost_trend}
        trendInverted
      />
    </div>
  );
}
