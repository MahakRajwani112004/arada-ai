/**
 * React Query hooks for workflow schedule management.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createSchedule,
  deleteSchedule,
  getSchedule,
  listSchedules,
  previewSchedule,
  updateSchedule,
  validateCron,
} from "../api/schedules";
import type {
  CreateScheduleRequest,
  UpdateScheduleRequest,
  ValidateCronRequest,
  SchedulePreviewRequest,
} from "@/types/schedule";

/**
 * Query key factory for schedules.
 */
export const scheduleKeys = {
  all: ["schedules"] as const,
  lists: () => [...scheduleKeys.all, "list"] as const,
  list: (filters?: { enabled?: boolean }) =>
    [...scheduleKeys.lists(), filters] as const,
  details: () => [...scheduleKeys.all, "detail"] as const,
  detail: (workflowId: string) =>
    [...scheduleKeys.details(), workflowId] as const,
};

/**
 * Hook to list all schedules.
 */
export function useSchedules(params?: {
  enabled?: boolean;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: scheduleKeys.list(params),
    queryFn: () => listSchedules(params),
  });
}

/**
 * Hook to get schedule for a specific workflow.
 */
export function useSchedule(workflowId: string) {
  return useQuery({
    queryKey: scheduleKeys.detail(workflowId),
    queryFn: () => getSchedule(workflowId),
    retry: (failureCount, error) => {
      // Don't retry on 404 (no schedule exists)
      const httpError = error as { response?: { status?: number } };
      if (httpError?.response?.status === 404) {
        return false;
      }
      return failureCount < 3;
    },
  });
}

/**
 * Hook to create a schedule.
 */
export function useCreateSchedule(workflowId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateScheduleRequest) =>
      createSchedule(workflowId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.all });
    },
  });
}

/**
 * Hook to update a schedule.
 */
export function useUpdateSchedule(workflowId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateScheduleRequest) =>
      updateSchedule(workflowId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.all });
    },
  });
}

/**
 * Hook to delete a schedule.
 */
export function useDeleteSchedule(workflowId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => deleteSchedule(workflowId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.all });
    },
  });
}

/**
 * Hook to validate a cron expression.
 */
export function useValidateCron() {
  return useMutation({
    mutationFn: (data: ValidateCronRequest) => validateCron(data),
  });
}

/**
 * Hook to preview schedule runs.
 */
export function usePreviewSchedule() {
  return useMutation({
    mutationFn: (data: SchedulePreviewRequest) => previewSchedule(data),
  });
}

/**
 * Hook to toggle schedule enabled state.
 */
export function useToggleSchedule(workflowId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (enabled: boolean) => updateSchedule(workflowId, { enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scheduleKeys.all });
    },
  });
}
