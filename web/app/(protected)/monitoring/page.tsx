"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { LogsTable } from "@/components/monitoring/logs-table";
import { LogFilters } from "@/components/monitoring/log-filters";
import { AnalyticsOverview } from "@/components/monitoring/analytics-overview";
import {
  useLogs,
  useLogServices,
  useLLMAnalytics,
  useAgentAnalytics,
  useWorkflowAnalytics,
  useDashboardSummary,
  useTopWorkflows,
  useTopAgents,
  useErrorAnalytics,
  useCostBreakdown,
} from "@/lib/hooks/use-monitoring";
import { RefreshCw, ExternalLink } from "lucide-react";
import type { LogFilters as LogFiltersType } from "@/types/monitoring";

export default function MonitoringPage() {
  const [activeTab, setActiveTab] = useState("analytics");
  const [logFilters, setLogFilters] = useState<LogFiltersType>({ limit: 100 });

  // Fetch data
  const { data: logsData, isLoading: logsLoading, refetch: refetchLogs } = useLogs(logFilters);
  const { data: servicesData } = useLogServices();
  const { data: llmStats, isLoading: llmLoading } = useLLMAnalytics();
  const { data: agentStats, isLoading: agentLoading } = useAgentAnalytics();
  const { data: workflowStats, isLoading: workflowLoading } = useWorkflowAnalytics();
  const { data: dashboardSummary, isLoading: dashboardLoading } = useDashboardSummary();
  const { data: topWorkflows, isLoading: topWorkflowsLoading } = useTopWorkflows({ limit: 5 });
  const { data: topAgents, isLoading: topAgentsLoading } = useTopAgents({ limit: 5 });
  const { data: errorStats, isLoading: errorLoading } = useErrorAnalytics();
  const { data: costBreakdown, isLoading: costLoading } = useCostBreakdown();

  const isAnalyticsLoading = llmLoading || agentLoading || workflowLoading ||
    dashboardLoading || topWorkflowsLoading || topAgentsLoading || errorLoading || costLoading;

  const handleRefresh = () => {
    refetchLogs();
  };

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="Monitoring"
          description="View logs and analytics for your AI agents and workflows"
          actions={
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                className="gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                asChild
                className="gap-2"
              >
                <a
                  href="http://localhost:3002"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-4 w-4" />
                  Grafana
                </a>
              </Button>
            </div>
          }
        />

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="logs">Logs</TabsTrigger>
          </TabsList>

          <TabsContent value="analytics">
            <AnalyticsOverview
              llmStats={llmStats}
              agentStats={agentStats}
              workflowStats={workflowStats}
              dashboardSummary={dashboardSummary}
              topWorkflows={topWorkflows}
              topAgents={topAgents}
              errorStats={errorStats}
              costBreakdown={costBreakdown}
              isLoading={isAnalyticsLoading}
            />
          </TabsContent>

          <TabsContent value="logs" className="space-y-4">
            <LogFilters
              filters={logFilters}
              onFiltersChange={setLogFilters}
              services={servicesData?.services || []}
            />
            <LogsTable
              logs={logsData?.logs || []}
              isLoading={logsLoading}
            />
            {logsData && (
              <p className="text-sm text-muted-foreground text-center">
                Showing {logsData.logs.length} of {logsData.total} logs
              </p>
            )}
          </TabsContent>
        </Tabs>
      </PageContainer>
    </>
  );
}
