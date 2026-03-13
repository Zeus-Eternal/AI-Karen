/**
 * Conversation Search Hooks - Custom hooks for conversation search functionality
 * Provides advanced search capabilities with filters, sorting, and history
 */

import { useCallback, useEffect, useState } from 'react';
import { useConversationStore, Conversation, ConversationFilters } from '../stores/conversationStore';
import { useDebounce } from './useDebounce';
import { useToast } from './useToast';

// Hook for basic conversation search
export const useConversationSearch = () => {
  const {
    searchConversations,
    clearSearch,
    filters,
  } = useConversationStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const debouncedSearchQuery = useDebounce(searchQuery, 300);

  const performSearch = useCallback(async (query: string) => {
    setIsSearching(true);
    
    try {
      await searchConversations(query, filters);
      
      // Update search history
      setSearchHistory(prev => {
        const newHistory = [query, ...prev.filter(q => q !== query)].slice(0, 10);
        return newHistory;
      });
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  }, [searchConversations, filters]);

  useEffect(() => {
    if (debouncedSearchQuery.trim()) {
      performSearch(debouncedSearchQuery);
    } else {
      clearSearch();
    }
  }, [debouncedSearchQuery, clearSearch, performSearch]);

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  const clearCurrentSearch = useCallback(() => {
    setSearchQuery('');
    clearSearch();
  }, [clearSearch]);

  const searchFromHistory = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  const clearSearchHistory = useCallback(() => {
    setSearchHistory([]);
  }, []);

  return {
    searchQuery,
    setSearchQuery: handleSearch,
    searchHistory,
    clearSearchHistory,
    searchFromHistory,
    clearSearch: clearCurrentSearch,
    isSearching,
  };
};

// Hook for advanced conversation search
export const useAdvancedConversationSearch = () => {
  const { showToast } = useToast();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [advancedFilters, setAdvancedFilters] = useState<ConversationFilters>({});
  const [searchResults, setSearchResults] = useState<Conversation[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchOptions, setSearchOptions] = useState({
    includeArchived: false,
    includeMessages: false,
    fuzzySearch: true,
    caseSensitive: false,
  });

  const debouncedSearchQuery = useDebounce(searchQuery, 300);

  const performAdvancedSearch = useCallback(async () => {
    if (!searchQuery.trim() && Object.keys(advancedFilters).length === 0) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    
    try {
      const params = new URLSearchParams();
      if (searchQuery.trim()) {
        params.append('q', searchQuery);
      }
      
      Object.entries(advancedFilters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            params.append(key, value.join(','));
          } else {
            params.append(key, value.toString());
          }
        }
      });

      Object.entries(searchOptions).forEach(([key, value]) => {
        params.append(key, value.toString());
      });

      const response = await fetch(`/api/chat/conversations/search/advanced?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to perform advanced search');
      }

      const data = await response.json();
      setSearchResults(data.conversations);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Search failed';
      showToast(errorMessage, 'error');
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery, advancedFilters, searchOptions, showToast]);

  useEffect(() => {
    if (debouncedSearchQuery.trim() || Object.keys(advancedFilters).length > 0) {
      performAdvancedSearch();
    } else {
      setSearchResults([]);
    }
  }, [debouncedSearchQuery, advancedFilters, performAdvancedSearch]);

  const updateFilters = useCallback((filters: ConversationFilters) => {
    setAdvancedFilters(prev => ({ ...prev, ...filters }));
  }, []);

  const updateSearchOptions = useCallback((options: Partial<typeof searchOptions>) => {
    setSearchOptions(prev => ({ ...prev, ...options }));
  }, []);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setAdvancedFilters({});
    setSearchResults([]);
  }, []);

  return {
    searchQuery,
    setSearchQuery,
    searchResults,
    isSearching,
    advancedFilters,
    updateFilters,
    searchOptions,
    updateSearchOptions,
    clearSearch,
    performSearch: performAdvancedSearch,
  };
};

// Hook for conversation search suggestions
export const useConversationSearchSuggestions = () => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 200);

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    const fetchSuggestions = async () => {
      setIsLoading(true);
      
      try {
        const response = await fetch(`/api/chat/conversations/suggestions?q=${encodeURIComponent(debouncedQuery)}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch suggestions');
        }

        const data = await response.json();
        setSuggestions(data.suggestions || []);
      } catch (error) {
        console.error('Failed to fetch suggestions:', error);
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSuggestions();
  }, [debouncedQuery]);

  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
    setQuery('');
  }, []);

  return {
    suggestions,
    isLoading,
    query,
    setQuery,
    clearSuggestions,
  };
};

// Hook for saved searches
export const useSavedSearches = () => {
  const [savedSearches, setSavedSearches] = useState<Array<{
    id: string;
    name: string;
    query: string;
    filters: ConversationFilters;
    createdAt: string;
  }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { showToast } = useToast();

  const loadSavedSearches = useCallback(async () => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/chat/conversations/saved-searches');
      
      if (!response.ok) {
        throw new Error('Failed to load saved searches');
      }

      const data = await response.json();
      setSavedSearches(data.searches || []);
    } catch (error) {
      console.error('Failed to load saved searches:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSavedSearches();
  }, [loadSavedSearches]);

  const saveSearch = useCallback(async (
    name: string,
    query: string,
    filters: ConversationFilters
  ) => {
    try {
      const response = await fetch('/api/chat/conversations/saved-searches', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          query,
          filters,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save search');
      }

      const data = await response.json();
      setSavedSearches(prev => [...prev, data.search]);
      showToast('Search saved successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to save search';
      showToast(errorMessage, 'error');
    }
  }, [showToast]);

  const deleteSavedSearch = useCallback(async (searchId: string) => {
    try {
      const response = await fetch(`/api/chat/conversations/saved-searches/${searchId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete saved search');
      }

      setSavedSearches(prev => prev.filter(search => search.id !== searchId));
      showToast('Saved search deleted', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete saved search';
      showToast(errorMessage, 'error');
    }
  }, [showToast]);

  const executeSavedSearch = useCallback(async (searchId: string) => {
    const search = savedSearches.find(s => s.id === searchId);
    
    if (search) {
      // This would typically trigger search with saved parameters
      // Implementation depends on how the search is integrated
      console.log('Executing saved search:', search);
    }
  }, [savedSearches]);

  return {
    savedSearches,
    isLoading,
    saveSearch,
    deleteSavedSearch,
    executeSavedSearch,
    refresh: loadSavedSearches,
  };
};

// Hook for search analytics
export const useSearchAnalytics = () => {
  const [analytics, setAnalytics] = useState<{
    popular_searches?: Array<{ query: string; count: number }>;
    search_trends?: Array<{ date: string; count: number }>;
    total_searches?: number;
    average_result_count?: number;
    search_success_rate?: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { showToast } = useToast();

  const loadSearchAnalytics = useCallback(async (days = 30) => {
    setIsLoading(true);
    
    try {
      const response = await fetch(`/api/chat/conversations/search/analytics?days=${days}`);
      
      if (!response.ok) {
        throw new Error('Failed to load search analytics');
      }

      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load analytics';
      showToast(errorMessage, 'error');
      setAnalytics(null);
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  const getPopularSearches = useCallback(() => {
    return analytics?.popular_searches || [];
  }, [analytics]);

  const getSearchTrends = useCallback(() => {
    return analytics?.search_trends || [];
  }, [analytics]);

  const getSearchStats = useCallback(() => {
    return {
      totalSearches: analytics?.total_searches || 0,
      averageResultCount: analytics?.average_result_count || 0,
      searchSuccessRate: analytics?.search_success_rate || 0,
    };
  }, [analytics]);

  return {
    analytics,
    isLoading,
    loadSearchAnalytics,
    getPopularSearches,
    getSearchTrends,
    getSearchStats,
  };
};

// Hook for search filters
export const useSearchFilters = () => {
  const [activeFilters, setActiveFilters] = useState<ConversationFilters>({});
  const [availableFilters, setAvailableFilters] = useState<Array<{
    id: string;
    name: string;
    type: string;
    options?: Array<{ value: string; label: string }>;
  }>>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadAvailableFilters = useCallback(async () => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/chat/conversations/search/filters');
      
      if (!response.ok) {
        throw new Error('Failed to load available filters');
      }

      const data = await response.json();
      setAvailableFilters(data.filters || []);
    } catch (error) {
      console.error('Failed to load available filters:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAvailableFilters();
  }, [loadAvailableFilters]);

  const updateFilter = useCallback((key: keyof ConversationFilters, value: ConversationFilters[keyof ConversationFilters]) => {
    setActiveFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const removeFilter = useCallback((key: keyof ConversationFilters) => {
    setActiveFilters(prev => {
      const newFilters = { ...prev };
      delete newFilters[key];
      return newFilters;
    });
  }, []);

  const clearAllFilters = useCallback(() => {
    setActiveFilters({});
  }, []);

  const getFilterCount = useCallback(() => {
    return Object.keys(activeFilters).length;
  }, [activeFilters]);

  const hasActiveFilters = useCallback(() => {
    return Object.keys(activeFilters).length > 0;
  }, [activeFilters]);

  return {
    activeFilters,
    availableFilters,
    isLoading,
    updateFilter,
    removeFilter,
    clearAllFilters,
    getFilterCount,
    hasActiveFilters,
  };
};

// Hook for search sorting
export const useSearchSorting = () => {
  const [sortBy, setSortBy] = useState<'relevance' | 'date' | 'title' | 'message_count'>('relevance');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const updateSort = useCallback((newSortBy: typeof sortBy, newSortOrder: typeof sortOrder) => {
    setSortBy(newSortBy);
    setSortOrder(newSortOrder);
  }, []);

  const toggleSortOrder = useCallback(() => {
    setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
  }, []);

  const getSortLabel = useCallback(() => {
    const sortLabels = {
      relevance: 'Relevance',
      date: 'Date',
      title: 'Title',
      message_count: 'Message Count',
    };
    
    return `${sortLabels[sortBy]} (${sortOrder === 'asc' ? 'A-Z' : 'Z-A'})`;
  }, [sortBy, sortOrder]);

  return {
    sortBy,
    sortOrder,
    updateSort,
    toggleSortOrder,
    getSortLabel,
  };
};

// Hook for search pagination
export const useSearchPagination = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const nextPage = useCallback(() => {
    if (hasMore) {
      setPage(prev => prev + 1);
    }
  }, [hasMore]);

  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(prev => prev - 1);
    }
  }, [page]);

  const goToPage = useCallback((targetPage: number) => {
    if (targetPage >= 1) {
      setPage(targetPage);
    }
  }, []);

  const resetPagination = useCallback(() => {
    setPage(1);
    setTotal(0);
    setHasMore(false);
  }, []);

  const updatePagination = useCallback((newPage: number, newTotal: number, newHasMore: boolean) => {
    setPage(newPage);
    setTotal(newTotal);
    setHasMore(newHasMore);
  }, []);

  const totalPages = Math.ceil(total / perPage);

  return {
    page,
    perPage,
    total,
    hasMore,
    totalPages,
    nextPage,
    prevPage,
    goToPage,
    resetPagination,
    updatePagination,
    setPerPage,
  };
};

// Hook for real-time search updates
export const useSearchRealtime = () => {
  const [searchUpdates, setSearchUpdates] = useState<Record<string, unknown>[]>([]);
  const [isConnected] = useState(false);

  useEffect(() => {
    // WebSocket connection for real-time search updates
    // This is a placeholder for actual WebSocket implementation
    
    return () => {
      // Cleanup WebSocket connection
    };
  }, []);

  const addSearchUpdate = useCallback((update: Record<string, unknown>) => {
    setSearchUpdates(prev => [update, ...prev.slice(0, 9)]);
  }, []);

  const clearSearchUpdates = useCallback(() => {
    setSearchUpdates([]);
  }, []);

  return {
    searchUpdates,
    isConnected,
    addSearchUpdate,
    clearSearchUpdates,
  };
};
