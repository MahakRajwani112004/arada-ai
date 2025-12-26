"use client";

import { useState } from "react";
import { Plug, Loader2, RefreshCw, Trash2, Key, ChevronDown, ChevronUp, AlertTriangle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { CatalogCard } from "@/components/mcp/catalog-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCatalog, useServers, useCreateServer, useDeleteServer, useReconnectServer } from "@/lib/hooks/use-mcp";
import { useSecretsStats, useSecrets, useDeleteSecret } from "@/lib/hooks/use-secrets";
import { getOAuthUrl, getMicrosoftOAuthUrl } from "@/lib/api/mcp";
import type { MCPCatalogItem, MCPServer } from "@/types/mcp";

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

function CatalogSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-start gap-3">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <div className="flex-1">
          <Skeleton className="h-5 w-28" />
          <Skeleton className="mt-1 h-3 w-16" />
        </div>
      </div>
      <Skeleton className="mt-4 h-4 w-20" />
      <div className="mt-2 flex gap-1">
        <Skeleton className="h-5 w-16" />
        <Skeleton className="h-5 w-20" />
        <Skeleton className="h-5 w-14" />
      </div>
      <Skeleton className="mt-4 h-9 w-full" />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 py-16">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-secondary">
        <Plug className="h-7 w-7 text-muted-foreground" />
      </div>
      <h3 className="mt-4 text-lg font-semibold">No integrations available</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Check back later for new integrations
      </p>
    </div>
  );
}

// Connected server card component
function ConnectedServerCard({
  server,
  onReconnect,
  onDisconnect,
  isReconnecting,
  isDisconnecting,
}: {
  server: MCPServer;
  onReconnect: () => void;
  onDisconnect: () => void;
  isReconnecting: boolean;
  isDisconnecting: boolean;
}) {
  const isGoogleOAuth = server.template ? !!googleOAuthServices[server.template] : false;
  const isMicrosoftOAuth = server.template ? !!microsoftOAuthServices[server.template] : false;
  const isOAuthService = isGoogleOAuth || isMicrosoftOAuth;

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-medium">{server.name}</h3>
          <p className="text-sm text-muted-foreground">{server.template}</p>
        </div>
        <Badge variant={server.status === "active" ? "default" : "secondary"}>
          {server.status}
        </Badge>
      </div>
      {server.error_message && (
        <p className="mt-2 text-sm text-destructive">{server.error_message}</p>
      )}
      <div className="mt-4 flex gap-2">
        {isOAuthService && (
          <Button
            variant="outline"
            size="sm"
            onClick={onReconnect}
            disabled={isReconnecting}
          >
            {isReconnecting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Reconnect
          </Button>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={onDisconnect}
          disabled={isDisconnecting}
          className="text-destructive hover:text-destructive"
        >
          {isDisconnecting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="mr-2 h-4 w-4" />
          )}
          Disconnect
        </Button>
      </div>
    </div>
  );
}

export default function IntegrationsPage() {
  const { data: catalog, isLoading: catalogLoading } = useCatalog();
  const { data: servers } = useServers();
  const { data: secretsStats } = useSecretsStats();
  const { data: secrets } = useSecrets();
  const createServer = useCreateServer();
  const deleteServer = useDeleteServer();
  const reconnectServer = useReconnectServer();
  const deleteSecret = useDeleteSecret();

  const [selectedItem, setSelectedItem] = useState<MCPCatalogItem | null>(null);
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [serverName, setServerName] = useState("");
  const [isOAuthLoading, setIsOAuthLoading] = useState(false);
  const [showSecrets, setShowSecrets] = useState(false);
  const [reconnectingServerId, setReconnectingServerId] = useState<string | null>(null);

  const connectedTemplates = new Set(
    servers?.servers.map((s) => s.template).filter(Boolean)
  );

  const connectedServers = servers?.servers || [];
  const isGoogleOAuth = selectedItem ? !!googleOAuthServices[selectedItem.id] : false;
  const isMicrosoftOAuth = selectedItem ? !!microsoftOAuthServices[selectedItem.id] : false;
  const isOAuthService = isGoogleOAuth || isMicrosoftOAuth;

  const handleConnect = (item: MCPCatalogItem) => {
    setSelectedItem(item);
    setServerName(`My ${item.name}`);
    setCredentials({});
  };

  const handleGoogleOAuth = async () => {
    if (!selectedItem) return;

    const oauthService = googleOAuthServices[selectedItem.id];
    if (!oauthService) return;

    setIsOAuthLoading(true);
    try {
      // Store server name in localStorage for the callback page
      localStorage.setItem("oauth_server_name", serverName);

      const { authorization_url } = await getOAuthUrl(oauthService);
      window.location.href = authorization_url;
    } catch (error) {
      console.error("Failed to get OAuth URL:", error);
      setIsOAuthLoading(false);
    }
  };

  const handleMicrosoftOAuth = async () => {
    if (!selectedItem) return;

    const oauthService = microsoftOAuthServices[selectedItem.id];
    if (!oauthService) return;

    setIsOAuthLoading(true);
    try {
      // Store server name and template in localStorage for the callback page
      localStorage.setItem("oauth_server_name", serverName);
      localStorage.setItem("oauth_template", selectedItem.id);

      const { authorization_url } = await getMicrosoftOAuthUrl(oauthService);
      window.location.href = authorization_url;
    } catch (error) {
      console.error("Failed to get Microsoft OAuth URL:", error);
      setIsOAuthLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedItem) return;

    await createServer.mutateAsync({
      template: selectedItem.id,
      name: serverName,
      credentials,
    });

    setSelectedItem(null);
    setCredentials({});
    setServerName("");
  };

  const handleReconnect = async (serverId: string) => {
    setReconnectingServerId(serverId);
    try {
      const { authorization_url } = await reconnectServer.mutateAsync(serverId);
      window.location.href = authorization_url;
    } catch (error) {
      console.error("Failed to initiate reconnect:", error);
      setReconnectingServerId(null);
    }
  };

  const handleDeleteOrphanedSecret = async (secretKey: string) => {
    await deleteSecret.mutateAsync(secretKey);
  };

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="Integrations"
          description="Connect MCP servers to enable tools for your agents"
        />

        {/* Connected Integrations Section */}
        {connectedServers.length > 0 && (
          <div className="mb-8">
            <h2 className="mb-4 text-lg font-semibold">Connected Integrations</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {connectedServers.map((server) => (
                <ConnectedServerCard
                  key={server.id}
                  server={server}
                  onReconnect={() => handleReconnect(server.id)}
                  onDisconnect={() => deleteServer.mutate(server.id)}
                  isReconnecting={reconnectingServerId === server.id}
                  isDisconnecting={deleteServer.isPending}
                />
              ))}
            </div>
          </div>
        )}

        {/* Secrets Summary - Collapsible */}
        {secretsStats && secretsStats.total > 0 && (
          <Collapsible open={showSecrets} onOpenChange={setShowSecrets} className="mb-8">
            <CollapsibleTrigger asChild>
              <Button variant="outline" className="w-full justify-between">
                <div className="flex items-center gap-2">
                  <Key className="h-4 w-4" />
                  <span>Stored Credentials</span>
                  <Badge variant="secondary">{secretsStats.total}</Badge>
                  {secretsStats.orphaned > 0 && (
                    <Badge variant="destructive" className="ml-2">
                      <AlertTriangle className="mr-1 h-3 w-3" />
                      {secretsStats.orphaned} orphaned
                    </Badge>
                  )}
                </div>
                {showSecrets ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-4">
              <div className="rounded-lg border border-border bg-card p-4">
                <div className="mb-4 flex gap-4 text-sm text-muted-foreground">
                  <span>OAuth Tokens: {secretsStats.oauth_tokens}</span>
                  <span>MCP Credentials: {secretsStats.mcp_credentials}</span>
                </div>
                <div className="space-y-2">
                  {secrets?.secrets.map((secret) => (
                    <div
                      key={secret.key}
                      className="flex items-center justify-between rounded-md border border-border bg-background p-3"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <code className="text-sm">{secret.key}</code>
                          {secret.is_orphaned && (
                            <Badge variant="destructive" className="text-xs">Orphaned</Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {secret.type === "oauth" ? `OAuth (${secret.provider} - ${secret.service})` : "MCP Credentials"}
                          {secret.linked_server_name && ` → ${secret.linked_server_name}`}
                        </p>
                      </div>
                      {secret.is_orphaned && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteOrphanedSecret(secret.key)}
                          disabled={deleteSecret.isPending}
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Available Integrations */}
        <h2 className="mb-4 text-lg font-semibold">Available Integrations</h2>

        {catalogLoading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <CatalogSkeleton key={i} />
            ))}
          </div>
        )}

        {catalog && catalog.servers.length === 0 && <EmptyState />}

        {catalog && catalog.servers.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {catalog.servers.map((item) => (
              <CatalogCard
                key={item.id}
                item={item}
                isConnected={connectedTemplates.has(item.id)}
                onConnect={handleConnect}
              />
            ))}
          </div>
        )}
      </PageContainer>

      <Sheet open={!!selectedItem} onOpenChange={() => setSelectedItem(null)}>
        <SheetContent className="sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Connect {selectedItem?.name}</SheetTitle>
            <SheetDescription>
              {isGoogleOAuth
                ? "Enter a name for this connection, then sign in with Google."
                : isMicrosoftOAuth
                  ? "Enter a name for this connection, then sign in with Microsoft."
                  : "Enter your credentials to connect this integration."}
            </SheetDescription>
          </SheetHeader>

          {selectedItem && (
            <div className="mt-6 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Connection Name</Label>
                <Input
                  id="name"
                  value={serverName}
                  onChange={(e) => setServerName(e.target.value)}
                  placeholder="e.g., Work Calendar"
                />
              </div>

              {/* Show credential fields only for non-OAuth services */}
              {!isOAuthService && selectedItem.credentials_required.map((cred) => (
                <div key={cred.name} className="space-y-2">
                  <Label htmlFor={cred.name}>{cred.description}</Label>
                  <Input
                    id={cred.name}
                    type={cred.sensitive ? "password" : "text"}
                    value={credentials[cred.name] || ""}
                    onChange={(e) =>
                      setCredentials((prev) => ({
                        ...prev,
                        [cred.name]: e.target.value,
                      }))
                    }
                    placeholder={cred.name}
                  />
                </div>
              ))}

              {!isOAuthService && selectedItem.token_guide_url && (
                <p className="text-xs text-muted-foreground">
                  Need help?{" "}
                  <a
                    href={selectedItem.token_guide_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Get your credentials here
                  </a>
                </p>
              )}

              {isGoogleOAuth ? (
                <Button
                  onClick={handleGoogleOAuth}
                  disabled={isOAuthLoading || !serverName.trim()}
                  className="w-full"
                >
                  {isOAuthLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isOAuthLoading ? "Redirecting..." : "Sign in with Google"}
                </Button>
              ) : isMicrosoftOAuth ? (
                <Button
                  onClick={handleMicrosoftOAuth}
                  disabled={isOAuthLoading || !serverName.trim()}
                  className="w-full"
                >
                  {isOAuthLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isOAuthLoading ? "Redirecting..." : "Sign in with Microsoft"}
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={createServer.isPending}
                  className="w-full"
                >
                  {createServer.isPending ? "Connecting..." : "Connect"}
                </Button>
              )}
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}
