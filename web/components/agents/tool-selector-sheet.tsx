"use client";

import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { ChevronRight, ChevronLeft, Server } from "lucide-react";
import { useServers, useCatalog } from "@/lib/hooks/use-mcp";
import { cn } from "@/lib/utils";

interface ToolSelectorSheetProps {
  selectedTools: string[];
  onToolsChange: (tools: string[]) => void;
  trigger?: React.ReactNode;
}

export function ToolSelectorSheet({
  selectedTools,
  onToolsChange,
  trigger,
}: ToolSelectorSheetProps) {
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<"servers" | "tools">("servers");
  const [activeServerId, setActiveServerId] = useState<string | null>(null);

  const { data: servers } = useServers();
  const { data: catalog } = useCatalog();

  // Build server list with tool counts
  const serversWithTools =
    servers?.servers
      .map((server) => {
        const template = catalog?.servers.find((c) => c.id === server.template);
        const tools = template?.tools || [];
        const selectedCount = selectedTools.filter((t) =>
          t.startsWith(`${server.id}:`)
        ).length;
        return { server, template, tools, selectedCount };
      })
      .filter((s) => s.tools.length > 0) || [];

  const activeServer = serversWithTools.find(
    (s) => s.server.id === activeServerId
  );

  const handleServerClick = (serverId: string) => {
    setActiveServerId(serverId);
    setView("tools");
  };

  const handleBack = () => {
    setView("servers");
    setActiveServerId(null);
  };

  const toggleTool = (toolName: string) => {
    if (!activeServerId) return;
    const toolId = `${activeServerId}:${toolName}`;
    if (selectedTools.includes(toolId)) {
      onToolsChange(selectedTools.filter((t) => t !== toolId));
    } else {
      onToolsChange([...selectedTools, toolId]);
    }
  };

  const selectAllFromServer = () => {
    if (!activeServer) return;
    const serverTools = activeServer.tools.map(
      (t) => `${activeServer.server.id}:${t}`
    );
    const otherTools = selectedTools.filter(
      (t) => !t.startsWith(`${activeServer.server.id}:`)
    );
    onToolsChange([...otherTools, ...serverTools]);
  };

  const clearAllFromServer = () => {
    if (!activeServer) return;
    onToolsChange(
      selectedTools.filter((t) => !t.startsWith(`${activeServer.server.id}:`))
    );
  };

  // Reset view when sheet closes
  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (!isOpen) {
      setView("servers");
      setActiveServerId(null);
    }
  };

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            Select Tools ({selectedTools.length})
          </Button>
        )}
      </SheetTrigger>
      <SheetContent side="right" className="w-[400px] sm:w-[450px]">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            {view === "tools" && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={handleBack}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            )}
            {view === "servers"
              ? "Select Tools"
              : activeServer?.template?.name || "Tools"}
          </SheetTitle>
        </SheetHeader>

        <div className="mt-4">
          {view === "servers" ? (
            // Server List View
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Select an MCP server to browse its tools
              </p>
              {serversWithTools.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No connected servers with tools
                </div>
              ) : (
                <div className="space-y-2">
                  {serversWithTools.map(
                    ({ server, template, tools, selectedCount }) => (
                      <button
                        key={server.id}
                        onClick={() => handleServerClick(server.id)}
                        className="w-full flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors text-left"
                      >
                        <div className="flex items-center gap-3">
                          <Server className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <div className="font-medium">
                              {template?.name || server.template}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {server.name}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {tools.length} tools{" "}
                              {selectedCount > 0 &&
                                `• ${selectedCount} selected`}
                            </div>
                          </div>
                        </div>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </button>
                    )
                  )}
                </div>
              )}
            </div>
          ) : (
            // Tool List View
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                {activeServer?.server.name}
              </p>
              <div className="space-y-2">
                {activeServer?.tools.map((toolName) => {
                  const toolId = `${activeServer.server.id}:${toolName}`;
                  const isSelected = selectedTools.includes(toolId);
                  return (
                    <div
                      key={toolName}
                      className={cn(
                        "flex items-center justify-between p-3 rounded-lg border",
                        isSelected && "border-primary bg-primary/5"
                      )}
                    >
                      <div>
                        <div className="font-medium">{toolName}</div>
                      </div>
                      <Switch
                        checked={isSelected}
                        onCheckedChange={() => toggleTool(toolName)}
                      />
                    </div>
                  );
                })}
              </div>
              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={selectAllFromServer}
                >
                  Select All
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearAllFromServer}
                >
                  Clear All
                </Button>
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
