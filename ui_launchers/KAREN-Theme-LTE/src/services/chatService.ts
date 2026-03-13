/**
 * Chat Service
 * Comprehensive API client for the KAREN chat system
 * Handles all API communication with error handling and retry logic
 */

import {
  ChatMessage,
  Conversation,
  LLMProvider,
  ConnectionStatus,
  ConversationFilter,
  MessageFilter,
  ChatError,
  ChatMetrics,
  WebSocketMessageType,
  AttachmentType
} from '@/types/chat';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

// Request/Response Types
export interface SendMessageRequest {
  content: string;
  conversationId?: string;
  provider?: string;
  model?: string;
  userId?: string;
  sessionId?: string;
  attachments?: Array<{
    id: string;
    name: string;
    type: AttachmentType;
    size: number;
    url: string;
  }>;
  preferences?: {
    personalityTone?: 'friendly' | 'professional' | 'casual';
    personalityVerbosity?: 'concise' | 'balanced' | 'detailed';
    memoryDepth?: 'minimal' | 'medium' | 'comprehensive';
    enableStreaming?: boolean;
  };
}

export interface SendMessageResponse {
  messageId: string;
  message: string;
  conversationId: string;
  tokens?: {
    input: number;
    output: number;
    total: number;
  };
  aiData?: {
    confidence: number;
    intent: string;
    model: string;
    provider: string;
  };
  metadata?: Record<string, unknown>;
}

export interface CreateConversationRequest {
  title: string;
  provider?: string;
  model?: string;
  settings?: {
    provider?: string;
    model?: string;
    temperature?: number;
    maxTokens?: number;
    systemPrompt?: string;
  };
}

export interface UpdateConversationRequest {
  title?: string;
  settings?: Record<string, unknown>;
  isArchived?: boolean;
  isPinned?: boolean;
}

export interface SearchConversationsRequest {
  query: string;
  filter?: ConversationFilter;
  page?: number;
  limit?: number;
}

export interface SearchConversationsResponse {
  results: Conversation[];
  hasMore: boolean;
  total: number;
  page: number;
}

export interface UpdateProviderConfigRequest {
  apiKey?: string;
  baseUrl?: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
  customSettings?: Record<string, unknown>;
}

export interface FileUploadResponse {
  id: string;
  url: string;
  name: string;
  type: string;
  size: number;
}

export interface VoiceTranscriptionResponse {
  text: string;
  confidence: number;
  duration: number;
  language: string;
}

// Error Types
export class ChatApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status?: number,
    public context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ChatApiError';
  }
}

// WebSocket Manager
class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Map<string, (data: unknown) => void> = new Map();
  private connectionStatus: ConnectionStatus = {
    isConnected: false,
    isConnecting: false,
    isReconnecting: false,
    connectionAttempts: 0,
  };

  constructor(
    private onConnectionStatusChange: (status: ConnectionStatus) => void,
    private onError: (error: ChatError) => void
  ) {}

  connect(userId: string, sessionId: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this.connectionStatus = {
      ...this.connectionStatus,
      isConnecting: true,
      connectionAttempts: this.connectionStatus.connectionAttempts + 1,
    };
    this.onConnectionStatusChange(this.connectionStatus);

    const wsUrl = `${WS_BASE_URL}/chat?userId=${userId}&sessionId=${sessionId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.connectionStatus = {
        isConnected: true,
        isConnecting: false,
        isReconnecting: false,
        connectionAttempts: 0,
        lastConnected: new Date(),
      };
      this.onConnectionStatusChange(this.connectionStatus);
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const handler = this.messageHandlers.get(message.type);
        if (handler) {
          handler(message.data);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = () => {
      this.connectionStatus = {
        ...this.connectionStatus,
        isConnected: false,
        isReconnecting: this.reconnectAttempts < this.maxReconnectAttempts,
      };
      this.onConnectionStatusChange(this.connectionStatus);

      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        setTimeout(() => {
          this.connect(userId, sessionId);
        }, this.reconnectDelay * this.reconnectAttempts);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.onError({
        code: 'WEBSOCKET_ERROR',
        message: 'WebSocket connection error',
        timestamp: new Date(),
        context: { action: 'connectWebSocket' },
      });
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(type: WebSocketMessageType, data: unknown) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data, timestamp: new Date() }));
    }
  }

  onMessage(type: WebSocketMessageType, handler: (data: unknown) => void) {
    this.messageHandlers.set(type, handler);
  }

  offMessage(type: WebSocketMessageType) {
    this.messageHandlers.delete(type);
  }

  getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus;
  }
}

// Main Chat Service Class
class ChatService {
  private wsManager: WebSocketManager | null = null;

  constructor() {
    // Initialize WebSocket manager when needed
  }

  // HTTP Request Helper
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(API_KEY && { 'Authorization': `Bearer ${API_KEY}` }),
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ChatApiError(
          errorData.message || `Request failed: ${response.statusText}`,
          errorData.code || 'REQUEST_FAILED',
          response.status,
          errorData.context
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ChatApiError) {
        throw error;
      }
      throw new ChatApiError(
        error instanceof Error ? error.message : 'Unknown error',
        'NETWORK_ERROR',
        undefined,
        { endpoint, options }
      );
    }
  }

  // Message Operations
  async sendMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
    return this.makeRequest<SendMessageResponse>('/chat/messages', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async retryMessage(messageId: string): Promise<SendMessageResponse> {
    return this.makeRequest<SendMessageResponse>(`/chat/messages/${messageId}/retry`, {
      method: 'POST',
    });
  }

  async updateMessage(messageId: string, updates: Partial<ChatMessage>): Promise<ChatMessage> {
    return this.makeRequest<ChatMessage>(`/chat/messages/${messageId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteMessage(messageId: string): Promise<void> {
    return this.makeRequest<void>(`/chat/messages/${messageId}`, {
      method: 'DELETE',
    });
  }

  async addReaction(messageId: string, emoji: string): Promise<void> {
    return this.makeRequest<void>(`/chat/messages/${messageId}/reactions`, {
      method: 'POST',
      body: JSON.stringify({ emoji }),
    });
  }

  async removeReaction(messageId: string, emoji: string): Promise<void> {
    return this.makeRequest<void>(`/chat/messages/${messageId}/reactions/${emoji}`, {
      method: 'DELETE',
    });
  }

  async bookmarkMessage(messageId: string, bookmarked: boolean): Promise<void> {
    return this.makeRequest<void>(`/chat/messages/${messageId}/bookmark`, {
      method: 'PUT',
      body: JSON.stringify({ bookmarked }),
    });
  }

  // Conversation Operations
  async createConversation(request: CreateConversationRequest): Promise<Conversation> {
    return this.makeRequest<Conversation>('/chat/conversations', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getConversations(filter?: ConversationFilter): Promise<Conversation[]> {
    const query = filter ? `?${new URLSearchParams(filter as Record<string, string>).toString()}` : '';
    return this.makeRequest<Conversation[]>(`/chat/conversations${query}`);
  }

  async getConversation(conversationId: string): Promise<Conversation> {
    return this.makeRequest<Conversation>(`/chat/conversations/${conversationId}`);
  }

  async updateConversation(
    conversationId: string,
    updates: UpdateConversationRequest
  ): Promise<Conversation> {
    return this.makeRequest<Conversation>(`/chat/conversations/${conversationId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteConversation(conversationId: string): Promise<void> {
    return this.makeRequest<void>(`/chat/conversations/${conversationId}`, {
      method: 'DELETE',
    });
  }

  async archiveConversation(conversationId: string, archived: boolean): Promise<void> {
    return this.makeRequest<void>(`/chat/conversations/${conversationId}/archive`, {
      method: 'PUT',
      body: JSON.stringify({ archived }),
    });
  }

  async pinConversation(conversationId: string, pinned: boolean): Promise<void> {
    return this.makeRequest<void>(`/chat/conversations/${conversationId}/pin`, {
      method: 'PUT',
      body: JSON.stringify({ pinned }),
    });
  }

  async searchConversations(
    request: SearchConversationsRequest
  ): Promise<SearchConversationsResponse> {
    return this.makeRequest<SearchConversationsResponse>('/chat/conversations/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getConversationMessages(
    conversationId: string,
    filter?: MessageFilter
  ): Promise<ChatMessage[]> {
    const query = filter ? `?${new URLSearchParams(filter as Record<string, string>).toString()}` : '';
    return this.makeRequest<ChatMessage[]>(
      `/chat/conversations/${conversationId}/messages${query}`
    );
  }

  // Provider Operations
  async getProviders(): Promise<LLMProvider[]> {
    return this.makeRequest<LLMProvider[]>('/chat/providers');
  }

  async getProvider(providerId: string): Promise<LLMProvider> {
    return this.makeRequest<LLMProvider>(`/chat/providers/${providerId}`);
  }

  async updateProviderConfig(
    providerId: string,
    config: UpdateProviderConfigRequest
  ): Promise<LLMProvider> {
    return this.makeRequest<LLMProvider>(`/chat/providers/${providerId}/config`, {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  async testProviderConnection(
    providerId: string,
    config?: Record<string, unknown>
  ): Promise<{ success: boolean; error?: string; data?: unknown }> {
    const requestBody = config ? { config } : {};
    return this.makeRequest<{ success: boolean; error?: string; data?: unknown }>(`/chat/providers/${providerId}/test`, {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  }

  async createProvider(
    providerType: string,
    config: Record<string, unknown>
  ): Promise<LLMProvider> {
    return this.makeRequest<LLMProvider>('/chat/providers', {
      method: 'POST',
      body: JSON.stringify({
        provider_type: providerType,
        config
      }),
    });
  }

  async deleteProvider(providerId: string): Promise<void> {
    return this.makeRequest<void>(`/chat/providers/${providerId}`, {
      method: 'DELETE',
    });
  }

  async getProviderStatus(providerId: string): Promise<Record<string, unknown>> {
    return this.makeRequest<Record<string, unknown>>(`/chat/providers/${providerId}/status`);
  }

  async getAllProviderStatuses(): Promise<Record<string, unknown>> {
    return this.makeRequest<Record<string, unknown>>('/chat/providers/status');
  }

  async getProviderMetrics(providerId: string): Promise<Record<string, unknown>> {
    return this.makeRequest<Record<string, unknown>>(`/chat/providers/${providerId}/metrics`);
  }

  async getAllProviderMetrics(): Promise<Record<string, unknown>> {
    return this.makeRequest<Record<string, unknown>>('/chat/providers/metrics');
  }

  async setFallbackChain(providerIds: string[]): Promise<void> {
    return this.makeRequest<void>('/chat/providers/fallback-chain', {
      method: 'PUT',
      body: JSON.stringify({ provider_ids: providerIds }),
    });
  }

  async getFallbackChain(): Promise<string[]> {
    return this.makeRequest<string[]>('/chat/providers/fallback-chain');
  }

  async setPrimaryProvider(providerId: string): Promise<void> {
    return this.makeRequest<void>(`/chat/providers/${providerId}/primary`, {
      method: 'PUT',
    });
  }

  async getPrimaryProvider(): Promise<string | null> {
    return this.makeRequest<string | null>('/chat/providers/primary');
  }

  // File Upload Operations
  async uploadFile(file: File, onProgress?: (progress: number) => void): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            onProgress(progress);
          }
        });
      }

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (error) {
            reject(new Error('Failed to parse upload response'));
          }
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('POST', `${API_BASE_URL}/chat/upload`);
      if (API_KEY) {
        xhr.setRequestHeader('Authorization', `Bearer ${API_KEY}`);
      }
      xhr.send(formData);
    });
  }

  // Voice Operations
  async transcribeAudio(audioBlob: Blob): Promise<VoiceTranscriptionResponse> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    return this.makeRequest<VoiceTranscriptionResponse>('/chat/voice/transcribe', {
      method: 'POST',
      body: formData,
    });
  }

  // Analytics Operations
  async getConversationMetrics(conversationId: string): Promise<ChatMetrics> {
    return this.makeRequest<ChatMetrics>(`/chat/conversations/${conversationId}/metrics`);
  }

  async getUserMetrics(userId?: string): Promise<ChatMetrics> {
    const query = userId ? `?userId=${userId}` : '';
    return this.makeRequest<ChatMetrics>(`/chat/metrics${query}`);
  }

  // Export/Import Operations
  async exportConversation(
    conversationId: string,
    format: 'json' | 'csv' | 'txt'
  ): Promise<Blob> {
    const response = await fetch(
      `${API_BASE_URL}/chat/conversations/${conversationId}/export?format=${format}`,
      {
        headers: {
          ...(API_KEY && { 'Authorization': `Bearer ${API_KEY}` }),
        },
      }
    );

    if (!response.ok) {
      throw new ChatApiError(
        `Export failed: ${response.statusText}`,
        'EXPORT_FAILED',
        response.status
      );
    }

    return response.blob();
  }

  async importConversation(file: File): Promise<Conversation> {
    const formData = new FormData();
    formData.append('file', file);

    return this.makeRequest<Conversation>('/chat/conversations/import', {
      method: 'POST',
      body: formData,
    });
  }

  // WebSocket Operations
  connectWebSocket(
    userId: string,
    sessionId: string,
    onConnectionStatusChange: (status: ConnectionStatus) => void,
    onError: (error: ChatError) => void,
    onMessage: (type: WebSocketMessageType, data: unknown) => void
  ): void {
    this.wsManager = new WebSocketManager(onConnectionStatusChange, onError);
    
    // Set up message handlers
    this.wsManager.onMessage(WebSocketMessageType.MESSAGE, (data) => {
      onMessage(WebSocketMessageType.MESSAGE, data);
    });
    
    this.wsManager.onMessage(WebSocketMessageType.TYPING, (data) => {
      onMessage(WebSocketMessageType.TYPING, data);
    });
    
    this.wsManager.onMessage(WebSocketMessageType.STATUS, (data) => {
      onMessage(WebSocketMessageType.STATUS, data);
    });
    
    this.wsManager.onMessage(WebSocketMessageType.ERROR, (data) => {
      onMessage(WebSocketMessageType.ERROR, data);
    });

    this.wsManager.connect(userId, sessionId);
  }

  disconnectWebSocket(): void {
    if (this.wsManager) {
      this.wsManager.disconnect();
      this.wsManager = null;
    }
  }

  sendWebSocketMessage(type: WebSocketMessageType, data: unknown): void {
    if (this.wsManager) {
      this.wsManager.send(type, data);
    }
  }

  getWebSocketConnectionStatus(): ConnectionStatus | null {
    return this.wsManager ? this.wsManager.getConnectionStatus() : null;
  }
}

// Export singleton instance
export const chatService = new ChatService();
