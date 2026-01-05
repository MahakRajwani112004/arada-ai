"use client";

import { useState } from "react";
import {
  Table,
  FileSpreadsheet,
  Trash2,
  Eye,
  Database,
  Loader2,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
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
import { cn } from "@/lib/utils";
import type { CSVTable, ColumnInfo } from "@/lib/api/csv-sql";

interface TableListProps {
  tables: CSVTable[];
  isLoading?: boolean;
  onDelete: (tableName: string) => Promise<void>;
  onViewSample: (tableName: string) => void;
  deletingTable?: string;
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getTypeColor(type: string): string {
  const t = type.toUpperCase();
  if (t.includes("INT") || t.includes("BIGINT")) return "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300";
  if (t.includes("DOUBLE") || t.includes("FLOAT") || t.includes("DECIMAL")) return "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300";
  if (t.includes("DATE") || t.includes("TIME")) return "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300";
  if (t.includes("BOOL")) return "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300";
  return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300";
}

interface TableRowProps {
  table: CSVTable;
  onDelete: (tableName: string) => Promise<void>;
  onViewSample: (tableName: string) => void;
  isDeleting: boolean;
}

function TableRow({ table, onDelete, onViewSample, isDeleting }: TableRowProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border rounded-lg overflow-hidden">
      <div
        className={cn(
          "flex items-center gap-4 p-4 cursor-pointer hover:bg-muted/50 transition-colors",
          expanded && "bg-muted/30"
        )}
        onClick={() => setExpanded(!expanded)}
      >
        <button className="text-muted-foreground">
          {expanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </button>

        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 shrink-0">
          <Table className="h-5 w-5 text-primary" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium truncate">{table.table_name}</p>
            {table.original_filename && (
              <Badge variant="outline" className="text-xs shrink-0">
                {table.original_filename}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
            <span>{table.row_count?.toLocaleString() ?? 0} rows</span>
            <span>{table.column_count ?? 0} columns</span>
            <span>{formatDate(table.created_at)}</span>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onViewSample(table.table_name)}
            className="gap-1"
          >
            <Eye className="h-4 w-4" />
            <span className="hidden sm:inline">Preview</span>
          </Button>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="text-destructive hover:text-destructive hover:bg-destructive/10"
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Table</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete &quot;{table.table_name}&quot;? This action
                  cannot be undone and all data will be permanently deleted.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => onDelete(table.table_name)}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      {expanded && table.columns && table.columns.length > 0 && (
        <div className="border-t bg-muted/20 p-4">
          <div className="text-xs font-medium text-muted-foreground mb-2">Columns</div>
          <div className="flex flex-wrap gap-2">
            {table.columns.map((col: ColumnInfo) => (
              <div
                key={col.name}
                className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-background border text-xs"
              >
                <span className="font-medium">{col.name}</span>
                <Badge className={cn("text-[10px] px-1.5 py-0", getTypeColor(col.type))}>
                  {col.type}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function TableList({
  tables,
  isLoading,
  onDelete,
  onViewSample,
  deletingTable,
}: TableListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (tables.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
          <Database className="h-6 w-6 text-muted-foreground" />
        </div>
        <h3 className="mt-4 text-sm font-medium">No tables yet</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload a CSV file to create your first table
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tables.map((table) => (
        <TableRow
          key={table.table_name}
          table={table}
          onDelete={onDelete}
          onViewSample={onViewSample}
          isDeleting={deletingTable === table.table_name}
        />
      ))}
    </div>
  );
}
