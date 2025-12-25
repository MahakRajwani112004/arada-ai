"use client";

import { ArrowLeft, Save, Play, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface CanvasToolbarProps {
  workflowName: string;
  hasUnsavedChanges: boolean;
  isSaving: boolean;
  canRun: boolean;
  isExecutionPanelOpen: boolean;
  onBack: () => void;
  onSave: () => void;
  onToggleExecution: () => void;
}

export function CanvasToolbar({
  workflowName,
  hasUnsavedChanges,
  isSaving,
  canRun,
  isExecutionPanelOpen,
  onBack,
  onSave,
  onToggleExecution,
}: CanvasToolbarProps) {
  return (
    <div className="h-14 border-b border-border bg-card flex items-center justify-between px-4 shrink-0">
      {/* Left side */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onBack}
          title="Back to workflow"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-2">
          <h1 className="font-semibold text-lg">{workflowName}</h1>
          {hasUnsavedChanges && (
            <Badge variant="secondary" className="text-xs">
              Unsaved
            </Badge>
          )}
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onSave}
          disabled={isSaving || !hasUnsavedChanges}
        >
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save
            </>
          )}
        </Button>
        <Button
          size="sm"
          onClick={onToggleExecution}
          variant={isExecutionPanelOpen ? "secondary" : "default"}
          title={canRun ? "Run workflow" : "Create all agents before running"}
        >
          {isExecutionPanelOpen ? (
            <>
              <X className="h-4 w-4 mr-2" />
              Close
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              Run
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
