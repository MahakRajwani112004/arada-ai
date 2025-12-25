"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useCreateAgent } from "@/lib/hooks/use-agents";
import type { Agent, AgentCreate } from "@/types/agent";
import {
  AgentFormFields,
  AgentFormData,
  defaultAgentFormData,
  detectAgentType,
} from "./agent-form-fields";

interface AgentCreationSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;

  // Pre-fill options
  suggestedName?: string;
  suggestedGoal?: string;
  suggestedDescription?: string;
  suggestedTools?: string[];

  // Context for AI generation
  context?: string; // e.g., "For workflow step: Classify Tickets"

  // Callbacks
  onAgentCreated: (agent: Agent) => void;
  onCancel?: () => void;
}

// Success celebration component
function SuccessOverlay({ agentName }: { agentName: string }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-50 flex items-center justify-center bg-background/90 backdrop-blur-sm"
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", damping: 15 }}
        className="text-center"
      >
        <motion.div
          animate={{ rotate: [0, 10, -10, 0] }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-5xl mb-4"
        >
          🎉
        </motion.div>
        <h2 className="text-xl font-bold">Agent Created!</h2>
        <p className="text-sm text-muted-foreground mt-1">{agentName}</p>
      </motion.div>
    </motion.div>
  );
}

export function AgentCreationSheet({
  open,
  onOpenChange,
  suggestedName,
  suggestedGoal,
  suggestedDescription,
  suggestedTools,
  context,
  onAgentCreated,
  onCancel,
}: AgentCreationSheetProps) {
  const createAgent = useCreateAgent();

  // Initialize form data with suggestions
  const [formData, setFormData] = useState<AgentFormData>(() => ({
    ...defaultAgentFormData,
    name: suggestedName || "",
    goal: suggestedGoal || "",
    description: suggestedDescription || "",
    selectedTools: suggestedTools || [],
  }));

  const [showSuccess, setShowSuccess] = useState(false);

  // Reset form when sheet opens (when open prop changes to true)
  useEffect(() => {
    if (open) {
      setFormData({
        ...defaultAgentFormData,
        name: suggestedName || "",
        goal: suggestedGoal || "",
        description: suggestedDescription || "",
        selectedTools: suggestedTools || [],
      });
      setShowSuccess(false);
    }
  }, [open, suggestedName, suggestedGoal, suggestedDescription, suggestedTools]);

  // Handle sheet close events (clicking outside, escape key, etc.)
  const handleOpenChange = (isOpen: boolean) => {
    onOpenChange(isOpen);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const agentId = formData.name
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

    try {
      const createdAgent = await createAgent.mutateAsync(agent);

      // Show success
      setShowSuccess(true);

      // Callback after brief delay
      setTimeout(() => {
        onAgentCreated(createdAgent);
        onOpenChange(false);
      }, 1200);
    } catch (error) {
      console.error("Failed to create agent:", error);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
    onOpenChange(false);
  };

  const isValid = formData.name.trim() && formData.goal.trim();

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent
        className="w-full sm:max-w-[80%] overflow-y-auto"
        side="right"
      >
        <AnimatePresence>
          {showSuccess && <SuccessOverlay agentName={formData.name} />}
        </AnimatePresence>

        <form onSubmit={handleSubmit} className="flex flex-col h-full">
          <SheetHeader className="pb-4">
            <SheetTitle className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500/20 to-blue-500/20">
                <Bot className="h-4 w-4 text-purple-400" />
              </div>
              Create New Agent
            </SheetTitle>
            <SheetDescription>
              {context ? (
                <span>
                  Creating agent for: <strong>{context}</strong>
                </span>
              ) : (
                "Configure your new AI agent with the options below."
              )}
            </SheetDescription>
          </SheetHeader>

          <div className="flex-1 overflow-y-auto py-4">
            <AgentFormFields
              data={formData}
              onChange={setFormData}
              mode="full"
              showAIGeneration={true}
              context={context}
            />
          </div>

          <SheetFooter className="pt-4 border-t">
            <div className="flex w-full gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!isValid || createAgent.isPending}
                className="flex-1"
              >
                {createAgent.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Agent"
                )}
              </Button>
            </div>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
