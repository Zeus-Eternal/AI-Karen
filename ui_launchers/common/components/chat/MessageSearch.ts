// Shared Message Search Component
// Framework-agnostic message search functionality

import { ChatMessage, Theme } from '../../abstractions/types';
import { debounce, formatRelativeTime } from '../../abstractions/utils';

export interface MessageSearchOptions {
  placeholder?: string;
  maxResults?: number;
  enableFilters?: boolean;
  enableHighlighting?: boolean;
  caseSensitive?: boolean;
  searchInAiData?: boolean;
  minQueryLength?: number;
}

export interface SearchFilter {
  role?: 'user' | 'assistant' | 'system';
  dateRange?: {
    start: Date;
    end: Date;
  };
  hasAiData?: boolean;
  tags?: string[];
}

export interface SearchResult {
  message: ChatMessage;
  relevanceScore: number;
  matchedText: string;
  highlightedContent: string;
  context: {
    previousMessage?: ChatMessage;
    nextMessage?: ChatMessage;
  };
}

export interface MessageSearchState {
  query: string;
  results: SearchResult[];
  isSearching: boolean;
  hasSearched: boolean;
  totalResults: number;
  filters: SearchFilter;
  selectedResultId: string | null;
}

export interface MessageSearchCallbacks {
  onSearch?: (query: string, filters: SearchFilter) => void;
  onResultSelect?: (result: SearchResult) => void;
  onClearSearch?: () => void;
}

export class SharedMessageSearch {
  private state: MessageSearchState;
  private options: MessageSearchOptions;
  private callbacks: MessageSearchCallbacks;
  private theme: Theme;
  private messages: ChatMessage[];
  private debouncedSearch: (query: string) => void;

  constructor(
    messages: ChatMessage[],
    theme: Theme,
    options: MessageSearchOptions = {},
    callbacks: MessageSearchCallbacks = {}
  ) {
    this.messages = messages;
    this.theme = theme;
    this.options = {
      placeholder: 'Search messages...',
      maxResults: 50,
      enableFilters: true,
      enableHighlighting: true,
      caseSensitive: false,
      searchInAiData: true,
      minQueryLength: 2,
      ...options
    };
    this.callbacks = callbacks;

    this.state = {
      query: '',
      results: [],
      isSearching: false,
      hasSearched: false,
      totalResults: 0,
      filters: {},
      selectedResultId: null
    };

    // Create debounced search function
    this.debouncedSearch = debounce((query: string) => {
      this.performSearch(query);
    }, 300);
  }

  // Get current state
  getState(): MessageSearchState {
    return { ...this.state };
  }

  // Update state
  updateState(newState: Partial<MessageSearchState>): void {
    this.state = { ...this.state, ...newState };
  }

  // Update messages to search
  updateMessages(messages: ChatMessage[]): void {
    this.messages = messages;
    
    // Re-run search if there's an active query
    if (this.state.query.trim()) {
      this.debouncedSearch(this.state.query);
    }
  }

  // Handle search input change
  handleSearchChange(query: string): void {
    this.updateState({ 
      query,
      selectedResultId: null
    });

    if (query.trim().length >= this.options.minQueryLength!) {
      this.updateState({ isSearching: true });
      this.debouncedSearch(query);
    } else {
      this.clearResults();
    }
  }

  // Update search filters
  updateFilters(filters: Partial<SearchFilter>): void {
    const newFilters = { ...this.state.filters, ...filters };
    this.updateState({ filters: newFilters });

    // Re-run search if there's an active query
    if (this.state.query.trim()) {
      this.debouncedSearch(this.state.query);
    }
  }

  // Perform the actual search
  private performSearch(query: string): void {
    if (!query.trim() || query.trim().length < this.options.minQueryLength!) {
      this.clearResults();
      return;
    }

    const searchTerm = this.options.caseSensitive ? query : query.toLowerCase();
    const results: SearchResult[] = [];

    this.messages.forEach((message, index) => {
      const relevanceScore = this.calculateRelevanceScore(message, searchTerm);
      
      if (relevanceScore > 0) {
        const matchedText = this.extractMatchedText(message, searchTerm);
        const highlightedContent = this.options.enableHighlighting 
          ? this.highlightMatches(message.content, searchTerm)
          : message.content;

        const result: SearchResult = {
          message,
          relevanceScore,
          matchedText,
          highlightedContent,
          context: {
            previousMessage: index > 0 ? this.messages[index - 1] : undefined,
            nextMessage: index < this.messages.length - 1 ? this.messages[index + 1] : undefined
          }
        };

        // Apply filters
        if (this.passesFilters(result)) {
          results.push(result);
        }
      }
    });

    // Sort by relevance score (highest first)
    results.sort((a, b) => b.relevanceScore - a.relevanceScore);

    // Limit results
    const limitedResults = results.slice(0, this.options.maxResults);

    this.updateState({
      results: limitedResults,
      totalResults: results.length,
      isSearching: false,
      hasSearched: true
    });

    if (this.callbacks.onSearch) {
      this.callbacks.onSearch(query, this.state.filters);
    }
  }

  // Calculate relevance score for a message
  private calculateRelevanceScore(message: ChatMessage, searchTerm: string): number {
    let score = 0;
    const content = this.options.caseSensitive ? message.content : message.content.toLowerCase();

    // Exact phrase match gets highest score
    if (content.includes(searchTerm)) {
      score += 10;
      
      // Bonus for matches at the beginning
      if (content.startsWith(searchTerm)) {
        score += 5;
      }
    }

    // Word matches
    const searchWords = searchTerm.split(/\s+/);
    const contentWords = content.split(/\s+/);
    
    searchWords.forEach(searchWord => {
      contentWords.forEach(contentWord => {
        if (contentWord.includes(searchWord)) {
          score += 3;
        }
        if (contentWord === searchWord) {
          score += 2; // Bonus for exact word match
        }
      });
    });

    // Search in AI data if enabled
    if (this.options.searchInAiData && message.aiData) {
      if (message.aiData.keywords) {
        message.aiData.keywords.forEach(keyword => {
          const keywordText = this.options.caseSensitive ? keyword : keyword.toLowerCase();
          if (keywordText.includes(searchTerm)) {
            score += 5;
          }
        });
      }

      if (message.aiData.knowledgeGraphInsights) {
        const insights = this.options.caseSensitive 
          ? message.aiData.knowledgeGraphInsights 
          : message.aiData.knowledgeGraphInsights.toLowerCase();
        
        if (insights.includes(searchTerm)) {
          score += 3;
        }
      }
    }

    return score;
  }

  // Extract the matched text for display
  private extractMatchedText(message: ChatMessage, searchTerm: string): string {
    const content = this.options.caseSensitive ? message.content : message.content.toLowerCase();
    const index = content.indexOf(searchTerm);
    
    if (index === -1) return '';

    const start = Math.max(0, index - 20);
    const end = Math.min(content.length, index + searchTerm.length + 20);
    
    let excerpt = message.content.substring(start, end);
    
    if (start > 0) excerpt = '...' + excerpt;
    if (end < content.length) excerpt = excerpt + '...';
    
    return excerpt;
  }

  // Highlight search matches in content
  private highlightMatches(content: string, searchTerm: string): string {
    if (!this.options.enableHighlighting) return content;

    const regex = new RegExp(
      `(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`,
      this.options.caseSensitive ? 'g' : 'gi'
    );

    return content.replace(regex, '<mark class="karen-search-highlight">$1</mark>');
  }

  // Check if a result passes the current filters
  private passesFilters(result: SearchResult): boolean {
    const { filters } = this.state;
    const { message } = result;

    // Role filter
    if (filters.role && message.role !== filters.role) {
      return false;
    }

    // Date range filter
    if (filters.dateRange) {
      const messageDate = message.timestamp;
      if (messageDate < filters.dateRange.start || messageDate > filters.dateRange.end) {
        return false;
      }
    }

    // AI data filter
    if (filters.hasAiData !== undefined) {
      const hasAiData = !!(message.aiData && Object.keys(message.aiData).length > 0);
      if (hasAiData !== filters.hasAiData) {
        return false;
      }
    }

    // Tags filter
    if (filters.tags && filters.tags.length > 0) {
      const messageKeywords = message.aiData?.keywords || [];
      const hasMatchingTag = filters.tags.some(tag => 
        messageKeywords.some(keyword => 
          keyword.toLowerCase().includes(tag.toLowerCase())
        )
      );
      if (!hasMatchingTag) {
        return false;
      }
    }

    return true;
  }

  // Clear search results
  clearResults(): void {
    this.updateState({
      results: [],
      totalResults: 0,
      isSearching: false,
      hasSearched: false,
      selectedResultId: null
    });
  }

  // Clear entire search
  clearSearch(): void {
    this.updateState({
      query: '',
      results: [],
      totalResults: 0,
      isSearching: false,
      hasSearched: false,
      filters: {},
      selectedResultId: null
    });

    if (this.callbacks.onClearSearch) {
      this.callbacks.onClearSearch();
    }
  }

  // Select a search result
  selectResult(resultId: string): void {
    const result = this.state.results.find(r => r.message.id === resultId);
    
    if (result) {
      this.updateState({ selectedResultId: resultId });
      
      if (this.callbacks.onResultSelect) {
        this.callbacks.onResultSelect(result);
      }
    }
  }

  // Get search statistics
  getSearchStats(): SearchStats {
    const { results, totalResults, hasSearched } = this.state;
    
    if (!hasSearched) {
      return {
        totalResults: 0,
        displayedResults: 0,
        hasMore: false,
        resultsByRole: {},
        averageRelevance: 0
      };
    }

    const resultsByRole = results.reduce((acc, result) => {
      acc[result.message.role] = (acc[result.message.role] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const averageRelevance = results.length > 0
      ? results.reduce((sum, result) => sum + result.relevanceScore, 0) / results.length
      : 0;

    return {
      totalResults,
      displayedResults: results.length,
      hasMore: totalResults > results.length,
      resultsByRole,
      averageRelevance: Math.round(averageRelevance * 100) / 100
    };
  }

  // Get CSS classes
  getCssClasses(): string[] {
    const classes = ['karen-message-search'];
    
    if (this.state.isSearching) {
      classes.push('karen-message-search-loading');
    }
    
    if (this.state.hasSearched && this.state.results.length === 0) {
      classes.push('karen-message-search-no-results');
    }
    
    return classes;
  }

  // Get inline styles
  getInlineStyles(): Record<string, string> {
    return {
      backgroundColor: this.theme.colors.surface,
      border: `1px solid ${this.theme.colors.border}`,
      borderRadius: this.theme.borderRadius,
      fontFamily: this.theme.typography.fontFamily
    };
  }

  // Get render data
  getRenderData(): MessageSearchRenderData {
    return {
      state: this.getState(),
      options: this.options,
      stats: this.getSearchStats(),
      cssClasses: this.getCssClasses(),
      styles: this.getInlineStyles(),
      theme: this.theme,
      handlers: {
        onSearchChange: (query: string) => this.handleSearchChange(query),
        onFilterChange: (filters: Partial<SearchFilter>) => this.updateFilters(filters),
        onResultSelect: (resultId: string) => this.selectResult(resultId),
        onClear: () => this.clearSearch()
      }
    };
  }

  // Update theme
  updateTheme(theme: Theme): void {
    this.theme = theme;
  }
}

// Supporting interfaces
export interface SearchStats {
  totalResults: number;
  displayedResults: number;
  hasMore: boolean;
  resultsByRole: Record<string, number>;
  averageRelevance: number;
}

export interface MessageSearchRenderData {
  state: MessageSearchState;
  options: MessageSearchOptions;
  stats: SearchStats;
  cssClasses: string[];
  styles: Record<string, string>;
  theme: Theme;
  handlers: {
    onSearchChange: (query: string) => void;
    onFilterChange: (filters: Partial<SearchFilter>) => void;
    onResultSelect: (resultId: string) => void;
    onClear: () => void;
  };
}

// Utility functions
export function createMessageSearch(
  messages: ChatMessage[],
  theme: Theme,
  options: MessageSearchOptions = {},
  callbacks: MessageSearchCallbacks = {}
): SharedMessageSearch {
  return new SharedMessageSearch(messages, theme, options, callbacks);
}

export function formatSearchResultPreview(result: SearchResult): string {
  const role = result.message.role === 'user' ? 'You' : 'Karen';
  const time = formatRelativeTime(result.message.timestamp);
  const preview = result.matchedText || result.message.content.substring(0, 100);
  
  return `${role} (${time}): ${preview}`;
}

export function getSearchSuggestions(messages: ChatMessage[]): string[] {
  const keywords = new Set<string>();
  
  messages.forEach(message => {
    if (message.aiData?.keywords) {
      message.aiData.keywords.forEach(keyword => keywords.add(keyword));
    }
    
    // Extract common words from content
    const words = message.content.toLowerCase().match(/\b\w{4,}\b/g) || [];
    words.forEach(word => {
      if (word.length >= 4) {
        keywords.add(word);
      }
    });
  });
  
  return Array.from(keywords).slice(0, 20);
}