/**
 * Conversation Service - API service layer for conversation management
 * Handles all API calls for conversations and messages
 */

import { Conversation, Message, Attachment, ConversationFilters, MessageFilters } from '../stores/conversationStore';

// API response types
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ConversationStats {
  total_conversations: number;
  active_conversations: number;
  archived_conversations: number;
  provider_usage: Record<string, number>;
  average_messages_per_conversation: number;
  period_days: number;
}

export interface MessageStats {
  message_stats: Array<{
    role: string;
    count: number;
    average_tokens: number;
    total_processing_time_ms: number;
  }>;
  length_distribution: Array<{
    category: string;
    count: number;
  }>;
  attachment_analytics: {
    total_attachments: number;
    messages_with_attachments: number;
    average_file_size: number;
    total_size: number;
    unique_mime_types: number;
  };
  mime_type_distribution: Array<{
    mime_type: string;
    count: number;
    average_size: number;
  }>;
}

// Base API client
class ApiClient {
  public baseUrl: string;
  public defaultHeaders: Record<string, string>;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || '/api';
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  public async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: { ...this.defaultHeaders, ...options.headers },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  public async post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  public async put<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  protected async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  protected async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const url = params ? `${endpoint}?${new URLSearchParams(params as Record<string, string>)}` : endpoint;
    return this.request<T>(url);
  }
  
  // Helper to convert mixed type params to Record<string, string>
  protected normalizeParams(params?: Record<string, unknown> | string[] | number): Record<string, string> {
    if (!params || typeof params !== 'object') return {};
    if (Array.isArray(params)) return {};
    
    const result: Record<string, string> = {};
    for (const [key, value] of Object.entries(params)) {
      result[key] = String(value);
    }
    return result;
  }

  // Helper to convert params with arrays to proper URL search params
  protected buildSearchParams(params: Record<string, unknown>): string {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null) continue;
      if (Array.isArray(value)) {
        value.forEach(v => searchParams.append(key, String(v)));
      } else {
        searchParams.set(key, String(value));
      }
    }
    return searchParams.toString();
  }
}

// Conversation API Service
export class ConversationService extends ApiClient {
  // Conversation CRUD
  async createConversation(data: {
    title?: string;
    provider_id?: string;
    model_used?: string;
    metadata?: Record<string, unknown>;
    tags?: string[];
    is_pinned?: boolean;
  }): Promise<Conversation> {
    return this.post<Conversation>('/chat/conversations', data);
  }

  async getConversation(id: string): Promise<Conversation> {
    return this.get<Conversation>(`/chat/conversations/${id}`);
  }

  async updateConversation(
    id: string,
    data: Partial<Conversation>
  ): Promise<Conversation> {
    return this.put<Conversation>(`/chat/conversations/${id}`, data);
  }

  async deleteConversation(id: string, permanent = false): Promise<void> {
    return this.delete<void>(`/chat/conversations/${id}?permanent=${permanent}`);
  }

  async listConversations(params: {
    limit?: number;
    offset?: number;
    include_archived?: boolean;
    sort_by?: string;
    sort_order?: string;
    filters?: ConversationFilters;
  } = {}): Promise<PaginatedResponse<Conversation>> {
    return this.get<PaginatedResponse<Conversation>>('/chat/conversations', this.normalizeParams(params as Record<string, unknown>));
  }

  async archiveConversation(id: string): Promise<Conversation> {
    return this.put<Conversation>(`/chat/conversations/${id}/archive`, {});
  }

  async unarchiveConversation(id: string): Promise<Conversation> {
    return this.put<Conversation>(`/chat/conversations/${id}/unarchive`, {});
  }

  async pinConversation(id: string): Promise<Conversation> {
    return this.put<Conversation>(`/chat/conversations/${id}/pin`, {});
  }

  async unpinConversation(id: string): Promise<Conversation> {
    return this.put<Conversation>(`/chat/conversations/${id}/unpin`, {});
  }

  async bulkUpdateConversations(
    ids: string[],
    updates: Partial<Conversation>
  ): Promise<{ updated_count: number; updates_applied: string[] }> {
    return this.put('/chat/conversations/bulk', {
      conversation_ids: ids,
      updates,
    });
  }

  async bulkDeleteConversations(
    ids: string[],
    permanent = false
  ): Promise<{ deleted_count: number }> {
    return this.post('/chat/conversations/bulk-delete', {
      conversation_ids: ids,
      permanent,
    });
  }

  // Search
  async searchConversations(params: {
    query: string;
    limit?: number;
    offset?: number;
    filters?: ConversationFilters;
    search_in?: string[];
  }): Promise<PaginatedResponse<Conversation>> {
    return this.get<PaginatedResponse<Conversation>>('/chat/conversations/search', this.normalizeParams(params as Record<string, unknown>));
  }

  async getSearchSuggestions(query: string): Promise<string[]> {
    return this.get<string[]>(`/chat/conversations/suggestions?q=${encodeURIComponent(query)}`);
  }

  async saveSearch(data: {
    name: string;
    query: string;
    filters: ConversationFilters;
  }): Promise<{ id: string; name: string; created_at: string }> {
    return this.post('/chat/conversations/saved-searches', data);
  }

  async getSavedSearches(): Promise<Array<{
    id: string;
    name: string;
    query: string;
    filters: ConversationFilters;
    created_at: string;
  }>> {
    return this.get('/chat/conversations/saved-searches');
  }

  async deleteSavedSearch(id: string): Promise<void> {
    return this.delete(`/chat/conversations/saved-searches/${id}`);
  }

  async getSearchAnalytics(days = 30): Promise<{
    popular_searches: Array<{ query: string; count: number }>;
    search_trends: Array<{ date: string; search_count: number }>;
    total_searches: number;
    average_result_count: number;
    search_success_rate: number;
  }> {
    return this.get(`/chat/conversations/search/analytics?days=${days}`);
  }

  // Export/Import
  async exportConversations(params: {
    conversation_ids?: string[];
    format: 'json' | 'csv' | 'pdf';
    include_messages?: boolean;
    date_from?: string;
    date_to?: string;
    include_archived?: boolean;
  }): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/chat/conversations/export?${this.buildSearchParams(params)}`, {
      headers: this.defaultHeaders,
    });

    if (!response.ok) {
      throw new Error('Failed to export conversations');
    }

    return response.blob();
  }
  
  async importConversations(
    file: File,
    mergeStrategy: 'skip_duplicates' | 'overwrite' = 'skip_duplicates'
  ): Promise<{
    imported_count: number;
    skipped_count: number;
    error_count: number;
    errors: string[];
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('merge_strategy', mergeStrategy);

    const response = await fetch(`${this.baseUrl}/chat/conversations/import`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to import conversations');
    }

    return response.json();
  }

  // Analytics
  async getConversationStats(days = 30): Promise<ConversationStats> {
    return this.get<ConversationStats>(`/chat/conversations/stats?days=${days}`);
  }

  async getConversationAnalytics(days = 30): Promise<{
    conversation_analytics: {
      basic_stats: {
        total_conversations: number;
        unique_providers: number;
        average_messages_per_conversation: number;
        total_messages: number;
        active_days: number;
      };
      duration_stats: {
        average_duration_seconds: number;
        minimum_duration_seconds: number;
        maximum_duration_seconds: number;
      };
      daily_trends: Array<{
        date: string;
        conversations_created: number;
        unique_providers: number;
      }>;
      hourly_patterns: Array<{
        hour: number;
        conversations: number;
      }>;
    };
    message_analytics: MessageStats;
    provider_analytics: Array<{
      provider_id: string;
      conversation_count: number;
      message_count: number;
      average_processing_time_ms: number;
      average_tokens_per_message: number;
      total_tokens: number;
    }>;
    usage_patterns: {
      daily_activity: Array<{
        date: string;
        message_count: number;
        conversation_count: number;
        average_processing_time_ms: number;
      }>;
      hourly_activity: Array<{
        hour: number;
        message_count: number;
        conversation_count: number;
      }>;
      day_of_week_patterns: Array<{
        day_of_week: number;
        message_count: number;
        conversation_count: number;
      }>;
      conversation_length_distribution: Array<{
        length_category: string;
        count: number;
      }>;
    };
    engagement_metrics: {
      active_days: number;
      active_days_percentage: number;
      conversation_completion_rate: number;
      average_session_duration_seconds: number;
      average_response_time_seconds: number;
      engagement_score: number;
      engagement_grade: string;
    };
  }> {
    return this.get(`/chat/conversations/analytics?days=${days}`);
  }

  async getTopConversations(days = 30, limit = 10): Promise<{
    top_by_messages: Array<{
      conversation_id: string;
      title: string;
      provider_id: string;
      message_count: number;
      created_at: string;
      updated_at: string;
    }>;
    top_by_duration: Array<{
      conversation_id: string;
      title: string;
      provider_id: string;
      message_count: number;
      created_at: string;
      updated_at: string;
      duration_seconds: number;
    }>;
  }> {
    return this.get(`/chat/conversations/top?days=${days}&limit=${limit}`);
  }
}

// Message API Service
export class MessageService extends ApiClient {
  // Message CRUD
  async sendMessage(
    conversationId: string,
    data: {
      content: string;
      metadata?: Record<string, unknown>;
      parent_message_id?: string;
      is_streaming?: boolean;
    }
  ): Promise<Message> {
    return this.post<Message>(`/chat/conversations/${conversationId}/messages`, data);
  }

  async getMessage(id: string): Promise<Message> {
    return this.get<Message>(`/chat/messages/${id}`);
  }

  async updateMessage(
    id: string,
    data: Partial<Message>
  ): Promise<Message> {
    return this.put<Message>(`/chat/messages/${id}`, data);
  }

  async deleteMessage(id: string, permanent = false): Promise<void> {
    return this.delete<void>(`/chat/messages/${id}?permanent=${permanent}`);
  }

  async listMessages(
    conversationId: string,
    params: {
      limit?: number;
      offset?: number;
      filters?: MessageFilters;
    } = {}
  ): Promise<PaginatedResponse<Message>> {
    return this.get<PaginatedResponse<Message>>(
      `/chat/conversations/${conversationId}/messages`,
      this.normalizeParams(params as Record<string, unknown>)
    );
  }

  async searchMessages(params: {
    query: string;
    conversation_ids?: string[];
    limit?: number;
    offset?: number;
    filters?: MessageFilters;
  }): Promise<PaginatedResponse<Message>> {
    return this.get<PaginatedResponse<Message>>('/chat/messages/search', this.normalizeParams(params as Record<string, unknown>));
  }

  // Message threading
  async getMessageThread(rootMessageId: string): Promise<Message[]> {
    return this.get<Message[]>(`/chat/messages/${rootMessageId}/thread`);
  }

  async replyToMessage(
    parentMessageId: string,
    data: {
      content: string;
      metadata?: Record<string, unknown>;
    }
  ): Promise<Message> {
    return this.post<Message>(`/chat/messages/${parentMessageId}/reply`, data);
  }

  async forwardMessage(
    messageId: string,
    data: {
      target_conversation_id: string;
      add_context?: boolean;
    }
  ): Promise<Message> {
    return this.post<Message>(`/chat/messages/${messageId}/forward`, data);
  }

  // Message reactions
  async addReaction(messageId: string, reaction: string): Promise<Message> {
    return this.post<Message>(`/chat/messages/${messageId}/reactions`, { reaction });
  }

  async removeReaction(messageId: string, reaction: string): Promise<Message> {
    return this.delete<Message>(`/chat/messages/${messageId}/reactions/${reaction}`);
  }

  async getReactions(messageId: string): Promise<Record<string, string[]>> {
    return this.get<Record<string, string[]>>(`/chat/messages/${messageId}/reactions`);
  }

  // Message importance
  async markImportant(
    messageId: string,
    data: {
      is_important: boolean;
      important_note?: string;
    }
  ): Promise<Message> {
    return this.put<Message>(`/chat/messages/${messageId}/importance`, data);
  }

  async getImportantMessages(conversationId?: string): Promise<Message[]> {
    const params = conversationId ? { conversation_id: conversationId } : undefined;
    return this.get<Message[]>(`/chat/messages/important`, params ? this.normalizeParams(params) : undefined);
  }

  // Message attachments
  async getAttachments(messageId: string): Promise<Attachment[]> {
    return this.get<Attachment[]>(`/chat/messages/${messageId}/attachments`);
  }

  async uploadAttachment(
    messageId: string,
    file: File
  ): Promise<Attachment> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/chat/messages/${messageId}/attachments`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload attachment');
    }

    return response.json();
  }

  async downloadAttachment(attachmentId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/chat/attachments/${attachmentId}/download`, {
      headers: this.defaultHeaders,
    });

    if (!response.ok) {
      throw new Error('Failed to download attachment');
    }

    return response.blob();
  }

  async deleteAttachment(attachmentId: string): Promise<void> {
    return this.delete(`/chat/attachments/${attachmentId}`);
  }

  // Message analytics
  async getMessageStats(
    conversationId?: string,
    days = 30
  ): Promise<{
    role_stats: Array<{
      role: string;
      count: number;
      average_tokens: number;
      total_processing_time_ms: number;
    }>;
    daily_volume: Array<{
      date: string;
      message_count: number;
      average_processing_time_ms: number;
    }>;
    provider_performance: Array<{
      provider_id: string;
      message_count: number;
      average_processing_time_ms: number;
      average_tokens: number;
    }>;
    attachment_stats: {
      total_attachments: number;
      messages_with_attachments: number;
      average_file_size: number;
    };
  }> {
    const params = conversationId ? { conversation_id: conversationId, days } : { days };
    return this.get(`/chat/messages/analytics?${this.buildSearchParams(params)}`);
  }

  async exportMessages(params: {
    conversation_id?: string;
    message_ids?: string[];
    format: 'json' | 'csv' | 'pdf';
    include_attachments?: boolean;
    date_from?: string;
    date_to?: string;
  }): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/chat/messages/export?${this.buildSearchParams(params)}`, {
      headers: this.defaultHeaders,
    });

    if (!response.ok) {
      throw new Error('Failed to export messages');
    }

    return response.blob();
  }
}

// Real-time service
export class RealtimeService extends ApiClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.baseUrl.replace(/^http/, 'ws') + '/chat/ws';
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  private handleMessage(data: unknown): void {
    // This would emit events that can be listened to by components
    window.dispatchEvent(new CustomEvent('conversation-realtime', { detail: data }));
  }

  // Real-time actions
  sendTypingIndicator(conversationId: string, isTyping: boolean): void {
    this.send({
      type: 'typing_indicator',
      payload: {
        conversation_id: conversationId,
        is_typing: isTyping,
      },
    });
  }

  subscribeToConversation(conversationId: string): void {
    this.send({
      type: 'subscribe',
      payload: {
        conversation_id: conversationId,
      },
    });
  }

  unsubscribeFromConversation(conversationId: string): void {
    this.send({
      type: 'unsubscribe',
      payload: {
        conversation_id: conversationId,
      },
    });
  }
}

// Export singleton instances
export const conversationService = new ConversationService();
export const messageService = new MessageService();
export const realtimeService = new RealtimeService();

// Utility functions
export const conversationUtils = {
  formatDate: (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  },

  formatMessageTime: (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 1) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffMins < 1440) { // 24 hours
      return `${Math.floor(diffMins / 60)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  },

  truncateText: (text: string, maxLength: number): string => {
    if (text.length <= maxLength) {
      return text;
    }
    return text.substring(0, maxLength) + '...';
  },

  extractKeywords: (text: string): string[] => {
    // Simple keyword extraction - in production, this would use NLP
    return text
      .toLowerCase()
      .split(/\s+/)
      .filter(word => word.length > 3)
      .slice(0, 5);
  },

  calculateReadingTime: (text: string): number => {
    const wordsPerMinute = 200;
    const wordCount = text.split(/\s+/).length;
    return Math.ceil(wordCount / wordsPerMinute);
  },

  getConversationPreview: (conversation: Conversation, maxLength = 100): string => {
    // This would typically get the first user message as preview
    // For now, return a truncated title
    return conversationUtils.truncateText(conversation.title || 'Untitled', maxLength);
  },

  getMessagePreview: (message: Message, maxLength = 150): string => {
    return conversationUtils.truncateText(message.content, maxLength);
  },

  isConversationActive: (conversation: Conversation): boolean => {
    const now = new Date();
    const lastUpdated = new Date(conversation.updated_at);
    const hoursSinceUpdate = (now.getTime() - lastUpdated.getTime()) / (1000 * 60 * 60);
    
    // Consider active if updated in last 24 hours
    return hoursSinceUpdate <= 24;
  },

  getConversationDuration: (conversation: Conversation): string => {
    const created = new Date(conversation.created_at);
    const updated = new Date(conversation.updated_at);
    const diffMs = updated.getTime() - created.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 60) {
      return `${diffMins}m`;
    } else if (diffMins < 1440) { // 24 hours
      return `${Math.floor(diffMins / 60)}h ${diffMins % 60}m`;
    } else {
      const days = Math.floor(diffMins / 1440);
      const hours = Math.floor((diffMins % 1440) / 60);
      const mins = diffMins % 60;
      return `${days}d ${hours}h ${mins}m`;
    }
  },
};

export default conversationService;
