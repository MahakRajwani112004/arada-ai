"use client";

import { useCallback, useState, useRef } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  FileUp,
  X,
  Loader2,
  CheckCircle2,
  AlertCircle,
  RotateCw,
  Pause,
  Play,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  SUPPORTED_FILE_TYPES,
  MAX_FILE_SIZE,
  formatFileSize,
} from "@/types/knowledge";
import {
  uploadFileChunked,
  resumeUpload,
  cancelUpload,
  needsChunkedUpload,
  type UploadProgress,
  type UploadCompleteResult,
} from "@/lib/upload-client";

interface FileUploadState {
  file: File;
  progress: UploadProgress | null;
  result: UploadCompleteResult | null;
  error: string | null;
  abortController: AbortController | null;
}

interface ChunkedUploaderProps {
  knowledgeBaseId: string;
  onUploadComplete?: (result: UploadCompleteResult) => void;
  onUploadError?: (error: Error, file: File) => void;
  disabled?: boolean;
}

export function ChunkedUploader({
  knowledgeBaseId,
  onUploadComplete,
  onUploadError,
  disabled,
}: ChunkedUploaderProps) {
  const [uploads, setUploads] = useState<Map<string, FileUploadState>>(new Map());
  const [isUploading, setIsUploading] = useState(false);

  const updateUpload = (fileKey: string, update: Partial<FileUploadState>) => {
    setUploads((prev) => {
      const newMap = new Map(prev);
      const current = newMap.get(fileKey);
      if (current) {
        newMap.set(fileKey, { ...current, ...update });
      }
      return newMap;
    });
  };

  const uploadFile = async (file: File) => {
    const fileKey = `${file.name}-${file.size}-${file.lastModified}`;
    const abortController = new AbortController();

    setUploads((prev) => {
      const newMap = new Map(prev);
      newMap.set(fileKey, {
        file,
        progress: null,
        result: null,
        error: null,
        abortController,
      });
      return newMap;
    });

    try {
      const result = await uploadFileChunked(
        knowledgeBaseId,
        file,
        (progress) => {
          updateUpload(fileKey, { progress });
        },
        abortController.signal
      );

      updateUpload(fileKey, { result, abortController: null });
      onUploadComplete?.(result);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Upload failed";
      updateUpload(fileKey, { error: errorMessage, abortController: null });
      onUploadError?.(error instanceof Error ? error : new Error(errorMessage), file);
    }
  };

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const validFiles = acceptedFiles.filter((file) => {
        const ext = file.name.split(".").pop()?.toLowerCase();
        return (
          ext &&
          SUPPORTED_FILE_TYPES.includes(ext as (typeof SUPPORTED_FILE_TYPES)[number]) &&
          file.size <= MAX_FILE_SIZE
        );
      });

      if (validFiles.length === 0) return;

      setIsUploading(true);

      // Upload files sequentially to avoid overwhelming the server
      for (const file of validFiles) {
        await uploadFile(file);
      }

      setIsUploading(false);
    },
    [knowledgeBaseId]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      "application/vnd.ms-powerpoint": [".ppt"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "text/csv": [".csv"],
      "text/plain": [".txt"],
      "text/markdown": [".md", ".markdown"],
      "text/html": [".html", ".htm"],
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

  const cancelFileUpload = async (fileKey: string) => {
    const upload = uploads.get(fileKey);
    if (upload?.abortController) {
      upload.abortController.abort();
    }
  };

  const retryUpload = async (fileKey: string) => {
    const upload = uploads.get(fileKey);
    if (upload?.file) {
      setIsUploading(true);
      await uploadFile(upload.file);
      setIsUploading(false);
    }
  };

  const removeUpload = (fileKey: string) => {
    setUploads((prev) => {
      const newMap = new Map(prev);
      newMap.delete(fileKey);
      return newMap;
    });
  };

  const clearCompleted = () => {
    setUploads((prev) => {
      const newMap = new Map(prev);
      for (const [key, upload] of newMap) {
        if (upload.result || upload.error) {
          newMap.delete(key);
        }
      }
      return newMap;
    });
  };

  const uploadsArray = Array.from(uploads.entries());
  const hasCompletedOrFailed = uploadsArray.some(
    ([, upload]) => upload.result || upload.error
  );

  return (
    <div className="space-y-4">
      {/* Drop zone */}
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
          PDF, DOCX, PPTX, XLSX, CSV, TXT, MD, HTML, Images up to{" "}
          {formatFileSize(MAX_FILE_SIZE)}
        </p>
        <p className="mt-1 text-xs text-muted-foreground/70">
          Large files are automatically chunked for reliable uploads
        </p>
      </div>

      {/* Upload list */}
      {uploadsArray.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">
              {uploadsArray.length} file{uploadsArray.length !== 1 ? "s" : ""}
            </span>
            {hasCompletedOrFailed && (
              <Button variant="ghost" size="sm" onClick={clearCompleted}>
                Clear completed
              </Button>
            )}
          </div>

          <div className="max-h-64 space-y-2 overflow-y-auto">
            {uploadsArray.map(([fileKey, upload]) => (
              <UploadItem
                key={fileKey}
                fileKey={fileKey}
                upload={upload}
                onCancel={() => cancelFileUpload(fileKey)}
                onRetry={() => retryUpload(fileKey)}
                onRemove={() => removeUpload(fileKey)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface UploadItemProps {
  fileKey: string;
  upload: FileUploadState;
  onCancel: () => void;
  onRetry: () => void;
  onRemove: () => void;
}

function UploadItem({
  fileKey,
  upload,
  onCancel,
  onRetry,
  onRemove,
}: UploadItemProps) {
  const { file, progress, result, error } = upload;
  const isUploading = progress?.status === "uploading" || progress?.status === "completing";
  const isComplete = result !== null;
  const isFailed = error !== null;

  return (
    <div
      className={cn(
        "rounded-lg border p-3 transition-colors",
        isComplete && "border-green-500/30 bg-green-500/5",
        isFailed && "border-destructive/30 bg-destructive/5"
      )}
    >
      <div className="flex items-center gap-3">
        {/* Status icon */}
        <div className="flex-shrink-0">
          {isComplete ? (
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          ) : isFailed ? (
            <AlertCircle className="h-5 w-5 text-destructive" />
          ) : isUploading ? (
            <Loader2 className="h-5 w-5 text-primary animate-spin" />
          ) : (
            <FileUp className="h-5 w-5 text-muted-foreground" />
          )}
        </div>

        {/* File info */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{file.name}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{formatFileSize(file.size)}</span>
            {progress && (
              <>
                <span>•</span>
                <span>
                  {progress.uploadedChunks}/{progress.totalChunks} chunks
                </span>
              </>
            )}
            {isComplete && <span className="text-green-600">Uploaded</span>}
            {isFailed && <span className="text-destructive">{error}</span>}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          {isUploading && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onCancel}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
          {isFailed && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onRetry}
            >
              <RotateCw className="h-4 w-4" />
            </Button>
          )}
          {(isComplete || isFailed) && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onRemove}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {progress && !isComplete && !isFailed && (
        <div className="mt-2">
          <Progress value={progress.progress} className="h-1.5" />
          <p className="mt-1 text-xs text-muted-foreground text-right">
            {progress.progress}%
          </p>
        </div>
      )}
    </div>
  );
}
