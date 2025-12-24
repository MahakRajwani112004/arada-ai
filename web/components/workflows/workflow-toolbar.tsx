"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Save, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { useWorkflowBuilderStore } from "@/stores/workflow-builder-store";
import {
  useCreateWorkflow,
  useUpdateWorkflow,
  useDeleteWorkflow,
} from "@/lib/hooks/use-workflows";
import { ID_PATTERN } from "@/types/workflow";

interface WorkflowToolbarProps {
  workflowId?: string;
  isEditing?: boolean;
}

export function WorkflowToolbar({ workflowId, isEditing }: WorkflowToolbarProps) {
  const router = useRouter();
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);

  const {
    workflowId: storeId,
    workflowName,
    workflowDescription,
    setWorkflowMetadata,
    toWorkflowDefinition,
    isDirty,
    nodes,
    reset,
  } = useWorkflowBuilderStore();

  const createWorkflow = useCreateWorkflow();
  const updateWorkflow = useUpdateWorkflow();
  const deleteWorkflow = useDeleteWorkflow();

  const [formId, setFormId] = useState(storeId || "");
  const [formName, setFormName] = useState(workflowName || "");
  const [formDescription, setFormDescription] = useState(workflowDescription || "");

  const handleSave = async () => {
    // Validate ID
    if (!formId || !ID_PATTERN.test(formId)) {
      toast.error("Invalid workflow ID. Must start with a letter and contain only alphanumeric characters, hyphens, and underscores.");
      return;
    }

    // Validate nodes
    if (nodes.length === 0) {
      toast.error("Workflow must have at least one step.");
      return;
    }

    // Update store metadata
    setWorkflowMetadata(formId, formName, formDescription);

    // Get workflow definition
    const workflow = toWorkflowDefinition();

    try {
      if (isEditing && workflowId) {
        await updateWorkflow.mutateAsync({ id: workflowId, data: workflow });
        toast.success("Workflow updated successfully");
      } else {
        await createWorkflow.mutateAsync(workflow);
        toast.success("Workflow created successfully");
        router.push("/workflows");
      }
      setSaveDialogOpen(false);
    } catch {
      // Error handled by mutation
    }
  };

  const handleDelete = async () => {
    if (!workflowId) return;

    try {
      await deleteWorkflow.mutateAsync(workflowId);
      toast.success("Workflow deleted");
      router.push("/workflows");
    } catch {
      // Error handled by mutation
    }
  };

  const handleClear = () => {
    reset();
    toast.info("Canvas cleared");
  };

  const isSaving = createWorkflow.isPending || updateWorkflow.isPending;

  return (
    <div className="px-4 py-3 border-b bg-background flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div>
          <h2 className="font-semibold">
            {isEditing ? `Edit: ${workflowName || workflowId}` : "New Workflow"}
          </h2>
          <p className="text-xs text-muted-foreground">
            {nodes.length} {nodes.length === 1 ? "step" : "steps"}
            {isDirty && <span className="text-amber-500 ml-2">Unsaved changes</span>}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {isEditing && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Workflow?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete the
                  workflow definition.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-destructive text-destructive-foreground"
                >
                  {deleteWorkflow.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    "Delete"
                  )}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}

        <Button variant="outline" size="sm" onClick={handleClear}>
          Clear
        </Button>

        <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Save className="h-4 w-4 mr-2" />
              Save
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {isEditing ? "Update Workflow" : "Save Workflow"}
              </DialogTitle>
              <DialogDescription>
                {isEditing
                  ? "Update the workflow definition."
                  : "Enter details for your new workflow."}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="id">Workflow ID</Label>
                <Input
                  id="id"
                  value={formId}
                  onChange={(e) => setFormId(e.target.value)}
                  placeholder="my-workflow"
                  disabled={isEditing}
                  className="font-mono"
                />
                <p className="text-xs text-muted-foreground">
                  Unique identifier. Letters, numbers, hyphens, underscores.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="My Workflow"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  placeholder="What does this workflow do?"
                  rows={3}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setSaveDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                {isEditing ? "Update" : "Create"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
