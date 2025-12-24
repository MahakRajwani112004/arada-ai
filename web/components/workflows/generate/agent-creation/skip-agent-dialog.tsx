"use client";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface SkipAgentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId: string;
  stepId: string;
  onConfirm: () => void;
}

export function SkipAgentDialog({
  open,
  onOpenChange,
  agentId,
  stepId,
  onConfirm,
}: SkipAgentDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Skip agent creation?</AlertDialogTitle>
          <AlertDialogDescription className="space-y-2">
            <p>
              If you skip creating <code className="rounded bg-secondary px-1.5 py-0.5 text-xs">{agentId}</code>,
              the workflow step &quot;{stepId}&quot; will be blocked and the workflow won&apos;t be able to run until you create this agent later.
            </p>
            <p>
              You can always create the agent later from the workflow detail page.
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-amber-500 hover:bg-amber-600"
          >
            Skip Anyway
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
