import React, { useState, useEffect, useRef } from 'react';

// Type definitions
interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      xxl: string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  aiData?: {
    keywords?: string[];
    knowledgeGraphInsights?: string;
    confidence?: number;
    reasoning?: string;
  };
  shouldAutoPlay?: boolean;
  attachments?: Array<{
    id: string;
    name: string;
    size: string;
    type: string;
    url?: string;
  }>;
}

interface MessageSearchProps {
  theme: Theme;
  messages: ChatMessage[];
  onSearchResult?: (results: ChatMessage[]) => void;
  onHighlightMessage?: (messageId: string) => void;
  className?: string;
}

interface SearchResult {
  message: ChatMessage;
  startIndex: number;
  endIndex: number;
  context: string;
}

export const MessageSearchComponent: React.FC<MessageSearchProps> = ({
  theme,
  messages,
  onSearchResult,
  onHighlightMessage,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [currentResultIndex, setCurrentResultIndex] = useState(-1);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when search is opened
  useEffect(() => {
    if (isSearchOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isSearchOpen]);

  // Handle search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setCurrentResultIndex(-1);
      if (onSearchResult) {
        onSearchResult([]);
      }
      return;
    }

    const query = searchQuery.toLowerCase();
    const results: SearchResult[] = [];

    messages.forEach(message => {
      const content = message.content.toLowerCase();
      let index = content.indexOf(query);
      
      while (index !== -1) {
        // Get context around the match (50 characters before and after)
        const contextStart = Math.max(0, index - 50);
        const contextEnd = Math.min(message.content.length, index + query.length + 50);
        const context = message.content.substring(contextStart, contextEnd);
        
        results.push({
          message,
          startIndex: index,
          endIndex: index + query.length,
          context
        });
        
        index = content.indexOf(query, index + 1);
      }
    });

    setSearchResults(results);
    setCurrentResultIndex(results.length > 0 ? 0 : -1);
    
    if (onSearchResult) {
      onSearchResult(results.map(result => result.message));
    }
  }, [searchQuery, messages, onSearchResult]);

  // Highlight current result
  useEffect(() => {
    if (currentResultIndex >= 0 && currentResultIndex < searchResults.length && onHighlightMessage) {
      const result = searchResults[currentResultIndex];
      if (result) {
        onHighlightMessage(result.message.id);
      }
    }
  }, [currentResultIndex, searchResults, onHighlightMessage]);

  // Navigate to next result
  const goToNextResult = () => {
    if (searchResults.length === 0) return;
    setCurrentResultIndex(prev => (prev + 1) % searchResults.length);
  };

  // Navigate to previous result
  const goToPrevResult = () => {
    if (searchResults.length === 0) return;
    setCurrentResultIndex(prev => (prev - 1 + searchResults.length) % searchResults.length);
  };

  // Handle key down events
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (e.shiftKey) {
        goToPrevResult();
      } else {
        goToNextResult();
      }
    } else if (e.key === 'Escape') {
      setIsSearchOpen(false);
      setSearchQuery('');
    }
  };

  // Clear search
  const clearSearch = () => {
    setSearchQuery('');
  };

  // Toggle search
  const toggleSearch = () => {
    setIsSearchOpen(!isSearchOpen);
  };

  const containerStyle: React.CSSProperties = {
    position: 'relative',
    width: '100%',
    marginBottom: theme.spacing.md
  };

  const inputContainerStyle: React.CSSProperties = {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    overflow: 'hidden'
  };

  const inputStyle: React.CSSProperties = {
    flex: 1,
    backgroundColor: 'transparent',
    border: 'none',
    padding: `${theme.spacing.sm} ${theme.spacing.sm} ${theme.spacing.sm} ${theme.spacing.lg}`,
    color: theme.colors.text,
    fontSize: theme.typography.fontSize.sm,
    fontFamily: theme.typography.fontFamily,
    outline: 'none'
  };

  const searchIconStyle: React.CSSProperties = {
    position: 'absolute',
    left: theme.spacing.sm,
    top: '50%',
    transform: 'translateY(-50%)',
    color: theme.colors.textSecondary,
    pointerEvents: 'none'
  };

  const clearButtonStyle: React.CSSProperties = {
    backgroundColor: 'transparent',
    color: theme.colors.textSecondary,
    border: 'none',
    borderRadius: '50%',
    width: '24px',
    height: '24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    fontSize: '0.8rem',
    padding: 0,
    marginRight: theme.spacing.xs
  };

  const resultsContainerStyle: React.CSSProperties = {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    backgroundColor: theme.colors.surface,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    boxShadow: theme.shadows.lg,
    zIndex: 100,
    marginTop: theme.spacing.xs,
    maxHeight: '300px',
    overflowY: 'auto'
  };

  const resultItemStyle: React.CSSProperties = {
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    borderBottom: `1px solid ${theme.colors.border}`,
    cursor: 'pointer',
    transition: 'background-color 0.2s ease'
  };

  const highlightedResultStyle: React.CSSProperties = {
    ...resultItemStyle,
    backgroundColor: `${theme.colors.primary}10`
  };

  const resultTextStyle: React.CSSProperties = {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text,
    marginBottom: theme.spacing.xs
  };

  const resultMetaStyle: React.CSSProperties = {
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.textSecondary
  };

  const matchHighlightStyle: React.CSSProperties = {
    backgroundColor: `${theme.colors.warning}30`,
    fontWeight: theme.typography.fontWeight.medium
  };

  const navigationStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: `${theme.spacing.xs} ${theme.spacing.md}`,
    backgroundColor: theme.colors.background,
    borderBottom: `1px solid ${theme.colors.border}`,
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.textSecondary
  };

  const navButtonStyle: React.CSSProperties = {
    backgroundColor: 'transparent',
    color: theme.colors.primary,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    padding: `2px ${theme.spacing.sm}`,
    fontSize: theme.typography.fontSize.xs,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing.xs
  };

  return (
    <div className={`copilot-message-search ${className}`} style={containerStyle}>
      {/* Search button */}
      <button
        onClick={toggleSearch}
        style={{
          position: 'absolute',
          top: theme.spacing.sm,
          right: theme.spacing.sm,
          backgroundColor: theme.colors.primary,
          color: 'white',
          border: 'none',
          borderRadius: '50%',
          width: '32px',
          height: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          zIndex: 2,
          boxShadow: theme.shadows.sm
        }}
        aria-label="Search messages"
        aria-expanded={isSearchOpen}
        aria-controls="search-container"
        title="Search messages (Ctrl+F)"
        tabIndex={0}
      >
        🔍
      </button>

      {/* Search input and results */}
      {isSearchOpen && (
        <div id="search-container" style={{ position: 'relative', zIndex: 10 }} role="search">
          <div style={inputContainerStyle}>
            <span style={searchIconStyle} aria-hidden="true">🔍</span>
            <input
              ref={inputRef}
              type="text"
              placeholder="Search in this conversation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              style={inputStyle}
              aria-label="Search messages"
              aria-describedby="search-instructions"
              aria-autocomplete="list"
              aria-controls="search-results"
            />
            <div id="search-instructions" style={{ display: 'none' }}>
              Type to search messages. Use Enter to navigate results, Shift+Enter for previous result, and Escape to close.
            </div>
            {searchQuery && (
              <button
                onClick={clearSearch}
                style={clearButtonStyle}
                aria-label="Clear search"
                tabIndex={0}
              >
                ✕
              </button>
            )}
          </div>

          {/* Search results */}
          {searchResults.length > 0 && (
            <div id="search-results" style={resultsContainerStyle} role="region" aria-label="Search results">
              {/* Navigation */}
              <div style={navigationStyle} role="status" aria-live="polite">
                <span>
                  {currentResultIndex + 1} of {searchResults.length} results
                </span>
                <div style={{ display: 'flex', gap: theme.spacing.xs }}>
                  <button
                    onClick={goToPrevResult}
                    style={navButtonStyle}
                    disabled={searchResults.length === 0}
                    aria-label="Previous search result"
                    tabIndex={0}
                  >
                    ↑ Prev
                  </button>
                  <button
                    onClick={goToNextResult}
                    style={navButtonStyle}
                    disabled={searchResults.length === 0}
                    aria-label="Next search result"
                    tabIndex={0}
                  >
                    Next ↓
                  </button>
                </div>
              </div>

              {/* Results list */}
              {searchResults.map((result, index) => {
                const { message, context } = result;
                const startIndex = Math.max(0, 50 - (result.startIndex - Math.max(0, result.startIndex - 50)));
                const endIndex = startIndex + searchQuery.length;
                
                // Highlight the matched text
                const beforeMatch = context.substring(0, startIndex);
                const matchText = context.substring(startIndex, endIndex);
                const afterMatch = context.substring(endIndex);
                
                return (
                  <div
                    key={`${message.id}-${index}`}
                    onClick={() => {
                      setCurrentResultIndex(index);
                      if (onHighlightMessage) {
                        onHighlightMessage(message.id);
                      }
                    }}
                    style={index === currentResultIndex ? highlightedResultStyle : resultItemStyle}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = theme.colors.background;
                    }}
                    onMouseLeave={(e) => {
                      if (index !== currentResultIndex) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}
                  >
                    <div style={resultTextStyle}>
                      {beforeMatch}
                      <span style={matchHighlightStyle}>{matchText}</span>
                      {afterMatch}
                    </div>
                    <div style={resultMetaStyle}>
                      {message.role === 'user' ? 'You' : 'Assistant'} • {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MessageSearchComponent;