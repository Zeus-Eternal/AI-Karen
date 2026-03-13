/**
 * Conversation Hooks - Custom hooks for conversation management
 * Provides convenient hooks for conversation CRUD operations, pagination, and state management
 */

import { useCallback, useEffect, useState } from 'react';
import { useConversationStore, Conversation, ConversationFilters } from '../stores/conversationStore';
import { useDebounce } from './useDebounce';
import { useToast } from './useToast';

// Hook for conversation CRUD operations
export const useConversationCRUD = () => {
  const {
    createConversation,
    updateConversation,
    deleteConversation,
    archiveConversation,
    unarchiveConversation,
    pinConversation,
    unpinConversation,
    setError,
    clearError,
  } = useConversationStore();
  
  const { showToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const handleCreateConversation = useCallback(async (title?: string, providerId?: string) => {
    setIsLoading(true);
    clearError();
    
    try {
      const conversation = await createConversation(title, providerId);
      showToast('Conversation created successfully', 'success');
      return conversation;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create conversation';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [createConversation, setError, clearError, showToast]);

  const handleUpdateConversation = useCallback(async (id: string, updates: Partial<Conversation>) => {
    setIsLoading(true);
    clearError();
    
    try {
      await updateConversation(id, updates);
      showToast('Conversation updated successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update conversation';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [updateConversation, setError, clearError, showToast]);

  const handleDeleteConversation = useCallback(async (id: string, permanent = false) => {
    setIsLoading(true);
    clearError();
    
    try {
      await deleteConversation(id, permanent);
      showToast(`Conversation ${permanent ? 'deleted permanently' : 'archived'} successfully`, 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete conversation';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [deleteConversation, setError, clearError, showToast]);

  const handleArchiveConversation = useCallback(async (id: string) => {
    setIsLoading(true);
    clearError();
    
    try {
      await archiveConversation(id);
      showToast('Conversation archived successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to archive conversation';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [archiveConversation, setError, clearError, showToast]);

  const handleUnarchiveConversation = useCallback(async (id: string) => {
    setIsLoading(true);
    clearError();
    
    try {
      await unarchiveConversation(id);
      showToast('Conversation unarchived successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to unarchive conversation';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [unarchiveConversation, setError, clearError, showToast]);

  const handlePinConversation = useCallback(async (id: string) => {
    setIsLoading(true);
    clearError();
    
    try {
      await pinConversation(id);
      showToast('Conversation pinned successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to pin conversation';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [pinConversation, setError, clearError, showToast]);

  const handleUnpinConversation = useCallback(async (id: string) => {
    setIsLoading(true);
    clearError();
    
    try {
      await unpinConversation(id);
      showToast('Conversation unpinned successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to unpin conversation';
      setError(errorMessage);
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [unpinConversation, setError, clearError, showToast]);

  return {
    createConversation: handleCreateConversation,
    updateConversation: handleUpdateConversation,
    deleteConversation: handleDeleteConversation,
    archiveConversation: handleArchiveConversation,
    unarchiveConversation: handleUnarchiveConversation,
    pinConversation: handlePinConversation,
    unpinConversation: handleUnpinConversation,
    isLoading,
  };
};

// Hook for conversation pagination
export const useConversationPagination = () => {
  const {
    conversations,
    pagination,
    loadConversations,
    isLoading,
    error,
  } = useConversationStore();

  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadMore = useCallback(async () => {
    if (pagination.hasMore && !isLoading && !isRefreshing) {
      await loadConversations();
    }
  }, [pagination.hasMore, isLoading, isRefreshing, loadConversations]);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await loadConversations(true);
    } finally {
      setIsRefreshing(false);
    }
  }, [loadConversations]);

  return {
    conversations,
    pagination,
    loadMore,
    refresh,
    isLoading: isLoading || isRefreshing,
    error,
    hasMore: pagination.hasMore,
    totalCount: pagination.total,
  };
};

// Hook for conversation filtering
export const useConversationFilters = () => {
  const {
    filters,
    setFilters,
    clearFilters,
    loadConversations,
    conversations,
  } = useConversationStore();

  const debouncedFilters = useDebounce(filters, 300);

  useEffect(() => {
    loadConversations(true);
  }, [debouncedFilters, loadConversations]);

  const updateFilters = useCallback((newFilters: ConversationFilters) => {
    setFilters({ ...filters, ...newFilters });
  }, [filters, setFilters]);

  const resetFilters = useCallback(() => {
    clearFilters();
  }, [clearFilters]);

  const getFilteredConversations = useCallback(() => {
    return conversations.filter(conv => {
      if (filters.is_archived !== undefined && conv.is_archived !== filters.is_archived) {
        return false;
      }
      
      if (filters.provider_id && conv.provider_id !== filters.provider_id) {
        return false;
      }
      
      if (filters.tags && filters.tags.length > 0) {
        const convTags = conv.tags || [];
        const hasMatchingTag = filters.tags.some(tag => convTags.includes(tag));
        if (!hasMatchingTag) {
          return false;
        }
      }
      
      if (filters.date_from && new Date(conv.created_at) < new Date(filters.date_from)) {
        return false;
      }
      
      if (filters.date_to && new Date(conv.created_at) > new Date(filters.date_to)) {
        return false;
      }
      
      if (filters.is_pinned !== undefined) {
        const isPinned = conv.is_pinned || false;
        if (isPinned !== filters.is_pinned) {
          return false;
        }
      }
      
      return true;
    });
  }, [conversations, filters]);

  return {
    filters,
    updateFilters,
    resetFilters,
    getFilteredConversations,
  };
};

// Hook for conversation selection
export const useConversationSelection = () => {
  const {
    selectedConversationIds,
    selectConversation,
    selectAllConversations,
    clearSelection,
    conversations,
  } = useConversationStore();

  const isSelected = useCallback((id: string) => {
    return selectedConversationIds.includes(id);
  }, [selectedConversationIds]);

  const toggleSelection = useCallback((id: string, multi = false) => {
    selectConversation(id, multi);
  }, [selectConversation]);

  const selectAll = useCallback(() => {
    selectAllConversations();
  }, [selectAllConversations]);

  const clear = useCallback(() => {
    clearSelection();
  }, [clearSelection]);

  const getSelectedCount = useCallback(() => {
    return selectedConversationIds.length;
  }, [selectedConversationIds]);

  const getSelectedConversations = useCallback(() => {
    return conversations.filter(conv => selectedConversationIds.includes(conv.id));
  }, [conversations, selectedConversationIds]);

  const isAllSelected = useCallback(() => {
    return conversations.length > 0 && selectedConversationIds.length === conversations.length;
  }, [conversations, selectedConversationIds]);

  const isPartiallySelected = useCallback(() => {
    return selectedConversationIds.length > 0 && selectedConversationIds.length < conversations.length;
  }, [selectedConversationIds, conversations]);

  return {
    selectedIds: selectedConversationIds,
    isSelected,
    toggleSelection,
    selectAll,
    clear,
    getSelectedCount,
    getSelectedConversations,
    isAllSelected,
    isPartiallySelected,
  };
};

// Hook for conversation sorting
export const useConversationSorting = () => {
  const [sortBy, setSortBy] = useState<'updated_at' | 'created_at' | 'title' | 'message_count'>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const sortConversations = useCallback((conversations: Conversation[]) => {
    return [...conversations].sort((a, b) => {
      let aValue: Date | number | string;
      let bValue: Date | number | string;

      switch (sortBy) {
        case 'updated_at':
        case 'created_at':
          aValue = new Date(a[sortBy]).getTime();
          bValue = new Date(b[sortBy]).getTime();
          break;
        case 'title':
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case 'message_count':
          aValue = a.message_count;
          bValue = b.message_count;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) {
        return sortOrder === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortOrder === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [sortBy, sortOrder]);

  const updateSort = useCallback((newSortBy: typeof sortBy, newSortOrder: typeof sortOrder) => {
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
  }, []);

  const toggleSortOrder = useCallback(() => {
    setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
  }, []);

  return {
    sortBy,
    sortOrder,
    sortConversations,
    updateSort,
    toggleSortOrder,
  };
};

// Hook for conversation bulk operations
export const useConversationBulkOperations = () => {
  const {
    selectedConversationIds,
    clearSelection,
    updateConversation,
    deleteConversation,
    archiveConversation,
    unarchiveConversation,
    pinConversation,
    unpinConversation,
    setError,
    clearError,
  } = useConversationStore();

  const { showToast } = useToast();
  const [isBulkLoading, setIsBulkLoading] = useState(false);

  const bulkArchive = useCallback(async () => {
    setIsBulkLoading(true);
    clearError();
    
    try {
      const promises = selectedConversationIds.map(id => archiveConversation(id));
      await Promise.all(promises);
      showToast(`${selectedConversationIds.length} conversations archived successfully`, 'success');
      clearSelection();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to archive conversations';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setIsBulkLoading(false);
    }
  }, [selectedConversationIds, archiveConversation, setError, clearError, showToast, clearSelection]);

  const bulkUnarchive = useCallback(async () => {
    setIsBulkLoading(true);
    clearError();
    
    try {
      const promises = selectedConversationIds.map(id => unarchiveConversation(id));
      await Promise.all(promises);
      showToast(`${selectedConversationIds.length} conversations unarchived successfully`, 'success');
      clearSelection();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to unarchive conversations';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setIsBulkLoading(false);
    }
  }, [selectedConversationIds, unarchiveConversation, setError, clearError, showToast, clearSelection]);

  const bulkDelete = useCallback(async (permanent = false) => {
    const confirmMessage = permanent 
      ? `Are you sure you want to permanently delete ${selectedConversationIds.length} conversations? This action cannot be undone.`
      : `Are you sure you want to archive ${selectedConversationIds.length} conversations?`;
    
    if (!window.confirm(confirmMessage)) {
      return;
    }

    setIsBulkLoading(true);
    clearError();
    
    try {
      const promises = selectedConversationIds.map(id => deleteConversation(id, permanent));
      await Promise.all(promises);
      showToast(`${selectedConversationIds.length} conversations ${permanent ? 'deleted permanently' : 'archived'} successfully`, 'success');
      clearSelection();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete conversations';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setIsBulkLoading(false);
    }
  }, [selectedConversationIds, deleteConversation, setError, clearError, showToast, clearSelection]);

  const bulkPin = useCallback(async () => {
    setIsBulkLoading(true);
    clearError();
    
    try {
      const promises = selectedConversationIds.map(id => pinConversation(id));
      await Promise.all(promises);
      showToast(`${selectedConversationIds.length} conversations pinned successfully`, 'success');
      clearSelection();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to pin conversations';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setIsBulkLoading(false);
    }
  }, [selectedConversationIds, pinConversation, setError, clearError, showToast, clearSelection]);

  const bulkUnpin = useCallback(async () => {
    setIsBulkLoading(true);
    clearError();
    
    try {
      const promises = selectedConversationIds.map(id => unpinConversation(id));
      await Promise.all(promises);
      showToast(`${selectedConversationIds.length} conversations unpinned successfully`, 'success');
      clearSelection();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to unpin conversations';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setIsBulkLoading(false);
    }
  }, [selectedConversationIds, unpinConversation, setError, clearError, showToast, clearSelection]);

  const bulkUpdateTags = useCallback(async (tags: string[]) => {
    setIsBulkLoading(true);
    clearError();
    
    try {
      const promises = selectedConversationIds.map(id => 
        updateConversation(id, { metadata: { tags } })
      );
      await Promise.all(promises);
      showToast(`Tags updated for ${selectedConversationIds.length} conversations successfully`, 'success');
      clearSelection();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update tags';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setIsBulkLoading(false);
    }
  }, [selectedConversationIds, updateConversation, setError, clearError, showToast, clearSelection]);

  return {
    bulkArchive,
    bulkUnarchive,
    bulkDelete,
    bulkPin,
    bulkUnpin,
    bulkUpdateTags,
    isBulkLoading,
    hasSelection: selectedConversationIds.length > 0,
    selectedCount: selectedConversationIds.length,
  };
};

// Hook for conversation export/import
export const useConversationExportImport = () => {
  const { showToast } = useToast();
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  const exportConversations = useCallback(async (
    conversationIds?: string[],
    format: 'json' | 'csv' | 'pdf' = 'json',
    options?: {
      includeMessages?: boolean;
      dateFrom?: string;
      dateTo?: string;
    }
  ) => {
    setIsExporting(true);
    
    try {
      const params = new URLSearchParams();
      if (conversationIds) {
        params.append('conversation_ids', conversationIds.join(','));
      }
      params.append('format', format);
      if (options?.includeMessages !== undefined) {
        params.append('include_messages', options.includeMessages.toString());
      }
      if (options?.dateFrom) {
        params.append('date_from', options.dateFrom);
      }
      if (options?.dateTo) {
        params.append('date_to', options.dateTo);
      }

      const response = await fetch(`/api/chat/conversations/export?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to export conversations');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversations_export_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showToast('Conversations exported successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to export conversations';
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsExporting(false);
    }
  }, [showToast]);

  const importConversations = useCallback(async (file: File, mergeStrategy: 'skip_duplicates' | 'overwrite' = 'skip_duplicates') => {
    setIsImporting(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('merge_strategy', mergeStrategy);

      const response = await fetch('/api/chat/conversations/import', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to import conversations');
      }

      const result = await response.json();
      
      showToast(
        `Imported ${result.imported_count} conversations successfully${result.skipped_count > 0 ? ` (${result.skipped_count} skipped)` : ''}`,
        'success'
      );

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to import conversations';
      showToast(errorMessage, 'error');
      throw error;
    } finally {
      setIsImporting(false);
    }
  }, [showToast]);

  return {
    exportConversations,
    importConversations,
    isExporting,
    isImporting,
  };
};

// Hook for conversation statistics
export const useConversationStats = (days: number = 30) => {
  const { stats, loadStats } = useConversationStore();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadStatsData = async () => {
      setIsLoading(true);
      try {
        await loadStats(days);
      } finally {
        setIsLoading(false);
      }
    };

    loadStatsData();
  }, [days, loadStats]);

  return {
    stats,
    isLoading,
    refresh: () => loadStats(days),
  };
};

// Hook for conversation real-time updates
export const useConversationRealtime = () => {
  const {
    handleRealtimeUpdate,
    updateTypingIndicator,
    isConnected,
  } = useConversationStore();

  useEffect(() => {
    // WebSocket connection would be handled here
    // This is a placeholder for the actual WebSocket implementation
    
    // Simulate connection
    return () => {
      // Cleanup WebSocket connection
    };
  }, [handleRealtimeUpdate]);

  const sendTypingIndicator = useCallback((conversationId: string, isTyping: boolean) => {
    // Send typing indicator via WebSocket
    updateTypingIndicator(conversationId, isTyping);
  }, [updateTypingIndicator]);

  return {
    isConnected,
    sendTypingIndicator,
  };
};

// Hook for conversation preferences
export const useConversationPreferences = () => {
  const { preferences, updatePreferences } = useConversationStore();

  const updatePreference = useCallback((key: keyof typeof preferences, value: Record<string, unknown> | string | number | boolean | string[]) => {
    updatePreferences({ [key]: value });
  }, [updatePreferences]);

  const resetPreferences = useCallback(() => {
    updatePreferences({
      autoSave: true,
      syncInterval: 30000,
      pageSize: 50,
      enableNotifications: true,
      enableSounds: true,
      theme: 'auto',
    });
  }, [updatePreferences]);

  return {
    preferences,
    updatePreference,
    resetPreferences,
  };
};
