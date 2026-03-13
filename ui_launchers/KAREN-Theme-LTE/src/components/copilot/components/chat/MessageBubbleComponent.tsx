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
  className?: string;
  onCopyMessage?: (messageId: string) => void;
  onRetryMessage?: (messageId: string) => void;
  onDeleteMessage?: (messageId: string) => void;
  showTimestamp?: boolean;
  showActions?: boolean;
  showAiData?: boolean;
  showConfidence?: boolean;
  showKeywords?: boolean;
  showReasoning?: boolean;
  isHighlighted?: boolean;
  ariaPosInSet?: number;
  ariaSetSize?: number;
}

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
const renderConfidence = (theme: Theme, confidence?: number): React.ReactNode => {
  if (confidence === undefined) return null;

  const confidenceColor = confidence > 0.8
    ? theme.colors.success
    : confidence > 0.6
      ? theme.colors.warning
      : theme.colors.error;

  return (
    <div
      className="copilot-confidence-indicator"
      style={{
        display: 'flex',
        alignItems: 'center',
        marginTop: theme.spacing.sm
      }}
    >
      <span
        className="copilot-confidence-label"
        style={{
          fontSize: theme.typography.fontSize.xs,
          color: theme.colors.textSecondary,
          marginRight: theme.spacing.xs
        }}
      >
        Confidence:
      </span>
      <div
        className="copilot-confidence-bar"
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
          className="copilot-confidence-fill"
          style={{
            width: `${confidence * 100}%`,
            height: '100%',
            backgroundColor: confidenceColor
          }}
        />
      </div>
      <span
        className="copilot-confidence-value"
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
const renderKeywords = (theme: Theme, keywords?: string[]): React.ReactNode => {
  if (!keywords || keywords.length === 0) return null;

  return (
    <div
      className="copilot-keywords"
      style={{
        marginTop: theme.spacing.sm
      }}
    >
      <span
        className="copilot-keywords-label"
        style={{
          fontSize: theme.typography.fontSize.xs,
          color: theme.colors.textSecondary,
          marginRight: theme.spacing.xs
        }}
      >
        Keywords:
      </span>
      <div
        className="copilot-keywords-container"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: theme.spacing.xs
        }}
      >
        {keywords.slice(0, 5).map((keyword, index) => (
          <span
            key={index}
            className="copilot-keyword"
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
            className="copilot-more-keywords"
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
const renderReasoning = (theme: Theme, reasoning?: string): React.ReactNode => {
  if (!reasoning) return null;

  return (
    <details
      className="copilot-reasoning"
      style={{
        marginTop: theme.spacing.sm
      }}
    >
      <summary
        className="copilot-reasoning-toggle"
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
        className="copilot-reasoning-content"
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
const renderAttachments = (theme: Theme, attachments?: Array<{
  id: string;
  name: string;
  size: string;
  type: string;
  url?: string;
}>): React.ReactNode => {
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
      className="copilot-attachments"
      style={{
        marginTop: theme.spacing.sm
      }}
    >
      <span
        className="copilot-attachments-label"
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
        className="copilot-attachments-container"
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
            className="copilot-attachment"
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
              className="copilot-attachment-icon"
              style={{
                marginRight: theme.spacing.xs,
                fontSize: '1rem'
              }}
            >
              {getFileIcon(attachment.type)}
            </span>
            <div
              className="copilot-attachment-details"
              style={{
                overflow: 'hidden'
              }}
            >
              <div
                className="copilot-attachment-name"
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
                className="copilot-attachment-size"
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
      className="copilot-message-actions"
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
          className="copilot-action-button copilot-copy-button"
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
          className="copilot-action-button copilot-retry-button"
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
          className="copilot-action-button copilot-delete-button"
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

export const MessageBubbleComponent: React.FC<MessageBubbleProps> = ({
  message,
  theme,
  className = '',
  onCopyMessage,
  onRetryMessage,
  onDeleteMessage,
  showTimestamp = true,
  showActions = true,
  showAiData = false,
  showConfidence = false,
  showKeywords = false,
  showReasoning = false,
  isHighlighted = false,
  ariaPosInSet,
  ariaSetSize
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const messageRef = useRef<HTMLDivElement>(null);
  
  // Scroll into view if this is the last message
  useEffect(() => {
    // This would be handled by the parent component
  }, []);
  
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  
  const bubbleStyle: React.CSSProperties = {
    backgroundColor: isUser
      ? `${theme.colors.primary}20`
      : isSystem
        ? `${theme.colors.warning}10`
        : theme.colors.surface,
    color: isUser ? theme.colors.text : theme.colors.text,
    border: isHighlighted
      ? `2px solid ${theme.colors.warning}`
      : `1px solid ${isUser ? theme.colors.primary : theme.colors.border}`,
    borderRadius: theme.borderRadius,
    padding: theme.spacing.md,
    maxWidth: '85%',
    position: 'relative',
    boxShadow: isHighlighted ? theme.shadows.md : theme.shadows.sm,
    wordBreak: 'break-word',
    overflow: 'hidden',
    transition: 'all 0.2s ease',
    animation: isHighlighted ? 'pulse 2s' : 'none'
  };
  
  const containerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: isUser ? 'flex-end' : 'flex-start',
    marginBottom: theme.spacing.md,
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
      id={`message-${message.id}`}
      className={`copilot-message-bubble ${isUser ? 'user' : ''} ${isSystem ? 'system' : ''} ${isHighlighted ? 'highlighted' : ''} ${className}`}
      style={containerStyle}
      role="article"
      aria-label={`${isUser ? 'Your' : isSystem ? 'System' : 'Assistant'} message`}
      aria-posinset={ariaPosInSet}
      aria-setsize={ariaSetSize}
      aria-live={isHighlighted ? "polite" : undefined}
      aria-atomic={isHighlighted ? true : undefined}
    >
      <div
        className="copilot-bubble-content"
        style={bubbleStyle}
      >
        {/* Message content */}
        <div
          className="copilot-message-text"
          style={contentStyle}
          aria-label="Message content"
        >
          {message.content}
        </div>
        
        {/* Expand button for long messages */}
        {needsExpandButton && (
          <button
            onClick={toggleExpand}
            className="copilot-expand-button"
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
            aria-expanded={isExpanded}
            aria-controls={`message-content-${message.id}`}
            tabIndex={0}
          >
            {isExpanded ? 'Show Less' : 'Show More'}
          </button>
        )}
        
        {/* Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div role="region" aria-label="Attachments">
            {renderAttachments(theme, message.attachments)}
          </div>
        )}
        
        {/* AI data */}
        {showAiData && (
          <div role="region" aria-label="AI information">
            {showConfidence && renderConfidence(theme, message.aiData?.confidence)}
            {showKeywords && renderKeywords(theme, message.aiData?.keywords)}
            {showReasoning && renderReasoning(theme, message.aiData?.reasoning)}
          </div>
        )}
        
        {/* Timestamp and actions */}
        <div
          className="copilot-message-footer"
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
          role="group"
          aria-label="Message information and actions"
        >
          {showTimestamp && (
            <span 
              className="copilot-message-timestamp"
              style={{
                fontStyle: 'italic'
              }}
            >
              {formatTimestamp(message.timestamp)}
            </span>
          )}
          
          {showActions && (
            <div
              className="copilot-message-actions-container"
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                flex: 1
              }}
              role="group"
              aria-label="Message actions"
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

export default MessageBubbleComponent;

<style jsx>{`
  /* Responsive styles for MessageBubbleComponent */
  @media (max-width: 768px) {
    .copilot-message-bubble .copilot-bubble-content {
      max-width: 95%;
      padding: 12px;
    }
    
    .copilot-message-bubble .copilot-message-text {
      font-size: 14px;
      line-height: 1.4;
    }
    
    .copilot-message-bubble .copilot-attachment {
      max-width: 150px;
    }
    
    .copilot-message-bubble .copilot-keywords-container {
      flex-direction: column;
    }
  }
  
  @media (max-width: 480px) {
    .copilot-message-bubble .copilot-bubble-content {
      max-width: 90%;
      padding: 10px;
    }
    
    .copilot-message-bubble .copilot-message-text {
      font-size: 13px;
      max-height: 150px;
    }
    
    .copilot-message-bubble .copilot-message-footer {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }
    
    .copilot-message-bubble .copilot-message-actions-container {
      justify-content: flex-start;
      width: 100%;
    }
    
    .copilot-message-bubble .copilot-attachment {
      max-width: 120px;
      padding: 6px 8px;
    }
    
    .copilot-message-bubble .copilot-attachment-name {
      font-size: 11px;
    }
    
    .copilot-message-bubble .copilot-keyword {
      font-size: 9px;
      padding: 1px 4px;
    }
  }
  
  @media (min-width: 1200px) {
    .copilot-message-bubble .copilot-bubble-content {
      max-width: 70%;
    }
    
    .copilot-message-bubble .copilot-message-text {
      font-size: 16px;
      line-height: 1.6;
    }
  }
  
  @keyframes pulse {
    0% {
      box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.4);
    }
    70% {
      box-shadow: 0 0 0 10px rgba(255, 193, 7, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(255, 193, 7, 0);
    }
  }
  
  .copilot-message-bubble.highlighted {
    animation: pulse 2s;
  }
`}</style>