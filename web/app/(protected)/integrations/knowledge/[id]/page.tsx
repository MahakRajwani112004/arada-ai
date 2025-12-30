"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  FileText,
  Layers,
  Trash2,
  Pencil,
  Loader2,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { PageContainer } from "@/components/layout/page-container";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { DocumentUpload } from "@/components/knowledge/document-upload";
import { DocumentList } from "@/components/knowledge/document-list";
import {
  useKnowledgeBase,
  useUpdateKnowledgeBase,
  useDeleteKnowledgeBase,
  useDocuments,
  useUploadDocumentsBatch,
  useDeleteDocument,
  knowledgeKeys,
} from "@/lib/hooks/use-knowledge";
import { useQueryClient } from "@tanstack/react-query";
import type { KnowledgeDocument } from "@/types/knowledge";
import { formatDistanceToNow } from "date-fns";

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Skeleton className="h-14 w-14 rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-7 w-48" />
            <Skeleton className="h-4 w-72" />
          </div>
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-9 w-20" />
          <Skeleton className="h-9 w-20" />
        </div>
      </div>
      <Skeleton className="h-40 w-full rounded-xl" />
      <Skeleton className="h-64 w-full rounded-lg" />
    </div>
  );
}

export default function KnowledgeBaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const kbId = params.id as string;

  const { data: kb, isLoading: kbLoading } = useKnowledgeBase(kbId);
  const { data: docsData, isLoading: docsLoading } = useDocuments(kbId);
  const updateKB = useUpdateKnowledgeBase();
  const deleteKB = useDeleteKnowledgeBase();
  const uploadDocs = useUploadDocumentsBatch();
  const deleteDoc = useDeleteDocument();

  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);

  const handleEdit = () => {
    if (!kb) return;
    setEditName(kb.name);
    setEditDescription(kb.description);
    setIsEditOpen(true);
  };

  const handleSaveEdit = async () => {
    await updateKB.mutateAsync({
      id: kbId,
      data: { name: editName, description: editDescription },
    });
    setIsEditOpen(false);
  };

  const handleDelete = async () => {
    await deleteKB.mutateAsync(kbId);
    router.push("/integrations/knowledge");
  };

  const handleUpload = async (files: File[]) => {
    await uploadDocs.mutateAsync({ kbId, files });
  };

  const handleDeleteDoc = async (docId: string) => {
    setDeletingDocId(docId);
    try {
      await deleteDoc.mutateAsync({ kbId, docId });
    } finally {
      setDeletingDocId(null);
    }
  };

  const handleDocumentUpdate = (doc: KnowledgeDocument) => {
    // Invalidate queries to refresh the list with updated metadata
    queryClient.invalidateQueries({ queryKey: knowledgeKeys.documents(kbId) });
  };

  if (kbLoading) {
    return (
      <>
        <Header />
        <PageContainer>
          <div className="mb-6">
            <Link
              href="/integrations/knowledge"
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Knowledge Bases
            </Link>
          </div>
          <DetailSkeleton />
        </PageContainer>
      </>
    );
  }

  if (!kb) {
    return (
      <>
        <Header />
        <PageContainer>
          <div className="flex flex-col items-center justify-center py-16">
            <BookOpen className="h-12 w-12 text-muted-foreground/50" />
            <h2 className="mt-4 text-lg font-semibold">Knowledge Base Not Found</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              This knowledge base may have been deleted.
            </p>
            <Link href="/integrations/knowledge">
              <Button className="mt-6" variant="outline">
                Back to Knowledge Bases
              </Button>
            </Link>
          </div>
        </PageContainer>
      </>
    );
  }

  const statusColor =
    kb.status === "active"
      ? "default"
      : kb.status === "indexing"
        ? "secondary"
        : "destructive";

  return (
    <>
      <Header />
      <PageContainer>
        <div className="mb-6">
          <Link
            href="/integrations/knowledge"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Knowledge Bases
          </Link>
        </div>

        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 text-primary">
              <BookOpen className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold">{kb.name}</h1>
                <Badge variant={statusColor}>{kb.status}</Badge>
              </div>
              {kb.description && (
                <p className="mt-1 text-muted-foreground">{kb.description}</p>
              )}
              <div className="mt-2 flex items-center gap-4 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <FileText className="h-4 w-4" />
                  {kb.document_count} document{kb.document_count !== 1 ? "s" : ""}
                </span>
                <span className="flex items-center gap-1">
                  <Layers className="h-4 w-4" />
                  {kb.chunk_count.toLocaleString()} chunks
                </span>
                <span>
                  Updated {formatDistanceToNow(new Date(kb.updated_at))} ago
                </span>
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleEdit}>
              <Pencil className="mr-1.5 h-4 w-4" />
              Edit
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="mr-1.5 h-4 w-4" />
                  Delete
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Knowledge Base</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete &ldquo;{kb.name}&rdquo; and all its
                    documents. This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleDelete}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {deleteKB.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Deleting...
                      </>
                    ) : (
                      "Delete"
                    )}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>

        {/* Upload Section */}
        <div className="mt-8">
          <h2 className="mb-4 text-lg font-semibold">Upload Documents</h2>
          <DocumentUpload
            onUpload={handleUpload}
            isUploading={uploadDocs.isPending}
          />
        </div>

        {/* Documents List */}
        <div className="mt-8">
          <h2 className="mb-4 text-lg font-semibold">
            Documents ({docsData?.total ?? 0})
          </h2>
          {docsLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : (
            <DocumentList
              documents={docsData?.documents ?? []}
              knowledgeBaseId={kbId}
              onDelete={handleDeleteDoc}
              onUpdate={handleDocumentUpdate}
              isDeleting={deletingDocId}
            />
          )}
        </div>
      </PageContainer>

      {/* Edit Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Knowledge Base</DialogTitle>
            <DialogDescription>
              Update the name and description for this knowledge base.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Name</Label>
              <Input
                id="edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">Description</Label>
              <Textarea
                id="edit-description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveEdit}
              disabled={!editName.trim() || updateKB.isPending}
            >
              {updateKB.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
