"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus, Trash2, GripVertical, Loader2, Zap, Play } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAvailableAgents, useCreateWorkflow } from "@/lib/hooks/use-workflows";
import type { TriggerType, WorkflowDefinition, WorkflowStep } from "@/types/workflow";

interface ManualStep {
  id: string;
  name: string;
  agentId: string;
  input: string;
}

export default function ManualWorkflowPage() {
  const router = useRouter();
  const createWorkflow = useCreateWorkflow();
  const { data: agentsData } = useAvailableAgents();

  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [triggerType, setTriggerType] = useState<TriggerType>("manual");
  const [steps, setSteps] = useState<ManualStep[]>([
    { id: "step-1", name: "Step 1", agentId: "", input: "${user_input}" },
  ]);

  const addStep = () => {
    const newId = `step-${steps.length + 1}`;
    setSteps([
      ...steps,
      { id: newId, name: `Step ${steps.length + 1}`, agentId: "", input: "${previous_output}" },
    ]);
  };

  const removeStep = (index: number) => {
    if (steps.length > 1) {
      setSteps(steps.filter((_, i) => i !== index));
    }
  };

  const updateStep = (index: number, updates: Partial<ManualStep>) => {
    setSteps(steps.map((step, i) => (i === index ? { ...step, ...updates } : step)));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const workflowId = name.toLowerCase().replace(/[^a-z0-9]+/g, "-");

    const workflowSteps: WorkflowStep[] = steps.map((step) => ({
      id: step.id,
      type: "agent" as const,
      agent_id: step.agentId || undefined,
      input: step.input || "${user_input}",
      timeout: 120,
      retries: 0,
      on_error: "fail",
    }));

    const definition: WorkflowDefinition = {
      id: workflowId,
      name,
      description,
      steps: workflowSteps,
      entry_step: workflowSteps[0]?.id,
    };

    try {
      const workflow = await createWorkflow.mutateAsync({
        id: workflowId,
        name,
        description,
        category: "manual",
        tags: [],
        definition,
      });

      router.push(`/workflows/${workflow.id}`);
    } catch (error) {
      console.error("Failed to create workflow:", error);
    }
  };

  const isValid = name.trim() && steps.length > 0;

  return (
    <>
      <Header />
      <PageContainer>
        <div className="max-w-3xl">
          <Link
            href="/workflows/new"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Options
          </Link>

          <div className="mb-8">
            <h1 className="text-2xl font-bold">Build Workflow Manually</h1>
            <p className="mt-2 text-muted-foreground">
              Create a workflow step by step with full control
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Workflow Name *</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., Customer Support Router"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="What does this workflow do?"
                    rows={2}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Trigger Type */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Trigger</CardTitle>
              </CardHeader>
              <CardContent>
                <RadioGroup
                  value={triggerType}
                  onValueChange={(v) => setTriggerType(v as TriggerType)}
                  className="grid grid-cols-2 gap-4"
                >
                  <label
                    className={`flex items-center gap-3 rounded-lg border p-4 cursor-pointer transition-colors ${
                      triggerType === "manual" ? "border-primary bg-primary/5" : "hover:bg-muted/50"
                    }`}
                  >
                    <RadioGroupItem value="manual" id="manual" />
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                        <Play className="h-5 w-5 text-green-500" />
                      </div>
                      <div>
                        <div className="font-medium">Manual</div>
                        <div className="text-xs text-muted-foreground">Run on demand</div>
                      </div>
                    </div>
                  </label>
                  <label
                    className={`flex items-center gap-3 rounded-lg border p-4 cursor-pointer transition-colors ${
                      triggerType === "webhook" ? "border-primary bg-primary/5" : "hover:bg-muted/50"
                    }`}
                  >
                    <RadioGroupItem value="webhook" id="webhook" />
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-yellow-500/10">
                        <Zap className="h-5 w-5 text-yellow-500" />
                      </div>
                      <div>
                        <div className="font-medium">Webhook</div>
                        <div className="text-xs text-muted-foreground">HTTP trigger</div>
                      </div>
                    </div>
                  </label>
                </RadioGroup>
              </CardContent>
            </Card>

            {/* Steps */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-lg">Steps</CardTitle>
                <Button type="button" variant="outline" size="sm" onClick={addStep}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Step
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {steps.map((step, index) => (
                  <div
                    key={step.id}
                    className="flex gap-3 p-4 rounded-lg border bg-card"
                  >
                    <div className="flex items-center text-muted-foreground">
                      <GripVertical className="h-5 w-5" />
                    </div>
                    <div className="flex-1 space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-medium text-sm">
                          {index + 1}
                        </div>
                        <Input
                          value={step.name}
                          onChange={(e) => updateStep(index, { name: e.target.value })}
                          placeholder="Step name"
                          className="flex-1"
                        />
                        {steps.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
                            onClick={() => removeStep(index)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs">Agent</Label>
                          <Select
                            value={step.agentId}
                            onValueChange={(v) => updateStep(index, { agentId: v })}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select agent..." />
                            </SelectTrigger>
                            <SelectContent>
                              {agentsData?.agents.map((agent) => (
                                <SelectItem key={agent.id} value={agent.id}>
                                  {agent.name}
                                </SelectItem>
                              ))}
                              {(!agentsData?.agents || agentsData.agents.length === 0) && (
                                <div className="p-2 text-sm text-muted-foreground text-center">
                                  No agents available
                                </div>
                              )}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Input Template</Label>
                          <Input
                            value={step.input}
                            onChange={(e) => updateStep(index, { input: e.target.value })}
                            placeholder="${user_input}"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {steps.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    Add at least one step to your workflow
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Submit */}
            <div className="flex justify-end gap-3">
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
              <Button type="submit" disabled={!isValid || createWorkflow.isPending}>
                {createWorkflow.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Workflow"
                )}
              </Button>
            </div>
          </form>
        </div>
      </PageContainer>
    </>
  );
}
