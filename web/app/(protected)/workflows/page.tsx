"use client";

import { useState, useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import { Workflow, Plus, Filter } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { WorkflowCard, type WorkflowStatus } from "@/components/workflows/workflow-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkflows, useDeleteWorkflow, workflowKeys } from "@/lib/hooks/use-workflows";
import { useAgents } from "@/lib/hooks/use-agents";
import { getWorkflow } from "@/lib/api/workflows";
import type { WorkflowDetail, WorkflowSummary } from "@/types/workflow";

type StatusFilter = "all" | WorkflowStatus;

interface WorkflowWithStats extends WorkflowSummary {
  totalSteps: number;
  configuredSteps: number;
  status: WorkflowStatus;
}

function WorkflowCardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-start gap-3">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <div className="flex-1">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="mt-2 h-4 w-20" />
        </div>
      </div>
      <Skeleton className="mt-4 h-4 w-full" />
      <Skeleton className="mt-1 h-4 w-3/4" />
      <div className="mt-4 flex justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-3 w-8" />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 py-16">
      <motion.div
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-purple-500/20 to-blue-500/20"
      >
        <Workflow className="h-8 w-8 text-primary" />
      </motion.div>
      <h3 className="mt-6 text-lg font-semibold">
        Your workflows are waiting to shine
      </h3>
      <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
        Create your first workflow to automate tasks and orchestrate your AI
        agents
      </p>
      <div className="mt-6">
        <Button asChild className="gap-2">
          <Link href="/workflows/new">
            <Plus className="h-4 w-4" />
            Create New Workflow
          </Link>
        </Button>
      </div>
    </div>
  );
}

const statusFilters: { value: StatusFilter; label: string; color: string }[] = [
  { value: "all", label: "All", color: "" },
  { value: "ready", label: "Ready", color: "bg-green-500/10 text-green-400 border-green-500/20" },
  { value: "incomplete", label: "Incomplete", color: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
  { value: "draft", label: "Draft", color: "bg-gray-500/10 text-gray-400 border-gray-500/20" },
];

// Compute workflow status from full workflow detail
function computeWorkflowStats(
  workflow: WorkflowDetail,
  existingAgentIds: Set<string>
): { totalSteps: number; configuredSteps: number; status: WorkflowStatus } {
  const steps = workflow.definition?.steps || [];
  const agentSteps = steps.filter(s => s.type === "agent");
  const totalSteps = agentSteps.length;

  if (totalSteps === 0) {
    return { totalSteps: 0, configuredSteps: 0, status: "draft" };
  }

  let configuredSteps = 0;
  for (const step of agentSteps) {
    if (step.agent_id && existingAgentIds.has(step.agent_id)) {
      configuredSteps++;
    }
  }

  const status: WorkflowStatus =
    configuredSteps === 0 ? "draft" :
    configuredSteps < totalSteps ? "incomplete" : "ready";

  return { totalSteps, configuredSteps, status };
}

export default function WorkflowsPage() {
  const { data, isLoading, error } = useWorkflows();
  const { data: agentsData } = useAgents();
  const deleteWorkflow = useDeleteWorkflow();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  // Get existing agent IDs
  const existingAgentIds = useMemo(() => {
    return new Set(agentsData?.agents?.map(a => a.id) || []);
  }, [agentsData]);

  // Fetch full details for each workflow to compute status
  const workflowIds = data?.workflows?.map(w => w.id) || [];
  const workflowDetailsQueries = useQueries({
    queries: workflowIds.map(id => ({
      queryKey: workflowKeys.detail(id),
      queryFn: () => getWorkflow(id),
      staleTime: 30000, // Cache for 30 seconds
    })),
  });

  // Combine summaries with computed stats
  const workflowsWithStats: WorkflowWithStats[] = useMemo(() => {
    if (!data?.workflows) return [];

    return data.workflows.map((summary, index) => {
      const detailQuery = workflowDetailsQueries[index];
      const detail = detailQuery?.data;

      if (detail) {
        const stats = computeWorkflowStats(detail, existingAgentIds);
        return { ...summary, ...stats };
      }

      // Fallback while loading detail
      return {
        ...summary,
        totalSteps: 0,
        configuredSteps: 0,
        status: "draft" as WorkflowStatus,
      };
    });
  }, [data?.workflows, workflowDetailsQueries, existingAgentIds]);

  // Filter workflows based on selected status
  const filteredWorkflows = useMemo(() => {
    if (statusFilter === "all") return workflowsWithStats;
    return workflowsWithStats.filter(w => w.status === statusFilter);
  }, [workflowsWithStats, statusFilter]);

  // Count workflows by status for filter badges
  const statusCounts = useMemo(() => {
    const counts = { all: workflowsWithStats.length, draft: 0, incomplete: 0, ready: 0 };
    for (const w of workflowsWithStats) {
      counts[w.status]++;
    }
    return counts;
  }, [workflowsWithStats]);

  const isLoadingDetails = workflowDetailsQueries.some(q => q.isLoading);

  return (
    <>
      <Header />
      <PageContainer className="items-start">
        <PageHeader
          title="Workflows"
          description="Orchestrate multi-step AI agent workflows"
          actions={
            <Button asChild className="gap-2">
              <Link href="/workflows/create">
                <Plus className="h-4 w-4" />
                Create New Workflow
              </Link>
            </Button>
          }
        />

        {/* Status Filter */}
        {data && data.workflows.length > 0 && (
          <div className="flex items-center gap-2 mb-6">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Filter:</span>
            <div className="flex gap-2">
              {statusFilters.map((filter) => (
                <button
                  key={filter.value}
                  onClick={() => setStatusFilter(filter.value)}
                  className={`px-3 py-1 text-xs font-medium rounded-full border transition-colors ${
                    statusFilter === filter.value
                      ? filter.color || "bg-primary/10 text-primary border-primary/20"
                      : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/20"
                  }`}
                >
                  {filter.label}
                  {!isLoadingDetails && (
                    <span className="ml-1 opacity-60">({statusCounts[filter.value]})</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {(isLoading || isLoadingDetails) && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <WorkflowCardSkeleton key={i} />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive">
            Failed to load workflows: {error.message}
          </div>
        )}

        {!isLoading && !isLoadingDetails && data && data.workflows.length === 0 && <EmptyState />}

        {!isLoading && !isLoadingDetails && filteredWorkflows.length === 0 && data && data.workflows.length > 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 py-12">
            <p className="text-muted-foreground">No workflows match the selected filter</p>
            <Button
              variant="ghost"
              size="sm"
              className="mt-2"
              onClick={() => setStatusFilter("all")}
            >
              Clear filter
            </Button>
          </div>
        )}

        {!isLoading && !isLoadingDetails && filteredWorkflows.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredWorkflows.map((workflow) => (
              <WorkflowCard
                key={workflow.id}
                workflow={workflow}
                onDelete={(id) => deleteWorkflow.mutate(id)}
                totalSteps={workflow.totalSteps}
                configuredSteps={workflow.configuredSteps}
                status={workflow.status}
              />
            ))}
          </div>
        )}
      </PageContainer>
    </>
  );
}
