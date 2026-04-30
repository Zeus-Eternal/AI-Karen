'use client';

import React, {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Clock, Search, SlidersHorizontal, X } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { PluginSearchParams, PluginSortOrder } from '@/types/plugin';

interface SearchBarProps {
  params: PluginSearchParams;
  onSearch: (params: PluginSearchParams) => void;
  placeholder?: string;
  className?: string;
  showSortOptions?: boolean;
}

type SortOption = {
  value: PluginSortOrder;
  label: string;
};

const SEARCH_HISTORY_STORAGE_KEY = 'plugin-search-history';
const MAX_SEARCH_HISTORY_ITEMS = 5;
const HISTORY_CLOSE_DELAY_MS = 160;

const SORT_OPTIONS: SortOption[] = [
  { value: 'popularity', label: 'Most Popular' },
  { value: 'newest', label: 'Newest' },
  { value: 'name', label: 'Name A-Z' },
  { value: 'updated', label: 'Recently Updated' },
  { value: 'rating', label: 'Highest Rated' },
];

const cleanString = (value: unknown): string => {
  return typeof value === 'string' ? value.trim() : '';
};

const normalizeHistory = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return [];
  }

  const seen = new Set<string>();

  return value
    .map((item) => cleanString(item))
    .filter((item) => {
      const normalized = item.toLowerCase();

      if (!item || seen.has(normalized)) {
        return false;
      }

      seen.add(normalized);
      return true;
    })
    .slice(0, MAX_SEARCH_HISTORY_ITEMS);
};

const readSearchHistory = (): string[] => {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const saved = window.localStorage.getItem(SEARCH_HISTORY_STORAGE_KEY);

    if (!saved) {
      return [];
    }

    return normalizeHistory(JSON.parse(saved));
  } catch {
    return [];
  }
};

const writeSearchHistory = (history: string[]): void => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.localStorage.setItem(
      SEARCH_HISTORY_STORAGE_KEY,
      JSON.stringify(normalizeHistory(history)),
    );
  } catch {
    // Search history is a convenience cache. Storage failure should not block search.
  }
};

const getSortLabel = (sortBy: PluginSearchParams['sort_by']): string => {
  return SORT_OPTIONS.find((option) => option.value === sortBy)?.label || 'Default';
};

export function SearchBar({
  params,
  onSearch,
  placeholder = 'Search plugins...',
  className = '',
  showSortOptions = true,
}: SearchBarProps) {
  const historyId = useId();
  const sortOptionsId = useId();
  const closeHistoryTimerRef = useRef<number | null>(null);

  const [localQuery, setLocalQuery] = useState(cleanString(params.query));
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const trimmedQuery = cleanString(localQuery);
  const hasHistory = searchHistory.length > 0;
  const shouldShowHistory = showHistory && hasHistory && !trimmedQuery;
  const sortLabel = useMemo(() => getSortLabel(params.sort_by), [params.sort_by]);

  useEffect(() => {
    setSearchHistory(readSearchHistory());
  }, []);

  useEffect(() => {
    setLocalQuery(cleanString(params.query));
  }, [params.query]);

  const clearHistoryCloseTimer = useCallback(() => {
    if (closeHistoryTimerRef.current === null || typeof window === 'undefined') {
      return;
    }

    window.clearTimeout(closeHistoryTimerRef.current);
    closeHistoryTimerRef.current = null;
  }, []);

  useEffect(() => {
    return () => {
      clearHistoryCloseTimer();
    };
  }, [clearHistoryCloseTimer]);

  const saveToHistory = useCallback((query: string) => {
    const normalizedQuery = cleanString(query);

    if (!normalizedQuery) {
      return;
    }

    setSearchHistory((currentHistory) => {
      const updated = normalizeHistory([
        normalizedQuery,
        ...currentHistory.filter(
          (item) => item.toLowerCase() !== normalizedQuery.toLowerCase(),
        ),
      ]);

      writeSearchHistory(updated);
      return updated;
    });
  }, []);

  const executeSearch = useCallback(
    (query: string) => {
      const normalizedQuery = cleanString(query);

      setLocalQuery(normalizedQuery);
      setShowHistory(false);

      if (normalizedQuery) {
        saveToHistory(normalizedQuery);
      }

      /*
       * SearchBar only emits the next search contract.
       * The store/API owns query execution, backend filtering, sorting, and pagination.
       */
      onSearch({
        ...params,
        query: normalizedQuery || undefined,
        page: 1,
      });
    },
    [onSearch, params, saveToHistory],
  );

  const handleClear = useCallback(() => {
    setLocalQuery('');
    setShowHistory(false);

    onSearch({
      ...params,
      query: undefined,
      page: 1,
    });
  }, [onSearch, params]);

  const handleSortChange = useCallback(
    (sort_by: PluginSortOrder) => {
      setShowAdvanced(false);

      onSearch({
        ...params,
        sort_by,
        page: 1,
      });
    },
    [onSearch, params],
  );

  const handleFocus = useCallback(() => {
    clearHistoryCloseTimer();
    setShowHistory(true);
  }, [clearHistoryCloseTimer]);

  const handleBlur = useCallback(() => {
    clearHistoryCloseTimer();

    if (typeof window !== 'undefined') {
      closeHistoryTimerRef.current = window.setTimeout(() => {
        setShowHistory(false);
      }, HISTORY_CLOSE_DELAY_MS);
    }
  }, [clearHistoryCloseTimer]);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        executeSearch(localQuery);
        return;
      }

      if (event.key === 'Escape') {
        setShowHistory(false);
        setShowAdvanced(false);
      }
    },
    [executeSearch, localQuery],
  );

  return (
    <div className={`flex flex-col gap-3 ${className}`.trim()}>
      <div className="relative">
        <Search
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />

        <Input
          type="search"
          placeholder={placeholder}
          value={localQuery}
          onChange={(event) => setLocalQuery(event.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
          className="pl-10 pr-10"
          aria-label="Search plugins"
          aria-autocomplete="list"
          aria-expanded={shouldShowHistory}
          aria-controls={shouldShowHistory ? historyId : undefined}
        />

        {trimmedQuery && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute right-2 top-1/2 h-6 w-6 -translate-y-1/2 p-0"
            onClick={handleClear}
            aria-label="Clear plugin search"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </Button>
        )}

        {shouldShowHistory && (
          <div
            id={historyId}
            className="absolute left-0 right-0 top-full z-50 mt-1 rounded-md border bg-background shadow-lg"
            role="listbox"
            aria-label="Recent plugin searches"
            onMouseDown={(event) => {
              /*
               * Prevent input blur from closing the menu before a history item
               * can run its search.
               */
              event.preventDefault();
            }}
          >
            <div className="p-2">
              <div className="mb-1 flex items-center gap-2 px-2 py-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" aria-hidden="true" />
                Recent searches
              </div>

              {searchHistory.map((historyItem) => (
                <button
                  key={historyItem}
                  type="button"
                  role="option"
                  className="w-full rounded-sm px-2 py-1.5 text-left text-sm transition-colors hover:bg-accent"
                  onClick={() => executeSearch(historyItem)}
                >
                  {historyItem}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {showSortOptions && (
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowAdvanced((current) => !current)}
            className="h-7 text-xs"
            aria-expanded={showAdvanced}
            aria-controls={showAdvanced ? sortOptionsId : undefined}
          >
            <SlidersHorizontal className="mr-1 h-3 w-3" aria-hidden="true" />
            Sort by: {sortLabel}
          </Button>

          {showAdvanced && (
            <div
              id={sortOptionsId}
              className="ml-2 flex flex-wrap gap-2"
              role="group"
              aria-label="Plugin sort options"
            >
              {SORT_OPTIONS.map((option) => {
                const isSelected = params.sort_by === option.value;

                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleSortChange(option.value)}
                    className="rounded-full"
                    aria-pressed={isSelected}
                  >
                    <Badge
                      variant={isSelected ? 'default' : 'outline'}
                      className="cursor-pointer hover:bg-accent"
                    >
                      {option.label}
                    </Badge>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}