import type { AgentType } from "./agent";

// ==================== Message Types ====================

export interface ConversationMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  workflow_id: string | null;
  execution_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

// ==================== Conversation Types ====================

export interface ConversationSummary {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_type: AgentType;
  title: string;
  message_count: number;
  last_message_preview: string | null;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_type: AgentType;
  title: string;
  is_auto_title: boolean;
  message_count: number;
  messages: ConversationMessage[];
  created_at: string;
  updated_at: string;
}

export interface ConversationListResponse {
  conversations: ConversationSummary[];
  total: number;
}

// ==================== Grouped Conversations (for sidebar) ====================

export interface GroupedConversations {
  today: ConversationSummary[];
  yesterday: ConversationSummary[];
  thisWeek: ConversationSummary[];
  older: ConversationSummary[];
}

// ==================== Request Types ====================

export interface CreateConversationRequest {
  title?: string;
}

export interface UpdateConversationRequest {
  title: string;
}

export interface SendMessageRequest {
  content: string;
}

// ==================== Response Types ====================

export interface CreateConversationResponse {
  id: string;
  agent_id: string;
  title: string;
  created_at: string;
}

export interface AddMessageResponse {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

// ==================== Streaming Event Types ====================

export type StreamEventType =
  | "thinking"
  | "retrieving"
  | "retrieved"
  | "tool_start"
  | "tool_end"
  | "mcp_start"
  | "mcp_end"
  | "skill_start"
  | "skill_end"
  | "generating"
  | "chunk"
  | "complete"
  | "error"
  | "message_saved"
  | "assistant_message_saved";

export interface StreamEvent {
  type: StreamEventType;
  data: Record<string, unknown>;
}

export interface ThinkingEventData {
  step?: string;
}

export interface RetrievingEventData {
  knowledge_base_name: string;
  query_preview?: string;
}

export interface RetrievedEventData {
  document_count: number;
  chunks_used: number;
}

export interface ToolEventData {
  tool_name: string;
  tool_id?: string;
  args_preview?: string;
  success?: boolean;
  result_preview?: string;
}

export interface MCPEventData {
  server_name: string;
  tool_name: string;
  success?: boolean;
}

export interface SkillEventData {
  skill_name: string;
  skill_id: string;
}

export interface ChunkEventData {
  content: string;
  token_count?: number;
}

export interface CompleteEventData {
  message_id: string;
  total_tokens?: number;
  execution_id?: string;
}

export interface ErrorEventData {
  error: string;
  error_type?: string;
  recoverable: boolean;
}

export interface MessageSavedEventData {
  role: string;
  message_id?: string;
}

// ==================== Progress Tracking ====================

export type ProgressStatus = "pending" | "active" | "complete" | "error";

export interface ProgressItem {
  type: "thinking" | "retrieving" | "tool" | "mcp" | "skill" | "generating";
  status: ProgressStatus;
  name?: string;
  detail?: string;
}

// ==================== Streaming State ====================

export interface StreamingState {
  status: "idle" | "thinking" | "retrieving" | "tools" | "generating" | "complete" | "error";
  progress: ProgressItem[];
  streamedContent: string;
  error?: string;
}

// ==================== Utility Functions ====================

/**
 * Group conversations by date for sidebar display.
 */
export function groupConversationsByDate(
  conversations: ConversationSummary[]
): GroupedConversations {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);

  const grouped: GroupedConversations = {
    today: [],
    yesterday: [],
    thisWeek: [],
    older: [],
  };

  for (const conv of conversations) {
    const updatedAt = new Date(conv.updated_at);
    const convDate = new Date(
      updatedAt.getFullYear(),
      updatedAt.getMonth(),
      updatedAt.getDate()
    );

    if (convDate >= today) {
      grouped.today.push(conv);
    } else if (convDate >= yesterday) {
      grouped.yesterday.push(conv);
    } else if (convDate >= weekAgo) {
      grouped.thisWeek.push(conv);
    } else {
      grouped.older.push(conv);
    }
  }

  return grouped;
}

/**
 * Format relative time for conversation display.
 */
export function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return "";

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}d`;

  // Format as date
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}
