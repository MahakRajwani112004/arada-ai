import { apiClient } from "./client";
import type {
  MCPCatalogItem,
  MCPCatalogResponse,
  MCPServer,
  MCPServerDetail,
  MCPServerListResponse,
  CreateMCPServerRequest,
  MCPHealthResponse,
  OAuthAuthorizeResponse,
} from "@/types/mcp";

export async function getCatalog(): Promise<MCPCatalogResponse> {
  const response = await apiClient.get<MCPCatalogResponse>("/mcp/catalog");
  return response.data;
}

export async function getCatalogItem(templateId: string): Promise<MCPCatalogItem> {
  const response = await apiClient.get<MCPCatalogItem>(`/mcp/catalog/${templateId}`);
  return response.data;
}

export async function listServers(): Promise<MCPServerListResponse> {
  const response = await apiClient.get<MCPServerListResponse>("/mcp/servers");
  return response.data;
}

export async function getServer(serverId: string): Promise<MCPServerDetail> {
  const response = await apiClient.get<MCPServerDetail>(`/mcp/servers/${serverId}`);
  return response.data;
}

export async function createServer(request: CreateMCPServerRequest): Promise<MCPServer> {
  const response = await apiClient.post<MCPServer>("/mcp/servers", request);
  return response.data;
}

export async function deleteServer(serverId: string): Promise<void> {
  await apiClient.delete(`/mcp/servers/${serverId}`);
}

export async function getMCPHealth(): Promise<MCPHealthResponse> {
  const response = await apiClient.get<MCPHealthResponse>("/mcp/health");
  return response.data;
}

export async function getOAuthUrl(service: string): Promise<OAuthAuthorizeResponse> {
  const response = await apiClient.get<OAuthAuthorizeResponse>(
    `/oauth/google/authorize-url?service=${service}`
  );
  return response.data;
}
