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

// Map template IDs to OAuth service names
const googleOAuthServices: Record<string, string> = {
  "google-calendar": "calendar",
  "gmail": "gmail",
  "google-drive": "drive",
};

const microsoftOAuthServices: Record<string, string> = {
  "outlook-calendar": "calendar",
  "outlook-email": "email",
};

const serviceIcons: Record<string, React.ReactNode> = {
  "google-calendar": <Calendar className="h-5 w-5" />,
  "gmail": <Mail className="h-5 w-5" />,
  "google-drive": <HardDrive className="h-5 w-5" />,
  "outlook-calendar": <Calendar className="h-5 w-5" />,
  "outlook-email": <Mail className="h-5 w-5" />,
  slack: <MessageSquare className="h-5 w-5" />,
};

const serviceColors: Record<string, string> = {
  "google-calendar": "bg-blue-500/10 text-blue-400",
  "gmail": "bg-red-500/10 text-red-400",
  "google-drive": "bg-yellow-500/10 text-yellow-400",
  "outlook-calendar": "bg-blue-600/10 text-blue-300",
  "outlook-email": "bg-blue-600/10 text-blue-300",
  slack: "bg-purple-500/10 text-purple-400",
};

export function CatalogCard({ item, onConnect, isConnected }: CatalogCardProps) {
  const icon = serviceIcons[item.id] || <ExternalLink className="h-5 w-5" />;
  const color = serviceColors[item.id] || "bg-secondary text-muted-foreground";
  const isGoogleOAuth = !!googleOAuthServices[item.id];
  const isMicrosoftOAuth = !!microsoftOAuthServices[item.id];

  const handleClick = () => {
    // Always use onConnect to open the sheet for name input
    onConnect(item);
  };

  const getButtonText = () => {
    if (isConnected) return "Manage";
    if (isGoogleOAuth) return "Sign in with Google";
    if (isMicrosoftOAuth) return "Sign in with Microsoft";
    return "Connect";
  };

  return (
    <Card className="h-full transition-all hover:border-primary/50">
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
            <Badge variant="outline" className="bg-success/10 text-success border-success/20">
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
          onClick={handleClick}
        >
          {getButtonText()}
        </Button>
      </CardContent>
    </Card>
  );
}
