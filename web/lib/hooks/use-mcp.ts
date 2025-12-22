"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  getCatalog,
  getCatalogItem,
  listServers,
  getServer,
  createServer,
  deleteServer,
  getMCPHealth,
  getOAuthUrl,
} from "@/lib/api/mcp";
import type { CreateMCPServerRequest } from "@/types/mcp";

export const mcpKeys = {
  all: ["mcp"] as const,
  catalog: () => [...mcpKeys.all, "catalog"] as const,
  catalogItem: (id: string) => [...mcpKeys.all, "catalog", id] as const,
  servers: () => [...mcpKeys.all, "servers"] as const,
  server: (id: string) => [...mcpKeys.all, "server", id] as const,
  health: () => [...mcpKeys.all, "health"] as const,
};

export function useCatalog() {
  return useQuery({
    queryKey: mcpKeys.catalog(),
    queryFn: getCatalog,
  });
}

export function useCatalogItem(templateId: string) {
  return useQuery({
    queryKey: mcpKeys.catalogItem(templateId),
    queryFn: () => getCatalogItem(templateId),
    enabled: !!templateId,
  });
}

export function useServers() {
  return useQuery({
    queryKey: mcpKeys.servers(),
    queryFn: listServers,
  });
}

export function useServer(serverId: string) {
  return useQuery({
    queryKey: mcpKeys.server(serverId),
    queryFn: () => getServer(serverId),
    enabled: !!serverId,
  });
}

export function useCreateServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateMCPServerRequest) => createServer(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mcpKeys.servers() });
      toast.success("Server connected successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useDeleteServer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (serverId: string) => deleteServer(serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mcpKeys.servers() });
      toast.success("Server disconnected");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useMCPHealth() {
  return useQuery({
    queryKey: mcpKeys.health(),
    queryFn: getMCPHealth,
    refetchInterval: 30000,
  });
}

export function useOAuthUrl(service: string) {
  return useQuery({
    queryKey: ["oauth", service],
    queryFn: () => getOAuthUrl(service),
    enabled: false,
  });
}
