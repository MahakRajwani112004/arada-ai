"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { format } from "date-fns";
import {
  ArrowLeft,
  Edit,
  Trash2,
  Globe,
  GlobeLock,
  Copy,
  MoreVertical,
  Lightbulb,
  Brain,
  FileText,
  Code,
  Settings,
  Sparkles,
  Play,
  Clock,
  Star,
  History,
  ExternalLink,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  useSkill,
  useDeleteSkill,
  useTestSkill,
  usePublishSkill,
  useSkillStats,
} from "@/lib/hooks/use-skills";
import {
  SKILL_CATEGORY_LABELS,
  SKILL_STATUS_LABELS,
  type SkillCategory,
} from "@/types/skill";

const categoryColors: Record<SkillCategory, string> = {
  domain_expertise: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  document_generation: "bg-green-500/10 text-green-400 border-green-500/20",
  data_analysis: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  communication: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  research: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  coding: "bg-violet-500/10 text-violet-400 border-violet-500/20",
  custom: "bg-gray-500/10 text-gray-400 border-gray-500/20",
};

const statusColors: Record<string, string> = {
  draft: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  published: "bg-green-500/10 text-green-400 border-green-500/20",
  archived: "bg-gray-500/10 text-gray-400 border-gray-500/20",
};

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-16 w-16 rounded-xl" />
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <Skeleton className="h-24 w-full" />
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    </div>
  );
}

export default function SkillDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [testInput, setTestInput] = useState("");
  const [testResult, setTestResult] = useState<string | null>(null);

  const { data: skill, isLoading, error } = useSkill(id);
  const { data: stats } = useSkillStats(id);
  const deleteSkill = useDeleteSkill();
  const testSkill = useTestSkill();
  const publishSkill = usePublishSkill();

  const handleDelete = () => {
    if (confirm("Are you sure you want to delete this skill?")) {
      deleteSkill.mutate(id, {
        onSuccess: () => router.push("/skills"),
      });
    }
  };

  const handleTest = () => {
    if (!testInput.trim()) return;
    testSkill.mutate(
      { skillId: id, request: { input: testInput } },
      {
        onSuccess: (result) => {
          setTestResult(result.enhanced_prompt);
        },
      }
    );
  };

  const handlePublish = (makePublic: boolean) => {
    publishSkill.mutate({
      skillId: id,
      request: { make_public: makePublic },
    });
  };

  if (isLoading) {
    return (
      <>
        <Header />
        <PageContainer>
          <LoadingSkeleton />
        </PageContainer>
      </>
    );
  }

  if (error || !skill) {
    return (
      <>
        <Header />
        <PageContainer>
          <div className="flex flex-col items-center justify-center py-16">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-destructive">
                Skill not found
              </h2>
              <p className="mt-2 text-muted-foreground">
                The skill you&apos;re looking for doesn&apos;t exist or you don&apos;t have
                access.
              </p>
              <Button asChild className="mt-4">
                <Link href="/skills">Back to Skills</Link>
              </Button>
            </div>
          </div>
        </PageContainer>
      </>
    );
  }

  const def = skill.definition;

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

        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20"
            >
              <Lightbulb className="h-8 w-8 text-amber-400" />
            </motion.div>
            <div>
              <h1 className="text-2xl font-bold">{skill.name}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <Badge
                  variant="outline"
                  className={categoryColors[skill.category]}
                >
                  {SKILL_CATEGORY_LABELS[skill.category]}
                </Badge>
                <Badge variant="outline" className={statusColors[skill.status]}>
                  {SKILL_STATUS_LABELS[skill.status]}
                </Badge>
                {skill.is_public ? (
                  <Badge variant="outline" className="gap-1">
                    <Globe className="h-3 w-3" />
                    Public
                  </Badge>
                ) : (
                  <Badge variant="outline" className="gap-1">
                    <GlobeLock className="h-3 w-3" />
                    Private
                  </Badge>
                )}
                <Badge variant="secondary">v{skill.version}</Badge>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" asChild className="gap-2">
              <Link href={`/skills/${id}/edit`}>
                <Edit className="h-4 w-4" />
                Edit
              </Link>
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => navigator.clipboard.writeText(id)}>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy ID
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href={`/skills/${id}/versions`}>
                    <History className="mr-2 h-4 w-4" />
                    View History
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {!skill.is_public && skill.status === "published" && (
                  <DropdownMenuItem onClick={() => handlePublish(true)}>
                    <Globe className="mr-2 h-4 w-4" />
                    Publish to Marketplace
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={handleDelete}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Description */}
        <p className="mt-4 text-muted-foreground">{skill.description}</p>

        {/* Tags */}
        {skill.tags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {skill.tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* Stats Row */}
        <div className="mt-6 grid gap-4 sm:grid-cols-4">
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                <Play className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {stats?.total_executions ?? 0}
                </p>
                <p className="text-xs text-muted-foreground">Executions</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                <Sparkles className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {stats?.success_rate
                    ? `${(stats.success_rate * 100).toFixed(0)}%`
                    : "—"}
                </p>
                <p className="text-xs text-muted-foreground">Success Rate</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
                <Clock className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {stats?.avg_duration_ms
                    ? `${stats.avg_duration_ms.toFixed(0)}ms`
                    : "—"}
                </p>
                <p className="text-xs text-muted-foreground">Avg Duration</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-yellow-500/10">
                <Star className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {skill.rating_avg?.toFixed(1) ?? "—"}
                </p>
                <p className="text-xs text-muted-foreground">
                  Rating ({skill.rating_count})
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Separator className="my-8" />

        {/* Main Content Accordion */}
        <Accordion
          type="multiple"
          defaultValue={["domain", "prompts", "test"]}
          className="space-y-4"
        >
          {/* Domain Knowledge Section */}
          <AccordionItem value="domain" className="rounded-lg border">
            <AccordionTrigger className="px-4 hover:no-underline">
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-blue-400" />
                <span className="font-semibold">Domain Knowledge</span>
                <Badge variant="secondary" className="ml-2">
                  {def.capability.expertise.terminology.length} terms
                </Badge>
                <Badge variant="secondary">
                  {def.capability.expertise.reasoning_patterns.length} patterns
                </Badge>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              <div className="space-y-6">
                {/* Domain */}
                {def.capability.expertise.domain && (
                  <div>
                    <h4 className="mb-2 text-sm font-medium text-muted-foreground">
                      Domain
                    </h4>
                    <p className="text-sm">{def.capability.expertise.domain}</p>
                  </div>
                )}

                {/* Terminology */}
                {def.capability.expertise.terminology.length > 0 && (
                  <div>
                    <h4 className="mb-3 text-sm font-medium text-muted-foreground">
                      Terminology
                    </h4>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {def.capability.expertise.terminology.map((term) => (
                        <Card key={term.id} className="p-3">
                          <p className="font-medium">{term.term}</p>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {term.definition}
                          </p>
                          {term.aliases && term.aliases.length > 0 && (
                            <p className="mt-2 text-xs text-muted-foreground">
                              Also known as: {term.aliases.join(", ")}
                            </p>
                          )}
                        </Card>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reasoning Patterns */}
                {def.capability.expertise.reasoning_patterns.length > 0 && (
                  <div>
                    <h4 className="mb-3 text-sm font-medium text-muted-foreground">
                      Reasoning Patterns
                    </h4>
                    <div className="space-y-3">
                      {def.capability.expertise.reasoning_patterns.map(
                        (pattern) => (
                          <Card key={pattern.id} className="p-3">
                            <p className="font-medium">{pattern.name}</p>
                            {pattern.description && (
                              <p className="mt-1 text-sm text-muted-foreground">
                                {pattern.description}
                              </p>
                            )}
                            <ol className="mt-3 space-y-1">
                              {pattern.steps.map((step, idx) => (
                                <li
                                  key={idx}
                                  className="flex items-start gap-2 text-sm"
                                >
                                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                                    {idx + 1}
                                  </span>
                                  {step}
                                </li>
                              ))}
                            </ol>
                          </Card>
                        )
                      )}
                    </div>
                  </div>
                )}

                {/* Examples */}
                {def.capability.expertise.examples.length > 0 && (
                  <div>
                    <h4 className="mb-3 text-sm font-medium text-muted-foreground">
                      Examples
                    </h4>
                    <div className="space-y-3">
                      {def.capability.expertise.examples.map((example) => (
                        <Card key={example.id} className="p-3">
                          {example.context && (
                            <p className="mb-2 text-xs text-muted-foreground">
                              Context: {example.context}
                            </p>
                          )}
                          <div className="space-y-2">
                            <div>
                              <p className="text-xs font-medium text-muted-foreground">
                                Input
                              </p>
                              <p className="mt-1 rounded bg-muted p-2 text-sm">
                                {example.input}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs font-medium text-muted-foreground">
                                Output
                              </p>
                              <p className="mt-1 rounded bg-muted p-2 text-sm">
                                {example.output}
                              </p>
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}

                {def.capability.expertise.terminology.length === 0 &&
                  def.capability.expertise.reasoning_patterns.length === 0 &&
                  def.capability.expertise.examples.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      No domain knowledge defined yet.
                    </p>
                  )}
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Resources Section */}
          <AccordionItem value="resources" className="rounded-lg border">
            <AccordionTrigger className="px-4 hover:no-underline">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-green-400" />
                <span className="font-semibold">Resources</span>
                <Badge variant="secondary" className="ml-2">
                  {def.resources.files.length} files
                </Badge>
                <Badge variant="secondary">
                  {def.resources.code_snippets.length} snippets
                </Badge>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              <div className="space-y-6">
                {/* Files */}
                {def.resources.files.length > 0 && (
                  <div>
                    <h4 className="mb-3 text-sm font-medium text-muted-foreground">
                      Files
                    </h4>
                    <div className="space-y-2">
                      {def.resources.files.map((file) => (
                        <Card
                          key={file.id}
                          className="flex items-center justify-between p-3"
                        >
                          <div className="flex items-center gap-3">
                            <FileText className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <p className="font-medium">{file.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {file.file_type} •{" "}
                                {(file.size_bytes / 1024).toFixed(1)} KB
                              </p>
                            </div>
                          </div>
                          <Button variant="ghost" size="sm" asChild>
                            <a
                              href={file.storage_url}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          </Button>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}

                {/* Code Snippets */}
                {def.resources.code_snippets.length > 0 && (
                  <div>
                    <h4 className="mb-3 text-sm font-medium text-muted-foreground">
                      Code Snippets
                    </h4>
                    <div className="space-y-3">
                      {def.resources.code_snippets.map((snippet) => (
                        <Card key={snippet.id} className="overflow-hidden">
                          <div className="flex items-center justify-between border-b bg-muted/30 px-3 py-2">
                            <div className="flex items-center gap-2">
                              <Code className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm font-medium">
                                {snippet.language}
                              </span>
                            </div>
                            {snippet.description && (
                              <span className="text-xs text-muted-foreground">
                                {snippet.description}
                              </span>
                            )}
                          </div>
                          <pre className="overflow-x-auto p-3 text-sm">
                            <code>{snippet.code}</code>
                          </pre>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}

                {def.resources.files.length === 0 &&
                  def.resources.code_snippets.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      No resources attached to this skill.
                    </p>
                  )}
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Parameters Section */}
          <AccordionItem value="parameters" className="rounded-lg border">
            <AccordionTrigger className="px-4 hover:no-underline">
              <div className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-purple-400" />
                <span className="font-semibold">Parameters</span>
                <Badge variant="secondary" className="ml-2">
                  {def.parameters.length}
                </Badge>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              {def.parameters.length > 0 ? (
                <div className="space-y-3">
                  {def.parameters.map((param) => (
                    <Card key={param.id} className="p-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium">
                            {param.name}
                            {param.required && (
                              <span className="ml-1 text-destructive">*</span>
                            )}
                          </p>
                          {param.description && (
                            <p className="mt-1 text-sm text-muted-foreground">
                              {param.description}
                            </p>
                          )}
                        </div>
                        <Badge variant="outline">{param.type}</Badge>
                      </div>
                      {param.default_value !== undefined && (
                        <p className="mt-2 text-xs text-muted-foreground">
                          Default: {String(param.default_value)}
                        </p>
                      )}
                      {param.options && param.options.length > 0 && (
                        <p className="mt-2 text-xs text-muted-foreground">
                          Options: {param.options.join(", ")}
                        </p>
                      )}
                    </Card>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No configurable parameters.
                </p>
              )}
            </AccordionContent>
          </AccordionItem>

          {/* Prompt Enhancement Section */}
          <AccordionItem value="prompts" className="rounded-lg border">
            <AccordionTrigger className="px-4 hover:no-underline">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-amber-400" />
                <span className="font-semibold">Prompt Enhancement</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              {def.prompts.system_enhancement ? (
                <div className="space-y-4">
                  <div>
                    <h4 className="mb-2 text-sm font-medium text-muted-foreground">
                      System Enhancement Template
                    </h4>
                    <pre className="overflow-x-auto rounded-lg bg-muted p-4 text-sm">
                      {def.prompts.system_enhancement}
                    </pre>
                  </div>
                  {def.prompts.variables.length > 0 && (
                    <div>
                      <h4 className="mb-2 text-sm font-medium text-muted-foreground">
                        Variables
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {def.prompts.variables.map((variable) => (
                          <Badge key={variable} variant="outline">
                            {`{{${variable}}}`}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No prompt enhancement template defined.
                </p>
              )}
            </AccordionContent>
          </AccordionItem>

          {/* Test Panel Section */}
          <AccordionItem value="test" className="rounded-lg border">
            <AccordionTrigger className="px-4 hover:no-underline">
              <div className="flex items-center gap-2">
                <Play className="h-5 w-5 text-green-400" />
                <span className="font-semibold">Test Skill</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium">
                    Test Input
                  </label>
                  <Textarea
                    placeholder="Enter a sample input to test the skill context injection..."
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    rows={4}
                  />
                </div>
                <Button
                  onClick={handleTest}
                  disabled={!testInput.trim() || testSkill.isPending}
                  className="gap-2"
                >
                  {testSkill.isPending ? (
                    <>Testing...</>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Run Test
                    </>
                  )}
                </Button>
                {testResult && (
                  <div className="mt-4">
                    <h4 className="mb-2 text-sm font-medium">
                      Enhanced Prompt Preview
                    </h4>
                    <pre className="overflow-x-auto rounded-lg bg-muted p-4 text-sm">
                      {testResult}
                    </pre>
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        {/* Metadata Footer */}
        <div className="mt-8 flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-4">
            <span>Created {format(new Date(skill.created_at), "PPP")}</span>
            <span>•</span>
            <span>Updated {format(new Date(skill.updated_at), "PPP")}</span>
          </div>
          {skill.created_by && <span>By {skill.created_by}</span>}
        </div>
      </PageContainer>
    </>
  );
}
