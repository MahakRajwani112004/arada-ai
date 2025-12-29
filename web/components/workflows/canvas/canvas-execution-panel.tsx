"use client";

import { useState, useRef, useEffect } from "react";
import { X, Send, Bot, User, Loader2, Play, MessageSquare, Workflow } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useExecuteWorkflow } from "@/lib/hooks/use-workflows";
import { useExecuteWorkflow as useExecuteAgent } from "@/lib/hooks/use-agents";
import type { StepExecutionResult } from "@/types/workflow";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  stepResults?: StepExecutionResult[];
  executionId?: string;
  status?: "completed" | "failed" | "running";
}

interface CanvasExecutionPanelProps {
  workflowId: string;
  workflowName: string;
  selectedAgentId?: string;
  selectedAgentName?: string;
  canRun: boolean;
  onClose: () => void;
}

export function CanvasExecutionPanel({
  workflowId,
  workflowName,
  selectedAgentId,
  selectedAgentName,
  canRun,
  onClose,
}: CanvasExecutionPanelProps) {
  const [activeTab, setActiveTab] = useState<"workflow" | "agent">(
    selectedAgentId ? "agent" : "workflow"
  );
  const [workflowMessages, setWorkflowMessages] = useState<Message[]>([]);
  const [agentMessages, setAgentMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const executeWorkflow = useExecuteWorkflow();
  const executeAgent = useExecuteAgent();

  const messages = activeTab === "workflow" ? workflowMessages : agentMessages;
  const isLoading = executeWorkflow.isPending || executeAgent.isPending;

  // Update active tab when selected agent changes
  useEffect(() => {
    if (selectedAgentId) {
      setActiveTab("agent");
    }
  }, [selectedAgentId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateId = () => Math.random().toString(36).substr(2, 9);

  const handleSubmitWorkflow = async () => {
    if (!input.trim() || !canRun) return;

    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content: input.trim(),
    };
    setWorkflowMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const response = await executeWorkflow.mutateAsync({
        workflowId,
        request: {
          user_input: input.trim(),
          conversation_history: workflowMessages
            .filter((m) => m.role !== "system")
            .map((m) => ({ role: m.role as "user" | "assistant", content: m.content })),
        },
      });

      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: response.final_output || "Workflow completed",
        stepResults: response.step_results,
        executionId: response.execution_id,
        status: response.status === "COMPLETED" ? "completed" : "failed",
      };
      setWorkflowMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: error instanceof Error ? error.message : "An error occurred",
        status: "failed",
      };
      setWorkflowMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleSubmitAgent = async () => {
    if (!input.trim() || !selectedAgentId) return;

    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content: input.trim(),
    };
    setAgentMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const response = await executeAgent.mutateAsync({
        agent_id: selectedAgentId,
        user_input: input.trim(),
        conversation_history: agentMessages
          .filter((m) => m.role !== "system")
          .map((m) => ({ role: m.role as "user" | "assistant", content: m.content })),
      });

      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: response.success ? response.content : (response.error || "An error occurred"),
        status: response.success ? "completed" : "failed",
      };
      setAgentMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: error instanceof Error ? error.message : "An error occurred",
        status: "failed",
      };
      setAgentMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (activeTab === "workflow") {
      handleSubmitWorkflow();
    } else {
      handleSubmitAgent();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const renderMessage = (message: Message) => {
    const isUser = message.role === "user";
    const isSystem = message.role === "system";

    if (isSystem) {
      return (
        <div key={message.id} className="flex justify-center">
          <div className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-full">
            {message.content}
          </div>
        </div>
      );
    }

    return (
      <div
        key={message.id}
        className={cn("flex gap-3", isUser && "flex-row-reverse")}
      >
        <div
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
            isUser ? "bg-primary text-primary-foreground" : "bg-secondary"
          )}
        >
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </div>
        <div className={cn("max-w-[85%] space-y-2")}>
          <div
            className={cn(
              "rounded-lg px-4 py-2",
              isUser ? "bg-primary text-primary-foreground" : "bg-secondary"
            )}
          >
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>

          {/* Step Results */}
          {message.stepResults && message.stepResults.length > 0 && (
            <div className="space-y-1 pl-2">
              <p className="text-xs text-muted-foreground">Steps executed:</p>
              {message.stepResults.map((step, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-xs"
                >
                  <Badge
                    variant="secondary"
                    className={cn(
                      "text-[10px]",
                      step.status === "completed" && "bg-green-500/10 text-green-600",
                      step.status === "failed" && "bg-red-500/10 text-red-600"
                    )}
                  >
                    {step.status}
                  </Badge>
                  <span className="text-muted-foreground">{step.step_id}</span>
                </div>
              ))}
            </div>
          )}

          {/* Status indicator */}
          {message.status && (
            <Badge
              variant="secondary"
              className={cn(
                "text-[10px]",
                message.status === "completed" && "bg-green-500/10 text-green-600",
                message.status === "failed" && "bg-red-500/10 text-red-600"
              )}
            >
              {message.status}
            </Badge>
          )}
        </div>
      </div>
    );
  };

  const renderEmptyState = () => {
    if (activeTab === "workflow") {
      return (
        <div className="flex h-full flex-col items-center justify-center text-center p-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
            <Workflow className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="mt-4 text-sm font-medium">Run Workflow</p>
          <p className="mt-1 text-xs text-muted-foreground max-w-[200px]">
            {canRun
              ? `Enter a message to run "${workflowName}"`
              : "Create all agents first to run this workflow"}
          </p>
        </div>
      );
    }

    return (
      <div className="flex h-full flex-col items-center justify-center text-center p-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
          <MessageSquare className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="mt-4 text-sm font-medium">Chat with Agent</p>
        <p className="mt-1 text-xs text-muted-foreground max-w-[200px]">
          {selectedAgentId
            ? `Chat with "${selectedAgentName}"`
            : "Select an agent node to chat with it"}
        </p>
      </div>
    );
  };

  return (
    <div className="w-[380px] min-w-[380px] border-l border-border bg-card flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-border shrink-0">
        <h2 className="font-semibold text-sm">Execute</h2>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as "workflow" | "agent")}
        className="flex-1 flex flex-col min-h-0"
      >
        <div className="px-3 pt-2 shrink-0">
          <TabsList className="w-full grid grid-cols-2">
            <TabsTrigger value="workflow" className="text-xs">
              <Play className="h-3 w-3 mr-1.5" />
              Workflow
            </TabsTrigger>
            <TabsTrigger value="agent" className="text-xs" disabled={!selectedAgentId}>
              <Bot className="h-3 w-3 mr-1.5" />
              Agent
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="workflow" className="flex-1 flex flex-col min-h-0 m-0 p-0 data-[state=inactive]:hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 min-h-0">
            {workflowMessages.length === 0 ? (
              renderEmptyState()
            ) : (
              <div className="space-y-4">
                {workflowMessages.map(renderMessage)}
                {executeWorkflow.isPending && (
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">Running workflow...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="agent" className="flex-1 flex flex-col min-h-0 m-0 p-0 data-[state=inactive]:hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 min-h-0">
            {agentMessages.length === 0 ? (
              renderEmptyState()
            ) : (
              <div className="space-y-4">
                {agentMessages.map(renderMessage)}
                {executeAgent.isPending && (
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">Thinking...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </TabsContent>

        {/* Input */}
        <form onSubmit={handleSubmit} className="border-t border-border p-3 shrink-0">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                activeTab === "workflow"
                  ? canRun
                    ? "Enter input for workflow..."
                    : "Create agents first..."
                  : selectedAgentId
                  ? "Chat with agent..."
                  : "Select an agent..."
              }
              rows={2}
              className="resize-none min-h-[60px] text-sm"
              disabled={
                (activeTab === "workflow" && !canRun) ||
                (activeTab === "agent" && !selectedAgentId)
              }
            />
            <Button
              type="submit"
              size="icon"
              className="self-end"
              disabled={
                !input.trim() ||
                isLoading ||
                (activeTab === "workflow" && !canRun) ||
                (activeTab === "agent" && !selectedAgentId)
              }
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </Tabs>
    </div>
  );
}
