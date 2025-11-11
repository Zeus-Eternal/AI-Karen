// Shared Conversation History Component
// Framework-agnostic conversation history management and display

import { ChatMessage, Theme } from '../../abstractions/types';
import { formatRelativeTime, groupMessagesByDate, getMessageStats } from './MessageBubble';
import { storageManager, eventEmitter } from '../../abstractions/utils';
import { STORAGE_KEYS } from '../../abstractions/config';

export interface ConversationHistoryOptions {
  maxConversations?: number;
  enableSearch?: boolean;
  enableGrouping?: boolean;
  enableExport?: boolean;
  showStats?: boolean;
  autoSave?: boolean;
  groupByDate?: boolean;
}

export interface ConversationSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  summary?: string;
  tags?: string[];
}

export interface ConversationHistoryState {
  conversations: ConversationSession[];
  currentConversationId: string | null;
  searchQuery: string;
  filteredConversations: ConversationSession[];
  isLoading: boolean;
  selectedConversations: string[];
}

export interface ConversationHistoryCallbacks {
  onConversationSelect?: (conversation: ConversationSession) => void;
  onConversationDelete?: (conversationId: string) => void;
  onConversationExport?: (conversations: ConversationSession[]) => void;
  onSearchChange?: (query: string) => void;
}

export class SharedConversationHistory {
  private state: ConversationHistoryState;
  private options: ConversationHistoryOptions;
  private callbacks: ConversationHistoryCallbacks;
  private theme: Theme;

  constructor(
    theme: Theme,
    options: ConversationHistoryOptions = {},
    callbacks: ConversationHistoryCallbacks = {}
  ) {
    this.theme = theme;
    this.options = {
      maxConversations: 100,
      enableSearch: true,
      enableGrouping: true,
      enableExport: true,
      showStats: true,
      autoSave: true,
      groupByDate: true,
      ...options
    };
    this.callbacks = callbacks;

    this.state = {
      conversations: [],
      currentConversationId: null,
      searchQuery: '',
      filteredConversations: [],
      isLoading: false,
      selectedConversations: []
    };

    this.loadConversations();
  }

  // Get current state
  getState(): ConversationHistoryState {
    return { ...this.state };
  }

  // Update state
  updateState(newState: Partial<ConversationHistoryState>): void {
    this.state = { ...this.state, ...newState };
    this.filterConversations();
  }

  // Load conversations from storage
  private loadConversations(): void {
    try {
      this.updateState({ isLoading: true });
      
      const savedConversations = storageManager.get(`${STORAGE_KEYS.MESSAGES}-history`);
      if (savedConversations && Array.isArray(savedConversations)) {
        const conversations = savedConversations.map(conv => ({
          ...conv,
          createdAt: new Date(conv.createdAt),
          updatedAt: new Date(conv.updatedAt),
          messages: conv.messages.map((msg: unknown) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
        }));
        
        this.updateState({ 
          conversations,
          isLoading: false 
        });
      } else {
        this.updateState({ isLoading: false });
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error);
      this.updateState({ isLoading: false });
    }
  }

  // Save conversations to storage
  private saveConversations(): void {
    if (!this.options.autoSave) return;

    try {
      const conversationsToSave = this.state.conversations.slice(0, this.options.maxConversations);
      storageManager.set(`${STORAGE_KEYS.MESSAGES}-history`, conversationsToSave);
    } catch (error) {
      console.error('Failed to save conversation history:', error);
    }
  }

  // Add or update a conversation
  addOrUpdateConversation(messages: ChatMessage[], title?: string): string {
    const existingIndex = this.state.conversations.findIndex(
      conv => conv.id === this.state.currentConversationId
    );

    const conversationId = this.state.currentConversationId || this.generateConversationId();
    const now = new Date();

    const conversation: ConversationSession = {
      id: conversationId,
      title: title || this.generateConversationTitle(messages),
      messages: [...messages],
      createdAt: existingIndex >= 0 ? this.state.conversations[existingIndex].createdAt : now,
      updatedAt: now,
      messageCount: messages.length,
      summary: this.generateConversationSummary(messages),
      tags: this.extractTags(messages)
    };

    let newConversations: ConversationSession[];
    
    if (existingIndex >= 0) {
      // Update existing conversation
      newConversations = [...this.state.conversations];
      newConversations[existingIndex] = conversation;
    } else {
      // Add new conversation
      newConversations = [conversation, ...this.state.conversations];
    }

    // Limit number of conversations
    if (newConversations.length > this.options.maxConversations!) {
      newConversations = newConversations.slice(0, this.options.maxConversations);
    }

    this.updateState({ 
      conversations: newConversations,
      currentConversationId: conversationId
    });

    this.saveConversations();
    eventEmitter.emit('conversation-history-updated', conversation);

    return conversationId;
  }

  // Delete a conversation
  deleteConversation(conversationId: string): void {
    const newConversations = this.state.conversations.filter(
      conv => conv.id !== conversationId
    );

    this.updateState({ 
      conversations: newConversations,
      currentConversationId: this.state.currentConversationId === conversationId 
        ? null 
        : this.state.currentConversationId
    });

    this.saveConversations();

    if (this.callbacks.onConversationDelete) {
      this.callbacks.onConversationDelete(conversationId);
    }

    eventEmitter.emit('conversation-deleted', conversationId);
  }

  // Select a conversation
  selectConversation(conversationId: string): ConversationSession | null {
    const conversation = this.state.conversations.find(conv => conv.id === conversationId);
    
    if (conversation) {
      this.updateState({ currentConversationId: conversationId });
      
      if (this.callbacks.onConversationSelect) {
        this.callbacks.onConversationSelect(conversation);
      }

      eventEmitter.emit('conversation-selected', conversation);
      return conversation;
    }

    return null;
  }

  // Search conversations
  searchConversations(query: string): void {
    this.updateState({ searchQuery: query });
    
    if (this.callbacks.onSearchChange) {
      this.callbacks.onSearchChange(query);
    }
  }

  // Filter conversations based on search query
  private filterConversations(): void {
    let filtered = [...this.state.conversations];

    if (this.state.searchQuery.trim()) {
      const query = this.state.searchQuery.toLowerCase();
      filtered = filtered.filter(conv =>
        conv.title.toLowerCase().includes(query) ||
        conv.summary?.toLowerCase().includes(query) ||
        conv.messages.some(msg => 
          msg.content.toLowerCase().includes(query)
        ) ||
        conv.tags?.some(tag => 
          tag.toLowerCase().includes(query)
        )
      );
    }

    this.state.filteredConversations = filtered;
  }

  // Get grouped conversations
  getGroupedConversations(): Record<string, ConversationSession[]> {
    if (!this.options.groupByDate) {
      return { 'All Conversations': this.state.filteredConversations };
    }

    const groups: Record<string, ConversationSession[]> = {};
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

    this.state.filteredConversations.forEach(conv => {
      const convDate = new Date(conv.updatedAt.getFullYear(), conv.updatedAt.getMonth(), conv.updatedAt.getDate());
      
      let groupKey: string;
      if (convDate.getTime() === today.getTime()) {
        groupKey = 'Today';
      } else if (convDate.getTime() === yesterday.getTime()) {
        groupKey = 'Yesterday';
      } else if (convDate >= weekAgo) {
        groupKey = 'This Week';
      } else {
        groupKey = convDate.toLocaleDateString('en-US', { 
          year: 'numeric', 
          month: 'long' 
        });
      }

      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(conv);
    });

    // Sort groups by date (most recent first)
    const sortedGroups: Record<string, ConversationSession[]> = {};
    const groupOrder = ['Today', 'Yesterday', 'This Week'];
    
    groupOrder.forEach(key => {
      if (groups[key]) {
        sortedGroups[key] = groups[key];
      }
    });

    // Add remaining groups sorted by date
    Object.keys(groups)
      .filter(key => !groupOrder.includes(key))
      .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())
      .forEach(key => {
        sortedGroups[key] = groups[key];
      });

    return sortedGroups;
  }

  // Get conversation statistics
  getStatistics(): ConversationHistoryStats {
    const conversations = this.state.conversations;
    const totalMessages = conversations.reduce((sum, conv) => sum + conv.messageCount, 0);
    const totalConversations = conversations.length;
    
    const averageMessagesPerConversation = totalConversations > 0 
      ? Math.round(totalMessages / totalConversations) 
      : 0;

    const oldestConversation = conversations.length > 0 
      ? conversations.reduce((oldest, conv) => 
          conv.createdAt < oldest.createdAt ? conv : oldest
        )
      : null;

    const newestConversation = conversations.length > 0
      ? conversations.reduce((newest, conv) =>
          conv.updatedAt > newest.updatedAt ? conv : newest
        )
      : null;

    const allTags = conversations.flatMap(conv => conv.tags || []);
    const tagCounts = allTags.reduce((counts, tag) => {
      counts[tag] = (counts[tag] || 0) + 1;
      return counts;
    }, {} as Record<string, number>);

    const topTags = Object.entries(tagCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([tag, count]) => ({ tag, count }));

    return {
      totalConversations,
      totalMessages,
      averageMessagesPerConversation,
      oldestConversation: oldestConversation?.createdAt || null,
      newestConversation: newestConversation?.updatedAt || null,
      topTags,
      searchResultCount: this.state.filteredConversations.length
    };
  }

  // Export conversations
  exportConversations(format: 'json' | 'text' | 'csv', conversationIds?: string[]): string {
    const conversationsToExport = conversationIds
      ? this.state.conversations.filter(conv => conversationIds.includes(conv.id))
      : this.state.filteredConversations;

    if (this.callbacks.onConversationExport) {
      this.callbacks.onConversationExport(conversationsToExport);
    }

    switch (format) {
      case 'json':
        return JSON.stringify(conversationsToExport, null, 2);
      
      case 'csv':
        return this.exportToCsv(conversationsToExport);
      
      case 'text':
      default:
        return this.exportToText(conversationsToExport);
    }
  }

  // Clear all conversations
  clearHistory(): void {
    this.updateState({
      conversations: [],
      currentConversationId: null,
      filteredConversations: []
    });

    storageManager.remove(`${STORAGE_KEYS.MESSAGES}-history`);
    eventEmitter.emit('conversation-history-cleared');
  }

  // Get render data
  getRenderData(): ConversationHistoryRenderData {
    return {
      state: this.getState(),
      options: this.options,
      groupedConversations: this.getGroupedConversations(),
      statistics: this.options.showStats ? this.getStatistics() : null,
      theme: this.theme,
      handlers: {
        onSelect: (id: string) => this.selectConversation(id),
        onDelete: (id: string) => this.deleteConversation(id),
        onSearch: (query: string) => this.searchConversations(query),
        onExport: (format: 'json' | 'text' | 'csv', ids?: string[]) => 
          this.exportConversations(format, ids),
        onClear: () => this.clearHistory()
      }
    };
  }

  // Private helper methods
  private generateConversationId(): string {
    return `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateConversationTitle(messages: ChatMessage[]): string {
    const userMessages = messages.filter(msg => msg.role === 'user');
    if (userMessages.length === 0) return 'New Conversation';

    const firstUserMessage = userMessages[0].content;
    const title = firstUserMessage.length > 50 
      ? firstUserMessage.substring(0, 47) + '...'
      : firstUserMessage;

    return title || 'New Conversation';
  }

  private generateConversationSummary(messages: ChatMessage[]): string {
    const messageCount = messages.length;
    const userMessageCount = messages.filter(msg => msg.role === 'user').length;
    const assistantMessageCount = messages.filter(msg => msg.role === 'assistant').length;

    return `${messageCount} messages (${userMessageCount} from you, ${assistantMessageCount} from Karen)`;
  }

  private extractTags(messages: ChatMessage[]): string[] {
    const tags = new Set<string>();
    
    messages.forEach(msg => {
      if (msg.aiData?.keywords) {
        msg.aiData.keywords.forEach(keyword => tags.add(keyword.toLowerCase()));
      }
    });

    return Array.from(tags).slice(0, 10); // Limit to 10 tags
  }

  private exportToText(conversations: ConversationSession[]): string {
    let text = 'AI Karen Conversation History Export\n';
    text += '='.repeat(50) + '\n\n';

    conversations.forEach(conv => {
      text += `Conversation: ${conv.title}\n`;
      text += `Created: ${conv.createdAt.toLocaleString()}\n`;
      text += `Updated: ${conv.updatedAt.toLocaleString()}\n`;
      text += `Messages: ${conv.messageCount}\n`;
      if (conv.tags && conv.tags.length > 0) {
        text += `Tags: ${conv.tags.join(', ')}\n`;
      }
      text += '-'.repeat(30) + '\n\n';

      conv.messages.forEach(msg => {
        const role = msg.role === 'user' ? 'You' : 'AI Karen';
        text += `[${msg.timestamp.toLocaleString()}] ${role}: ${msg.content}\n\n`;
      });

      text += '='.repeat(50) + '\n\n';
    });

    return text;
  }

  private exportToCsv(conversations: ConversationSession[]): string {
    const headers = [
      'Conversation ID',
      'Title',
      'Created At',
      'Updated At',
      'Message Count',
      'Tags',
      'Message Role',
      'Message Content',
      'Message Timestamp'
    ];

    let csv = headers.join(',') + '\n';

    conversations.forEach(conv => {
      conv.messages.forEach(msg => {
        const row = [
          conv.id,
          `"${conv.title.replace(/"/g, '""')}"`,
          conv.createdAt.toISOString(),
          conv.updatedAt.toISOString(),
          conv.messageCount.toString(),
          `"${(conv.tags || []).join(', ')}"`,
          msg.role,
          `"${msg.content.replace(/"/g, '""')}"`,
          msg.timestamp.toISOString()
        ];
        csv += row.join(',') + '\n';
      });
    });

    return csv;
  }
}

// Supporting interfaces
export interface ConversationHistoryStats {
  totalConversations: number;
  totalMessages: number;
  averageMessagesPerConversation: number;
  oldestConversation: Date | null;
  newestConversation: Date | null;
  topTags: Array<{ tag: string; count: number }>;
  searchResultCount: number;
}

export interface ConversationHistoryRenderData {
  state: ConversationHistoryState;
  options: ConversationHistoryOptions;
  groupedConversations: Record<string, ConversationSession[]>;
  statistics: ConversationHistoryStats | null;
  theme: Theme;
  handlers: {
    onSelect: (id: string) => ConversationSession | null;
    onDelete: (id: string) => void;
    onSearch: (query: string) => void;
    onExport: (format: 'json' | 'text' | 'csv', ids?: string[]) => string;
    onClear: () => void;
  };
}

// Utility functions
export function createConversationHistory(
  theme: Theme,
  options: ConversationHistoryOptions = {},
  callbacks: ConversationHistoryCallbacks = {}
): SharedConversationHistory {
  return new SharedConversationHistory(theme, options, callbacks);
}