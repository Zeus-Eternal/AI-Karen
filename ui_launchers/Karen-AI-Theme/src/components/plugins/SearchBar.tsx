'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Search, X, Clock, SlidersHorizontal } from 'lucide-react';
import { PluginSearchParams, PluginSortOrder } from '@/types/plugin';

interface SearchBarProps {
  params: PluginSearchParams;
  onSearch: (params: PluginSearchParams) => void;
  placeholder?: string;
  className?: string;
  showSortOptions?: boolean;
}

export function SearchBar({ 
  params, 
  onSearch, 
  placeholder = 'Search plugins...', 
  className,
  showSortOptions = true 
}: SearchBarProps) {
  const [localQuery, setLocalQuery] = useState(params.query || '');
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('plugin-search-history');
      if (saved) {
        setSearchHistory(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Failed to load search history:', error);
    }
  }, []);

  const saveToHistory = useCallback((query: string) => {
    if (!query.trim()) return;
    
    try {
      const updated = [query, ...searchHistory.filter(h => h !== query)].slice(0, 5);
      setSearchHistory(updated);
      localStorage.setItem('plugin-search-history', JSON.stringify(updated));
    } catch (error) {
      console.error('Failed to save search history:', error);
    }
  }, [searchHistory]);

  const handleSearch = useCallback((query: string) => {
    setLocalQuery(query);
    setShowHistory(false);
    
    if (query.trim()) {
      saveToHistory(query.trim());
    }
    
    onSearch({ ...params, query: query.trim(), page: 1 });
  }, [params, onSearch, saveToHistory]);

  const handleClear = () => {
    setLocalQuery('');
    onSearch({ ...params, query: undefined, page: 1 });
  };

  const handleSortChange = (sort_by: PluginSortOrder) => {
    onSearch({ ...params, sort_by, page: 1 });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(localQuery);
    } else if (e.key === 'Escape') {
      setShowHistory(false);
    }
  };

  const sortOptions: { value: PluginSortOrder; label: string }[] = [
    { value: 'popularity', label: 'Most Popular' },
    { value: 'newest', label: 'Newest' },
    { value: 'name', label: 'Name A-Z' },
    { value: 'updated', label: 'Recently Updated' },
    { value: 'rating', label: 'Highest Rated' },
  ];

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder={placeholder}
          value={localQuery}
          onChange={(e) => setLocalQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowHistory(true)}
          onBlur={() => setTimeout(() => setShowHistory(false), 200)}
          className="pl-10 pr-10"
        />
        {localQuery && (
          <Button
            variant="ghost"
            size="sm"
            className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
            onClick={handleClear}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
        
        {showHistory && searchHistory.length > 0 && !localQuery && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-background border rounded-md shadow-lg z-50">
            <div className="p-2">
              <div className="flex items-center gap-2 px-2 py-1 text-xs text-muted-foreground mb-1">
                <Clock className="h-3 w-3" />
                Recent searches
              </div>
              {searchHistory.map((history, index) => (
                <button
                  key={index}
                  className="w-full text-left px-2 py-1.5 text-sm hover:bg-accent rounded-sm transition-colors"
                  onClick={() => handleSearch(history)}
                >
                  {history}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {showSortOptions && (
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="h-7 text-xs"
          >
            <SlidersHorizontal className="h-3 w-3 mr-1" />
            Sort by: {sortOptions.find(o => o.value === params.sort_by)?.label}
          </Button>
          
          {showAdvanced && (
            <div className="flex flex-wrap gap-2 ml-2">
              {sortOptions.map((option) => (
                <Badge
                  key={option.value}
                  variant={params.sort_by === option.value ? 'default' : 'outline'}
                  className="cursor-pointer hover:bg-accent"
                  onClick={() => {
                    handleSortChange(option.value);
                    setShowAdvanced(false);
                  }}
                >
                  {option.label}
                </Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
