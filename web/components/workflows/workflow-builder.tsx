"use client";

import { ReactFlowProvider } from "@xyflow/react";
import { WorkflowSidebar } from "./workflow-sidebar";
import { WorkflowCanvas } from "./workflow-canvas";
import { WorkflowConfigPanel } from "./workflow-config-panel";
import { WorkflowToolbar } from "./workflow-toolbar";
import { useWorkflowBuilderStore } from "@/stores/workflow-builder-store";

interface WorkflowBuilderProps {
  workflowId?: string;
  isEditing?: boolean;
}

export function WorkflowBuilder({ workflowId, isEditing }: WorkflowBuilderProps) {
  const { selectedNodeId } = useWorkflowBuilderStore();

  return (
    <ReactFlowProvider>
      <div className="flex flex-col h-[calc(100vh-120px)]">
        <WorkflowToolbar workflowId={workflowId} isEditing={isEditing} />
        <div className="flex flex-1 overflow-hidden">
          <WorkflowSidebar />
          <WorkflowCanvas />
          {selectedNodeId && <WorkflowConfigPanel />}
        </div>
      </div>
    </ReactFlowProvider>
  );
}
