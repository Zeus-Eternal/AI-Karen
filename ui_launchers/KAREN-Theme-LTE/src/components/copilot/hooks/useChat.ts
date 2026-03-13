import { useState, useEffect, useCallback, useRef } from 'react';
import type { ChatMessage, Conversation } from '../components/chat/types';
import { ConversationService } from '../services/ConversationService';

interface UseChatOptions {
  initialConversationId?: string;
  autoCreateConversation?: boolean;
  persistConversations?: boolean;
}

interface UseChatResult {
  // Conversation state
  conversations: Conversation[];
  activeConversation: Conversation | null;
  isLoading: boolean;
  error: string | null;
  
  // Message state
  messages: ChatMessage[];
  isTyping: boolean;
  
  // Actions
  createConversation: (title?: string, agent?: string) => Conversation;
  selectConversation: (conversationId: string) => void;
  deleteConversation: (conversationId: string) => boolean;
  updateConversation: (conversationId: string, updates: Partial<Conversation>) => Conversation | null;
  
  // Message actions
  sendMessage: (content: string, role?: 'user' | 'assistant' | 'system') => void;
  addMessage: (message: Omit<ChatMessage, 'id'>) => void;
  updateMessage: (messageId: string, updates: Partial<ChatMessage>) => void;
  deleteMessage: (messageId: string) => void;
  
  // Search and filter
  searchConversations: (query: string) => Conversation[];
  filterConversationsByTag: (tag: string) => Conversation[];
  filterConversationsByDate: (startDate: Date, endDate: Date) => Conversation[];
  
  // Export and import
  exportConversation: (conversationId: string) => string | null;
  importConversation: (jsonData: string) => Conversation | null;
  
  // Utility
  clearAllConversations: () => void;
  generateSummary: (conversationId: string) => string | null;
  generateTags: (conversationId: string) => string[];
  
  // Typing indicators
  setTyping: (isTyping: boolean) => void;
}

/**
 * React hook for managing chat state and conversation history
 */
export const useChat = (options: UseChatOptions = {}): UseChatResult => {
  const {
    initialConversationId,
    autoCreateConversation = true,
    persistConversations = true
  } = options;
  
  // State
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isTyping, setIsTypingState] = useState(false);
  
  // Refs
  const isMountedRef = useRef(true);
  
  // Load conversations from storage
  const loadConversations = useCallback(() => {
    if (!persistConversations) {
      setIsLoading(false);
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      const loadedConversations = ConversationService.getConversations();
      setConversations(loadedConversations);
      
      // Set active conversation
      const activeId = initialConversationId || ConversationService.getActiveConversationId();
      if (activeId) {
        const conversation = loadedConversations.find(c => c.id === activeId);
        if (conversation) {
          setActiveConversation(conversation);
        } else if (loadedConversations.length > 0) {
          // Fallback to first conversation if active not found
          setActiveConversation(loadedConversations[0] ?? null);
          ConversationService.setActiveConversationId(loadedConversations[0]?.id ?? '');
        }
      } else if (loadedConversations.length > 0) {
        // Fallback to first conversation
        setActiveConversation(loadedConversations[0] ?? null);
        ConversationService.setActiveConversationId(loadedConversations[0]?.id ?? '');
      } else if (autoCreateConversation) {
        // Create a new conversation if none exist
        const newConversation = ConversationService.createConversation();
        setConversations([newConversation]);
        setActiveConversation(newConversation);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setError('Failed to load conversations');
    } finally {
      setIsLoading(false);
    }
  }, [initialConversationId, autoCreateConversation, persistConversations]);
  
  // Initialize
  useEffect(() => {
    loadConversations();
    
    return () => {
      isMountedRef.current = false;
    };
  }, [loadConversations]);
  
  // Update conversations when active conversation changes
  useEffect(() => {
    if (activeConversation && persistConversations) {
      try {
        const updatedConversations = conversations.map(conv => 
          conv.id === activeConversation.id ? activeConversation : conv
        );
        setConversations(updatedConversations);
        ConversationService.saveConversations(updatedConversations);
      } catch (err) {
        console.error('Failed to save conversations:', err);
        setError('Failed to save conversations');
      }
    }
  }, [activeConversation, conversations, persistConversations]);
  
  // Create a new conversation
  const createConversation = useCallback((title?: string, agent?: string): Conversation => {
    try {
      const newConversation = ConversationService.createConversation(title, agent);
      
      if (isMountedRef.current) {
        setConversations(prev => [newConversation, ...prev]);
        setActiveConversation(newConversation);
      }
      
      return newConversation;
    } catch (err) {
      console.error('Failed to create conversation:', err);
      setError('Failed to create conversation');
      throw err;
    }
  }, []);
  
  // Select a conversation
  const selectConversation = useCallback((conversationId: string) => {
    try {
      const conversation = conversations.find(c => c.id === conversationId);
      
      if (conversation) {
        setActiveConversation(conversation);
        if (persistConversations) {
          ConversationService.setActiveConversationId(conversationId);
        }
      } else {
        setError('Conversation not found');
      }
    } catch (err) {
      console.error('Failed to select conversation:', err);
      setError('Failed to select conversation');
    }
  }, [conversations, persistConversations]);
  
  // Delete a conversation
  const deleteConversation = useCallback((conversationId: string): boolean => {
    try {
      const success = ConversationService.deleteConversation(conversationId);
      
      if (success && isMountedRef.current) {
        setConversations(prev => prev.filter(c => c.id !== conversationId));
        
        // If we deleted the active conversation, select another one
        if (activeConversation?.id === conversationId) {
          const remainingConversations = conversations.filter(c => c.id !== conversationId);
          
          if (remainingConversations.length > 0) {
            setActiveConversation(remainingConversations[0] ?? null);
            if (persistConversations) {
              ConversationService.setActiveConversationId(remainingConversations[0]?.id ?? '');
            }
          } else if (autoCreateConversation) {
            const newConversation = ConversationService.createConversation();
            setConversations([newConversation]);
            setActiveConversation(newConversation);
          } else {
            setActiveConversation(null);
            if (persistConversations) {
              ConversationService.clearActiveConversationId();
            }
          }
        }
      }
      
      return success;
    } catch (err) {
      console.error('Failed to delete conversation:', err);
      setError('Failed to delete conversation');
      return false;
    }
  }, [conversations, activeConversation, autoCreateConversation, persistConversations]);
  
  // Update a conversation
  const updateConversation = useCallback((conversationId: string, updates: Partial<Conversation>): Conversation | null => {
    try {
      const updatedConversation = ConversationService.updateConversation(conversationId, updates);
      
      if (updatedConversation && isMountedRef.current) {
        setConversations(prev => 
          prev.map(c => c.id === conversationId ? updatedConversation : c)
        );
        
        if (activeConversation?.id === conversationId) {
          setActiveConversation(updatedConversation);
        }
      }
      
      return updatedConversation;
    } catch (err) {
      console.error('Failed to update conversation:', err);
      setError('Failed to update conversation');
      return null;
    }
  }, [activeConversation]);
  
  // Send a message
  const sendMessage = useCallback((content: string, role: 'user' | 'assistant' | 'system' = 'user') => {
    if (!activeConversation) {
      setError('No active conversation');
      return;
    }
    
    if (!content.trim()) {
      return;
    }
    
    try {
      const newMessage: Omit<ChatMessage, 'id'> = {
        content,
        role,
        timestamp: new Date()
      };
      
      const updatedConversation = ConversationService.addMessage(activeConversation.id, newMessage);
      
      if (updatedConversation && isMountedRef.current) {
        setActiveConversation(updatedConversation);
        setConversations(prev => 
          prev.map(c => c.id === activeConversation.id ? updatedConversation : c)
        );
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message');
    }
  }, [activeConversation]);
  
  // Add a message
  const addMessage = useCallback((message: Omit<ChatMessage, 'id'>) => {
    if (!activeConversation) {
      setError('No active conversation');
      return;
    }
    
    try {
      const updatedConversation = ConversationService.addMessage(activeConversation.id, message);
      
      if (updatedConversation && isMountedRef.current) {
        setActiveConversation(updatedConversation);
        setConversations(prev => 
          prev.map(c => c.id === activeConversation.id ? updatedConversation : c)
        );
      }
    } catch (err) {
      console.error('Failed to add message:', err);
      setError('Failed to add message');
    }
  }, [activeConversation]);
  
  // Update a message
  const updateMessage = useCallback((messageId: string, updates: Partial<ChatMessage>) => {
    if (!activeConversation) {
      setError('No active conversation');
      return;
    }
    
    try {
      const updatedConversation = ConversationService.updateMessage(activeConversation.id, messageId, updates);
      
      if (updatedConversation && isMountedRef.current) {
        setActiveConversation(updatedConversation);
        setConversations(prev => 
          prev.map(c => c.id === activeConversation.id ? updatedConversation : c)
        );
      }
    } catch (err) {
      console.error('Failed to update message:', err);
      setError('Failed to update message');
    }
  }, [activeConversation]);
  
  // Delete a message
  const deleteMessage = useCallback((messageId: string) => {
    if (!activeConversation) {
      setError('No active conversation');
      return;
    }
    
    try {
      const updatedConversation = ConversationService.deleteMessage(activeConversation.id, messageId);
      
      if (updatedConversation && isMountedRef.current) {
        setActiveConversation(updatedConversation);
        setConversations(prev => 
          prev.map(c => c.id === activeConversation.id ? updatedConversation : c)
        );
      }
    } catch (err) {
      console.error('Failed to delete message:', err);
      setError('Failed to delete message');
    }
  }, [activeConversation]);
  
  // Search conversations
  const searchConversations = useCallback((query: string): Conversation[] => {
    try {
      return ConversationService.searchConversations(query);
    } catch (err) {
      console.error('Failed to search conversations:', err);
      setError('Failed to search conversations');
      return [];
    }
  }, []);
  
  // Filter conversations by tag
  const filterConversationsByTag = useCallback((tag: string): Conversation[] => {
    try {
      return ConversationService.filterConversationsByTag(tag);
    } catch (err) {
      console.error('Failed to filter conversations by tag:', err);
      setError('Failed to filter conversations by tag');
      return [];
    }
  }, []);
  
  // Filter conversations by date
  const filterConversationsByDate = useCallback((startDate: Date, endDate: Date): Conversation[] => {
    try {
      return ConversationService.filterConversationsByDate(startDate, endDate);
    } catch (err) {
      console.error('Failed to filter conversations by date:', err);
      setError('Failed to filter conversations by date');
      return [];
    }
  }, []);
  
  // Export conversation
  const exportConversation = useCallback((conversationId: string): string | null => {
    try {
      return ConversationService.exportConversation(conversationId);
    } catch (err) {
      console.error('Failed to export conversation:', err);
      setError('Failed to export conversation');
      return null;
    }
  }, []);
  
  // Import conversation
  const importConversation = useCallback((jsonData: string): Conversation | null => {
    try {
      const importedConversation = ConversationService.importConversation(jsonData);
      
      if (importedConversation && isMountedRef.current) {
        setConversations(prev => [importedConversation, ...prev]);
      }
      
      return importedConversation;
    } catch (err) {
      console.error('Failed to import conversation:', err);
      setError('Failed to import conversation');
      return null;
    }
  }, []);
  
  // Clear all conversations
  const clearAllConversations = useCallback(() => {
    try {
      ConversationService.clearAllConversations();
      
      if (isMountedRef.current) {
        setConversations([]);
        
        if (autoCreateConversation) {
          const newConversation = ConversationService.createConversation();
          setConversations([newConversation]);
          setActiveConversation(newConversation);
        } else {
          setActiveConversation(null);
        }
      }
    } catch (err) {
      console.error('Failed to clear conversations:', err);
      setError('Failed to clear conversations');
    }
  }, [autoCreateConversation]);
  
  // Generate summary
  const generateSummary = useCallback((conversationId: string): string | null => {
    try {
      return ConversationService.generateSummary(conversationId);
    } catch (err) {
      console.error('Failed to generate summary:', err);
      setError('Failed to generate summary');
      return null;
    }
  }, []);
  
  // Generate tags
  const generateTags = useCallback((conversationId: string): string[] => {
    try {
      return ConversationService.generateTags(conversationId);
    } catch (err) {
      console.error('Failed to generate tags:', err);
      setError('Failed to generate tags');
      return [];
    }
  }, []);
  
  // Set typing indicator
  const setTyping = useCallback((isTyping: boolean) => {
    setIsTypingState(isTyping);
  }, []);
  
  return {
    // Conversation state
    conversations,
    activeConversation,
    isLoading,
    error,
    
    // Message state
    messages: activeConversation?.messages || [],
    isTyping,
    
    // Actions
    createConversation,
    selectConversation,
    deleteConversation,
    updateConversation,
    
    // Message actions
    sendMessage,
    addMessage,
    updateMessage,
    deleteMessage,
    
    // Search and filter
    searchConversations,
    filterConversationsByTag,
    filterConversationsByDate,
    
    // Export and import
    exportConversation,
    importConversation,
    
    // Utility
    clearAllConversations,
    generateSummary,
    generateTags,
    
    // Typing indicators
    setTyping
  };
};

export default useChat;