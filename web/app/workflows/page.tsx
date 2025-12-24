"use client";

import Link from "next/link";
import { Plus, Workflow } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { WorkflowCard, WorkflowCardSkeleton } from "@/components/workflows/workflow-card";
import { useWorkflows } from "@/lib/hooks/use-workflows";

export default function WorkflowsPage() {
  const { data, isLoading, error } = useWorkflows();

  return (
    <>
      <Header
        title="Workflows"
        actionLabel="New Workflow"
        actionHref="/workflows/new"
      />
      <PageContainer>
        {isLoading && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <WorkflowCardSkeleton key={i} />
            ))}
          </div>
        )}

        {error && (
          <div className="text-center py-12">
            <p className="text-destructive">
              Failed to load workflows: {error.message}
            </p>
          </div>
        )}

        {data && data.workflows.length === 0 && (
          <div className="text-center py-12 border rounded-lg border-dashed">
            <div className="flex justify-center mb-4">
              <div className="p-4 rounded-full bg-primary/10">
                <Workflow className="h-8 w-8 text-primary" />
              </div>
            </div>
            <h3 className="text-lg font-semibold mb-2">No workflows yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first workflow to orchestrate agents
            </p>
            <Button asChild>
              <Link href="/workflows/new">
                <Plus className="h-4 w-4 mr-2" />
                Create Workflow
              </Link>
            </Button>
          </div>
        )}

        {data && data.workflows.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data.workflows.map((workflow) => (
              <WorkflowCard key={workflow.id} workflow={workflow} />
            ))}
          </div>
        )}
      </PageContainer>
    </>
  );
}
