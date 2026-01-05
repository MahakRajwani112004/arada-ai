"use client";

import { Bot, GitBranch, Layers, Settings2, Workflow } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { OrchestratorConfig, AgentReference } from "@/types/agent";

interface OrchestratorDetailsProps {
  config: OrchestratorConfig;
}

function SubAgentCard({ agent }: { agent: AgentReference }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
        <Bot className="h-4 w-4 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium truncate">
            {agent.alias || agent.agent_id}
          </p>
          {agent.alias && (
            <Badge variant="outline" className="text-[10px] shrink-0">
              {agent.agent_id}
            </Badge>
          )}
        </div>
        {agent.description && (
          <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">
            {agent.description}
          </p>
        )}
      </div>
    </div>
  );
}

function SettingItem({
  icon: Icon,
  label,
  value,
  className,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-2 text-sm", className)}>
      <Icon className="h-4 w-4 text-muted-foreground" />
      <span className="text-muted-foreground">{label}:</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function getModeLabel(mode: string): string {
  const labels: Record<string, string> = {
    sequential: "Sequential",
    parallel: "Parallel",
    adaptive: "Adaptive",
    hierarchical: "Hierarchical",
  };
  return labels[mode.toLowerCase()] || mode;
}

function getModeDescription(mode: string): string {
  const descriptions: Record<string, string> = {
    sequential: "Agents execute one after another in order",
    parallel: "Multiple agents execute simultaneously",
    adaptive: "Dynamically decides execution order based on context",
    hierarchical: "Agents organized in a hierarchy with delegation",
  };
  return descriptions[mode.toLowerCase()] || "Custom orchestration mode";
}

function getModeColor(mode: string): string {
  const colors: Record<string, string> = {
    sequential: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    parallel: "bg-green-500/10 text-green-500 border-green-500/20",
    adaptive: "bg-purple-500/10 text-purple-500 border-purple-500/20",
    hierarchical: "bg-orange-500/10 text-orange-500 border-orange-500/20",
  };
  return colors[mode.toLowerCase()] || "bg-gray-500/10 text-gray-500 border-gray-500/20";
}

export function OrchestratorDetails({ config }: OrchestratorDetailsProps) {
  const hasSubAgents = config.available_agents && config.available_agents.length > 0;

  return (
    <div className="space-y-4">
      {/* Orchestration Mode */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Workflow className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">Orchestration Mode</CardTitle>
            </div>
            <Badge variant="outline" className={cn("gap-1", getModeColor(config.mode))}>
              <GitBranch className="h-3 w-3" />
              {getModeLabel(config.mode)}
            </Badge>
          </div>
          <CardDescription>{getModeDescription(config.mode)}</CardDescription>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <SettingItem
              icon={Layers}
              label="Max Parallel"
              value={config.max_parallel}
            />
            <SettingItem
              icon={Layers}
              label="Max Depth"
              value={config.max_depth}
            />
            <SettingItem
              icon={Settings2}
              label="Aggregation"
              value={config.default_aggregation}
            />
            <SettingItem
              icon={Settings2}
              label="Self Reference"
              value={config.allow_self_reference ? "Allowed" : "Disabled"}
            />
          </div>
        </CardContent>
      </Card>

      {/* Available Sub-Agents */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Available Agents</CardTitle>
              <CardDescription>
                {hasSubAgents
                  ? `${config.available_agents.length} agent${config.available_agents.length !== 1 ? 's' : ''} available for orchestration`
                  : "No sub-agents configured"}
              </CardDescription>
            </div>
            {hasSubAgents && (
              <Badge variant="secondary" className="text-xs">
                {config.available_agents.length}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {hasSubAgents ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {config.available_agents.map((agent) => (
                <SubAgentCard key={agent.agent_id} agent={agent} />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-6 text-muted-foreground">
              <Bot className="h-10 w-10 mb-2 opacity-50" />
              <p className="text-sm font-medium">No sub-agents configured</p>
              <p className="text-xs">Add agents in the Configuration tab</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Workflow Definition (if present) */}
      {config.workflow_definition && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Workflow Definition</CardTitle>
            <CardDescription>Custom workflow logic</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="p-3 rounded-lg bg-muted text-xs overflow-x-auto">
              <code>{config.workflow_definition}</code>
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
