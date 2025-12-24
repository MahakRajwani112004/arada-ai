"use client";

import Link from "next/link";
import { MoreVertical, Pencil, Trash2, Workflow } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { Badge } from "@/components/ui/badge";
import { WorkflowDefinitionResponse } from "@/types/workflow";
import { useDeleteWorkflow } from "@/lib/hooks/use-workflows";
import { toast } from "sonner";

interface WorkflowCardProps {
  workflow: WorkflowDefinitionResponse;
}

export function WorkflowCard({ workflow }: WorkflowCardProps) {
  const deleteWorkflow = useDeleteWorkflow();

  const handleDelete = async () => {
    try {
      await deleteWorkflow.mutateAsync(workflow.id);
      toast.success("Workflow deleted");
    } catch {
      // Error handled by mutation
    }
  };

  const stepCount = workflow.steps?.length || 0;

  return (
    <Card className="hover:border-primary/40 hover:shadow-md transition-all">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-primary/10">
              <Workflow className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-base">
                {workflow.name || workflow.id}
              </CardTitle>
              <Badge variant="outline" className="font-mono text-xs mt-1">
                {workflow.id}
              </Badge>
            </div>
          </div>

          <AlertDialog>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem asChild>
                  <Link href={`/workflows/${workflow.id}`}>
                    <Pencil className="h-4 w-4 mr-2" />
                    Edit
                  </Link>
                </DropdownMenuItem>
                <AlertDialogTrigger asChild>
                  <DropdownMenuItem className="text-destructive">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </AlertDialogTrigger>
              </DropdownMenuContent>
            </DropdownMenu>

            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Workflow?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete &quot;{workflow.name || workflow.id}&quot;.
                  This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-destructive text-destructive-foreground"
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </CardHeader>

      <CardContent>
        {workflow.description && (
          <CardDescription className="mb-3 line-clamp-2">
            {workflow.description}
          </CardDescription>
        )}

        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>
            {stepCount} {stepCount === 1 ? "step" : "steps"}
          </span>
          {workflow.updated_at && (
            <span>
              Updated {new Date(workflow.updated_at).toLocaleDateString()}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function WorkflowCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-md bg-muted animate-pulse w-9 h-9" />
          <div className="flex-1">
            <div className="h-5 bg-muted animate-pulse rounded w-32 mb-2" />
            <div className="h-4 bg-muted animate-pulse rounded w-24" />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-4 bg-muted animate-pulse rounded w-full mb-3" />
        <div className="h-4 bg-muted animate-pulse rounded w-20" />
      </CardContent>
    </Card>
  );
}
