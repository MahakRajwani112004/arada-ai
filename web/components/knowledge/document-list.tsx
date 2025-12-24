"use client";

import { FileText, Trash2, Loader2, AlertCircle, CheckCircle2, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { KnowledgeDocument } from "@/types/knowledge";
import {
  formatFileSize,
  getDocumentStatusColor,
  FILE_TYPE_LABELS,
  type SupportedFileType,
} from "@/types/knowledge";
import { formatDistanceToNow } from "date-fns";

interface DocumentListProps {
  documents: KnowledgeDocument[];
  onDelete?: (docId: string) => void;
  isDeleting?: string | null;
}

function StatusIcon({ status }: { status: KnowledgeDocument["status"] }) {
  switch (status) {
    case "indexed":
      return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    case "processing":
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
    case "error":
      return <AlertCircle className="h-4 w-4 text-destructive" />;
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />;
  }
}

export function DocumentList({
  documents,
  onDelete,
  isDeleting,
}: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 py-12">
        <FileText className="h-10 w-10 text-muted-foreground/50" />
        <p className="mt-3 text-sm text-muted-foreground">No documents yet</p>
        <p className="mt-1 text-xs text-muted-foreground/70">
          Upload files above to get started
        </p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-border rounded-lg border border-border bg-card">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="flex items-center gap-4 p-4 transition-colors hover:bg-muted/30"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
            <FileText className="h-5 w-5 text-muted-foreground" />
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="font-medium truncate">{doc.filename}</span>
              <Badge
                variant={getDocumentStatusColor(doc.status)}
                className="shrink-0"
              >
                {doc.status}
              </Badge>
            </div>
            <div className="mt-0.5 flex items-center gap-3 text-xs text-muted-foreground">
              <span>
                {FILE_TYPE_LABELS[doc.file_type as SupportedFileType] ||
                  doc.file_type.toUpperCase()}
              </span>
              <span>{formatFileSize(doc.file_size)}</span>
              {doc.status === "indexed" && (
                <span>{doc.chunk_count} chunks</span>
              )}
              <span>
                {formatDistanceToNow(new Date(doc.created_at))} ago
              </span>
            </div>
            {doc.error_message && (
              <p className="mt-1 text-xs text-destructive">{doc.error_message}</p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <StatusIcon status={doc.status} />
                </TooltipTrigger>
                <TooltipContent>
                  {doc.status === "indexed" && "Ready for search"}
                  {doc.status === "processing" && "Being processed..."}
                  {doc.status === "pending" && "Waiting to process"}
                  {doc.status === "error" && "Processing failed"}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  disabled={isDeleting === doc.id}
                >
                  {isDeleting === doc.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Document</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to delete &ldquo;{doc.filename}&rdquo;? This
                    action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => onDelete?.(doc.id)}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      ))}
    </div>
  );
}
