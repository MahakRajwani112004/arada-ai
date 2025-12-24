/**
 * Knowledge Base API client.
 */

import { apiClient } from "./client";
import type {
  KnowledgeBase,
  KnowledgeBaseListResponse,
  CreateKnowledgeBaseRequest,
  UpdateKnowledgeBaseRequest,
  KnowledgeDocumentListResponse,
  UploadDocumentResponse,
  BatchUploadResponse,
  SearchKnowledgeBaseRequest,
  SearchKnowledgeBaseResponse,
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

export async function listDocuments(
  kbId: string
): Promise<KnowledgeDocumentListResponse> {
  const response = await apiClient.get<KnowledgeDocumentListResponse>(
    `/knowledge-bases/${kbId}/documents`
  );
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
