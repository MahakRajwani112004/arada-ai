"use client";

import { useState } from "react";
import Link from "next/link";
import { BookOpen, Plus, ArrowLeft } from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { KBCard } from "@/components/knowledge/kb-card";
import {
  useKnowledgeBases,
  useCreateKnowledgeBase,
  useDeleteKnowledgeBase,
} from "@/lib/hooks/use-knowledge";
import { DEFAULT_KB_FORM_DATA, type KnowledgeBaseFormData } from "@/types/knowledge";

function KBSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="flex items-start gap-4">
        <Skeleton className="h-11 w-11 rounded-xl" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-3 w-40" />
        </div>
      </div>
      <div className="mt-4 flex justify-between">
        <Skeleton className="h-8 w-8" />
        <Skeleton className="h-9 w-24" />
      </div>
    </div>
  );
}

function EmptyState({ onCreateClick }: { onCreateClick: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-gradient-to-b from-muted/30 to-transparent py-16">
      <div className="relative">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 text-primary">
          <BookOpen className="h-8 w-8" />
        </div>
        <div className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <Plus className="h-3.5 w-3.5" />
        </div>
      </div>
      <h3 className="mt-5 text-lg font-semibold">Your knowledge library awaits</h3>
      <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
        Create a knowledge base and upload documents to give your agents context
        and expertise.
      </p>
      <Button onClick={onCreateClick} className="mt-6 gap-2">
        <Plus className="h-4 w-4" />
        Create Knowledge Base
      </Button>
    </div>
  );
}

export default function KnowledgeBasesPage() {
  const { data, isLoading } = useKnowledgeBases();
  const createKB = useCreateKnowledgeBase();
  const deleteKB = useDeleteKnowledgeBase();

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [formData, setFormData] = useState<KnowledgeBaseFormData>(DEFAULT_KB_FORM_DATA);

  const handleCreate = async () => {
    await createKB.mutateAsync({
      name: formData.name,
      description: formData.description,
      embedding_model: formData.embedding_model,
    });
    setIsCreateOpen(false);
    setFormData(DEFAULT_KB_FORM_DATA);
  };

  const handleDelete = async (id: string) => {
    await deleteKB.mutateAsync(id);
  };

  return (
    <>
      <Header />
      <PageContainer>
        <div className="mb-6">
          <Link
            href="/integrations"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Integrations
          </Link>
        </div>

        <div className="flex items-center justify-between">
          <PageHeader
            title="Knowledge Bases"
            description="Upload documents to give your agents domain knowledge"
          />

          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Create New
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Knowledge Base</DialogTitle>
                <DialogDescription>
                  Create a new knowledge base to store and organize your
                  documents.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Product Documentation"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, name: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="What kind of documents will this contain?"
                    value={formData.description}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                    rows={3}
                  />
                </div>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsCreateOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreate}
                  disabled={!formData.name.trim() || createKB.isPending}
                >
                  {createKB.isPending ? "Creating..." : "Create"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {isLoading && (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <KBSkeleton key={i} />
            ))}
          </div>
        )}

        {data && data.knowledge_bases.length === 0 && (
          <div className="mt-6">
            <EmptyState onCreateClick={() => setIsCreateOpen(true)} />
          </div>
        )}

        {data && data.knowledge_bases.length > 0 && (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.knowledge_bases.map((kb) => (
              <KBCard
                key={kb.id}
                kb={kb}
                onDelete={handleDelete}
                isDeleting={deleteKB.isPending}
              />
            ))}
          </div>
        )}
      </PageContainer>
    </>
  );
}
