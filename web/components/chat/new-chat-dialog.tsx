"use client";

import { useState, ReactNode } from "react";
import { Bot, MessageSquare, Workflow, Search } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useAgents } from "@/lib/hooks/use-agents";
import type { AgentType } from "@/types/agent";

interface NewChatDialogProps {
  children: ReactNode;
  onNewChat: (agentId: string) => void;
}

// Icon mapping for agent types
function AgentTypeIcon({
  type,
  className,
}: {
  type: AgentType;
  className?: string;
}) {
  switch (type) {
    case "OrchestratorAgent":
    case "RouterAgent":
    case "FullAgent":
      return <Workflow className={className} />;
    case "LLMAgent":
      return <MessageSquare className={className} />;
    default:
      return <Bot className={className} />;
  }
}

function AgentListSkeleton() {
  return (
    <div className="space-y-2">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-3 p-3">
          <Skeleton className="h-10 w-10 rounded-lg" />
          <div className="flex-1">
            <Skeleton className="h-4 w-32 mb-1" />
            <Skeleton className="h-3 w-48" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function NewChatDialog({ children, onNewChat }: NewChatDialogProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const { data: agentsData, isLoading } = useAgents();

  const agents = agentsData?.agents ?? [];

  // Filter agents by search
  const filteredAgents = agents.filter(
    (agent) =>
      agent.name.toLowerCase().includes(search.toLowerCase()) ||
      agent.description?.toLowerCase().includes(search.toLowerCase())
  );

  const handleSelect = (agentId: string) => {
    onNewChat(agentId);
    setOpen(false);
    setSearch("");
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Start New Chat</DialogTitle>
          <DialogDescription>
            Choose an agent to start a conversation with.
          </DialogDescription>
        </DialogHeader>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search agents..."
            className="pl-9"
          />
        </div>

        {/* Agent List */}
        <ScrollArea className="h-[300px] -mx-6 px-6">
          {isLoading ? (
            <AgentListSkeleton />
          ) : filteredAgents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Bot className="h-8 w-8 text-muted-foreground/50 mb-2" />
              <p className="text-sm text-muted-foreground">
                {search ? "No agents found" : "No agents available"}
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredAgents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => handleSelect(agent.id)}
                  className={cn(
                    "w-full flex items-center gap-3 p-3 rounded-lg",
                    "hover:bg-accent transition-colors text-left"
                  )}
                >
                  <div className="flex-shrink-0 h-10 w-10 rounded-lg bg-secondary flex items-center justify-center">
                    <AgentTypeIcon
                      type={agent.agent_type}
                      className="h-5 w-5 text-muted-foreground"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{agent.name}</p>
                    {agent.description && (
                      <p className="text-sm text-muted-foreground truncate">
                        {agent.description}
                      </p>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
