"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SkillBuilderForm } from "@/components/skills/create";
import { useSkill } from "@/lib/hooks/use-skills";

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-48" />
      <div className="space-y-4">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    </div>
  );
}

export default function EditSkillPage() {
  const { id } = useParams<{ id: string }>();
  const { data: skill, isLoading, error } = useSkill(id);

  if (isLoading) {
    return (
      <>
        <Header />
        <PageContainer>
          <div className="mb-6">
            <Button variant="ghost" size="sm" asChild className="gap-2">
              <Link href={`/skills/${id}`}>
                <ArrowLeft className="h-4 w-4" />
                Back to Skill
              </Link>
            </Button>
          </div>
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
                The skill you&apos;re trying to edit doesn&apos;t exist or you don&apos;t have
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

  return (
    <>
      <Header />
      <PageContainer>
        {/* Back button */}
        <div className="mb-6">
          <Button variant="ghost" size="sm" asChild className="gap-2">
            <Link href={`/skills/${id}`}>
              <ArrowLeft className="h-4 w-4" />
              Back to Skill
            </Link>
          </Button>
        </div>

        {/* Title */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold">Edit Skill</h1>
          <p className="mt-1 text-muted-foreground">
            Modify the skill definition and settings
          </p>
        </div>

        {/* Form */}
        <SkillBuilderForm
          mode="edit"
          initialData={{
            id: skill.id,
            name: skill.name,
            description: skill.description,
            category: skill.category,
            tags: skill.tags,
            definition: skill.definition,
          }}
        />
      </PageContainer>
    </>
  );
}
