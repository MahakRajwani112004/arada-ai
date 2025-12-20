"use client";

import { Bot, Plus } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { AgentCard } from "@/components/agents/agent-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAgents, useDeleteAgent } from "@/lib/hooks/use-agents";

function AgentCardSkeleton() {
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
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 py-16">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-secondary">
        <Bot className="h-7 w-7 text-muted-foreground" />
      </div>
      <h3 className="mt-4 text-lg font-semibold">No agents yet</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Create your first AI agent to get started
      </p>
      <Button asChild className="mt-6 gap-2">
        <Link href="/agents/new">
          <Plus className="h-4 w-4" />
          Create Agent
        </Link>
      </Button>
    </div>
  );
}

export default function AgentsPage() {
  const { data, isLoading, error } = useAgents();
  const deleteAgent = useDeleteAgent();

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="Agents"
          description="Create and manage your AI agents"
        />

        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <AgentCardSkeleton key={i} />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive">
            Failed to load agents: {error.message}
          </div>
        )}

        {data && data.agents.length === 0 && <EmptyState />}

        {data && data.agents.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.agents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onDelete={(id) => deleteAgent.mutate(id)}
              />
            ))}
          </div>
        )}
      </PageContainer>
    </>
  );
}
