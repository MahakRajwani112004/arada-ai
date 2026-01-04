"use client";

import { useMemo } from "react";
import { Plus, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { ConversationItem } from "./conversation-item";
import { NewChatDialog } from "./new-chat-dialog";
import type { ConversationSummary } from "@/types/conversation";
import { groupConversationsByDate } from "@/types/conversation";

interface ConversationSidebarProps {
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: (agentId: string) => void;
  agentId?: string;
  isLoading?: boolean;
}

interface ConversationGroupProps {
  label: string;
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
}

function ConversationGroup({
  label,
  conversations,
  activeId,
  onSelect,
}: ConversationGroupProps) {
  if (conversations.length === 0) return null;

  return (
    <div className="space-y-1">
      <div className="px-2 py-1.5">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
      </div>
      {conversations.map((conv) => (
        <ConversationItem
          key={conv.id}
          conversation={conv}
          isActive={conv.id === activeId}
          onClick={() => onSelect(conv.id)}
        />
      ))}
    </div>
  );
}

function SidebarSkeleton() {
  return (
    <div className="space-y-4 p-3">
      <Skeleton className="h-9 w-full" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-20 w-full" />
      </div>
    </div>
  );
}

export function ConversationSidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  agentId,
  isLoading,
}: ConversationSidebarProps) {
  // Group conversations by date
  const grouped = useMemo(
    () => groupConversationsByDate(conversations),
    [conversations]
  );

  const hasConversations = conversations.length > 0;

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <h2 className="font-semibold flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          Conversations
        </h2>
      </div>

      {/* New Chat Button */}
      <div className="p-3 border-b border-border">
        {agentId ? (
          <Button
            variant="outline"
            className="w-full justify-start gap-2"
            onClick={() => onNewChat(agentId)}
          >
            <Plus className="h-4 w-4" />
            New Conversation
          </Button>
        ) : (
          <NewChatDialog onNewChat={onNewChat}>
            <Button variant="outline" className="w-full justify-start gap-2">
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
          </NewChatDialog>
        )}
      </div>

      {/* Conversation List */}
      {isLoading ? (
        <SidebarSkeleton />
      ) : !hasConversations ? (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center text-muted-foreground">
            <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No conversations yet</p>
            <p className="text-xs mt-1">Start a new chat to begin</p>
          </div>
        </div>
      ) : (
        <ScrollArea className="flex-1">
          <div className="px-2 pb-4 space-y-4">
            <ConversationGroup
              label="Today"
              conversations={grouped.today}
              activeId={activeId}
              onSelect={onSelect}
            />
            <ConversationGroup
              label="Yesterday"
              conversations={grouped.yesterday}
              activeId={activeId}
              onSelect={onSelect}
            />
            <ConversationGroup
              label="This Week"
              conversations={grouped.thisWeek}
              activeId={activeId}
              onSelect={onSelect}
            />
            <ConversationGroup
              label="Older"
              conversations={grouped.older}
              activeId={activeId}
              onSelect={onSelect}
            />
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
