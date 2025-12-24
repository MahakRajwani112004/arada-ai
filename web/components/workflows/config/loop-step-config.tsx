"use client";

import { Plus, Trash2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { WorkflowNodeData, LoopInnerStep } from "@/types/workflow";
import { useAgents } from "@/lib/hooks/use-agents";

interface LoopStepConfigProps {
  data: WorkflowNodeData;
  onChange: (data: Partial<WorkflowNodeData>) => void;
}

export function LoopStepConfig({ data, onChange }: LoopStepConfigProps) {
  const { data: agentsData, isLoading } = useAgents();
  const agents = agentsData?.agents || [];
  const loopSteps = data.loopSteps || [];

  const addStep = () => {
    const newStep: LoopInnerStep = {
      id: `inner-${loopSteps.length + 1}`,
      agent_id: "",
      input: "${user_input}",
      timeout: 120,
    };
    onChange({ loopSteps: [...loopSteps, newStep] });
  };

  const updateStep = (index: number, updates: Partial<LoopInnerStep>) => {
    const updated = [...loopSteps];
    updated[index] = { ...updated[index], ...updates };
    onChange({ loopSteps: updated });
  };

  const removeStep = (index: number) => {
    onChange({ loopSteps: loopSteps.filter((_, i) => i !== index) });
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="maxIterations">Max Iterations</Label>
          <Input
            id="maxIterations"
            type="number"
            min={1}
            max={20}
            value={data.maxIterations || 5}
            onChange={(e) =>
              onChange({ maxIterations: parseInt(e.target.value) || 5 })
            }
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="exitCondition">Exit Condition</Label>
        <Textarea
          id="exitCondition"
          value={data.exitCondition || ""}
          onChange={(e) => onChange({ exitCondition: e.target.value })}
          placeholder="${steps.validator.output} == 'approved'"
          className="font-mono text-sm"
          rows={2}
        />
        <p className="text-xs text-muted-foreground">
          Expression to evaluate. Loop exits when true. Use comparisons like == != {">"} {"<"}.
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Inner Steps ({loopSteps.length})</Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addStep}
            disabled={loopSteps.length >= 10}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Step
          </Button>
        </div>

        {loopSteps.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4 border rounded-lg border-dashed">
            No inner steps. Add steps to execute in each iteration.
          </p>
        )}

        <div className="space-y-3">
          {loopSteps.map((step, index) => (
            <div key={index} className="p-3 border rounded-lg space-y-3 bg-muted/30">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Step {index + 1}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeStep(index)}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Step ID</Label>
                <Input
                  value={step.id}
                  onChange={(e) => updateStep(index, { id: e.target.value })}
                  placeholder="inner-step-1"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Agent</Label>
                <Select
                  value={step.agent_id}
                  onValueChange={(value) => updateStep(index, { agent_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={isLoading ? "Loading..." : "Select agent"} />
                  </SelectTrigger>
                  <SelectContent>
                    {agents.map((agent) => (
                      <SelectItem key={agent.id} value={agent.id}>
                        {agent.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Input</Label>
                <Input
                  value={step.input}
                  onChange={(e) => updateStep(index, { input: e.target.value })}
                  placeholder="${user_input}"
                  className="font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground">
                  Use {"${loop_iteration}"} for current iteration number
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
