/**
 * Memory Search Component
 * Provides semantic search capabilities with similarity scoring and advanced filtering
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Search, 
  Filter, 
  Clock, 
  Star, 
  Tag, 
  Calendar,
  ChevronDown,
  ChevronUp,
  Bookmark,
  History,
  X,
  SortAsc,
  SortDesc
} from 'lucide-react';
import { getMemoryService } from '@/services/memoryService';
import type { 
  MemoryEntry,
  MemorySearchOptions,
  MemorySearchResult,
  MemorySearchHistory,
  SavedSearch,
  MemorySearchProps,
  SearchFacets
} from '@/types/memory';

interface SearchFilters {
  tags: string[];
  contentTypes: string[];
  clusters: string[];
  confidenceRange: [number, number];
  dateRange: [Date | null, Date | null];
  sortBy: 'relevance' | 'date' | 'confidence' | 'access_count';
  sortOrder: 'asc' | 'desc';
}

interface SearchSuggestion {
  query: string;
  type: 'history' | 'popular' | 'related';
  count?: number;
}

export const MemorySearch: React.FC<MemorySearchProps> = ({
  userId,
  tenantId,
  initialQuery = '',
  onMemorySelect,
  onSearchComplete,
  height = 600
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [searchResult, setSearchResult] = useState<MemorySearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [searchHistory, setSearchHistory] = useState<MemorySearchHistory[]>([]);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<MemoryEntry | null>(null);

  const [filters, setFilters] = useState<SearchFilters>({
    tags: [],
    contentTypes: [],
    clusters: [],
    confidenceRange: [0, 1],
    dateRange: [null, null],
    sortBy: 'relevance',
    sortOrder: 'desc'
  });

  const searchInputRef = useRef<HTMLInputElement>(null);
  const memoryService = useMemo(() => getMemoryService(), []);

  // Load search history and saved searches on mount
  useEffect(() => {
    loadSearchHistory();
    loadSavedSearches();
  }, [userId]);

  // Generate search suggestions based on query
  useEffect(() => {
    if (query.length > 2) {
      generateSuggestions(query);
    } else {
      setSuggestions([]);
    }
  }, [query]);

  const loadSearchHistory = useCallback(async () => {
    try {
      // In a real implementation, this would fetch from backend
      const mockHistory: MemorySearchHistory[] = [
        {
          id: '1',
          query: 'javascript functions',
          timestamp: new Date(Date.now() - 3600000),
          resultCount: 25,
          filters: { topK: 10 },
          userId
        },
        {
          id: '2',
          query: 'react hooks',
          timestamp: new Date(Date.now() - 7200000),
          resultCount: 18,
          filters: { topK: 10 },
          userId
        }
      ];
      setSearchHistory(mockHistory);
    } catch (err) {
      console.error('Failed to load search history:', err);
    }
  }, [userId]);

  const loadSavedSearches = useCallback(async () => {
    try {
      // In a real implementation, this would fetch from backend
      const mockSaved: SavedSearch[] = [
        {
          id: '1',
          name: 'Technical Documentation',
          query: 'documentation OR tutorial OR guide',
          filters: { tags: ['technical'], topK: 20 },
          userId,
          createdAt: new Date(Date.now() - 86400000),
          lastUsed: new Date(Date.now() - 3600000),
          useCount: 5
        }
      ];
      setSavedSearches(mockSaved);
    } catch (err) {
      console.error('Failed to load saved searches:', err);
    }
  }, [userId]);

  const generateSuggestions = useCallback(async (searchQuery: string) => {
    try {
      // Generate suggestions based on search history and popular queries
      const historySuggestions = searchHistory
        .filter(h => h.query.toLowerCase().includes(searchQuery.toLowerCase()))
        .slice(0, 3)
        .map(h => ({
          query: h.query,
          type: 'history' as const,
          count: h.resultCount
        }));

      // Mock popular suggestions
      const popularSuggestions: SearchSuggestion[] = [
        { query: `${searchQuery} tutorial`, type: 'popular', count: 45 },
        { query: `${searchQuery} example`, type: 'popular', count: 32 },
        { query: `${searchQuery} best practices`, type: 'popular', count: 28 }
      ];

      setSuggestions([...historySuggestions, ...popularSuggestions.slice(0, 2)]);
    } catch (err) {
      console.error('Failed to generate suggestions:', err);
    }
  }, [searchHistory]);

  const performSearch = useCallback(async (searchQuery: string = query, searchFilters: SearchFilters = filters) => {
    if (!searchQuery.trim()) return;

    try {
      setLoading(true);
      setError(null);

      const searchOptions: MemorySearchOptions = {
        topK: 20,
        similarityThreshold: 0.5,
        tags: searchFilters.tags.length > 0 ? searchFilters.tags : undefined,
        timeRange: searchFilters.dateRange[0] && searchFilters.dateRange[1] 
          ? [searchFilters.dateRange[0], searchFilters.dateRange[1]]
          : undefined,
        sortBy: searchFilters.sortBy,
        sortOrder: searchFilters.sortOrder
      };

      const result = await memoryService.searchMemories(searchQuery, {
        userId,
        tenantId,
        tags: searchOptions.tags,
        dateRange: searchOptions.timeRange,
        minSimilarity: searchOptions.similarityThreshold,
        maxResults: searchOptions.topK
      });

      // Enhance result with mock facets and suggestions
      const enhancedResult: MemorySearchResult = {
        memories: result.memories,
        totalFound: result.totalFound,
        searchTime: result.searchTime,
        facets: generateFacets(result.memories),
        suggestions: generateQuerySuggestions(searchQuery),
        relatedQueries: generateRelatedQueries(searchQuery)
      };

      setSearchResult(enhancedResult);
      onSearchComplete?.(enhancedResult);

      // Add to search history
      addToSearchHistory(searchQuery, enhancedResult.totalFound, searchOptions);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Search failed';
      setError(errorMessage);
      console.error('Search error:', err);
    } finally {
      setLoading(false);
      setShowSuggestions(false);
    }
  }, [query, filters, userId, tenantId, memoryService, onSearchComplete]);

  const generateFacets = useCallback((memories: MemoryEntry[]): SearchFacets => {
    const types: Record<string, number> = {};
    const tags: Record<string, number> = {};
    const clusters: Record<string, number> = {};

    memories.forEach(memory => {
      // Count types
      const type = memory.type || 'unknown';
      types[type] = (types[type] || 0) + 1;

      // Count tags
      memory.tags.forEach(tag => {
        tags[tag] = (tags[tag] || 0) + 1;
      });

      // Count clusters
      const cluster = memory.metadata?.cluster || 'general';
      clusters[cluster] = (clusters[cluster] || 0) + 1;
    });

    return {
      types: Object.entries(types).map(([type, count]) => ({ type, count })),
      tags: Object.entries(tags).map(([tag, count]) => ({ tag, count })),
      clusters: Object.entries(clusters).map(([cluster, count]) => ({ cluster, count })),
      timeRanges: [
        { range: 'Last 24 hours', count: memories.filter(m => 
          Date.now() - m.timestamp < 86400000).length },
        { range: 'Last week', count: memories.filter(m => 
          Date.now() - m.timestamp < 604800000).length },
        { range: 'Last month', count: memories.filter(m => 
          Date.now() - m.timestamp < 2592000000).length }
      ],
      confidenceRanges: [
        { range: '0.8-1.0', count: memories.filter(m => (m.confidence || 0) >= 0.8).length },
        { range: '0.6-0.8', count: memories.filter(m => (m.confidence || 0) >= 0.6 && (m.confidence || 0) < 0.8).length },
        { range: '0.4-0.6', count: memories.filter(m => (m.confidence || 0) >= 0.4 && (m.confidence || 0) < 0.6).length },
        { range: '0.0-0.4', count: memories.filter(m => (m.confidence || 0) < 0.4).length }
      ]
    };
  }, []);

  const generateQuerySuggestions = useCallback((searchQuery: string): string[] => {
    return [
      `${searchQuery} examples`,
      `${searchQuery} tutorial`,
      `${searchQuery} best practices`,
      `how to ${searchQuery}`,
      `${searchQuery} documentation`
    ];
  }, []);

  const generateRelatedQueries = useCallback((searchQuery: string): string[] => {
    // Mock related queries based on search term
    const related = [
      searchQuery.replace(/\w+$/, 'patterns'),
      searchQuery.replace(/\w+$/, 'implementation'),
      searchQuery.replace(/\w+$/, 'optimization')
    ];
    return related.filter(q => q !== searchQuery);
  }, []);

  const addToSearchHistory = useCallback((searchQuery: string, resultCount: number, searchOptions: MemorySearchOptions) => {
    const historyEntry: MemorySearchHistory = {
      id: Date.now().toString(),
      query: searchQuery,
      timestamp: new Date(),
      resultCount,
      filters: searchOptions,
      userId
    };

    setSearchHistory(prev => [historyEntry, ...prev.slice(0, 9)]); // Keep last 10
  }, [userId]);

  const saveSearch = useCallback(async (name: string) => {
    if (!query.trim()) return;

    try {
      const savedSearch: SavedSearch = {
        id: Date.now().toString(),
        name,
        query,
        filters: {
          tags: filters.tags,
          topK: 20,
          similarityThreshold: 0.5,
          sortBy: filters.sortBy,
          sortOrder: filters.sortOrder
        },
        userId,
        createdAt: new Date(),
        lastUsed: new Date(),
        useCount: 1
      };

      setSavedSearches(prev => [savedSearch, ...prev]);
      
      // In real implementation, save to backend
      console.log('Saved search:', savedSearch);
    } catch (err) {
      console.error('Failed to save search:', err);
    }
  }, [query, filters, userId]);

  const loadSavedSearch = useCallback((savedSearch: SavedSearch) => {
    setQuery(savedSearch.query);
    setFilters(prev => ({
      ...prev,
      tags: savedSearch.filters.tags || [],
      sortBy: savedSearch.filters.sortBy || 'relevance',
      sortOrder: savedSearch.filters.sortOrder || 'desc'
    }));
    
    // Update last used
    setSavedSearches(prev => 
      prev.map(s => s.id === savedSearch.id 
        ? { ...s, lastUsed: new Date(), useCount: s.useCount + 1 }
        : s
      )
    );

    performSearch(savedSearch.query);
  }, [performSearch]);

  const handleMemoryClick = useCallback((memory: MemoryEntry) => {
    setSelectedMemory(memory);
    onMemorySelect?.(memory);
  }, [onMemorySelect]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      performSearch();
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  }, [performSearch]);

  const clearFilters = useCallback(() => {
    setFilters({
      tags: [],
      contentTypes: [],
      clusters: [],
      confidenceRange: [0, 1],
      dateRange: [null, null],
      sortBy: 'relevance',
      sortOrder: 'desc'
    });
  }, []);

  const formatTimestamp = useCallback((timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  }, []);

  const highlightText = useCallback((text: string, searchQuery: string) => {
    if (!searchQuery.trim()) return text;
    
    const regex = new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 px-1 rounded">
          {part}
        </mark>
      ) : part
    );
  }, []);

  return (
    <div className="space-y-4" style={{ height: `${height}px` }}>
      {/* Search Header */}
      <Card className="p-4">
        <div className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                ref={searchInputRef}
                type="text"
                placeholder="Search memories semantically..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setShowSuggestions(true)}
                className="pl-10 pr-4"
              />
              {query && (
                <button
                  onClick={() => setQuery('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Search Suggestions */}
            {showSuggestions && suggestions.length > 0 && (
              <Card className="absolute top-full left-0 right-0 mt-1 z-10 max-h-64 overflow-y-auto">
                <div className="p-2">
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setQuery(suggestion.query);
                        performSearch(suggestion.query);
                      }}
                      className="w-full text-left p-2 hover:bg-gray-50 rounded flex items-center justify-between"
                    >
                      <div className="flex items-center space-x-2">
                        {suggestion.type === 'history' ? (
                          <History className="w-4 h-4 text-gray-400" />
                        ) : (
                          <Search className="w-4 h-4 text-gray-400" />
                        )}
                        <span>{suggestion.query}</span>
                      </div>
                      {suggestion.count && (
                        <Badge variant="secondary" className="text-xs">
                          {suggestion.count}
                        </Badge>
                      )}
                    </button>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Search Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Button
                onClick={() => performSearch()}
                disabled={loading || !query.trim()}
                className="px-6"
              >
                {loading ? 'Searching...' : 'Search'}
              </Button>

              <Button
                variant="outline"
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center space-x-1"
              >
                <Filter className="w-4 h-4" />
                <span>Filters</span>
                {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </Button>

              {query.trim() && (
                <Button
                  variant="outline"
                  onClick={() => {
                    const name = prompt('Enter a name for this search:');
                    if (name) saveSearch(name);
                  }}
                  className="flex items-center space-x-1"
                >
                  <Bookmark className="w-4 h-4" />
                  <span>Save</span>
                </Button>
              )}
            </div>

            {/* Search Stats */}
            {searchResult && (
              <div className="text-sm text-gray-600">
                {searchResult.totalFound.toLocaleString()} results in {searchResult.searchTime}ms
              </div>
            )}
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <Card className="p-4 bg-gray-50">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Tags Filter */}
                <div>
                  <label className="block text-sm font-medium mb-2">Tags</label>
                  <div className="flex flex-wrap gap-1">
                    {searchResult?.facets.tags.slice(0, 5).map(({ tag, count }) => (
                      <button
                        key={tag}
                        onClick={() => {
                          setFilters(prev => ({
                            ...prev,
                            tags: prev.tags.includes(tag)
                              ? prev.tags.filter(t => t !== tag)
                              : [...prev.tags, tag]
                          }));
                        }}
                        className={`text-xs px-2 py-1 rounded ${
                          filters.tags.includes(tag)
                            ? 'bg-blue-500 text-white'
                            : 'bg-white border hover:bg-gray-50'
                        }`}
                      >
                        {tag} ({count})
                      </button>
                    ))}
                  </div>
                </div>

                {/* Sort Options */}
                <div>
                  <label className="block text-sm font-medium mb-2">Sort By</label>
                  <div className="flex space-x-2">
                    <select
                      value={filters.sortBy}
                      onChange={(e) => setFilters(prev => ({ 
                        ...prev, 
                        sortBy: e.target.value as any 
                      }))}
                      className="flex-1 px-3 py-1 border rounded text-sm"
                    >
                      <option value="relevance">Relevance</option>
                      <option value="date">Date</option>
                      <option value="confidence">Confidence</option>
                      <option value="access_count">Access Count</option>
                    </select>
                    <button
                      onClick={() => setFilters(prev => ({
                        ...prev,
                        sortOrder: prev.sortOrder === 'asc' ? 'desc' : 'asc'
                      }))}
                      className="px-2 py-1 border rounded hover:bg-gray-50"
                    >
                      {filters.sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Clear Filters */}
                <div className="flex items-end">
                  <Button
                    variant="outline"
                    onClick={clearFilters}
                    className="text-sm"
                  >
                    Clear Filters
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </Card>

      {/* Search Results */}
      <div className="flex-1 overflow-hidden">
        <Tabs defaultValue="results" className="h-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="results">
              Results {searchResult && `(${searchResult.totalFound})`}
            </TabsTrigger>
            <TabsTrigger value="history">History ({searchHistory.length})</TabsTrigger>
            <TabsTrigger value="saved">Saved ({savedSearches.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="results" className="h-full overflow-y-auto">
            {error ? (
              <Card className="p-6 text-center">
                <div className="text-red-600 mb-2">Search Error</div>
                <p className="text-gray-600 mb-4">{error}</p>
                <Button onClick={() => performSearch()} variant="outline">
                  Try Again
                </Button>
              </Card>
            ) : loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map(i => (
                  <Card key={i} className="p-4">
                    <div className="animate-pulse space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                      <div className="h-3 bg-gray-200 rounded w-full"></div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : searchResult?.memories.length ? (
              <div className="space-y-4">
                {searchResult.memories.map((memory) => (
                  <Card
                    key={memory.id}
                    className={`p-4 cursor-pointer transition-colors hover:bg-gray-50 ${
                      selectedMemory?.id === memory.id ? 'ring-2 ring-blue-500' : ''
                    }`}
                    onClick={() => handleMemoryClick(memory)}
                  >
                    <div className="space-y-2">
                      {/* Memory Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-2">
                          {memory.similarity_score && (
                            <Badge variant="secondary" className="text-xs">
                              {(memory.similarity_score * 100).toFixed(0)}% match
                            </Badge>
                          )}
                          {memory.type && (
                            <Badge variant="outline" className="text-xs">
                              {memory.type}
                            </Badge>
                          )}
                          {memory.confidence && (
                            <div className="flex items-center space-x-1">
                              <Star className="w-3 h-3 text-yellow-500" />
                              <span className="text-xs text-gray-600">
                                {(memory.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <Clock className="w-3 h-3" />
                          <span>{formatTimestamp(memory.timestamp)}</span>
                        </div>
                      </div>

                      {/* Memory Content */}
                      <div className="text-sm">
                        <p className="line-clamp-3">
                          {highlightText(memory.content, query)}
                        </p>
                      </div>

                      {/* Memory Tags */}
                      {memory.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {memory.tags.slice(0, 5).map(tag => (
                            <Badge key={tag} variant="outline" className="text-xs">
                              <Tag className="w-2 h-2 mr-1" />
                              {tag}
                            </Badge>
                          ))}
                          {memory.tags.length > 5 && (
                            <Badge variant="outline" className="text-xs">
                              +{memory.tags.length - 5} more
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            ) : searchResult ? (
              <Card className="p-6 text-center">
                <div className="text-gray-600 mb-2">No memories found</div>
                <p className="text-sm text-gray-500">
                  Try adjusting your search terms or filters
                </p>
              </Card>
            ) : (
              <Card className="p-6 text-center">
                <div className="text-gray-600 mb-2">Start searching</div>
                <p className="text-sm text-gray-500">
                  Enter a search query to find relevant memories
                </p>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="history" className="h-full overflow-y-auto">
            <div className="space-y-2">
              {searchHistory.map((historyItem) => (
                <Card
                  key={historyItem.id}
                  className="p-3 cursor-pointer hover:bg-gray-50"
                  onClick={() => {
                    setQuery(historyItem.query);
                    performSearch(historyItem.query);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <History className="w-4 h-4 text-gray-400" />
                      <span className="font-medium">{historyItem.query}</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-gray-500">
                      <Badge variant="secondary">{historyItem.resultCount} results</Badge>
                      <span>{historyItem.timestamp.toLocaleTimeString()}</span>
                    </div>
                  </div>
                </Card>
              ))}
              {searchHistory.length === 0 && (
                <Card className="p-6 text-center">
                  <div className="text-gray-600">No search history</div>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="saved" className="h-full overflow-y-auto">
            <div className="space-y-2">
              {savedSearches.map((savedSearch) => (
                <Card
                  key={savedSearch.id}
                  className="p-3 cursor-pointer hover:bg-gray-50"
                  onClick={() => loadSavedSearch(savedSearch)}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Bookmark className="w-4 h-4 text-blue-500" />
                        <span className="font-medium">{savedSearch.name}</span>
                      </div>
                      <Badge variant="secondary">{savedSearch.useCount} uses</Badge>
                    </div>
                    <div className="text-sm text-gray-600">
                      {savedSearch.query}
                    </div>
                    <div className="text-xs text-gray-500">
                      Created {savedSearch.createdAt.toLocaleDateString()} • 
                      Last used {savedSearch.lastUsed.toLocaleDateString()}
                    </div>
                  </div>
                </Card>
              ))}
              {savedSearches.length === 0 && (
                <Card className="p-6 text-center">
                  <div className="text-gray-600">No saved searches</div>
                  <p className="text-sm text-gray-500 mt-1">
                    Save frequently used searches for quick access
                  </p>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default MemorySearch;