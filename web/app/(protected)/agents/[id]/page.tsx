"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Trash2, Bot, MessageSquare, Workflow, Pencil } from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { AgentChat } from "@/components/agents/agent-chat";
import { AgentForm } from "@/components/agents/agent-form";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useAgent, useDeleteAgent } from "@/lib/hooks/use-agents";
import type { AgentType } from "@/types/agent";

const agentTypeConfig: Record<AgentType, { label: string; icon: React.ReactNode; color: string }> = {
  SimpleAgent: {
    label: "Simple",
    icon: <Bot className="h-3 w-3" />,
    color: "bg-gray-500/10 text-gray-400 border-gray-500/20",
  },
  LLMAgent: {
    label: "Chat",
    icon: <MessageSquare className="h-3 w-3" />,
    color: "bg-green-500/10 text-green-400 border-green-500/20",
  },
  RAGAgent: {
    label: "RAG",
    icon: <Bot className="h-3 w-3" />,
    color: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  },
  ToolAgent: {
    label: "Tool Agent",
    icon: <Bot className="h-3 w-3" />,
    color: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  },
  FullAgent: {
    label: "Full Agent",
    icon: <Workflow className="h-3 w-3" />,
    color: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  },
  RouterAgent: {
    label: "Router",
    icon: <Workflow className="h-3 w-3" />,
    color: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  },
  OrchestratorAgent: {
    label: "Orchestrator",
    icon: <Workflow className="h-3 w-3" />,
    color: "bg-violet-500/10 text-violet-400 border-violet-500/20",
  },
};

const defaultConfig = {
  label: "Agent",
  icon: <Bot className="h-3 w-3" />,
  color: "bg-gray-500/10 text-gray-400 border-gray-500/20",
};

export default function AgentDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { id } = params;
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isEditing, setIsEditing] = useState(searchParams.get("edit") === "true");
  const { data: agent, isLoading, error } = useAgent(id);
  const deleteAgent = useDeleteAgent();

  // Update isEditing when URL changes
  useEffect(() => {
    setIsEditing(searchParams.get("edit") === "true");
  }, [searchParams]);

  const handleDelete = async () => {
    await deleteAgent.mutateAsync(id);
    router.push("/agents");
  };

  if (isLoading) {
    return (
      <>
        <Header />
        <PageContainer>
          <div className="mb-6 flex items-center gap-4">
            <Skeleton className="h-10 w-10 rounded-lg" />
            <div>
              <Skeleton className="h-6 w-48" />
              <Skeleton className="mt-1 h-4 w-24" />
            </div>
          </div>
          <Skeleton className="h-[600px] w-full rounded-lg" />
        </PageContainer>
      </>
    );
  }

  if (error || !agent) {
    return (
      <>
        <Header />
        <PageContainer>
          <div className="flex flex-col items-center justify-center py-16">
            <p className="text-destructive">
              {error?.message || "Agent not found"}
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => router.push("/agents")}
            >
              Back to Agents
            </Button>
          </div>
        </PageContainer>
      </>
    );
  }

  const config = agentTypeConfig[agent.agent_type] || defaultConfig;

  return (
    <>
      <Header />
      <PageContainer>
        <div className="mb-6 flex items-start justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/agents")}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-secondary">
              <Bot className="h-6 w-6 text-muted-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                {agent.name}
              </h1>
              <div className="mt-1 flex items-center gap-2">
                <Badge variant="outline" className={`gap-1 ${config.color}`}>
                  {config.icon}
                  {config.label}
                </Badge>
                {agent.description && (
                  <span className="text-sm text-muted-foreground">
                    {agent.description}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (isEditing) {
                  router.push(`/agents/${id}`);
                } else {
                  router.push(`/agents/${id}?edit=true`);
                }
              }}
            >
              <Pencil className="mr-2 h-4 w-4" />
              {isEditing ? "Cancel Edit" : "Edit"}
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline" size="sm" className="text-destructive">
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Agent</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to delete &quot;{agent.name}&quot;? This
                    action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleDelete}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>

        {isEditing ? (
          <AgentForm
            initialData={agent}
            isEditing={true}
            onCancel={() => router.push(`/agents/${id}`)}
          />
        ) : (
          <AgentChat agentId={id} />
        )}
      </PageContainer>
    </>
  );
}
