"use client";

import { useState, useCallback } from "react";
import { useMediaQuery } from "@/lib/hooks/use-media-query";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { ConversationSidebar } from "./conversation-sidebar";
import { ChatArea } from "./chat-area";
import { ChatEmptyState } from "./chat-empty-state";
import {
  useAllConversations,
  useAgentConversations,
  useCreateConversation,
} from "@/lib/hooks/use-conversations";

interface ChatLayoutProps {
  // For main /chat page: undefined
  // For agent page: the agent ID to filter conversations
  agentId?: string;

  // Allow controlling the active conversation from parent
  activeConversationId?: string;
  onConversationChange?: (id: string | null) => void;

  // Full height mode
  className?: string;
}

export function ChatLayout({
  agentId,
  activeConversationId: controlledActiveId,
  onConversationChange,
  className,
}: ChatLayoutProps) {
  // Use either controlled or uncontrolled state
  const [internalActiveId, setInternalActiveId] = useState<string | null>(null);
  const activeId = controlledActiveId ?? internalActiveId;
  const setActiveId = useCallback(
    (id: string | null) => {
      if (onConversationChange) {
        onConversationChange(id);
      } else {
        setInternalActiveId(id);
      }
    },
    [onConversationChange]
  );

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isMobile = useMediaQuery("(max-width: 768px)");

  // Use appropriate query based on context
  const allConversations = useAllConversations();
  const agentConversations = useAgentConversations(agentId || "");

  const { data, isLoading } = agentId ? agentConversations : allConversations;

  const createConversation = useCreateConversation();

  const handleNewChat = useCallback(
    async (selectedAgentId: string) => {
      const result = await createConversation.mutateAsync({
        agentId: selectedAgentId,
      });
      setActiveId(result.id);
      setSidebarOpen(false);
    },
    [createConversation, setActiveId]
  );

  const handleSelectConversation = useCallback(
    (id: string) => {
      setActiveId(id);
      setSidebarOpen(false);
    },
    [setActiveId]
  );

  return (
    <div className={cn("flex h-full", className)}>
      {/* Desktop Sidebar */}
      {!isMobile && (
        <div className="w-72 border-r border-border flex-shrink-0">
          <ConversationSidebar
            conversations={data?.conversations || []}
            activeId={activeId}
            onSelect={handleSelectConversation}
            onNewChat={handleNewChat}
            agentId={agentId}
            isLoading={isLoading}
          />
        </div>
      )}

      {/* Mobile Sidebar (Sheet) */}
      {isMobile && (
        <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
          <SheetContent side="left" className="w-72 p-0">
            <ConversationSidebar
              conversations={data?.conversations || []}
              activeId={activeId}
              onSelect={handleSelectConversation}
              onNewChat={handleNewChat}
              agentId={agentId}
              isLoading={isLoading}
            />
          </SheetContent>
        </Sheet>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {activeId ? (
          <ChatArea
            conversationId={activeId}
            onMenuClick={() => setSidebarOpen(true)}
            isMobile={isMobile}
          />
        ) : (
          <ChatEmptyState
            onNewChat={handleNewChat}
            agentId={agentId}
          />
        )}
      </div>
    </div>
  );
}
