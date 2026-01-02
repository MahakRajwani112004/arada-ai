"use client";

import { useState } from "react";
import { Plus, Trash2, Workflow, Bot, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import type { Agent, OrchestratorConfig, AgentReference } from "@/types/agent";

interface OrchestratorConfigBuilderProps {
  config: OrchestratorConfig;
  onChange: (config: OrchestratorConfig) => void;
  agents: Agent[];
}

const ORCHESTRATION_MODES = [
  {
    value: "fanout",
    label: "Fanout",
    description: "Classify query, run relevant agents in parallel, synthesize results",
  },
  {
    value: "llm_driven",
    label: "LLM Driven",
    description: "LLM decides which agents to call based on the task",
  },
  {
    value: "workflow",
    label: "Workflow",
    description: "Follow a predefined workflow definition",
  },
  {
    value: "hybrid",
    label: "Hybrid",
    description: "LLM can deviate from workflow when needed",
  },
];

const AGGREGATION_STRATEGIES = [
  { value: "all", label: "All", description: "Return all agent results" },
  { value: "first", label: "First", description: "Return first successful result" },
  { value: "merge", label: "Merge", description: "Combine results into one" },
  { value: "best", label: "Best", description: "LLM selects best result" },
];

export function OrchestratorConfigBuilder({
  config,
  onChange,
  agents,
}: OrchestratorConfigBuilderProps) {
  const [selectedAgentId, setSelectedAgentId] = useState("");

  const handleAddAgent = () => {
    if (!selectedAgentId) return;

    const agent = agents.find((a) => a.id === selectedAgentId);
    if (!agent) return;

    // Check if already added
    if (config.available_agents.some((a) => a.agent_id === selectedAgentId)) {
      return;
    }

    onChange({
      ...config,
      available_agents: [
        ...config.available_agents,
        {
          agent_id: selectedAgentId,
          alias: agent.name.toLowerCase().replace(/\s+/g, "_"),
          description: agent.description || null,
        },
      ],
    });
    setSelectedAgentId("");
  };

  const handleRemoveAgent = (agentId: string) => {
    onChange({
      ...config,
      available_agents: config.available_agents.filter(
        (a) => a.agent_id !== agentId
      ),
    });
  };

  const handleUpdateAgent = (
    agentId: string,
    field: keyof AgentReference,
    value: string | null
  ) => {
    onChange({
      ...config,
      available_agents: config.available_agents.map((a) =>
        a.agent_id === agentId ? { ...a, [field]: value } : a
      ),
    });
  };

  const availableAgentIds = config.available_agents.map((a) => a.agent_id);
  const unaddedAgents = agents.filter((a) => !availableAgentIds.includes(a.id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2 text-sm font-medium">
        <Workflow className="h-4 w-4 text-purple-500" />
        <span>Orchestrator Configuration</span>
      </div>

      <p className="text-sm text-muted-foreground">
        Configure how this orchestrator coordinates multiple agents to complete
        complex tasks.
      </p>

      {/* Mode Selection */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Orchestration Mode</Label>
        <div className="grid gap-2">
          {ORCHESTRATION_MODES.map((mode) => (
            <label
              key={mode.value}
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                config.mode === mode.value
                  ? "border-purple-500/50 bg-purple-500/5"
                  : "hover:bg-muted/50"
              }`}
            >
              <input
                type="radio"
                name="mode"
                value={mode.value}
                checked={config.mode === mode.value}
                onChange={() => onChange({ ...config, mode: mode.value })}
                className="mt-1"
              />
              <div>
                <div className="text-sm font-medium">{mode.label}</div>
                <div className="text-xs text-muted-foreground">
                  {mode.description}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Available Agents */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-sm font-medium">Available Agents</Label>
          <span className="text-xs text-muted-foreground">
            {config.available_agents.length} agent
            {config.available_agents.length !== 1 ? "s" : ""}
          </span>
        </div>

        {config.available_agents.length === 0 ? (
          <div className="p-4 border border-dashed rounded-lg text-center text-sm text-muted-foreground">
            No agents added. Add agents that this orchestrator can coordinate.
          </div>
        ) : (
          <div className="space-y-2">
            {config.available_agents.map((agentRef) => {
              const agent = agents.find((a) => a.id === agentRef.agent_id);
              return (
                <div
                  key={agentRef.agent_id}
                  className="p-3 rounded-lg border bg-muted/30 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4 text-purple-500" />
                      <span className="text-sm font-medium">
                        {agent?.name || agentRef.agent_id}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => handleRemoveAgent(agentRef.agent_id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label className="text-xs text-muted-foreground">Alias</Label>
                      <Input
                        value={agentRef.alias || ""}
                        onChange={(e) =>
                          handleUpdateAgent(agentRef.agent_id, "alias", e.target.value)
                        }
                        placeholder="e.g., calendar"
                        className="h-8 text-xs"
                      />
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">
                        Description Override
                      </Label>
                      <Input
                        value={agentRef.description || ""}
                        onChange={(e) =>
                          handleUpdateAgent(
                            agentRef.agent_id,
                            "description",
                            e.target.value || null
                          )
                        }
                        placeholder="Optional..."
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Add Agent */}
        <div className="flex gap-2">
          <Select value={selectedAgentId} onValueChange={setSelectedAgentId}>
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Select an agent to add..." />
            </SelectTrigger>
            <SelectContent>
              {unaddedAgents.length === 0 ? (
                <div className="p-2 text-sm text-muted-foreground text-center">
                  All agents already added
                </div>
              ) : (
                unaddedAgents.map((agent) => (
                  <SelectItem key={agent.id} value={agent.id}>
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4" />
                      <span>{agent.name}</span>
                    </div>
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={handleAddAgent}
            disabled={!selectedAgentId}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add
          </Button>
        </div>
      </div>

      {/* Aggregation Strategy */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-muted-foreground" />
          <Label className="text-sm font-medium">Default Aggregation</Label>
        </div>
        <Select
          value={config.default_aggregation}
          onValueChange={(value) =>
            onChange({ ...config, default_aggregation: value })
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {AGGREGATION_STRATEGIES.map((strategy) => (
              <SelectItem key={strategy.value} value={strategy.value}>
                <div>
                  <span className="font-medium">{strategy.label}</span>
                  <span className="text-muted-foreground ml-2">
                    - {strategy.description}
                  </span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Limits */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label className="text-sm font-medium">Max Parallel</Label>
          <Input
            type="number"
            min={1}
            max={10}
            value={config.max_parallel}
            onChange={(e) =>
              onChange({ ...config, max_parallel: parseInt(e.target.value) || 1 })
            }
          />
          <p className="text-xs text-muted-foreground">
            Max concurrent agent calls
          </p>
        </div>

        <div className="space-y-2">
          <Label className="text-sm font-medium">Max Depth</Label>
          <Input
            type="number"
            min={1}
            max={5}
            value={config.max_depth}
            onChange={(e) =>
              onChange({ ...config, max_depth: parseInt(e.target.value) || 1 })
            }
          />
          <p className="text-xs text-muted-foreground">
            Max nested orchestrator depth
          </p>
        </div>
      </div>

      {/* Self Reference Toggle */}
      <div className="flex items-center justify-between p-3 rounded-lg border">
        <div>
          <Label className="text-sm font-medium">Allow Self Reference</Label>
          <p className="text-xs text-muted-foreground">
            Allow this orchestrator to call itself recursively
          </p>
        </div>
        <Switch
          checked={config.allow_self_reference}
          onCheckedChange={(checked) =>
            onChange({ ...config, allow_self_reference: checked })
          }
        />
      </div>

      {/* Help Text */}
      <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 p-3">
        <div className="text-xs text-purple-600 font-medium mb-1">How it works</div>
        <p className="text-xs text-muted-foreground">
          1. Orchestrator receives a complex task<br />
          2. LLM analyzes which agents are needed<br />
          3. Calls agents (in parallel or sequence)<br />
          4. Aggregates results and returns final response
        </p>
      </div>
    </div>
  );
}
