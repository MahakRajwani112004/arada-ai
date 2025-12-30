"use client";

import { useState, useEffect } from "react";
import { Calendar, Clock, Loader2, AlertCircle, Check } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  useSchedule,
  useCreateSchedule,
  useUpdateSchedule,
  useDeleteSchedule,
  useValidateCron,
} from "@/lib/hooks/use-schedules";
import { CRON_PRESETS, COMMON_TIMEZONES } from "@/types/schedule";
import { toast } from "sonner";
import { format } from "date-fns";

interface ScheduleDialogProps {
  workflowId: string;
  workflowName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ScheduleDialog({
  workflowId,
  workflowName,
  open,
  onOpenChange,
}: ScheduleDialogProps) {
  const [cronExpression, setCronExpression] = useState("0 9 * * 1-5");
  const [timezone, setTimezone] = useState("UTC");
  const [enabled, setEnabled] = useState(true);
  const [inputText, setInputText] = useState("");
  const [useCustomCron, setUseCustomCron] = useState(false);
  const [cronValid, setCronValid] = useState<boolean | null>(null);
  const [cronDescription, setCronDescription] = useState("");
  const [nextRuns, setNextRuns] = useState<string[]>([]);

  const { data: existingSchedule, isLoading: isLoadingSchedule } =
    useSchedule(workflowId);
  const createSchedule = useCreateSchedule(workflowId);
  const updateSchedule = useUpdateSchedule(workflowId);
  const deleteSchedule = useDeleteSchedule(workflowId);
  const validateCron = useValidateCron();

  const hasSchedule = !!existingSchedule;

  // Load existing schedule data
  useEffect(() => {
    if (existingSchedule) {
      setCronExpression(existingSchedule.cron_expression);
      setTimezone(existingSchedule.timezone);
      setEnabled(existingSchedule.enabled);
      setInputText(existingSchedule.input || "");
      setCronDescription(existingSchedule.cron_description);

      // Check if it's a preset
      const isPreset = CRON_PRESETS.some(
        (p) => p.value === existingSchedule.cron_expression
      );
      setUseCustomCron(!isPreset);
    }
  }, [existingSchedule]);

  // Validate cron expression when it changes
  useEffect(() => {
    if (!cronExpression) {
      setCronValid(null);
      setCronDescription("");
      setNextRuns([]);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const result = await validateCron.mutateAsync({
          cron_expression: cronExpression,
          timezone,
        });
        setCronValid(result.is_valid);
        setCronDescription(result.description || "");
        setNextRuns(result.next_runs);
      } catch {
        setCronValid(false);
        setCronDescription("");
        setNextRuns([]);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [cronExpression, timezone]);

  const handleSave = async () => {
    if (!cronValid) {
      toast.error("Please enter a valid cron expression");
      return;
    }

    try {
      if (hasSchedule) {
        await updateSchedule.mutateAsync({
          cron_expression: cronExpression,
          timezone,
          enabled,
          input: inputText || undefined,
        });
        toast.success("Schedule updated successfully");
      } else {
        await createSchedule.mutateAsync({
          cron_expression: cronExpression,
          timezone,
          enabled,
          input: inputText || undefined,
        });
        toast.success("Schedule created successfully");
      }
      onOpenChange(false);
    } catch (error: any) {
      toast.error(error?.message || "Failed to save schedule");
    }
  };

  const handleDelete = async () => {
    try {
      await deleteSchedule.mutateAsync();
      toast.success("Schedule deleted");
      onOpenChange(false);
    } catch (error: any) {
      toast.error(error?.message || "Failed to delete schedule");
    }
  };

  const handlePresetSelect = (value: string) => {
    setCronExpression(value);
    setUseCustomCron(false);
  };

  const isSaving = createSchedule.isPending || updateSchedule.isPending;
  const isDeleting = deleteSchedule.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            {hasSchedule ? "Edit Schedule" : "Create Schedule"}
          </DialogTitle>
          <DialogDescription>
            Configure automated execution for &ldquo;{workflowName}&rdquo;
          </DialogDescription>
        </DialogHeader>

        {isLoadingSchedule ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-6 py-4">
            {/* Enable/Disable Toggle */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Schedule Enabled</Label>
                <p className="text-sm text-muted-foreground">
                  When disabled, scheduled runs will be paused
                </p>
              </div>
              <Switch checked={enabled} onCheckedChange={setEnabled} />
            </div>

            <Separator />

            {/* Cron Expression */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Schedule Timing</Label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setUseCustomCron(!useCustomCron)}
                >
                  {useCustomCron ? "Use Preset" : "Custom"}
                </Button>
              </div>

              {useCustomCron ? (
                <div className="space-y-2">
                  <Input
                    placeholder="* * * * * (min hour day month dow)"
                    value={cronExpression}
                    onChange={(e) => setCronExpression(e.target.value)}
                    className={
                      cronValid === false
                        ? "border-destructive"
                        : cronValid === true
                        ? "border-green-500"
                        : ""
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    Standard 5-field cron: minute (0-59) hour (0-23) day (1-31)
                    month (1-12) day-of-week (0-6, Sun=0)
                  </p>
                </div>
              ) : (
                <Select value={cronExpression} onValueChange={handlePresetSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a schedule" />
                  </SelectTrigger>
                  <SelectContent>
                    {CRON_PRESETS.map((preset) => (
                      <SelectItem key={preset.value} value={preset.value}>
                        <div className="flex flex-col">
                          <span>{preset.label}</span>
                          <span className="text-xs text-muted-foreground">
                            {preset.description}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {/* Validation Status */}
              {cronExpression && (
                <div className="flex items-start gap-2">
                  {cronValid === true && (
                    <>
                      <Check className="h-4 w-4 mt-0.5 text-green-500" />
                      <div className="space-y-1">
                        <p className="text-sm text-green-600">{cronDescription}</p>
                      </div>
                    </>
                  )}
                  {cronValid === false && (
                    <>
                      <AlertCircle className="h-4 w-4 mt-0.5 text-destructive" />
                      <p className="text-sm text-destructive">
                        Invalid cron expression
                      </p>
                    </>
                  )}
                  {cronValid === null && validateCron.isPending && (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  )}
                </div>
              )}
            </div>

            {/* Timezone */}
            <div className="space-y-2">
              <Label>Timezone</Label>
              <Select value={timezone} onValueChange={setTimezone}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {COMMON_TIMEZONES.map((tz) => (
                    <SelectItem key={tz.value} value={tz.value}>
                      {tz.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Next Runs Preview */}
            {nextRuns.length > 0 && (
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Upcoming Runs
                </Label>
                <div className="flex flex-wrap gap-2">
                  {nextRuns.slice(0, 5).map((run, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">
                      {format(new Date(run), "MMM d, h:mm a")}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <Separator />

            {/* Input Text */}
            <div className="space-y-2">
              <Label>Scheduled Input (Optional)</Label>
              <Textarea
                placeholder="Enter the input text to use for each scheduled run..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                rows={3}
              />
              <p className="text-xs text-muted-foreground">
                This text will be passed as user input for each scheduled
                execution.
              </p>
            </div>

            {/* Existing Schedule Info */}
            {hasSchedule && existingSchedule && (
              <Alert>
                <AlertDescription className="text-sm">
                  <div className="flex flex-wrap gap-x-4 gap-y-1">
                    <span>
                      Runs: <strong>{existingSchedule.run_count}</strong>
                    </span>
                    {existingSchedule.last_run_at && (
                      <span>
                        Last run:{" "}
                        <strong>
                          {format(
                            new Date(existingSchedule.last_run_at),
                            "MMM d, h:mm a"
                          )}
                        </strong>
                      </span>
                    )}
                    {existingSchedule.last_error && (
                      <span className="text-destructive">
                        Error: {existingSchedule.last_error}
                      </span>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          {hasSchedule && (
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={isDeleting || isSaving}
              className="mr-auto"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete Schedule"
              )}
            </Button>
          )}
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving || !cronValid}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : hasSchedule ? (
              "Update Schedule"
            ) : (
              "Create Schedule"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
