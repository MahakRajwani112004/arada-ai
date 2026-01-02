"use client";

import { useState } from "react";
import { X, Bot, Check, Sparkles, Loader2, GitBranch, Split, Plus, Trash2, ChevronRight, Layers, RefreshCw, Hash, ListOrdered, Target } from "lucide-react";
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
import type { CanvasNode, AgentNodeData, TriggerNodeData, ConditionalNodeData, ParallelNodeData, LoopNodeData, LoopMode } from "@/lib/workflow-canvas/types";
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

  if (node.type === "conditional") {
    return (
      <ConditionalConfigPanel
        data={node.data as ConditionalNodeData}
        agents={agents}
        onClose={onClose}
      />
    );
  }

  if (node.type === "parallel") {
    return (
      <ParallelConfigPanel
        data={node.data as ParallelNodeData}
        agents={agents}
        onClose={onClose}
      />
    );
  }

  if (node.type === "loop") {
    return (
      <LoopConfigPanel
        data={node.data as LoopNodeData}
        agents={agents}
        onClose={onClose}
      />
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

function ConditionalConfigPanel({
  data,
  agents,
  onClose,
}: {
  data: ConditionalNodeData;
  agents: Agent[];
  onClose: () => void;
}) {
  const [newCondition, setNewCondition] = useState("");
  const routerAgents = agents.filter((a) => a.agent_type === "RouterAgent");

  return (
    <div className="w-[380px] min-w-[380px] border-l border-border bg-card flex flex-col h-full overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border shrink-0">
        <div className="flex items-center gap-2">
          <GitBranch className="h-5 w-5 text-blue-500" />
          <h2 className="font-semibold">Conditional Step</h2>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Step Name */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Step Name</label>
          <Input value={data.name} readOnly className="bg-muted" />
        </div>

        {/* Classifier Agent Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Classifier Agent</label>
          <p className="text-xs text-muted-foreground">
            Select a RouterAgent that will classify user input and determine which branch to take.
          </p>
          <Select defaultValue={data.classifierAgentId}>
            <SelectTrigger>
              <SelectValue placeholder="Select a RouterAgent..." />
            </SelectTrigger>
            <SelectContent>
              {routerAgents.length === 0 ? (
                <div className="p-2 text-sm text-muted-foreground text-center">
                  No RouterAgents available. Create one first.
                </div>
              ) : (
                routerAgents.map((agent) => (
                  <SelectItem key={agent.id} value={agent.id}>
                    <div className="flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-blue-500" />
                      <span>{agent.name}</span>
                    </div>
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
          {data.classifierAgentName && (
            <div className="text-xs text-green-600 flex items-center gap-1">
              <Check className="h-3 w-3" />
              Using: {data.classifierAgentName}
            </div>
          )}
        </div>

        {/* Branches Configuration */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Branches</label>
            <Badge variant="secondary" className="text-xs">
              {data.branches.length} configured
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            Map classification results to target steps.
          </p>

          {/* Existing branches */}
          <div className="space-y-2">
            {data.branches.map((branch, index) => (
              <div key={index} className="flex items-center gap-2 p-2 rounded border bg-muted/50">
                <ChevronRight className="h-4 w-4 text-blue-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">{branch.condition}</div>
                  <div className="text-xs text-muted-foreground truncate">
                    → {branch.targetStepName || branch.targetStepId}
                  </div>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0">
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>

          {/* Default branch */}
          {data.defaultStepId && (
            <div className="flex items-center gap-2 p-2 rounded border border-dashed bg-muted/30">
              <ChevronRight className="h-4 w-4 text-gray-400 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-muted-foreground">default</div>
                <div className="text-xs text-muted-foreground truncate">
                  → {data.defaultStepName || data.defaultStepId}
                </div>
              </div>
            </div>
          )}

          {/* Add new branch */}
          <div className="flex gap-2">
            <Input
              placeholder="Condition name..."
              value={newCondition}
              onChange={(e) => setNewCondition(e.target.value)}
              className="flex-1"
            />
            <Button size="sm" variant="outline" disabled={!newCondition}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Help text */}
        <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">
          <div className="text-xs text-blue-600 font-medium mb-1">How it works</div>
          <p className="text-xs text-muted-foreground">
            1. User input goes to the classifier agent<br />
            2. Classifier returns a category (e.g., &quot;calendar&quot;)<br />
            3. Workflow routes to the matching branch step
          </p>
        </div>
      </div>
    </div>
  );
}

const AGGREGATION_OPTIONS = [
  { value: "all", label: "Collect All", description: "Return all results as an array" },
  { value: "first", label: "First Completed", description: "Return the first result that completes" },
  { value: "merge", label: "Merge Results", description: "Combine all results into one object" },
  { value: "best", label: "LLM Selects Best", description: "Use AI to pick the best result" },
];

function ParallelConfigPanel({
  data,
  agents,
  onClose,
}: {
  data: ParallelNodeData;
  agents: Agent[];
  onClose: () => void;
}) {
  return (
    <div className="w-[380px] min-w-[380px] border-l border-border bg-card flex flex-col h-full overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border shrink-0">
        <div className="flex items-center gap-2">
          <Split className="h-5 w-5 text-purple-500" />
          <h2 className="font-semibold">Parallel Step</h2>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Step Name */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Step Name</label>
          <Input value={data.name} readOnly className="bg-muted" />
        </div>

        {/* Branches Configuration */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Parallel Branches</label>
            <Badge variant="secondary" className="text-xs">
              {data.branches.length} agent{data.branches.length !== 1 ? "s" : ""}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            These agents will run concurrently. Results are combined based on the aggregation strategy.
          </p>

          {/* Branch list */}
          <div className="space-y-2">
            {data.branches.map((branch, index) => (
              <div key={branch.id} className="p-3 rounded border bg-muted/50 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className={`h-4 w-4 ${branch.agentId ? "text-purple-500" : "text-gray-400"}`} />
                    <span className="text-sm font-medium">
                      {branch.agentName || `Branch ${index + 1}`}
                    </span>
                  </div>
                  <Button variant="ghost" size="icon" className="h-6 w-6">
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>

                {/* Agent selector */}
                {!branch.agentId && (
                  <Select>
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue placeholder="Select agent..." />
                    </SelectTrigger>
                    <SelectContent>
                      {agents.map((agent) => (
                        <SelectItem key={agent.id} value={agent.id}>
                          <div className="flex items-center gap-2">
                            <Bot className="h-3 w-3" />
                            <span>{agent.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}

                {/* Input template */}
                <div className="text-xs text-muted-foreground font-mono truncate">
                  Input: {branch.input || "${user_input}"}
                </div>
              </div>
            ))}
          </div>

          {/* Add branch button */}
          <Button variant="outline" size="sm" className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            Add Branch
          </Button>
        </div>

        {/* Aggregation Strategy */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-muted-foreground" />
            <label className="text-sm font-medium">Aggregation Strategy</label>
          </div>
          <p className="text-xs text-muted-foreground">
            How should results from all branches be combined?
          </p>

          <div className="space-y-2">
            {AGGREGATION_OPTIONS.map((option) => (
              <label
                key={option.value}
                className={`flex items-start gap-3 p-3 rounded border cursor-pointer transition-colors ${
                  data.aggregation === option.value
                    ? "border-purple-500/50 bg-purple-500/5"
                    : "hover:bg-muted/50"
                }`}
              >
                <input
                  type="radio"
                  name="aggregation"
                  value={option.value}
                  checked={data.aggregation === option.value}
                  onChange={() => {}}
                  className="mt-0.5"
                />
                <div>
                  <div className="text-sm font-medium">{option.label}</div>
                  <div className="text-xs text-muted-foreground">{option.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Help text */}
        <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 p-3">
          <div className="text-xs text-purple-600 font-medium mb-1">How it works</div>
          <p className="text-xs text-muted-foreground">
            All branches execute simultaneously. The workflow waits for all to complete
            (or just the first, depending on strategy) before proceeding.
          </p>
        </div>
      </div>
    </div>
  );
}

const LOOP_MODE_OPTIONS: { value: LoopMode; label: string; description: string; icon: React.ReactNode }[] = [
  { value: "count", label: "Count", description: "Run a fixed number of times", icon: <Hash className="h-4 w-4" /> },
  { value: "foreach", label: "For Each", description: "Iterate over a collection", icon: <ListOrdered className="h-4 w-4" /> },
  { value: "until", label: "Until", description: "Run until condition is met", icon: <Target className="h-4 w-4" /> },
];

function LoopConfigPanel({
  data,
  agents,
  onClose,
}: {
  data: LoopNodeData;
  agents: Agent[];
  onClose: () => void;
}) {
  return (
    <div className="w-[380px] min-w-[380px] border-l border-border bg-card flex flex-col h-full overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border shrink-0">
        <div className="flex items-center gap-2">
          <RefreshCw className="h-5 w-5 text-cyan-500" />
          <h2 className="font-semibold">Loop Step</h2>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Step Name */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Step Name</label>
          <Input value={data.name} readOnly className="bg-muted" />
        </div>

        {/* Loop Mode */}
        <div className="space-y-3">
          <label className="text-sm font-medium">Loop Mode</label>
          <div className="space-y-2">
            {LOOP_MODE_OPTIONS.map((option) => (
              <label
                key={option.value}
                className={`flex items-start gap-3 p-3 rounded border cursor-pointer transition-colors ${
                  data.loopMode === option.value
                    ? "border-cyan-500/50 bg-cyan-500/5"
                    : "hover:bg-muted/50"
                }`}
              >
                <input
                  type="radio"
                  name="loopMode"
                  value={option.value}
                  checked={data.loopMode === option.value}
                  onChange={() => {}}
                  className="mt-0.5"
                />
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-cyan-500">{option.icon}</span>
                  <div>
                    <div className="text-sm font-medium">{option.label}</div>
                    <div className="text-xs text-muted-foreground">{option.description}</div>
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Count Mode: Max Iterations */}
        {data.loopMode === "count" && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Max Iterations</label>
            <Input
              type="number"
              value={data.maxIterations}
              min={1}
              max={100}
              readOnly
              className="bg-muted"
            />
          </div>
        )}

        {/* Foreach Mode: Over Expression */}
        {data.loopMode === "foreach" && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Iterate Over</label>
              <Textarea
                value={data.over || ""}
                placeholder='["item1", "item2", "item3"] or ${steps.X.output}'
                readOnly
                rows={2}
                className="bg-muted font-mono text-xs"
              />
              <p className="text-xs text-muted-foreground">
                JSON array, template variable, or comma-separated values
              </p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Item Variable Name</label>
              <Input
                value={data.itemVariable || "item"}
                readOnly
                className="bg-muted font-mono"
              />
              <p className="text-xs text-muted-foreground">
                Access via {"${loop.item}"} in step inputs
              </p>
            </div>
          </div>
        )}

        {/* Until Mode: Exit Condition */}
        {data.loopMode === "until" && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Exit Condition</label>
            <Textarea
              value={data.exitCondition || ""}
              placeholder='${previous} contains "done"'
              readOnly
              rows={2}
              className="bg-muted font-mono text-xs"
            />
            <p className="text-xs text-muted-foreground">
              Loop exits when this evaluates to &quot;true&quot;, &quot;done&quot;, or &quot;complete&quot;
            </p>
          </div>
        )}

        {/* Inner Steps Configuration */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Loop Steps</label>
            <Badge variant="secondary" className="text-xs">
              {data.innerSteps.length} step{data.innerSteps.length !== 1 ? "s" : ""}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            These steps execute in each iteration. All must complete before the next iteration.
          </p>

          {/* Step list */}
          <div className="space-y-2">
            {data.innerSteps.map((step, index) => (
              <div key={step.id} className="p-3 rounded border bg-muted/50 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className={`h-4 w-4 ${step.agentId ? "text-cyan-500" : "text-gray-400"}`} />
                    <span className="text-sm font-medium">
                      {step.agentName || `Step ${index + 1}`}
                    </span>
                  </div>
                  <Button variant="ghost" size="icon" className="h-6 w-6">
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>

                {/* Agent selector */}
                {!step.agentId && (
                  <Select>
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue placeholder="Select agent..." />
                    </SelectTrigger>
                    <SelectContent>
                      {agents.map((agent) => (
                        <SelectItem key={agent.id} value={agent.id}>
                          <div className="flex items-center gap-2">
                            <Bot className="h-3 w-3" />
                            <span>{agent.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}

                {/* Input template */}
                <div className="text-xs text-muted-foreground font-mono truncate">
                  Input: {step.input || "${user_input}"}
                </div>
              </div>
            ))}
          </div>

          {/* Add step button */}
          <Button variant="outline" size="sm" className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            Add Step
          </Button>
        </div>

        {/* Advanced Options */}
        <div className="space-y-3">
          <label className="text-sm font-medium">Advanced Options</label>

          {/* Break Condition */}
          <div className="space-y-2">
            <label className="text-xs text-muted-foreground">Break Condition (Optional)</label>
            <Input
              value={data.breakCondition || ""}
              placeholder="Exit loop early when..."
              readOnly
              className="bg-muted font-mono text-xs"
            />
          </div>

          {/* Continue Condition */}
          <div className="space-y-2">
            <label className="text-xs text-muted-foreground">Continue Condition (Optional)</label>
            <Input
              value={data.continueCondition || ""}
              placeholder="Skip iteration when..."
              readOnly
              className="bg-muted font-mono text-xs"
            />
          </div>

          {/* Collect Results Toggle */}
          <label className="flex items-center gap-3 p-3 rounded border cursor-pointer">
            <input
              type="checkbox"
              checked={data.collectResults}
              onChange={() => {}}
              className="h-4 w-4"
            />
            <div>
              <div className="text-sm font-medium">Collect Results</div>
              <div className="text-xs text-muted-foreground">
                Store all iteration outputs in an array
              </div>
            </div>
          </label>
        </div>

        {/* Loop Variables Reference */}
        <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-3">
          <div className="text-xs text-cyan-600 font-medium mb-2">Loop Variables</div>
          <div className="space-y-1 text-xs font-mono text-muted-foreground">
            <div><span className="text-cyan-600">{"${loop.index}"}</span> - Current iteration (1-based)</div>
            <div><span className="text-cyan-600">{"${loop.item}"}</span> - Current item (foreach)</div>
            <div><span className="text-cyan-600">{"${loop.previous}"}</span> - Last iteration output</div>
            <div><span className="text-cyan-600">{"${loop.total}"}</span> - Total iterations</div>
            <div><span className="text-cyan-600">{"${loop.first}"}</span> - Is first iteration</div>
            <div><span className="text-cyan-600">{"${loop.last}"}</span> - Is last iteration</div>
          </div>
        </div>
      </div>
    </div>
  );
}
