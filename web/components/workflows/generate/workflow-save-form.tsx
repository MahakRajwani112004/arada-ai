"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Check, AlertTriangle, Rocket, ArrowRight } from "lucide-react";
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
import type { GenerateWorkflowResponse } from "@/types/workflow";

const categories = [
  { value: "customer-support", label: "Customer Support" },
  { value: "data-processing", label: "Data Processing" },
  { value: "content-creation", label: "Content Creation" },
  { value: "sales-automation", label: "Sales Automation" },
  { value: "hr-onboarding", label: "HR & Onboarding" },
  { value: "ai-generated", label: "AI Generated" },
  { value: "general", label: "General" },
];

const formSchema = z.object({
  name: z.string().min(1, "Name is required").max(200),
  description: z.string().max(1000).optional(),
  category: z.string().min(1, "Category is required"),
});

type FormData = z.infer<typeof formSchema>;

interface WorkflowSaveFormProps {
  response: GenerateWorkflowResponse;
  createdAgentIds: string[];
  skippedAgentIds: string[];
  onSubmit: (data: FormData) => void;
  isSubmitting?: boolean;
}

export function WorkflowSaveForm({
  response,
  createdAgentIds,
  skippedAgentIds,
  onSubmit,
  isSubmitting,
}: WorkflowSaveFormProps) {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: response.workflow.name || "",
      description: response.workflow.description || "",
      category: "ai-generated",
    },
  });

  const handleSubmit = form.handleSubmit(onSubmit);

  const agentsToCreate = response.agents_to_create ?? [];
  const existingAgentsUsed = response.existing_agents_used ?? [];
  const mcpsSuggested = response.mcps_suggested ?? [];
  const workflowSteps = response.workflow?.steps ?? [];

  const totalAgentsNeeded = agentsToCreate.length;
  const hasBlockedSteps = skippedAgentIds.length > 0;
  const allAgentsCreated = createdAgentIds.length === totalAgentsNeeded && totalAgentsNeeded > 0;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-xl font-semibold">Save Your Workflow</h2>
        <p className="text-muted-foreground">
          {hasBlockedSteps
            ? "Your workflow will be saved with some blocked steps."
            : "All agents are ready! Save your workflow."}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Workflow Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Workflow Name</Label>
              <Input
                id="name"
                {...form.register("name")}
                placeholder="My Awesome Workflow"
              />
              {form.formState.errors.name && (
                <p className="text-xs text-destructive">
                  {form.formState.errors.name.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                {...form.register("description")}
                placeholder="What does this workflow do?"
                className="resize-none"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select
                value={form.watch("category")}
                onValueChange={(value) => form.setValue("category", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Summary */}
            <div className="rounded-lg border border-border bg-secondary/30 p-4 space-y-3">
              <h4 className="font-medium">Summary</h4>
              <div className="grid gap-2 text-sm">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-400" />
                  <span>{workflowSteps.length} steps configured</span>
                </div>

                {existingAgentsUsed.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-400" />
                    <span>{existingAgentsUsed.length} existing agent{existingAgentsUsed.length > 1 ? "s" : ""} reused</span>
                  </div>
                )}

                {createdAgentIds.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-400" />
                    <span>{createdAgentIds.length} new agent{createdAgentIds.length > 1 ? "s" : ""} created</span>
                  </div>
                )}

                {skippedAgentIds.length > 0 && (
                  <div className="flex items-center gap-2 text-amber-400">
                    <AlertTriangle className="h-4 w-4" />
                    <span>{skippedAgentIds.length} agent{skippedAgentIds.length > 1 ? "s" : ""} skipped (workflow will be blocked)</span>
                  </div>
                )}

                {mcpsSuggested.length > 0 && (
                  <div className="flex items-center gap-2 text-blue-400">
                    <span className="ml-6">{mcpsSuggested.length} MCP suggestion{mcpsSuggested.length > 1 ? "s" : ""}</span>
                  </div>
                )}
              </div>
            </div>

            <Button type="submit" disabled={isSubmitting} className="w-full gap-2">
              {isSubmitting ? (
                "Saving..."
              ) : (
                <>
                  <Rocket className="h-4 w-4" />
                  {hasBlockedSteps ? "Save Workflow (Incomplete)" : "Save & Go to Workflow"}
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Status message */}
      {allAgentsCreated && !hasBlockedSteps && (
        <div className="rounded-md bg-green-500/10 p-4 text-center text-green-400">
          <Check className="inline-block h-5 w-5 mr-2" />
          Workflow is ready to run after saving!
        </div>
      )}

      {hasBlockedSteps && (
        <div className="rounded-md bg-amber-500/10 p-4 text-amber-400">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">Workflow will be saved with blocked steps</p>
              <p className="text-sm text-amber-400/80 mt-1">
                You can create the missing agents later from the workflow detail page.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
