"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Sparkles, Loader2 } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { SkeletonEditor } from "@/components/workflows/create/skeleton-editor";
import { useGenerateWorkflowSkeleton, useCreateWorkflow } from "@/lib/hooks/use-workflows";
import type { GenerateSkeletonResponse, WorkflowSkeleton, SkeletonStepWithSuggestion, WorkflowDefinition, WorkflowStep } from "@/types/workflow";

type CreationPhase = "prompt" | "skeleton";

export default function CreateWorkflowPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<CreationPhase>("prompt");
  const [prompt, setPrompt] = useState("");
  const [skeletonResponse, setSkeletonResponse] = useState<GenerateSkeletonResponse | null>(null);
  const [editedSkeleton, setEditedSkeleton] = useState<WorkflowSkeleton | null>(null);
  const [stepSuggestions, setStepSuggestions] = useState<SkeletonStepWithSuggestion[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  const generateSkeleton = useGenerateWorkflowSkeleton();
  const createWorkflow = useCreateWorkflow();

  const handleGenerateSkeleton = async () => {
    if (!prompt.trim()) return;

    try {
      const response = await generateSkeleton.mutateAsync({ prompt });
      setSkeletonResponse(response);
      setEditedSkeleton(response.skeleton);
      setStepSuggestions(response.step_suggestions);
      setPhase("skeleton");
    } catch {
      // Error handled by mutation
    }
  };

  // Save workflow with suggested agents and redirect to canvas
  const handleSkeletonConfirm = async (skeleton: WorkflowSkeleton, suggestions: SkeletonStepWithSuggestion[]) => {
    setEditedSkeleton(skeleton);
    setStepSuggestions(suggestions);
    setIsSaving(true);

    try {
      // Convert skeleton steps to workflow steps with suggested agents
      const workflowSteps: WorkflowStep[] = skeleton.steps.map((step, index) => {
        const suggestion = suggestions.find(s => s.id === step.id)?.suggestion;
        return {
          id: step.id,
          type: "agent" as const,
          name: step.name,
          agent_id: undefined, // No agent assigned yet - will be created in canvas
          suggested_agent: suggestion ? {
            name: suggestion.name,
            description: `${step.name} - ${step.role}`,
            goal: suggestion.goal,
            model: "gpt-4o",
            required_mcps: suggestion.required_mcps || [],
            suggested_tools: suggestion.suggested_tools || [],
          } : undefined,
          input: index === 0 ? "${user_input}" : "${previous}",
          timeout: 120,
          retries: 0,
          on_error: "fail",
        };
      });

      // Create workflow ID from name
      const workflowId = skeleton.name
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^a-z0-9-]/g, "")
        .slice(0, 50);

      const definition: WorkflowDefinition = {
        id: workflowId,
        name: skeleton.name,
        description: skeleton.description,
        steps: workflowSteps,
        entry_step: workflowSteps[0]?.id,
      };

      // Create the workflow
      await createWorkflow.mutateAsync({
        id: workflowId,
        name: skeleton.name,
        description: skeleton.description,
        category: "ai-generated",
        tags: ["ai-created"],
        definition,
      });

      // Redirect to canvas for agent configuration
      router.push(`/workflows/${workflowId}/canvas`);
    } catch (error) {
      console.error("Failed to create workflow:", error);
      setIsSaving(false);
    }
  };

  const handleBackToPrompt = () => {
    setPhase("prompt");
  };

  return (
    <>
      <Header />
      <PageContainer>
        <div className="mx-auto max-w-4xl">
          {/* Back Link */}
          <Link
            href="/workflows"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Workflows
          </Link>

          {/* Phase 1: Prompt Input */}
          {phase === "prompt" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  Create Workflow with AI
                </CardTitle>
                <CardDescription>
                  Describe what you want your workflow to accomplish. AI will suggest a structure
                  that you can review and customize.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="Example: Monitor my emails, classify them by urgency, and send Slack notifications for urgent ones"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={4}
                  className="resize-none"
                />
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    {prompt.length}/2000 characters
                  </p>
                  <Button
                    onClick={handleGenerateSkeleton}
                    disabled={!prompt.trim() || generateSkeleton.isPending}
                  >
                    {generateSkeleton.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-2" />
                        Generate Structure
                      </>
                    )}
                  </Button>
                </div>

                {/* Example prompts */}
                <div className="border-t pt-4 mt-4">
                  <p className="text-sm font-medium mb-3">Example prompts:</p>
                  <div className="space-y-2">
                    {[
                      "Create a customer support workflow that classifies tickets and routes them to the right team",
                      "Build an email monitoring system that summarizes important emails and creates tasks",
                      "Set up a content review pipeline that checks for quality and sends approvals",
                    ].map((example) => (
                      <button
                        key={example}
                        onClick={() => setPrompt(example)}
                        className="block w-full text-left text-sm text-muted-foreground hover:text-foreground p-2 rounded hover:bg-muted transition-colors"
                      >
                        &ldquo;{example}&rdquo;
                      </button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Phase 2: Skeleton Editor */}
          {phase === "skeleton" && editedSkeleton && skeletonResponse && (
            <SkeletonEditor
              skeleton={editedSkeleton}
              stepSuggestions={stepSuggestions}
              mcpDependencies={skeletonResponse.mcp_dependencies}
              explanation={skeletonResponse.explanation}
              warnings={skeletonResponse.warnings}
              onConfirm={handleSkeletonConfirm}
              onBack={handleBackToPrompt}
              onEditPrompt={() => setPhase("prompt")}
              isSaving={isSaving}
            />
          )}
        </div>
      </PageContainer>
    </>
  );
}
