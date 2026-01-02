/**
 * API client for workflow schedule operations.
 */

import { apiClient } from "./client";
import type {
  Schedule,
  CreateScheduleRequest,
  UpdateScheduleRequest,
  ValidateCronRequest,
  ValidateCronResponse,
  SchedulePreviewRequest,
  ScheduleListResponse,
} from "@/types/schedule";

/**
 * Create a schedule for a workflow.
 */
export async function createSchedule(
  workflowId: string,
  data: CreateScheduleRequest
): Promise<Schedule> {
  const response = await apiClient.post<Schedule>(
    `/api/v1/workflows/${workflowId}/schedule`,
    data
  );
  return response.data;
}

/**
 * Get the schedule for a workflow.
 */
export async function getSchedule(workflowId: string): Promise<Schedule> {
  const response = await apiClient.get<Schedule>(
    `/api/v1/workflows/${workflowId}/schedule`
  );
  return response.data;
}

/**
 * Update the schedule for a workflow.
 */
export async function updateSchedule(
  workflowId: string,
  data: UpdateScheduleRequest
): Promise<Schedule> {
  const response = await apiClient.put<Schedule>(
    `/api/v1/workflows/${workflowId}/schedule`,
    data
  );
  return response.data;
}

/**
 * Delete the schedule for a workflow.
 */
export async function deleteSchedule(workflowId: string): Promise<void> {
  await apiClient.delete(`/api/v1/workflows/${workflowId}/schedule`);
}

/**
 * List all schedules for the current user.
 */
export async function listSchedules(params?: {
  enabled?: boolean;
  limit?: number;
  offset?: number;
}): Promise<ScheduleListResponse> {
  const response = await apiClient.get<ScheduleListResponse>(
    "/api/v1/workflows/schedules",
    { params }
  );
  return response.data;
}

/**
 * Validate a cron expression.
 */
export async function validateCron(
  data: ValidateCronRequest
): Promise<ValidateCronResponse> {
  const response = await apiClient.post<ValidateCronResponse>(
    "/api/v1/workflows/schedule/validate",
    data
  );
  return response.data;
}

/**
 * Preview schedule run times.
 */
export async function previewSchedule(
  data: SchedulePreviewRequest
): Promise<ValidateCronResponse> {
  const response = await apiClient.post<ValidateCronResponse>(
    "/api/v1/workflows/schedule/preview",
    data
  );
  return response.data;
}
