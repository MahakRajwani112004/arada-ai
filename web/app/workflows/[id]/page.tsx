"use client";

import { useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { WorkflowHeader } from "@/components/workflows/workflow-header";
import { BlockedWorkflowBanner } from "@/components/workflows/blocked-workflow-banner";
import { StepList } from "@/components/workflows/steps/step-list";
import { RunWorkflowPanel } from "@/components/workflows/execution/run-workflow-panel";
import { ExecutionHistory } from "@/components/workflows/execution/execution-history";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useWorkflow,
  useWorkflowExecutions,
  useDeleteWorkflow,
  useExecuteWorkflow,
} from "@/lib/hooks/use-workflows";
import { useAgents } from "@/lib/hooks/use-agents";

function WorkflowDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-6 w-32" />
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="flex items-start gap-4">
          <Skeleton className="h-12 w-12 rounded-lg" />
          <div className="flex-1">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="mt-2 h-4 w-96" />
            <div className="mt-3 flex gap-2">
              <Skeleton className="h-6 w-24" />
              <Skeleton className="h-6 w-16" />
            </div>
          </div>
        </div>
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Skeleton className="h-[400px] rounded-lg" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-[200px] rounded-lg" />
          <Skeleton className="h-[200px] rounded-lg" />
        </div>
      </div>
    </div>
  );
}

export default function WorkflowDetailPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [activeTab, setActiveTab] = useState("definition");

  const { data: workflow, isLoading: isLoadingWorkflow, error } = useWorkflow(workflowId);
  const { data: executionsData, isLoading: isLoadingExecutions } = useWorkflowExecutions(workflowId);
  const { data: agentsData } = useAgents();
  const deleteWorkflow = useDeleteWorkflow();
  const executeWorkflow = useExecuteWorkflow();

  // Compute missing agents
  const missingAgents = useMemo(() => {
    if (!workflow?.definition?.steps || !agentsData?.agents) return [];

    const existingAgentIds = new Set(agentsData.agents.map((a) => a.id));
    const missing: string[] = [];

    for (const step of workflow.definition.steps) {
      if (step.type === "agent" && step.agent_id) {
        if (!existingAgentIds.has(step.agent_id)) {
          missing.push(step.agent_id);
        }
      }
    }

    return missing;
  }, [workflow, agentsData]);

  const isBlocked = missingAgents.length > 0;

  const handleRun = (userInput: string) => {
    executeWorkflow.mutate(
      { workflowId, request: { user_input: userInput } },
      {
        onSuccess: (data) => {
          // Could open execution panel or navigate to execution view
          console.log("Execution started:", data);
        },
      }
    );
  };

  const handleDelete = () => {
    if (confirm("Are you sure you want to delete this workflow?")) {
      deleteWorkflow.mutate(workflowId, {
        onSuccess: () => router.push("/workflows"),
      });
    }
  };

  const handleEdit = () => {
    router.push(`/workflows/${workflowId}/edit`);
  };

  const handleCreateAgents = () => {
    // Navigate to agent creation with context about which agents are needed
    // For now, navigate to agents page
    router.push("/agents");
  };

  const handleCreateAgent = (agentId: string) => {
    // Navigate to agent creation form with prefilled agent ID
    router.push(`/agents/new?suggested_id=${agentId}`);
  };

  if (isLoadingWorkflow) {
    return (
      <>
        <Header />
        <PageContainer>
          <WorkflowDetailSkeleton />
        </PageContainer>
      </>
    );
  }

  if (error || !workflow) {
    return (
      <>
        <Header />
        <PageContainer>
          <div className="flex flex-col items-center justify-center py-16">
            <h2 className="text-lg font-semibold">Workflow not found</h2>
            <p className="mt-2 text-muted-foreground">
              The workflow you&apos;re looking for doesn&apos;t exist or was deleted.
            </p>
          </div>
        </PageContainer>
      </>
    );
  }

  return (
    <>
      <Header />
      <PageContainer>
        <div className="space-y-6">
          <WorkflowHeader
            workflow={workflow}
            isBlocked={isBlocked}
            executionCount={executionsData?.executions?.length ?? 0}
            onRun={() => handleRun("")}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />

          {isBlocked && (
            <BlockedWorkflowBanner
              missingAgents={missingAgents}
              onCreateAgents={handleCreateAgents}
            />
          )}

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="definition">Definition</TabsTrigger>
              <TabsTrigger value="executions">
                Executions ({executionsData?.executions?.length ?? 0})
              </TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>

            <div className="mt-6">
              <TabsContent value="definition" className="mt-0">
                <div className="grid gap-6 lg:grid-cols-3">
                  <div className="lg:col-span-2">
                    <Card>
                      <CardContent className="p-6">
                        <h3 className="font-semibold mb-4">Workflow Steps</h3>
                        {workflow.definition?.steps && workflow.definition.steps.length > 0 ? (
                          <StepList
                            steps={workflow.definition.steps}
                            missingAgents={missingAgents}
                            onCreateAgent={handleCreateAgent}
                          />
                        ) : (
                          <p className="text-muted-foreground text-center py-8">
                            No steps defined yet
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                  <div className="space-y-4">
                    <RunWorkflowPanel
                      workflowId={workflowId}
                      isBlocked={isBlocked}
                      isExecuting={executeWorkflow.isPending}
                      onRun={handleRun}
                    />
                    <ExecutionHistory
                      executions={executionsData?.executions ?? []}
                      isLoading={isLoadingExecutions}
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="executions" className="mt-0">
                <Card>
                  <CardContent className="p-6">
                    {executionsData?.executions && executionsData.executions.length > 0 ? (
                      <div className="space-y-3">
                        {executionsData.executions.map((execution) => (
                          <div
                            key={execution.id}
                            className="flex items-center justify-between rounded-lg border border-border p-4 hover:bg-secondary/50 transition-colors cursor-pointer"
                            onClick={() => router.push(`/workflows/executions/${execution.id}`)}
                          >
                            <div>
                              <p className="font-medium">{execution.id}</p>
                              <p className="text-sm text-muted-foreground">
                                Started {new Date(execution.started_at).toLocaleString()}
                              </p>
                            </div>
                            <div className="text-right">
                              <span
                                className={`text-sm font-medium ${
                                  execution.status === "COMPLETED"
                                    ? "text-green-400"
                                    : execution.status === "FAILED"
                                    ? "text-red-400"
                                    : execution.status === "RUNNING"
                                    ? "text-blue-400"
                                    : "text-gray-400"
                                }`}
                              >
                                {execution.status}
                              </span>
                              {execution.duration_ms && (
                                <p className="text-xs text-muted-foreground">
                                  {(execution.duration_ms / 1000).toFixed(1)}s
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        No executions yet. Run the workflow to see execution history.
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="settings" className="mt-0">
                <Card>
                  <CardContent className="p-6 space-y-6">
                    <div>
                      <h4 className="font-medium mb-2">Workflow Information</h4>
                      <dl className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <dt className="text-muted-foreground">ID</dt>
                          <dd className="font-mono">{workflow.id}</dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Version</dt>
                          <dd>{workflow.version}</dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Category</dt>
                          <dd className="capitalize">{workflow.category.replace("-", " ")}</dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Template</dt>
                          <dd>{workflow.is_template ? "Yes" : "No"}</dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Created</dt>
                          <dd>{new Date(workflow.created_at).toLocaleDateString()}</dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Updated</dt>
                          <dd>{new Date(workflow.updated_at).toLocaleDateString()}</dd>
                        </div>
                      </dl>
                    </div>
                    {workflow.tags && workflow.tags.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Tags</h4>
                        <div className="flex flex-wrap gap-2">
                          {workflow.tags.map((tag) => (
                            <span
                              key={tag}
                              className="rounded-full bg-secondary px-3 py-1 text-xs"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </PageContainer>
    </>
  );
}
