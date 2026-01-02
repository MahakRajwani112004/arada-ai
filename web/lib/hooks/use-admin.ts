"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listUsers,
  getUser,
  updateUser,
  resetUserPassword,
  toggleUserStatus,
  type UserUpdateData,
} from "@/lib/api/admin";

export const adminKeys = {
  all: ["admin"] as const,
  users: () => [...adminKeys.all, "users"] as const,
  usersList: (page: number, limit: number) =>
    [...adminKeys.users(), "list", { page, limit }] as const,
  user: (id: string) => [...adminKeys.users(), "detail", id] as const,
};

// List users with pagination
export function useUsers(page: number = 1, limit: number = 50) {
  return useQuery({
    queryKey: adminKeys.usersList(page, limit),
    queryFn: () => listUsers(page, limit),
  });
}

// Get single user
export function useUser(userId: string) {
  return useQuery({
    queryKey: adminKeys.user(userId),
    queryFn: () => getUser(userId),
    enabled: !!userId,
  });
}

// Update user profile
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: UserUpdateData }) =>
      updateUser(userId, data),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      queryClient.invalidateQueries({ queryKey: adminKeys.user(userId) });
      toast.success("User updated successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Reset user password
export function useResetPassword() {
  return useMutation({
    mutationFn: ({
      userId,
      newPassword,
    }: {
      userId: string;
      newPassword: string;
    }) => resetUserPassword(userId, newPassword),
    onSuccess: () => {
      toast.success("Password reset successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Toggle user active status
export function useToggleUserStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) =>
      toggleUserStatus(userId, isActive),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: adminKeys.users() });
      const action = user.is_active ? "activated" : "deactivated";
      toast.success(`User ${action} successfully`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
