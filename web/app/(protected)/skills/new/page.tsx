"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft, Sparkles, PenTool, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { SkillBuilderForm } from "@/components/skills/create";
import { useGenerateSkill } from "@/lib/hooks/use-skills";
import type { SkillDefinition, SkillCategory } from "@/types/skill";

function NewSkillContent() {
  const searchParams = useSearchParams();
  const startWithAI = searchParams.get("ai") === "true";

  const [mode, setMode] = useState<"manual" | "ai">(startWithAI ? "ai" : "manual");
  const [aiPrompt, setAiPrompt] = useState("");
  const [generatedSkill, setGeneratedSkill] = useState<{
    name: string;
    description: string;
    category: SkillCategory;
    tags: string[];
    definition: SkillDefinition;
  } | null>(null);

  const generateSkill = useGenerateSkill();

  const handleGenerate = () => {
    if (!aiPrompt.trim()) return;

    generateSkill.mutate(
      { prompt: aiPrompt, include_examples: true, include_terminology: true },
      {
        onSuccess: (response) => {
          setGeneratedSkill({
            name: response.skill.metadata.name,
            description: `AI-generated skill based on: ${aiPrompt.substring(0, 100)}`,
            category: response.skill.metadata.category,
            tags: response.skill.metadata.tags,
            definition: response.skill,
          });
        },
      }
    );
  };

  return (
    <>
      <Header />
      <PageContainer>
        {/* Back button */}
        <div className="mb-6">
          <Button variant="ghost" size="sm" asChild className="gap-2">
            <Link href="/skills">
              <ArrowLeft className="h-4 w-4" />
              Back to Skills
            </Link>
          </Button>
        </div>

        {/* Title */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold">Create New Skill</h1>
          <p className="mt-1 text-muted-foreground">
            Define domain expertise and reasoning patterns for your agents
          </p>
        </div>

        {/* Mode Selection */}
        {!generatedSkill && (
          <Tabs value={mode} onValueChange={(v) => setMode(v as "manual" | "ai")} className="mb-8">
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="manual" className="gap-2">
                <PenTool className="h-4 w-4" />
                Create Manually
              </TabsTrigger>
              <TabsTrigger value="ai" className="gap-2">
                <Sparkles className="h-4 w-4" />
                Generate with AI
              </TabsTrigger>
            </TabsList>

            <TabsContent value="ai" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-amber-400" />
                    AI Skill Generator
                  </CardTitle>
                  <CardDescription>
                    Describe what expertise you need and AI will create a skill structure for you
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Textarea
                    placeholder="Example: I need a skill for analyzing legal contracts and identifying risk clauses. The agent should understand common contract terminology, be able to assess indemnification clauses, and follow a structured risk evaluation process..."
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    rows={6}
                    className="resize-none"
                  />
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-muted-foreground">
                      Be specific about the domain, terminology, and reasoning patterns needed
                    </p>
                    <Button
                      onClick={handleGenerate}
                      disabled={!aiPrompt.trim() || generateSkill.isPending}
                      className="gap-2"
                    >
                      {generateSkill.isPending ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-4 w-4" />
                          Generate Skill
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {generateSkill.isError && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive"
                >
                  Failed to generate skill. Please try again with a different description.
                </motion.div>
              )}
            </TabsContent>

            <TabsContent value="manual" className="mt-6">
              <SkillBuilderForm mode="create" />
            </TabsContent>
          </Tabs>
        )}

        {/* Generated Skill Preview & Edit */}
        {generatedSkill && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Generated Skill</h2>
                <p className="text-sm text-muted-foreground">
                  Review and customize the AI-generated skill below
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  setGeneratedSkill(null);
                  setAiPrompt("");
                }}
              >
                Start Over
              </Button>
            </div>

            <SkillBuilderForm
              mode="create"
              initialData={generatedSkill}
            />
          </motion.div>
        )}
      </PageContainer>
    </>
  );
}

export default function NewSkillPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <NewSkillContent />
    </Suspense>
  );
}
