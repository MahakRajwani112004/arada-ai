"use client";

import { useState } from "react";
import { Bot, MessageSquare, Workflow } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ConversationSummary } from "@/types/conversation";
import type { AgentType } from "@/types/agent";
import { formatRelativeTime } from "@/types/conversation";
import { ConversationActions } from "./conversation-actions";

interface ConversationItemProps {
  conversation: ConversationSummary;
  isActive: boolean;
  onClick: () => void;
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

export function ConversationItem({
  conversation,
  isActive,
  onClick,
}: ConversationItemProps) {
  const [showActions, setShowActions] = useState(false);

  return (
    <div
      className={cn(
        "group relative rounded-lg p-3 cursor-pointer transition-colors",
        isActive
          ? "bg-accent border-l-2 border-primary"
          : "hover:bg-muted/50"
      )}
      onClick={onClick}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* Title Row */}
      <div className="flex items-start justify-between gap-2">
        <span className="font-medium text-sm truncate flex-1">
          {conversation.title}
        </span>
        {showActions && (
          <ConversationActions
            conversationId={conversation.id}
            title={conversation.title}
            onDelete={() => {}}
          />
        )}
      </div>

      {/* Agent Badge */}
      <div className="flex items-center gap-1.5 mt-1">
        <AgentTypeIcon
          type={conversation.agent_type}
          className="h-3 w-3 text-muted-foreground"
        />
        <span className="text-xs text-muted-foreground truncate">
          {conversation.agent_name}
        </span>
      </div>

      {/* Message Preview */}
      {conversation.last_message_preview && (
        <p className="text-xs text-muted-foreground mt-1.5 line-clamp-1">
          &ldquo;{conversation.last_message_preview}&rdquo;
        </p>
      )}

      {/* Stats Row */}
      <div className="flex items-center gap-2 mt-1.5 text-xs text-muted-foreground">
        <span>
          {conversation.message_count}{" "}
          {conversation.message_count === 1 ? "message" : "messages"}
        </span>
        {conversation.last_message_at && (
          <>
            <span>&bull;</span>
            <span>{formatRelativeTime(conversation.last_message_at)}</span>
          </>
        )}
      </div>
    </div>
  );
}
