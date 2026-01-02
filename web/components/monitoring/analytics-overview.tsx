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
  Workflow,
  AlertTriangle,
  Database,
  Server,
  Activity,
} from "lucide-react";
import type {
  LLMUsageStats,
  AgentStats,
  WorkflowStats,
  DashboardSummary,
  TopWorkflowsResponse,
  TopAgentsResponse,
  ErrorStats,
  CostBreakdown,
} from "@/types/monitoring";

interface AnalyticsOverviewProps {
  llmStats?: LLMUsageStats;
  agentStats?: AgentStats;
  workflowStats?: WorkflowStats;
  dashboardSummary?: DashboardSummary;
  topWorkflows?: TopWorkflowsResponse;
  topAgents?: TopAgentsResponse;
  errorStats?: ErrorStats;
  costBreakdown?: CostBreakdown;
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

function formatPercent(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

export function AnalyticsOverview({
  llmStats,
  agentStats,
  workflowStats,
  dashboardSummary,
  topWorkflows,
  topAgents,
  errorStats,
  costBreakdown,
  isLoading,
}: AnalyticsOverviewProps) {
  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Dashboard Summary Skeleton */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Dashboard Overview</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <StatsCardSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Summary */}
      {dashboardSummary && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Dashboard Overview (Last 24h)</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatsCard
              title="Total Agents"
              value={formatNumber(dashboardSummary.total_agents)}
              icon={Bot}
              description="Active agents"
            />
            <StatsCard
              title="Total Workflows"
              value={formatNumber(dashboardSummary.total_workflows)}
              icon={Workflow}
              description="Active workflows"
            />
            <StatsCard
              title="MCP Servers"
              value={`${dashboardSummary.active_mcp_servers}/${dashboardSummary.total_mcp_servers}`}
              icon={Server}
              description="Connected / Total"
            />
            <StatsCard
              title="Knowledge Bases"
              value={formatNumber(dashboardSummary.total_knowledge_bases)}
              icon={Database}
              description="Document stores"
            />
            <StatsCard
              title="Workflow Executions"
              value={formatNumber(dashboardSummary.executions_24h)}
              icon={Activity}
              description={formatPercent(dashboardSummary.workflow_success_rate_24h) + " success"}
            />
            <StatsCard
              title="LLM Calls"
              value={formatNumber(dashboardSummary.llm_calls_24h)}
              icon={MessageSquare}
              description={formatNumber(dashboardSummary.tokens_used_24h) + " tokens"}
            />
            <StatsCard
              title="Total Cost"
              value={formatCost(dashboardSummary.cost_cents_24h)}
              icon={DollarSign}
              description="Last 24 hours"
            />
            <StatsCard
              title="Agent Success"
              value={formatPercent(dashboardSummary.agent_success_rate_24h)}
              icon={CheckCircle}
              description="Success rate"
            />
          </div>

          {/* Recent Activity */}
          {(dashboardSummary.recent_workflows.length > 0 || dashboardSummary.recent_executions.length > 0) && (
            <div className="grid gap-4 mt-4 lg:grid-cols-2">
              {dashboardSummary.recent_workflows.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Recent Workflows</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {dashboardSummary.recent_workflows.slice(0, 5).map((w) => (
                        <div key={w.id} className="flex items-center justify-between p-2 rounded-lg bg-accent/30">
                          <span className="text-sm font-medium truncate">{w.name}</span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(w.updated_at).toLocaleDateString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
              {dashboardSummary.recent_executions.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Recent Executions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {dashboardSummary.recent_executions.slice(0, 5).map((e) => (
                        <div key={e.id} className="flex items-center justify-between p-2 rounded-lg bg-accent/30">
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={e.status === "COMPLETED" ? "default" : e.status === "FAILED" ? "destructive" : "secondary"}
                              className="text-xs"
                            >
                              {e.status}
                            </Badge>
                            <span className="text-sm truncate">{e.workflow_id}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {e.duration_ms ? formatLatency(e.duration_ms) : "-"}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      )}

      {/* Workflow Stats */}
      {workflowStats && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Workflow Executions (Last 7 Days)</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatsCard
              title="Total Executions"
              value={formatNumber(workflowStats.total_executions)}
              icon={Workflow}
              description={`${workflowStats.successful_executions} successful`}
            />
            <StatsCard
              title="Success Rate"
              value={formatPercent(workflowStats.success_rate)}
              icon={CheckCircle}
              description={`${workflowStats.failed_executions} failed`}
            />
            <StatsCard
              title="Avg Duration"
              value={formatLatency(workflowStats.avg_duration_ms)}
              icon={Clock}
              description="Per execution"
            />
            <StatsCard
              title="Total Runtime"
              value={formatLatency(workflowStats.total_duration_ms)}
              icon={Activity}
              description="Cumulative"
            />
          </div>

          {/* Status breakdown */}
          {Object.keys(workflowStats.by_status).length > 0 && (
            <Card className="mt-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Executions by Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(workflowStats.by_status).map(([status, count]) => (
                    <Badge
                      key={status}
                      variant={status === "COMPLETED" ? "default" : status === "FAILED" ? "destructive" : "secondary"}
                    >
                      {status}: {count}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Top Workflows */}
      {topWorkflows && topWorkflows.workflows.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Top Workflows</h3>
          <Card>
            <CardContent className="pt-4">
              <div className="space-y-3">
                {topWorkflows.workflows.map((w) => (
                  <div key={w.workflow_id} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">{w.name}</span>
                        <span className="text-sm text-muted-foreground">{w.execution_count} runs</span>
                      </div>
                      <Progress value={w.success_rate * 100} className="h-2" />
                    </div>
                    <div className="text-right w-20">
                      <div className="text-sm font-medium">{formatPercent(w.success_rate)}</div>
                      <div className="text-xs text-muted-foreground">{formatLatency(w.avg_duration_ms)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Top Agents */}
      {topAgents && topAgents.agents.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Top Agents</h3>
          <Card>
            <CardContent className="pt-4">
              <div className="space-y-3">
                {topAgents.agents.map((a) => (
                  <div key={a.agent_id} className="flex items-center gap-3">
                    <Badge variant="outline" className="w-20 justify-center">
                      {a.agent_type}
                    </Badge>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">{a.name}</span>
                        <span className="text-sm text-muted-foreground">{a.execution_count} runs</span>
                      </div>
                      <Progress value={a.success_rate * 100} className="h-2" />
                    </div>
                    <div className="text-right w-24">
                      <div className="text-sm font-medium">{formatPercent(a.success_rate)}</div>
                      <div className="text-xs text-muted-foreground">
                        {a.total_llm_calls} LLM / {a.total_tool_calls} tools
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

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
              value={formatPercent(llmStats.success_rate)}
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
              value={formatPercent(agentStats.success_rate)}
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

      {/* Cost Breakdown */}
      {costBreakdown && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Cost Breakdown (Last 30 Days)</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatsCard
              title="Total Cost"
              value={formatCost(costBreakdown.total_cost_cents)}
              icon={DollarSign}
              description="All providers"
            />
          </div>

          {costBreakdown.by_provider.length > 0 && (
            <Card className="mt-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Cost by Provider</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {costBreakdown.by_provider.map((p) => (
                    <div key={p.provider} className="flex items-center gap-3">
                      <Badge variant="outline" className="w-24 justify-center">
                        {p.provider}
                      </Badge>
                      <div className="flex-1">
                        <Progress
                          value={(p.cost_cents / costBreakdown.total_cost_cents) * 100}
                          className="h-2"
                        />
                      </div>
                      <span className="text-sm font-medium w-20 text-right">
                        {formatCost(p.cost_cents)}
                      </span>
                      <span className="text-xs text-muted-foreground w-24 text-right">
                        {formatNumber(p.tokens)} tokens
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {costBreakdown.by_model.length > 0 && (
            <Card className="mt-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Cost by Model</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {costBreakdown.by_model.map((m) => (
                    <div
                      key={m.model}
                      className="flex items-center justify-between p-2 rounded-lg bg-accent/30"
                    >
                      <span className="text-sm font-mono truncate">{m.model}</span>
                      <span className="text-sm font-medium">{formatCost(m.cost_cents)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Error Stats */}
      {errorStats && errorStats.total_errors > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Errors (Last 7 Days)</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatsCard
              title="Total Errors"
              value={formatNumber(errorStats.total_errors)}
              icon={AlertTriangle}
              description={formatPercent(errorStats.error_rate) + " error rate"}
            />
          </div>

          {Object.keys(errorStats.by_type).length > 0 && (
            <Card className="mt-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Errors by Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(errorStats.by_type).map(([type, count]) => (
                    <Badge key={type} variant="destructive">
                      {type}: {count}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {errorStats.recent_errors.length > 0 && (
            <Card className="mt-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Recent Errors</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {errorStats.recent_errors.slice(0, 5).map((e, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 p-2 rounded-lg bg-destructive/10"
                    >
                      <AlertTriangle className="h-4 w-4 text-destructive mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {e.agent_id}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {e.error_type || "Unknown"}
                          </span>
                        </div>
                        {e.error_message && (
                          <p className="text-xs text-muted-foreground mt-1 truncate">
                            {e.error_message}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {new Date(e.timestamp).toLocaleTimeString()}
                      </span>
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
