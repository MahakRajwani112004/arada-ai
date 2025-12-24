"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, ArrowRight, X } from "lucide-react";
import type { AgentSuggestion } from "@/types/agent-suggestion";

// Agent types must match backend: SimpleAgent | LLMAgent | RAGAgent | ToolAgent | FullAgent | RouterAgent
const agentFormSchema = z.object({
  id: z.string().min(1, "Agent ID is required").regex(/^[a-zA-Z][a-zA-Z0-9_-]*$/, "Must start with letter, only letters, numbers, hyphens, underscores"),
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  agent_type: z.enum(["SimpleAgent", "LLMAgent", "RAGAgent", "ToolAgent", "FullAgent", "RouterAgent"]),
  role_title: z.string().min(1, "Role title is required"),
  role_expertise: z.string().optional(),
  goal_objective: z.string().min(1, "Goal is required"),
  instructions: z.string().optional(),
});

type AgentFormData = z.infer<typeof agentFormSchema>;

interface AgentPrefillFormProps {
  suggestion: AgentSuggestion;
  onSubmit: (data: AgentFormData) => void;
  onSkip: () => void;
  isSubmitting?: boolean;
  currentIndex: number;
  totalCount: number;
}

export function AgentPrefillForm({
  suggestion,
  onSubmit,
  onSkip,
  isSubmitting,
  currentIndex,
  totalCount,
}: AgentPrefillFormProps) {
  // AgentSuggestion is now just GeneratedAgentConfig (flat structure)
  const agentConfig = suggestion;

  const form = useForm<AgentFormData>({
    resolver: zodResolver(agentFormSchema),
    defaultValues: {
      id: agentConfig.id || "",
      name: agentConfig.name || "",
      description: agentConfig.description || "",
      agent_type: (agentConfig.agent_type || "LLMAgent") as "SimpleAgent" | "LLMAgent" | "RAGAgent" | "ToolAgent" | "FullAgent" | "RouterAgent",
      role_title: agentConfig.role?.title || "",
      role_expertise: agentConfig.role?.expertise?.join(", ") || "",
      goal_objective: agentConfig.goal?.objective || "",
      instructions: agentConfig.instructions?.steps?.join("\n") || "",
    },
  });

  const handleSubmit = form.handleSubmit((data) => {
    onSubmit(data);
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Create: {agentConfig.id || agentConfig.name}
            </CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              {agentConfig.description || "Configure this agent for the workflow"}
            </p>
          </div>
          <span className="text-sm text-muted-foreground">
            {currentIndex + 1} of {totalCount}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="id">Agent ID</Label>
              <Input
                id="id"
                {...form.register("id")}
                placeholder="my-agent"
              />
              {form.formState.errors.id && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.id.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                {...form.register("name")}
                placeholder="My Agent"
              />
              {form.formState.errors.name && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.name.message}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              {...form.register("description")}
              placeholder="What does this agent do?"
              className="resize-none"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="agent_type">Agent Type</Label>
            <Select
              value={form.watch("agent_type")}
              onValueChange={(value) => form.setValue("agent_type", value as "SimpleAgent" | "LLMAgent" | "RAGAgent" | "ToolAgent" | "FullAgent" | "RouterAgent")}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="SimpleAgent">Simple Agent</SelectItem>
                <SelectItem value="LLMAgent">LLM Agent</SelectItem>
                <SelectItem value="RAGAgent">RAG Agent</SelectItem>
                <SelectItem value="ToolAgent">Tool Agent</SelectItem>
                <SelectItem value="FullAgent">Full Agent</SelectItem>
                <SelectItem value="RouterAgent">Router Agent</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="role_title">Role Title</Label>
              <Input
                id="role_title"
                {...form.register("role_title")}
                placeholder="e.g., Data Analyst"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="role_expertise">Expertise (comma-separated)</Label>
              <Input
                id="role_expertise"
                {...form.register("role_expertise")}
                placeholder="e.g., analysis, reporting"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="goal_objective">Goal</Label>
            <Textarea
              id="goal_objective"
              {...form.register("goal_objective")}
              placeholder="What should this agent accomplish?"
              className="resize-none"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="instructions">Instructions (one per line)</Label>
            <Textarea
              id="instructions"
              {...form.register("instructions")}
              placeholder="Step 1&#10;Step 2&#10;Step 3"
              className="min-h-[80px] resize-none"
            />
          </div>

          {/* Agent Type Info */}
          {agentConfig.agent_type && (
            <div className="rounded-md border border-blue-500/30 bg-blue-500/5 p-3">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-blue-400 mt-0.5 shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-blue-400">Agent Type: {agentConfig.agent_type}</p>
                  <p className="text-muted-foreground">
                    Review and adjust the configuration as needed before creating.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between pt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={onSkip}
              className="gap-2"
            >
              <X className="h-4 w-4" />
              Skip Agent
            </Button>
            <Button type="submit" disabled={isSubmitting} className="gap-2">
              {isSubmitting ? "Creating..." : "Create Agent"}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
