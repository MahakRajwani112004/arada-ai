"use client";

import { useState } from "react";
import { Plug } from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { CatalogCard } from "@/components/mcp/catalog-card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCatalog, useServers, useCreateServer } from "@/lib/hooks/use-mcp";
import type { MCPCatalogItem } from "@/types/mcp";

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

export default function IntegrationsPage() {
  const { data: catalog, isLoading: catalogLoading } = useCatalog();
  const { data: servers } = useServers();
  const createServer = useCreateServer();

  const [selectedItem, setSelectedItem] = useState<MCPCatalogItem | null>(null);
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [serverName, setServerName] = useState("");

  const connectedTemplates = new Set(
    servers?.servers.map((s) => s.template).filter(Boolean)
  );

  const handleConnect = (item: MCPCatalogItem) => {
    setSelectedItem(item);
    setServerName(`My ${item.name}`);
    setCredentials({});
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

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="Integrations"
          description="Connect MCP servers to enable tools for your agents"
        />

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
              Enter your credentials to connect this integration.
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

              {selectedItem.credentials_required.map((cred) => (
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

              {selectedItem.token_guide_url && (
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

              <Button
                onClick={handleSubmit}
                disabled={createServer.isPending}
                className="w-full"
              >
                {createServer.isPending ? "Connecting..." : "Connect"}
              </Button>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}
