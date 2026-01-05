"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Database, FileSpreadsheet, Code, Play, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Header } from "@/components/layout/header";
import { PageContainer, PageHeader } from "@/components/layout/page-container";
import { CSVUpload } from "@/components/csv-sql/csv-upload";
import { TableList } from "@/components/csv-sql/table-list";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  uploadCSV,
  listCSVTables,
  deleteCSVTable,
  getSampleData,
  executeSQL,
  type CSVTable,
} from "@/lib/api/csv-sql";

export default function CSVSQLPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("upload");
  const [sqlQuery, setSqlQuery] = useState("");
  const [queryResult, setQueryResult] = useState<string | null>(null);
  const [isQueryRunning, setIsQueryRunning] = useState(false);
  const [deletingTable, setDeletingTable] = useState<string | undefined>();
  const [previewData, setPreviewData] = useState<{ tableName: string; data: string } | null>(null);

  // Fetch tables
  const { data: tablesData, isLoading: tablesLoading } = useQuery({
    queryKey: ["csv-tables"],
    queryFn: listCSVTables,
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async ({
      file,
      tableName,
      ifExists,
    }: {
      file: File;
      tableName: string;
      ifExists: "fail" | "replace" | "append";
    }) => {
      return uploadCSV(file, tableName, ifExists);
    },
    onSuccess: (result) => {
      if (result.success) {
        toast.success(`Table "${result.table_name}" created with ${result.row_count} rows`);
        queryClient.invalidateQueries({ queryKey: ["csv-tables"] });
        setActiveTab("tables");
      } else {
        toast.error(result.error || "Failed to upload CSV");
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to upload CSV");
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteCSVTable,
    onSuccess: (result, tableName) => {
      if (result.success) {
        toast.success(`Table "${tableName}" deleted`);
        queryClient.invalidateQueries({ queryKey: ["csv-tables"] });
      } else {
        toast.error(result.error || "Failed to delete table");
      }
      setDeletingTable(undefined);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to delete table");
      setDeletingTable(undefined);
    },
  });

  const handleUpload = async (
    file: File,
    tableName: string,
    ifExists: "fail" | "replace" | "append"
  ) => {
    await uploadMutation.mutateAsync({ file, tableName, ifExists });
  };

  const handleDelete = async (tableName: string) => {
    setDeletingTable(tableName);
    await deleteMutation.mutateAsync(tableName);
  };

  const handleViewSample = async (tableName: string) => {
    try {
      const result = await getSampleData(tableName, 10);
      if (result.success && result.sample) {
        setPreviewData({ tableName, data: result.sample });
      } else {
        toast.error(result.error || "Failed to get sample data");
      }
    } catch (error) {
      toast.error("Failed to get sample data");
    }
  };

  const handleRunQuery = async () => {
    if (!sqlQuery.trim()) return;

    setIsQueryRunning(true);
    setQueryResult(null);

    try {
      const result = await executeSQL(sqlQuery, 100);
      if (result.success) {
        setQueryResult(result.results || result.message || "Query executed successfully");
        if (result.affected_rows !== undefined) {
          toast.success(`${result.affected_rows} rows affected`);
        }
      } else {
        setQueryResult(`Error: ${result.error}`);
        toast.error(result.error || "Query failed");
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Query failed";
      setQueryResult(`Error: ${message}`);
      toast.error(message);
    } finally {
      setIsQueryRunning(false);
    }
  };

  const tables = tablesData?.tables || [];

  return (
    <>
      <Header />
      <PageContainer>
        <PageHeader
          title="CSV to SQL"
          description="Upload CSV files and query them with SQL"
          icon={<Database className="h-6 w-6" />}
        />

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="upload" className="gap-2">
              <FileSpreadsheet className="h-4 w-4" />
              Upload
            </TabsTrigger>
            <TabsTrigger value="tables" className="gap-2">
              <Database className="h-4 w-4" />
              Tables
              {tables.length > 0 && (
                <span className="ml-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs">
                  {tables.length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="query" className="gap-2">
              <Code className="h-4 w-4" />
              Query
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Upload CSV</CardTitle>
                <CardDescription>
                  Upload a CSV file to create a PostgreSQL table that you can query with SQL
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CSVUpload
                  onUpload={handleUpload}
                  isUploading={uploadMutation.isPending}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tables" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Your Tables</CardTitle>
                <CardDescription>
                  Manage your uploaded CSV tables
                </CardDescription>
              </CardHeader>
              <CardContent>
                <TableList
                  tables={tables}
                  isLoading={tablesLoading}
                  onDelete={handleDelete}
                  onViewSample={handleViewSample}
                  deletingTable={deletingTable}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="query" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>SQL Query</CardTitle>
                <CardDescription>
                  Write and execute SQL queries on your CSV tables. Tables are in the{" "}
                  <code className="rounded bg-muted px-1 py-0.5 text-xs">csv_data</code> schema.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {tables.length > 0 && (
                  <div className="rounded-lg bg-muted/50 p-3">
                    <p className="text-xs font-medium text-muted-foreground mb-2">
                      Available tables:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {tables.map((table: CSVTable) => (
                        <button
                          key={table.table_name}
                          onClick={() =>
                            setSqlQuery(
                              `SELECT * FROM csv_data.${table.table_name} LIMIT 10`
                            )
                          }
                          className="rounded-md bg-background px-2 py-1 text-xs font-mono hover:bg-primary/10 transition-colors"
                        >
                          {table.table_name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <Textarea
                  value={sqlQuery}
                  onChange={(e) => setSqlQuery(e.target.value)}
                  placeholder="SELECT * FROM csv_data.your_table LIMIT 10"
                  className="font-mono min-h-[120px]"
                />

                <Button
                  onClick={handleRunQuery}
                  disabled={isQueryRunning || !sqlQuery.trim()}
                  className="gap-2"
                >
                  {isQueryRunning ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Run Query
                    </>
                  )}
                </Button>

                {queryResult && (
                  <div className="rounded-lg border bg-muted/30 p-4">
                    <p className="text-xs font-medium text-muted-foreground mb-2">
                      Result:
                    </p>
                    <pre className="text-sm font-mono whitespace-pre-wrap overflow-x-auto max-h-[400px] overflow-y-auto">
                      {queryResult}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </PageContainer>

      {/* Preview Dialog */}
      <Dialog open={!!previewData} onOpenChange={() => setPreviewData(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Preview: {previewData?.tableName}</DialogTitle>
            <DialogDescription>
              Sample data from the table (first 10 rows)
            </DialogDescription>
          </DialogHeader>
          <div className="overflow-auto max-h-[60vh]">
            <pre className="text-sm font-mono whitespace-pre-wrap">
              {previewData?.data}
            </pre>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
