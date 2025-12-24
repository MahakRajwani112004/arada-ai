"use client";

import { Plus, Trash2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { WorkflowNodeData, ParallelBranch, AggregationType } from "@/types/workflow";
import { useAgents } from "@/lib/hooks/use-agents";

interface ParallelStepConfigProps {
  data: WorkflowNodeData;
  onChange: (data: Partial<WorkflowNodeData>) => void;
}

export function ParallelStepConfig({ data, onChange }: ParallelStepConfigProps) {
  const { data: agentsData, isLoading } = useAgents();
  const agents = agentsData?.agents || [];
  const branches = data.branches || [];

  const addBranch = () => {
    const newBranch: ParallelBranch = {
      id: `branch-${branches.length + 1}`,
      agent_id: "",
      input: "${user_input}",
      timeout: 120,
    };
    onChange({ branches: [...branches, newBranch] });
  };

  const updateBranch = (index: number, updates: Partial<ParallelBranch>) => {
    const updated = [...branches];
    updated[index] = { ...updated[index], ...updates };
    onChange({ branches: updated });
  };

  const removeBranch = (index: number) => {
    onChange({ branches: branches.filter((_, i) => i !== index) });
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Aggregation Strategy</Label>
        <Select
          value={data.aggregation || "all"}
          onValueChange={(value) => onChange({ aggregation: value as AggregationType })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All - Combine all outputs</SelectItem>
            <SelectItem value="first">First - Return first success</SelectItem>
            <SelectItem value="merge">Merge - Merge into dictionary</SelectItem>
            <SelectItem value="best">Best - Return best result</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Branches ({branches.length})</Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addBranch}
            disabled={branches.length >= 10}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Branch
          </Button>
        </div>

        {branches.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4 border rounded-lg border-dashed">
            No branches added. Click &quot;Add Branch&quot; to add parallel agents.
          </p>
        )}

        <div className="space-y-3">
          {branches.map((branch, index) => (
            <div key={index} className="p-3 border rounded-lg space-y-3 bg-muted/30">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Branch {index + 1}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeBranch(index)}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Agent</Label>
                <Select
                  value={branch.agent_id}
                  onValueChange={(value) => updateBranch(index, { agent_id: value })}
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
                  value={branch.input}
                  onChange={(e) => updateBranch(index, { input: e.target.value })}
                  placeholder="${user_input}"
                  className="font-mono text-sm"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Timeout (s)</Label>
                <Input
                  type="number"
                  min={1}
                  max={600}
                  value={branch.timeout}
                  onChange={(e) =>
                    updateBranch(index, { timeout: parseInt(e.target.value) || 120 })
                  }
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
