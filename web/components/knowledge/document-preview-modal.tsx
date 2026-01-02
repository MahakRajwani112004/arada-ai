"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Download,
  FileText,
  Image as ImageIcon,
  Table2,
  Loader2,
  AlertCircle,
  ZoomIn,
  ZoomOut,
  RotateCw,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { KnowledgeDocument } from "@/types/knowledge";
import {
  formatFileSize,
  FILE_TYPE_LABELS,
  getFileTypeCategory,
  type SupportedFileType,
} from "@/types/knowledge";
import {
  getDocumentPreview,
  getDocumentDownloadUrl,
  type DocumentPreviewResponse,
} from "@/lib/api/knowledge";

interface DocumentPreviewModalProps {
  document: KnowledgeDocument | null;
  knowledgeBaseId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function DocumentPreviewModal({
  document,
  knowledgeBaseId,
  isOpen,
  onClose,
}: DocumentPreviewModalProps) {
  const [preview, setPreview] = useState<DocumentPreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageZoom, setImageZoom] = useState(100);

  useEffect(() => {
    if (isOpen && document) {
      loadPreview();
    } else {
      setPreview(null);
      setError(null);
      setImageZoom(100);
    }
  }, [isOpen, document?.id]);

  const loadPreview = async () => {
    if (!document) return;

    setLoading(true);
    setError(null);

    try {
      const data = await getDocumentPreview(knowledgeBaseId, document.id);
      setPreview(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load preview");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!document) return;
    const url = getDocumentDownloadUrl(knowledgeBaseId, document.id);
    window.open(url, "_blank");
  };

  const zoomIn = () => setImageZoom((prev) => Math.min(prev + 25, 200));
  const zoomOut = () => setImageZoom((prev) => Math.max(prev - 25, 50));
  const resetZoom = () => setImageZoom(100);

  if (!document) return null;

  const fileCategory = getFileTypeCategory(document.file_type);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center justify-between pr-8">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                {fileCategory === "image" ? (
                  <ImageIcon className="h-5 w-5 text-muted-foreground" />
                ) : fileCategory === "spreadsheet" ? (
                  <Table2 className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <FileText className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
              <div>
                <DialogTitle className="text-left">{document.filename}</DialogTitle>
                <DialogDescription className="text-left">
                  {FILE_TYPE_LABELS[document.file_type as SupportedFileType] ||
                    document.file_type.toUpperCase()}{" "}
                  - {formatFileSize(document.file_size)}
                </DialogDescription>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-hidden mt-4">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <AlertCircle className="h-10 w-10 text-destructive mb-4" />
              <p className="text-sm text-destructive">{error}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={loadPreview}
                className="mt-4"
              >
                <RotateCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          ) : preview?.type === "image" ? (
            <div className="relative">
              {/* Image zoom controls */}
              <div className="absolute top-2 right-2 z-10 flex gap-1 bg-background/80 rounded-lg p-1">
                <Button variant="ghost" size="icon" onClick={zoomOut}>
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <span className="flex items-center px-2 text-sm text-muted-foreground">
                  {imageZoom}%
                </span>
                <Button variant="ghost" size="icon" onClick={zoomIn}>
                  <ZoomIn className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" onClick={resetZoom}>
                  <RotateCw className="h-4 w-4" />
                </Button>
              </div>

              {/* Image preview */}
              <div className="overflow-auto max-h-[60vh] border rounded-lg bg-muted/20">
                <img
                  src={preview.url}
                  alt={document.filename}
                  className="mx-auto transition-transform"
                  style={{ transform: `scale(${imageZoom / 100})`, transformOrigin: "center top" }}
                />
              </div>
            </div>
          ) : preview?.type === "text" ? (
            <Tabs defaultValue="content" className="h-full flex flex-col">
              <TabsList className="flex-shrink-0">
                <TabsTrigger value="content">Content</TabsTrigger>
                {preview.tables && preview.tables.length > 0 && (
                  <TabsTrigger value="tables">
                    Tables ({preview.tables.length})
                  </TabsTrigger>
                )}
                <TabsTrigger value="info">Info</TabsTrigger>
              </TabsList>

              <TabsContent value="content" className="flex-1 overflow-auto mt-4">
                <div className="prose prose-sm dark:prose-invert max-w-none p-4 bg-muted/20 rounded-lg max-h-[50vh] overflow-auto">
                  <ReactMarkdown>{preview.content || ""}</ReactMarkdown>
                </div>
              </TabsContent>

              {preview.tables && preview.tables.length > 0 && (
                <TabsContent value="tables" className="flex-1 overflow-auto mt-4">
                  <div className="space-y-4 max-h-[50vh] overflow-auto">
                    {preview.tables.map((table, idx) => (
                      <div key={idx} className="border rounded-lg overflow-hidden">
                        <div className="bg-muted px-4 py-2 flex items-center justify-between">
                          <span className="text-sm font-medium">
                            {table.sheet_name || `Table ${idx + 1}`}
                            {table.page_number && ` (Page ${table.page_number})`}
                          </span>
                          <Badge variant="secondary">
                            {table.row_count} rows x {table.col_count} cols
                          </Badge>
                        </div>
                        <div className="p-4 overflow-auto prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown>{table.markdown}</ReactMarkdown>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              )}

              <TabsContent value="info" className="flex-1 overflow-auto mt-4">
                <div className="grid gap-4 p-4 bg-muted/20 rounded-lg">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">File Type:</span>
                      <p className="font-medium">
                        {FILE_TYPE_LABELS[document.file_type as SupportedFileType] ||
                          document.file_type.toUpperCase()}
                      </p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">File Size:</span>
                      <p className="font-medium">{formatFileSize(document.file_size)}</p>
                    </div>
                    {preview.page_count && preview.page_count > 0 && (
                      <div>
                        <span className="text-muted-foreground">Pages:</span>
                        <p className="font-medium">{preview.page_count}</p>
                      </div>
                    )}
                    {preview.word_count && preview.word_count > 0 && (
                      <div>
                        <span className="text-muted-foreground">Word Count:</span>
                        <p className="font-medium">{preview.word_count.toLocaleString()}</p>
                      </div>
                    )}
                    <div>
                      <span className="text-muted-foreground">Chunks:</span>
                      <p className="font-medium">{document.chunk_count}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Status:</span>
                      <Badge
                        variant={
                          document.status === "indexed"
                            ? "default"
                            : document.status === "error"
                            ? "destructive"
                            : "secondary"
                        }
                      >
                        {document.status}
                      </Badge>
                    </div>
                  </div>

                  {/* Metadata */}
                  {preview.metadata && Object.keys(preview.metadata).length > 0 && (
                    <div className="border-t pt-4">
                      <h4 className="text-sm font-medium mb-2">Document Metadata</h4>
                      <dl className="grid grid-cols-2 gap-2 text-sm">
                        {Object.entries(preview.metadata).map(([key, value]) => (
                          <div key={key}>
                            <dt className="text-muted-foreground capitalize">
                              {key.replace(/_/g, " ")}:
                            </dt>
                            <dd className="font-medium truncate">
                              {String(value) || "-"}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          ) : (
            <div className="flex items-center justify-center h-64 text-muted-foreground">
              No preview available
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
