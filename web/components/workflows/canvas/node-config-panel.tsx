"use client";

import { useState } from "react";
import { X, Bot, Check, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { AgentCreationSheet } from "@/components/agents/agent-creation-sheet";
import type { CanvasNode, AgentNodeData, TriggerNodeData } from "@/lib/workflow-canvas/types";
import type { Agent } from "@/types/agent";
import type { SuggestedAgent } from "@/types/workflow";

interface NodeConfigPanelProps {
  node: CanvasNode;
  agents: Agent[];
  onClose: () => void;
  onCreateAgent: (nodeId: string, suggestion: SuggestedAgent) => Promise<Agent>;
  onAssignAgent: (nodeId: string, agent: Agent) => void;
}

export function NodeConfigPanel({
  node,
  agents,
  onClose,
  onCreateAgent,
  onAssignAgent,
}: NodeConfigPanelProps) {
  // All hooks must be called before any early returns
  const [isCreating, setIsCreating] = useState(false);
  const [showAgentSheet, setShowAgentSheet] = useState(false);
  const [isChangingAgent, setIsChangingAgent] = useState(false);

  if (node.type === "trigger") {
    return (
      <TriggerConfigPanel
        data={node.data as TriggerNodeData}
        onClose={onClose}
      />
    );
  }

  if (node.type === "end") {
    return (
      <EndConfigPanel onClose={onClose} />
    );
  }

  const data = node.data as AgentNodeData;
  const isDraft = data.status === "draft";
  const hasSuggestion = !!data.suggestedAgent;

  const handleCreateFromSuggestion = async () => {
    if (!data.suggestedAgent) return;

    setIsCreating(true);
    try {
      await onCreateAgent(node.id, data.suggestedAgent);
    } finally {
      setIsCreating(false);
    }
  };

  const handleSelectExistingAgent = (agentId: string) => {
    const agent = agents.find((a) => a.id === agentId);
    if (agent) {
      onAssignAgent(node.id, agent);
    }
  };

  const handleAgentCreated = (agent: Agent) => {
    onAssignAgent(node.id, agent);
    setShowAgentSheet(false);
  };

  return (
    <>
      <div className="w-[340px] min-w-[340px] border-l border-border bg-card flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border shrink-0">
          <h2 className="font-semibold text-base">Configure Step</h2>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Step Name */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Step Name</label>
            <Input value={data.name} readOnly className="bg-muted" />
          </div>

          {/* Agent Assignment Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Agent Assignment</label>
              <Badge
                variant={isDraft ? "secondary" : "default"}
                className={isDraft ? "bg-orange-500/10 text-orange-600" : "bg-green-500/10 text-green-600"}
              >
                {isDraft ? "Draft" : "Ready"}
              </Badge>
            </div>

            {/* Ready state - show assigned agent */}
            {!isDraft && data.agentId && !isChangingAgent && (
              <div className="rounded-lg border border-green-500/30 bg-green-500/5 p-4 space-y-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                    <Bot className="h-5 w-5 text-green-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{data.agentName}</div>
                    <div className="text-xs text-muted-foreground truncate">
                      {data.agentGoal}
                    </div>
                  </div>
                  <Check className="h-5 w-5 text-green-500 shrink-0" />
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="flex-1" disabled>
                    View Agent
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => setIsChangingAgent(true)}
                  >
                    Change
                  </Button>
                </div>
              </div>
            )}

            {/* Changing agent mode */}
            {isChangingAgent && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Select a different agent</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsChangingAgent(false)}
                  >
                    Cancel
                  </Button>
                </div>
                <Select onValueChange={(agentId) => {
                  handleSelectExistingAgent(agentId);
                  setIsChangingAgent(false);
                }}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select an agent..." />
                  </SelectTrigger>
                  <SelectContent>
                    {agents.map((agent) => (
                      <SelectItem key={agent.id} value={agent.id}>
                        <div className="flex items-center gap-2">
                          <Bot className="h-4 w-4" />
                          <span>{agent.name}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setIsChangingAgent(false);
                    setShowAgentSheet(true);
                  }}
                >
                  Create New Agent
                </Button>
              </div>
            )}

            {/* Draft state with AI suggestion */}
            {isDraft && hasSuggestion && (
              <div className="rounded-lg border border-orange-500/30 bg-orange-500/5 p-4 space-y-4">
                <div className="flex items-start gap-2">
                  <Sparkles className="h-4 w-4 text-orange-500 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm font-medium">AI Suggested Agent</div>
                    <div className="text-xs text-muted-foreground">
                      Based on your workflow requirements
                    </div>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Name:</span>{" "}
                    <span className="font-medium">{data.suggestedAgent?.name}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Goal:</span>{" "}
                    <span>{data.suggestedAgent?.goal}</span>
                  </div>
                  {data.suggestedAgent?.model && (
                    <div>
                      <span className="text-muted-foreground">Model:</span>{" "}
                      <span className="font-mono text-xs">{data.suggestedAgent.model}</span>
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2">
                  <Button
                    onClick={handleCreateFromSuggestion}
                    disabled={isCreating}
                    className="w-full"
                  >
                    {isCreating ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Check className="h-4 w-4 mr-2" />
                        Create Agent
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowAgentSheet(true)}
                    className="w-full"
                  >
                    Customize First
                  </Button>
                </div>
              </div>
            )}

            {/* Draft state without suggestion */}
            {isDraft && !hasSuggestion && (
              <div className="text-sm text-muted-foreground">
                No AI suggestion available. Select an existing agent or create a new one.
              </div>
            )}

            {/* Separator */}
            {isDraft && (
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">or</span>
                </div>
              </div>
            )}

            {/* Select existing agent */}
            {isDraft && (
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">
                  Use existing agent
                </label>
                <Select onValueChange={handleSelectExistingAgent}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select an agent..." />
                  </SelectTrigger>
                  <SelectContent>
                    {agents.map((agent) => (
                      <SelectItem key={agent.id} value={agent.id}>
                        <div className="flex items-center gap-2">
                          <Bot className="h-4 w-4" />
                          <span>{agent.name}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* Input Template */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Input Template</label>
            <Textarea
              value={data.role || "${user_input}"}
              readOnly
              rows={3}
              className="bg-muted font-mono text-xs"
            />
            <p className="text-xs text-muted-foreground">
              Variables: {"${user_input}"}, {"${previous}"}
            </p>
          </div>
        </div>
      </div>

      {/* Agent Creation Sheet */}
      <AgentCreationSheet
        open={showAgentSheet}
        onOpenChange={setShowAgentSheet}
        suggestedName={data.suggestedAgent?.name}
        suggestedGoal={data.suggestedAgent?.goal}
        suggestedDescription={data.suggestedAgent?.description}
        suggestedTools={data.suggestedAgent?.suggested_tools}
        context={`For workflow step: ${data.name}`}
        onAgentCreated={handleAgentCreated}
      />
    </>
  );
}

function TriggerConfigPanel({
  data,
  onClose,
}: {
  data: TriggerNodeData;
  onClose: () => void;
}) {
  return (
    <div className="w-[340px] min-w-[340px] border-l border-border bg-card flex flex-col h-full overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border shrink-0">
        <h2 className="font-semibold">Trigger Configuration</h2>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Trigger Type</label>
          <div className="text-sm capitalize">{data.triggerType}</div>
        </div>
        {data.webhookUrl && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Webhook URL</label>
            <code className="block text-xs bg-muted p-2 rounded break-all">
              {data.webhookUrl}
            </code>
          </div>
        )}
      </div>
    </div>
  );
}

function EndConfigPanel({ onClose }: { onClose: () => void }) {
  return (
    <div className="w-[340px] min-w-[340px] border-l border-border bg-card flex flex-col h-full overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border shrink-0">
        <h2 className="font-semibold">End Node</h2>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <p className="text-sm text-muted-foreground">
          This marks the end of your workflow. The final output from the previous step
          will be returned as the workflow result.
        </p>
      </div>
    </div>
  );
}
