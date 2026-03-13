import React, { useState, useEffect, useRef } from 'react';
import { SharedChatInterface } from './ChatInterface';
import { SharedMessageInput } from './MessageInput';
import { SharedMessageBubble } from './MessageBubble';
import { SharedVoiceRecorder } from './VoiceRecorder';
import { SharedConversationHistory } from './ConversationHistory';
import {
  Theme,
  ChatMessage,
  KarenSettings,
  ComponentConfig,
  ChatState,
  MessageInputOptions,
  VoiceRecorderOptions,
  ConversationHistoryOptions
} from '../abstractions/types';
import { IChatService, IThemeManager } from '../abstractions/interfaces';

interface ChatInterfaceProps {
  containerId: string;
  chatService: IChatService;
  themeManager: IThemeManager;
  config: ComponentConfig;
  options?: {
    enableVoice?: boolean;
    enableExport?: boolean;
    enableSearch?: boolean;
    maxMessages?: number;
    autoSave?: boolean;
    placeholder?: string;
  };
  className?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  containerId,
  chatService,
  themeManager,
  config,
  options = {},
  className = ''
}) => {
  const [theme, setTheme] = useState<Theme>(themeManager.currentTheme);
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    isRecording: false,
    input: '',
    settings: {
      memoryDepth: 'medium',
      personalityTone: 'friendly',
      personalityVerbosity: 'balanced',
      personalFacts: [],
      notifications: {
        enabled: true,
        alertOnNewInsights: true,
        alertOnSummaryReady: true
      },
      ttsVoiceURI: null,
      customPersonaInstructions: '',
      temperatureUnit: 'C',
      weatherService: 'wttr_in',
      weatherApiKey: null,
      defaultWeatherLocation: null,
      activeListenMode: false
    }
  });

  const chatInterfaceRef = useRef<SharedChatInterface | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize chat interface
  useEffect(() => {
    const chatInterface = new SharedChatInterface(
      containerId,
      chatService,
      themeManager,
      config,
      options
    );

    chatInterfaceRef.current = chatInterface;

    // Set up theme change listener
    themeManager.onThemeChanged((newTheme: Theme) => {
      setTheme(newTheme);
    });

    // Set up message listeners
    chatInterface.onMessageSent((message) => {
      setChatState((prev: ChatState) => ({
        ...prev,
        messages: [...prev.messages, message]
      }));
    });

    chatInterface.onMessageReceived((message) => {
      setChatState((prev: ChatState) => ({
        ...prev,
        messages: [...prev.messages, message],
        isLoading: false
      }));
    });

    chatInterface.onRecordingStateChanged((isRecording) => {
      setChatState((prev: ChatState) => ({
        ...prev,
        isRecording
      }));
    });

    // Load initial state
    setChatState(chatInterface.getState());

    return () => {
      chatInterface.destroy();
    };
  }, [containerId, chatService, themeManager, config, options]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatState.messages]);

  const handleSendMessage = (content: string, isVoice: boolean = false) => {
    if (chatInterfaceRef.current) {
      setChatState((prev: ChatState) => ({ ...prev, isLoading: true }));
      chatInterfaceRef.current.sendMessage(content, isVoice);
    }
  };

  const handleVoiceToggle = async () => {
    if (chatInterfaceRef.current) {
      await chatInterfaceRef.current.toggleRecording();
    }
  };

  const handleClearMessages = () => {
    if (chatInterfaceRef.current) {
      chatInterfaceRef.current.clearMessages();
      setChatState((prev: ChatState) => ({ ...prev, messages: [] }));
    }
  };

  const handleExportMessages = (format: 'text' | 'json') => {
    if (chatInterfaceRef.current) {
      return chatInterfaceRef.current.exportMessages(format);
    }
    return '';
  };

  return (
    <div 
      className={`karen-chat-interface ${className}`}
      role="region"
      aria-label="Chat interface"
      style={{
        backgroundColor: theme.colors.background,
        color: theme.colors.text,
        fontFamily: theme.typography.fontFamily,
        borderRadius: theme.borderRadius
      }}
    >
      {/* Chat Header */}
      <div 
        className="karen-chat-header"
        style={{
          backgroundColor: theme.colors.primary,
          color: '#ffffff',
          padding: theme.spacing.md,
          borderBottom: `1px solid ${theme.colors.border}`
        }}
      >
        <h2 
          className="karen-chat-title"
          style={{
            margin: 0,
            fontSize: theme.typography.fontSize.lg,
            fontWeight: theme.typography.fontWeight.bold
          }}
        >
          AI Karen Chat
        </h2>
        <div className="karen-chat-status">
          {chatState.isLoading ? (
            <span className="karen-chat-loading">Processing...</span>
          ) : (
            <span className="karen-chat-ready">Ready</span>
          )}
        </div>
      </div>

      {/* Messages Container */}
      <div 
        className="karen-messages-container"
        style={{
          height: '400px',
          overflowY: 'auto',
          padding: theme.spacing.md
        }}
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {chatState.messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            theme={theme}
            options={{
              showTimestamp: true,
              showAiData: true,
              enableTts: true,
              maxContentLength: 0,
              enableMarkdown: true,
              showAvatar: true,
              compactMode: false
            }}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div 
        className="karen-input-area"
        style={{
          padding: theme.spacing.md,
          borderTop: `1px solid ${theme.colors.border}`
        }}
      >
        <MessageInput
          theme={theme}
          options={{
            placeholder: (options as any).placeholder || 'Type your message...',
            maxLength: 10000,
            enableVoice: (options as any).enableVoice ?? true,
            enableAttachments: false,
            multiline: true,
            autoFocus: true,
            showCharacterCount: true,
            submitOnEnter: true,
            enableSuggestions: false
          }}
          callbacks={{
            onSubmit: handleSendMessage,
            onRecordingStart: handleVoiceToggle,
            onRecordingStop: handleVoiceToggle
          }}
        />
      </div>

      {/* Action Buttons */}
      <div 
        className="karen-chat-actions"
        style={{
          padding: theme.spacing.sm,
          display: 'flex',
          justifyContent: 'space-between',
          borderTop: `1px solid ${theme.colors.border}`
        }}
      >
        <div>
          {(options as any).enableVoice && (
            <button
              onClick={handleVoiceToggle}
              disabled={chatState.isLoading}
              className="karen-voice-button"
              aria-label={chatState.isRecording ? 'Stop recording' : 'Start voice input'}
              style={{
                backgroundColor: chatState.isRecording 
                  ? theme.colors.error 
                  : theme.colors.primary,
                color: 'white',
                border: 'none',
                borderRadius: theme.borderRadius,
                padding: theme.spacing.sm,
                cursor: chatState.isLoading ? 'not-allowed' : 'pointer',
                opacity: chatState.isLoading ? 0.5 : 1
              }}
            >
              {chatState.isRecording ? 'Stop Recording' : 'Voice Input'}
            </button>
          )}
        </div>
        <div>
          <button
            onClick={handleClearMessages}
            disabled={chatState.messages.length === 0}
            className="karen-clear-button"
            aria-label="Clear conversation"
            style={{
              backgroundColor: theme.colors.secondary,
              color: 'white',
              border: 'none',
              borderRadius: theme.borderRadius,
              padding: theme.spacing.sm,
              marginRight: theme.spacing.sm,
              cursor: chatState.messages.length === 0 ? 'not-allowed' : 'pointer',
              opacity: chatState.messages.length === 0 ? 0.5 : 1
            }}
          >
            Clear
          </button>
          {(options as any).enableExport && (
            <button
              onClick={() => handleExportMessages('json')}
              className="karen-export-button"
              aria-label="Export conversation"
              style={{
                backgroundColor: theme.colors.success,
                color: 'white',
                border: 'none',
                borderRadius: theme.borderRadius,
                padding: theme.spacing.sm,
                cursor: 'pointer'
              }}
            >
              Export
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Message Bubble Component
interface MessageBubbleProps {
  message: ChatMessage;
  theme: Theme;
  options?: {
    showTimestamp?: boolean;
    showAiData?: boolean;
    enableTts?: boolean;
    maxContentLength?: number;
    enableMarkdown?: boolean;
    showAvatar?: boolean;
    compactMode?: boolean;
  };
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  theme,
  options = {}
}) => {
  const messageBubble = new SharedMessageBubble({
    message,
    theme,
    options: {
      showTimestamp: true,
      showAiData: true,
      enableTts: true,
      maxContentLength: 0,
      enableMarkdown: true,
      showAvatar: true,
      compactMode: false,
      ...options
    }
  });

  const renderData = messageBubble.getRenderData();
  const isUser = message.role === 'user';

  return (
    <div 
      className={`karen-message-bubble karen-message-${message.role}`}
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: theme.spacing.md
      }}
    >
      <div
        style={{
          maxWidth: '70%',
          backgroundColor: isUser ? theme.colors.primary : theme.colors.surface,
          color: isUser ? '#ffffff' : theme.colors.text,
          borderRadius: theme.borderRadius,
          padding: theme.spacing.md,
          boxShadow: theme.shadows.sm
        }}
      >
        {/* Avatar */}
        {renderData.avatar.show && (
          <div 
            className="karen-message-avatar"
            style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: theme.spacing.sm
            }}
          >
            <div
              style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: isUser ? theme.colors.primary : theme.colors.secondary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: theme.spacing.sm
              }}
            >
              <span style={{ color: '#ffffff', fontSize: '12px' }}>
                {isUser ? 'U' : 'K'}
              </span>
            </div>
            <span style={{ fontWeight: 'bold', fontSize: '14px' }}>
              {isUser ? 'You' : 'Karen'}
            </span>
          </div>
        )}

        {/* Content */}
        <div 
          className="karen-message-content"
          style={{
            marginBottom: renderData.timestamp ? theme.spacing.sm : 0
          }}
          dangerouslySetInnerHTML={{ __html: renderData.content }}
        />

        {/* Timestamp */}
        {renderData.timestamp && (
          <div 
            className="karen-message-timestamp"
            style={{
              fontSize: '12px',
              opacity: 0.7,
              textAlign: isUser ? 'right' : 'left'
            }}
          >
            {renderData.timestamp}
          </div>
        )}

        {/* AI Data */}
        {renderData.aiData && (
          <div 
            className="karen-message-ai-data"
            style={{
              marginTop: theme.spacing.sm,
              paddingTop: theme.spacing.sm,
              borderTop: `1px solid ${theme.colors.border}`,
              fontSize: '12px'
            }}
          >
            {renderData.aiData.hasKeywords && renderData.aiData.keywords.length > 0 && (
              <div>
                <strong>Keywords:</strong> {renderData.aiData.keywords.join(', ')}
              </div>
            )}
            {renderData.aiData.hasInsights && (
              <div style={{ marginTop: theme.spacing.xs }}>
                <strong>Insights:</strong> {renderData.aiData.insights}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Message Input Component
interface MessageInputProps {
  theme: Theme;
  options?: MessageInputOptions;
  callbacks?: {
    onSubmit?: (message: string, isVoice?: boolean) => void;
    onChange?: (value: string) => void;
    onFocus?: () => void;
    onBlur?: () => void;
    onRecordingStart?: () => void;
    onRecordingStop?: () => void;
    onSuggestionSelect?: (suggestion: string) => void;
  };
}

const MessageInput: React.FC<MessageInputProps> = ({
  theme,
  options = {},
  callbacks = {}
}) => {
  const [messageInput] = useState(() => new SharedMessageInput(theme, options, callbacks));
  const [inputValue, setInputValue] = useState('');

  const renderData = messageInput.getRenderData();

  const handleSubmit = () => {
    if (inputValue.trim() && callbacks.onSubmit) {
      callbacks.onSubmit(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && options.submitOnEnter) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="karen-message-input-container">
      <textarea
        value={inputValue}
        onChange={(e) => {
          setInputValue(e.target.value);
          renderData.handlers.onChange(e.target.value);
        }}
        onKeyPress={handleKeyPress}
        onFocus={renderData.handlers.onFocus}
        onBlur={renderData.handlers.onBlur}
        placeholder={renderData.options.enableVoice 
          ? (renderData.state.isRecording ? 'Listening...' : 'Type your message or use voice input...')
          : 'Type your message...'
        }
        disabled={renderData.state.isLoading}
        className="karen-message-input"
        style={{
          ...renderData.styles,
          width: '100%',
          minHeight: '60px',
          resize: 'vertical',
          boxSizing: 'border-box'
        }}
        aria-label="Message input"
        aria-invalid={renderData.state.hasError}
      />
      
      {renderData.state.hasError && (
        <div 
          className="karen-input-error"
          style={{
            color: theme.colors.error,
            fontSize: '12px',
            marginTop: theme.spacing.xs
          }}
        >
          {renderData.state.errorMessage}
        </div>
      )}
      
      <div 
        className="karen-input-actions"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: theme.spacing.sm
        }}
      >
        {renderData.options.enableVoice && (
          <button
            onClick={renderData.handlers.onVoiceToggle}
            disabled={renderData.state.isLoading}
            className="karen-voice-button"
            aria-label={renderData.state.isRecording ? 'Stop recording' : 'Start voice input'}
            style={{
              backgroundColor: renderData.state.isRecording 
                ? theme.colors.error 
                : theme.colors.primary,
              color: 'white',
              border: 'none',
              borderRadius: theme.borderRadius,
              padding: theme.spacing.sm,
              cursor: renderData.state.isLoading ? 'not-allowed' : 'pointer',
              opacity: renderData.state.isLoading ? 0.5 : 1
            }}
          >
            {renderData.state.isRecording ? 'Stop' : 'Voice'}
          </button>
        )}
        
        <div>
          {renderData.options.showCharacterCount && (
            <span 
              className="karen-character-count"
              style={{
                fontSize: '12px',
                color: theme.colors.textSecondary,
                marginRight: theme.spacing.sm
              }}
            >
              {renderData.state.characterCount}/{renderData.options.maxLength}
            </span>
          )}
          
          <button
            onClick={handleSubmit}
            disabled={!inputValue.trim() || renderData.state.isLoading}
            className="karen-send-button"
            aria-label="Send message"
            style={{
              backgroundColor: theme.colors.primary,
              color: 'white',
              border: 'none',
              borderRadius: theme.borderRadius,
              padding: theme.spacing.sm,
              cursor: (!inputValue.trim() || renderData.state.isLoading) ? 'not-allowed' : 'pointer',
              opacity: (!inputValue.trim() || renderData.state.isLoading) ? 0.5 : 1
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;