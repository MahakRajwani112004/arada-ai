"use client";

import Link from "next/link";
import { Bot, MessageSquare, Workflow, Pencil } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Agent, AgentType } from "@/types/agent";

interface AgentCardProps {
  agent: Agent;
}

const agentTypeConfig: Record<AgentType, { label: string; icon: React.ReactNode; color: string }> = {
  SimpleAgent: {
    label: "Simple",
    icon: <Bot className="h-3 w-3" />,
    color: "bg-slate-100 text-slate-600 border-slate-200",
  },
  LLMAgent: {
    label: "Chat",
    icon: <MessageSquare className="h-3 w-3" />,
    color: "bg-emerald-50 text-emerald-600 border-emerald-200",
  },
  RAGAgent: {
    label: "RAG",
    icon: <Bot className="h-3 w-3" />,
    color: "bg-cyan-50 text-cyan-600 border-cyan-200",
  },
  ToolAgent: {
    label: "Tool Agent",
    icon: <Bot className="h-3 w-3" />,
    color: "bg-blue-50 text-blue-600 border-blue-200",
  },
  FullAgent: {
    label: "Full Agent",
    icon: <Workflow className="h-3 w-3" />,
    color: "bg-violet-50 text-violet-600 border-violet-200",
  },
  RouterAgent: {
    label: "Router",
    icon: <Workflow className="h-3 w-3" />,
    color: "bg-amber-50 text-amber-600 border-amber-200",
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
  color: "bg-slate-100 text-slate-600 border-slate-200",
};

export function AgentCard({ agent }: AgentCardProps) {
  const config = agentTypeConfig[agent.agent_type] || defaultConfig;

  return (
    <Link href={`/agents/${agent.id}`}>
      <Card className="group h-full cursor-pointer border-border/60 shadow-sm transition-all duration-200 hover:border-primary/40 hover:shadow-md">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary">
              <Bot className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <h3 className="font-semibold leading-none tracking-tight">
                {agent.name}
              </h3>
              <Badge
                variant="outline"
                className={`mt-1.5 gap-1 ${config.color}`}
              >
                {config.icon}
                {config.label}
              </Badge>
            </div>
          </div>
          <Link
            href={`/agents/${agent.id}?edit=true`}
            onClick={(e) => e.stopPropagation()}
          >
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 opacity-0 group-hover:opacity-100"
            >
              <Pencil className="h-4 w-4" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          <p className="line-clamp-2 text-sm text-muted-foreground">
            {agent.description || "No description provided"}
          </p>
        </CardContent>
      </Card>
    </Link>
  );
}
