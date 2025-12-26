import { apiClient } from "./client";

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

export interface ApiKeyCreated {
  id: string;
  name: string;
  key: string;
  key_prefix: string;
  created_at: string;
}

export interface ApiKeyListResponse {
  api_keys: ApiKey[];
  total: number;
}

export interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  is_superuser: boolean;
  org_id: string;
}

// Email update
export async function updateEmail(newEmail: string): Promise<UserProfile> {
  const response = await apiClient.put<UserProfile>("/auth/me/email", {
    new_email: newEmail,
  });
  return response.data;
}

// Password update
export async function updatePassword(
  currentPassword: string,
  newPassword: string
): Promise<{ message: string }> {
  const response = await apiClient.put<{ message: string }>("/auth/me/password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return response.data;
}

// Profile update (display name)
export async function updateProfile(displayName: string | null): Promise<UserProfile> {
  const response = await apiClient.put<UserProfile>("/auth/me/profile", {
    display_name: displayName,
  });
  return response.data;
}

// API Keys
export async function listApiKeys(): Promise<ApiKeyListResponse> {
  const response = await apiClient.get<ApiKeyListResponse>("/auth/api-keys");
  return response.data;
}

export async function createApiKey(name: string): Promise<ApiKeyCreated> {
  const response = await apiClient.post<ApiKeyCreated>("/auth/api-keys", {
    name,
  });
  return response.data;
}

export async function deleteApiKey(keyId: string): Promise<void> {
  await apiClient.delete(`/auth/api-keys/${keyId}`);
}

// LLM Credentials
export interface LLMCredential {
  id: string;
  provider: string;
  display_name: string;
  api_key_preview: string;
  api_base: string | null;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LLMCredentialListResponse {
  credentials: LLMCredential[];
  total: number;
}

export interface LLMCredentialCreate {
  provider: string;
  display_name: string;
  api_key: string;
  api_base?: string | null;
}

export interface LLMCredentialUpdate {
  display_name?: string;
  api_key?: string;
  api_base?: string | null;
  is_active?: boolean;
}

export async function listLLMCredentials(): Promise<LLMCredentialListResponse> {
  const response = await apiClient.get<LLMCredentialListResponse>("/auth/llm-credentials");
  return response.data;
}

export async function createLLMCredential(data: LLMCredentialCreate): Promise<LLMCredential> {
  const response = await apiClient.post<LLMCredential>("/auth/llm-credentials", data);
  return response.data;
}

export async function updateLLMCredential(
  credentialId: string,
  data: LLMCredentialUpdate
): Promise<LLMCredential> {
  const response = await apiClient.put<LLMCredential>(
    `/auth/llm-credentials/${credentialId}`,
    data
  );
  return response.data;
}

export async function deleteLLMCredential(credentialId: string): Promise<void> {
  await apiClient.delete(`/auth/llm-credentials/${credentialId}`);
}
