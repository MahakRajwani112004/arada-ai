"use client";

import { useEffect } from "react";
import { Header } from "@/components/layout/header";
import { WorkflowBuilder } from "@/components/workflows/workflow-builder";
import { useWorkflowBuilderStore } from "@/stores/workflow-builder-store";

export default function NewWorkflowPage() {
  const { reset } = useWorkflowBuilderStore();

  // Reset the builder state when mounting
  useEffect(() => {
    reset();
  }, [reset]);

  return (
    <>
      <Header title="Create Workflow" backHref="/workflows" />
      <WorkflowBuilder />
    </>
  );
}
