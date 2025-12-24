"use client";

import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";
import type { MCPServer, MCPCatalogItem } from "@/types/mcp";

interface SelectedToolsDisplayProps {
  selectedTools: string[];
  servers?: MCPServer[];
  catalog?: MCPCatalogItem[];
  onRemove: (toolId: string) => void;
}

export function SelectedToolsDisplay({
  selectedTools,
  servers,
  catalog,
  onRemove,
}: SelectedToolsDisplayProps) {
  if (selectedTools.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No tools selected</p>
    );
  }

  const getServerName = (serverId: string) => {
    const server = servers?.find((s) => s.id === serverId);
    if (server) {
      const template = catalog?.find((c) => c.id === server.template);
      return template?.name || server.name;
    }
    return serverId;
  };

  return (
    <div className="flex flex-wrap gap-2">
      {selectedTools.map((toolId) => {
        const [serverId, toolName] = toolId.split(":");
        return (
          <Badge key={toolId} variant="secondary" className="gap-1 pr-1">
            <span>{toolName}</span>
            <span className="text-xs text-muted-foreground">
              ({getServerName(serverId)})
            </span>
            <button
              type="button"
              onClick={() => onRemove(toolId)}
              className="ml-1 hover:bg-muted rounded-full p-0.5"
            >
              <X className="h-3 w-3" />
            </button>
          </Badge>
        );
      })}
    </div>
  );
}
