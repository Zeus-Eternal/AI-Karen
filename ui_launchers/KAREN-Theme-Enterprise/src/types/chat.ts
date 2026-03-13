/**
 * Chat and Conversation Types
 *
 * Type definitions for the chat and conversation system, aligned with backend schemas.
 * These types support real-time messaging, conversation management, AI interactions,
 * and context tracking.
 */

/**
 * Message metadata for extensibility
 */
export interface MessageMetadata {
  /** Tokens used in this message */
  tokens?: number;
  /** Model used for generation */
  model?: string;
  /** Processing time in milliseconds */
  processingTime?: number;
  /** Indicates if message was edited */
  edited?: boolean;
  /** Indicates if message contains sensitive data */
  sensitive?: boolean;
  /** Custom extensible fields */
  [key: string]: unknown;
}

/**
 * Individual chat message in a conversation
 */
export interface ChatMessage {
  id: string;
  conversation_id: string;
  user_id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  metadata?: MessageMetadata;
}

/**
 * UI context for conversation state persistence
 */
export interface UIContext {
  /** Active panel or view */
  activeView?: string;
  /** Scroll position */
  scrollPosition?: number;
  /** Selected text or elements */
  selection?: string;
  /** Draft message */
  draft?: string;
  /** Custom extensible fields */
  [key: string]: unknown;
}

/**
 * AI-generated insights about the conversation
 */
export interface AIInsights {
  /** Detected user intent */
  intent?: string;
  /** Conversation sentiment */
  sentiment?: 'positive' | 'neutral' | 'negative';
  /** Detected language */
  language?: string;
  /** Suggested next actions */
  suggestedActions?: string[];
  /** Confidence scores */
  confidence?: Record<string, number>;
  /** Custom extensible fields */
  [key: string]: unknown;
}

/**
 * User-specific settings for the conversation
 */
export interface ConversationUserSettings {
  /** Notification preferences */
  notifications?: boolean;
  /** Theme preference for this conversation */
  theme?: 'light' | 'dark';
  /** Font size preference */
  fontSize?: 'small' | 'medium' | 'large';
  /** Auto-scroll behavior */
  autoScroll?: boolean;
  /** Custom extensible fields */
  [key: string]: unknown;
}

/**
 * Context memory entry for conversation continuity
 */
export interface ContextMemory {
  /** Memory entry ID */
  id: string;
  /** Memory content */
  content: string;
  /** Memory type */
  type: 'fact' | 'preference' | 'context' | 'reference';
  /** Relevance score */
  relevance?: number;
  /** Timestamp of memory creation */
  timestamp: string;
  /** Custom extensible fields */
  [key: string]: unknown;
}

/**
 * Complete conversation response with all associated data
 */
export interface ConversationResponse {
  id: string;
  user_id: string;
  title: string | null;
  messages: ChatMessage[];
  metadata: MessageMetadata;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_at: string | null;
  session_id: string | null;
  ui_context: UIContext;
  ai_insights: AIInsights;
  user_settings: ConversationUserSettings;
  summary: string | null;
  tags: string[];
  last_ai_response_id: string | null;
  status: string;
  priority: string;
  context_memories: ContextMemory[];
  proactive_suggestions: string[];
}

/**
 * Lightweight conversation summary for list views
 */
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

/**
 * Request payload for creating a new conversation
 */
export interface CreateConversationRequest {
  /** Optional conversation title */
  title?: string;
  /** Initial metadata */
  metadata?: MessageMetadata;
  /** Initial UI context */
  ui_context?: UIContext;
  /** User settings for this conversation */
  user_settings?: ConversationUserSettings;
  /** Tags for categorization */
  tags?: string[];
}

/**
 * Tool call made by the AI during response generation
 */
export interface ToolCall {
  /** Tool identifier */
  id: string;
  /** Tool name */
  name: string;
  /** Tool arguments */
  arguments: Record<string, unknown>;
  /** Tool execution result */
  result?: unknown;
}

/**
 * Memory operation performed during conversation
 */
export interface MemoryOperation {
  /** Operation type */
  type: 'create' | 'update' | 'delete' | 'retrieve';
  /** Memory ID */
  memoryId?: string;
  /** Memory content */
  content?: string;
  /** Operation metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Request to the chat runtime for message processing
 */
export interface ChatRuntimeRequest {
  /** User message content */
  message: string;
  /** Existing conversation ID or create new */
  conversation_id?: string;
  /** Enable streaming response */
  stream?: boolean;
  /** Additional context for the request */
  context?: Record<string, unknown>;
  /** Available tools for the AI to use */
  tools?: string[];
  /** Memory context for conversation continuity */
  memory_context?: string;
  /** User preferences for response generation */
  user_preferences?: Record<string, unknown>;
  /** Platform identifier (web, mobile, etc.) */
  platform?: string;
  /** Model selection hint */
  model?: string;
  /** Provider selection hint */
  provider?: string;
  /** Temperature for response generation (0.0-1.0) */
  temperature?: number;
  /** Maximum tokens in response */
  max_tokens?: number;
}

/**
 * Response from the chat runtime after message processing
 */
export interface ChatRuntimeResponse {
  /** Generated response content */
  content: string;
  /** Conversation ID (existing or newly created) */
  conversation_id?: string;
  /** Response metadata */
  metadata?: MessageMetadata;
  /** Tools called during generation */
  tool_calls?: ToolCall[];
  /** Memory operations performed */
  memory_operations?: MemoryOperation[];
  /** Response timestamp */
  timestamp?: string;
}
