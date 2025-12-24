"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { listSecrets, getSecretsStats, deleteSecret } from "@/lib/api/secrets";

export const secretsKeys = {
  all: ["secrets"] as const,
  list: () => [...secretsKeys.all, "list"] as const,
  stats: () => [...secretsKeys.all, "stats"] as const,
};

export function useSecrets() {
  return useQuery({
    queryKey: secretsKeys.list(),
    queryFn: listSecrets,
  });
}

export function useSecretsStats() {
  return useQuery({
    queryKey: secretsKeys.stats(),
    queryFn: getSecretsStats,
  });
}

export function useDeleteSecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (secretKey: string) => deleteSecret(secretKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: secretsKeys.all });
      toast.success("Secret deleted successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
