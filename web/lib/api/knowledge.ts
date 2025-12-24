/**
 * Knowledge Base API client.
 */

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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ==================== Knowledge Base API ====================

export async function createKnowledgeBase(
  data: CreateKnowledgeBaseRequest
): Promise<KnowledgeBase> {
  const response = await fetch(`${API_BASE}/api/v1/knowledge-bases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to create knowledge base");
  }

  return response.json();
}

export async function listKnowledgeBases(): Promise<KnowledgeBaseListResponse> {
  const response = await fetch(`${API_BASE}/api/v1/knowledge-bases`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to fetch knowledge bases");
  }

  return response.json();
}

export async function getKnowledgeBase(id: string): Promise<KnowledgeBase> {
  const response = await fetch(`${API_BASE}/api/v1/knowledge-bases/${id}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to fetch knowledge base");
  }

  return response.json();
}

export async function updateKnowledgeBase(
  id: string,
  data: UpdateKnowledgeBaseRequest
): Promise<KnowledgeBase> {
  const response = await fetch(`${API_BASE}/api/v1/knowledge-bases/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to update knowledge base");
  }

  return response.json();
}

export async function deleteKnowledgeBase(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/knowledge-bases/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to delete knowledge base");
  }
}

// ==================== Document API ====================

export async function listDocuments(
  kbId: string
): Promise<KnowledgeDocumentListResponse> {
  const response = await fetch(
    `${API_BASE}/api/v1/knowledge-bases/${kbId}/documents`
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to fetch documents");
  }

  return response.json();
}

export async function uploadDocument(
  kbId: string,
  file: File
): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${API_BASE}/api/v1/knowledge-bases/${kbId}/documents`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to upload document");
  }

  return response.json();
}

export async function uploadDocumentsBatch(
  kbId: string,
  files: File[]
): Promise<BatchUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch(
    `${API_BASE}/api/v1/knowledge-bases/${kbId}/documents/batch`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to upload documents");
  }

  return response.json();
}

export async function deleteDocument(
  kbId: string,
  docId: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/v1/knowledge-bases/${kbId}/documents/${docId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to delete document");
  }
}

// ==================== Search API ====================

export async function searchKnowledgeBase(
  kbId: string,
  request: SearchKnowledgeBaseRequest
): Promise<SearchKnowledgeBaseResponse> {
  const response = await fetch(
    `${API_BASE}/api/v1/knowledge-bases/${kbId}/search`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Search failed");
  }

  return response.json();
}
