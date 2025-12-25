"use client";

import { useState } from "react";
import { ArrowLeft, ArrowRight, Plus, AlertCircle, CheckCircle, Edit2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { TriggerSelector } from "./trigger-selector";
import { SkeletonStepCard } from "./skeleton-step-card";
import type { WorkflowSkeleton, SkeletonStepWithSuggestion, MCPDependency, TriggerType, WorkflowTrigger } from "@/types/workflow";

interface SkeletonEditorProps {
  skeleton: WorkflowSkeleton;
  stepSuggestions: SkeletonStepWithSuggestion[];
  mcpDependencies: MCPDependency[];
  explanation: string;
  warnings: string[];
  onConfirm: (skeleton: WorkflowSkeleton, suggestions: SkeletonStepWithSuggestion[]) => void;
  onBack: () => void;
  onEditPrompt: () => void;
  isSaving?: boolean;
}

export function SkeletonEditor({
  skeleton: initialSkeleton,
  stepSuggestions: initialSuggestions,
  mcpDependencies,
  explanation,
  warnings,
  onConfirm,
  onBack: _onBack,
  onEditPrompt,
  isSaving = false,
}: SkeletonEditorProps) {
  void _onBack; // Suppress unused variable warning - kept for API compatibility
  const [skeleton, setSkeleton] = useState<WorkflowSkeleton>(initialSkeleton);
  const [suggestions, setSuggestions] = useState<SkeletonStepWithSuggestion[]>(initialSuggestions);
  const [editingName, setEditingName] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  const handleTriggerChange = (type: TriggerType) => {
    const newTrigger: WorkflowTrigger = {
      type,
      webhook_config: type === "webhook" ? {
        token: crypto.randomUUID().slice(0, 22),
        rate_limit: 60,
        max_payload_kb: 100,
        expected_fields: [],
      } : undefined,
    };
    setSkeleton({ ...skeleton, trigger: newTrigger });
  };

  const handleStepUpdate = (index: number, name: string, role: string) => {
    const newSteps = [...skeleton.steps];
    newSteps[index] = { ...newSteps[index], name, role };
    setSkeleton({ ...skeleton, steps: newSteps });

    const newSuggestions = [...suggestions];
    newSuggestions[index] = { ...newSuggestions[index], name, role };
    setSuggestions(newSuggestions);
  };

  const handleStepRemove = (index: number) => {
    const newSteps = skeleton.steps.filter((_, i) => i !== index);
    // Reorder steps
    const reorderedSteps = newSteps.map((step, i) => ({ ...step, order: i }));
    setSkeleton({ ...skeleton, steps: reorderedSteps });

    const newSuggestions = suggestions.filter((_, i) => i !== index);
    const reorderedSuggestions = newSuggestions.map((s, i) => ({ ...s, order: i }));
    setSuggestions(reorderedSuggestions);
  };

  const handleAddStep = () => {
    const newOrder = skeleton.steps.length;
    const newStep = {
      id: `step-${newOrder}`,
      name: "New Step",
      role: "Define what this step should do",
      order: newOrder,
    };
    setSkeleton({ ...skeleton, steps: [...skeleton.steps, newStep] });
    setSuggestions([...suggestions, { ...newStep, suggestion: undefined }]);
  };

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;

    // Reorder steps
    const newSteps = [...skeleton.steps];
    const [removed] = newSteps.splice(draggedIndex, 1);
    newSteps.splice(index, 0, removed);

    const reorderedSteps = newSteps.map((step, i) => ({ ...step, order: i }));
    setSkeleton({ ...skeleton, steps: reorderedSteps });

    const newSuggestions = [...suggestions];
    const [removedSug] = newSuggestions.splice(draggedIndex, 1);
    newSuggestions.splice(index, 0, removedSug);

    const reorderedSuggestions = newSuggestions.map((s, i) => ({ ...s, order: i }));
    setSuggestions(reorderedSuggestions);

    setDraggedIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  const disconnectedMcps = mcpDependencies.filter(m => !m.connected);
  const connectedMcps = mcpDependencies.filter(m => m.connected);

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1 flex-1">
              {editingName ? (
                <Input
                  value={skeleton.name}
                  onChange={(e) => setSkeleton({ ...skeleton, name: e.target.value })}
                  onBlur={() => setEditingName(false)}
                  onKeyDown={(e) => e.key === "Enter" && setEditingName(false)}
                  autoFocus
                  className="text-xl font-semibold"
                />
              ) : (
                <CardTitle
                  className="flex items-center gap-2 cursor-pointer hover:text-primary"
                  onClick={() => setEditingName(true)}
                >
                  {skeleton.name}
                  <Edit2 className="h-4 w-4 text-muted-foreground" />
                </CardTitle>
              )}
              <CardDescription>{explanation}</CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Warnings */}
      {warnings.length > 0 && (
        <Alert variant="default" className="border-yellow-500/50 bg-yellow-500/10">
          <AlertCircle className="h-4 w-4 text-yellow-500" />
          <AlertDescription>
            <ul className="list-disc list-inside space-y-1">
              {warnings.map((warning, i) => (
                <li key={i}>{warning}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* MCP Dependencies */}
      {mcpDependencies.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Required Integrations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex flex-wrap gap-2">
              {connectedMcps.map((mcp) => (
                <Badge key={mcp.template} variant="secondary" className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  {mcp.name}
                </Badge>
              ))}
              {disconnectedMcps.map((mcp) => (
                <Badge key={mcp.template} variant="outline" className="flex items-center gap-1 border-yellow-500/50">
                  <AlertCircle className="h-3 w-3 text-yellow-500" />
                  {mcp.name} (not connected)
                </Badge>
              ))}
            </div>
            {disconnectedMcps.length > 0 && (
              <p className="text-xs text-muted-foreground">
                You can still create the workflow. Connect these integrations before running.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Trigger Selector */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Trigger</CardTitle>
          <CardDescription className="text-xs">How this workflow will be started</CardDescription>
        </CardHeader>
        <CardContent>
          <TriggerSelector
            value={skeleton.trigger.type}
            onChange={handleTriggerChange}
          />
        </CardContent>
      </Card>

      {/* Steps */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-sm font-medium">Steps</CardTitle>
              <CardDescription className="text-xs">
                Drag to reorder. Edit names and roles before configuring agents.
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={handleAddStep}>
              <Plus className="h-4 w-4 mr-1" />
              Add Step
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {skeleton.steps.map((step, index) => (
            <div
              key={step.id}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnd={handleDragEnd}
              className={`${draggedIndex === index ? "opacity-50" : ""}`}
            >
              <SkeletonStepCard
                step={step}
                suggestion={suggestions[index]?.suggestion}
                stepNumber={index + 1}
                totalSteps={skeleton.steps.length}
                onUpdate={(name, role) => handleStepUpdate(index, name, role)}
                onRemove={() => handleStepRemove(index)}
                canRemove={skeleton.steps.length > 1}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={onEditPrompt} disabled={isSaving}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Edit Prompt
        </Button>
        <Button onClick={() => onConfirm(skeleton, suggestions)} disabled={isSaving}>
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Creating Workflow...
            </>
          ) : (
            <>
              Continue to Canvas
              <ArrowRight className="h-4 w-4 ml-2" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
