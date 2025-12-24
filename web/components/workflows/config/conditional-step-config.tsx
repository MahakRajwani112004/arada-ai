"use client";

import { Plus, Trash2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { WorkflowNodeData } from "@/types/workflow";
import { useWorkflowBuilderStore } from "@/stores/workflow-builder-store";

interface ConditionalStepConfigProps {
  data: WorkflowNodeData;
  onChange: (data: Partial<WorkflowNodeData>) => void;
}

export function ConditionalStepConfig({ data, onChange }: ConditionalStepConfigProps) {
  const { nodes } = useWorkflowBuilderStore();
  const branches = data.conditionalBranches || {};
  const branchEntries = Object.entries(branches);

  // Get other step IDs for target selection
  const otherStepIds = nodes
    .filter((node) => node.id !== data.label)
    .map((node) => node.id);

  const addBranch = () => {
    const newKey = `condition-${branchEntries.length + 1}`;
    onChange({
      conditionalBranches: {
        ...branches,
        [newKey]: "",
      },
    });
  };

  const updateBranchKey = (oldKey: string, newKey: string) => {
    const newBranches = { ...branches };
    const value = newBranches[oldKey];
    delete newBranches[oldKey];
    newBranches[newKey] = value;
    onChange({ conditionalBranches: newBranches });
  };

  const updateBranchValue = (key: string, value: string) => {
    onChange({
      conditionalBranches: {
        ...branches,
        [key]: value,
      },
    });
  };

  const removeBranch = (key: string) => {
    const newBranches = { ...branches };
    delete newBranches[key];
    onChange({ conditionalBranches: newBranches });
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="conditionSource">Condition Source</Label>
        <Textarea
          id="conditionSource"
          value={data.conditionSource || ""}
          onChange={(e) => onChange({ conditionSource: e.target.value })}
          placeholder="${steps.classify.output}"
          className="font-mono text-sm"
          rows={2}
        />
        <p className="text-xs text-muted-foreground">
          Template that resolves to a value for routing. Use {"${steps.stepId.output}"}.
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Condition Branches ({branchEntries.length})</Label>
          <Button type="button" variant="outline" size="sm" onClick={addBranch}>
            <Plus className="h-4 w-4 mr-1" />
            Add Branch
          </Button>
        </div>

        {branchEntries.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4 border rounded-lg border-dashed">
            No branches. Add conditions to route to different steps.
          </p>
        )}

        <div className="space-y-3">
          {branchEntries.map(([key, value], index) => (
            <div key={index} className="p-3 border rounded-lg space-y-3 bg-muted/30">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Branch {index + 1}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeBranch(key)}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label className="text-xs">When value is</Label>
                  <Input
                    value={key}
                    onChange={(e) => updateBranchKey(key, e.target.value)}
                    placeholder="news"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Go to step</Label>
                  <Input
                    value={value}
                    onChange={(e) => updateBranchValue(key, e.target.value)}
                    placeholder="step-id"
                    list={`steps-${index}`}
                  />
                  <datalist id={`steps-${index}`}>
                    {otherStepIds.map((id) => (
                      <option key={id} value={id} />
                    ))}
                  </datalist>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="defaultStep">Default Step</Label>
        <Input
          id="defaultStep"
          value={data.defaultStep || ""}
          onChange={(e) => onChange({ defaultStep: e.target.value })}
          placeholder="fallback-step-id"
          list="default-steps"
        />
        <datalist id="default-steps">
          {otherStepIds.map((id) => (
            <option key={id} value={id} />
          ))}
        </datalist>
        <p className="text-xs text-muted-foreground">
          Step to execute if no condition matches
        </p>
      </div>
    </div>
  );
}
