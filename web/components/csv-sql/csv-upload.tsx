"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileSpreadsheet, X, Loader2, Database } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

interface CSVUploadProps {
  onUpload: (file: File, tableName: string, ifExists: "fail" | "replace" | "append") => Promise<void>;
  isUploading?: boolean;
  disabled?: boolean;
}

export function CSVUpload({
  onUpload,
  isUploading,
  disabled,
}: CSVUploadProps) {
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [tableName, setTableName] = useState("");
  const [ifExists, setIfExists] = useState<"fail" | "replace" | "append">("fail");

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file && file.name.toLowerCase().endsWith(".csv") && file.size <= MAX_FILE_SIZE) {
      setPendingFile(file);
      // Auto-generate table name from filename
      const baseName = file.name.replace(/\.csv$/i, "");
      setTableName(baseName.replace(/[^a-zA-Z0-9_]/g, "_").toLowerCase());
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
    },
    maxSize: MAX_FILE_SIZE,
    maxFiles: 1,
    disabled: disabled || isUploading,
  });

  const handleUpload = async () => {
    if (!pendingFile || !tableName.trim()) return;
    await onUpload(pendingFile, tableName.trim(), ifExists);
    setPendingFile(null);
    setTableName("");
    setIfExists("fail");
  };

  const clearFile = () => {
    setPendingFile(null);
    setTableName("");
  };

  return (
    <div className="space-y-4">
      {!pendingFile ? (
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
              <FileSpreadsheet className="h-6 w-6" />
            )}
          </div>

          <p className="mt-4 text-sm font-medium text-foreground">
            {isDragActive
              ? "Drop CSV file here..."
              : "Drop a CSV file here or click to upload"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            CSV files up to {formatFileSize(MAX_FILE_SIZE)}
          </p>
        </div>
      ) : (
        <div className="rounded-xl border bg-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <FileSpreadsheet className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">{pendingFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(pendingFile.size)}
                </p>
              </div>
            </div>
            <button
              onClick={clearFile}
              className="text-muted-foreground hover:text-destructive transition-colors"
              disabled={isUploading}
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="tableName">Table Name</Label>
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="tableName"
                  value={tableName}
                  onChange={(e) => setTableName(e.target.value)}
                  placeholder="Enter table name"
                  disabled={isUploading}
                  className="flex-1"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                The table will be created as csv_data.csv_[user_id]_{tableName}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="ifExists">If Table Exists</Label>
              <Select
                value={ifExists}
                onValueChange={(value: "fail" | "replace" | "append") => setIfExists(value)}
                disabled={isUploading}
              >
                <SelectTrigger id="ifExists">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fail">Fail (don&apos;t overwrite)</SelectItem>
                  <SelectItem value="replace">Replace existing table</SelectItem>
                  <SelectItem value="append">Append to existing table</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            onClick={handleUpload}
            disabled={isUploading || !tableName.trim()}
            className="w-full gap-2"
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                Upload CSV
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
