/**
 * Chat Service - Handles conversation management and AI processing
 * Integrates with Python backend conversation and AI orchestrator services
 */

import { getKarenBackend } from '@/lib/karen-backend';
import { getApiClient } from '@/lib/api-client';
import type {
  ChatMessage,
  KarenSettings,
  HandleUserMessageResult,
  AiData
} from '@/lib/types';

export interface ConversationSession {
  sessionId: string;
  userId: string;
  createdAt: Date;
  updatedAt: Date;
  messages: ChatMessage[];
  context: Record<string, any>;
  summary?: string;
}

export interface ProcessMessageOptions {
  userId?: string;
  sessionId?: string;
  storeInMemory?: boolean;
  generateSummary?: boolean;
}

export class ChatService {
  private backend = getKarenBackend();
  private apiClient = getApiClient();
  private cache = new Map<string, ConversationSession>();

  async processUserMessage(
    message: string,
    conversationHistory: ChatMessage[],
    settings: KarenSettings,
    options: ProcessMessageOptions = {}
  ): Promise<HandleUserMessageResult> {
    try {
      const response = await this.backend.processUserMessage(
        message,
        conversationHistory,
        settings,
        options.userId,
        options.sessionId
      );

      return response;
    } catch (error) {
      console.error('ChatService: Failed to process user message:', error);
      return {
        finalResponse: "I'm experiencing some technical difficulties right now. Please try again in a moment.",
        summaryWasGenerated: false,
      };
    }
  }

  async createConversationSession(userId: string): Promise<{ conversationId: string; sessionId: string }> {
    try {
      const sessionId = crypto.randomUUID();

      const response = await this.apiClient.post('/api/conversations/create', {
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
    } catch (error) {
      console.error('ChatService.createConversationSession failed', error);
      throw new Error(
        'Cannot reach Kari API. Check that the backend is running on http://127.0.0.1:8000 and that NEXT_PUBLIC_API_BASE_URL is set.'
      );
    }
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
      console.warn('ChatService: Failed to add message to conversation:', error);
    }
  }

  async getConversation(sessionId: string): Promise<ConversationSession | null> {
    try {
      if (this.cache.has(sessionId)) {
        return this.cache.get(sessionId)!;
      }

      const response = await this.apiClient.get(`/api/conversations/${sessionId}`);

      const data = response.data;
      const session: ConversationSession = {
        sessionId: data.session_id,
        userId: data.user_id,
        createdAt: new Date(data.created_at),
        updatedAt: new Date(data.updated_at),
        messages: data.messages.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.created_at),
          aiData: msg.metadata?.ai_data,
          shouldAutoPlay: msg.metadata?.should_auto_play,
        })),
        context: data.metadata || {},
        summary: data.summary,
      };

      this.cache.set(sessionId, session);
      return session;
    } catch (error: any) {
      if (error.status === 404) {
        return null;
      }
      console.warn('ChatService: Failed to get conversation:', error);
      return null;
    }
  }

  async generateConversationSummary(sessionId: string): Promise<string | null> {
    try {
      const response = await this.apiClient.post(`/api/conversations/${sessionId}/summary`);
      return response.data.summary;
    } catch (error) {
      console.warn('ChatService: Failed to generate conversation summary:', error);
      return null;
    }
  }

  async getUserConversations(userId: string): Promise<ConversationSession[]> {
    try {
      const response = await this.apiClient.get(`/api/conversations/user/${userId}`);

      return response.data.conversations.map((conv: any) => ({
        sessionId: conv.session_id,
        userId: conv.user_id,
        createdAt: new Date(conv.created_at),
        updatedAt: new Date(conv.updated_at),
        messages: [],
        context: conv.metadata || {},
        summary: conv.summary,
      }));
    } catch (error) {
      console.warn('ChatService: Failed to get user conversations:', error);
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

