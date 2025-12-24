"use client";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { WorkflowNodeData } from "@/types/workflow";
import { useAgents } from "@/lib/hooks/use-agents";

interface AgentStepConfigProps {
  data: WorkflowNodeData;
  onChange: (data: Partial<WorkflowNodeData>) => void;
}

export function AgentStepConfig({ data, onChange }: AgentStepConfigProps) {
  const { data: agentsData, isLoading } = useAgents();
  const agents = agentsData?.agents || [];

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="agent">Agent</Label>
        <Select
          value={data.agentId || ""}
          onValueChange={(value) => {
            const agent = agents.find((a) => a.id === value);
            onChange({
              agentId: value,
              agentName: agent?.name || value,
            });
          }}
        >
          <SelectTrigger>
            <SelectValue placeholder={isLoading ? "Loading..." : "Select an agent"} />
          </SelectTrigger>
          <SelectContent>
            {agents.map((agent) => (
              <SelectItem key={agent.id} value={agent.id}>
                <div className="flex flex-col">
                  <span>{agent.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {agent.agent_type}
                  </span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="input">Input Template</Label>
        <Textarea
          id="input"
          value={data.input || "${user_input}"}
          onChange={(e) => onChange({ input: e.target.value })}
          placeholder="${user_input}"
          className="font-mono text-sm"
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          Use {"${user_input}"} for user input, {"${steps.stepId.output}"} for previous step output
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="timeout">Timeout (seconds)</Label>
          <Input
            id="timeout"
            type="number"
            min={1}
            max={600}
            value={data.timeout || 120}
            onChange={(e) => onChange({ timeout: parseInt(e.target.value) || 120 })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="retries">Retries</Label>
          <Input
            id="retries"
            type="number"
            min={0}
            max={5}
            value={data.retries || 0}
            onChange={(e) => onChange({ retries: parseInt(e.target.value) || 0 })}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="onError">On Error</Label>
        <Select
          value={data.onError || "fail"}
          onValueChange={(value) => onChange({ onError: value })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="fail">Fail workflow</SelectItem>
            <SelectItem value="skip">Skip and continue</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
