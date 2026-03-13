/**
 * Conversation and Message Types
 */

export interface Conversation {
  id: string;
  title: string;
  userId: string;
  messages?: Message[];
  metadata?: ConversationMetadata;
  createdAt: string;
  updatedAt: string;
  archived?: boolean;
  pinned?: boolean;
}

export interface ConversationMetadata {
  tags?: string[];
  provider?: string;
  model?: string;
  color?: string;
  icon?: string;
  description?: string;
  [key: string]: unknown;
}

export interface Message {
  id: string;
  conversationId: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  metadata?: MessageMetadata;
  attachments?: Attachment[];
  replyTo?: string;
  reactions?: MessageReaction[];
  edited?: boolean;
  editedAt?: string;
}

export interface MessageMetadata {
  tokens?: number;
  cost?: number;
  latency?: number;
  model?: string;
  provider?: string;
  temperature?: number;
  [key: string]: unknown;
}

export interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  thumbnail?: string;
}

export interface MessageReaction {
  id: string;
  emoji: string;
  userId: string;
  timestamp: string;
}

export interface ConversationStats {
  totalConversations: number;
  totalMessages: number;
  activeConversations: number;
  archivedConversations: number;
  pinnedConversations: number;
  averageMessagesPerConversation: number;
  mostActiveDay: string;
  providerUsage: Record<string, number>;
  tagUsage: Record<string, number>;
}

export interface SearchFilters {
  query?: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
  tags?: string[];
  providers?: string[];
  hasAttachments?: boolean;
  isArchived?: boolean;
  isPinned?: boolean;
}

export interface ConversationSearchResult {
  conversation: Conversation;
  matchingMessages: Message[];
  relevanceScore: number;
  highlightedContent?: string;
}

export interface MessageSearchResult {
  message: Message;
  conversation: Conversation;
  relevanceScore: number;
  highlightedContent?: string;
}

export interface ExportOptions {
  format: 'json' | 'csv' | 'pdf' | 'txt';
  includeAttachments?: boolean;
  includeMetadata?: boolean;
  dateRange?: {
    start: Date;
    end: Date;
  };
  conversationIds?: string[];
  messageIds?: string[];
}

export interface ImportResult {
  success: boolean;
  importedConversations: number;
  importedMessages: number;
  errors: string[];
  duplicates: number;
}