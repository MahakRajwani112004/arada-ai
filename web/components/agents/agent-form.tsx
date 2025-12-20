"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Loader2,
  Wand2,
  Plus,
  X,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useCreateAgent } from "@/lib/hooks/use-agents";
import { useCatalog, useServers } from "@/lib/hooks/use-mcp";
import { generateAgentConfig } from "@/lib/api/agents";
import type { AgentType, AgentCreate, AgentExample } from "@/types/agent";
import { cn } from "@/lib/utils";

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
          style={{ left: `${piece.x}%`, top: "-10%", backgroundColor: piece.color }}
          initial={{ y: -100, rotate: 0, opacity: 1 }}
          animate={{ y: "100vh", rotate: piece.rotation, opacity: 0 }}
          transition={{ duration: piece.duration, delay: piece.delay, ease: "easeIn" }}
        />
      ))}
    </div>
  );
}

// Auto-detect agent type based on configuration
function detectAgentType(purpose: string, tools: string[]): AgentType {
  const lower = purpose.toLowerCase();
  // If tools selected, use ToolAgent (LLM + tools)
  if (tools.length > 0) return "ToolAgent";
  // Multi-step workflows with retrieval
  if (lower.includes("workflow") || lower.includes("multi-step") || lower.includes("research")) return "FullAgent";
  // Default to LLMAgent for simple chat
  return "LLMAgent";
}

export function AgentForm() {
  const router = useRouter();
  const createAgent = useCreateAgent();
  const { data: catalog } = useCatalog();
  const { data: servers } = useServers();

  // Form fields
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [personality, setPersonality] = useState<string[]>([]);
  const [expertise, setExpertise] = useState<string[]>([]);
  const [communicationStyle, setCommunicationStyle] = useState("");
  const [goal, setGoal] = useState("");
  const [successCriteria, setSuccessCriteria] = useState<string[]>([]);
  const [instructions, setInstructions] = useState("");
  const [rules, setRules] = useState<string[]>([]);
  const [examples, setExamples] = useState<AgentExample[]>([]);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);

  // Temp inputs for list fields
  const [newPersonality, setNewPersonality] = useState("");
  const [newExampleInput, setNewExampleInput] = useState("");
  const [newExampleOutput, setNewExampleOutput] = useState("");

  // Settings
  const [llmProvider, setLlmProvider] = useState<"openai" | "anthropic">("openai");
  const [llmModel, setLlmModel] = useState("gpt-4o-mini");
  const [temperature, setTemperature] = useState(0.7);

  // Handle provider change - reset model to valid option
  const handleProviderChange = (provider: "openai" | "anthropic") => {
    setLlmProvider(provider);
    setLlmModel(provider === "openai" ? "gpt-4o-mini" : "claude-3-sonnet");
  };

  // UI state
  const [isAIFilling, setIsAIFilling] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [showExamples, setShowExamples] = useState(false);

  // Available tools from connected servers
  // Tool ID format must match backend: server_id:tool_name (e.g., srv_xxx:create_event)
  const availableTools = servers?.servers.flatMap((server) => {
    const template = catalog?.servers.find((c) => c.id === server.template);
    return template?.tools.map((tool) => ({
      id: `${server.id}:${tool}`,  // Use server.id not server.template
      name: tool,
      server: server.name,
    })) || [];
  }) || [];

  // Helper to add to list
  const addToList = (
    value: string,
    list: string[],
    setter: (v: string[]) => void,
    clearInput: () => void
  ) => {
    if (value.trim()) {
      setter([...list, value.trim()]);
      clearInput();
    }
  };

  // AI Fill - calls real API
  const handleAIFill = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!name.trim()) return;

    try {
      setIsAIFilling(true);

      const result = await generateAgentConfig({ name: name.trim() });

      // Apply generated config to form
      setDescription(result.description);
      setRoleTitle(result.role.title);
      setPersonality(result.role.personality);
      setExpertise(result.role.expertise);
      setCommunicationStyle(result.role.communication_style);
      setGoal(result.goal.objective);
      setSuccessCriteria(result.goal.success_criteria);
      setInstructions(result.instructions.steps.join("\n"));
      setRules(result.instructions.rules);
      if (result.examples.length > 0) {
        setExamples(result.examples);
      }
    } catch (error) {
      console.error("AI Fill error:", error);
    } finally {
      setIsAIFilling(false);
    }
  };

  // Add example
  const addExample = () => {
    if (newExampleInput.trim() && newExampleOutput.trim()) {
      setExamples([...examples, { input: newExampleInput.trim(), output: newExampleOutput.trim() }]);
      setNewExampleInput("");
      setNewExampleOutput("");
    }
  };

  // Submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const agentId = name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");

    const agent: AgentCreate = {
      id: agentId,
      name,
      description: description || `${name} agent`,
      agent_type: detectAgentType(goal, selectedTools),
      role: {
        title: roleTitle || "AI Assistant",
        expertise: expertise.length > 0 ? expertise : ["general assistance"],
        personality: personality.length > 0 ? personality : ["helpful", "professional"],
        communication_style: communicationStyle || "Clear and concise",
      },
      goal: {
        objective: goal || `Help users with ${name.toLowerCase()} tasks`,
        success_criteria: successCriteria.length > 0 ? successCriteria : ["Task completed"],
        constraints: [],
      },
      instructions: {
        steps: instructions ? instructions.split("\n").filter(Boolean) : ["Listen to user request", "Provide helpful response"],
        rules: rules.length > 0 ? rules : ["Be helpful and accurate"],
        prohibited_actions: [],
        output_format: "Natural language response",
      },
      examples: examples,
      llm_config: {
        provider: llmProvider,
        model: llmModel,
        temperature
      },
      tools: selectedTools.map((id) => ({ tool_id: id })),
      safety: {
        level: "standard",  // lowercase as API expects
        blocked_topics: [],
        blocked_patterns: []
      },
    };

    await createAgent.mutateAsync(agent);
    setShowSuccess(true);
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 4000);
    setTimeout(() => router.push("/agents"), 2000);
  };

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
              <div className="text-5xl mb-3">🎉</div>
              <h2 className="text-xl font-bold">Agent Created!</h2>
              <p className="text-sm text-muted-foreground mt-1">Redirecting...</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Form */}
        <div className="lg:col-span-2 space-y-4">
          {/* Basic Info */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Agent name"
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="roleTitle">Role Title</Label>
              <Input
                id="roleTitle"
                value={roleTitle}
                onChange={(e) => setRoleTitle(e.target.value)}
                placeholder="e.g., Executive Assistant"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What does this agent do?"
            />
          </div>

          {/* Model Selection */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>Model</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAIFill}
                disabled={isAIFilling || !name.trim()}
                className="h-7 text-xs gap-1"
              >
                {isAIFilling ? <Loader2 className="h-3 w-3 animate-spin" /> : <Wand2 className="h-3 w-3" />}
                Generate with AI
              </Button>
            </div>
            <div className="flex gap-2">
              <Select value={llmProvider} onValueChange={(v) => handleProviderChange(v as "openai" | "anthropic")}>
                <SelectTrigger className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="anthropic">Anthropic</SelectItem>
                </SelectContent>
              </Select>
              <Select value={llmModel} onValueChange={setLlmModel}>
                <SelectTrigger className="flex-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {llmProvider === "openai" ? (
                    <>
                      <SelectItem value="gpt-4o">gpt-4o</SelectItem>
                      <SelectItem value="gpt-4o-mini">gpt-4o-mini</SelectItem>
                    </>
                  ) : (
                    <>
                      <SelectItem value="claude-3-opus">claude-3-opus</SelectItem>
                      <SelectItem value="claude-3-sonnet">claude-3-sonnet</SelectItem>
                    </>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator />

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
                    addToList(newPersonality, personality, setPersonality, () => setNewPersonality(""));
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => addToList(newPersonality, personality, setPersonality, () => setNewPersonality(""))}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {personality.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {personality.map((p, i) => (
                  <Badge key={i} variant="secondary" className="gap-1">
                    {p}
                    <button type="button" onClick={() => setPersonality(personality.filter((_, j) => j !== i))}>
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Goal */}
          <div className="space-y-1.5">
            <Label htmlFor="goal">Goal / Objective</Label>
            <Textarea
              id="goal"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="What is the main objective of this agent?"
              rows={2}
              className="resize-none"
            />
          </div>

          {/* Instructions */}
          <div className="space-y-1.5">
            <Label htmlFor="instructions">Instructions (one per line)</Label>
            <Textarea
              id="instructions"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Step-by-step instructions for the agent..."
              rows={3}
              className="resize-none"
            />
          </div>

          <Separator />

          {/* Tools */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label>Tools</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowTools(!showTools)}
                className="h-7 text-xs gap-1"
              >
                {showTools ? "Hide" : "Select"} ({selectedTools.length})
              </Button>
            </div>

            {selectedTools.length > 0 && !showTools && (
              <div className="flex flex-wrap gap-1">
                {selectedTools.map((toolId) => {
                  const tool = availableTools.find((t) => t.id === toolId);
                  return (
                    <Badge key={toolId} variant="outline" className="gap-1">
                      {tool?.name || toolId}
                      <button type="button" onClick={() => setSelectedTools(selectedTools.filter((t) => t !== toolId))}>
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  );
                })}
              </div>
            )}

            <AnimatePresence>
              {showTools && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  {availableTools.length > 0 ? (
                    <div className="grid grid-cols-2 gap-2 pt-2">
                      {availableTools.map((tool) => (
                        <button
                          key={tool.id}
                          type="button"
                          onClick={() => setSelectedTools((prev) =>
                            prev.includes(tool.id)
                              ? prev.filter((t) => t !== tool.id)
                              : [...prev, tool.id]
                          )}
                          className={cn(
                            "text-left p-2 rounded border text-sm transition-colors",
                            selectedTools.includes(tool.id)
                              ? "border-primary bg-primary/10"
                              : "border-border hover:border-primary/50"
                          )}
                        >
                          <div className="font-medium">{tool.name}</div>
                          <div className="text-xs text-muted-foreground">{tool.server}</div>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-4 text-sm text-muted-foreground border border-dashed rounded-lg">
                      No tools available.{" "}
                      <a
                        href="/integrations"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        Connect integrations
                      </a>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

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
                {showExamples ? "Hide" : "Add"} ({examples.length})
              </Button>
            </div>

            {examples.length > 0 && !showExamples && (
              <div className="space-y-2">
                {examples.map((ex, i) => (
                  <div key={i} className="text-xs p-2 border rounded bg-secondary/30">
                    <div><strong>Input:</strong> {ex.input}</div>
                    <div><strong>Output:</strong> {ex.output}</div>
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
                  {examples.map((ex, i) => (
                    <div key={i} className="flex items-start gap-2 p-2 border rounded bg-secondary/30">
                      <div className="flex-1 text-xs">
                        <div><strong>Input:</strong> {ex.input}</div>
                        <div><strong>Output:</strong> {ex.output}</div>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => setExamples(examples.filter((_, j) => j !== i))}
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
                      onChange={(e) => setNewExampleOutput(e.target.value)}
                      placeholder="Expected output..."
                      className="text-sm"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={addExample}
                      disabled={!newExampleInput.trim() || !newExampleOutput.trim()}
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
        </div>

        {/* Right Column - Features & Actions */}
        <div className="space-y-4">
          {/* Settings */}
          <div className="rounded-lg border bg-card p-4 space-y-3">
            <h3 className="font-medium text-sm">Settings</h3>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm">Temperature</Label>
                <span className="text-xs text-muted-foreground">{temperature}</span>
              </div>
              <Input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="cursor-pointer"
              />
            </div>
          </div>

          {/* Guide */}
          <div className="rounded-lg border bg-card p-4">
            <div className="text-center mb-4">
              <Sparkles className="h-6 w-6 mx-auto text-muted-foreground mb-2" />
              <h3 className="font-medium">Quick Start</h3>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex gap-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">1</span>
                <div>
                  <div className="font-medium">Name & Model</div>
                  <div className="text-xs text-muted-foreground">Give your agent a name and select LLM</div>
                </div>
              </div>
              <div className="flex gap-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-secondary text-xs">2</span>
                <div>
                  <div className="font-medium">Define Role & Goal</div>
                  <div className="text-xs text-muted-foreground">Or click &quot;Generate with AI&quot;</div>
                </div>
              </div>
              <div className="flex gap-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-secondary text-xs">3</span>
                <div>
                  <div className="font-medium">Add Tools (Optional)</div>
                  <div className="text-xs text-muted-foreground">Connect MCP tools</div>
                </div>
              </div>
            </div>

            <Button
              type="submit"
              disabled={createAgent.isPending || !name.trim()}
              className="w-full mt-4"
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
        </div>
      </form>
    </>
  );
}
