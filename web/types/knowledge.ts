/**
 * Knowledge Base types for the frontend.
 */

// ==================== Knowledge Base Types ====================

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  collection_name: string;
  embedding_model: string;
  document_count: number;
  chunk_count: number;
  status: KnowledgeBaseStatus;
  error_message: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export type KnowledgeBaseStatus = "active" | "indexing" | "error";

export interface KnowledgeBaseListResponse {
  knowledge_bases: KnowledgeBase[];
  total: number;
}

export interface CreateKnowledgeBaseRequest {
  name: string;
  description?: string;
  embedding_model?: string;
}

export interface UpdateKnowledgeBaseRequest {
  name?: string;
  description?: string;
}

// ==================== Document Types ====================

export interface KnowledgeDocument {
  id: string;
  knowledge_base_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  status: DocumentStatus;
  error_message: string | null;
  created_at: string;
  indexed_at: string | null;
}

export type DocumentStatus = "pending" | "processing" | "indexed" | "error";

export interface KnowledgeDocumentListResponse {
  documents: KnowledgeDocument[];
  total: number;
}

export interface UploadDocumentResponse {
  document: KnowledgeDocument;
  message: string;
}

export interface BatchUploadResponse {
  documents: KnowledgeDocument[];
  success_count: number;
  error_count: number;
  errors: string[];
}

// ==================== Search Types ====================

export interface SearchKnowledgeBaseRequest {
  query: string;
  top_k?: number;
  similarity_threshold?: number;
}

export interface SearchResultItem {
  content: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface SearchKnowledgeBaseResponse {
  results: SearchResultItem[];
  query: string;
  total_results: number;
}

// ==================== UI Helper Types ====================

export interface KnowledgeBaseFormData {
  name: string;
  description: string;
  embedding_model: string;
}

export const DEFAULT_KB_FORM_DATA: KnowledgeBaseFormData = {
  name: "",
  description: "",
  embedding_model: "text-embedding-3-small",
};

export const SUPPORTED_FILE_TYPES = ["pdf", "txt", "md", "docx"] as const;
export type SupportedFileType = (typeof SUPPORTED_FILE_TYPES)[number];

export const FILE_TYPE_LABELS: Record<SupportedFileType, string> = {
  pdf: "PDF Document",
  txt: "Text File",
  md: "Markdown",
  docx: "Word Document",
};

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function getDocumentStatusLabel(status: DocumentStatus): string {
  switch (status) {
    case "pending":
      return "Pending";
    case "processing":
      return "Processing";
    case "indexed":
      return "Indexed";
    case "error":
      return "Error";
  }
}

export function getDocumentStatusColor(
  status: DocumentStatus
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "pending":
      return "outline";
    case "processing":
      return "secondary";
    case "indexed":
      return "default";
    case "error":
      return "destructive";
  }
}
