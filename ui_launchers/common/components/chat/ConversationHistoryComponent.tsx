import React, { useState, useEffect } from 'react';

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

interface ConversationSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  summary?: string;
  tags?: string[];
}

interface ConversationHistoryProps {
  theme: Theme;
  conversations?: ConversationSession[];
  currentConversationId?: string | null;
  onSelectConversation?: (conversation: ConversationSession) => void;
  onDeleteConversation?: (conversationId: string) => void;
  onExportConversations?: (format: 'json' | 'text' | 'csv', conversationIds?: string[]) => string;
  onClearHistory?: () => void;
  className?: string;
}

interface ConversationHistoryState {
  conversations: ConversationSession[];
  currentConversationId: string | null;
  searchQuery: string;
  filteredConversations: ConversationSession[];
  isLoading: boolean;
  selectedConversations: string[];
}

// Default theme
const defaultTheme: Theme = {
  colors: {
    primary: '#3b82f6',
    secondary: '#64748b',
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#1e293b',
    textSecondary: '#64748b',
    border: '#e2e8f0',
    error: '#ef4444',
    warning: '#f59e0b',
    success: '#10b981',
    info: '#3b82f6'
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem'
  },
  typography: {
    fontFamily: 'Inter, system-ui, sans-serif',
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      xxl: '1.5rem'
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    }
  },
  borderRadius: '0.5rem',
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)'
  }
};

// Sample conversations for demonstration
const sampleConversations: ConversationSession[] = [
  {
    id: 'conv-1',
    title: 'Project Planning Discussion',
    messages: [
      {
        id: 'msg-1',
        role: 'user',
        content: 'Can you help me plan my new software project?',
        timestamp: new Date(Date.now() - 86400000), // 1 day ago
      },
      {
        id: 'msg-2',
        role: 'assistant',
        content: 'I\'d be happy to help you plan your software project. Let\'s start by discussing the project scope, requirements, and timeline.',
        timestamp: new Date(Date.now() - 86300000),
        aiData: {
          keywords: ['planning', 'software', 'project'],
          confidence: 0.95
        }
      }
    ],
    createdAt: new Date(Date.now() - 86400000),
    updatedAt: new Date(Date.now() - 86300000),
    messageCount: 2,
    summary: 'Discussion about planning a new software project',
    tags: ['planning', 'software']
  },
  {
    id: 'conv-2',
    title: 'Debugging Assistance',
    messages: [
      {
        id: 'msg-3',
        role: 'user',
        content: 'I\'m getting an error in my React component. Can you help me debug it?',
        timestamp: new Date(Date.now() - 172800000), // 2 days ago
      },
      {
        id: 'msg-4',
        role: 'assistant',
        content: 'Of course! Please share the error message and the relevant code, and I\'ll help you identify and fix the issue.',
        timestamp: new Date(Date.now() - 172700000),
        aiData: {
          keywords: ['debugging', 'react', 'error'],
          confidence: 0.98
        }
      }
    ],
    createdAt: new Date(Date.now() - 172800000),
    updatedAt: new Date(Date.now() - 172700000),
    messageCount: 2,
    summary: 'Help with debugging a React component error',
    tags: ['debugging', 'react']
  }
];

export const ConversationHistory: React.FC<ConversationHistoryProps> = ({
  theme = defaultTheme,
  conversations = sampleConversations,
  currentConversationId = null,
  onSelectConversation,
  onDeleteConversation,
  onExportConversations,
  onClearHistory,
  className = ''
}) => {
  const [state, setState] = useState<ConversationHistoryState>({
    conversations,
    currentConversationId,
    searchQuery: '',
    filteredConversations: conversations,
    isLoading: false,
    selectedConversations: []
  });

  const [exportFormat, setExportFormat] = useState<'json' | 'text' | 'csv'>('json');

  // Filter conversations based on search query
  useEffect(() => {
    let filtered = [...conversations];

    if (state.searchQuery.trim()) {
      const query = state.searchQuery.toLowerCase();
      filtered = filtered.filter(conv =>
        conv.title.toLowerCase().includes(query) ||
        conv.summary?.toLowerCase().includes(query) ||
        conv.messages.some(msg => 
          msg.content.toLowerCase().includes(query)
        ) ||
        conv.tags?.some(tag => 
          tag.toLowerCase().includes(query)
        )
      );
    }

    setState(prev => ({ ...prev, filteredConversations: filtered }));
  }, [conversations, state.searchQuery]);

  // Handle search
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setState(prev => ({ ...prev, searchQuery: e.target.value }));
  };

  // Handle conversation selection
  const handleSelectConversation = (conversation: ConversationSession) => {
    setState(prev => ({ ...prev, currentConversationId: conversation.id }));
    
    if (onSelectConversation) {
      onSelectConversation(conversation);
    }
  };

  // Handle conversation deletion
  const handleDeleteConversation = (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    const newConversations = state.conversations.filter(
      conv => conv.id !== conversationId
    );

    setState(prev => ({
      ...prev,
      conversations: newConversations,
      filteredConversations: newConversations.filter(conv =>
        state.searchQuery ? 
          conv.title.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
          conv.summary?.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
          conv.messages.some(msg => 
            msg.content.toLowerCase().includes(state.searchQuery.toLowerCase())
          ) ||
          conv.tags?.some(tag => 
            tag.toLowerCase().includes(state.searchQuery.toLowerCase())
          )
        : true
      ),
      currentConversationId: prev.currentConversationId === conversationId 
        ? null 
        : prev.currentConversationId
    }));

    if (onDeleteConversation) {
      onDeleteConversation(conversationId);
    }
  };

  // Handle conversation selection for export
  const handleSelectForExport = (conversationId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    
    const selected = e.target.checked;
    let newSelectedConversations: string[];
    
    if (selected) {
      newSelectedConversations = [...state.selectedConversations, conversationId];
    } else {
      newSelectedConversations = state.selectedConversations.filter(id => id !== conversationId);
    }
    
    setState(prev => ({ ...prev, selectedConversations: newSelectedConversations }));
  };

  // Handle export
  const handleExport = () => {
    if (onExportConversations) {
      const conversationsToExport = state.selectedConversations.length > 0
        ? state.conversations.filter(conv => state.selectedConversations.includes(conv.id))
        : state.filteredConversations;
      
      onExportConversations(exportFormat, conversationsToExport.map(conv => conv.id));
    }
  };

  // Handle clear history
  const handleClearHistory = () => {
    setState(prev => ({
      ...prev,
      conversations: [],
      filteredConversations: [],
      currentConversationId: null,
      selectedConversations: []
    }));

    if (onClearHistory) {
      onClearHistory();
    }
  };

  // Format date for display
  const formatDate = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    
    return date.toLocaleDateString();
  };

  // Group conversations by date
  const getGroupedConversations = (): Record<string, ConversationSession[]> => {
    const groups: Record<string, ConversationSession[]> = {};
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

    state.filteredConversations.forEach(conv => {
      const convDate = new Date(conv.updatedAt.getFullYear(), conv.updatedAt.getMonth(), conv.updatedAt.getDate());
      
      let groupKey: string;
      if (convDate.getTime() === today.getTime()) {
        groupKey = 'Today';
      } else if (convDate.getTime() === yesterday.getTime()) {
        groupKey = 'Yesterday';
      } else if (convDate >= weekAgo) {
        groupKey = 'This Week';
      } else {
        groupKey = convDate.toLocaleDateString('en-US', { 
          year: 'numeric', 
          month: 'long' 
        });
      }

      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(conv);
    });

    // Sort groups by date (most recent first)
    const sortedGroups: Record<string, ConversationSession[]> = {};
    const groupOrder = ['Today', 'Yesterday', 'This Week'];
    
    groupOrder.forEach(key => {
      if (groups[key]) {
        sortedGroups[key] = groups[key];
      }
    });

    // Add remaining groups sorted by date
    Object.keys(groups)
      .filter(key => !groupOrder.includes(key))
      .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())
      .forEach(key => {
        sortedGroups[key] = groups[key];
      });

    return sortedGroups;
  };

  const groupedConversations = getGroupedConversations();

  return (
    <div 
      className={`karen-conversation-history ${className}`}
      style={{
        backgroundColor: theme.colors.background,
        color: theme.colors.text,
        fontFamily: theme.typography.fontFamily,
        borderRadius: theme.borderRadius,
        border: `1px solid ${theme.colors.border}`,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        height: '100%'
      }}
    >
      {/* Header */}
      <div 
        className="karen-history-header"
        style={{
          padding: theme.spacing.md,
          borderBottom: `1px solid ${theme.colors.border}`,
          backgroundColor: theme.colors.surface
        }}
      >
        <h2 
          className="karen-history-title"
          style={{
            margin: 0,
            fontSize: theme.typography.fontSize.lg,
            fontWeight: theme.typography.fontWeight.bold,
            marginBottom: theme.spacing.md
          }}
        >
          Conversation History
        </h2>
        
        {/* Search */}
        <div 
          className="karen-history-search"
          style={{
            position: 'relative',
            marginBottom: theme.spacing.md
          }}
        >
          <input
            type="text"
            value={state.searchQuery}
            onChange={handleSearch}
            placeholder="Search conversations..."
            className="karen-search-input"
            style={{
              width: '100%',
              padding: `${theme.spacing.sm} ${theme.spacing.sm} ${theme.spacing.sm} ${theme.spacing.lg}`,
              backgroundColor: theme.colors.background,
              color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              fontSize: theme.typography.fontSize.base,
              outline: 'none',
              transition: 'border-color 0.2s ease',
              boxSizing: 'border-box'
            }}
          />
          <span 
            className="karen-search-icon"
            style={{
              position: 'absolute',
              left: theme.spacing.sm,
              top: '50%',
              transform: 'translateY(-50%)',
              color: theme.colors.textSecondary
            }}
          >
            🔍
          </span>
        </div>
        
        {/* Actions */}
        <div 
          className="karen-history-actions"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div 
            className="karen-export-controls"
            style={{
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as 'json' | 'text' | 'csv')}
              className="karen-export-format"
              style={{
                marginRight: theme.spacing.sm,
                padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                backgroundColor: theme.colors.background,
                color: theme.colors.text,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius,
                fontSize: theme.typography.fontSize.sm
              }}
            >
              <option value="json">JSON</option>
              <option value="text">Text</option>
              <option value="csv">CSV</option>
            </select>
            <button
              onClick={handleExport}
              disabled={state.filteredConversations.length === 0}
              className="karen-export-button"
              style={{
                backgroundColor: theme.colors.primary,
                color: 'white',
                border: 'none',
                borderRadius: theme.borderRadius,
                padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                cursor: state.filteredConversations.length === 0 ? 'not-allowed' : 'pointer',
                opacity: state.filteredConversations.length === 0 ? 0.5 : 1,
                fontSize: theme.typography.fontSize.sm
              }}
            >
              Export
            </button>
          </div>
          
          <button
            onClick={handleClearHistory}
            disabled={state.conversations.length === 0}
            className="karen-clear-button"
            style={{
              backgroundColor: theme.colors.error,
              color: 'white',
              border: 'none',
              borderRadius: theme.borderRadius,
              padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
              cursor: state.conversations.length === 0 ? 'not-allowed' : 'pointer',
              opacity: state.conversations.length === 0 ? 0.5 : 1,
              fontSize: theme.typography.fontSize.sm
            }}
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Conversations List */}
      <div 
        className="karen-conversations-list"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: theme.spacing.md
        }}
      >
        {state.filteredConversations.length === 0 ? (
          <div 
            className="karen-empty-state"
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: theme.colors.textSecondary,
              padding: theme.spacing.lg
            }}
          >
            <p style={{ marginBottom: theme.spacing.md, textAlign: 'center' }}>
              {state.searchQuery 
                ? 'No conversations match your search.'
                : 'No conversations yet. Start a new conversation!'}
            </p>
          </div>
        ) : (
          Object.entries(groupedConversations).map(([groupName, conversations]) => (
            <div key={groupName} style={{ marginBottom: theme.spacing.lg }}>
              <h3 
                className="karen-group-title"
                style={{
                  margin: `0 0 ${theme.spacing.md} 0`,
                  fontSize: theme.typography.fontSize.md,
                  fontWeight: theme.typography.fontWeight.semibold,
                  color: theme.colors.textSecondary,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}
              >
                {groupName}
              </h3>
              
              {conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  onClick={() => handleSelectConversation(conversation)}
                  className={`karen-conversation-item ${state.currentConversationId === conversation.id ? 'active' : ''}`}
                  style={{
                    backgroundColor: state.currentConversationId === conversation.id 
                      ? `${theme.colors.primary}10` 
                      : theme.colors.surface,
                    border: `1px solid ${theme.colors.border}`,
                    borderRadius: theme.borderRadius,
                    padding: theme.spacing.md,
                    marginBottom: theme.spacing.sm,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    boxShadow: theme.shadows.sm
                  }}
                >
                  <div 
                    className="karen-conversation-header"
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: theme.spacing.sm
                    }}
                  >
                    <div 
                      className="karen-conversation-title-container"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        flex: 1
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={state.selectedConversations.includes(conversation.id)}
                        onChange={(e) => handleSelectForExport(conversation.id, e)}
                        onClick={(e) => e.stopPropagation()}
                        className="karen-conversation-checkbox"
                        style={{
                          marginRight: theme.spacing.sm,
                          cursor: 'pointer'
                        }}
                      />
                      <h4 
                        className="karen-conversation-title"
                        style={{
                          margin: 0,
                          fontSize: theme.typography.fontSize.base,
                          fontWeight: theme.typography.fontWeight.medium,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                        title={conversation.title}
                      >
                        {conversation.title}
                      </h4>
                    </div>
                    
                    <div 
                      className="karen-conversation-actions"
                      style={{
                        display: 'flex',
                        alignItems: 'center'
                      }}
                    >
                      <span 
                        className="karen-conversation-date"
                        style={{
                          fontSize: theme.typography.fontSize.xs,
                          color: theme.colors.textSecondary,
                          marginRight: theme.spacing.sm
                        }}
                      >
                        {formatDate(conversation.updatedAt)}
                      </span>
                      <button
                        onClick={(e) => handleDeleteConversation(conversation.id, e)}
                        className="karen-delete-button"
                        aria-label="Delete conversation"
                        style={{
                          backgroundColor: 'transparent',
                          color: theme.colors.error,
                          border: 'none',
                          borderRadius: theme.borderRadius,
                          padding: theme.spacing.xs,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                  
                  <div 
                    className="karen-conversation-meta"
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontSize: theme.typography.fontSize.xs,
                      color: theme.colors.textSecondary,
                      marginBottom: conversation.summary ? theme.spacing.sm : 0
                    }}
                  >
                    <span>{conversation.messageCount} messages</span>
                    {conversation.tags && conversation.tags.length > 0 && (
                      <div 
                        className="karen-conversation-tags"
                        style={{
                          display: 'flex',
                          gap: theme.spacing.xs
                        }}
                      >
                        {conversation.tags.slice(0, 3).map((tag, index) => (
                          <span 
                            key={index}
                            className="karen-conversation-tag"
                            style={{
                              backgroundColor: `${theme.colors.primary}20`,
                              color: theme.colors.primary,
                              padding: `2px ${theme.spacing.xs}`,
                              borderRadius: '4px',
                              fontSize: '10px'
                            }}
                          >
                            {tag}
                          </span>
                        ))}
                        {conversation.tags.length > 3 && (
                          <span 
                            className="karen-more-tags"
                            style={{
                              color: theme.colors.textSecondary
                            }}
                          >
                            +{conversation.tags.length - 3}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {conversation.summary && (
                    <p 
                      className="karen-conversation-summary"
                      style={{
                        margin: 0,
                        fontSize: theme.typography.fontSize.sm,
                        color: theme.colors.textSecondary,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                      title={conversation.summary}
                    >
                      {conversation.summary}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ConversationHistory;