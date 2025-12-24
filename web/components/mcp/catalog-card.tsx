"use client";

import { Calendar, Mail, HardDrive, MessageSquare, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { MCPCatalogItem } from "@/types/mcp";

interface CatalogCardProps {
  item: MCPCatalogItem;
  onConnect: (item: MCPCatalogItem) => void;
  isConnected?: boolean;
}

const serviceIcons: Record<string, React.ReactNode> = {
  "google-calendar": <Calendar className="h-5 w-5" />,
  "google-gmail": <Mail className="h-5 w-5" />,
  "google-drive": <HardDrive className="h-5 w-5" />,
  "outlook-calendar": <Calendar className="h-5 w-5" />,
  "outlook-email": <Mail className="h-5 w-5" />,
  slack: <MessageSquare className="h-5 w-5" />,
};

const serviceColors: Record<string, string> = {
  "google-calendar": "bg-blue-50 text-blue-600",
  "google-gmail": "bg-red-50 text-red-600",
  "google-drive": "bg-amber-50 text-amber-600",
  "outlook-calendar": "bg-sky-50 text-sky-600",
  "outlook-email": "bg-sky-50 text-sky-600",
  slack: "bg-purple-50 text-purple-600",
};

export function CatalogCard({ item, onConnect, isConnected }: CatalogCardProps) {
  const icon = serviceIcons[item.id] || <ExternalLink className="h-5 w-5" />;
  const color = serviceColors[item.id] || "bg-secondary text-muted-foreground";

  return (
    <Card className="h-full border-border/60 shadow-sm transition-all duration-200 hover:border-primary/40 hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
              {icon}
            </div>
            <div>
              <h3 className="font-semibold leading-none tracking-tight">
                {item.name}
              </h3>
              <p className="mt-1 text-xs text-muted-foreground">
                {item.auth_type === "oauth_token" ? "OAuth" : item.auth_type}
              </p>
            </div>
          </div>
          {isConnected && (
            <Badge variant="outline" className="bg-emerald-50 text-emerald-600 border-emerald-200">
              Connected
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2">
            Available Tools
          </p>
          <div className="flex flex-wrap gap-1">
            {item.tools.slice(0, 4).map((tool) => (
              <Badge key={tool} variant="secondary" className="text-xs">
                {tool}
              </Badge>
            ))}
            {item.tools.length > 4 && (
              <Badge variant="secondary" className="text-xs">
                +{item.tools.length - 4}
              </Badge>
            )}
          </div>
        </div>
        <Button
          className="w-full"
          variant={isConnected ? "outline" : "default"}
          onClick={() => onConnect(item)}
        >
          {isConnected ? "Manage" : "Connect"}
        </Button>
      </CardContent>
    </Card>
  );
}
