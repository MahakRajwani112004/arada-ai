"use client";

import { useState, useCallback, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listAllConversations,
  listAgentConversations,
  getConversation,
  createConversation,
  updateConversation,
  deleteConversation,
  archiveConversation,
  streamMessage,
  cancelStream,
} from "@/lib/api/conversations";
import type {
  StreamEvent,
  StreamingState,
  ProgressItem,
  CreateConversationRequest,
} from "@/types/conversation";

// ============================================================================
// Query Keys
// ============================================================================

export const conversationKeys = {
  all: ["conversations"] as const,
  lists: () => [...conversationKeys.all, "list"] as const,
  listAll: () => [...conversationKeys.lists(), "all"] as const,
  listAgent: (agentId: string) =>
    [...conversationKeys.lists(), "agent", agentId] as const,
  details: () => [...conversationKeys.all, "detail"] as const,
  detail: (id: string) => [...conversationKeys.details(), id] as const,
};

// ============================================================================
// List Hooks
// ============================================================================

/**
 * List all conversations for the current user.
 */
export function useAllConversations() {
  return useQuery({
    queryKey: conversationKeys.listAll(),
    queryFn: () => listAllConversations(),
  });
}

/**
 * List conversations for a specific agent.
 */
export function useAgentConversations(agentId: string) {
  return useQuery({
    queryKey: conversationKeys.listAgent(agentId),
    queryFn: () => listAgentConversations(agentId),
    enabled: !!agentId,
  });
}

// ============================================================================
// Detail Hook
// ============================================================================

/**
 * Get a single conversation with messages.
 */
export function useConversation(conversationId: string | null) {
  return useQuery({
    queryKey: conversationKeys.detail(conversationId!),
    queryFn: () => getConversation(conversationId!),
    enabled: !!conversationId,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Create a new conversation.
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      agentId,
      request,
    }: {
      agentId: string;
      request?: CreateConversationRequest;
    }) => createConversation(agentId, request),
    onSuccess: (_, { agentId }) => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.listAll() });
      queryClient.invalidateQueries({
        queryKey: conversationKeys.listAgent(agentId),
      });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

/**
 * Update (rename) a conversation.
 */
export function useUpdateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) =>
      updateConversation(id, { title }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() });
      toast.success("Conversation renamed");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

/**
 * Delete a conversation.
 */
export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() });
      toast.success("Conversation deleted");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

/**
 * Archive a conversation.
 */
export function useArchiveConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: archiveConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() });
      toast.success("Conversation archived");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ============================================================================
// Streaming Chat Hook
// ============================================================================

/**
 * Hook for streaming chat with progress events.
 *
 * @example
 * ```tsx
 * function ChatComponent({ conversationId }) {
 *   const {
 *     state,
 *     sendMessage,
 *     cancelMessage,
 *     clearState,
 *   } = useStreamingChat(conversationId);
 *
 *   const handleSend = async () => {
 *     await sendMessage("Hello!");
 *   };
 *
 *   return (
 *     <div>
 *       {state.status === "generating" && (
 *         <StreamingMessage content={state.streamedContent} />
 *       )}
 *       {state.progress.map((p, i) => (
 *         <ProgressIndicator key={i} item={p} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useStreamingChat(conversationId: string | null) {
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  const [state, setState] = useState<StreamingState>({
    status: "idle",
    progress: [],
    streamedContent: "",
  });

  const updateProgress = useCallback(
    (item: ProgressItem, action: "add" | "update") => {
      setState((prev) => {
        if (action === "add") {
          return {
            ...prev,
            progress: [...prev.progress, item],
          };
        }
        // Update last item of same type
        const updated = [...prev.progress];
        const lastIndex = updated
          .map((p, i) => (p.type === item.type ? i : -1))
          .filter((i) => i >= 0)
          .pop();
        if (lastIndex !== undefined && lastIndex >= 0) {
          updated[lastIndex] = { ...updated[lastIndex], ...item };
        }
        return { ...prev, progress: updated };
      });
    },
    []
  );

  const handleEvent = useCallback(
    (event: StreamEvent) => {
      switch (event.type) {
        case "thinking":
          setState((prev) => ({ ...prev, status: "thinking" }));
          updateProgress(
            {
              type: "thinking",
              status: "active",
              detail: event.data.step as string | undefined,
            },
            "add"
          );
          break;

        case "retrieving":
          setState((prev) => ({ ...prev, status: "retrieving" }));
          updateProgress(
            {
              type: "retrieving",
              status: "active",
              name: event.data.knowledge_base_name as string,
            },
            "add"
          );
          break;

        case "retrieved":
          updateProgress(
            {
              type: "retrieving",
              status: "complete",
              detail: `${event.data.document_count} documents`,
            },
            "update"
          );
          break;

        case "tool_start":
          setState((prev) => ({ ...prev, status: "tools" }));
          updateProgress(
            {
              type: "tool",
              status: "active",
              name: event.data.tool_name as string,
            },
            "add"
          );
          break;

        case "tool_end":
          updateProgress(
            {
              type: "tool",
              status: event.data.success ? "complete" : "error",
              name: event.data.tool_name as string,
            },
            "update"
          );
          break;

        case "mcp_start":
          setState((prev) => ({ ...prev, status: "tools" }));
          updateProgress(
            {
              type: "mcp",
              status: "active",
              name: `${event.data.server_name}:${event.data.tool_name}`,
            },
            "add"
          );
          break;

        case "mcp_end":
          updateProgress(
            {
              type: "mcp",
              status: event.data.success ? "complete" : "error",
              name: `${event.data.server_name}:${event.data.tool_name}`,
            },
            "update"
          );
          break;

        case "skill_start":
          updateProgress(
            {
              type: "skill",
              status: "active",
              name: event.data.skill_name as string,
            },
            "add"
          );
          break;

        case "skill_end":
          updateProgress(
            {
              type: "skill",
              status: "complete",
              name: event.data.skill_name as string,
            },
            "update"
          );
          break;

        case "generating":
          setState((prev) => ({ ...prev, status: "generating" }));
          updateProgress({ type: "generating", status: "active" }, "add");
          break;

        case "chunk":
          setState((prev) => ({
            ...prev,
            streamedContent:
              prev.streamedContent + (event.data.content as string || ""),
          }));
          break;

        case "complete":
          setState((prev) => ({ ...prev, status: "complete" }));
          updateProgress({ type: "generating", status: "complete" }, "update");
          break;

        case "error":
          setState((prev) => ({
            ...prev,
            status: "error",
            error: event.data.error as string,
          }));
          break;

        case "assistant_message_saved":
          // Invalidate queries to refresh the conversation
          if (conversationId) {
            queryClient.invalidateQueries({
              queryKey: conversationKeys.detail(conversationId),
            });
            queryClient.invalidateQueries({
              queryKey: conversationKeys.lists(),
            });
          }
          break;
      }
    },
    [conversationId, queryClient, updateProgress]
  );

  const sendMessage = useCallback(
    async (content: string) => {
      if (!conversationId) return;

      // Reset state
      setState({
        status: "thinking",
        progress: [],
        streamedContent: "",
      });

      // Create abort controller
      abortControllerRef.current = new AbortController();

      try {
        await streamMessage(
          conversationId,
          content,
          handleEvent,
          abortControllerRef.current.signal
        );
      } catch (error) {
        if ((error as Error).name === "AbortError") {
          setState((prev) => ({ ...prev, status: "idle" }));
        } else {
          setState((prev) => ({
            ...prev,
            status: "error",
            error: (error as Error).message,
          }));
        }
      } finally {
        abortControllerRef.current = null;
      }
    },
    [conversationId, handleEvent]
  );

  const cancelMessage = useCallback(() => {
    if (abortControllerRef.current) {
      cancelStream(abortControllerRef.current);
      abortControllerRef.current = null;
    }
    setState((prev) => ({ ...prev, status: "idle" }));
  }, []);

  const clearState = useCallback(() => {
    setState({
      status: "idle",
      progress: [],
      streamedContent: "",
    });
  }, []);

  return {
    state,
    sendMessage,
    cancelMessage,
    clearState,
    isStreaming:
      state.status !== "idle" &&
      state.status !== "complete" &&
      state.status !== "error",
  };
}
