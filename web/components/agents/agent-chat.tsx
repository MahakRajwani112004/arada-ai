"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, Loader2, Maximize2, Minimize2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { useExecuteWorkflow } from "@/lib/hooks/use-agents";
import { WorkflowResponse } from "@/types/agent";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  clarificationOptions?: string[];
}

interface AgentChatProps {
  agentId: string;
}

// Generate unique message ID
const generateMessageId = () => crypto.randomUUID();

export function AgentChat({ agentId }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesRef = useRef<Message[]>(messages);
  const executeWorkflow = useExecuteWorkflow();

  // Keep ref in sync with state to avoid stale closures
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Extract shared response handling logic
  const handleWorkflowResponse = useCallback((response: WorkflowResponse) => {
    if (response.success) {
      setMessages((prev) => [
        ...prev,
        {
          id: generateMessageId(),
          role: "assistant",
          content: response.content,
          clarificationOptions: response.requires_clarification
            ? response.clarification_options
            : undefined,
        },
      ]);
    } else {
      setMessages((prev) => [
        ...prev,
        {
          id: generateMessageId(),
          role: "assistant",
          content: response.error || "An error occurred. Please try again.",
        },
      ]);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || executeWorkflow.isPending) return;

    const userMessage: Message = {
      id: generateMessageId(),
      role: "user",
      content: input.trim(),
    };
    const currentMessages = messagesRef.current;
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const response = await executeWorkflow.mutateAsync({
        agent_id: agentId,
        user_input: input.trim(),
        conversation_history: currentMessages,
      });
      handleWorkflowResponse(response);
    } catch (error) {
      // Error is handled by mutation's onError, but we catch to prevent unhandled rejection
      console.error("Workflow execution failed:", error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleClarificationClick = async (option: string) => {
    if (executeWorkflow.isPending) return;

    const userMessage: Message = {
      id: generateMessageId(),
      role: "user",
      content: option,
    };
    // Use ref to get current messages to avoid stale closure
    const currentMessages = [...messagesRef.current, userMessage];
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await executeWorkflow.mutateAsync({
        agent_id: agentId,
        user_input: option,
        conversation_history: currentMessages,
      });
      handleWorkflowResponse(response);
    } catch (error) {
      // Error is handled by mutation's onError, but we catch to prevent unhandled rejection
      console.error("Workflow execution failed:", error);
    }
  };

  return (
    <div className="flex h-[600px] flex-col rounded-lg border border-border bg-card">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
              <Bot className="h-6 w-6 text-muted-foreground" />
            </div>
            <p className="mt-4 text-sm text-muted-foreground">
              Start a conversation with your agent
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex gap-3",
                  message.role === "user" && "flex-row-reverse"
                )}
              >
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary"
                  )}
                >
                  {message.role === "user" ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </div>
                <div className="flex flex-col gap-2 max-w-[80%]">
                  <div
                    className={cn(
                      "rounded-lg px-4 py-2",
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary text-secondary-foreground"
                    )}
                  >
                    <div className={cn(
                      "text-sm prose prose-sm max-w-none [&>*]:!text-inherit",
                      message.role === "assistant" && "dark:prose-invert"
                    )}>
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  </div>
                  {/* Clarification options as quick-reply buttons */}
                  {message.clarificationOptions && message.clarificationOptions.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {message.clarificationOptions.map((option) => (
                        <Button
                          key={option}
                          variant="outline"
                          size="sm"
                          className="text-xs"
                          onClick={() => handleClarificationClick(option)}
                          disabled={executeWorkflow.isPending}
                        >
                          {option}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {executeWorkflow.isPending && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">
                    Thinking...
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-border p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message..."
              rows={isExpanded ? 10 : 1}
              className={cn(
                "resize-none pr-10",
                isExpanded ? "min-h-[240px]" : "min-h-[44px]"
              )}
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1 h-7 w-7 text-muted-foreground hover:text-foreground"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>
          </div>
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || executeWorkflow.isPending}
            className={isExpanded ? "self-end" : ""}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
