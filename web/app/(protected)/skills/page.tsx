"use client";

import { Lightbulb, Plus, Sparkles, Search, Filter } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { SkillCard } from "@/components/skills/skill-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSkills, useDeleteSkill } from "@/lib/hooks/use-skills";
import { SKILL_CATEGORY_LABELS, type SkillCategory } from "@/types/skill";

function SkillCardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-start gap-3">
        <Skeleton className="h-10 w-10 rounded-lg" />
        <div className="flex-1">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="mt-2 h-4 w-20" />
        </div>
      </div>
      <Skeleton className="mt-4 h-4 w-full" />
      <Skeleton className="mt-1 h-4 w-3/4" />
      <div className="mt-4 flex justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-3 w-8" />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 py-16">
      <motion.div
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-amber-500/20 to-orange-500/20"
      >
        <Lightbulb className="h-8 w-8 text-amber-400" />
      </motion.div>
      <h3 className="mt-6 text-lg font-semibold">
        Empower your agents with skills
      </h3>
      <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
        Create your first skill to inject domain expertise, terminology, and
        reasoning patterns into your AI agents
      </p>
      <div className="mt-6 flex gap-3">
        <Button asChild variant="outline" className="gap-2">
          <Link href="/skills/new">
            <Plus className="h-4 w-4" />
            Create Manually
          </Link>
        </Button>
        <Button asChild className="gap-2">
          <Link href="/skills/new?ai=true">
            <Sparkles className="h-4 w-4" />
            Generate with AI
          </Link>
        </Button>
      </div>
    </div>
  );
}

export default function SkillsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<SkillCategory | "all">(
    "all"
  );

  const { data, isLoading, error } = useSkills({
    search: searchQuery || undefined,
    category: categoryFilter === "all" ? undefined : categoryFilter,
  });
  const deleteSkill = useDeleteSkill();

  const handleDelete = (id: string) => {
    if (confirm("Are you sure you want to delete this skill?")) {
      deleteSkill.mutate(id);
    }
  };

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="Skills"
          description="Domain expertise and reasoning patterns for your agents"
          actions={
            <div className="flex gap-2">
              <Button asChild variant="outline" className="gap-2">
                <Link href="/skills/new">
                  <Plus className="h-4 w-4" />
                  New Skill
                </Link>
              </Button>
              <Button asChild className="gap-2">
                <Link href="/skills/new?ai=true">
                  <Sparkles className="h-4 w-4" />
                  AI Generate
                </Link>
              </Button>
            </div>
          }
        />

        {/* Filters */}
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2">
            <Select
              value={categoryFilter}
              onValueChange={(value) =>
                setCategoryFilter(value as SkillCategory | "all")
              }
            >
              <SelectTrigger className="w-[180px]">
                <Filter className="mr-2 h-4 w-4" />
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {Object.entries(SKILL_CATEGORY_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <SkillCardSkeleton key={i} />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive">
            Failed to load skills: {error.message}
          </div>
        )}

        {data && data.skills.length === 0 && !searchQuery && !categoryFilter && (
          <EmptyState />
        )}

        {data && data.skills.length === 0 && (searchQuery || categoryFilter !== "all") && (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 py-12">
            <Search className="h-12 w-12 text-muted-foreground/50" />
            <h3 className="mt-4 text-lg font-semibold">No skills found</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Try adjusting your search or filters
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => {
                setSearchQuery("");
                setCategoryFilter("all");
              }}
            >
              Clear filters
            </Button>
          </div>
        )}

        {data && data.skills.length > 0 && (
          <>
            <div className="mb-4 text-sm text-muted-foreground">
              {data.total} skill{data.total !== 1 ? "s" : ""} found
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data.skills.map((skill) => (
                <SkillCard
                  key={skill.id}
                  skill={skill}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          </>
        )}
      </PageContainer>
    </>
  );
}
