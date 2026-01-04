"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useAgentStats,
  useAgentExecutions,
  useAgentUsageHistory,
} from "@/lib/hooks/use-agents";
import type { AgentDetail, TimeRange } from "@/types/agent";
import { StatsCards } from "./stats-cards";
import { UsageChart } from "./usage-chart";
import { RecentExecutions } from "./recent-executions";
import { OrchestratorDetails } from "./orchestrator-details";

interface AgentOverviewProps {
  agent: AgentDetail;
}

export function AgentOverview({ agent }: AgentOverviewProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>("7d");

  const { data: stats, isLoading: statsLoading } = useAgentStats(agent.id, timeRange);
  const { data: usageHistory, isLoading: historyLoading } = useAgentUsageHistory(
    agent.id,
    timeRange,
    timeRange === "24h" ? "hour" : "day"
  );
  const { data: executions, isLoading: executionsLoading } = useAgentExecutions(agent.id, {
    limit: 10,
  });

  const isOrchestrator = agent.agent_type === "OrchestratorAgent" && agent.orchestrator_config;

  return (
    <div className="space-y-6">
      {/* Orchestrator-specific section */}
      {isOrchestrator && (
        <OrchestratorDetails config={agent.orchestrator_config!} />
      )}

      {/* Time Range Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Performance Overview</h2>
        <Tabs value={timeRange} onValueChange={(v) => setTimeRange(v as TimeRange)}>
          <TabsList className="h-8">
            <TabsTrigger value="24h" className="text-xs px-3">24h</TabsTrigger>
            <TabsTrigger value="7d" className="text-xs px-3">7d</TabsTrigger>
            <TabsTrigger value="30d" className="text-xs px-3">30d</TabsTrigger>
            <TabsTrigger value="90d" className="text-xs px-3">90d</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Stats Cards */}
      <StatsCards stats={stats} isLoading={statsLoading} />

      {/* Usage Chart */}
      <UsageChart data={usageHistory} isLoading={historyLoading} />

      {/* Recent Executions */}
      <RecentExecutions
        executions={executions?.executions}
        isLoading={executionsLoading}
        total={executions?.total ?? 0}
      />
    </div>
  );
}
