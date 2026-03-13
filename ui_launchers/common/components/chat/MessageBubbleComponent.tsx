import React, { useState, useRef, useEffect } from 'react';

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

interface MessageBubbleProps {
  message: ChatMessage;
  theme: Theme;
  isLast?: boolean;
  className?: string;
  onMessageAction?: (action: string, messageId: string) => void;
  onCopyMessage?: (messageId: string) => void;
  onRetryMessage?: (messageId: string) => void;
  onDeleteMessage?: (messageId: string) => void;
  showTimestamp?: boolean;
  showActions?: boolean;
  showAiData?: boolean;
  showConfidence?: boolean;
  showKeywords?: boolean;
  showReasoning?: boolean;
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

// Format timestamp for display
const formatTimestamp = (timestamp: Date): string => {
  return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// Format file size
const formatFileSize = (size: string): string => {
  if (size === '') return '';
  
  const sizeNum = parseInt(size);
  if (isNaN(sizeNum)) return size;
  
  if (sizeNum < 1024) {
    return `${sizeNum} B`;
  } else if (sizeNum < 1024 * 1024) {
    return `${(sizeNum / 1024).toFixed(1)} KB`;
  } else {
    return `${(sizeNum / (1024 * 1024)).toFixed(1)} MB`;
  }
};

// Render confidence indicator
const renderConfidence = (confidence?: number, theme: Theme): React.ReactNode => {
  if (confidence === undefined) return null;
  
  const confidenceColor = confidence > 0.8 
    ? theme.colors.success 
    : confidence > 0.6 
      ? theme.colors.warning 
      : theme.colors.error;
  
  return (
    <div 
      className="karen-confidence-indicator"
      style={{
        display: 'flex',
        alignItems: 'center',
        marginTop: theme.spacing.sm
      }}
    >
      <span 
        className="karen-confidence-label"
        style={{
          fontSize: theme.typography.fontSize.xs,
          color: theme.colors.textSecondary,
          marginRight: theme.spacing.xs
        }}
      >
        Confidence:
      </span>
      <div 
        className="karen-confidence-bar"
        style={{
          width: '80px',
          height: '6px',
          backgroundColor: theme.colors.border,
          borderRadius: '3px',
          overflow: 'hidden',
          marginRight: theme.spacing.xs
        }}
      >
        <div 
          className="karen-confidence-fill"
          style={{
            width: `${confidence * 100}%`,
            height: '100%',
            backgroundColor: confidenceColor
          }}
        />
      </div>
      <span 
        className="karen-confidence-value"
        style={{
          fontSize: theme.typography.fontSize.xs,
          color: confidenceColor,
          fontWeight: theme.typography.fontWeight.medium
        }}
      >
        {Math.round(confidence * 100)}%
      </span>
    </div>
  );
};

// Render keywords
const renderKeywords = (keywords?: string[], theme: Theme): React.ReactNode => {
  if (!keywords || keywords.length === 0) return null;
  
  return (
    <div 
      className="karen-keywords"
      style={{
        marginTop: theme.spacing.sm
      }}
    >
      <span 
        className="karen-keywords-label"
        style={{
          fontSize: theme.typography.fontSize.xs,
          color: theme.colors.textSecondary,
          marginRight: theme.spacing.xs
        }}
      >
        Keywords:
      </span>
      <div 
        className="karen-keywords-container"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: theme.spacing.xs
        }}
      >
        {keywords.slice(0, 5).map((keyword, index) => (
          <span 
            key={index}
            className="karen-keyword"
            style={{
              backgroundColor: `${theme.colors.primary}20`,
              color: theme.colors.primary,
              padding: `2px ${theme.spacing.xs}`,
              borderRadius: '4px',
              fontSize: '10px'
            }}
          >
            {keyword}
          </span>
        ))}
        {keywords.length > 5 && (
          <span 
            className="karen-more-keywords"
            style={{
              color: theme.colors.textSecondary,
              fontSize: '10px'
            }}
          >
            +{keywords.length - 5}
          </span>
        )}
      </div>
    </div>
  );
};

// Render reasoning
const renderReasoning = (reasoning?: string, theme: Theme): React.ReactNode => {
  if (!reasoning) return null;
  
  return (
    <details 
      className="karen-reasoning"
      style={{
        marginTop: theme.spacing.sm
      }}
    >
      <summary 
        className="karen-reasoning-toggle"
        style={{
          fontSize: theme.typography.fontSize.sm,
          fontWeight: theme.typography.fontWeight.medium,
          color: theme.colors.primary,
          cursor: 'pointer',
          marginBottom: theme.spacing.xs
        }}
      >
        View Reasoning
      </summary>
      <div 
        className="karen-reasoning-content"
        style={{
          fontSize: theme.typography.fontSize.xs,
          color: theme.colors.textSecondary,
          padding: theme.spacing.sm,
          backgroundColor: theme.colors.surface,
          borderRadius: theme.borderRadius,
          borderLeft: `3px solid ${theme.colors.primary}`,
          whiteSpace: 'pre-wrap'
        }}
      >
        {reasoning}
      </div>
    </details>
  );
};

// Render attachments
const renderAttachments = (attachments?: Array<{
  id: string;
  name: string;
  size: string;
  type: string;
  url?: string;
}>, theme: Theme): React.ReactNode => {
  if (!attachments || attachments.length === 0) return null;
  
  const getFileIcon = (type: string): string => {
    if (type.startsWith('image/')) return '🖼️';
    if (type.includes('pdf')) return '📄';
    if (type.includes('word') || type.includes('document')) return '📝';
    if (type.includes('sheet') || type.includes('excel')) return '📊';
    if (type.includes('presentation') || type.includes('powerpoint')) return '📽️';
    if (type.includes('zip') || type.includes('rar') || type.includes('tar')) return '📦';
    if (type.includes('video')) return '🎬';
    if (type.includes('audio')) return '🎵';
    return '📎';
  };
  
  return (
    <div 
      className="karen-attachments"
      style={{
        marginTop: theme.spacing.sm
      }}
    >
      <span 
        className="karen-attachments-label"
        style={{
          fontSize: theme.typography.fontSize.xs,
          color: theme.colors.textSecondary,
          display: 'block',
          marginBottom: theme.spacing.xs
        }}
      >
        Attachments:
      </span>
      <div 
        className="karen-attachments-container"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: theme.spacing.sm
        }}
      >
        {attachments.map((attachment) => (
          <a
            key={attachment.id}
            href={attachment.url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="karen-attachment"
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
              backgroundColor: theme.colors.surface,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              textDecoration: 'none',
              color: theme.colors.text,
              fontSize: theme.typography.fontSize.sm,
              transition: 'all 0.2s ease',
              maxWidth: '200px'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.colors.primary + '10';
              e.currentTarget.style.borderColor = theme.colors.primary;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.colors.surface;
              e.currentTarget.style.borderColor = theme.colors.border;
            }}
          >
            <span 
              className="karen-attachment-icon"
              style={{
                marginRight: theme.spacing.xs,
                fontSize: '1rem'
              }}
            >
              {getFileIcon(attachment.type)}
            </span>
            <div 
              className="karen-attachment-details"
              style={{
                overflow: 'hidden'
              }}
            >
              <div 
                className="karen-attachment-name"
                style={{
                  fontWeight: theme.typography.fontWeight.medium,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  fontSize: theme.typography.fontSize.xs
                }}
                title={attachment.name}
              >
                {attachment.name}
              </div>
              <div 
                className="karen-attachment-size"
                style={{
                  fontSize: '10px',
                  color: theme.colors.textSecondary
                }}
              >
                {formatFileSize(attachment.size)}
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
};

// Render message actions
const renderMessageActions = (
  message: ChatMessage,
  theme: Theme,
  onCopyMessage?: (messageId: string) => void,
  onRetryMessage?: (messageId: string) => void,
  onDeleteMessage?: (messageId: string) => void
): React.ReactNode => {
  return (
    <div 
      className="karen-message-actions"
      style={{
        display: 'flex',
        justifyContent: 'flex-end',
        marginTop: theme.spacing.sm,
        gap: theme.spacing.xs
      }}
    >
      {onCopyMessage && (
        <button
          onClick={() => onCopyMessage(message.id)}
          className="karen-action-button karen-copy-button"
          aria-label="Copy message"
          style={{
            backgroundColor: 'transparent',
            color: theme.colors.textSecondary,
            border: 'none',
            borderRadius: theme.borderRadius,
            padding: theme.spacing.xs,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.8rem',
            transition: 'color 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = theme.colors.primary;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = theme.colors.textSecondary;
          }}
          title="Copy"
        >
          📋
        </button>
      )}
      
      {onRetryMessage && message.role === 'assistant' && (
        <button
          onClick={() => onRetryMessage(message.id)}
          className="karen-action-button karen-retry-button"
          aria-label="Retry message"
          style={{
            backgroundColor: 'transparent',
            color: theme.colors.textSecondary,
            border: 'none',
            borderRadius: theme.borderRadius,
            padding: theme.spacing.xs,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.8rem',
            transition: 'color 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = theme.colors.warning;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = theme.colors.textSecondary;
          }}
          title="Retry"
        >
          🔄
        </button>
      )}
      
      {onDeleteMessage && (
        <button
          onClick={() => onDeleteMessage(message.id)}
          className="karen-action-button karen-delete-button"
          aria-label="Delete message"
          style={{
            backgroundColor: 'transparent',
            color: theme.colors.textSecondary,
            border: 'none',
            borderRadius: theme.borderRadius,
            padding: theme.spacing.xs,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.8rem',
            transition: 'color 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = theme.colors.error;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = theme.colors.textSecondary;
          }}
          title="Delete"
        >
          🗑️
        </button>
      )}
    </div>
  );
};

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  theme = defaultTheme,
  isLast = false,
  className = '',
  onMessageAction,
  onCopyMessage,
  onRetryMessage,
  onDeleteMessage,
  showTimestamp = true,
  showActions = true,
  showAiData = false,
  showConfidence = false,
  showKeywords = false,
  showReasoning = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const messageRef = useRef<HTMLDivElement>(null);
  
  // Scroll into view if this is the last message
  useEffect(() => {
    if (isLast && messageRef.current) {
      messageRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [isLast]);
  
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  
  const bubbleStyle: React.CSSProperties = {
    backgroundColor: isUser 
      ? `${theme.colors.primary}20` 
      : isSystem 
        ? `${theme.colors.warning}10` 
        : theme.colors.surface,
    color: isUser ? theme.colors.text : theme.colors.text,
    border: `1px solid ${isUser ? theme.colors.primary : theme.colors.border}`,
    borderRadius: theme.borderRadius,
    padding: theme.spacing.md,
    maxWidth: '85%',
    position: 'relative',
    boxShadow: theme.shadows.sm,
    wordBreak: 'break-word',
    overflow: 'hidden',
    transition: 'all 0.2s ease'
  };
  
  const containerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: isUser ? 'flex-end' : 'flex-start',
    marginBottom: isLast ? theme.spacing.lg : theme.spacing.md,
    width: '100%'
  };
  
  const contentStyle: React.CSSProperties = {
    fontSize: theme.typography.fontSize.base,
    lineHeight: '1.5',
    whiteSpace: 'pre-wrap',
    overflow: isExpanded ? 'visible' : 'hidden',
    textOverflow: isExpanded ? 'initial' : 'ellipsis',
    maxHeight: isExpanded ? 'none' : '200px'
  };
  
  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };
  
  const needsExpandButton = message.content.length > 300;
  
  return (
    <div 
      ref={messageRef}
      className={`karen-message-bubble ${isUser ? 'user' : ''} ${isSystem ? 'system' : ''} ${className}`}
      style={containerStyle}
    >
      <div 
        className="karen-bubble-content"
        style={bubbleStyle}
      >
        {/* Message content */}
        <div 
          className="karen-message-text"
          style={contentStyle}
        >
          {message.content}
        </div>
        
        {/* Expand button for long messages */}
        {needsExpandButton && (
          <button
            onClick={toggleExpand}
            className="karen-expand-button"
            style={{
              background: 'none',
              border: 'none',
              color: theme.colors.primary,
              fontSize: theme.typography.fontSize.sm,
              cursor: 'pointer',
              padding: `${theme.spacing.xs} 0`,
              marginTop: theme.spacing.xs,
              display: 'block',
              width: '100%',
              textAlign: 'left',
              fontWeight: theme.typography.fontWeight.medium
            }}
          >
            {isExpanded ? 'Show Less' : 'Show More'}
          </button>
        )}
        
        {/* Attachments */}
        {renderAttachments(message.attachments, theme)}
        
        {/* AI data */}
        {showAiData && (
          <>
            {showConfidence && renderConfidence(message.aiData?.confidence, theme)}
            {showKeywords && renderKeywords(message.aiData?.keywords, theme)}
            {showReasoning && renderReasoning(message.aiData?.reasoning, theme)}
          </>
        )}
        
        {/* Timestamp and actions */}
        <div 
          className="karen-message-footer"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: theme.spacing.sm,
            paddingTop: theme.spacing.sm,
            borderTop: `1px solid ${theme.colors.border}20`,
            fontSize: theme.typography.fontSize.xs,
            color: theme.colors.textSecondary
          }}
        >
          {showTimestamp && (
            <span 
              className="karen-message-timestamp"
              style={{
                fontStyle: 'italic'
              }}
            >
              {formatTimestamp(message.timestamp)}
            </span>
          )}
          
          {showActions && (
            <div 
              className="karen-message-actions-container"
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                flex: 1
              }}
            >
              {renderMessageActions(
                message, 
                theme, 
                onCopyMessage, 
                onRetryMessage, 
                onDeleteMessage
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;