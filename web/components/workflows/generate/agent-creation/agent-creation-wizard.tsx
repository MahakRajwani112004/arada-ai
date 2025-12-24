"use client";

import { useState } from "react";
import { AgentPrefillForm } from "./agent-prefill-form";
import { CreationProgress } from "./creation-progress";
import { SkipAgentDialog } from "./skip-agent-dialog";
import type { AgentSuggestion } from "@/types/agent-suggestion";
import { useCreateAgent } from "@/lib/hooks/use-agents";

interface AgentCreationWizardProps {
  suggestions: AgentSuggestion[];
  onComplete: (createdAgentIds: string[], skippedAgentIds: string[]) => void;
  onBack: () => void;
}

interface FormData {
  id: string;
  name: string;
  description?: string;
  agent_type: "SimpleAgent" | "LLMAgent" | "RAGAgent" | "ToolAgent" | "FullAgent" | "RouterAgent";
  role_title: string;
  role_expertise?: string;
  goal_objective: string;
  instructions?: string;
}

export function AgentCreationWizard({
  suggestions,
  onComplete,
}: AgentCreationWizardProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [createdAgentIds, setCreatedAgentIds] = useState<string[]>([]);
  const [skippedAgentIds, setSkippedAgentIds] = useState<string[]>([]);
  const [showSkipDialog, setShowSkipDialog] = useState(false);

  const createAgent = useCreateAgent();

  const currentSuggestion = suggestions[currentIndex];
  const isLastAgent = currentIndex === suggestions.length - 1;

  const handleCreate = async (data: FormData) => {
    try {
      // Transform form data to AgentCreate format
      await createAgent.mutateAsync({
        id: data.id,
        name: data.name,
        description: data.description || "",
        agent_type: data.agent_type,
        role: {
          title: data.role_title,
          expertise: data.role_expertise?.split(",").map((s) => s.trim()).filter(Boolean) || [],
          personality: ["helpful", "professional"],
          communication_style: "clear and concise",
        },
        goal: {
          objective: data.goal_objective,
          success_criteria: [],
          constraints: [],
        },
        instructions: {
          steps: data.instructions?.split("\n").filter(Boolean) || [],
          rules: [],
          prohibited_actions: [],
          output_format: "text",
        },
        examples: [],
        llm_config: {
          provider: "openai",
          model: "gpt-4o",
          temperature: 0.7,
        },
        tools: [],
        safety: {
          level: "standard",
          blocked_topics: [],
          blocked_patterns: [],
        },
      });

      setCreatedAgentIds((prev) => [...prev, data.id]);

      if (isLastAgent) {
        onComplete([...createdAgentIds, data.id], skippedAgentIds);
      } else {
        setCurrentIndex((prev) => prev + 1);
      }
    } catch (error) {
      // Error is handled by the mutation's onError
      console.error("Failed to create agent:", error);
    }
  };

  const handleSkipConfirm = () => {
    const agentId = currentSuggestion?.id || "";
    setSkippedAgentIds((prev) => [...prev, agentId]);
    setShowSkipDialog(false);

    if (isLastAgent) {
      onComplete(createdAgentIds, [...skippedAgentIds, agentId]);
    } else {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  if (suggestions.length === 0) {
    // No agents to create
    onComplete([], []);
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Create Missing Agents</h2>
        <p className="text-muted-foreground">
          {suggestions.length} agent{suggestions.length > 1 ? "s need" : " needs"} to be created.
          Review and create each one, or skip to create later.
        </p>
      </div>

      <CreationProgress
        totalAgents={suggestions.length}
        createdCount={createdAgentIds.length}
        skippedCount={skippedAgentIds.length}
        currentAgentName={currentSuggestion?.name}
      />

      {currentSuggestion && (
        <AgentPrefillForm
          suggestion={currentSuggestion}
          onSubmit={handleCreate}
          onSkip={() => setShowSkipDialog(true)}
          isSubmitting={createAgent.isPending}
          currentIndex={currentIndex}
          totalCount={suggestions.length}
        />
      )}

      <SkipAgentDialog
        open={showSkipDialog}
        onOpenChange={setShowSkipDialog}
        agentId={currentSuggestion?.id || ""}
        stepId=""
        onConfirm={handleSkipConfirm}
      />
    </div>
  );
}
