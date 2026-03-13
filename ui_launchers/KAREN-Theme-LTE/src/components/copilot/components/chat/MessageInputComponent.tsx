import React, { useState, useRef, useEffect, KeyboardEvent, ChangeEvent, DragEvent } from 'react';

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

interface FileAttachment {
  id: string;
  name: string;
  size: string;
  type: string;
  url?: string;
  file?: File;
}

interface MessageInputProps {
  theme: Theme;
  className?: string;
  placeholder?: string;
  disabled?: boolean;
  maxLength?: number;
  showCharacterCount?: boolean;
  showVoiceButton?: boolean;
  showAttachButton?: boolean;
  showEmojiButton?: boolean;
  allowDragAndDrop?: boolean;
  onSendMessage?: (message: string, attachments?: FileAttachment[]) => void;
  onVoiceRecord?: () => void;
  onAttachFiles?: (files: FileAttachment[]) => void;
  onEmojiSelect?: (emoji: string) => void;
  onTyping?: (isTyping: boolean) => void;
  initialMessage?: string;
  initialAttachments?: FileAttachment[];
  autoResize?: boolean;
  maxRows?: number;
  minRows?: number;
}

// Format file size
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) {
    return `${bytes} B`;
  } else if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  } else {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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

// Render file attachment
const renderAttachment = (
  attachment: FileAttachment,
  theme: Theme,
  onRemove?: (id: string) => void
): React.ReactNode => {
  return (
    <div
      key={attachment.id}
      className="copilot-attachment-preview"
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
        backgroundColor: theme.colors.surface,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius,
        marginBottom: theme.spacing.sm,
        maxWidth: '100%'
      }}
    >
      <span
        className="copilot-attachment-icon"
        style={{
          marginRight: theme.spacing.sm,
          fontSize: '1.2rem'
        }}
      >
        {getFileIcon(attachment.type)}
      </span>
      <div
        className="copilot-attachment-details"
        style={{
          flex: 1,
          minWidth: 0
        }}
      >
        <div
          className="copilot-attachment-name"
          style={{
            fontWeight: theme.typography.fontWeight.medium,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            fontSize: theme.typography.fontSize.sm,
            color: theme.colors.text
          }}
          title={attachment.name}
        >
          {attachment.name}
        </div>
        <div
          className="copilot-attachment-size"
          style={{
            fontSize: '0.7rem',
            color: theme.colors.textSecondary
          }}
        >
          {attachment.size}
        </div>
      </div>
      {onRemove && (
        <button
          onClick={() => onRemove(attachment.id)}
          className="copilot-remove-attachment"
          aria-label="Remove attachment"
          style={{
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
            marginLeft: theme.spacing.sm,
            fontSize: '0.8rem',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = theme.colors.error + '20';
            e.currentTarget.style.color = theme.colors.error;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.color = theme.colors.textSecondary;
          }}
        >
          ✕
        </button>
      )}
    </div>
  );
};

// Render emoji picker (simplified version)
const renderEmojiPicker = (
  theme: Theme,
  onSelect: (emoji: string) => void,
  onClose: () => void
): React.ReactNode => {
  const commonEmojis = [
    '😀', '😂', '😍', '😎', '👍', '👋', '🙏', '❤️',
    '🔥', '✨', '🎉', '💯', '🤔', '😊', '😢', '😡'
  ];

  return (
    <div
      className="copilot-emoji-picker"
      style={{
        position: 'absolute',
        bottom: '100%',
        right: '0',
        backgroundColor: theme.colors.surface,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius,
        boxShadow: theme.shadows.lg,
        padding: theme.spacing.sm,
        marginBottom: theme.spacing.xs,
        zIndex: 1000
      }}
    >
      <div
        className="copilot-emoji-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(8, 1fr)',
          gap: theme.spacing.xs
        }}
      >
        {commonEmojis.map((emoji, index) => (
          <button
            key={index}
            onClick={() => onSelect(emoji)}
            className="copilot-emoji-button"
            aria-label={`Add ${emoji} emoji`}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              borderRadius: theme.borderRadius,
              width: '30px',
              height: '30px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '1rem',
              transition: 'background-color 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.colors.primary + '20';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            {emoji}
          </button>
        ))}
      </div>
    </div>
  );
};

export const MessageInputComponent: React.FC<MessageInputProps> = ({
  theme,
  className = '',
  placeholder = 'Type a message...',
  disabled = false,
  maxLength = 5000,
  showCharacterCount = true,
  showVoiceButton = true,
  showAttachButton = true,
  showEmojiButton = true,
  allowDragAndDrop = true,
  onSendMessage,
  onVoiceRecord,
  onAttachFiles,
  onEmojiSelect,
  onTyping,
  initialMessage = '',
  initialAttachments = [],
  autoResize = true,
  maxRows = 5,
  minRows = 1
}) => {
  const [message, setMessage] = useState(initialMessage);
  const [attachments, setAttachments] = useState<FileAttachment[]>(initialAttachments);
  const [isDragging, setIsDragging] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle text input change
  const handleMessageChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const newMessage = e.target.value;
    setMessage(newMessage);
    
    if (onTyping) {
      onTyping(newMessage.length > 0);
    }
    
    if (autoResize) {
      adjustTextareaHeight();
    }
  };

  // Adjust textarea height based on content
  const adjustTextareaHeight = () => {
    if (!textareaRef.current) return;
    
    textareaRef.current.style.height = 'auto';
    
    const lineHeight = parseInt(theme.typography.fontSize.base) * 1.5;
    const maxHeight = lineHeight * maxRows;
    const minHeight = lineHeight * minRows;
    
    const scrollHeight = textareaRef.current.scrollHeight;
    const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
    
    textareaRef.current.style.height = `${newHeight}px`;
  };

  // Handle key press events
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send message on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handle composition events for IME support
  const handleCompositionStart = () => {
    setIsComposing(true);
  };

  const handleCompositionEnd = () => {
    setIsComposing(false);
  };

  // Send message
  const handleSendMessage = () => {
    const trimmedMessage = message.trim();
    
    if (!trimmedMessage && attachments.length === 0) return;
    
    if (onSendMessage) {
      onSendMessage(trimmedMessage, attachments);
    }
    
    // Reset form
    setMessage('');
    setAttachments([]);
    
    if (onTyping) {
      onTyping(false);
    }
    
    if (autoResize && textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    
    // Focus back on textarea
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  // Handle voice recording
  const handleVoiceRecord = () => {
    if (onVoiceRecord) {
      onVoiceRecord();
    }
  };

  // Handle file attachment button click
  const handleAttachClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Handle file selection
  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newAttachments: FileAttachment[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (!file) continue;

      const attachment: FileAttachment = {
        id: `file-${Date.now()}-${i}`,
        name: file.name,
        size: formatFileSize(file.size),
        type: file.type,
        file: file
      };
      newAttachments.push(attachment);
    }

    setAttachments([...attachments, ...newAttachments]);

    if (onAttachFiles) {
      onAttachFiles(newAttachments);
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Remove attachment
  const handleRemoveAttachment = (id: string) => {
    setAttachments(attachments.filter(att => att.id !== id));
  };

  // Handle drag and drop events
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    if (!allowDragAndDrop) return;

    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;

    const newAttachments: FileAttachment[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (!file) continue;

      const attachment: FileAttachment = {
        id: `file-${Date.now()}-${i}`,
        name: file.name,
        size: formatFileSize(file.size),
        type: file.type,
        file: file
      };
      newAttachments.push(attachment);
    }

    setAttachments([...attachments, ...newAttachments]);

    if (onAttachFiles) {
      onAttachFiles(newAttachments);
    }
  };

  // Handle emoji selection
  const handleEmojiSelect = (emoji: string) => {
    setMessage(prev => prev + emoji);
    setShowEmojiPicker(false);
    
    if (onEmojiSelect) {
      onEmojiSelect(emoji);
    }
    
    // Focus back on textarea
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  // Toggle emoji picker
  const toggleEmojiPicker = () => {
    setShowEmojiPicker(!showEmojiPicker);
  };

  // Close emoji picker when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current && 
        !containerRef.current.contains(event.target as Node) &&
        showEmojiPicker
      ) {
        setShowEmojiPicker(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showEmojiPicker]);

  // Initialize textarea height
  useEffect(() => {
    if (autoResize && textareaRef.current) {
      adjustTextareaHeight();
    }
  }, []);

  // Focus textarea when component mounts
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  const canSend = message.trim().length > 0 || attachments.length > 0;
  const characterCount = message.length;
  const isNearLimit = characterCount > maxLength * 0.9;
  const isAtLimit = characterCount >= maxLength;

  const containerStyle: React.CSSProperties = {
    position: 'relative',
    width: '100%',
    backgroundColor: theme.colors.surface,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.md,
    transition: 'all 0.2s ease',
    ...(isDragging ? {
      borderColor: theme.colors.primary,
      backgroundColor: `${theme.colors.primary}10`
    } : {}),
    ...(disabled ? {
      opacity: 0.7,
      cursor: 'not-allowed'
    } : {})
  };

  const textareaStyle: React.CSSProperties = {
    width: '100%',
    minHeight: `${minRows * 1.5}rem`,
    maxHeight: `${maxRows * 1.5}rem`,
    backgroundColor: 'transparent',
    border: 'none',
    outline: 'none',
    resize: 'none',
    color: theme.colors.text,
    fontSize: theme.typography.fontSize.base,
    fontFamily: theme.typography.fontFamily,
    lineHeight: '1.5',
    ...(disabled ? {
      cursor: 'not-allowed'
    } : {})
  };

  const buttonStyle: React.CSSProperties = {
    backgroundColor: 'transparent',
    color: theme.colors.textSecondary,
    border: 'none',
    borderRadius: '50%',
    width: '36px',
    height: '36px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    fontSize: '1rem',
    transition: 'all 0.2s ease',
    ...(disabled ? {
      cursor: 'not-allowed',
      opacity: 0.5
    } : {})
  };

  const sendButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: canSend ? theme.colors.primary : 'transparent',
    color: canSend ? '#fff' : theme.colors.textSecondary,
    ...(canSend ? {
      boxShadow: theme.shadows.sm
    } : {})
  };

  return (
    <div
      ref={containerRef}
      className={`copilot-message-input ${className}`}
      style={containerStyle}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      role="form"
      aria-label="Message input form"
    >
      {/* Drag and drop overlay */}
      {isDragging && (
        <div
          className="copilot-drag-overlay"
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
            className="copilot-drag-text"
            style={{
              fontSize: theme.typography.fontSize.lg,
              fontWeight: theme.typography.fontWeight.medium,
              color: theme.colors.primary
            }}
          >
            Drop files here
          </div>
        </div>
      )}

      {/* Attachments preview */}
      {attachments.length > 0 && (
        <div
          className="copilot-attachments-preview"
          style={{
            marginBottom: theme.spacing.sm,
            maxHeight: '150px',
            overflowY: 'auto'
          }}
          role="region"
          aria-label="Attached files"
        >
          {attachments.map(attachment =>
            renderAttachment(attachment, theme, handleRemoveAttachment)
          )}
        </div>
      )}

      {/* Text input */}
      <textarea
        ref={textareaRef}
        className="copilot-text-input"
        placeholder={placeholder}
        value={message}
        onChange={handleMessageChange}
        onKeyDown={handleKeyDown}
        onCompositionStart={handleCompositionStart}
        onCompositionEnd={handleCompositionEnd}
        disabled={disabled}
        maxLength={maxLength}
        style={textareaStyle}
        aria-label="Message input"
        aria-describedby={isAtLimit ? "character-limit-warning" : undefined}
        rows={minRows}
        aria-required="true"
      />
      {isAtLimit && (
        <div id="character-limit-warning" style={{ color: theme.colors.error, fontSize: theme.typography.fontSize.xs }}>
          Character limit reached
        </div>
      )}

      {/* Character count */}
      {showCharacterCount && (
        <div
          className="copilot-character-count"
          style={{
            fontSize: theme.typography.fontSize.xs,
            color: isAtLimit
              ? theme.colors.error
              : isNearLimit
                ? theme.colors.warning
                : theme.colors.textSecondary,
            textAlign: 'right',
            marginTop: theme.spacing.xs
          }}
          aria-live={isAtLimit ? "assertive" : "polite"}
          aria-atomic="true"
        >
          {characterCount}/{maxLength}
        </div>
      )}

      {/* Action buttons */}
      <div
        className="copilot-input-actions"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: theme.spacing.sm
        }}
        role="group"
        aria-label="Message actions"
      >
        {/* Left buttons */}
        <div
          className="copilot-left-buttons"
          style={{
            display: 'flex',
            gap: theme.spacing.xs
          }}
          role="group"
          aria-label="Message input options"
        >
          {/* Attach button */}
          {showAttachButton && (
            <button
              onClick={handleAttachClick}
              className="copilot-attach-button"
              aria-label="Attach files"
              disabled={disabled}
              style={buttonStyle}
              onMouseEnter={(e) => {
                if (!disabled) {
                  e.currentTarget.style.backgroundColor = theme.colors.primary + '20';
                  e.currentTarget.style.color = theme.colors.primary;
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = theme.colors.textSecondary;
              }}
              tabIndex={0}
            >
              📎
            </button>
          )}

          {/* Emoji button */}
          {showEmojiButton && (
            <div
              className="copilot-emoji-container"
              style={{ position: 'relative' }}
            >
              <button
                onClick={toggleEmojiPicker}
                className="copilot-emoji-button"
                aria-label="Add emoji"
                aria-expanded={showEmojiPicker}
                aria-controls="emoji-picker"
                disabled={disabled}
                style={buttonStyle}
                onMouseEnter={(e) => {
                  if (!disabled) {
                    e.currentTarget.style.backgroundColor = theme.colors.primary + '20';
                    e.currentTarget.style.color = theme.colors.primary;
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = theme.colors.textSecondary;
                }}
                tabIndex={0}
              >
                😊
              </button>

              {/* Emoji picker */}
              {showEmojiPicker && (
                <div id="emoji-picker" role="region" aria-label="Emoji picker">
                  {renderEmojiPicker(theme, handleEmojiSelect, () => setShowEmojiPicker(false))}
                </div>
              )}
            </div>
          )}

          {/* Voice button */}
          {showVoiceButton && (
            <button
              onClick={handleVoiceRecord}
              className="copilot-voice-button"
              aria-label="Record voice message"
              disabled={disabled}
              style={buttonStyle}
              onMouseEnter={(e) => {
                if (!disabled) {
                  e.currentTarget.style.backgroundColor = theme.colors.primary + '20';
                  e.currentTarget.style.color = theme.colors.primary;
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = theme.colors.textSecondary;
              }}
              tabIndex={0}
            >
              🎤
            </button>
          )}
        </div>

        {/* Send button */}
        <button
          onClick={handleSendMessage}
          className="copilot-send-button"
          aria-label="Send message"
          disabled={disabled || !canSend}
          style={sendButtonStyle}
          onMouseEnter={(e) => {
            if (canSend && !disabled) {
              e.currentTarget.style.backgroundColor = theme.colors.primary;
              e.currentTarget.style.transform = 'scale(1.05)';
            }
          }}
          onMouseLeave={(e) => {
            if (canSend && !disabled) {
              e.currentTarget.style.backgroundColor = theme.colors.primary;
              e.currentTarget.style.transform = 'scale(1)';
            }
          }}
          tabIndex={0}
        >
          ➤
        </button>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />
    </div>
  );
};

export default MessageInputComponent;