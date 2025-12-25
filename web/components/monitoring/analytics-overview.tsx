"use client";

import { StatsCard, StatsCardSkeleton } from "./stats-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Zap,
  DollarSign,
  Clock,
  CheckCircle,
  Bot,
  Cpu,
  MessageSquare,
  TrendingUp,
} from "lucide-react";
import type { LLMUsageStats, AgentStats } from "@/types/monitoring";

interface AnalyticsOverviewProps {
  llmStats?: LLMUsageStats;
  agentStats?: AgentStats;
  isLoading?: boolean;
}

function formatCost(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
}

function formatLatency(ms: number): string {
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(2)}s`;
  }
  return `${Math.round(ms)}ms`;
}

export function AnalyticsOverview({
  llmStats,
  agentStats,
  isLoading,
}: AnalyticsOverviewProps) {
  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* LLM Stats Skeleton */}
        <div>
          <h3 className="text-lg font-semibold mb-4">LLM Usage</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <StatsCardSkeleton key={i} />
            ))}
          </div>
        </div>

        {/* Agent Stats Skeleton */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Agent Executions</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <StatsCardSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* LLM Stats */}
      {llmStats && (
        <div>
          <h3 className="text-lg font-semibold mb-4">LLM Usage (Last 7 Days)</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatsCard
              title="Total Requests"
              value={formatNumber(llmStats.total_requests)}
              icon={MessageSquare}
              description={`${formatNumber(llmStats.total_tokens)} tokens used`}
            />
            <StatsCard
              title="Total Cost"
              value={formatCost(llmStats.total_cost_cents)}
              icon={DollarSign}
              description="Across all providers"
            />
            <StatsCard
              title="Avg Latency"
              value={formatLatency(llmStats.avg_latency_ms)}
              icon={Clock}
              description="Per request"
            />
            <StatsCard
              title="Success Rate"
              value={`${(llmStats.success_rate * 100).toFixed(1)}%`}
              icon={CheckCircle}
              description={`${llmStats.total_requests} total calls`}
            />
          </div>

          {/* Provider breakdown */}
          {Object.keys(llmStats.by_provider).length > 0 && (
            <Card className="mt-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">
                  Usage by Provider
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(llmStats.by_provider).map(
                    ([provider, data]) => (
                      <div key={provider} className="flex items-center gap-3">
                        <Badge variant="outline" className="w-24 justify-center">
                          {provider}
                        </Badge>
                        <div className="flex-1">
                          <Progress
                            value={
                              (data.count / llmStats.total_requests) * 100
                            }
                            className="h-2"
                          />
                        </div>
                        <span className="text-sm text-muted-foreground w-20 text-right">
                          {data.count} calls
                        </span>
                        <span className="text-sm font-medium w-16 text-right">
                          {formatCost(data.cost_cents)}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Model breakdown */}
          {Object.keys(llmStats.by_model).length > 0 && (
            <Card className="mt-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">
                  Usage by Model
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {Object.entries(llmStats.by_model).map(([model, data]) => (
                    <div
                      key={model}
                      className="flex items-center justify-between p-2 rounded-lg bg-accent/30"
                    >
                      <span className="text-sm font-mono truncate">{model}</span>
                      <div className="text-right">
                        <span className="text-sm font-medium">{data.count}</span>
                        <span className="text-xs text-muted-foreground ml-1">
                          calls
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Agent Stats */}
      {agentStats && (
        <div>
          <h3 className="text-lg font-semibold mb-4">
            Agent Executions (Last 7 Days)
          </h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatsCard
              title="Total Executions"
              value={formatNumber(agentStats.total_executions)}
              icon={Bot}
              description="Across all agents"
            />
            <StatsCard
              title="Avg Latency"
              value={formatLatency(agentStats.avg_latency_ms)}
              icon={Zap}
              description="Per execution"
            />
            <StatsCard
              title="Success Rate"
              value={`${(agentStats.success_rate * 100).toFixed(1)}%`}
              icon={TrendingUp}
              description="Successful executions"
            />
          </div>

          {/* Agent type breakdown */}
          {Object.keys(agentStats.by_type).length > 0 && (
            <Card className="mt-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">
                  Executions by Agent Type
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {Object.entries(agentStats.by_type).map(([type, data]) => (
                    <div
                      key={type}
                      className="flex items-center justify-between p-3 rounded-lg bg-accent/30"
                    >
                      <div className="flex items-center gap-2">
                        <Cpu className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium capitalize">
                          {type}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">{data.count}</div>
                        <div className="text-xs text-muted-foreground">
                          ~{formatLatency(data.avg_latency_ms)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
