"use client";

import Link from "next/link";
import { BookOpen, FileText, Layers, ChevronRight, Trash2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import type { KnowledgeBase } from "@/types/knowledge";
import { formatDistanceToNow } from "date-fns";

interface KBCardProps {
  kb: KnowledgeBase;
  onDelete?: (id: string) => void;
  isDeleting?: boolean;
}

export function KBCard({ kb, onDelete, isDeleting }: KBCardProps) {
  const statusColor =
    kb.status === "active"
      ? "default"
      : kb.status === "indexing"
        ? "secondary"
        : "destructive";

  return (
    <Card className="group relative overflow-hidden transition-all hover:shadow-md hover:border-primary/20">
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 text-primary">
            <BookOpen className="h-5 w-5" />
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-foreground truncate">
                {kb.name}
              </h3>
              <Badge variant={statusColor} className="shrink-0">
                {kb.status}
              </Badge>
            </div>

            {kb.description && (
              <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                {kb.description}
              </p>
            )}

            <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <FileText className="h-3.5 w-3.5" />
                {kb.document_count} document{kb.document_count !== 1 ? "s" : ""}
              </span>
              <span className="flex items-center gap-1">
                <Layers className="h-3.5 w-3.5" />
                {kb.chunk_count.toLocaleString()} chunks
              </span>
              <span>
                Updated {formatDistanceToNow(new Date(kb.updated_at))} ago
              </span>
            </div>
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-destructive"
                disabled={isDeleting}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Knowledge Base</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete &ldquo;{kb.name}&rdquo; and all its documents.
                  This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => onDelete?.(kb.id)}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>

          <Link href={`/integrations/knowledge/${kb.id}`}>
            <Button variant="outline" size="sm" className="gap-1">
              Manage
              <ChevronRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
