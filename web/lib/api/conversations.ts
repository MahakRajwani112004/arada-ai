import { apiClient } from "./client";
import type {
  ConversationListResponse,
  ConversationDetail,
  ConversationSummary,
  CreateConversationRequest,
  CreateConversationResponse,
  UpdateConversationRequest,
  AddMessageResponse,
  StreamEvent,
  StreamEventType,
} from "@/types/conversation";

// ============================================================================
// List Conversations
// ============================================================================

/**
 * List all conversations for the current user across all agents.
 * Used for the main /chat page.
 */
export async function listAllConversations(options?: {
  limit?: number;
  offset?: number;
  includeArchived?: boolean;
}): Promise<ConversationListResponse> {
  const response = await apiClient.get<ConversationListResponse>(
    "/conversations",
    {
      params: {
        limit: options?.limit ?? 50,
        offset: options?.offset ?? 0,
        include_archived: options?.includeArchived ?? false,
      },
    }
  );
  return response.data;
}

/**
 * List conversations for a specific agent.
 * Used for the agent detail chat tab.
 */
export async function listAgentConversations(
  agentId: string,
  options?: {
    limit?: number;
    offset?: number;
    includeArchived?: boolean;
  }
): Promise<ConversationListResponse> {
  const response = await apiClient.get<ConversationListResponse>(
    `/agents/${agentId}/conversations`,
    {
      params: {
        limit: options?.limit ?? 50,
        offset: options?.offset ?? 0,
        include_archived: options?.includeArchived ?? false,
      },
    }
  );
  return response.data;
}

// ============================================================================
// Single Conversation
// ============================================================================

/**
 * Get a conversation with its messages.
 */
export async function getConversation(
  conversationId: string,
  messageLimit?: number
): Promise<ConversationDetail> {
  const response = await apiClient.get<ConversationDetail>(
    `/conversations/${conversationId}`,
    {
      params: {
        message_limit: messageLimit ?? 100,
      },
    }
  );
  return response.data;
}

/**
 * Create a new conversation for an agent.
 */
export async function createConversation(
  agentId: string,
  request?: CreateConversationRequest
): Promise<CreateConversationResponse> {
  const response = await apiClient.post<CreateConversationResponse>(
    `/agents/${agentId}/conversations`,
    request ?? {}
  );
  return response.data;
}

/**
 * Update a conversation (rename).
 */
export async function updateConversation(
  conversationId: string,
  request: UpdateConversationRequest
): Promise<ConversationSummary> {
  const response = await apiClient.patch<ConversationSummary>(
    `/conversations/${conversationId}`,
    request
  );
  return response.data;
}

/**
 * Delete a conversation and all its messages.
 */
export async function deleteConversation(conversationId: string): Promise<void> {
  await apiClient.delete(`/conversations/${conversationId}`);
}

/**
 * Archive a conversation (soft delete).
 */
export async function archiveConversation(conversationId: string): Promise<void> {
  await apiClient.post(`/conversations/${conversationId}/archive`);
}

// ============================================================================
// Messages
// ============================================================================

/**
 * Add a message to a conversation (internal use).
 * For chat interactions, use streamMessage instead.
 */
export async function addMessage(
  conversationId: string,
  message: {
    role: "user" | "assistant" | "system";
    content: string;
    workflow_id?: string;
    execution_id?: string;
    metadata?: Record<string, unknown>;
  }
): Promise<AddMessageResponse> {
  const response = await apiClient.post<AddMessageResponse>(
    `/conversations/${conversationId}/messages`,
    message
  );
  return response.data;
}

// ============================================================================
// Streaming Chat
// ============================================================================

/**
 * Stream a message to a conversation with progress events.
 *
 * @param conversationId - The conversation to send the message to
 * @param content - The message content
 * @param onEvent - Callback for each streaming event
 * @param signal - Optional AbortSignal to cancel the stream
 *
 * @example
 * ```typescript
 * await streamMessage(conversationId, "Hello!", (event) => {
 *   if (event.type === "chunk") {
 *     // Append content to message
 *     setContent(prev => prev + event.data.content);
 *   } else if (event.type === "thinking") {
 *     setProgress(prev => [...prev, { type: "thinking", status: "active" }]);
 *   }
 * });
 * ```
 */
export async function streamMessage(
  conversationId: string,
  content: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  const url = `${baseUrl}/conversations/${conversationId}/stream`;

  // Get auth token from zustand persist storage
  let token: string | null = null;
  if (typeof window !== "undefined") {
    try {
      const authStorage = localStorage.getItem("auth-storage");
      if (authStorage) {
        const parsed = JSON.parse(authStorage);
        token = parsed?.state?.accessToken || null;
      }
    } catch {
      // Ignore parse errors
    }
  }

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify({ content }),
    signal,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE events
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      let currentEvent: string | null = null;
      let currentData: string[] = [];

      for (const line of lines) {
        if (line.startsWith("event:")) {
          // If we have a previous event, emit it
          if (currentEvent && currentData.length > 0) {
            const data = currentData.join("\n");
            try {
              const parsed = JSON.parse(data);
              onEvent({
                type: currentEvent as StreamEventType,
                data: parsed,
              });
            } catch {
              // Ignore parse errors
            }
          }
          currentEvent = line.slice(6).trim();
          currentData = [];
        } else if (line.startsWith("data:")) {
          currentData.push(line.slice(5).trim());
        } else if (line === "" && currentEvent && currentData.length > 0) {
          // Empty line signals end of event
          const data = currentData.join("\n");
          try {
            const parsed = JSON.parse(data);
            onEvent({
              type: currentEvent as StreamEventType,
              data: parsed,
            });
          } catch {
            // Ignore parse errors
          }
          currentEvent = null;
          currentData = [];
        }
      }

      // Emit any remaining event
      if (currentEvent && currentData.length > 0) {
        const data = currentData.join("\n");
        try {
          const parsed = JSON.parse(data);
          onEvent({
            type: currentEvent as StreamEventType,
            data: parsed,
          });
        } catch {
          // Ignore parse errors
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Cancel an ongoing stream.
 *
 * @param controller - The AbortController used when starting the stream
 */
export function cancelStream(controller: AbortController): void {
  controller.abort();
}
