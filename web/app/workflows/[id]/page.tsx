"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Header } from "@/components/layout/header";
import { WorkflowBuilder } from "@/components/workflows/workflow-builder";
import { useWorkflow } from "@/lib/hooks/use-workflows";
import { useWorkflowBuilderStore } from "@/stores/workflow-builder-store";

export default function EditWorkflowPage() {
  const params = useParams();
  const workflowId = params.id as string;

  const { data: workflow, isLoading, error } = useWorkflow(workflowId);
  const { fromWorkflowDefinition } = useWorkflowBuilderStore();

  // Load workflow into builder when data arrives
  useEffect(() => {
    if (workflow) {
      fromWorkflowDefinition(workflow);
    }
  }, [workflow, fromWorkflowDefinition]);

  if (isLoading) {
    return (
      <>
        <Header title="Loading..." backHref="/workflows" />
        <div className="flex items-center justify-center h-[calc(100vh-120px)]">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Header title="Error" backHref="/workflows" />
        <div className="flex items-center justify-center h-[calc(100vh-120px)]">
          <div className="text-center">
            <p className="text-destructive mb-2">Failed to load workflow</p>
            <p className="text-sm text-muted-foreground">{error.message}</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title={workflow?.name || workflowId}
        backHref="/workflows"
      />
      <WorkflowBuilder workflowId={workflowId} isEditing />
    </>
  );
}
