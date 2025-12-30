/**
 * Chunked upload client for resumable file uploads.
 *
 * Features:
 * - Automatic chunking for large files
 * - Resume support for failed uploads
 * - Progress tracking at chunk level
 * - Retry logic for failed chunks
 */

import { apiClient } from "./api/client";

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB chunks
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

export interface UploadProgress {
  uploadId: string;
  filename: string;
  fileSize: number;
  totalChunks: number;
  uploadedChunks: number;
  progress: number; // 0-100
  status: "initializing" | "uploading" | "completing" | "completed" | "failed" | "cancelled";
  error?: string;
}

export interface UploadSession {
  uploadId: string;
  filename: string;
  fileSize: number;
  chunkSize: number;
  totalChunks: number;
  status: string;
}

export interface ChunkUploadResult {
  uploadId: string;
  chunkNum: number;
  receivedChunks: number;
  totalChunks: number;
  status: string;
}

export interface UploadCompleteResult {
  document: {
    id: string;
    filename: string;
    fileType: string;
    fileSize: number;
    status: string;
    createdAt: string;
  };
  upload: {
    uploadId: string;
    status: string;
    checksum: string;
  };
  message: string;
}

export interface UploadStatusResult {
  uploadId: string;
  filename: string;
  fileSize: number;
  chunkSize: number;
  totalChunks: number;
  receivedChunks: number[];
  missingChunks: number[];
  status: string;
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
  errorMessage: string | null;
}

export type ProgressCallback = (progress: UploadProgress) => void;

/**
 * Initialize a chunked upload session.
 */
async function initUpload(
  kbId: string,
  file: File
): Promise<UploadSession> {
  const formData = new FormData();
  formData.append("filename", file.name);
  formData.append("file_size", file.size.toString());
  formData.append("content_type", file.type || "application/octet-stream");

  const response = await apiClient.post<{
    upload_id: string;
    filename: string;
    file_size: number;
    chunk_size: number;
    total_chunks: number;
    status: string;
  }>(`/knowledge-bases/${kbId}/documents/upload/init`, formData);

  return {
    uploadId: response.data.upload_id,
    filename: response.data.filename,
    fileSize: response.data.file_size,
    chunkSize: response.data.chunk_size,
    totalChunks: response.data.total_chunks,
    status: response.data.status,
  };
}

/**
 * Upload a single chunk with retry logic.
 */
async function uploadChunk(
  kbId: string,
  uploadId: string,
  chunkNum: number,
  chunkData: Blob,
  retries = MAX_RETRIES
): Promise<ChunkUploadResult> {
  const formData = new FormData();
  formData.append("chunk", chunkData, `chunk_${chunkNum}`);

  try {
    const response = await apiClient.post<{
      upload_id: string;
      chunk_num: number;
      received_chunks: number;
      total_chunks: number;
      status: string;
    }>(
      `/knowledge-bases/${kbId}/documents/upload/${uploadId}/chunk/${chunkNum}`,
      formData
    );

    return {
      uploadId: response.data.upload_id,
      chunkNum: response.data.chunk_num,
      receivedChunks: response.data.received_chunks,
      totalChunks: response.data.total_chunks,
      status: response.data.status,
    };
  } catch (error) {
    if (retries > 0) {
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
      return uploadChunk(kbId, uploadId, chunkNum, chunkData, retries - 1);
    }
    throw error;
  }
}

/**
 * Complete the upload and trigger indexing.
 */
async function completeUpload(
  kbId: string,
  uploadId: string
): Promise<UploadCompleteResult> {
  const response = await apiClient.post<{
    document: {
      id: string;
      filename: string;
      file_type: string;
      file_size: number;
      status: string;
      created_at: string;
    };
    upload: {
      upload_id: string;
      status: string;
      checksum: string;
    };
    message: string;
  }>(`/knowledge-bases/${kbId}/documents/upload/${uploadId}/complete`);

  return {
    document: {
      id: response.data.document.id,
      filename: response.data.document.filename,
      fileType: response.data.document.file_type,
      fileSize: response.data.document.file_size,
      status: response.data.document.status,
      createdAt: response.data.document.created_at,
    },
    upload: {
      uploadId: response.data.upload.upload_id,
      status: response.data.upload.status,
      checksum: response.data.upload.checksum,
    },
    message: response.data.message,
  };
}

/**
 * Get the status of an upload session.
 */
export async function getUploadStatus(
  kbId: string,
  uploadId: string
): Promise<UploadStatusResult> {
  const response = await apiClient.get<{
    upload_id: string;
    filename: string;
    file_size: number;
    chunk_size: number;
    total_chunks: number;
    received_chunks: number[];
    missing_chunks: number[];
    status: string;
    created_at: string;
    updated_at: string;
    completed_at: string | null;
    error_message: string | null;
  }>(`/knowledge-bases/${kbId}/documents/upload/${uploadId}/status`);

  return {
    uploadId: response.data.upload_id,
    filename: response.data.filename,
    fileSize: response.data.file_size,
    chunkSize: response.data.chunk_size,
    totalChunks: response.data.total_chunks,
    receivedChunks: response.data.received_chunks,
    missingChunks: response.data.missing_chunks,
    status: response.data.status,
    createdAt: response.data.created_at,
    updatedAt: response.data.updated_at,
    completedAt: response.data.completed_at,
    errorMessage: response.data.error_message,
  };
}

/**
 * Cancel an upload session.
 */
export async function cancelUpload(
  kbId: string,
  uploadId: string
): Promise<void> {
  await apiClient.delete(`/knowledge-bases/${kbId}/documents/upload/${uploadId}`);
}

/**
 * Upload a file with chunked upload support.
 *
 * For small files (< chunk size), uses a single chunk.
 * For large files, splits into chunks and uploads with progress tracking.
 */
export async function uploadFileChunked(
  kbId: string,
  file: File,
  onProgress?: ProgressCallback,
  abortSignal?: AbortSignal
): Promise<UploadCompleteResult> {
  let uploadId: string | null = null;

  const updateProgress = (
    status: UploadProgress["status"],
    uploadedChunks: number,
    totalChunks: number,
    error?: string
  ) => {
    if (onProgress) {
      onProgress({
        uploadId: uploadId || "",
        filename: file.name,
        fileSize: file.size,
        totalChunks,
        uploadedChunks,
        progress: totalChunks > 0 ? Math.round((uploadedChunks / totalChunks) * 100) : 0,
        status,
        error,
      });
    }
  };

  try {
    // Check if cancelled
    if (abortSignal?.aborted) {
      throw new Error("Upload cancelled");
    }

    // Initialize upload
    updateProgress("initializing", 0, 0);
    const session = await initUpload(kbId, file);
    uploadId = session.uploadId;

    updateProgress("uploading", 0, session.totalChunks);

    // Upload chunks
    let uploadedCount = 0;
    for (let chunkNum = 0; chunkNum < session.totalChunks; chunkNum++) {
      // Check if cancelled
      if (abortSignal?.aborted) {
        await cancelUpload(kbId, uploadId);
        throw new Error("Upload cancelled");
      }

      const start = chunkNum * session.chunkSize;
      const end = Math.min(start + session.chunkSize, file.size);
      const chunk = file.slice(start, end);

      await uploadChunk(kbId, uploadId, chunkNum, chunk);
      uploadedCount++;
      updateProgress("uploading", uploadedCount, session.totalChunks);
    }

    // Complete upload
    updateProgress("completing", session.totalChunks, session.totalChunks);
    const result = await completeUpload(kbId, uploadId);
    updateProgress("completed", session.totalChunks, session.totalChunks);

    return result;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Upload failed";
    updateProgress("failed", 0, 0, errorMessage);

    // Try to cancel upload on error
    if (uploadId) {
      try {
        await cancelUpload(kbId, uploadId);
      } catch {
        // Ignore cancel errors
      }
    }

    throw error;
  }
}

/**
 * Resume a failed upload.
 *
 * Gets the status of an existing upload and uploads only missing chunks.
 */
export async function resumeUpload(
  kbId: string,
  uploadId: string,
  file: File,
  onProgress?: ProgressCallback,
  abortSignal?: AbortSignal
): Promise<UploadCompleteResult> {
  const updateProgress = (
    status: UploadProgress["status"],
    uploadedChunks: number,
    totalChunks: number,
    error?: string
  ) => {
    if (onProgress) {
      onProgress({
        uploadId,
        filename: file.name,
        fileSize: file.size,
        totalChunks,
        uploadedChunks,
        progress: totalChunks > 0 ? Math.round((uploadedChunks / totalChunks) * 100) : 0,
        status,
        error,
      });
    }
  };

  try {
    // Get current status
    const status = await getUploadStatus(kbId, uploadId);

    if (status.status === "completed") {
      updateProgress("completed", status.totalChunks, status.totalChunks);
      throw new Error("Upload already completed");
    }

    if (status.status === "failed" || status.status === "expired") {
      throw new Error(`Cannot resume upload: ${status.status}`);
    }

    const missingChunks = status.missingChunks;
    let uploadedCount = status.receivedChunks.length;
    updateProgress("uploading", uploadedCount, status.totalChunks);

    // Upload missing chunks
    for (const chunkNum of missingChunks) {
      if (abortSignal?.aborted) {
        throw new Error("Upload cancelled");
      }

      const start = chunkNum * status.chunkSize;
      const end = Math.min(start + status.chunkSize, file.size);
      const chunk = file.slice(start, end);

      await uploadChunk(kbId, uploadId, chunkNum, chunk);
      uploadedCount++;
      updateProgress("uploading", uploadedCount, status.totalChunks);
    }

    // Complete upload
    updateProgress("completing", status.totalChunks, status.totalChunks);
    const result = await completeUpload(kbId, uploadId);
    updateProgress("completed", status.totalChunks, status.totalChunks);

    return result;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Resume failed";
    updateProgress("failed", 0, 0, errorMessage);
    throw error;
  }
}

/**
 * Check if a file needs chunked upload.
 */
export function needsChunkedUpload(file: File): boolean {
  return file.size > CHUNK_SIZE;
}

/**
 * Get the recommended number of chunks for a file.
 */
export function getChunkCount(fileSize: number): number {
  return Math.ceil(fileSize / CHUNK_SIZE);
}
