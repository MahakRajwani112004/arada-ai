"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Trash2, Bot, MessageSquare, Workflow, BarChart3, Settings } from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { AgentChat } from "@/components/agents/agent-chat";
import { AgentForm } from "@/components/agents/agent-form";
import { AgentOverview } from "@/components/agents/agent-overview";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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

type TabValue = "overview" | "chat" | "config";

export default function AgentDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { id } = params;
  const router = useRouter();
  const searchParams = useSearchParams();

  // Determine initial tab from URL
  const getInitialTab = useCallback((): TabValue => {
    if (searchParams.get("edit") === "true") return "config";
    const tab = searchParams.get("tab");
    if (tab === "chat" || tab === "config" || tab === "overview") return tab;
    return "overview"; // Default to overview
  }, [searchParams]);

  const [activeTab, setActiveTab] = useState<TabValue>(getInitialTab());
  const { data: agent, isLoading, error } = useAgent(id);
  const deleteAgent = useDeleteAgent();

  // Update tab when URL changes
  useEffect(() => {
    setActiveTab(getInitialTab());
  }, [getInitialTab]);

  const handleTabChange = (value: string) => {
    const tab = value as TabValue;
    setActiveTab(tab);
    // Update URL without full navigation
    if (tab === "config") {
      router.replace(`/agents/${id}?edit=true`, { scroll: false });
    } else if (tab === "chat") {
      router.replace(`/agents/${id}?tab=chat`, { scroll: false });
    } else {
      router.replace(`/agents/${id}`, { scroll: false });
    }
  };

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

        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="overview" className="gap-2">
              <BarChart3 className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="chat" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="config" className="gap-2">
              <Settings className="h-4 w-4" />
              Configuration
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-0">
            <AgentOverview agent={agent} />
          </TabsContent>

          <TabsContent value="chat" className="mt-0">
            <AgentChat agentId={id} />
          </TabsContent>

          <TabsContent value="config" className="mt-0">
            <AgentForm
              initialData={agent}
              isEditing={true}
              onCancel={() => handleTabChange("overview")}
            />
          </TabsContent>
        </Tabs>
      </PageContainer>
    </>
  );
}
