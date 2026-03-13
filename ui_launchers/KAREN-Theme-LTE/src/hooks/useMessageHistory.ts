/**
 * Message History Hooks - Custom hooks for message history management
 * Provides convenient hooks for message CRUD, pagination, threading, and search
 */

import { useCallback, useEffect, useState } from 'react';
import { useConversationStore, Message, MessageFilters } from '../stores/conversationStore';
import { useDebounce } from './useDebounce';
import { useToast } from './useToast';

type MessageAttachment = {
  id: string;
  filename?: string;
} & Record<string, unknown>;

// Hook for message CRUD operations
export const useMessageCRUD = () => {
  const {
    sendMessage,
    updateMessage,
    deleteMessage,
    setError,
    clearError,
  } = useConversationStore();
  
  const { showToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  
  const handleSendMessage = useCallback(async (
    conversationId: string,
    content: string,
    metadata?: Record<string, unknown>
  ) => {
    setIsLoading(true);
    clearError();
    
    try {
      await sendMessage(conversationId, content, metadata);
      showToast('Message sent successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [sendMessage, setError, clearError, showToast]);

  const handleUpdateMessage = useCallback(async (
    messageId: string,
    updates: Partial<Message>
  ) => {
    setIsLoading(true);
    clearError();
    
    try {
      await updateMessage(messageId, updates);
      showToast('Message updated successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update message';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [updateMessage, setError, clearError, showToast]);

  const handleDeleteMessage = useCallback(async (
    messageId: string,
    permanent = false
  ) => {
    const confirmMessage = permanent 
      ? 'Are you sure you want to permanently delete this message? This action cannot be undone.'
      : 'Are you sure you want to delete this message?';
    
    if (!window.confirm(confirmMessage)) {
      return;
    }

    setIsLoading(true);
    clearError();
    
    try {
      await deleteMessage(messageId, permanent);
      showToast(`Message ${permanent ? 'deleted permanently' : 'deleted'} successfully`, 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete message';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [deleteMessage, setError, clearError, showToast]);

  return {
    sendMessage: handleSendMessage,
    updateMessage: handleUpdateMessage,
    deleteMessage: handleDeleteMessage,
    isLoading,
  };
};

// Hook for message pagination
export const useMessagePagination = (conversationId: string) => {
  const {
    messages,
    loadMessages,
    loadMoreMessages,
    messagePagination,
    isLoading,
    error,
  } = useConversationStore();

  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadMore = useCallback(async () => {
    const pagination = messagePagination[conversationId];
    if (!pagination || !pagination.hasMore || isLoading || isRefreshing) {
      return;
    }

    await loadMoreMessages(conversationId);
  }, [conversationId, messagePagination, isLoading, isRefreshing, loadMoreMessages]);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await loadMessages(conversationId, true);
    } finally {
      setIsRefreshing(false);
    }
  }, [conversationId, loadMessages]);

  const pagination = messagePagination[conversationId] || {
    page: 1,
    perPage: 100,
    total: 0,
    hasMore: false,
    isLoading: false,
  };

  return {
    messages: messages[conversationId] || [],
    pagination,
    loadMore,
    refresh,
    isLoading: isLoading || isRefreshing || pagination.isLoading,
    error,
    hasMore: pagination.hasMore,
    totalCount: pagination.total,
  };
};

// Hook for message threading
export const useMessageThreading = (conversationId: string) => {
  const { messages } = useConversationStore();
  const [rootMessages, setRootMessages] = useState<Message[]>([]);
  const [threadedMessages, setThreadedMessages] = useState<Record<string, Message[]>>({});

  useEffect(() => {
    const conversationMessages = messages[conversationId] || [];
    
    // Find root messages (messages without parent)
    const roots = conversationMessages.filter(msg => !msg.parent_message_id);
    setRootMessages(roots);

    // Group messages by thread
    const threads: Record<string, Message[]> = {};
    conversationMessages.forEach(msg => {
      if (msg.parent_message_id) {
        const thread = threads[msg.parent_message_id];
        if (!thread) {
          threads[msg.parent_message_id] = [];
        }
        threads[msg.parent_message_id]!.push(msg);
      }
    });
    setThreadedMessages(threads);
  }, [conversationId, messages]);

  const getThread = useCallback((rootMessageId: string) => {
    return threadedMessages[rootMessageId] || [];
  }, [threadedMessages]);

  const getThreadDepth = useCallback((messageId: string): number => {
    let depth = 0;
    let currentMessage = messages[conversationId]?.find(msg => msg.id === messageId);
    
    if (!currentMessage) {
      return depth;
    }
    
    while (currentMessage && currentMessage.parent_message_id) {
      depth++;
      const parentMessage = messages[conversationId]?.find(msg => msg.id === currentMessage?.parent_message_id);
      if (parentMessage) {
        currentMessage = parentMessage;
      } else {
        break;
      }
    }

    return depth;
  }, [conversationId, messages]);

  const getThreadPath = useCallback((messageId: string): string[] => {
    const path: string[] = [];
    let currentMessage = messages[conversationId]?.find(msg => msg.id === messageId);
    
    while (currentMessage) {
      path.unshift(currentMessage.id);
      if (currentMessage && currentMessage.parent_message_id) {
        const parentMessage = messages[conversationId]?.find(msg => msg.id === currentMessage?.parent_message_id);
        if (parentMessage) {
          currentMessage = parentMessage;
        } else {
          break;
        }
      } else {
        break;
      }
    }
    
    return path;
  }, [conversationId, messages]);

  return {
    rootMessages,
    threadedMessages,
    getThread,
    getThreadDepth,
    getThreadPath,
  };
};

// Hook for message search
export const useMessageSearch = (conversationId: string) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Message[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchFilters, setSearchFilters] = useState<MessageFilters>({});

  const debouncedSearchQuery = useDebounce(searchQuery, 300);

  useEffect(() => {
    if (!debouncedSearchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    const performSearch = async () => {
      setIsSearching(true);
      
      try {
        const params = new URLSearchParams({
          q: debouncedSearchQuery,
          conversation_id: conversationId,
          ...Object.fromEntries(
            Object.entries(searchFilters).filter(([, value]) => value !== undefined)
          ),
        });

        const response = await fetch(`/api/chat/messages/search?${params}`);
        
        if (!response.ok) {
          throw new Error('Failed to search messages');
        }

        const data = await response.json();
        setSearchResults(data.messages);
      } catch (error) {
        console.error('Search failed:', error);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    };

    performSearch();
  }, [debouncedSearchQuery, conversationId, searchFilters]);

  const updateSearchFilters = useCallback((filters: MessageFilters) => {
    setSearchFilters({ ...searchFilters, ...filters });
  }, [searchFilters]);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setSearchResults([]);
    setSearchFilters({});
  }, []);

  return {
    searchQuery,
    setSearchQuery,
    searchResults,
    isSearching,
    searchFilters,
    updateSearchFilters,
    clearSearch,
  };
};

// Hook for message reactions
export const useMessageReactions = () => {
  const { updateMessage } = useConversationStore();
  const { showToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const addReaction = useCallback(async (
    messageId: string,
    reaction: string
  ) => {
    setIsLoading(true);
    
    try {
      const response = await fetch(`/api/chat/messages/${messageId}/reactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reaction }),
      });

      if (!response.ok) {
        throw new Error('Failed to add reaction');
      }

      const updatedMessage = await response.json();
      await updateMessage(messageId, updatedMessage);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to add reaction';
      showToast(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  }, [updateMessage, showToast]);

  const removeReaction = useCallback(async (
    messageId: string,
    reaction: string
  ) => {
    setIsLoading(true);
    
    try {
      const response = await fetch(`/api/chat/messages/${messageId}/reactions/${reaction}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to remove reaction');
      }

      const updatedMessage = await response.json();
      await updateMessage(messageId, updatedMessage);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to remove reaction';
      showToast(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  }, [updateMessage, showToast]);

  return {
    addReaction,
    removeReaction,
    isLoading,
  };
};

// Hook for message importance
export const useMessageImportance = () => {
  const { updateMessage } = useConversationStore();
  const { showToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const markImportant = useCallback(async (
    messageId: string,
    isImportant: boolean,
    note?: string
  ) => {
    setIsLoading(true);
    
    try {
      const response = await fetch(`/api/chat/messages/${messageId}/importance`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_important: isImportant, important_note: note }),
      });

      if (!response.ok) {
        throw new Error('Failed to update message importance');
      }

      const updatedMessage = await response.json();
      await updateMessage(messageId, updatedMessage);
      
      showToast(
        `Message ${isImportant ? 'marked as' : 'unmarked as'} important`,
        'success'
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update message importance';
      showToast(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  }, [updateMessage, showToast]);

  return {
    markImportant,
    isLoading,
  };
};

// Hook for message forwarding
export const useMessageForwarding = () => {
  const { showToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const forwardMessage = useCallback(async (
    messageId: string,
    targetConversationId: string,
    addContext = true
  ) => {
    setIsLoading(true);
    
    try {
      const response = await fetch(`/api/chat/messages/${messageId}/forward`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_conversation_id: targetConversationId,
          add_context: addContext,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to forward message');
      }

      const forwardedMessage = await response.json();
      showToast('Message forwarded successfully', 'success');
      
      return forwardedMessage;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to forward message';
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  return {
    forwardMessage,
    isLoading,
  };
};

// Hook for message attachments
export const useMessageAttachments = (messageId: string) => {
  const [attachments, setAttachments] = useState<MessageAttachment[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadAttachments = async () => {
      setIsLoading(true);
      
      try {
        const response = await fetch(`/api/chat/messages/${messageId}/attachments`);
        
        if (!response.ok) {
          throw new Error('Failed to load attachments');
        }

        const data = await response.json();
        setAttachments(data.attachments);
      } catch (error) {
        console.error('Failed to load attachments:', error);
        setAttachments([]);
      } finally {
        setIsLoading(false);
      }
    };

    if (messageId) {
      loadAttachments();
    }
  }, [messageId]);

  const downloadAttachment = useCallback(async (attachmentId: string) => {
    try {
      const response = await fetch(`/api/chat/attachments/${attachmentId}/download`);
      
      if (!response.ok) {
        throw new Error('Failed to download attachment');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = attachments.find(att => att.id === attachmentId)?.filename || 'download';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to download attachment:', error);
    }
  }, [attachments]);

  return {
    attachments,
    isLoading,
    downloadAttachment,
  };
};

// Hook for message filtering
export const useMessageFilters = (conversationId: string) => {
  const {
    messageFilters,
    setMessageFilters,
    messages,
  } = useConversationStore();

  const debouncedFilters = useDebounce(messageFilters, 300);

  useEffect(() => {
    // Re-filter messages when filters change
    // This would typically trigger a reload from the server
  }, [debouncedFilters, conversationId]);

  const updateFilters = useCallback((filters: MessageFilters) => {
    setMessageFilters({ ...messageFilters, ...filters });
  }, [messageFilters, setMessageFilters]);

  const resetFilters = useCallback(() => {
    setMessageFilters({});
  }, [setMessageFilters]);

  const getFilteredMessages = useCallback(() => {
    const conversationMessages = messages[conversationId] || [];
    
    return conversationMessages.filter(msg => {
      if (messageFilters.role && msg.role !== messageFilters.role) {
        return false;
      }
      
      if (messageFilters.provider_id && msg.provider_id !== messageFilters.provider_id) {
        return false;
      }
      
      if (messageFilters.date_from && new Date(msg.created_at) < new Date(messageFilters.date_from)) {
        return false;
      }
      
      if (messageFilters.date_to && new Date(msg.created_at) > new Date(messageFilters.date_to)) {
        return false;
      }
      
      if (messageFilters.has_attachments !== undefined) {
        const hasAttachments = msg.attachments !== undefined && msg.attachments.length > 0;
        if (hasAttachments !== messageFilters.has_attachments) {
          return false;
        }
      }
      
      if (messageFilters.is_streaming !== undefined && msg.is_streaming !== messageFilters.is_streaming) {
        return false;
      }
      
      return true;
    });
  }, [conversationId, messages, messageFilters]);

  return {
    filters: messageFilters,
    updateFilters,
    resetFilters,
    getFilteredMessages,
  };
};

// Hook for message analytics
export const useMessageAnalytics = (conversationId?: string, days = 30) => {
  const [analytics, setAnalytics] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadAnalytics = async () => {
      setIsLoading(true);
      
      try {
        const params = new URLSearchParams({
          days: days.toString(),
        });
        
        if (conversationId) {
          params.append('conversation_id', conversationId);
        }

        const response = await fetch(`/api/chat/messages/analytics?${params}`);
        
        if (!response.ok) {
          throw new Error('Failed to load message analytics');
        }

        const data = await response.json();
        setAnalytics(data);
      } catch (error) {
        console.error('Failed to load analytics:', error);
        setAnalytics(null);
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalytics();
  }, [conversationId, days]);

  return {
    analytics,
    isLoading,
    refresh: () => {
      setIsLoading(true);
      // Reload analytics
      setTimeout(() => setIsLoading(false), 100);
    },
  };
};

// Hook for message real-time updates
export const useMessageRealtime = (conversationId: string) => {
  const {
    handleRealtimeUpdate,
    updateTypingIndicator,
    isConnected,
  } = useConversationStore();

  const [typingUsers, setTypingUsers] = useState<string[]>([]);

  useEffect(() => {
    // WebSocket connection for real-time message updates
    // This is a placeholder for actual WebSocket implementation
    
    const mockWebSocket = {
      onmessage: (event: MessageEvent) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'message_created' && data.payload.conversation_id === conversationId) {
          handleRealtimeUpdate('message_created', data.payload);
        } else if (data.type === 'message_updated' && data.payload.conversation_id === conversationId) {
          handleRealtimeUpdate('message_updated', data.payload);
        } else if (data.type === 'typing_indicator' && data.payload.conversation_id === conversationId) {
          setTypingUsers(prev => {
            if (data.payload.is_typing) {
              return prev.includes(data.payload.user_id) ? prev : [...prev, data.payload.user_id];
            } else {
              return prev.filter(id => id !== data.payload.user_id);
            }
          });
        }
      },
    };
    void mockWebSocket;

    return () => {
      // Cleanup WebSocket connection
    };
  }, [conversationId, handleRealtimeUpdate]);

  const sendTypingIndicator = useCallback((isTyping: boolean) => {
    // Send typing indicator via WebSocket
    updateTypingIndicator(conversationId, isTyping);
  }, [conversationId, updateTypingIndicator]);

  return {
    isConnected,
    typingUsers,
    sendTypingIndicator,
  };
};

// Hook for message export
export const useMessageExport = () => {
  const { showToast } = useToast();
  const [isExporting, setIsExporting] = useState(false);

  const exportMessages = useCallback(async (
    conversationId?: string,
    messageIds?: string[],
    format: 'json' | 'csv' | 'pdf' = 'json',
    options?: {
      includeAttachments?: boolean;
      dateFrom?: string;
      dateTo?: string;
    }
  ) => {
    setIsExporting(true);
    
    try {
      const params = new URLSearchParams();
      if (conversationId) {
        params.append('conversation_id', conversationId);
      }
      if (messageIds) {
        params.append('message_ids', messageIds.join(','));
      }
      params.append('format', format);
      if (options?.includeAttachments !== undefined) {
        params.append('include_attachments', options.includeAttachments.toString());
      }
      if (options?.dateFrom) {
        params.append('date_from', options.dateFrom);
      }
      if (options?.dateTo) {
        params.append('date_to', options.dateTo);
      }

      const response = await fetch(`/api/chat/messages/export?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to export messages');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `messages_export_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showToast('Messages exported successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to export messages';
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsExporting(false);
    }
  }, [showToast]);

  return {
    exportMessages,
    isExporting,
  };
};
