"use client";

import { Workflow, Plus, Sparkles } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { WorkflowCard } from "@/components/workflows/workflow-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkflows, useDeleteWorkflow } from "@/lib/hooks/use-workflows";

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
      <div className="mt-6 flex gap-3">
        <Button asChild variant="outline" className="gap-2">
          <Link href="/workflows/new">
            <Plus className="h-4 w-4" />
            Build Manually
          </Link>
        </Button>
        <Button asChild className="gap-2">
          <Link href="/workflows/create">
            <Sparkles className="h-4 w-4" />
            AI Generate
          </Link>
        </Button>
      </div>
    </div>
  );
}

export default function WorkflowsPage() {
  const { data, isLoading, error } = useWorkflows();
  const deleteWorkflow = useDeleteWorkflow();

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="Workflows"
          description="Orchestrate multi-step AI agent workflows"
          actions={
            <div className="flex gap-2">
              <Button asChild variant="outline" className="gap-2">
                <Link href="/workflows/new">
                  <Plus className="h-4 w-4" />
                  New Workflow
                </Link>
              </Button>
              <Button asChild className="gap-2">
                <Link href="/workflows/create">
                  <Sparkles className="h-4 w-4" />
                  AI Generate
                </Link>
              </Button>
            </div>
          }
        />

        {isLoading && (
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

        {data && data.workflows.length === 0 && <EmptyState />}

        {data && data.workflows.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.workflows.map((workflow) => (
              <WorkflowCard
                key={workflow.id}
                workflow={workflow}
                onDelete={(id) => deleteWorkflow.mutate(id)}
              />
            ))}
          </div>
        )}
      </PageContainer>
    </>
  );
}
