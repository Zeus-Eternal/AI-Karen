/**
 * Chat Service - Handles conversation management and AI processing
 * Integrates with Python backend conversation and AI orchestrator services
 */
import { getKarenBackend } from '@/lib/karen-backend';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { getServiceErrorHandler } from './errorHandler';
import { generateUUID } from '@/lib/uuid';
import type { ChatMessage, KarenSettings, HandleUserMessageResult } from '@/lib/types';
export interface ConversationSession {
  conversationId: string;
  sessionId: string;
  userId: string;
  createdAt: Date;
  updatedAt: Date;
  messages: ChatMessage[];
  context: Record<string, unknown>;
  summary?: string;
}
export type Toolset = Record<string, (...args: unknown[]) => unknown>;

export interface ProcessMessageOptions {
  userId?: string;
  sessionId?: string;
  storeInMemory?: boolean;
  generateSummary?: boolean;
  preferredLLMProvider?: string;
  preferredModel?: string;
  tools?: Toolset;
}

interface MessageMetadataPayload {
  ai_data?: ChatMessage['aiData'];
  should_auto_play?: boolean;
}

interface ApiConversationMessage {
  id: string;
  role: ChatMessage['role'];
  content: string;
  created_at?: string;
  timestamp?: string;
  metadata?: MessageMetadataPayload;
}

interface ApiConversationPayload {
  id: string;
  session_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  messages?: ApiConversationMessage[];
  metadata?: Record<string, unknown>;
  summary?: string;
}

interface CreateConversationResponse {
  conversation: {
    id: string;
    session_id?: string;
  };
}

interface ConversationSummaryResponse {
  summary: string;
}

interface ConversationListResponse {
  conversations: ApiConversationPayload[];
}

const mapApiMessageToChatMessage = (msg: ApiConversationMessage): ChatMessage => {
  const timestampValue = msg.created_at ?? msg.timestamp;
  return {
    id: msg.id,
    role: msg.role,
    content: msg.content,
    timestamp: timestampValue ? new Date(timestampValue) : new Date(),
    aiData: msg.metadata?.ai_data,
    shouldAutoPlay: msg.metadata?.should_auto_play,
  };
};
export class ChatService {
  private backend = getKarenBackend();
  private apiClient = enhancedApiClient;
  private errorHandler = getServiceErrorHandler();
  private cache = new Map<string, ConversationSession>();
  async processUserMessage(
    message: string,
    conversationHistory: ChatMessage[],
    settings: KarenSettings,
    options: ProcessMessageOptions = {}
  ): Promise<HandleUserMessageResult> {
    return this.errorHandler.withRetryAndFallback(
      async () => {
        const response = await this.backend.processUserMessage(
          message,
          conversationHistory,
          settings,
          options.userId,
          options.sessionId,
          {
            preferredLLMProvider: options.preferredLLMProvider,
            preferredModel: options.preferredModel,
          },
          options.tools
        );
        return response;
      },
      {
        finalResponse: "I'm experiencing some technical difficulties right now. Please try again in a moment.",
        summaryWasGenerated: false,
      },
      {
        service: 'ChatService',
        method: 'processUserMessage',
        endpoint: '/api/chat/process',
      }
    );
  }
  async createConversationSession(userId: string): Promise<{ conversationId: string; sessionId: string }> {
    return this.errorHandler.withRetry(
      async () => {
        const sessionId = generateUUID();
        const response = await this.apiClient.post<CreateConversationResponse>('/api/conversations/create', {
          session_id: sessionId,
          ui_source: 'web',
          title: 'New Conversation',
          user_settings: {},
          ui_context: {
            user_id: userId,
            created_from: 'web_ui',
            browser: navigator.userAgent
          },
          tags: [],
          priority: 'normal'
        });

        return {
          conversationId: response.data.conversation.id,
          sessionId: response.data.conversation.session_id || sessionId
        };
      },
      {
        service: 'ChatService',
        method: 'createConversationSession',
        endpoint: '/api/conversations/create',
      }
    );
  }
  async addMessageToConversation(conversationId: string, message: ChatMessage): Promise<void> {
    try {
      await this.apiClient.post(`/api/conversations/${conversationId}/messages`, {
        role: message.role,
        content: message.content,
        ui_source: 'web',
        metadata: {
          ai_data: message.aiData,
          should_auto_play: message.shouldAutoPlay,
          timestamp: message.timestamp.toISOString(),
        },
      });

    } catch (error) {
      console.warn('Failed to add message to conversation', conversationId, error);
    }
  }
  async getConversation(sessionId: string): Promise<ConversationSession | null> {
    try {
      if (this.cache.has(sessionId)) {
        return this.cache.get(sessionId)!;
      }
      const response = await this.apiClient.get<ApiConversationPayload>(
        `/api/conversations/by-session/${sessionId}`
      );
      const data: ApiConversationPayload = response.data;
      const session: ConversationSession = {
        conversationId: data.id,
        sessionId: data.session_id,
        userId: data.user_id,
        createdAt: new Date(data.created_at),
        updatedAt: new Date(data.updated_at),
        messages: (data.messages || []).map(mapApiMessageToChatMessage),
        context: data.metadata || {},
        summary: data.summary,
      };
      this.cache.set(sessionId, session);
      return session;
    } catch (error) {
      let status: number | undefined;
      if (typeof error === 'object' && error !== null && 'status' in error) {
        status = (error as { status?: number }).status;
      }
      if (status === 404) {
        return null;
      }
      console.error('Failed to load conversation', sessionId, error);
      return null;
    }
  }
  async generateConversationSummary(sessionId: string): Promise<string | null> {
    try {
      const response = await this.apiClient.post<ConversationSummaryResponse>(
        `/api/conversations/${sessionId}/summary`
      );
      return response.data.summary;
    } catch (error) {
      console.warn('Failed to generate conversation summary', sessionId, error);
      return null;
    }
  }
  async getUserConversations(_userId: string): Promise<ConversationSession[]> {
    try {
      const response = await this.apiClient.get<ConversationListResponse>(
        '/api/conversations'
      );
      const conversations = response.data.conversations || [];
      return conversations.map((conv) => ({
        conversationId: conv.id,
        sessionId: conv.session_id,
        userId: conv.user_id,
        createdAt: new Date(conv.created_at),
        updatedAt: new Date(conv.updated_at),
        messages: (conv.messages || []).map(mapApiMessageToChatMessage),
        context: conv.metadata || {},
        summary: conv.summary,
      }));
    } catch (error) {
      console.warn('Failed to load user conversations', error);
      return [];
    }
  }
  clearCache(): void {
    this.cache.clear();
  }
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }
}
let chatService: ChatService | null = null;
export function getChatService(): ChatService {
  if (!chatService) {
    chatService = new ChatService();
  }
  return chatService;
}
export function initializeChatService(): ChatService {
  chatService = new ChatService();
  return chatService;
}
