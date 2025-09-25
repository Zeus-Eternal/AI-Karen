/**
 * Chat and Conversation Types
 * Aligned with backend schemas
 */

export interface ChatMessage {
  id: string;
  conversation_id: string;
  user_id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ConversationResponse {
  id: string;
  user_id: string;
  title: string | null;
  messages: ChatMessage[];
  metadata: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_at: string | null;
  session_id: string | null;
  ui_context: Record<string, any>;
  ai_insights: Record<string, any>;
  user_settings: Record<string, any>;
  summary: string | null;
  tags: string[];
  last_ai_response_id: string | null;
  status: string;
  priority: string;
  context_memories: Array<Record<string, any>>;
  proactive_suggestions: string[];
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_at: string | null;
  status: string;
  priority: string;
  tags: string[];
}

export interface CreateConversationRequest {
  title?: string;
  metadata?: Record<string, any>;
  ui_context?: Record<string, any>;
  user_settings?: Record<string, any>;
  tags?: string[];
}

export interface ChatRuntimeRequest {
  message: string;
  conversation_id?: string;
  model?: string;
  provider?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  context?: Record<string, any>;
}

export interface ChatRuntimeResponse {
  response: string;
  conversation_id: string;
  message_id: string;
  model_used: string;
  provider_used: string;
  tokens_used?: number;
  processing_time_ms?: number;
  metadata?: Record<string, any>;
}
