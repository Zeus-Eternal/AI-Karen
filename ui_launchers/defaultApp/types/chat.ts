/**
 * Chat Type Definitions
 * Based on AI-Karen backend models from src/ai_karen_engine/api_routes/conversation_routes.py
 */

export type MessageRole = 'user' | 'assistant' | 'system'

export interface Message {
  id: string
  conversationId: string
  role: MessageRole
  content: string
  timestamp: string
  metadata?: MessageMetadata
  isStreaming?: boolean
}

export interface MessageMetadata {
  tokens?: number
  model?: string
  latency?: number
  contentType?: 'text' | 'markdown' | 'code' | 'json'
  attachments?: Attachment[]
}

export interface Attachment {
  id: string
  name: string
  type: string
  size: number
  url: string
}

export interface Conversation {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  messageCount: number
  tags?: string[]
  metadata?: ConversationMetadata
}

export interface ConversationMetadata {
  model?: string
  agent?: string
  executionMode?: 'native' | 'langgraph' | 'deepagents' | 'auto'
}

export interface SendMessageRequest {
  conversationId: string
  message: string
  context?: Record<string, unknown>
  agentId?: string
  executionMode?: 'native' | 'langgraph' | 'deepagents' | 'auto'
}

export interface SendMessageResponse {
  success: boolean
  messageId: string
  response?: string
  isStreaming: boolean
  metadata?: ResponseMetadata
  error?: string
}

export interface ResponseMetadata {
  responseId: string
  contentType: 'text' | 'markdown' | 'code' | 'json'
  timestamp: string
  executionTime: number
  agentId?: string
  taskId?: string
  sessionId?: string
  threadId?: string
  isStreaming: boolean
  isPartial: boolean
  hasError: boolean
}

export interface StreamChunk {
  type: 'token' | 'metadata' | 'error' | 'done'
  content?: string
  metadata?: ResponseMetadata
  error?: string
}
