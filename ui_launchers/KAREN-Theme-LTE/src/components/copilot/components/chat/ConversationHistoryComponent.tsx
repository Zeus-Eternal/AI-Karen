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

interface Conversation {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: ChatMessage[];
  summary?: string;
  tags?: string[];
  agent?: string;
}

interface ConversationHistoryProps {
  theme: Theme;
  className?: string;
  conversations?: Conversation[];
  selectedConversationId?: string;
  onSelectConversation?: (conversation: Conversation) => void;
  onDeleteConversation?: (conversationId: string) => void;
  onRenameConversation?: (conversationId: string, newTitle: string) => void;
  onExportConversation?: (conversation: Conversation) => void;
  onCreateNewConversation?: () => void;
  onSearchConversations?: (query: string) => void;
  onFilterByTag?: (tag: string) => void;
  onFilterByDate?: (startDate: Date, endDate: Date) => void;
  onClearFilters?: () => void;
  isLoading?: boolean;
  showSearch?: boolean;
  showFilters?: boolean;
  showTags?: boolean;
  showDates?: boolean;
  showActions?: boolean;
  showPreview?: boolean;
  maxPreviewLength?: number;
  sortConversationsBy?: 'date' | 'title' | 'messageCount';
  sortDirection?: 'asc' | 'desc';
}

// Format date for display
const formatDate = (date: Date): string => {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  
  if (date.toDateString() === today.toDateString()) {
    return 'Today';
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Yesterday';
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }
};

// Format time for display
const formatTime = (date: Date): string => {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// Truncate text with ellipsis
const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

// Get conversation preview
const getConversationPreview = (conversation: Conversation, maxLength: number): string => {
  if (conversation.summary) {
    return truncateText(conversation.summary, maxLength);
  }
  
  // Find first user message for preview
  const userMessage = conversation.messages.find(msg => msg.role === 'user');
  if (userMessage) {
    return truncateText(userMessage.content, maxLength);
  }
  
  // Find first non-system message if no user message
  const firstMessage = conversation.messages.find(msg => msg.role !== 'system');
  if (firstMessage) {
    return truncateText(firstMessage.content, maxLength);
  }
  
  return 'No messages';
};

// Get message count for conversation
const getMessageCount = (conversation: Conversation): number => {
  return conversation.messages.length;
};

// Render tag
const renderTag = (tag: string, theme: Theme, onClick?: () => void): React.ReactNode => {
  return (
    <span
      key={tag}
      className="copilot-conversation-tag"
      onClick={onClick}
      style={{
        backgroundColor: `${theme.colors.primary}20`,
        color: theme.colors.primary,
        padding: `2px ${theme.spacing.xs}`,
        borderRadius: '4px',
        fontSize: '10px',
        cursor: onClick ? 'pointer' : 'default',
        display: 'inline-block',
        marginRight: theme.spacing.xs,
        marginBottom: theme.spacing.xs
      }}
      title={tag}
    >
      {tag}
    </span>
  );
};

// Get tag style object
const getTagStyle = (tag: string, theme: Theme, selectedTag: string | null): React.CSSProperties => {
  return {
    backgroundColor: selectedTag === tag
      ? theme.colors.primary
      : `${theme.colors.primary}20`,
    color: selectedTag === tag
      ? '#fff'
      : theme.colors.primary,
    cursor: 'pointer'
  };
};

// Render conversation actions
const renderConversationActions = (
  conversation: Conversation,
  theme: Theme,
  onSelect?: (conversation: Conversation) => void,
  onDelete?: (conversationId: string) => void,
  onRename?: (conversationId: string, newTitle: string) => void,
  onExport?: (conversation: Conversation) => void
): React.ReactNode => {
  const [isRenaming, setIsRenaming] = useState(false);
  const [newTitle, setNewTitle] = useState(conversation.title);
  const [showMenu, setShowMenu] = useState(false);
  
  const handleRename = () => {
    if (onRename && newTitle.trim() !== '') {
      onRename(conversation.id, newTitle.trim());
      setIsRenaming(false);
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRename();
    } else if (e.key === 'Escape') {
      setIsRenaming(false);
      setNewTitle(conversation.title);
    }
  };
  
  return (
    <div
      className="copilot-conversation-actions"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: theme.spacing.xs
      }}
    >
      {isRenaming ? (
        <div
          className="copilot-rename-form"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: theme.spacing.xs,
            flex: 1
          }}
        >
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
            className="copilot-rename-input"
            style={{
              backgroundColor: theme.colors.background,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
              color: theme.colors.text,
              fontSize: theme.typography.fontSize.sm,
              fontFamily: theme.typography.fontFamily,
              flex: 1,
              outline: 'none'
            }}
          />
          <button
            onClick={handleRename}
            className="copilot-confirm-rename"
            aria-label="Confirm rename"
            style={{
              backgroundColor: 'transparent',
              color: theme.colors.success,
              border: 'none',
              borderRadius: theme.borderRadius,
              width: '28px',
              height: '28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            ✓
          </button>
          <button
            onClick={() => {
              setIsRenaming(false);
              setNewTitle(conversation.title);
            }}
            className="copilot-cancel-rename"
            aria-label="Cancel rename"
            style={{
              backgroundColor: 'transparent',
              color: theme.colors.error,
              border: 'none',
              borderRadius: theme.borderRadius,
              width: '28px',
              height: '28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            ✕
          </button>
        </div>
      ) : (
        <>
          <div
            className="copilot-conversation-title"
            style={{
              fontWeight: theme.typography.fontWeight.medium,
              color: theme.colors.text,
              flex: 1,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
            title={conversation.title}
          >
            {conversation.title}
          </div>
          
          <div
            className="copilot-actions-menu"
            style={{ position: 'relative' }}
          >
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="copilot-menu-toggle"
              aria-label="Conversation options"
              style={{
                backgroundColor: 'transparent',
                color: theme.colors.textSecondary,
                border: 'none',
                borderRadius: '50%',
                width: '28px',
                height: '28px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              ⋮
            </button>
            
            {showMenu && (
              <div
                className="copilot-actions-dropdown"
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: '0',
                  backgroundColor: theme.colors.surface,
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: theme.borderRadius,
                  boxShadow: theme.shadows.lg,
                  zIndex: 100,
                  minWidth: '150px',
                  marginTop: theme.spacing.xs
                }}
              >
                <button
                  onClick={() => {
                    onSelect && onSelect(conversation);
                    setShowMenu(false);
                  }}
                  className="copilot-action-select"
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    backgroundColor: 'transparent',
                    color: theme.colors.text,
                    border: 'none',
                    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                    fontSize: theme.typography.fontSize.sm,
                    cursor: 'pointer',
                    transition: 'background-color 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = theme.colors.background;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  Open
                </button>
                
                <button
                  onClick={() => {
                    setIsRenaming(true);
                    setShowMenu(false);
                  }}
                  className="copilot-action-rename"
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    backgroundColor: 'transparent',
                    color: theme.colors.text,
                    border: 'none',
                    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                    fontSize: theme.typography.fontSize.sm,
                    cursor: 'pointer',
                    transition: 'background-color 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = theme.colors.background;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  Rename
                </button>
                
                {onExport && (
                  <button
                    onClick={() => {
                      onExport(conversation);
                      setShowMenu(false);
                    }}
                    className="copilot-action-export"
                    style={{
                      width: '100%',
                      textAlign: 'left',
                      backgroundColor: 'transparent',
                      color: theme.colors.text,
                      border: 'none',
                      padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                      fontSize: theme.typography.fontSize.sm,
                      cursor: 'pointer',
                      transition: 'background-color 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = theme.colors.background;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    Export
                  </button>
                )}
                
                <button
                  onClick={() => {
                    if (onDelete && window.confirm('Are you sure you want to delete this conversation?')) {
                      onDelete(conversation.id);
                    }
                    setShowMenu(false);
                  }}
                  className="copilot-action-delete"
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    backgroundColor: 'transparent',
                    color: theme.colors.error,
                    border: 'none',
                    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                    fontSize: theme.typography.fontSize.sm,
                    cursor: 'pointer',
                    transition: 'background-color 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = theme.colors.error + '10';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  Delete
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export const ConversationHistoryComponent: React.FC<ConversationHistoryProps> = ({
  theme,
  className = '',
  conversations = [],
  selectedConversationId,
  onSelectConversation,
  onDeleteConversation,
  onRenameConversation,
  onExportConversation,
  onCreateNewConversation,
  onSearchConversations,
  onFilterByTag,
  onFilterByDate,
  onClearFilters,
  isLoading = false,
  showSearch = true,
  showFilters = true,
  showTags = true,
  showDates = true,
  showActions = true,
  showPreview = true,
  maxPreviewLength = 100,
  sortConversationsBy = 'date',
  sortDirection = 'desc'
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [dateFilter, setDateFilter] = useState<{ start: Date | null; end: Date | null }>({ start: null, end: null });
  const [filteredConversations, setFilteredConversations] = useState<Conversation[]>(conversations);
  const [allTags, setAllTags] = useState<string[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Extract all unique tags from conversations
  useEffect(() => {
    const tags = new Set<string>();
    conversations.forEach(conversation => {
      if (conversation.tags) {
        conversation.tags.forEach(tag => tags.add(tag));
      }
    });
    setAllTags(Array.from(tags));
  }, [conversations]);
  
  // Filter and sort conversations
  useEffect(() => {
    let result = [...conversations];
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(conversation => 
        conversation.title.toLowerCase().includes(query) ||
        conversation.messages.some(message => 
          message.content.toLowerCase().includes(query)
        ) ||
        (conversation.summary && conversation.summary.toLowerCase().includes(query))
      );
    }
    
    // Apply tag filter
    if (selectedTag) {
      result = result.filter(conversation => 
        conversation.tags && conversation.tags.includes(selectedTag)
      );
    }
    
    // Apply date filter
    if (dateFilter.start && dateFilter.end) {
      result = result.filter(conversation => {
        const convDate = new Date(conversation.updatedAt);
        return convDate >= dateFilter.start! && convDate <= dateFilter.end!;
      });
    }
    
    // Sort conversations
    result.sort((a, b) => {
      let comparison = 0;
      
      switch (sortConversationsBy) {
        case 'date':
          comparison = new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
          break;
        case 'title':
          comparison = a.title.localeCompare(b.title);
          break;
        case 'messageCount':
          comparison = b.messages.length - a.messages.length;
          break;
      }
      
      return sortDirection === 'asc' ? comparison * -1 : comparison;
    });
    
    setFilteredConversations(result);
  }, [conversations, searchQuery, selectedTag, dateFilter, sortConversationsBy, sortDirection]);
  
  // Handle search input
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    if (onSearchConversations) {
      onSearchConversations(query);
    }
  };
  
  // Handle tag selection
  const handleTagSelect = (tag: string) => {
    const newSelectedTag = selectedTag === tag ? null : tag;
    setSelectedTag(newSelectedTag);
    
    if (onFilterByTag && newSelectedTag) {
      onFilterByTag(newSelectedTag);
    } else if (onClearFilters && !newSelectedTag) {
      onClearFilters();
    }
  };
  
  // Handle date filter
  const handleDateFilterChange = (start: Date | null, end: Date | null) => {
    setDateFilter({ start, end });
    
    if (onFilterByDate && start && end) {
      onFilterByDate(start, end);
    } else if (onClearFilters && !start && !end) {
      onClearFilters();
    }
  };
  
  // Clear all filters
  const handleClearFilters = () => {
    setSearchQuery('');
    setSelectedTag(null);
    setDateFilter({ start: null, end: null });
    
    if (onClearFilters) {
      onClearFilters();
    }
  };
  
  // Handle conversation selection
  const handleSelectConversation = (conversation: Conversation) => {
    if (onSelectConversation) {
      onSelectConversation(conversation);
    }
  };
  
  // Handle conversation deletion
  const handleDeleteConversation = (conversationId: string) => {
    if (onDeleteConversation) {
      onDeleteConversation(conversationId);
    }
  };
  
  // Handle conversation renaming
  const handleRenameConversation = (conversationId: string, newTitle: string) => {
    if (onRenameConversation) {
      onRenameConversation(conversationId, newTitle);
    }
  };
  
  // Handle conversation export
  const handleExportConversation = (conversation: Conversation) => {
    if (onExportConversation) {
      onExportConversation(conversation);
    }
  };
  
  // Handle new conversation creation
  const handleCreateNewConversation = () => {
    if (onCreateNewConversation) {
      onCreateNewConversation();
    }
  };
  
  // Check if any filters are active
  const hasActiveFilters = searchQuery || selectedTag || (dateFilter.start && dateFilter.end);
  
  const containerStyle: React.CSSProperties = {
    width: '100%',
    backgroundColor: theme.colors.surface,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    boxShadow: theme.shadows.sm,
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    height: '100%'
  };
  
  const headerStyle: React.CSSProperties = {
    padding: theme.spacing.md,
    borderBottom: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.background
  };
  
  const searchContainerStyle: React.CSSProperties = {
    position: 'relative',
    marginBottom: showFilters ? theme.spacing.md : 0
  };
  
  const searchInputStyle: React.CSSProperties = {
    width: '100%',
    backgroundColor: theme.colors.background,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    padding: `${theme.spacing.sm} ${theme.spacing.sm} ${theme.spacing.sm} ${theme.spacing.lg}`,
    color: theme.colors.text,
    fontSize: theme.typography.fontSize.sm,
    fontFamily: theme.typography.fontFamily,
    outline: 'none',
    transition: 'border-color 0.2s ease'
  };
  
  const searchIconStyle: React.CSSProperties = {
    position: 'absolute',
    left: theme.spacing.sm,
    top: '50%',
    transform: 'translateY(-50%)',
    color: theme.colors.textSecondary
  };
  
  const clearButtonStyle: React.CSSProperties = {
    position: 'absolute',
    right: theme.spacing.sm,
    top: '50%',
    transform: 'translateY(-50%)',
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
    padding: 0
  };
  
  const filtersStyle: React.CSSProperties = {
    display: 'flex',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.md
  };
  
  const tagFiltersStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing.xs,
    marginBottom: theme.spacing.sm
  };
  
  const listStyle: React.CSSProperties = {
    flex: 1,
    overflowY: 'auto',
    padding: theme.spacing.sm
  };
  
  const conversationItemStyle: React.CSSProperties = {
    padding: theme.spacing.sm,
    borderRadius: theme.borderRadius,
    marginBottom: theme.spacing.xs,
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
    border: `1px solid transparent`
  };
  
  const selectedConversationStyle: React.CSSProperties = {
    ...conversationItemStyle,
    backgroundColor: `${theme.colors.primary}10`,
    borderColor: theme.colors.primary
  };
  
  const emptyStateStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.xl,
    color: theme.colors.textSecondary,
    textAlign: 'center'
  };
  
  const newConversationButtonStyle: React.CSSProperties = {
    width: '100%',
    backgroundColor: theme.colors.primary,
    color: '#fff',
    border: 'none',
    borderRadius: theme.borderRadius,
    padding: theme.spacing.sm,
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.medium,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.xs,
    transition: 'background-color 0.2s ease'
  };
  
  return (
    <div
      ref={containerRef}
      className={`copilot-conversation-history ${className}`}
      style={containerStyle}
      role="region"
      aria-label="Conversation history"
    >
      {/* Header */}
      <div
        className="copilot-history-header"
        style={headerStyle}
        role="banner"
      >
        <h2
          className="copilot-history-title"
          id="conversation-history-title"
          style={{
            fontSize: theme.typography.fontSize.lg,
            fontWeight: theme.typography.fontWeight.semibold,
            color: theme.colors.text,
            margin: 0,
            marginBottom: theme.spacing.md
          }}
        >
          Conversation History
        </h2>
        
        {/* Search input */}
        {showSearch && (
          <div
            className="copilot-search-container"
            style={searchContainerStyle}
            role="search"
          >
            <span
              className="copilot-search-icon"
              style={searchIconStyle}
              aria-hidden="true"
            >
              🔍
            </span>
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="copilot-search-input"
              style={searchInputStyle}
              aria-label="Search conversations"
              aria-describedby="search-help"
            />
            <div id="search-help" style={{ display: 'none' }}>
              Search conversations by title, content, or tags
            </div>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="copilot-clear-search"
                aria-label="Clear search"
                style={clearButtonStyle}
                tabIndex={0}
              >
                ✕
              </button>
            )}
          </div>
        )}
        
        {/* Filters */}
        {showFilters && (
          <div
            className="copilot-filters"
            style={filtersStyle}
            role="group"
            aria-label="Filters"
          >
            {/* Tag filters */}
            {showTags && allTags.length > 0 && (
              <div
                className="copilot-tag-filters"
                style={tagFiltersStyle}
                role="group"
                aria-label="Filter by tags"
              >
                {allTags.map(tag => (
                  <span
                    key={tag}
                    onClick={() => handleTagSelect(tag)}
                    style={getTagStyle(tag, theme, selectedTag)}
                    role="button"
                    tabIndex={0}
                    aria-pressed={selectedTag === tag}
                    aria-label={`Filter by tag: ${tag}`}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleTagSelect(tag);
                      }
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
            
            {/* Clear filters button */}
            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="copilot-clear-filters"
                style={{
                  backgroundColor: 'transparent',
                  color: theme.colors.textSecondary,
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: theme.borderRadius,
                  padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                  fontSize: theme.typography.fontSize.xs,
                  cursor: 'pointer',
                  marginLeft: 'auto'
                }}
                tabIndex={0}
              >
                Clear Filters
              </button>
            )}
          </div>
        )}
      </div>
      
      {/* Conversation list */}
      <div
        className="copilot-conversation-list"
        style={listStyle}
        role="list"
        aria-labelledby="conversation-history-title"
      >
        {isLoading ? (
          <div
            className="copilot-loading-state"
            style={emptyStateStyle}
            role="status"
            aria-live="polite"
            aria-busy="true"
          >
            <div
              className="copilot-loading-spinner"
              style={{
                width: '40px',
                height: '40px',
                border: `3px solid ${theme.colors.border}`,
                borderTop: `3px solid ${theme.colors.primary}`,
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                marginBottom: theme.spacing.md
              }}
            />
            <p>Loading conversations...</p>
          </div>
        ) : filteredConversations.length === 0 ? (
          <div
            className="copilot-empty-state"
            style={emptyStateStyle}
            role="status"
            aria-live="polite"
          >
            <p
              className="copilot-empty-text"
              style={{
                fontSize: theme.typography.fontSize.base,
                marginBottom: theme.spacing.md
              }}
            >
              {hasActiveFilters
                ? 'No conversations match your filters.'
                : 'No conversations yet.'}
            </p>
            {!hasActiveFilters && (
              <button
                onClick={handleCreateNewConversation}
                className="copilot-new-conversation"
                style={newConversationButtonStyle}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = theme.colors.secondary;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = theme.colors.primary;
                }}
                tabIndex={0}
              >
                <span>+</span>
                <span>New Conversation</span>
              </button>
            )}
          </div>
        ) : (
          <div
            className="copilot-conversations"
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: theme.spacing.xs
            }}
            role="list"
          >
            {filteredConversations.map(conversation => (
              <div
                key={conversation.id}
                onClick={() => handleSelectConversation(conversation)}
                className={`copilot-conversation-item ${selectedConversationId === conversation.id ? 'selected' : ''}`}
                style={
                  selectedConversationId === conversation.id
                    ? selectedConversationStyle
                    : conversationItemStyle
                }
                role="listitem"
                aria-selected={selectedConversationId === conversation.id}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleSelectConversation(conversation);
                  }
                }}
              >
                {/* Conversation header */}
                <div
                  className="copilot-conversation-header"
                  style={{
                    marginBottom: theme.spacing.xs
                  }}
                >
                  {showActions ? (
                    renderConversationActions(
                      conversation,
                      theme,
                      handleSelectConversation,
                      handleDeleteConversation,
                      handleRenameConversation,
                      handleExportConversation
                    )
                  ) : (
                    <div
                      className="copilot-conversation-title"
                      style={{
                        fontWeight: theme.typography.fontWeight.medium,
                        color: theme.colors.text,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}
                      title={conversation.title}
                    >
                      {conversation.title}
                    </div>
                  )}
                </div>
                
                {/* Conversation metadata */}
                <div
                  className="copilot-conversation-meta"
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: showPreview ? theme.spacing.xs : 0
                  }}
                >
                  <div
                    className="copilot-conversation-info"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: theme.spacing.sm,
                      fontSize: theme.typography.fontSize.xs,
                      color: theme.colors.textSecondary
                    }}
                  >
                    {showDates && (
                      <span
                        className="copilot-conversation-date"
                        title={formatDate(conversation.updatedAt)}
                      >
                        {formatDate(conversation.updatedAt)}
                      </span>
                    )}
                    
                    <span
                      className="copilot-conversation-time"
                      title={formatTime(conversation.updatedAt)}
                    >
                      {formatTime(conversation.updatedAt)}
                    </span>
                    
                    <span
                      className="copilot-message-count"
                      title={`${getMessageCount(conversation)} messages`}
                    >
                      {getMessageCount(conversation)} messages
                    </span>
                    
                    {conversation.agent && (
                      <span
                        className="copilot-conversation-agent"
                        title={`Agent: ${conversation.agent}`}
                      >
                        🤖 {conversation.agent}
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Conversation preview */}
                {showPreview && (
                  <div
                    className="copilot-conversation-preview"
                    style={{
                      fontSize: theme.typography.fontSize.sm,
                      color: theme.colors.textSecondary,
                      whiteSpace: 'pre-wrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}
                  >
                    {getConversationPreview(conversation, maxPreviewLength)}
                  </div>
                )}
                
                {/* Conversation tags */}
                {showTags && conversation.tags && conversation.tags.length > 0 && (
                  <div
                    className="copilot-conversation-tags"
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: theme.spacing.xs,
                      marginTop: theme.spacing.xs
                    }}
                  >
                    {conversation.tags.map(tag => 
                      renderTag(tag, theme, () => handleTagSelect(tag))
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      <style jsx>{`
        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
};

export default ConversationHistoryComponent;