"use client";

import { Server, Trash2, RefreshCw, AlertCircle, CheckCircle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useServers, useDeleteServer, useMCPHealth } from "@/lib/hooks/use-mcp";
import type { ServerStatus } from "@/types/mcp";

const statusConfig: Record<ServerStatus, { label: string; icon: React.ReactNode; color: string }> = {
  active: {
    label: "Active",
    icon: <CheckCircle className="h-3 w-3" />,
    color: "bg-success/10 text-success border-success/20",
  },
  error: {
    label: "Error",
    icon: <AlertCircle className="h-3 w-3" />,
    color: "bg-destructive/10 text-destructive border-destructive/20",
  },
  disconnected: {
    label: "Disconnected",
    icon: <RefreshCw className="h-3 w-3" />,
    color: "bg-warning/10 text-warning border-warning/20",
  },
};

function ServerSkeleton() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="h-10 w-10 rounded-lg" />
          <div>
            <Skeleton className="h-5 w-32" />
            <Skeleton className="mt-1.5 h-4 w-20" />
          </div>
        </div>
        <Skeleton className="h-8 w-8" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-48" />
      </CardContent>
    </Card>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 py-16">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-secondary">
        <Server className="h-7 w-7 text-muted-foreground" />
      </div>
      <h3 className="mt-4 text-lg font-semibold">No servers connected</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Connect an integration to see your servers here
      </p>
      <Button asChild variant="outline" className="mt-6">
        <a href="/integrations">Browse Catalog</a>
      </Button>
    </div>
  );
}

export default function ServersPage() {
  const { data, isLoading, error, refetch } = useServers();
  const { data: health } = useMCPHealth();
  const deleteServer = useDeleteServer();

  const getServerStatus = (serverId: string): ServerStatus => {
    const serverHealth = health?.servers.find((s) => s.server_id === serverId);
    return serverHealth?.status || "disconnected";
  };

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="My Servers"
          description="Manage your connected MCP servers"
          actions={
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          }
        />

        {health && (
          <div className="mb-6 flex gap-4">
            <div className="flex items-center gap-2 text-sm">
              <div className="h-2 w-2 rounded-full bg-success" />
              <span className="text-muted-foreground">
                {health.total_active} Active
              </span>
            </div>
            {health.total_error > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <div className="h-2 w-2 rounded-full bg-destructive" />
                <span className="text-muted-foreground">
                  {health.total_error} Error
                </span>
              </div>
            )}
            {health.total_disconnected > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <div className="h-2 w-2 rounded-full bg-warning" />
                <span className="text-muted-foreground">
                  {health.total_disconnected} Disconnected
                </span>
              </div>
            )}
          </div>
        )}

        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2">
            {[...Array(4)].map((_, i) => (
              <ServerSkeleton key={i} />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive">
            Failed to load servers: {error.message}
          </div>
        )}

        {data && data.servers.length === 0 && <EmptyState />}

        {data && data.servers.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            {data.servers.map((server) => {
              const status = getServerStatus(server.id);
              const config = statusConfig[status];

              return (
                <Card key={server.id}>
                  <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary">
                        <Server className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div>
                        <h3 className="font-semibold leading-none tracking-tight">
                          {server.name}
                        </h3>
                        <Badge
                          variant="outline"
                          className={`mt-1.5 gap-1 ${config.color}`}
                        >
                          {config.icon}
                          {config.label}
                        </Badge>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={() => deleteServer.mutate(server.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      {server.template && (
                        <span className="capitalize">
                          {server.template.replace(/-/g, " ")}
                        </span>
                      )}
                      {server.last_used && (
                        <span className="ml-2">
                          &middot; Last used{" "}
                          {new Date(server.last_used).toLocaleDateString()}
                        </span>
                      )}
                    </p>
                    {server.error_message && (
                      <p className="mt-2 text-sm text-destructive">
                        {server.error_message}
                      </p>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </PageContainer>
    </>
  );
}
