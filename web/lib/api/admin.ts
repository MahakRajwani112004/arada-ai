import { apiClient } from "./client";

export interface AdminUser {
  id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  org_id: string;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  limit: number;
}

export interface UserUpdateData {
  email?: string;
  display_name?: string;
}

export interface UserStatusData {
  is_active: boolean;
}

export interface PasswordResetData {
  new_password: string;
}

// List all users (paginated)
export async function listUsers(
  page: number = 1,
  limit: number = 50
): Promise<UserListResponse> {
  const response = await apiClient.get<UserListResponse>("/admin/users", {
    params: { page, limit },
  });
  return response.data;
}

// Get a specific user
export async function getUser(userId: string): Promise<AdminUser> {
  const response = await apiClient.get<AdminUser>(`/admin/users/${userId}`);
  return response.data;
}

// Update a user's profile
export async function updateUser(
  userId: string,
  data: UserUpdateData
): Promise<AdminUser> {
  const response = await apiClient.put<AdminUser>(`/admin/users/${userId}`, data);
  return response.data;
}

// Reset a user's password
export async function resetUserPassword(
  userId: string,
  newPassword: string
): Promise<{ message: string }> {
  const response = await apiClient.put<{ message: string }>(
    `/admin/users/${userId}/password`,
    { new_password: newPassword }
  );
  return response.data;
}

// Toggle user active status
export async function toggleUserStatus(
  userId: string,
  isActive: boolean
): Promise<AdminUser> {
  const response = await apiClient.put<AdminUser>(
    `/admin/users/${userId}/status`,
    { is_active: isActive }
  );
  return response.data;
}
