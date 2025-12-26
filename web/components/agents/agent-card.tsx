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

export function AgentCard({ agent }: AgentCardProps) {
  const config = agentTypeConfig[agent.agent_type] || defaultConfig;

  return (
    <Link href={`/agents/${agent.id}`}>
      <Card className="group h-full cursor-pointer transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5">
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
