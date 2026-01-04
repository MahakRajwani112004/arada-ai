"use client";

import { useRef, useEffect } from "react";
import { Menu, Bot, MessageSquare, Workflow } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessages } from "./chat-messages";
import { ChatInput } from "./chat-input";
import { ThinkingIndicator } from "./thinking-indicator";
import { StreamingMessage } from "./streaming-message";
import { useConversation, useStreamingChat } from "@/lib/hooks/use-conversations";
import type { AgentType } from "@/types/agent";

interface ChatAreaProps {
  conversationId: string;
  onMenuClick?: () => void;
  isMobile?: boolean;
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

function ChatAreaSkeleton() {
  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-border p-4">
        <Skeleton className="h-6 w-48" />
      </div>
      <div className="flex-1 p-4 space-y-4">
        <Skeleton className="h-20 w-3/4" />
        <Skeleton className="h-16 w-2/3 ml-auto" />
        <Skeleton className="h-24 w-3/4" />
      </div>
      <div className="border-t border-border p-4">
        <Skeleton className="h-12 w-full" />
      </div>
    </div>
  );
}

export function ChatArea({ conversationId, onMenuClick, isMobile }: ChatAreaProps) {
  const { data: conversation, isLoading } = useConversation(conversationId);
  const {
    state: streamingState,
    sendMessage,
    cancelMessage,
    isStreaming,
  } = useStreamingChat(conversationId);

  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [conversation?.messages, streamingState.streamedContent]);

  if (isLoading) {
    return <ChatAreaSkeleton />;
  }

  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        Conversation not found
      </div>
    );
  }

  const handleSend = async (content: string) => {
    await sendMessage(content);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border px-4 py-3 flex items-center gap-3">
        {isMobile && onMenuClick && (
          <Button variant="ghost" size="icon" onClick={onMenuClick}>
            <Menu className="h-5 w-5" />
          </Button>
        )}
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <AgentTypeIcon
            type={conversation.agent_type}
            className="h-5 w-5 text-muted-foreground flex-shrink-0"
          />
          <div className="min-w-0">
            <h2 className="font-medium truncate">{conversation.title}</h2>
            <p className="text-xs text-muted-foreground truncate">
              {conversation.agent_name}
            </p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea ref={scrollRef} className="flex-1">
        <div className="p-4 space-y-4">
          <ChatMessages messages={conversation.messages} />

          {/* Streaming State */}
          {isStreaming && (
            <>
              {streamingState.progress.length > 0 && (
                <ThinkingIndicator progress={streamingState.progress} />
              )}
              {streamingState.streamedContent && (
                <StreamingMessage content={streamingState.streamedContent} />
              )}
            </>
          )}

          {/* Error State */}
          {streamingState.status === "error" && (
            <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-sm">
              {streamingState.error || "An error occurred"}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-border p-4">
        <ChatInput
          onSend={handleSend}
          onCancel={cancelMessage}
          isLoading={isStreaming}
          disabled={isStreaming}
        />
      </div>
    </div>
  );
}
