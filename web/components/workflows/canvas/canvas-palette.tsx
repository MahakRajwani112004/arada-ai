"use client";

import { useState } from "react";
import { Bot, ChevronLeft, ChevronRight, Plus, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AgentCreationSheet } from "@/components/agents/agent-creation-sheet";
import type { Agent } from "@/types/agent";

interface CanvasPaletteProps {
  isOpen: boolean;
  onToggle: () => void;
  agents: Agent[];
  onAddStep?: () => void;
  onDragStart?: (agent: Agent) => void;
  onAgentCreated?: (agent: Agent) => void;
}

export function CanvasPalette({
  isOpen,
  onToggle,
  agents,
  onAddStep,
  onDragStart,
  onAgentCreated,
}: CanvasPaletteProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showAgentSheet, setShowAgentSheet] = useState(false);

  const filteredAgents = agents.filter((agent) =>
    agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    agent.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isOpen) {
    return (
      <div className="w-10 border-r border-border bg-card flex flex-col items-center py-2 shrink-0">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onToggle}
          title="Open palette"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className="w-64 border-r border-border bg-card flex flex-col shrink-0 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-border shrink-0">
        <h3 className="font-semibold text-sm">Palette</h3>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onToggle}
          title="Close palette"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Quick Add */}
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Quick Add
          </h4>
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={onAddStep}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Step
          </Button>
        </div>

        {/* Agents */}
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Existing Agents
          </h4>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search agents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9 text-sm"
            />
          </div>

          {/* Agent List */}
          <div className="space-y-1.5">
            {filteredAgents.length === 0 ? (
              <p className="text-xs text-muted-foreground py-4 text-center">
                {searchQuery ? "No agents found" : "No agents yet"}
              </p>
            ) : (
              filteredAgents.map((agent) => (
                <div
                  key={agent.id}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData("application/agent", JSON.stringify(agent));
                    onDragStart?.(agent);
                  }}
                  className="flex items-center gap-2 p-2 rounded-md border border-border bg-card hover:bg-accent cursor-grab active:cursor-grabbing transition-colors"
                  title={`Drag to add ${agent.name} to workflow`}
                >
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-purple-500/10">
                    <Bot className="h-3.5 w-3.5 text-purple-500" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium truncate">{agent.name}</div>
                    <div className="text-xs text-muted-foreground truncate">
                      {agent.agent_type}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Create New Agent */}
        <div className="pt-2 border-t border-border">
          <Button
            variant="ghost"
            className="w-full justify-start text-muted-foreground hover:text-foreground"
            size="sm"
            onClick={() => setShowAgentSheet(true)}
          >
            <Plus className="h-4 w-4 mr-2" />
            Create New Agent
          </Button>
        </div>
      </div>

      {/* Agent Creation Sheet */}
      <AgentCreationSheet
        open={showAgentSheet}
        onOpenChange={setShowAgentSheet}
        context="From workflow canvas"
        onAgentCreated={(agent) => {
          onAgentCreated?.(agent);
          setShowAgentSheet(false);
        }}
      />
    </div>
  );
}
