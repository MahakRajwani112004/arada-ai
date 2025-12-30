/**
 * Schedule types for workflow cron-based scheduling.
 */

/**
 * Schedule details.
 */
export interface Schedule {
  id: string;
  workflow_id: string;
  cron_expression: string;
  cron_description: string;
  timezone: string;
  enabled: boolean;
  input?: string;
  context: Record<string, unknown>;
  next_run_at?: string;
  last_run_at?: string;
  run_count: number;
  last_error?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Request to create a schedule.
 */
export interface CreateScheduleRequest {
  cron_expression: string;
  timezone?: string;
  enabled?: boolean;
  input?: string;
  context?: Record<string, unknown>;
}

/**
 * Request to update a schedule.
 */
export interface UpdateScheduleRequest {
  cron_expression?: string;
  timezone?: string;
  enabled?: boolean;
  input?: string;
  context?: Record<string, unknown>;
}

/**
 * Response from cron validation.
 */
export interface ValidateCronResponse {
  is_valid: boolean;
  error?: string;
  description?: string;
  next_runs: string[];
}

/**
 * Request to validate cron expression.
 */
export interface ValidateCronRequest {
  cron_expression: string;
  timezone?: string;
}

/**
 * Request to preview schedule runs.
 */
export interface SchedulePreviewRequest {
  cron_expression: string;
  timezone?: string;
  count?: number;
}

/**
 * List of schedules.
 */
export interface ScheduleListResponse {
  schedules: Schedule[];
  total: number;
}

/**
 * Common cron presets for easy selection.
 */
export const CRON_PRESETS = [
  { label: "Every minute", value: "* * * * *", description: "Runs every minute" },
  { label: "Every 5 minutes", value: "*/5 * * * *", description: "Runs every 5 minutes" },
  { label: "Every 15 minutes", value: "*/15 * * * *", description: "Runs every 15 minutes" },
  { label: "Every 30 minutes", value: "*/30 * * * *", description: "Runs every 30 minutes" },
  { label: "Every hour", value: "0 * * * *", description: "At the start of every hour" },
  { label: "Every 6 hours", value: "0 */6 * * *", description: "Every 6 hours" },
  { label: "Daily at midnight", value: "0 0 * * *", description: "Every day at 12:00 AM" },
  { label: "Daily at 9 AM", value: "0 9 * * *", description: "Every day at 9:00 AM" },
  { label: "Weekdays at 9 AM", value: "0 9 * * 1-5", description: "Monday to Friday at 9:00 AM" },
  { label: "Weekly on Monday", value: "0 9 * * 1", description: "Every Monday at 9:00 AM" },
  { label: "Monthly", value: "0 0 1 * *", description: "First day of every month at midnight" },
] as const;

/**
 * Common timezones.
 */
export const COMMON_TIMEZONES = [
  { label: "UTC", value: "UTC" },
  { label: "Eastern (US)", value: "America/New_York" },
  { label: "Central (US)", value: "America/Chicago" },
  { label: "Mountain (US)", value: "America/Denver" },
  { label: "Pacific (US)", value: "America/Los_Angeles" },
  { label: "London", value: "Europe/London" },
  { label: "Paris", value: "Europe/Paris" },
  { label: "Tokyo", value: "Asia/Tokyo" },
  { label: "Sydney", value: "Australia/Sydney" },
  { label: "Singapore", value: "Asia/Singapore" },
] as const;
