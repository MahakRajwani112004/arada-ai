"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCreateAgent, useUpdateAgent } from "@/lib/hooks/use-agents";
import type { AgentDetail, AgentCreate } from "@/types/agent";
import {
  AgentFormFields,
  AgentFormData,
  defaultAgentFormData,
  detectAgentType,
} from "./agent-form-fields";

interface AgentFormProps {
  initialData?: AgentDetail;
  isEditing?: boolean;
  onCancel?: () => void;
}

// Confetti component
function Confetti() {
  const pieces = Array.from({ length: 50 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    rotation: Math.random() * 360,
    delay: Math.random() * 0.5,
    duration: 2 + Math.random() * 2,
    color: ["#ff6b6b", "#4ecdc4", "#45b7d1", "#f7b731", "#5f27cd"][i % 5],
  }));

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {pieces.map((piece) => (
        <motion.div
          key={piece.id}
          className="absolute w-3 h-3 rounded-sm"
          style={{
            left: `${piece.x}%`,
            top: "-10%",
            backgroundColor: piece.color,
          }}
          initial={{ y: -100, rotate: 0, opacity: 1 }}
          animate={{ y: "100vh", rotate: piece.rotation, opacity: 0 }}
          transition={{
            duration: piece.duration,
            delay: piece.delay,
            ease: "easeIn",
          }}
        />
      ))}
    </div>
  );
}

// Convert AgentDetail to AgentFormData
function toFormData(detail?: AgentDetail): AgentFormData {
  if (!detail) return defaultAgentFormData;

  return {
    name: detail.name ?? "",
    description: detail.description ?? "",
    roleTitle: detail.role?.title ?? "",
    personality: detail.role?.personality ?? [],
    expertise: detail.role?.expertise ?? [],
    communicationStyle: detail.role?.communication_style ?? "",
    goal: detail.goal?.objective ?? "",
    successCriteria: detail.goal?.success_criteria ?? [],
    instructions: detail.instructions?.steps?.join("\n") ?? "",
    rules: detail.instructions?.rules ?? [],
    examples: detail.examples ?? [],
    selectedTools: detail.tools?.map((t) => t.tool_id) ?? [],
    knowledgeBase: detail.knowledge_base ?? undefined,
    llmProvider:
      (detail.llm_config?.provider as "openai" | "anthropic") ?? "openai",
    llmModel: detail.llm_config?.model ?? "gpt-4o",
    temperature: detail.llm_config?.temperature ?? 0.7,
  };
}

export function AgentForm({
  initialData,
  isEditing = false,
  onCancel,
}: AgentFormProps) {
  const router = useRouter();
  const createAgent = useCreateAgent();
  const updateAgent = useUpdateAgent();

  // Form state
  const [formData, setFormData] = useState<AgentFormData>(() =>
    toFormData(initialData)
  );

  // UI state
  const [showConfetti, setShowConfetti] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // Submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Use existing ID when editing, generate new one when creating
    const agentId =
      isEditing && initialData
        ? initialData.id
        : formData.name
            .toLowerCase()
            .replace(/\s+/g, "-")
            .replace(/[^a-z0-9-]/g, "");

    const agent: AgentCreate = {
      id: agentId,
      name: formData.name,
      description: formData.description || `${formData.name} agent`,
      agent_type: detectAgentType(
        formData.goal,
        formData.selectedTools,
        !!formData.knowledgeBase
      ),
      role: {
        title: formData.roleTitle || "AI Assistant",
        expertise:
          formData.expertise.length > 0
            ? formData.expertise
            : ["general assistance"],
        personality:
          formData.personality.length > 0
            ? formData.personality
            : ["helpful", "professional"],
        communication_style:
          formData.communicationStyle || "Clear and concise",
      },
      goal: {
        objective:
          formData.goal ||
          `Help users with ${formData.name.toLowerCase()} tasks`,
        success_criteria:
          formData.successCriteria.length > 0
            ? formData.successCriteria
            : ["Task completed"],
        constraints: [],
      },
      instructions: {
        steps: formData.instructions
          ? formData.instructions.split("\n").filter(Boolean)
          : ["Listen to user request", "Provide helpful response"],
        rules:
          formData.rules.length > 0
            ? formData.rules
            : ["Be helpful and accurate"],
        prohibited_actions: [],
        output_format: "Natural language response",
      },
      examples: formData.examples,
      llm_config: {
        provider: formData.llmProvider,
        model: formData.llmModel,
        temperature: formData.temperature,
      },
      knowledge_base: formData.knowledgeBase,
      tools: formData.selectedTools.map((id) => ({ tool_id: id })),
      safety: {
        level: "standard",
        blocked_topics: [],
        blocked_patterns: [],
      },
    };

    if (isEditing && initialData) {
      await updateAgent.mutateAsync({ agentId: initialData.id, agent });
      setShowSuccess(true);
      setTimeout(() => {
        if (onCancel) {
          onCancel();
        } else {
          router.push(`/agents/${initialData.id}`);
        }
      }, 1500);
    } else {
      await createAgent.mutateAsync(agent);
      setShowSuccess(true);
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 4000);
      setTimeout(() => router.push("/agents"), 2000);
    }
  };

  const isPending = isEditing ? updateAgent.isPending : createAgent.isPending;

  return (
    <>
      {showConfetti && <Confetti />}

      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              className="bg-card border rounded-2xl p-8 text-center"
            >
              <div className="text-5xl mb-3">
                {isEditing ? "✅" : "🎉"}
              </div>
              <h2 className="text-xl font-bold">
                {isEditing ? "Agent Updated!" : "Agent Created!"}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                {isEditing ? "Changes saved" : "Redirecting..."}
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
        {/* Left Column - Main Form */}
        <div className="lg:col-span-2">
          <AgentFormFields
            data={formData}
            onChange={setFormData}
            mode="full"
            showAIGeneration={true}
          />
        </div>

        {/* Right Column - Guide & Actions */}
        <div className="space-y-4">
          {/* Guide */}
          <div className="rounded-lg border bg-card p-4">
            <div className="text-center mb-4">
              <Sparkles className="h-6 w-6 mx-auto text-muted-foreground mb-2" />
              <h3 className="font-medium">Quick Start</h3>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex gap-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                  1
                </span>
                <div>
                  <div className="font-medium">Name & Model</div>
                  <div className="text-xs text-muted-foreground">
                    Give your agent a name and select LLM
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-secondary text-xs">
                  2
                </span>
                <div>
                  <div className="font-medium">Define Role & Goal</div>
                  <div className="text-xs text-muted-foreground">
                    Or click &quot;Generate with AI&quot;
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-secondary text-xs">
                  3
                </span>
                <div>
                  <div className="font-medium">Add Tools (Optional)</div>
                  <div className="text-xs text-muted-foreground">
                    Connect MCP tools
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-2 mt-4">
              <Button
                type="submit"
                disabled={isPending || !formData.name.trim()}
                className="w-full"
              >
                {isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {isEditing ? "Saving..." : "Creating..."}
                  </>
                ) : isEditing ? (
                  "Save Changes"
                ) : (
                  "Create Agent"
                )}
              </Button>
              {isEditing && onCancel && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={onCancel}
                  className="w-full"
                >
                  Cancel
                </Button>
              )}
            </div>
          </div>
        </div>
      </form>
    </>
  );
}
