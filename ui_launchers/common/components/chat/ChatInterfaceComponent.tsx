import React, { useState, useEffect, useRef } from 'react';

// Import components
import { MessageBubble } from './MessageBubbleComponent';
import { MessageInput } from './MessageInputComponent';
import { ConversationHistory } from './ConversationHistoryComponent';
import { VoiceRecorder } from './VoiceRecorderComponent';

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

interface ChatInterfaceProps {
  theme: Theme;
  messages?: ChatMessage[];
  conversations?: ConversationSession[];
  currentConversationId?: string | null;
  onSendMessage?: (message: string, attachments?: any[]) => void;
  onRetryMessage?: (messageId: string) => void;
  onDeleteMessage?: (messageId: string) => void;
  onCopyMessage?: (messageId: string) => void;
  onSelectConversation?: (conversation: ConversationSession) => void;
  onDeleteConversation?: (conversationId: string) => void;
  onExportConversations?: (format: 'json' | 'text' | 'csv', conversationIds?: string[]) => string;
  onClearHistory?: () => void;
  onVoiceMessage?: (message: string) => void;
  onTyping?: (isTyping: boolean) => void;
  placeholder?: string;
  disabled?: boolean;
  maxLength?: number;
  showHistory?: boolean;
  showVoiceInput?: boolean;
  showAiData?: boolean;
  showConfidence?: boolean;
  showKeywords?: boolean;
  showReasoning?: boolean;
  showTimestamps?: boolean;
  showActions?: boolean;
  showCharacterCount?: boolean;
  showSendButton?: boolean;
  showVoiceButton?: boolean;
  showAttachButton?: boolean;
  allowAttachments?: boolean;
  allowVoiceInput?: boolean;
  autoFocus?: boolean;
  className?: string;
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

// Sample messages for demonstration
const sampleMessages: ChatMessage[] = [
  {
    id: 'msg-1',
    role: 'assistant',
    content: 'Hello! I\'m your AI assistant. How can I help you today?',
    timestamp: new Date(Date.now() - 30000),
    aiData: {
      confidence: 0.98,
      keywords: ['greeting', 'introduction', 'assistance']
    }
  },
  {
    id: 'msg-2',
    role: 'user',
    content: 'I need help with my project. Can you provide some guidance?',
    timestamp: new Date(Date.now() - 20000)
  },
  {
    id: 'msg-3',
    role: 'assistant',
    content: 'I\'d be happy to help with your project! To provide you with the best guidance, could you please tell me more about what kind of project you\'re working on and what specific areas you need assistance with?',
    timestamp: new Date(Date.now() - 10000),
    aiData: {
      confidence: 0.95,
      keywords: ['project', 'guidance', 'assistance'],
      reasoning: 'User is asking for help with a project but hasn\'t provided specific details. I need to ask for more information to provide targeted assistance.'
    }
  }
];

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  theme = defaultTheme,
  messages = sampleMessages,
  conversations = [],
  currentConversationId = null,
  onSendMessage,
  onRetryMessage,
  onDeleteMessage,
  onCopyMessage,
  onSelectConversation,
  onDeleteConversation,
  onExportConversations,
  onClearHistory,
  onVoiceMessage,
  onTyping,
  placeholder = 'Type a message...',
  disabled = false,
  maxLength = 4000,
  showHistory = true,
  showVoiceInput = true,
  showAiData = false,
  showConfidence = false,
  showKeywords = false,
  showReasoning = false,
  showTimestamps = true,
  showActions = true,
  showCharacterCount = true,
  showSendButton = true,
  showVoiceButton = true,
  showAttachButton = true,
  allowAttachments = true,
  allowVoiceInput = true,
  autoFocus = true,
  className = ''
}) => {
  const [stateMessages, setStateMessages] = useState<ChatMessage[]>(messages);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isHistoryVisible, setIsHistoryVisible] = useState<boolean>(showHistory);
  const [isVoiceInputVisible, setIsVoiceInputVisible] = useState<boolean>(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Update messages when prop changes
  useEffect(() => {
    setStateMessages(messages);
  }, [messages]);
  
  // Scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [stateMessages]);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  // Handle sending a message
  const handleSendMessage = (message: string, attachments?: any[]) => {
    if (message.trim() || (attachments && attachments.length > 0)) {
      const newMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date(),
        attachments
      };
      
      setStateMessages(prev => [...prev, newMessage]);
      
      if (onSendMessage) {
        onSendMessage(message, attachments);
      }
    }
  };
  
  // Handle voice message
  const handleVoiceMessage = (message: string) => {
    if (message.trim()) {
      const newMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date()
      };
      
      setStateMessages(prev => [...prev, newMessage]);
      
      if (onVoiceMessage) {
        onVoiceMessage(message);
      }
    }
  };
  
  // Handle retry message
  const handleRetryMessage = (messageId: string) => {
    if (onRetryMessage) {
      onRetryMessage(messageId);
    }
  };
  
  // Handle delete message
  const handleDeleteMessage = (messageId: string) => {
    setStateMessages(prev => prev.filter(msg => msg.id !== messageId));
    
    if (onDeleteMessage) {
      onDeleteMessage(messageId);
    }
  };
  
  // Handle copy message
  const handleCopyMessage = (messageId: string) => {
    const message = stateMessages.find(msg => msg.id === messageId);
    if (message) {
      navigator.clipboard.writeText(message.content);
    }
    
    if (onCopyMessage) {
      onCopyMessage(messageId);
    }
  };
  
  // Handle conversation selection
  const handleSelectConversation = (conversation: ConversationSession) => {
    setStateMessages(conversation.messages);
    
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
  
  // Handle export conversations
  const handleExportConversations = (format: 'json' | 'text' | 'csv', conversationIds?: string[]) => {
    if (onExportConversations) {
      return onExportConversations(format, conversationIds);
    }
    return '';
  };
  
  // Handle clear history
  const handleClearHistory = () => {
    if (onClearHistory) {
      onClearHistory();
    }
  };
  
  // Handle voice recording start
  const handleVoiceRecordStart = () => {
    setIsRecording(true);
    setIsVoiceInputVisible(true);
  };
  
  // Handle voice recording end
  const handleVoiceRecordEnd = () => {
    setIsRecording(false);
    setIsVoiceInputVisible(false);
  };
  
  // Handle typing indicator
  const handleTyping = (isTyping: boolean) => {
    if (onTyping) {
      onTyping(isTyping);
    }
  };
  
  // Toggle history visibility
  const toggleHistory = () => {
    setIsHistoryVisible(!isHistoryVisible);
  };
  
  // Toggle voice input visibility
  const toggleVoiceInput = () => {
    setIsVoiceInputVisible(!isVoiceInputVisible);
    if (!isVoiceInputVisible) {
      setIsRecording(true);
    } else {
      setIsRecording(false);
    }
  };
  
  // Generate conversation title
  const generateConversationTitle = (): string => {
    if (stateMessages.length === 0) return 'New Conversation';
    
    const firstUserMessage = stateMessages.find(msg => msg.role === 'user');
    if (firstUserMessage) {
      // Use first few words of the first user message as title
      const words = firstUserMessage.content.split(' ');
      const titleWords = words.slice(0, 5).join(' ');
      return titleWords + (words.length > 5 ? '...' : '');
    }
    
    return 'Conversation';
  };
  
  return (
    <div 
      className={`karen-chat-interface ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: theme.colors.background,
        color: theme.colors.text,
        fontFamily: theme.typography.fontFamily,
        borderRadius: theme.borderRadius,
        overflow: 'hidden',
        position: 'relative'
      }}
    >
      {/* Chat header */}
      <div 
        className="karen-chat-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: theme.spacing.md,
          backgroundColor: theme.colors.surface,
          borderBottom: `1px solid ${theme.colors.border}`,
          boxShadow: theme.shadows.sm
        }}
      >
        <div 
          className="karen-chat-title"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: theme.spacing.sm
          }}
        >
          <h2 
            className="karen-chat-title-text"
            style={{
              margin: 0,
              fontSize: theme.typography.fontSize.lg,
              fontWeight: theme.typography.fontWeight.bold
            }}
          >
            {generateConversationTitle()}
          </h2>
        </div>
        
        <div 
          className="karen-chat-actions"
          style={{
            display: 'flex',
            gap: theme.spacing.sm
          }}
        >
          {showHistory && (
            <button
              onClick={toggleHistory}
              className="karen-history-toggle"
              aria-label="Toggle conversation history"
              style={{
                backgroundColor: 'transparent',
                color: theme.colors.text,
                border: 'none',
                borderRadius: theme.borderRadius,
                padding: theme.spacing.sm,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1rem',
                transition: 'color 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = theme.colors.primary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = theme.colors.text;
              }}
            >
              📚
            </button>
          )}
          
          {showVoiceInput && (
            <button
              onClick={toggleVoiceInput}
              className="karen-voice-toggle"
              aria-label="Toggle voice input"
              style={{
                backgroundColor: 'transparent',
                color: isRecording ? theme.colors.error : theme.colors.text,
                border: 'none',
                borderRadius: theme.borderRadius,
                padding: theme.spacing.sm,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1rem',
                transition: 'color 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = theme.colors.primary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = isRecording ? theme.colors.error : theme.colors.text;
              }}
            >
              🎤
            </button>
          )}
        </div>
      </div>
      
      {/* Chat content */}
      <div 
        className="karen-chat-content"
        style={{
          display: 'flex',
          flex: 1,
          overflow: 'hidden'
        }}
      >
        {/* Conversation history */}
        {isHistoryVisible && (
          <div 
            className="karen-history-panel"
            style={{
              width: '300px',
              borderRight: `1px solid ${theme.colors.border}`,
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            <ConversationHistory
              theme={theme}
              conversations={conversations}
              currentConversationId={currentConversationId}
              onSelectConversation={handleSelectConversation}
              onDeleteConversation={handleDeleteConversation}
              onExportConversations={handleExportConversations}
              onClearHistory={handleClearHistory}
            />
          </div>
        )}
        
        {/* Messages area */}
        <div 
          className="karen-messages-container"
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}
        >
          {/* Messages */}
          <div 
            className="karen-messages"
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: theme.spacing.md
            }}
          >
            {stateMessages.length === 0 ? (
              <div 
                className="karen-empty-state"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: theme.colors.textSecondary,
                  padding: theme.spacing.lg,
                  textAlign: 'center'
                }}
              >
                <div 
                  className="karen-empty-icon"
                  style={{
                    fontSize: '3rem',
                    marginBottom: theme.spacing.md
                  }}
                >
                  💬
                </div>
                <h3 
                  className="karen-empty-title"
                  style={{
                    margin: `0 0 ${theme.spacing.md} 0`,
                    fontSize: theme.typography.fontSize.lg,
                    fontWeight: theme.typography.fontWeight.bold
                  }}
                >
                  No messages yet
                </h3>
                <p 
                  className="karen-empty-text"
                  style={{
                    margin: 0,
                    fontSize: theme.typography.fontSize.base,
                    lineHeight: '1.5'
                  }}
                >
                  Start a conversation by typing a message below
                </p>
              </div>
            ) : (
              stateMessages.map((message, index) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  theme={theme}
                  isLast={index === stateMessages.length - 1}
                  onCopyMessage={handleCopyMessage}
                  onRetryMessage={handleRetryMessage}
                  onDeleteMessage={handleDeleteMessage}
                  showTimestamp={showTimestamps}
                  showActions={showActions}
                  showAiData={showAiData}
                  showConfidence={showConfidence}
                  showKeywords={showKeywords}
                  showReasoning={showReasoning}
                />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
          
          {/* Voice input */}
          {isVoiceInputVisible && (
            <div 
              className="karen-voice-input-container"
              style={{
                padding: theme.spacing.md,
                borderTop: `1px solid ${theme.colors.border}`,
                backgroundColor: theme.colors.surface
              }}
            >
              <VoiceRecorder
                theme={theme}
                onRecordingComplete={handleVoiceMessage}
                isRecording={isRecording}
                onRecordingStart={handleVoiceRecordStart}
                onRecordingEnd={handleVoiceRecordEnd}
              />
            </div>
          )}
          
          {/* Message input */}
          <div 
            className="karen-input-container"
            style={{
              padding: theme.spacing.md,
              borderTop: `1px solid ${theme.colors.border}`,
              backgroundColor: theme.colors.surface
            }}
          >
            <MessageInput
              theme={theme}
              onSendMessage={handleSendMessage}
              onVoiceInput={toggleVoiceInput}
              onTyping={handleTyping}
              placeholder={placeholder}
              disabled={disabled}
              maxLength={maxLength}
              showCharacterCount={showCharacterCount}
              showSendButton={showSendButton}
              showVoiceButton={showVoiceButton && !isVoiceInputVisible}
              showAttachButton={showAttachButton}
              allowAttachments={allowAttachments}
              allowVoiceInput={allowVoiceInput}
              autoFocus={autoFocus}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;