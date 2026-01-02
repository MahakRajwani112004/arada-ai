"use client";

import { useState } from "react";
import { ArrowLeft, ArrowRight, Check, SkipForward, Loader2, AlertCircle, Bot, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAvailableAgents, useCreateWorkflow } from "@/lib/hooks/use-workflows";
import { AgentCreationSheet } from "@/components/agents/agent-creation-sheet";
import type { Agent } from "@/types/agent";
import type { WorkflowSkeleton, SkeletonStepWithSuggestion, WorkflowDefinition, WorkflowStep } from "@/types/workflow";

interface StepConfiguratorProps {
  skeleton: WorkflowSkeleton;
  stepSuggestions: SkeletonStepWithSuggestion[];
  onBack: () => void;
  onComplete: (workflowId: string) => void;
}

type ConfigMode = "existing" | "create" | "skip";

interface StepConfig {
  mode: ConfigMode;
  existingAgentId?: string;
  // For created agents, we store the agent ID after creation
  createdAgentId?: string;
  createdAgentName?: string;
}

export function StepConfigurator({
  skeleton,
  stepSuggestions,
  onBack,
  onComplete,
}: StepConfiguratorProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [configs, setConfigs] = useState<Map<string, StepConfig>>(() => {
    const map = new Map<string, StepConfig>();
    skeleton.steps.forEach((step) => {
      map.set(step.id, {
        mode: "existing", // Default to existing, user can choose to create
      });
    });
    return map;
  });
  const [isCreating, setIsCreating] = useState(false);
  const [showAgentSheet, setShowAgentSheet] = useState(false);

  const { data: agentsData } = useAvailableAgents();
  const createWorkflow = useCreateWorkflow();

  const currentStep = skeleton.steps[currentIndex];
  const currentSuggestion = stepSuggestions.find(s => s.id === currentStep.id)?.suggestion;
  const currentConfig = configs.get(currentStep.id)!;
  const progress = ((currentIndex + 1) / skeleton.steps.length) * 100;

  const updateConfig = (updates: Partial<StepConfig>) => {
    setConfigs(prev => {
      const newMap = new Map(prev);
      newMap.set(currentStep.id, { ...currentConfig, ...updates });
      return newMap;
    });
  };

  const canProceed = () => {
    if (currentConfig.mode === "skip") return true;
    if (currentConfig.mode === "existing") return !!currentConfig.existingAgentId;
    if (currentConfig.mode === "create") return !!currentConfig.createdAgentId; // Agent must be created via sheet
    return false;
  };

  // Handle agent creation from sheet
  const handleAgentCreated = (agent: Agent) => {
    setConfigs(prev => {
      const newMap = new Map(prev);
      newMap.set(currentStep.id, {
        mode: "create",
        createdAgentId: agent.id,
        createdAgentName: agent.name,
      });
      return newMap;
    });
    setShowAgentSheet(false);
  };

  const handleNext = () => {
    if (currentIndex < skeleton.steps.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleComplete = async () => {
    setIsCreating(true);

    try {
      // Build agent ID map from configs (agents are already created via sheet)
      const agentIdMap = new Map<string, string>();

      for (const step of skeleton.steps) {
        const config = configs.get(step.id)!;

        if (config.mode === "create" && config.createdAgentId) {
          agentIdMap.set(step.id, config.createdAgentId);
        } else if (config.mode === "existing" && config.existingAgentId) {
          agentIdMap.set(step.id, config.existingAgentId);
        }
      }

      // Build workflow definition
      const workflowSteps: WorkflowStep[] = skeleton.steps
        .filter(step => configs.get(step.id)?.mode !== "skip")
        .map((step) => {
          const agentId = agentIdMap.get(step.id);
          return {
            id: step.id,
            type: "agent" as const,
            agent_id: agentId,
            input: "${user_input}",
            timeout: 120,
            retries: 0,
            on_error: "fail",
          };
        });

      const workflowId = skeleton.name.toLowerCase().replace(/[^a-z0-9]+/g, "-");

      const workflowDefinition: WorkflowDefinition = {
        id: workflowId,
        name: skeleton.name,
        description: skeleton.description,
        steps: workflowSteps,
        entry_step: workflowSteps[0]?.id,
      };

      // Create the workflow
      const workflow = await createWorkflow.mutateAsync({
        id: workflowId,
        name: skeleton.name,
        description: skeleton.description,
        category: "ai-generated",
        tags: [],
        definition: workflowDefinition,
      });

      onComplete(workflow.id);
    } catch (error) {
      console.error("Failed to create workflow:", error);
    } finally {
      setIsCreating(false);
    }
  };

  const isLastStep = currentIndex === skeleton.steps.length - 1;

  return (
    <div className="space-y-6">
      {/* Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            Step {currentIndex + 1} of {skeleton.steps.length}
          </span>
          <span className="font-medium">{currentStep.name}</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Current Step Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary text-sm font-bold">
              {currentIndex + 1}
            </div>
            Configure: {currentStep.name}
          </CardTitle>
          <CardDescription>{currentStep.role}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Mode Selection */}
          <div className="space-y-3">
            <Label>How should this step be handled?</Label>
            <RadioGroup
              value={currentConfig.mode}
              onValueChange={(value) => updateConfig({ mode: value as ConfigMode })}
              className="space-y-2"
            >
              <label className="flex items-center space-x-3 cursor-pointer">
                <RadioGroupItem value="existing" id="existing" />
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4" />
                  <span>Use existing agent</span>
                </div>
              </label>
              <label className="flex items-center space-x-3 cursor-pointer">
                <RadioGroupItem value="create" id="create" />
                <div className="flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  <span>Create new agent</span>
                  {currentSuggestion && (
                    <Badge variant="secondary" className="text-xs">AI suggested</Badge>
                  )}
                </div>
              </label>
              <label className="flex items-center space-x-3 cursor-pointer">
                <RadioGroupItem value="skip" id="skip" />
                <div className="flex items-center gap-2">
                  <SkipForward className="h-4 w-4" />
                  <span>Skip for now</span>
                </div>
              </label>
            </RadioGroup>
          </div>

          {/* Existing Agent Selection */}
          {currentConfig.mode === "existing" && (
            <div className="space-y-3">
              <Label>Select Agent</Label>
              <Select
                value={currentConfig.existingAgentId}
                onValueChange={(value) => updateConfig({ existingAgentId: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose an agent..." />
                </SelectTrigger>
                <SelectContent>
                  {agentsData?.agents.map((agent) => (
                    <SelectItem key={agent.id} value={agent.id}>
                      <div className="flex flex-col">
                        <span>{agent.name}</span>
                        <span className="text-xs text-muted-foreground">{agent.description}</span>
                      </div>
                    </SelectItem>
                  ))}
                  {(!agentsData?.agents || agentsData.agents.length === 0) && (
                    <div className="p-2 text-sm text-muted-foreground text-center">
                      No agents available. Create a new one instead.
                    </div>
                  )}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* New Agent Creation */}
          {currentConfig.mode === "create" && (
            <div className="space-y-4 border-t pt-4">
              {currentConfig.createdAgentId ? (
                // Agent already created - show confirmation
                <div className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 border border-green-500/30">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500/20">
                    <Check className="h-5 w-5 text-green-500" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">{currentConfig.createdAgentName}</p>
                    <p className="text-sm text-muted-foreground">Agent created successfully</p>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAgentSheet(true)}
                  >
                    Create Different
                  </Button>
                </div>
              ) : (
                // Agent not yet created - show create button
                <div className="flex flex-col items-center gap-4 p-6 rounded-lg border border-dashed">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-500/10">
                    <Plus className="h-6 w-6 text-purple-500" />
                  </div>
                  <div className="text-center">
                    <p className="font-medium">Create a new agent for this step</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Use our full agent builder with AI assistance
                    </p>
                  </div>
                  <Button
                    type="button"
                    onClick={() => setShowAgentSheet(true)}
                    className="gap-2"
                  >
                    <Plus className="h-4 w-4" />
                    Create Agent
                  </Button>
                  {currentSuggestion?.required_mcps && currentSuggestion.required_mcps.length > 0 && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                      <span>May need:</span>
                      {currentSuggestion.required_mcps.map((mcp) => (
                        <Badge key={mcp} variant="outline">{mcp}</Badge>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Skip Message */}
          {currentConfig.mode === "skip" && (
            <div className="p-4 rounded-lg bg-muted/50 text-sm text-muted-foreground">
              This step will be included in the workflow but will not have an agent assigned yet.
              You can configure it later from the workflow editor.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={currentIndex === 0 ? onBack : handlePrevious}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          {currentIndex === 0 ? "Back to Structure" : "Previous Step"}
        </Button>

        {isLastStep ? (
          <Button
            onClick={handleComplete}
            disabled={!canProceed() || isCreating}
          >
            {isCreating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Check className="h-4 w-4 mr-2" />
                Create Workflow
              </>
            )}
          </Button>
        ) : (
          <Button
            onClick={handleNext}
            disabled={!canProceed()}
          >
            Next Step
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        )}
      </div>

      {/* Step Overview */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">All Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {skeleton.steps.map((step, index) => {
              const config = configs.get(step.id);
              const isConfigured = config?.mode === "existing" ? !!config.existingAgentId :
                                   config?.mode === "create" ? !!config.createdAgentId :
                                   config?.mode === "skip";

              return (
                <button
                  key={step.id}
                  onClick={() => setCurrentIndex(index)}
                  className={`
                    px-3 py-1.5 rounded-lg text-sm border transition-colors
                    ${index === currentIndex ? "border-primary bg-primary/10" : "border-border hover:bg-muted"}
                    ${isConfigured ? "text-foreground" : "text-muted-foreground"}
                  `}
                >
                  <span className="flex items-center gap-1.5">
                    {isConfigured && <Check className="h-3 w-3 text-green-500" />}
                    {step.name}
                  </span>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Agent Creation Sheet */}
      <AgentCreationSheet
        open={showAgentSheet}
        onOpenChange={setShowAgentSheet}
        suggestedName={currentSuggestion?.name || currentStep.name}
        suggestedGoal={currentSuggestion?.goal || `You are an AI agent responsible for: ${currentStep.role}`}
        suggestedDescription={currentStep.role}
        context={`Workflow step: ${currentStep.name}`}
        onAgentCreated={handleAgentCreated}
      />
    </div>
  );
}
