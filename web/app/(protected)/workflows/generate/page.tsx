"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { BuilderProgress } from "@/components/workflows/builder/builder-progress";
import { AIPromptInput } from "@/components/workflows/generate/ai-prompt-input";
import { AIGenerationLoader } from "@/components/workflows/generate/ai-generation-loader";
import { AIReviewPanel } from "@/components/workflows/generate/ai-review-panel";
import { AIResourceStatus } from "@/components/workflows/generate/ai-resource-status";
import { AgentCreationWizard } from "@/components/workflows/generate/agent-creation/agent-creation-wizard";
import { WorkflowSaveForm } from "@/components/workflows/generate/workflow-save-form";
import { Button } from "@/components/ui/button";
import { useGenerateWorkflow, useSaveGeneratedWorkflow } from "@/lib/hooks/use-workflows";
import type { GenerationWizardStep } from "@/types/agent-suggestion";
import type { GenerateWorkflowResponse } from "@/types/workflow";

export default function GenerateWorkflowPage() {
  const router = useRouter();

  const [step, setStep] = useState<GenerationWizardStep>("describe");
  const [generatedResponse, setGeneratedResponse] = useState<GenerateWorkflowResponse | null>(null);
  const [createdAgentIds, setCreatedAgentIds] = useState<string[]>([]);
  const [skippedAgentIds, setSkippedAgentIds] = useState<string[]>([]);

  const generateWorkflow = useGenerateWorkflow();
  const saveWorkflow = useSaveGeneratedWorkflow();

  const handlePromptSubmit = async (prompt: string) => {
    setStep("loading");

    try {
      const response = await generateWorkflow.mutateAsync({ prompt });
      setGeneratedResponse(response);
      setStep("review");
    } catch {
      // Error handled by mutation
      setStep("describe");
    }
  };

  const handleReviewContinue = () => {
    if (!generatedResponse) return;

    if ((generatedResponse.agents_to_create ?? []).length > 0) {
      setStep("create_agents");
    } else {
      setStep("save");
    }
  };

  const handleReviewRegenerate = () => {
    setGeneratedResponse(null);
    setCreatedAgentIds([]);
    setSkippedAgentIds([]);
    setStep("describe");
  };

  const handleAgentsComplete = (created: string[], skipped: string[]) => {
    setCreatedAgentIds(created);
    setSkippedAgentIds(skipped);
    setStep("save");
  };

  const handleSave = async (data: { name: string; description?: string; category: string }) => {
    if (!generatedResponse) return;

    try {
      const result = await saveWorkflow.mutateAsync({
        workflow: generatedResponse.workflow,
        workflow_name: data.name,
        workflow_description: data.description || "",
        workflow_category: data.category,
      });

      router.push(`/workflows/${result.workflow_id}`);
    } catch {
      // Error handled by mutation
    }
  };

  const hasAgentsToCreate = (generatedResponse?.agents_to_create?.length ?? 0) > 0;

  return (
    <>
      <Header />
      <PageContainer>
        <div className="mx-auto max-w-3xl">
          {/* Back Link */}
          <Link
            href="/workflows"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Workflows
          </Link>

          {/* Progress Indicator */}
          <div className="mb-8">
            <BuilderProgress currentStep={step} hasAgentsToCreate={hasAgentsToCreate} />
          </div>

          {/* Step Content */}
          {step === "describe" && (
            <AIPromptInput
              onSubmit={handlePromptSubmit}
              isLoading={generateWorkflow.isPending}
            />
          )}

          {step === "loading" && <AIGenerationLoader />}

          {step === "review" && generatedResponse && (
            <div className="space-y-6">
              <div className="grid gap-6 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <AIReviewPanel response={generatedResponse} />
                </div>
                <div>
                  <AIResourceStatus response={generatedResponse} />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <Button variant="outline" onClick={handleReviewRegenerate}>
                  Regenerate
                </Button>
                <Button onClick={handleReviewContinue}>
                  {hasAgentsToCreate ? "Continue to Create Agents" : "Continue to Save"}
                </Button>
              </div>
            </div>
          )}

          {step === "create_agents" && generatedResponse && (
            <AgentCreationWizard
              suggestions={generatedResponse.agents_to_create}
              onComplete={handleAgentsComplete}
              onBack={() => setStep("review")}
            />
          )}

          {step === "save" && generatedResponse && (
            <WorkflowSaveForm
              response={generatedResponse}
              createdAgentIds={createdAgentIds}
              skippedAgentIds={skippedAgentIds}
              onSubmit={handleSave}
              isSubmitting={saveWorkflow.isPending}
            />
          )}
        </div>
      </PageContainer>
    </>
  );
}
