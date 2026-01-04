"use client";

import { ChatLayout } from "@/components/chat/chat-layout";

interface AgentChatProps {
  agentId: string;
}

export function AgentChat({ agentId }: AgentChatProps) {
  return (
    <div className="h-[600px] rounded-lg border border-border overflow-hidden">
      <ChatLayout agentId={agentId} className="h-full" />
    </div>
  );
}
