"use client";

import { useState, useRef, useCallback } from "react";
import {
  Upload,
  File,
  FileText,
  Code,
  Trash2,
  Plus,
  AlertCircle,
  Loader2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  useSkillFiles,
  useUploadSkillFile,
  useDeleteSkillFile,
  useSupportedFileTypes,
} from "@/lib/hooks/use-skills";
import type { CodeSnippet, FileType, SkillResources } from "@/types/skill";

interface ResourcesSectionProps {
  skillId?: string; // Only available in edit mode
  resources: SkillResources;
  onChange: (resources: SkillResources) => void;
  mode: "create" | "edit";
}

const FILE_TYPE_LABELS: Record<FileType, string> = {
  reference: "Reference Document",
  template: "Template",
};

const LANGUAGE_OPTIONS = [
  "python",
  "javascript",
  "typescript",
  "json",
  "yaml",
  "sql",
  "bash",
  "markdown",
  "html",
  "css",
  "other",
];

export function ResourcesSection({
  skillId,
  resources,
  onChange,
  mode,
}: ResourcesSectionProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFileType, setSelectedFileType] = useState<FileType>("reference");
  const [showSnippetDialog, setShowSnippetDialog] = useState(false);
  const [editingSnippet, setEditingSnippet] = useState<CodeSnippet | null>(null);
  const [newSnippet, setNewSnippet] = useState({
    language: "python",
    code: "",
    description: "",
  });

  // Queries and mutations for file management (only in edit mode)
  const { data: uploadedFiles = [], isLoading: filesLoading } = useSkillFiles(
    skillId || ""
  );
  const { data: supportedTypes } = useSupportedFileTypes();
  const uploadFile = useUploadSkillFile();
  const deleteFile = useDeleteSkillFile();

  // Handle file selection
  const handleFileSelect = useCallback(
    async (files: FileList | null) => {
      if (!files || !skillId) return;

      for (const file of Array.from(files)) {
        uploadFile.mutate({
          skillId,
          file,
          fileType: selectedFileType,
        });
      }
    },
    [skillId, selectedFileType, uploadFile]
  );

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  // Code snippet handlers
  const handleAddSnippet = () => {
    if (!newSnippet.code.trim()) return;

    const snippet: CodeSnippet = {
      id: `snippet_${Date.now()}`,
      language: newSnippet.language,
      code: newSnippet.code,
      description: newSnippet.description || undefined,
    };

    onChange({
      ...resources,
      code_snippets: [...resources.code_snippets, snippet],
    });

    setNewSnippet({ language: "python", code: "", description: "" });
    setShowSnippetDialog(false);
  };

  const handleUpdateSnippet = () => {
    if (!editingSnippet) return;

    onChange({
      ...resources,
      code_snippets: resources.code_snippets.map((s) =>
        s.id === editingSnippet.id ? editingSnippet : s
      ),
    });

    setEditingSnippet(null);
  };

  const handleDeleteSnippet = (id: string) => {
    onChange({
      ...resources,
      code_snippets: resources.code_snippets.filter((s) => s.id !== id),
    });
  };

  const handleDeleteFile = (fileId: string) => {
    if (!skillId) return;
    deleteFile.mutate({ skillId, fileId });
  };

  // Get file icon based on type
  const getFileIcon = (fileName: string) => {
    const ext = fileName.split(".").pop()?.toLowerCase();
    if (["py", "js", "ts", "jsx", "tsx"].includes(ext || "")) {
      return <Code className="h-4 w-4" />;
    }
    if (["pdf", "doc", "docx", "txt", "md"].includes(ext || "")) {
      return <FileText className="h-4 w-4" />;
    }
    return <File className="h-4 w-4" />;
  };

  // Combine local code snippets with uploaded files for display
  const allFiles = mode === "edit" ? uploadedFiles : resources.files;

  return (
    <div className="space-y-6">
      {/* Info alert for create mode */}
      {mode === "create" && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            File uploads will be available after saving the skill. You can add
            code snippets now.
          </AlertDescription>
        </Alert>
      )}

      {/* File Upload Section (only in edit mode) */}
      {mode === "edit" && skillId && (
        <div>
          <div className="mb-3 flex items-center justify-between">
            <Label className="text-sm font-medium">Files</Label>
            <Select
              value={selectedFileType}
              onValueChange={(v) => setSelectedFileType(v as FileType)}
            >
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="reference">Reference Document</SelectItem>
                <SelectItem value="template">Template</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Drag & Drop Zone */}
          <div
            className={`relative cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
              isDragging
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-muted-foreground/50"
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              multiple
              accept={supportedTypes?.extensions
                .map((ext) => `.${ext}`)
                .join(",")}
              onChange={(e) => handleFileSelect(e.target.files)}
            />

            {uploadFile.isPending ? (
              <div className="flex flex-col items-center gap-2">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <p className="text-sm text-muted-foreground">Uploading...</p>
              </div>
            ) : (
              <>
                <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">
                  Drag & drop files here, or click to browse
                </p>
                {supportedTypes && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Supported: {supportedTypes.extensions.slice(0, 8).join(", ")}
                    {supportedTypes.extensions.length > 8 && "..."} (max{" "}
                    {supportedTypes.max_size_mb}MB)
                  </p>
                )}
              </>
            )}
          </div>

          {/* Uploaded Files List */}
          {filesLoading ? (
            <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading files...
            </div>
          ) : allFiles.length > 0 ? (
            <div className="mt-4 space-y-2">
              {allFiles.map((file) => (
                <Card
                  key={file.id}
                  className="flex items-center justify-between p-3"
                >
                  <div className="flex items-center gap-3">
                    {getFileIcon(file.name)}
                    <div>
                      <p className="text-sm font-medium">{file.name}</p>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {FILE_TYPE_LABELS[file.file_type]}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {(file.size_bytes / 1024).toFixed(1)} KB
                        </span>
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteFile(file.id)}
                    disabled={deleteFile.isPending}
                  >
                    {deleteFile.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4 text-destructive" />
                    )}
                  </Button>
                </Card>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">
              No files uploaded yet
            </p>
          )}
        </div>
      )}

      {/* Code Snippets Section */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <Label className="text-sm font-medium">Code Snippets</Label>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSnippetDialog(true)}
            className="gap-1"
          >
            <Plus className="h-3 w-3" />
            Add Snippet
          </Button>
        </div>

        {resources.code_snippets.length > 0 ? (
          <div className="space-y-3">
            {resources.code_snippets.map((snippet) => (
              <Card key={snippet.id} className="overflow-hidden">
                <div className="flex items-center justify-between border-b bg-muted/30 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <Code className="h-4 w-4 text-muted-foreground" />
                    <Badge variant="secondary">{snippet.language}</Badge>
                    {snippet.description && (
                      <span className="text-xs text-muted-foreground">
                        {snippet.description}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => setEditingSnippet(snippet)}
                    >
                      <Code className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => handleDeleteSnippet(snippet.id)}
                    >
                      <X className="h-3 w-3 text-destructive" />
                    </Button>
                  </div>
                </div>
                <pre className="max-h-32 overflow-auto p-3 text-xs">
                  <code>{snippet.code}</code>
                </pre>
              </Card>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No code snippets added yet. Add code examples to help the agent
            understand patterns.
          </p>
        )}
      </div>

      {/* Add Snippet Dialog */}
      <Dialog open={showSnippetDialog} onOpenChange={setShowSnippetDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add Code Snippet</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="language">Language</Label>
                <Select
                  value={newSnippet.language}
                  onValueChange={(v) =>
                    setNewSnippet({ ...newSnippet, language: v })
                  }
                >
                  <SelectTrigger id="language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LANGUAGE_OPTIONS.map((lang) => (
                      <SelectItem key={lang} value={lang}>
                        {lang.charAt(0).toUpperCase() + lang.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="description">Description (optional)</Label>
                <Input
                  id="description"
                  value={newSnippet.description}
                  onChange={(e) =>
                    setNewSnippet({ ...newSnippet, description: e.target.value })
                  }
                  placeholder="What does this snippet do?"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="code">Code</Label>
              <Textarea
                id="code"
                value={newSnippet.code}
                onChange={(e) =>
                  setNewSnippet({ ...newSnippet, code: e.target.value })
                }
                placeholder="Paste your code here..."
                className="font-mono text-sm"
                rows={12}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowSnippetDialog(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleAddSnippet} disabled={!newSnippet.code.trim()}>
              Add Snippet
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Snippet Dialog */}
      <Dialog
        open={!!editingSnippet}
        onOpenChange={() => setEditingSnippet(null)}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Code Snippet</DialogTitle>
          </DialogHeader>
          {editingSnippet && (
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="edit-language">Language</Label>
                  <Select
                    value={editingSnippet.language}
                    onValueChange={(v) =>
                      setEditingSnippet({ ...editingSnippet, language: v })
                    }
                  >
                    <SelectTrigger id="edit-language">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {LANGUAGE_OPTIONS.map((lang) => (
                        <SelectItem key={lang} value={lang}>
                          {lang.charAt(0).toUpperCase() + lang.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="edit-description">Description (optional)</Label>
                  <Input
                    id="edit-description"
                    value={editingSnippet.description || ""}
                    onChange={(e) =>
                      setEditingSnippet({
                        ...editingSnippet,
                        description: e.target.value,
                      })
                    }
                    placeholder="What does this snippet do?"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="edit-code">Code</Label>
                <Textarea
                  id="edit-code"
                  value={editingSnippet.code}
                  onChange={(e) =>
                    setEditingSnippet({
                      ...editingSnippet,
                      code: e.target.value,
                    })
                  }
                  className="font-mono text-sm"
                  rows={12}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingSnippet(null)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateSnippet}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
