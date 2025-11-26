/**
 * Chat Service - Handles conversation management and AI processing
 * Integrates with Python backend conversation and AI orchestrator services
 */
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
  conversation: ApiConversationPayload;
}

interface ConversationSummaryResponse {
  summary?: string;
}

interface ConversationsListResponse {
  conversations?: ApiConversationPayload[];
}

interface MemorySearchResponse {
  memories: Array<{
    id: string;
    content: string;
    similarity_score?: number;
    tags?: string[];
  }>;
}

interface AIProcessingResponse {
  response: string;
  ai_data?: Record<string, unknown>;
  suggested_actions?: string[];
  proactive_suggestion?: string;
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
        const sid = options.sessionId || generateUUID();
        
        // First, query relevant memories if needed
        let relevantMemories: MemorySearchResponse['memories'] = [];
        if (options.storeInMemory !== false) {
          try {
            const memoriesResponse = await this.apiClient.post<MemorySearchResponse>('/api/memory/search', {
              user_id: options.userId || sid || "anonymous",
              session_id: sid,
              query: message,
              top_k: 5,
              similarity_threshold: 0.7
            });
            relevantMemories = memoriesResponse.data?.memories || [];
          } catch (error) {
            console.warn('Failed to query memories for chat context', error);
          }
        }
        
        // Process the user message with the AI orchestrator
        const response = await this.apiClient.post<AIProcessingResponse>('/api/ai/conversation-processing', {
          prompt: message,
          conversation_history: conversationHistory.map(msg => ({
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp.toISOString(),
          })),
          user_settings: settings,
          session_id: sid,
          context: {
            relevant_memories: relevantMemories.map(mem => ({
              content: mem.content,
              similarity_score: mem.similarity_score,
              tags: mem.tags,
            })),
            user_id: options.userId,
            session_id: sid,
            tools: options.tools ? Object.keys(options.tools) : undefined,
          },
          include_memories: options.storeInMemory !== false,
          include_insights: true,
          // Include LLM preferences for proper fallback hierarchy
          llm_preferences: {
            preferred_llm_provider: options.preferredLLMProvider || "llama-cpp",
            preferred_model: options.preferredModel || "llama3.2:latest",
          },
        });
        
        // Transform the response to match the expected HandleUserMessageResult format
        const result: HandleUserMessageResult = {
          finalResponse: response.data?.response || "I'm sorry, I couldn't process your request.",
          aiDataForFinalResponse: response.data?.ai_data,
          suggestedNewFacts: response.data?.suggested_actions,
          proactiveSuggestion: response.data?.proactive_suggestion,
        };
        
        // Store the conversation in memory if successful
        if (result.finalResponse && options.storeInMemory !== false) {
          try {
            await this.apiClient.post('/api/memory/commit', {
              user_id: options.userId || sid || "anonymous",
              org_id: null,
              text: `User: ${message}\nAssistant: ${result.finalResponse}`,
              tags: ["conversation", "chat"],
              importance: 5,
              decay: "short",
              session_id: sid,
              metadata: {
                type: "conversation",
                user_message: message,
                assistant_response: result.finalResponse,
              },
            });
          } catch (error) {
            console.warn('Failed to store conversation in memory', error);
          }
        }
        
        return result;
      },
      {
        finalResponse: "I'm experiencing some technical difficulties right now. Please try again in a moment.",
        summaryWasGenerated: false,
      },
      {
        service: 'ChatService',
        method: 'processUserMessage',
        endpoint: '/api/ai/conversation-processing',
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

        const { conversation } = response.data;

        return {
          conversationId: conversation.id,
          sessionId: conversation.session_id || sessionId
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
      const response = await this.apiClient.get<ApiConversationPayload>(`/api/conversations/by-session/${sessionId}`);
      const data = response.data;
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
      const response = await this.apiClient.post<ConversationSummaryResponse>(`/api/conversations/${sessionId}/summary`);
      return response.data.summary ?? null;
    } catch (error) {
      console.warn('Failed to generate conversation summary', sessionId, error);
      return null;
    }
  }
  async getUserConversations(_userId: string): Promise<ConversationSession[]> {
    try {
      const response = await this.apiClient.get<ConversationsListResponse>('/api/conversations');
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
