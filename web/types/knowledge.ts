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
  // Metadata fields
  tags: string[];
  category: string | null;
  author: string | null;
  custom_metadata: Record<string, unknown>;
}

export interface UpdateDocumentMetadataRequest {
  tags?: string[];
  category?: string;
  author?: string;
  custom_metadata?: Record<string, unknown>;
}

export interface DocumentTag {
  tag: string;
  usage_count: number;
}

export interface DocumentTagListResponse {
  tags: DocumentTag[];
  total: number;
}

export interface DocumentCategoryListResponse {
  categories: string[];
  total: number;
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

export const SUPPORTED_FILE_TYPES = [
  "pdf", "docx", "doc", "pptx", "ppt",
  "xlsx", "xls", "csv",
  "txt", "md", "markdown", "html", "htm",
  "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp"
] as const;
export type SupportedFileType = (typeof SUPPORTED_FILE_TYPES)[number];

export const FILE_TYPE_LABELS: Record<SupportedFileType, string> = {
  pdf: "PDF Document",
  docx: "Word Document",
  doc: "Word Document (Legacy)",
  pptx: "PowerPoint",
  ppt: "PowerPoint (Legacy)",
  xlsx: "Excel Spreadsheet",
  xls: "Excel (Legacy)",
  csv: "CSV Data",
  txt: "Text File",
  md: "Markdown",
  markdown: "Markdown",
  html: "HTML Page",
  htm: "HTML Page",
  jpg: "JPEG Image",
  jpeg: "JPEG Image",
  png: "PNG Image",
  gif: "GIF Image",
  bmp: "Bitmap Image",
  tiff: "TIFF Image",
  tif: "TIFF Image",
  webp: "WebP Image",
};

// File type categories for preview handling
export type FileTypeCategory = "pdf" | "image" | "text" | "spreadsheet" | "presentation" | "document";

export function getFileTypeCategory(fileType: string): FileTypeCategory {
  const type = fileType.toLowerCase();
  if (type === "pdf") return "pdf";
  if (["jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp"].includes(type)) return "image";
  if (["txt", "md", "markdown", "html", "htm"].includes(type)) return "text";
  if (["xlsx", "xls", "csv"].includes(type)) return "spreadsheet";
  if (["pptx", "ppt"].includes(type)) return "presentation";
  return "document";
}

export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB (increased for larger documents)

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
