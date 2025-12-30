/**
 * Knowledge Base API client.
 */

import { apiClient } from "./client";
import type {
  KnowledgeBase,
  KnowledgeBaseListResponse,
  CreateKnowledgeBaseRequest,
  UpdateKnowledgeBaseRequest,
  KnowledgeDocument,
  KnowledgeDocumentListResponse,
  UploadDocumentResponse,
  BatchUploadResponse,
  SearchKnowledgeBaseRequest,
  SearchKnowledgeBaseResponse,
  UpdateDocumentMetadataRequest,
  DocumentTagListResponse,
  DocumentCategoryListResponse,
} from "@/types/knowledge";

// ==================== Knowledge Base API ====================

export async function createKnowledgeBase(
  data: CreateKnowledgeBaseRequest
): Promise<KnowledgeBase> {
  const response = await apiClient.post<KnowledgeBase>("/knowledge-bases", data);
  return response.data;
}

export async function listKnowledgeBases(): Promise<KnowledgeBaseListResponse> {
  const response = await apiClient.get<KnowledgeBaseListResponse>("/knowledge-bases");
  return response.data;
}

export async function getKnowledgeBase(id: string): Promise<KnowledgeBase> {
  const response = await apiClient.get<KnowledgeBase>(`/knowledge-bases/${id}`);
  return response.data;
}

export async function updateKnowledgeBase(
  id: string,
  data: UpdateKnowledgeBaseRequest
): Promise<KnowledgeBase> {
  const response = await apiClient.patch<KnowledgeBase>(`/knowledge-bases/${id}`, data);
  return response.data;
}

export async function deleteKnowledgeBase(id: string): Promise<void> {
  await apiClient.delete(`/knowledge-bases/${id}`);
}

// ==================== Document API ====================

export interface ListDocumentsOptions {
  status?: string;
  category?: string;
  tags?: string[];
}

export async function listDocuments(
  kbId: string,
  options?: ListDocumentsOptions
): Promise<KnowledgeDocumentListResponse> {
  const params = new URLSearchParams();
  if (options?.status) params.append("status_filter", options.status);
  if (options?.category) params.append("category", options.category);
  if (options?.tags?.length) params.append("tags", options.tags.join(","));

  const queryString = params.toString();
  const url = `/knowledge-bases/${kbId}/documents${queryString ? `?${queryString}` : ""}`;

  const response = await apiClient.get<KnowledgeDocumentListResponse>(url);
  return response.data;
}

export async function uploadDocument(
  kbId: string,
  file: File
): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<UploadDocumentResponse>(
    `/knowledge-bases/${kbId}/documents`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return response.data;
}

export async function uploadDocumentsBatch(
  kbId: string,
  files: File[]
): Promise<BatchUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await apiClient.post<BatchUploadResponse>(
    `/knowledge-bases/${kbId}/documents/batch`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return response.data;
}

export async function deleteDocument(
  kbId: string,
  docId: string
): Promise<void> {
  await apiClient.delete(`/knowledge-bases/${kbId}/documents/${docId}`);
}

// ==================== Document Preview API ====================

export interface DocumentPreviewResponse {
  type: "image" | "text";
  url?: string;  // For images
  content?: string;  // For text
  filename: string;
  file_type: string;
  file_size: number;
  page_count?: number;
  word_count?: number;
  has_tables?: boolean;
  has_images?: boolean;
  tables?: Array<{
    markdown: string;
    page_number?: number;
    sheet_name?: string;
    row_count: number;
    col_count: number;
  }>;
  metadata?: Record<string, unknown>;
}

export async function getDocumentPreview(
  kbId: string,
  docId: string
): Promise<DocumentPreviewResponse> {
  const response = await apiClient.get<DocumentPreviewResponse>(
    `/knowledge-bases/${kbId}/documents/${docId}/preview`
  );
  return response.data;
}

export function getDocumentDownloadUrl(kbId: string, docId: string): string {
  return `/api/v1/knowledge-bases/${kbId}/documents/${docId}/download`;
}

// ==================== Search API ====================

export async function searchKnowledgeBase(
  kbId: string,
  request: SearchKnowledgeBaseRequest
): Promise<SearchKnowledgeBaseResponse> {
  const response = await apiClient.post<SearchKnowledgeBaseResponse>(
    `/knowledge-bases/${kbId}/search`,
    request
  );
  return response.data;
}

// ==================== Document Metadata API ====================

export async function updateDocumentMetadata(
  kbId: string,
  docId: string,
  data: UpdateDocumentMetadataRequest
): Promise<KnowledgeDocument> {
  const response = await apiClient.patch<KnowledgeDocument>(
    `/knowledge-bases/${kbId}/documents/${docId}/metadata`,
    data
  );
  return response.data;
}

export async function getDocumentTags(
  kbId: string,
  prefix?: string,
  limit: number = 20
): Promise<DocumentTagListResponse> {
  const params = new URLSearchParams();
  if (prefix) params.append("prefix", prefix);
  params.append("limit", limit.toString());

  const response = await apiClient.get<DocumentTagListResponse>(
    `/knowledge-bases/${kbId}/tags?${params.toString()}`
  );
  return response.data;
}

export async function getDocumentCategories(
  kbId: string
): Promise<DocumentCategoryListResponse> {
  const response = await apiClient.get<DocumentCategoryListResponse>(
    `/knowledge-bases/${kbId}/categories`
  );
  return response.data;
}
