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
