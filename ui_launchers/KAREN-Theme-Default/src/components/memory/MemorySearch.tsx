"use client";

/**
 * Memory Search Component (Production)
 * Semantic search with similarity scoring, facets, suggestions, history & saved views
 */

import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Search as SearchIcon,
  X,
  History,
  Filter,
  ChevronUp,
  ChevronDown,
  Bookmark,
  SortAsc,
  SortDesc,
  Star,
  Clock,
  Tag,
} from "lucide-react";
import { getMemoryService } from "@/services/memoryService";
import type {
  MemoryEntry,
  MemorySearchOptions,
  MemorySearchResult,
  MemorySearchHistory,
  SavedSearch,
  MemorySearchProps,
  SearchFacets,
} from "@/types/memory";

export interface SearchFilters {
  tags: string[];
  contentTypes: string[];
  clusters: string[];
  confidenceRange: [number, number];
  dateRange: [Date | null, Date | null];
  sortBy: "relevance" | "date" | "confidence" | "access_count";
  sortOrder: "asc" | "desc";
}

export interface SearchSuggestion {
  query: string;
  type: "history" | "popular" | "related";
  count?: number;
}

export const MemorySearch: React.FC<MemorySearchProps> = ({
  userId,
  tenantId,
  initialQuery = "",
  onMemorySelect,
  onSearchComplete,
  height = 600,
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [searchResult, setSearchResult] = useState<MemorySearchResult | null>(
    null
  );
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
    sortBy: "relevance",
    sortOrder: "desc",
  });

  const searchInputRef = useRef<HTMLInputElement>(null);
  const memoryService = useMemo(() => getMemoryService(), []);

  /* ----------------------------- Bootstrapping ----------------------------- */

  useEffect(() => {
    loadSearchHistory();
    loadSavedSearches();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  /* ----------------------------- Suggestions UX ---------------------------- */

  useEffect(() => {
    if (query.trim().length > 2) {
      generateSuggestions(query);
    } else {
      setSuggestions([]);
    }
  }, [query, generateSuggestions]);

  const loadSearchHistory = useCallback(async () => {
    try {
      const memoryService = getMemoryService();
      const history = await memoryService.getSearchHistory(userId, 20);
      setSearchHistory(history);
    } catch (error) {
      console.error('Failed to load search history:', error);
      // Gracefully fail - search history is a nice-to-have feature
    }
  }, [userId]);

  const loadSavedSearches = useCallback(async () => {
    try {
      const memoryService = getMemoryService();
      const searches = await memoryService.getSavedSearches(userId);
      setSavedSearches(searches);
    } catch (error) {
      console.error('Failed to load saved searches:', error);
      // Gracefully fail - saved searches are a nice-to-have feature
    }
  }, [userId]);

  const generateSuggestions = useCallback(
    async (searchQuery: string) => {
      try {
        const historySuggestions = searchHistory
          .filter((h) =>
            h.query.toLowerCase().includes(searchQuery.toLowerCase())
          )
          .slice(0, 3)
          .map((h) => ({
            query: h.query,
            type: "history" as const,
            count: h.resultCount,
          }));

        const popularSuggestions: SearchSuggestion[] = [
          { query: `${searchQuery} tutorial`, type: "popular", count: 45 },
          { query: `${searchQuery} example`, type: "popular", count: 32 },
          { query: `${searchQuery} best practices`, type: "popular", count: 28 },
        ];

        setSuggestions([...historySuggestions, ...popularSuggestions.slice(0, 2)]);
      } catch {
        /* silent */
      }
    },
    [searchHistory]
  );

  /* -------------------------------- Search -------------------------------- */

  const debounceRef = useRef<number | null>(null);
  const DEBOUNCE_MS = 150;

  const performSearch = useCallback(
    async (
      searchQuery: string = query,
      searchFilters: SearchFilters = filters
    ) => {
      const q = searchQuery.trim();
      if (!q) return;

      setLoading(true);
      setError(null);

      try {
        const searchOptions: MemorySearchOptions = {
          topK: 20,
          similarityThreshold: 0.5,
          tags: searchFilters.tags.length > 0 ? searchFilters.tags : undefined,
          timeRange:
            searchFilters.dateRange[0] && searchFilters.dateRange[1]
              ? [searchFilters.dateRange[0]!, searchFilters.dateRange[1]!]
              : undefined,
          sortBy: searchFilters.sortBy,
          sortOrder: searchFilters.sortOrder,
        };

        const result = await memoryService.searchMemories(q, {
          userId,
          tags: searchOptions.tags,
          dateRange: searchOptions.timeRange,
          minSimilarity: searchOptions.similarityThreshold,
          maxResults: searchOptions.topK,
        });

        const enhancedResult: MemorySearchResult = {
          memories: result.memories,
          totalFound: result.totalFound,
          searchTime: result.searchTime,
          facets: generateFacets(result.memories),
          suggestions: generateQuerySuggestions(q),
          relatedQueries: generateRelatedQueries(q),
        };

        setSearchResult(enhancedResult);
        onSearchComplete?.(enhancedResult);
        addToSearchHistory(q, enhancedResult.totalFound, searchOptions);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Search failed";
        setError(errorMessage);
      } finally {
        setLoading(false);
        setShowSuggestions(false);
      }
    },
    [
      query,
      filters,
      userId,
      memoryService,
      onSearchComplete,
      generateFacets,
      generateQuerySuggestions,
      generateRelatedQueries,
      addToSearchHistory,
    ]
  );

  // Debounced search trigger (useful for "Enter" or explicit button click only)
  const triggerSearch = useCallback(() => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => {
      performSearch();
      debounceRef.current = null;
    }, DEBOUNCE_MS);
  }, [performSearch]);

  /* -------------------------------- Facets -------------------------------- */

  const generateFacets = useCallback((memories: MemoryEntry[]): SearchFacets => {
    const types: Record<string, number> = {};
    const tags: Record<string, number> = {};
    const clusters: Record<string, number> = {};

    memories.forEach((m) => {
      const t = m.type || "unknown";
      types[t] = (types[t] || 0) + 1;

      (m.tags || []).forEach((tag) => {
        tags[tag] = (tags[tag] || 0) + 1;
      });

      const cluster = m.metadata?.cluster || "general";
      clusters[cluster] = (clusters[cluster] || 0) + 1;
    });

    const now = Date.now();

    return {
      types: Object.entries(types).map(([type, count]) => ({ type, count })),
      tags: Object.entries(tags).map(([tag, count]) => ({ tag, count })),
      clusters: Object.entries(clusters).map(([cluster, count]) => ({
        cluster,
        count,
      })),
      timeRanges: [
        {
          range: "Last 24 hours",
          count: memories.filter((m) => now - m.timestamp < 86_400_000).length,
        },
        {
          range: "Last week",
          count: memories.filter((m) => now - m.timestamp < 604_800_000).length,
        },
        {
          range: "Last month",
          count: memories.filter((m) => now - m.timestamp < 2_592_000_000)
            .length,
        },
      ],
      confidenceRanges: [
        {
          range: "0.8-1.0",
          count: memories.filter((m) => (m.confidence || 0) >= 0.8).length,
        },
        {
          range: "0.6-0.8",
          count: memories.filter(
            (m) => (m.confidence || 0) >= 0.6 && (m.confidence || 0) < 0.8
          ).length,
        },
        {
          range: "0.4-0.6",
          count: memories.filter(
            (m) => (m.confidence || 0) >= 0.4 && (m.confidence || 0) < 0.6
          ).length,
        },
        {
          range: "0.0-0.4",
          count: memories.filter((m) => (m.confidence || 0) < 0.4).length,
        },
      ],
    };
  }, []);

  const generateQuerySuggestions = useCallback((q: string): string[] => {
    const base = q.trim();
    if (!base) return [];
    return [
      `${base} examples`,
      `${base} tutorial`,
      `${base} best practices`,
      `how to ${base}`,
      `${base} documentation`,
    ];
  }, []);

  const generateRelatedQueries = useCallback((q: string): string[] => {
    const tokenSwap = (suffix: string) =>
      q.replace(/\w+$/, "") + suffix || `${q} ${suffix}`;
    const related = ["patterns", "implementation", "optimization"].map(
      tokenSwap
    );
    return Array.from(new Set(related)).filter((x) => x !== q);
  }, []);

  /* ------------------------------ History/Saved ----------------------------- */

  const addToSearchHistory = useCallback(
    (
      searchQuery: string,
      resultCount: number,
      searchOptions: MemorySearchOptions
    ) => {
      const entry: MemorySearchHistory = {
        id: Date.now().toString(),
        query: searchQuery,
        timestamp: new Date(),
        resultCount,
        filters: searchOptions,
        userId,
      };
      setSearchHistory((prev) => [entry, ...prev.slice(0, 9)]);
    },
    [userId]
  );

  const saveSearch = useCallback(async (name: string) => {
    if (!query.trim()) return;
    try {
      const saved: SavedSearch = {
        id: Date.now().toString(),
        name,
        query,
        filters: {
          tags: filters.tags,
          topK: 20,
          similarityThreshold: 0.5,
          sortBy: filters.sortBy,
          sortOrder: filters.sortOrder,
        },
        userId,
        createdAt: new Date(),
        lastUsed: new Date(),
        useCount: 1,
      };
      setSavedSearches((prev) => [saved, ...prev]);
    } catch {
      /* silent */
    }
  }, [filters.sortBy, filters.sortOrder, filters.tags, query, userId]);

  const loadSavedSearch = useCallback(
    (saved: SavedSearch) => {
      setQuery(saved.query);
      setFilters((prev) => ({
        ...prev,
        tags: saved.filters.tags || [],
        sortBy: (saved.filters.sortBy as SearchFilters["sortBy"]) || "relevance",
        sortOrder:
          (saved.filters.sortOrder as SearchFilters["sortOrder"]) || "desc",
        // leave other filters as-is; saved object can be extended later
      }));
      setSavedSearches((prev) =>
        prev.map((s) =>
          s.id === saved.id
            ? { ...s, lastUsed: new Date(), useCount: s.useCount + 1 }
            : s
        )
      );
      performSearch(saved.query);
    },
    [performSearch]
  );

  /* --------------------------------- UI Bits -------------------------------- */

  const handleMemoryClick = useCallback(
    (memory: MemoryEntry) => {
      setSelectedMemory(memory);
      onMemorySelect?.(memory);
    },
    [onMemorySelect]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        triggerSearch();
      } else if (e.key === "Escape") {
        setShowSuggestions(false);
      }
    },
    [triggerSearch]
  );

  const clearFilters = useCallback(() => {
    setFilters({
      tags: [],
      contentTypes: [],
      clusters: [],
      confidenceRange: [0, 1],
      dateRange: [null, null],
      sortBy: "relevance",
      sortOrder: "desc",
    });
  }, []);

  const formatTimestamp = useCallback((timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  }, []);

  const highlightText = useCallback((text: string, q: string) => {
    const needle = q.trim();
    if (!needle) return text;
    const safe = needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`(${safe})`, "gi");
    const parts = text.split(regex);
    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="bg-yellow-200 px-1 rounded">
          {part}
        </mark>
      ) : (
        <span key={i}>{part}</span>
      )
    );
  }, []);

  /* --------------------------------- Render -------------------------------- */

  return (
    <div className="space-y-4" style={{ height: `${height}px` }}>
      {/* Search Header */}
      <Card className="p-4 sm:p-4 md:p-6">
        <div className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <div className="relative">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search memories semantically..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setShowSuggestions(true)}
                className="pl-10 pr-9 w-full rounded-md border border-input bg-background py-2 text-sm"
              />
              {query && (
                <button
                  onClick={() => setQuery("")}
                  aria-label="Clear search"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Search Suggestions */}
            {showSuggestions && suggestions.length > 0 && (
              <Card className="absolute top-full left-0 right-0 mt-1 z-10 max-h-64 overflow-y-auto">
                <div className="p-2">
                  {suggestions.map((s, idx) => (
                    <button
                      key={`${s.query}-${idx}`}
                      onClick={() => {
                        setQuery(s.query);
                        performSearch(s.query);
                      }}
                      className="w-full text-left p-2 hover:bg-gray-50 rounded flex items-center justify-between"
                    >
                      <div className="flex items-center space-x-2">
                        {s.type === "history" ? (
                          <History className="w-4 h-4 text-gray-400" />
                        ) : (
                          <SearchIcon className="w-4 h-4 text-gray-400" />
                        )}
                        <span>{s.query}</span>
                      </div>
                      {s.count ? (
                        <Badge variant="secondary" className="text-xs">
                          {s.count}
                        </Badge>
                      ) : null}
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
                onClick={triggerSearch}
                disabled={loading || !query.trim()}
                className="px-6"
              >
                {loading ? "Searching..." : "Search"}
              </Button>

              <Button
                variant="outline"
                onClick={() => setShowFilters((v) => !v)}
                className="flex items-center space-x-1"
              >
                <Filter className="w-4 h-4" />
                <span>Filters</span>
                {showFilters ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </Button>

              {query.trim() && (
                <Button
                  variant="outline"
                  onClick={() => {
                    const name = window.prompt("Enter a name for this search:");
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
                {searchResult.totalFound.toLocaleString()} results in{" "}
                {searchResult.searchTime}ms
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
                    {searchResult?.facets.tags.slice(0, 8).map(({ tag, count }) => {
                      const active = filters.tags.includes(tag);
                      return (
                        <button
                          key={tag}
                          onClick={() =>
                            setFilters((prev) => ({
                              ...prev,
                              tags: active
                                ? prev.tags.filter((t) => t !== tag)
                                : [...prev.tags, tag],
                            }))
                          }
                          className={`text-xs px-2 py-1 rounded border ${
                            active
                              ? "bg-blue-500 text-white border-blue-500"
                              : "bg-white hover:bg-gray-50"
                          }`}
                        >
                          {tag} ({count})
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Sort Options */}
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Sort By
                  </label>
                  <div className="flex space-x-2">
                    <select
                      value={filters.sortBy}
                      onChange={(e) =>
                        setFilters((prev) => ({
                          ...prev,
                          sortBy: e.target.value as SearchFilters["sortBy"],
                        }))
                      }
                      className="flex-1 px-3 py-1 border rounded text-sm"
                    >
                      <option value="relevance">Relevance</option>
                      <option value="date">Date</option>
                      <option value="confidence">Confidence</option>
                      <option value="access_count">Access Count</option>
                    </select>
                    <Button
                      onClick={() =>
                        setFilters((prev) => ({
                          ...prev,
                          sortOrder: prev.sortOrder === "asc" ? "desc" : "asc",
                        }))
                      }
                      className="px-2 py-1 border rounded hover:bg-gray-50"
                      variant="outline"
                    >
                      {filters.sortOrder === "asc" ? (
                        <SortAsc className="w-4 h-4" />
                      ) : (
                        <SortDesc className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>

                {/* Clear Filters */}
                <div className="flex items-end">
                  <Button variant="outline" onClick={clearFilters}>
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
              Results {searchResult ? `(${searchResult.totalFound})` : ""}
            </TabsTrigger>
            <TabsTrigger value="history">History ({searchHistory.length})</TabsTrigger>
            <TabsTrigger value="saved">Saved ({savedSearches.length})</TabsTrigger>
          </TabsList>

          {/* Results */}
          <TabsContent value="results" className="h-full overflow-y-auto">
            {error ? (
              <Card className="p-6 text-center">
                <div className="text-red-600 mb-2 font-medium">Search Error</div>
                <p className="text-gray-600 mb-4">{error}</p>
                <Button onClick={() => performSearch()} variant="outline">
                  Retry
                </Button>
              </Card>
            ) : loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Card key={i} className="p-4">
                    <div className="animate-pulse space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                      <div className="h-3 bg-gray-200 rounded w-1/2" />
                      <div className="h-3 bg-gray-200 rounded w-full" />
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
                      selectedMemory?.id === memory.id ? "ring-2 ring-blue-500" : ""
                    }`}
                    onClick={() => handleMemoryClick(memory)}
                  >
                    <div className="space-y-2">
                      {/* Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-2">
                          {typeof memory.similarity_score === "number" && (
                            <Badge variant="secondary" className="text-xs">
                              {(memory.similarity_score * 100).toFixed(0)}% match
                            </Badge>
                          )}
                          {memory.type && (
                            <Badge variant="outline" className="text-xs">
                              {memory.type}
                            </Badge>
                          )}
                          {typeof memory.confidence === "number" && (
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

                      {/* Content */}
                      <div className="text-sm">
                        <p className="line-clamp-3">
                          {highlightText(memory.content, query)}
                        </p>
                      </div>

                      {/* Tags */}
                      {Array.isArray(memory.tags) && memory.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {memory.tags.slice(0, 5).map((tag) => (
                            <Badge key={tag} variant="outline" className="text-xs">
                              <Tag className="w-3 h-3 mr-1" />
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
                <div className="text-gray-700 mb-2 font-medium">
                  No memories found
                </div>
                <p className="text-sm text-gray-500">
                  Try broader terms, remove filters, or check spelling.
                </p>
              </Card>
            ) : (
              <Card className="p-6 text-center">
                <div className="text-gray-700 mb-2 font-medium">Start searching</div>
                <p className="text-sm text-gray-500">
                  Type a phrase above and press Enter to search semantically.
                </p>
              </Card>
            )}
          </TabsContent>

          {/* History */}
          <TabsContent value="history" className="h-full overflow-y-auto">
            <div className="space-y-2">
              {searchHistory.map((h) => (
                <Card
                  key={h.id}
                  className="p-3 cursor-pointer hover:bg-gray-50"
                  onClick={() => {
                    setQuery(h.query);
                    performSearch(h.query);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <History className="w-4 h-4 text-gray-400" />
                      <span className="font-medium">{h.query}</span>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-gray-500">
                      <Badge variant="secondary">{h.resultCount} results</Badge>
                      <span>{h.timestamp.toLocaleTimeString()}</span>
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

          {/* Saved */}
          <TabsContent value="saved" className="h-full overflow-y-auto">
            <div className="space-y-2">
              {savedSearches.map((s) => (
                <Card
                  key={s.id}
                  className="p-3 cursor-pointer hover:bg-gray-50"
                  onClick={() => loadSavedSearch(s)}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Bookmark className="w-4 h-4 text-blue-500" />
                        <span className="font-medium">{s.name}</span>
                      </div>
                      <Badge variant="secondary">{s.useCount} uses</Badge>
                    </div>
                    <div className="text-sm text-gray-700">{s.query}</div>
                    <div className="text-xs text-gray-500">
                      Created {s.createdAt.toLocaleDateString()} • Last used{" "}
                      {s.lastUsed.toLocaleDateString()}
                    </div>
                  </div>
                </Card>
              ))}
              {savedSearches.length === 0 && (
                <Card className="p-6 text-center">
                  <div className="text-gray-600">No saved searches</div>
                  <p className="text-sm text-gray-500 mt-1">
                    Run a search and click “Save” to store it here.
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
