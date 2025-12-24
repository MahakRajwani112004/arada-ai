"use client";

import { Check, AlertTriangle, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { GenerateWorkflowResponse } from "@/types/workflow";

interface AIResourceStatusProps {
  response: GenerateWorkflowResponse;
}

export function AIResourceStatus({ response }: AIResourceStatusProps) {
  const existingAgentsUsed = response.existing_agents_used ?? [];
  const agentsToCreate = response.agents_to_create ?? [];
  const mcpsSuggested = response.mcps_suggested ?? [];

  const hasReusedAgents = existingAgentsUsed.length > 0;
  const hasMissingAgents = agentsToCreate.length > 0;
  const hasMCPSuggestions = mcpsSuggested.length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Resource Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Reused Agents */}
        {hasReusedAgents && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-green-400">
              <Check className="h-4 w-4" />
              <span className="text-sm font-medium">
                Reusing {existingAgentsUsed.length} agent
                {existingAgentsUsed.length > 1 ? "s" : ""}
              </span>
            </div>
            <ul className="space-y-1 pl-6">
              {existingAgentsUsed.map((agentId) => (
                <li key={agentId} className="text-sm text-muted-foreground">
                  <code className="rounded bg-secondary px-1.5 py-0.5 text-xs">
                    {agentId}
                  </code>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Missing Agents */}
        {hasMissingAgents && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-amber-400">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm font-medium">
                {agentsToCreate.length} agent
                {agentsToCreate.length > 1 ? "s" : ""} needed
              </span>
            </div>
            <ul className="space-y-1 pl-6">
              {agentsToCreate.map((agent, index) => (
                <li
                  key={agent.id || index}
                  className="text-sm text-muted-foreground"
                >
                  <code className="rounded bg-secondary px-1.5 py-0.5 text-xs">
                    {agent.id || agent.name || "Unknown agent"}
                  </code>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* MCP Suggestions */}
        {hasMCPSuggestions && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-blue-400">
              <Info className="h-4 w-4" />
              <span className="text-sm font-medium">MCP Suggestions</span>
            </div>
            <ul className="space-y-2 pl-6">
              {mcpsSuggested.map((mcp) => (
                <li key={mcp.template} className="text-sm">
                  <span className="text-muted-foreground">{mcp.template}</span>
                  <p className="text-xs text-muted-foreground/70">
                    {mcp.reason}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Ready Status */}
        {response.can_execute ? (
          <div className="rounded-md bg-green-500/10 px-3 py-2 text-sm text-green-400">
            Ready to run! All agents are available.
          </div>
        ) : (
          <div className="rounded-md bg-amber-500/10 px-3 py-2 text-sm text-amber-400">
            Create missing agents to run this workflow.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
