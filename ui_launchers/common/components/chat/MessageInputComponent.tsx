import React, { useState, useRef, useEffect, KeyboardEvent, ChangeEvent } from 'react';

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

interface Attachment {
  id: string;
  name: string;
  size: string;
  type: string;
  url?: string;
}

interface MessageInputProps {
  theme: Theme;
  onSendMessage?: (message: string, attachments?: Attachment[]) => void;
  onVoiceInput?: () => void;
  onAttachFile?: (files: File[]) => void;
  onTyping?: (isTyping: boolean) => void;
  placeholder?: string;
  disabled?: boolean;
  maxLength?: number;
  showCharacterCount?: boolean;
  showSendButton?: boolean;
  showVoiceButton?: boolean;
  showAttachButton?: boolean;
  allowAttachments?: boolean;
  allowVoiceInput?: boolean;
  className?: string;
  initialValue?: string;
  autoFocus?: boolean;
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

// Format file size
const formatFileSize = (size: number): string => {
  if (size < 1024) {
    return `${size} B`;
  } else if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  } else {
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }
};

// Get file icon based on type
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

export const MessageInput: React.FC<MessageInputProps> = ({
  theme = defaultTheme,
  onSendMessage,
  onVoiceInput,
  onAttachFile,
  onTyping,
  placeholder = 'Type a message...',
  disabled = false,
  maxLength = 4000,
  showCharacterCount = true,
  showSendButton = true,
  showVoiceButton = true,
  showAttachButton = true,
  allowAttachments = true,
  allowVoiceInput = true,
  className = '',
  initialValue = '',
  autoFocus = true
}) => {
  const [message, setMessage] = useState<string>(initialValue);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [typingTimeout, setTypingTimeout] = useState<NodeJS.Timeout | null>(null);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Focus on the textarea when component mounts
  useEffect(() => {
    if (autoFocus && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [autoFocus]);
  
  // Handle textarea height adjustment
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);
  
  // Handle typing indicator
  const handleTyping = (text: string) => {
    setMessage(text);
    
    if (text.trim() && !isTyping) {
      setIsTyping(true);
      if (onTyping) {
        onTyping(true);
      }
    } else if (!text.trim() && isTyping) {
      setIsTyping(false);
      if (onTyping) {
        onTyping(false);
      }
    }
    
    // Clear previous timeout
    if (typingTimeout) {
      clearTimeout(typingTimeout);
    }
    
    // Set new timeout
    if (text.trim()) {
      const timeout = setTimeout(() => {
        setIsTyping(false);
        if (onTyping) {
          onTyping(false);
        }
      }, 1000);
      setTypingTimeout(timeout);
    }
  };
  
  // Handle send message
  const handleSendMessage = () => {
    if ((message.trim() || attachments.length > 0) && !disabled) {
      if (onSendMessage) {
        onSendMessage(message.trim(), attachments);
      }
      setMessage('');
      setAttachments([]);
      setIsTyping(false);
      if (onTyping) {
        onTyping(false);
      }
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  
  // Handle keyboard shortcuts
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Handle file attachment
  const handleAttachFile = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  
  // Handle file selection
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      const newAttachments: Attachment[] = files.map(file => ({
        id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        name: file.name,
        size: formatFileSize(file.size),
        type: file.type,
        url: URL.createObjectURL(file)
      }));
      
      setAttachments(prev => [...prev, ...newAttachments]);
      
      if (onAttachFile) {
        onAttachFile(files);
      }
    }
    
    // Reset the file input value so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  // Handle file removal
  const handleRemoveAttachment = (id: string) => {
    setAttachments(prev => prev.filter(att => att.id !== id));
  };
  
  // Handle drag and drop
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = () => {
    setIsDragging(false);
  };
  
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files);
      const newAttachments: Attachment[] = files.map(file => ({
        id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        name: file.name,
        size: formatFileSize(file.size),
        type: file.type,
        url: URL.createObjectURL(file)
      }));
      
      setAttachments(prev => [...prev, ...newAttachments]);
      
      if (onAttachFile) {
        onAttachFile(files);
      }
    }
  };
  
  // Render attachments
  const renderAttachments = () => {
    if (attachments.length === 0) return null;
    
    return (
      <div 
        className="karen-attachments"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: theme.spacing.sm,
          marginBottom: theme.spacing.sm,
          padding: theme.spacing.sm,
          backgroundColor: theme.colors.surface,
          borderRadius: theme.borderRadius,
          border: `1px solid ${theme.colors.border}`
        }}
      >
        {attachments.map(attachment => (
          <div 
            key={attachment.id}
            className="karen-attachment-item"
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
              backgroundColor: theme.colors.background,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              maxWidth: '200px'
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
                {attachment.size}
              </div>
            </div>
            <button
              onClick={() => handleRemoveAttachment(attachment.id)}
              className="karen-remove-attachment"
              aria-label="Remove attachment"
              style={{
                backgroundColor: 'transparent',
                color: theme.colors.error,
                border: 'none',
                borderRadius: theme.borderRadius,
                padding: theme.spacing.xs,
                cursor: 'pointer',
                marginLeft: theme.spacing.xs,
                fontSize: '0.8rem'
              }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    );
  };
  
  // Calculate character count
  const characterCount = message.length;
  const isNearLimit = characterCount > maxLength * 0.9;
  const isOverLimit = characterCount > maxLength;
  
  return (
    <div 
      className={`karen-message-input ${className}`}
      style={{
        backgroundColor: theme.colors.background,
        borderRadius: theme.borderRadius,
        border: `1px solid ${theme.colors.border}`,
        padding: theme.spacing.md,
        boxShadow: theme.shadows.sm
      }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drag and drop overlay */}
      {isDragging && (
        <div 
          className="karen-drag-overlay"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: `${theme.colors.primary}20`,
            border: `2px dashed ${theme.colors.primary}`,
            borderRadius: theme.borderRadius,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10
          }}
        >
          <div 
            className="karen-drag-text"
            style={{
              fontSize: theme.typography.fontSize.lg,
              fontWeight: theme.typography.fontWeight.bold,
              color: theme.colors.primary
            }}
          >
            Drop files here
          </div>
        </div>
      )}
      
      {/* Attachments */}
      {renderAttachments()}
      
      {/* Input area */}
      <div 
        className="karen-input-container"
        style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'flex-end',
          gap: theme.spacing.sm
        }}
      >
        {/* Textarea */}
        <div 
          className="karen-textarea-wrapper"
          style={{
            flex: 1,
            position: 'relative'
          }}
        >
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => handleTyping(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            maxLength={maxLength}
            className="karen-message-textarea"
            style={{
              width: '100%',
              minHeight: '44px',
              maxHeight: '200px',
              padding: `${theme.spacing.sm} ${theme.spacing.md}`,
              backgroundColor: theme.colors.background,
              color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              fontSize: theme.typography.fontSize.base,
              fontFamily: theme.typography.fontFamily,
              lineHeight: '1.5',
              resize: 'none',
              outline: 'none',
              transition: 'border-color 0.2s ease',
              boxSizing: 'border-box'
            }}
          />
          
          {/* Character count */}
          {showCharacterCount && (
            <div 
              className="karen-character-count"
              style={{
                position: 'absolute',
                bottom: theme.spacing.xs,
                right: theme.spacing.sm,
                fontSize: '10px',
                color: isOverLimit 
                  ? theme.colors.error 
                  : isNearLimit 
                    ? theme.colors.warning 
                    : theme.colors.textSecondary
              }}
            >
              {characterCount}/{maxLength}
            </div>
          )}
        </div>
        
        {/* Action buttons */}
        <div 
          className="karen-input-actions"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: theme.spacing.xs
          }}
        >
          {/* Attach button */}
          {allowAttachments && showAttachButton && (
            <button
              onClick={handleAttachFile}
              disabled={disabled}
              className="karen-attach-button"
              aria-label="Attach file"
              style={{
                backgroundColor: 'transparent',
                color: disabled ? theme.colors.textSecondary : theme.colors.text,
                border: 'none',
                borderRadius: theme.borderRadius,
                padding: theme.spacing.sm,
                cursor: disabled ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem',
                transition: 'color 0.2s ease'
              }}
              onMouseEnter={(e) => {
                if (!disabled) {
                  e.currentTarget.style.color = theme.colors.primary;
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = disabled ? theme.colors.textSecondary : theme.colors.text;
              }}
            >
              📎
            </button>
          )}
          
          {/* Voice button */}
          {allowVoiceInput && showVoiceButton && (
            <button
              onClick={onVoiceInput}
              disabled={disabled}
              className="karen-voice-button"
              aria-label="Voice input"
              style={{
                backgroundColor: 'transparent',
                color: disabled ? theme.colors.textSecondary : theme.colors.text,
                border: 'none',
                borderRadius: theme.borderRadius,
                padding: theme.spacing.sm,
                cursor: disabled ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem',
                transition: 'color 0.2s ease'
              }}
              onMouseEnter={(e) => {
                if (!disabled) {
                  e.currentTarget.style.color = theme.colors.primary;
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = disabled ? theme.colors.textSecondary : theme.colors.text;
              }}
            >
              🎤
            </button>
          )}
          
          {/* Send button */}
          {showSendButton && (
            <button
              onClick={handleSendMessage}
              disabled={disabled || (!message.trim() && attachments.length === 0)}
              className="karen-send-button"
              aria-label="Send message"
              style={{
                backgroundColor: disabled || (!message.trim() && attachments.length === 0)
                  ? theme.colors.textSecondary
                  : theme.colors.primary,
                color: 'white',
                border: 'none',
                borderRadius: theme.borderRadius,
                padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                cursor: disabled || (!message.trim() && attachments.length === 0)
                  ? 'not-allowed'
                  : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1rem',
                fontWeight: theme.typography.fontWeight.medium,
                transition: 'background-color 0.2s ease'
              }}
            >
              ➤
            </button>
          )}
        </div>
      </div>
      
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />
    </div>
  );
};

export default MessageInput;