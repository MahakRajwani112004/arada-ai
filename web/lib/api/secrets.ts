import { apiClient } from "./client";

export interface SecretInfo {
  key: string;
  type: "oauth" | "mcp" | "unknown";
  provider?: string;
  service?: string;
  linked_server_id?: string;
  linked_server_name?: string;
  is_orphaned: boolean;
}

export interface SecretsListResponse {
  secrets: SecretInfo[];
  total: number;
  orphaned_count: number;
}

export interface SecretsStatsResponse {
  total: number;
  oauth_tokens: number;
  mcp_credentials: number;
  orphaned: number;
}

export async function listSecrets(): Promise<SecretsListResponse> {
  const response = await apiClient.get<SecretsListResponse>("/secrets");
  return response.data;
}

export async function getSecretsStats(): Promise<SecretsStatsResponse> {
  const response = await apiClient.get<SecretsStatsResponse>("/secrets/stats");
  return response.data;
}

export async function deleteSecret(secretKey: string): Promise<void> {
  await apiClient.delete(`/secrets/${encodeURIComponent(secretKey)}`);
}
