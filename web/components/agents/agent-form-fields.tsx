"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Loader2,
  Wand2,
  Plus,
  X,
  Trash2,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ExpandableTextarea } from "@/components/ui/expandable-textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useCatalog, useServers } from "@/lib/hooks/use-mcp";
import { useAgents } from "@/lib/hooks/use-agents";
import { generateAgentConfig } from "@/lib/api/agents";
import type { AgentType, AgentExample, KnowledgeBaseConfig, RouterConfig, OrchestratorConfig } from "@/types/agent";
import { ToolSelectorSheet } from "./tool-selector-sheet";
import { SelectedToolsDisplay } from "./selected-tools-display";
import { KBSelector } from "./kb-selector";
import { RoutingTableBuilder } from "./routing-table-builder";
import { OrchestratorConfigBuilder } from "./orchestrator-config-builder";

export interface AgentFormData {
  name: string;
  description: string;
  roleTitle: string;
  personality: string[];
  expertise: string[];
  communicationStyle: string;
  goal: string;
  successCriteria: string[];
  instructions: string;
  rules: string[];
  examples: AgentExample[];
  selectedTools: string[];
  knowledgeBase?: KnowledgeBaseConfig;
  llmProvider: "openai" | "anthropic";
  llmModel: string;
  temperature: number;
  // Advanced agent types
  agentType?: AgentType;
  routerConfig?: RouterConfig;
  orchestratorConfig?: OrchestratorConfig;
}

export const defaultAgentFormData: AgentFormData = {
  name: "",
  description: "",
  roleTitle: "",
  personality: [],
  expertise: [],
  communicationStyle: "",
  goal: "",
  successCriteria: [],
  instructions: "",
  rules: [],
  examples: [],
  selectedTools: [],
  knowledgeBase: undefined,
  llmProvider: "openai",
  llmModel: "gpt-4o",
  temperature: 0.7,
  agentType: undefined,
  routerConfig: undefined,
  orchestratorConfig: undefined,
};

// Default configs for advanced agent types
export const defaultRouterConfig: RouterConfig = {
  routing_table: {},
  confidence_threshold: 0.7,
};

export const defaultOrchestratorConfig: OrchestratorConfig = {
  mode: "llm_driven",
  available_agents: [],
  workflow_definition: null,
  default_aggregation: "all",
  max_parallel: 5,
  max_depth: 3,
  allow_self_reference: false,
};

interface AgentFormFieldsProps {
  data: AgentFormData;
  onChange: (data: AgentFormData) => void;
  mode?: "full" | "compact";
  showAIGeneration?: boolean;
  context?: string; // Context for AI generation (e.g., "For workflow step: Classify Tickets")
}

// Auto-detect agent type based on configuration
export function detectAgentType(
  purpose: string,
  tools: string[],
  hasKnowledgeBase: boolean
): AgentType {
  const lower = purpose.toLowerCase();
  if (tools.length > 0 && hasKnowledgeBase) return "FullAgent";
  if (tools.length > 0) return "ToolAgent";
  if (hasKnowledgeBase) return "RAGAgent";
  if (
    lower.includes("workflow") ||
    lower.includes("multi-step") ||
    lower.includes("research")
  )
    return "FullAgent";
  return "LLMAgent";
}

export function AgentFormFields({
  data,
  onChange,
  mode = "full",
  showAIGeneration = true,
  context,
}: AgentFormFieldsProps) {
  const { data: catalog } = useCatalog();
  const { data: servers } = useServers();
  const { data: agentsData } = useAgents();

  // UI state
  const [isAIFilling, setIsAIFilling] = useState(false);
  const [showAIModal, setShowAIModal] = useState(false);
  const [aiPurpose, setAIPurpose] = useState("");
  const [showExamples, setShowExamples] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Temp inputs for list fields
  const [newPersonality, setNewPersonality] = useState("");
  const [newExampleInput, setNewExampleInput] = useState("");
  const [newExampleOutput, setNewExampleOutput] = useState("");

  // Update helpers
  const updateField = <K extends keyof AgentFormData>(
    field: K,
    value: AgentFormData[K]
  ) => {
    onChange({ ...data, [field]: value });
  };

  const handleProviderChange = (provider: "openai" | "anthropic") => {
    onChange({
      ...data,
      llmProvider: provider,
      llmModel: provider === "openai" ? "gpt-4o" : "claude-3-sonnet",
    });
  };

  const addToList = (
    field: keyof AgentFormData,
    value: string,
    clearInput: () => void
  ) => {
    if (value.trim()) {
      const currentList = data[field] as string[];
      updateField(field, [...currentList, value.trim()]);
      clearInput();
    }
  };

  const removeFromList = (field: keyof AgentFormData, index: number) => {
    const currentList = data[field] as string[];
    updateField(
      field,
      currentList.filter((_, i) => i !== index)
    );
  };

  // AI Fill - calls real API
  const handleAIFill = async () => {
    if (!data.name.trim()) return;

    try {
      setIsAIFilling(true);
      setShowAIModal(false);

      const result = await generateAgentConfig({
        name: data.name.trim(),
        context: aiPurpose.trim() || context || undefined,
      });

      // Apply generated config to form
      onChange({
        ...data,
        description: result.description,
        roleTitle: result.role.title,
        personality: result.role.personality,
        expertise: result.role.expertise,
        communicationStyle: result.role.communication_style,
        goal: result.goal.objective,
        successCriteria: result.goal.success_criteria,
        instructions: result.instructions.steps.join("\n"),
        rules: result.instructions.rules,
        examples: result.examples.length > 0 ? result.examples : data.examples,
      });
    } catch (error) {
      console.error("AI Fill error:", error);
    } finally {
      setIsAIFilling(false);
      setAIPurpose("");
    }
  };

  // Add example
  const addExample = () => {
    if (newExampleInput.trim() && newExampleOutput.trim()) {
      updateField("examples", [
        ...data.examples,
        { input: newExampleInput.trim(), output: newExampleOutput.trim() },
      ]);
      setNewExampleInput("");
      setNewExampleOutput("");
    }
  };

  return (
    <>
      {/* AI Generation Modal */}
      <Dialog open={showAIModal} onOpenChange={setShowAIModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Wand2 className="h-5 w-5" />
              Generate Agent Config
            </DialogTitle>
            <DialogDescription>
              Describe what you want{" "}
              <strong>{data.name || "this agent"}</strong> to do. The more
              detail you provide, the better the generated config.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-4">
            <Textarea
              value={aiPurpose}
              onChange={(e) => setAIPurpose(e.target.value)}
              placeholder="e.g., Help manage my work calendar, send meeting reminders, handle scheduling conflicts, and summarize upcoming events..."
              rows={4}
              className="resize-none"
              autoFocus
            />
            <p className="text-xs text-muted-foreground">
              Tip: Include specific tasks, tools it should use, and any
              constraints.
            </p>
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setShowAIModal(false);
                setAIPurpose("");
              }}
            >
              Cancel
            </Button>
            <Button type="button" onClick={handleAIFill} disabled={isAIFilling}>
              {isAIFilling ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="space-y-4">
        {/* AI Quick Generate - shown at top */}
        {showAIGeneration && (
          <div className="rounded-lg border border-dashed border-purple-500/50 bg-purple-500/5 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-purple-500/20 to-blue-500/20">
                <Sparkles className="h-5 w-5 text-purple-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium">Generate with AI</h3>
                <p className="text-xs text-muted-foreground">
                  Describe what you need and AI will configure the agent
                </p>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowAIModal(true)}
                disabled={isAIFilling || !data.name.trim()}
                className="gap-1"
              >
                {isAIFilling ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Wand2 className="h-3 w-3" />
                )}
                {isAIFilling ? "Generating..." : "Generate"}
              </Button>
            </div>
          </div>
        )}

        {/* Essential Fields */}
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={data.name}
                onChange={(e) => updateField("name", e.target.value)}
                placeholder="Agent name"
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="agentType">Agent Type</Label>
              <Select
                value={data.agentType || "auto"}
                onValueChange={(v) => {
                  const newType = v === "auto" ? undefined : v as AgentType;
                  const updates: Partial<AgentFormData> = { agentType: newType };

                  // Initialize configs when type is selected
                  if (v === "RouterAgent" && !data.routerConfig) {
                    updates.routerConfig = defaultRouterConfig;
                  }
                  if (v === "OrchestratorAgent" && !data.orchestratorConfig) {
                    updates.orchestratorConfig = defaultOrchestratorConfig;
                  }

                  onChange({ ...data, ...updates });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Auto-detect" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Auto-detect</SelectItem>
                  <SelectItem value="LLMAgent">LLM Agent</SelectItem>
                  <SelectItem value="ToolAgent">Tool Agent</SelectItem>
                  <SelectItem value="RAGAgent">RAG Agent</SelectItem>
                  <SelectItem value="FullAgent">Full Agent</SelectItem>
                  <SelectItem value="RouterAgent">Router Agent</SelectItem>
                  <SelectItem value="OrchestratorAgent">Orchestrator Agent</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Role Title - moved to separate row */}
          <div className="space-y-1.5">
            <Label htmlFor="roleTitle">Role Title</Label>
            <Input
              id="roleTitle"
              value={data.roleTitle}
              onChange={(e) => updateField("roleTitle", e.target.value)}
              placeholder="e.g., Executive Assistant"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="description">Description</Label>
            <ExpandableTextarea
              id="description"
              value={data.description}
              onChange={(val) => updateField("description", val)}
              placeholder="What does this agent do?"
              label="Description"
              rows={1}
            />
          </div>

          {/* Goal */}
          <div className="space-y-1.5">
            <Label htmlFor="goal">Goal / Objective *</Label>
            <ExpandableTextarea
              id="goal"
              value={data.goal}
              onChange={(val) => updateField("goal", val)}
              placeholder="What is the main objective of this agent?"
              label="Goal / Objective"
              rows={2}
            />
          </div>

          {/* Instructions */}
          <div className="space-y-1.5">
            <Label htmlFor="instructions">Instructions (one per line)</Label>
            <ExpandableTextarea
              id="instructions"
              value={data.instructions}
              onChange={(val) => updateField("instructions", val)}
              placeholder="Step-by-step instructions for the agent..."
              label="Instructions"
              rows={3}
            />
          </div>

          {/* Model Selection */}
          <div className="space-y-1.5">
            <Label>Model</Label>
            <div className="flex gap-2">
              <Select
                value={data.llmProvider}
                onValueChange={(v) =>
                  handleProviderChange(v as "openai" | "anthropic")
                }
              >
                <SelectTrigger className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="anthropic">Anthropic</SelectItem>
                </SelectContent>
              </Select>
              <Select
                value={data.llmModel}
                onValueChange={(v) => updateField("llmModel", v)}
              >
                <SelectTrigger className="flex-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {data.llmProvider === "openai" ? (
                    <>
                      <SelectItem value="gpt-4o">gpt-4o</SelectItem>
                      <SelectItem value="gpt-4o-mini">gpt-4o-mini</SelectItem>
                    </>
                  ) : (
                    <>
                      <SelectItem value="claude-3-opus">
                        claude-3-opus
                      </SelectItem>
                      <SelectItem value="claude-3-sonnet">
                        claude-3-sonnet
                      </SelectItem>
                    </>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Tools */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Tools</Label>
              <ToolSelectorSheet
                selectedTools={data.selectedTools}
                onToolsChange={(tools) => updateField("selectedTools", tools)}
              />
            </div>
            <SelectedToolsDisplay
              selectedTools={data.selectedTools}
              servers={servers?.servers}
              catalog={catalog?.servers}
              onRemove={(toolId) =>
                updateField(
                  "selectedTools",
                  data.selectedTools.filter((t) => t !== toolId)
                )
              }
            />
          </div>

          {/* RouterAgent Configuration */}
          {data.agentType === "RouterAgent" && data.routerConfig && (
            <>
              <Separator />
              <RoutingTableBuilder
                config={data.routerConfig}
                onChange={(config) => updateField("routerConfig", config)}
                agents={agentsData?.agents || []}
              />
            </>
          )}

          {/* OrchestratorAgent Configuration */}
          {data.agentType === "OrchestratorAgent" && data.orchestratorConfig && (
            <>
              <Separator />
              <OrchestratorConfigBuilder
                config={data.orchestratorConfig}
                onChange={(config) => updateField("orchestratorConfig", config)}
                agents={agentsData?.agents || []}
              />
            </>
          )}
        </div>

        {/* Advanced Options - Collapsible */}
        {mode === "full" && (
          <>
            <Separator />

            <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
              <CollapsibleTrigger asChild>
                <Button
                  variant="ghost"
                  type="button"
                  className="w-full justify-between"
                >
                  <span className="text-sm font-medium">Advanced Options</span>
                  {showAdvanced ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-4 pt-4">
                {/* Temperature */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Temperature</Label>
                    <span className="text-xs text-muted-foreground">
                      {data.temperature}
                    </span>
                  </div>
                  <Input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={data.temperature}
                    onChange={(e) =>
                      updateField("temperature", parseFloat(e.target.value))
                    }
                    className="cursor-pointer"
                  />
                </div>

                {/* Personality (array) */}
                <div className="space-y-1.5">
                  <Label>Personality Traits</Label>
                  <div className="flex gap-2">
                    <Input
                      value={newPersonality}
                      onChange={(e) => setNewPersonality(e.target.value)}
                      placeholder="e.g., Professional, Friendly"
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addToList("personality", newPersonality, () =>
                            setNewPersonality("")
                          );
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() =>
                        addToList("personality", newPersonality, () =>
                          setNewPersonality("")
                        )
                      }
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  {data.personality.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {data.personality.map((p, i) => (
                        <Badge key={i} variant="secondary" className="gap-1">
                          {p}
                          <button
                            type="button"
                            onClick={() => removeFromList("personality", i)}
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>

                {/* Knowledge Base */}
                <KBSelector
                  value={data.knowledgeBase}
                  onChange={(kb) => updateField("knowledgeBase", kb)}
                />

                {/* Examples */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label>Examples</Label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setShowExamples(!showExamples)}
                      className="h-7 text-xs gap-1"
                    >
                      {showExamples ? "Hide" : "Add"} ({data.examples.length})
                    </Button>
                  </div>

                  {data.examples.length > 0 && !showExamples && (
                    <div className="space-y-2">
                      {data.examples.map((ex, i) => (
                        <div
                          key={i}
                          className="text-xs p-2 border rounded bg-secondary/30"
                        >
                          <div>
                            <strong>Input:</strong> {ex.input}
                          </div>
                          <div>
                            <strong>Output:</strong> {ex.output}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <AnimatePresence>
                    {showExamples && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden space-y-2 pt-2"
                      >
                        {data.examples.map((ex, i) => (
                          <div
                            key={i}
                            className="flex items-start gap-2 p-2 border rounded bg-secondary/30"
                          >
                            <div className="flex-1 text-xs">
                              <div>
                                <strong>Input:</strong> {ex.input}
                              </div>
                              <div>
                                <strong>Output:</strong> {ex.output}
                              </div>
                            </div>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={() => {
                                updateField(
                                  "examples",
                                  data.examples.filter((_, j) => j !== i)
                                );
                              }}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        ))}

                        <div className="space-y-2 p-3 border border-dashed rounded">
                          <Input
                            value={newExampleInput}
                            onChange={(e) => setNewExampleInput(e.target.value)}
                            placeholder="Example input..."
                            className="text-sm"
                          />
                          <Input
                            value={newExampleOutput}
                            onChange={(e) =>
                              setNewExampleOutput(e.target.value)
                            }
                            placeholder="Expected output..."
                            className="text-sm"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={addExample}
                            disabled={
                              !newExampleInput.trim() ||
                              !newExampleOutput.trim()
                            }
                            className="w-full"
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            Add Example
                          </Button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </>
        )}
      </div>
    </>
  );
}
