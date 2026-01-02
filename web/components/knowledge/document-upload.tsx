"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileUp, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  SUPPORTED_FILE_TYPES,
  MAX_FILE_SIZE,
  formatFileSize,
} from "@/types/knowledge";

interface DocumentUploadProps {
  onUpload: (files: File[]) => Promise<void>;
  isUploading?: boolean;
  disabled?: boolean;
}

export function DocumentUpload({
  onUpload,
  isUploading,
  disabled,
}: DocumentUploadProps) {
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const validFiles = acceptedFiles.filter((file) => {
      const ext = file.name.split(".").pop()?.toLowerCase();
      return (
        ext &&
        SUPPORTED_FILE_TYPES.includes(ext as (typeof SUPPORTED_FILE_TYPES)[number]) &&
        file.size <= MAX_FILE_SIZE
      );
    });
    setPendingFiles((prev) => [...prev, ...validFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      // Documents
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      "application/vnd.ms-powerpoint": [".ppt"],
      // Spreadsheets
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "text/csv": [".csv"],
      // Text files
      "text/plain": [".txt"],
      "text/markdown": [".md", ".markdown"],
      "text/html": [".html", ".htm"],
      // Images
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
      "image/gif": [".gif"],
      "image/bmp": [".bmp"],
      "image/tiff": [".tiff", ".tif"],
      "image/webp": [".webp"],
    },
    maxSize: MAX_FILE_SIZE,
    disabled: disabled || isUploading,
  });

  const removeFile = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (pendingFiles.length === 0) return;
    await onUpload(pendingFiles);
    setPendingFiles([]);
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          "relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-all cursor-pointer",
          isDragActive
            ? "border-primary bg-primary/5 scale-[1.02]"
            : "border-border hover:border-primary/50 hover:bg-muted/50",
          (disabled || isUploading) && "opacity-50 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />

        <div
          className={cn(
            "flex h-14 w-14 items-center justify-center rounded-full transition-transform",
            isDragActive
              ? "bg-primary/10 text-primary scale-110"
              : "bg-muted text-muted-foreground"
          )}
        >
          {isUploading ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : (
            <Upload className="h-6 w-6" />
          )}
        </div>

        <p className="mt-4 text-sm font-medium text-foreground">
          {isDragActive
            ? "Drop files here..."
            : "Drop files here or click to upload"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          PDF, DOCX, PPTX, XLSX, CSV, TXT, MD, HTML, Images up to {formatFileSize(MAX_FILE_SIZE)}
        </p>
      </div>

      {pendingFiles.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">
              {pendingFiles.length} file{pendingFiles.length !== 1 ? "s" : ""}{" "}
              ready to upload
            </span>
            <Button
              size="sm"
              onClick={handleUpload}
              disabled={isUploading}
              className="gap-2"
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <FileUp className="h-4 w-4" />
                  Upload All
                </>
              )}
            </Button>
          </div>

          <div className="max-h-48 space-y-1 overflow-y-auto">
            {pendingFiles.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2 text-sm"
              >
                <span className="truncate">{file.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    {formatFileSize(file.size)}
                  </span>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-muted-foreground hover:text-destructive"
                    disabled={isUploading}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
