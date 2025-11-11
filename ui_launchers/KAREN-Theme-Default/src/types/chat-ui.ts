import type { AiData, ChatMessage, HandleUserMessageResult, KarenSettings } from '@/lib/types';
import type { MemoryReference } from '@/types/enhanced-chat';

export type ChatSystemView = 'chat' | 'conversations' | 'analytics';

export type UiAiData = AiData & {
  reasoning?: string;
  sources?: string[];
};

export type UiChatMessage = ChatMessage & {
  aiData?: UiAiData;
  confidence?: number;
};

export interface ConversationSummaryRow {
  id: string;
  sessionId: string;
  title: string;
  lastActivity: Date;
  messageCount: number;
  status: 'active' | 'archived';
  sentiment: 'positive' | 'neutral' | 'negative';
  lastMessage?: string;
  participants?: string[];
  tags?: string[];
}

export type MessageSubmitHandler = (message: string) => Promise<void>;

export interface MemoryListEntry {
  id: string;
  content: string;
  timestamp: Date;
  category?: string;
  importance?: 'high' | 'medium' | 'low';
  tags?: string[];
}

export interface ProcessMessageOptions {
  userId?: string;
  sessionId?: string;
  storeInMemory?: boolean;
  generateSummary?: boolean;
  preferredLLMProvider?: string;
  preferredModel?: string;
  tools?: Record<string, (...args: unknown[]) => unknown>;
}

export interface ChatRuntimeClient {
  createConversationSession(userId: string): Promise<{ conversationId: string; sessionId: string }>;
  addMessageToConversation(conversationId: string, message: ChatMessage): Promise<void>;
  processUserMessage(
    message: string,
    history: ChatMessage[],
    settings: Partial<KarenSettings>,
    options?: ProcessMessageOptions
  ): Promise<HandleUserMessageResult>;
  getUserConversations(userId: string): Promise<ConversationSummaryRow[]>;
}

export type MemoryReferenceList = MemoryReference[];

