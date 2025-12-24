"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listKnowledgeBases,
  getKnowledgeBase,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  listDocuments,
  uploadDocument,
  uploadDocumentsBatch,
  deleteDocument,
  searchKnowledgeBase,
} from "@/lib/api/knowledge";
import type {
  CreateKnowledgeBaseRequest,
  UpdateKnowledgeBaseRequest,
  SearchKnowledgeBaseRequest,
} from "@/types/knowledge";

// ==================== Query Keys ====================

export const knowledgeKeys = {
  all: ["knowledge-bases"] as const,
  list: () => [...knowledgeKeys.all, "list"] as const,
  detail: (id: string) => [...knowledgeKeys.all, "detail", id] as const,
  documents: (kbId: string) =>
    [...knowledgeKeys.all, "documents", kbId] as const,
};

// ==================== Knowledge Base Hooks ====================

export function useKnowledgeBases() {
  return useQuery({
    queryKey: knowledgeKeys.list(),
    queryFn: listKnowledgeBases,
  });
}

export function useKnowledgeBase(kbId: string) {
  return useQuery({
    queryKey: knowledgeKeys.detail(kbId),
    queryFn: () => getKnowledgeBase(kbId),
    enabled: !!kbId,
  });
}

export function useCreateKnowledgeBase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateKnowledgeBaseRequest) => createKnowledgeBase(data),
    onSuccess: (kb) => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.list() });
      toast.success(`Knowledge base "${kb.name}" created`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useUpdateKnowledgeBase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: UpdateKnowledgeBaseRequest;
    }) => updateKnowledgeBase(id, data),
    onSuccess: (kb) => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.list() });
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.detail(kb.id) });
      toast.success("Knowledge base updated");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useDeleteKnowledgeBase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (kbId: string) => deleteKnowledgeBase(kbId),
    onSuccess: (_, kbId) => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.list() });
      queryClient.removeQueries({ queryKey: knowledgeKeys.detail(kbId) });
      toast.success("Knowledge base deleted");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ==================== Document Hooks ====================

export function useDocuments(kbId: string) {
  return useQuery({
    queryKey: knowledgeKeys.documents(kbId),
    queryFn: () => listDocuments(kbId),
    enabled: !!kbId,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ kbId, file }: { kbId: string; file: File }) =>
      uploadDocument(kbId, file),
    onSuccess: (result, { kbId }) => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.documents(kbId) });
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.detail(kbId) });
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.list() });
      if (result.document.status === "indexed") {
        toast.success(`"${result.document.filename}" indexed successfully`);
      } else if (result.document.status === "error") {
        toast.error(`Failed to index "${result.document.filename}"`);
      }
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useUploadDocumentsBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ kbId, files }: { kbId: string; files: File[] }) =>
      uploadDocumentsBatch(kbId, files),
    onSuccess: (result, { kbId }) => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.documents(kbId) });
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.detail(kbId) });
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.list() });

      if (result.error_count === 0) {
        toast.success(
          `${result.success_count} document${result.success_count !== 1 ? "s" : ""} uploaded`
        );
      } else {
        toast.warning(
          `${result.success_count} uploaded, ${result.error_count} failed`
        );
      }
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ kbId, docId }: { kbId: string; docId: string }) =>
      deleteDocument(kbId, docId),
    onSuccess: (_, { kbId }) => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.documents(kbId) });
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.detail(kbId) });
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.list() });
      toast.success("Document deleted");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ==================== Search Hook ====================

export function useSearchKnowledgeBase() {
  return useMutation({
    mutationFn: ({
      kbId,
      request,
    }: {
      kbId: string;
      request: SearchKnowledgeBaseRequest;
    }) => searchKnowledgeBase(kbId, request),
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
