"use client";

import { MessageSquare, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { NewChatDialog } from "./new-chat-dialog";

interface ChatEmptyStateProps {
  onNewChat: (agentId: string) => void;
  agentId?: string;
}

export function ChatEmptyState({ onNewChat, agentId }: ChatEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 text-center">
      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-secondary mb-4">
        <MessageSquare className="h-8 w-8 text-muted-foreground" />
      </div>

      <h2 className="text-xl font-semibold mb-2">
        {agentId ? "Start a Conversation" : "Welcome to Chat"}
      </h2>

      <p className="text-muted-foreground mb-6 max-w-md">
        {agentId
          ? "Start a new conversation with this agent to get help with your tasks."
          : "Select a conversation from the sidebar or start a new chat with one of your agents."}
      </p>

      {agentId ? (
        <Button onClick={() => onNewChat(agentId)} className="gap-2">
          <Plus className="h-4 w-4" />
          New Conversation
        </Button>
      ) : (
        <NewChatDialog onNewChat={onNewChat}>
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            Start New Chat
          </Button>
        </NewChatDialog>
      )}
    </div>
  );
}
