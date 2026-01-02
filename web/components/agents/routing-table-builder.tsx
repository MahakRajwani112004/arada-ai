"use client";

import { useState } from "react";
import { Plus, Trash2, GitBranch, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Agent, RouterConfig, RoutingEntry } from "@/types/agent";

interface RoutingTableBuilderProps {
  config: RouterConfig;
  onChange: (config: RouterConfig) => void;
  agents: Agent[];
}

export function RoutingTableBuilder({
  config,
  onChange,
  agents,
}: RoutingTableBuilderProps) {
  const [newRouteName, setNewRouteName] = useState("");

  const routes = Object.entries(config.routing_table || {});

  const handleAddRoute = () => {
    if (!newRouteName.trim()) return;

    const newTable = {
      ...config.routing_table,
      [newRouteName.toLowerCase()]: {
        target_agent: "",
        description: "",
      },
    };

    onChange({
      ...config,
      routing_table: newTable,
    });
    setNewRouteName("");
  };

  const handleRemoveRoute = (routeName: string) => {
    const newTable = { ...config.routing_table };
    delete newTable[routeName];
    onChange({
      ...config,
      routing_table: newTable,
    });
  };

  const handleUpdateRoute = (
    routeName: string,
    field: keyof RoutingEntry,
    value: string
  ) => {
    onChange({
      ...config,
      routing_table: {
        ...config.routing_table,
        [routeName]: {
          ...config.routing_table[routeName],
          [field]: value,
        },
      },
    });
  };

  const handleThresholdChange = (value: number[]) => {
    onChange({
      ...config,
      confidence_threshold: value[0],
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2 text-sm font-medium">
        <GitBranch className="h-4 w-4 text-blue-500" />
        <span>Routing Configuration</span>
      </div>

      <p className="text-sm text-muted-foreground">
        Define how user intents are classified and routed to different agents.
        Each route maps a classification category to a target agent.
      </p>

      {/* Routing Table */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Routes</Label>

        {routes.length === 0 ? (
          <div className="p-4 border border-dashed rounded-lg text-center text-sm text-muted-foreground">
            No routes configured. Add your first route below.
          </div>
        ) : (
          <div className="space-y-2">
            {routes.map(([routeName, entry]) => (
              <div
                key={routeName}
                className="flex items-start gap-2 p-3 rounded-lg border bg-muted/30"
              >
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium bg-blue-500/10 text-blue-600 px-2 py-0.5 rounded">
                      {routeName}
                    </span>
                    <span className="text-xs text-muted-foreground">→</span>
                  </div>

                  {/* Target Agent Selector */}
                  <Select
                    value={entry.target_agent || ""}
                    onValueChange={(value) =>
                      handleUpdateRoute(routeName, "target_agent", value)
                    }
                  >
                    <SelectTrigger className="h-9">
                      <SelectValue placeholder="Select target agent..." />
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

                  {/* Description */}
                  <Input
                    placeholder="Description (optional)..."
                    value={entry.description || ""}
                    onChange={(e) =>
                      handleUpdateRoute(routeName, "description", e.target.value)
                    }
                    className="h-8 text-xs"
                  />
                </div>

                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 shrink-0"
                  onClick={() => handleRemoveRoute(routeName)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* Add Route */}
        <div className="flex gap-2">
          <Input
            placeholder="Route name (e.g., calendar, email, support)..."
            value={newRouteName}
            onChange={(e) => setNewRouteName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleAddRoute();
              }
            }}
            className="flex-1"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={handleAddRoute}
            disabled={!newRouteName.trim()}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add
          </Button>
        </div>
      </div>

      {/* Confidence Threshold */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-sm font-medium">Confidence Threshold</Label>
          <span className="text-sm text-muted-foreground">
            {((config.confidence_threshold ?? 0.7) * 100).toFixed(0)}%
          </span>
        </div>
        <Slider
          value={[config.confidence_threshold ?? 0.7]}
          onValueChange={handleThresholdChange}
          min={0}
          max={1}
          step={0.05}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          Minimum confidence required to route to a specific agent. If below threshold,
          the default route will be used.
        </p>
      </div>

      {/* Help Text */}
      <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">
        <div className="text-xs text-blue-600 font-medium mb-1">How it works</div>
        <p className="text-xs text-muted-foreground">
          1. User sends a message to this agent<br />
          2. The LLM classifies the intent into one of your defined routes<br />
          3. The request is forwarded to the corresponding target agent<br />
          4. The target agent&apos;s response is returned to the user
        </p>
      </div>
    </div>
  );
}
