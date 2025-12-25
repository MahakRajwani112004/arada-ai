"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listApiKeys,
  createApiKey,
  deleteApiKey,
  updateEmail,
  updatePassword,
  updateProfile,
} from "@/lib/api/settings";
import { useAuth } from "@/lib/auth";

export const settingsKeys = {
  all: ["settings"] as const,
  apiKeys: () => [...settingsKeys.all, "api-keys"] as const,
};

// API Keys hooks
export function useApiKeys() {
  return useQuery({
    queryKey: settingsKeys.apiKeys(),
    queryFn: listApiKeys,
  });
}

export function useCreateApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (name: string) => createApiKey(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.apiKeys() });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useDeleteApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (keyId: string) => deleteApiKey(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.apiKeys() });
      toast.success("API key deleted");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Email update hook
export function useUpdateEmail() {
  const { fetchUser } = useAuth();

  return useMutation({
    mutationFn: (newEmail: string) => updateEmail(newEmail),
    onSuccess: async () => {
      // Refresh user data after email update
      await fetchUser();
      toast.success("Email updated successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Password update hook
export function useUpdatePassword() {
  return useMutation({
    mutationFn: ({
      currentPassword,
      newPassword,
    }: {
      currentPassword: string;
      newPassword: string;
    }) => updatePassword(currentPassword, newPassword),
    onSuccess: () => {
      toast.success("Password updated successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Profile update hook
export function useUpdateProfile() {
  const { fetchUser } = useAuth();

  return useMutation({
    mutationFn: (displayName: string | null) => updateProfile(displayName),
    onSuccess: async () => {
      // Refresh user data after profile update
      await fetchUser();
      toast.success("Profile updated successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
