/**
 * CSV-SQL API client.
 *
 * Provides functions for uploading CSV files and querying them via SQL.
 */

import { apiClient } from "./client";

// ==================== Types ====================

export interface ColumnInfo {
  name: string;
  type: string;
  original?: string;
}

export interface CSVTable {
  table_name: string;
  original_filename?: string;
  row_count?: number;
  column_count?: number;
  columns?: ColumnInfo[];
  created_at?: string;
  updated_at?: string;
}

export interface CSVTableListResponse {
  tables: CSVTable[];
  total: number;
}

export interface UploadCSVResponse {
  success: boolean;
  table_name?: string;
  schema?: string;
  full_path?: string;
  row_count?: number;
  column_count?: number;
  columns?: ColumnInfo[];
  message?: string;
  error?: string;
}

export interface TableSchemaResponse {
  success: boolean;
  table_name?: string;
  schema?: string;
  full_path?: string;
  columns?: ColumnInfo[];
  row_count?: number;
  original_filename?: string;
  created_at?: string;
  error?: string;
}

export interface SampleDataResponse {
  success: boolean;
  table_name?: string;
  sample?: string;
  row_count?: number;
  error?: string;
}

export interface ExecuteSQLResponse {
  success: boolean;
  query_type?: string;
  row_count?: number;
  affected_rows?: number;
  results?: string;
  query?: string;
  message?: string;
  error?: string;
}

export interface DeleteTableResponse {
  success: boolean;
  message?: string;
  error?: string;
}

// ==================== API Functions ====================

/**
 * Upload a CSV file and create a PostgreSQL table.
 */
export async function uploadCSV(
  file: File,
  tableName: string,
  ifExists: "fail" | "replace" | "append" = "fail"
): Promise<UploadCSVResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("table_name", tableName);
  formData.append("if_exists", ifExists);

  const response = await apiClient.post<UploadCSVResponse>(
    "/csv-sql/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
}

/**
 * List all CSV tables for the current user.
 */
export async function listCSVTables(): Promise<CSVTableListResponse> {
  const response = await apiClient.get<CSVTableListResponse>("/csv-sql/tables");
  return response.data;
}

/**
 * Get the schema for a specific table.
 */
export async function getTableSchema(
  tableName: string
): Promise<TableSchemaResponse> {
  const response = await apiClient.get<TableSchemaResponse>(
    `/csv-sql/tables/${encodeURIComponent(tableName)}/schema`
  );
  return response.data;
}

/**
 * Get sample data from a table.
 */
export async function getSampleData(
  tableName: string,
  rows: number = 5
): Promise<SampleDataResponse> {
  const response = await apiClient.get<SampleDataResponse>(
    `/csv-sql/tables/${encodeURIComponent(tableName)}/sample`,
    { params: { rows } }
  );
  return response.data;
}

/**
 * Execute a SQL query on the CSV tables.
 */
export async function executeSQL(
  query: string,
  limit: number = 100
): Promise<ExecuteSQLResponse> {
  const response = await apiClient.post<ExecuteSQLResponse>("/csv-sql/query", {
    query,
    limit,
  });
  return response.data;
}

/**
 * Delete a CSV table.
 */
export async function deleteCSVTable(
  tableName: string
): Promise<DeleteTableResponse> {
  const response = await apiClient.delete<DeleteTableResponse>(
    `/csv-sql/tables/${encodeURIComponent(tableName)}`
  );
  return response.data;
}
