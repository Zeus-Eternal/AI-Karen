import type { ChatMessage, Conversation } from '../components/chat/types';

// Storage key for localStorage
const CONVERSATIONS_STORAGE_KEY = 'copilot-conversations';
const ACTIVE_CONVERSATION_KEY = 'copilot-active-conversation';

/**
 * Service for managing conversation history with persistence
 */
export class ConversationService {
  /**
   * Get all conversations from storage
   */
  static getConversations(): Conversation[] {
    if (typeof window === 'undefined') {
      return [];
    }
    
    try {
      const stored = localStorage.getItem(CONVERSATIONS_STORAGE_KEY);
      if (!stored) {
        return [];
      }
      
      const conversations = JSON.parse(stored);
      
      // Convert date strings back to Date objects
      return conversations.map((conv: any) => ({
        ...conv,
        createdAt: new Date(conv.createdAt),
        updatedAt: new Date(conv.updatedAt),
        messages: conv.messages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
      }));
    } catch (error) {
      console.error('Failed to parse conversations from storage:', error);
      return [];
    }
  }
  
  /**
   * Save conversations to storage
   */
  static saveConversations(conversations: Conversation[]): void {
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      localStorage.setItem(CONVERSATIONS_STORAGE_KEY, JSON.stringify(conversations));
    } catch (error) {
      console.error('Failed to save conversations to storage:', error);
    }
  }
  
  /**
   * Get a conversation by ID
   */
  static getConversationById(id: string): Conversation | null {
    const conversations = this.getConversations();
    return conversations.find(conv => conv.id === id) || null;
  }
  
  /**
   * Create a new conversation
   */
  static createConversation(title?: string, agent?: string): Conversation {
    const newConversation: Conversation = {
      id: `conv-${Date.now()}`,
      title: title || `Conversation ${new Date().toLocaleString()}`,
      createdAt: new Date(),
      updatedAt: new Date(),
      messages: [],
      agent
    };
    
    const conversations = this.getConversations();
    conversations.unshift(newConversation); // Add to beginning
    this.saveConversations(conversations);
    
    // Set as active conversation
    this.setActiveConversationId(newConversation.id);
    
    return newConversation;
  }
  
  /**
   * Update a conversation
   */
  static updateConversation(id: string, updates: Partial<Conversation>): Conversation | null {
    const conversations = this.getConversations();
    const index = conversations.findIndex(conv => conv.id === id);
    
    if (index === -1) {
      return null;
    }
    
    const existingConversation = conversations[index];
    if (!existingConversation) {
      return null;
    }
 
    const updatedConversation = {
      ...existingConversation,
      ...updates,
      updatedAt: new Date()
    };
    
    conversations[index] = updatedConversation;
    this.saveConversations(conversations);
    
    return updatedConversation;
  }
  
  /**
   * Delete a conversation
   */
  static deleteConversation(id: string): boolean {
    const conversations = this.getConversations();
    const filteredConversations = conversations.filter(conv => conv.id !== id);
    
    if (filteredConversations.length === conversations.length) {
      return false; // Conversation not found
    }
    
    this.saveConversations(filteredConversations);
    
    // Clear active conversation if it was the deleted one
    const activeId = this.getActiveConversationId();
    if (activeId === id) {
      this.clearActiveConversationId();
    }
    
    return true;
  }
  
  /**
   * Add a message to a conversation
   */
  static addMessage(conversationId: string, message: Omit<ChatMessage, 'id'>): Conversation | null {
    const conversation = this.getConversationById(conversationId);
    
    if (!conversation) {
      return null;
    }
    
    const newMessage: ChatMessage = {
      ...message,
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    };
    
    const updatedMessages = [...conversation.messages, newMessage];
    
    return this.updateConversation(conversationId, {
      messages: updatedMessages
    });
  }
  
  /**
   * Update a message in a conversation
   */
  static updateMessage(conversationId: string, messageId: string, updates: Partial<ChatMessage>): Conversation | null {
    const conversation = this.getConversationById(conversationId);
    
    if (!conversation) {
      return null;
    }
    
    const updatedMessages = conversation.messages.map(msg => 
      msg.id === messageId ? { ...msg, ...updates } : msg
    );
    
    return this.updateConversation(conversationId, {
      messages: updatedMessages
    });
  }
  
  /**
   * Delete a message from a conversation
   */
  static deleteMessage(conversationId: string, messageId: string): Conversation | null {
    const conversation = this.getConversationById(conversationId);
    
    if (!conversation) {
      return null;
    }
    
    const updatedMessages = conversation.messages.filter(msg => msg.id !== messageId);
    
    return this.updateConversation(conversationId, {
      messages: updatedMessages
    });
  }
  
  /**
   * Get active conversation ID
   */
  static getActiveConversationId(): string | null {
    if (typeof window === 'undefined') {
      return null;
    }
    
    try {
      return localStorage.getItem(ACTIVE_CONVERSATION_KEY);
    } catch (error) {
      console.error('Failed to get active conversation ID from storage:', error);
      return null;
    }
  }
  
  /**
   * Set active conversation ID
   */
  static setActiveConversationId(id: string): void {
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      localStorage.setItem(ACTIVE_CONVERSATION_KEY, id);
    } catch (error) {
      console.error('Failed to save active conversation ID to storage:', error);
    }
  }
  
  /**
   * Clear active conversation ID
   */
  static clearActiveConversationId(): void {
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      localStorage.removeItem(ACTIVE_CONVERSATION_KEY);
    } catch (error) {
      console.error('Failed to clear active conversation ID from storage:', error);
    }
  }
  
  /**
   * Get active conversation
   */
  static getActiveConversation(): Conversation | null {
    const activeId = this.getActiveConversationId();
    if (!activeId) {
      return null;
    }
    
    return this.getConversationById(activeId);
  }
  
  /**
   * Search conversations by query
   */
  static searchConversations(query: string): Conversation[] {
    const conversations = this.getConversations();
    const lowerQuery = query.toLowerCase();
    
    return conversations.filter(conv => 
      conv.title.toLowerCase().includes(lowerQuery) ||
      conv.messages.some(msg => 
        msg.content.toLowerCase().includes(lowerQuery)
      ) ||
      (conv.summary && conv.summary.toLowerCase().includes(lowerQuery)) ||
      (conv.tags && conv.tags.some(tag => 
        tag.toLowerCase().includes(lowerQuery)
      ))
    );
  }
  
  /**
   * Filter conversations by tag
   */
  static filterConversationsByTag(tag: string): Conversation[] {
    const conversations = this.getConversations();
    
    return conversations.filter(conv => 
      conv.tags && conv.tags.includes(tag)
    );
  }
  
  /**
   * Filter conversations by date range
   */
  static filterConversationsByDate(startDate: Date, endDate: Date): Conversation[] {
    const conversations = this.getConversations();
    
    return conversations.filter(conv => {
      const convDate = new Date(conv.updatedAt);
      return convDate >= startDate && convDate <= endDate;
    });
  }
  
  /**
   * Export a conversation to JSON
   */
  static exportConversation(conversationId: string): string | null {
    const conversation = this.getConversationById(conversationId);
    
    if (!conversation) {
      return null;
    }
    
    try {
      return JSON.stringify(conversation, null, 2);
    } catch (error) {
      console.error('Failed to export conversation:', error);
      return null;
    }
  }
  
  /**
   * Import a conversation from JSON
   */
  static importConversation(jsonData: string): Conversation | null {
    try {
      const conversation = JSON.parse(jsonData);
      
      // Validate required fields
      if (!conversation.id || !conversation.title || !conversation.messages) {
        throw new Error('Invalid conversation format');
      }
      
      // Convert date strings back to Date objects
      conversation.createdAt = new Date(conversation.createdAt);
      conversation.updatedAt = new Date(conversation.updatedAt);
      conversation.messages = conversation.messages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }));
      
      // Save imported conversation
      const conversations = this.getConversations();
      conversations.unshift(conversation);
      this.saveConversations(conversations);
      
      return conversation;
    } catch (error) {
      console.error('Failed to import conversation:', error);
      return null;
    }
  }
  
  /**
   * Clear all conversations
   */
  static clearAllConversations(): void {
    if (typeof window === 'undefined') {
      return;
    }
    
    try {
      localStorage.removeItem(CONVERSATIONS_STORAGE_KEY);
      this.clearActiveConversationId();
    } catch (error) {
      console.error('Failed to clear conversations from storage:', error);
    }
  }
  
  /**
   * Get conversation statistics
   */
  static getConversationStats(): {
    totalConversations: number;
    totalMessages: number;
    oldestConversation?: Date;
    newestConversation?: Date;
    tags: Record<string, number>;
  } {
    const conversations = this.getConversations();
    
    if (conversations.length === 0) {
      return {
        totalConversations: 0,
        totalMessages: 0,
        tags: {}
      };
    }
    
    const totalMessages = conversations.reduce((sum, conv) => sum + conv.messages.length, 0);
    
    const dates = conversations.map(conv => new Date(conv.createdAt));
    const oldestConversation = new Date(Math.min(...dates.map(date => date.getTime())));
    const newestConversation = new Date(Math.max(...dates.map(date => date.getTime())));
    
    const tags: Record<string, number> = {};
    conversations.forEach(conv => {
      if (conv.tags) {
        conv.tags.forEach(tag => {
          tags[tag] = (tags[tag] || 0) + 1;
        });
      }
    });
    
    return {
      totalConversations: conversations.length,
      totalMessages,
      oldestConversation,
      newestConversation,
      tags
    };
  }
  
  /**
   * Generate a summary for a conversation
   */
  static generateSummary(conversationId: string): string | null {
    const conversation = this.getConversationById(conversationId);
    
    if (!conversation || conversation.messages.length === 0) {
      return null;
    }
    
    // Simple summary generation - in a real app, this might use an AI service
    const userMessages = conversation.messages
      .filter(msg => msg.role === 'user')
      .map(msg => msg.content);
    
    // Take first user message as a simple summary
    if (userMessages.length > 0) {
      const firstMessage = userMessages[0];
      if (firstMessage) {
        return firstMessage.length > 100
          ? firstMessage.substring(0, 100) + '...'
          : firstMessage;
      }
    }

    return 'Empty conversation';
  }
  
  /**
   * Generate tags for a conversation
   */
  static generateTags(conversationId: string): string[] {
    const conversation = this.getConversationById(conversationId);
    
    if (!conversation || conversation.messages.length === 0) {
      return [];
    }
    
    // Simple tag generation - in a real app, this might use an AI service
    const allText = conversation.messages
      .map(msg => msg.content.toLowerCase())
      .join(' ');
    
    // Simple keyword extraction
    const commonWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'];
    
    const words = allText
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 3 && !commonWords.includes(word));
    
    // Count word frequency
    const wordCount: Record<string, number> = {};
    words.forEach(word => {
      wordCount[word] = (wordCount[word] || 0) + 1;
    });
    
    // Get most frequent words as tags
    const sortedWords = Object.entries(wordCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([word]) => word);
    
    return sortedWords;
  }
}
