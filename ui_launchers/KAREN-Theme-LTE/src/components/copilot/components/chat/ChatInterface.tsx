import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MessageInputComponent } from './MessageInputComponent';
import { ThemeProvider, useTheme, ThemeToggle } from './ThemeProvider';
import { useChat } from '../../hooks/useChat';
import { useStreamResponse } from '../../hooks/useStreamResponse';
import {
  KeyboardKeys,
  ModifierKeys,
  createReactKeyboardHandler,
  trapFocus,
  announceToScreenReader,
  useKeyboardFocus,
  useKeyboardShortcuts
} from '../../utils/keyboard-navigation';
import {
  ScreenReaderRoles,
  createLiveRegion,
  updateLiveRegion,
  addScreenReaderInstructions,
  createLandmarkRegion,
  markElementBusy,
  announceStateChange
} from '../../utils/screen-reader';

// Lazy load components
import { LazyMessageBubbleComponent } from '../lazy/chat/LazyMessageBubbleComponent';
import { LazyConversationHistoryComponent } from '../lazy/chat/LazyConversationHistoryComponent';
import { LazyMessageSearchComponent } from '../lazy/chat/LazyMessageSearchComponent';
import { LazyVoiceRecorderComponent } from '../lazy/chat/LazyVoiceRecorderComponent';
import { StreamedContent } from './StreamedContent';

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

interface ChatInterfaceProps {
  className?: string;
  initialMessages?: ChatMessage[];
  onSendMessage?: (message: string, attachments?: any[]) => void;
  onVoiceRecord?: () => void;
  onConversationSelect?: (conversation: Conversation) => void;
  onConversationDelete?: (conversationId: string) => void;
  onExport?: (conversation: Conversation) => void;
  showHistory?: boolean;
  showVoiceRecorder?: boolean;
  showTimestamps?: boolean;
  showActions?: boolean;
  showAiData?: boolean;
  showConfidence?: boolean;
  showKeywords?: boolean;
  showReasoning?: boolean;
  maxMessages?: number;
  theme?: Partial<Theme>;
  autoScroll?: boolean;
  placeholder?: string;
  disabled?: boolean;
  persistConversations?: boolean;
  autoCreateConversation?: boolean;
  showThemeToggle?: boolean;
}

interface ChatState {
  showHistoryPanel: boolean;
  showVoicePanel: boolean;
  showExportDialog: boolean;
  searchQuery: string;
  highlightedMessageId: string | null;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  className = '',
  initialMessages = [],
  onSendMessage,
  onVoiceRecord,
  onConversationSelect,
  onConversationDelete,
  onExport,
  showHistory = true,
  showVoiceRecorder = true,
  showTimestamps = true,
  showActions = true,
  showAiData = false,
  showConfidence = false,
  showKeywords = false,
  showReasoning = false,
  maxMessages = 100,
  theme: customTheme,
  autoScroll = true,
  placeholder = 'Type a message...',
  disabled = false,
  persistConversations = true,
  autoCreateConversation = true,
  showThemeToggle = true
}) => {
  const { theme } = useTheme();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatInterfaceRef = useRef<HTMLDivElement>(null);
  const historyPanelRef = useRef<HTMLDivElement>(null);
  const voicePanelRef = useRef<HTMLDivElement>(null);
  const exportDialogRef = useRef<HTMLDivElement>(null);
  
  // Use keyboard focus management
  const { saveFocus, restoreFocus } = useKeyboardFocus();
  
  // Use the chat hook for state management
  const {
    conversations,
    activeConversation,
    isLoading,
    error,
    messages,
    isTyping,
    createConversation,
    selectConversation,
    deleteConversation,
    updateConversation,
    sendMessage,
    addMessage,
    updateMessage,
    deleteMessage,
    searchConversations,
    exportConversation,
    importConversation,
    setTyping
  } = useChat({
    autoCreateConversation,
    persistConversations
  });
  
  // Use the streaming response hook
  const {
    response: streamingResponse,
    isLoading: isStreaming,
    error: streamingError,
    startStream,
    resetStream
  } = useStreamResponse();

  // Initialize state
  const [state, setState] = useState<ChatState>({
    showHistoryPanel: false,
    showVoicePanel: false,
    showExportDialog: false,
    searchQuery: '',
    highlightedMessageId: null
  });

  // Create live regions for dynamic content
  useEffect(() => {
    // Create live regions for important dynamic content
    createLiveRegion('chat-messages-live-region', 'polite');
    createLiveRegion('chat-status-live-region', 'assertive');
    createLiveRegion('chat-error-live-region', 'assertive');
    
    // Add screen reader instructions to the chat interface
    if (chatInterfaceRef.current) {
      addScreenReaderInstructions(
        chatInterfaceRef.current,
        'Chat interface. Use Tab to navigate between elements, Enter to activate buttons, and Escape to close panels. Press ? for keyboard shortcuts help.'
      );
    }
    
    // Create landmark regions
    if (chatInterfaceRef.current) {
      createLandmarkRegion(chatInterfaceRef.current, 'main', 'Chat interface');
    }
  }, []);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Handle sending a message
  const handleSendMessage = (message: string, attachments?: any[]) => {
    if (!message.trim() && (!attachments || attachments.length === 0)) return;

    // Reset any existing stream
    resetStream();

    // Use the hook's sendMessage function
    sendMessage(message, 'user');

    // Call parent handler if provided
    if (onSendMessage) {
      onSendMessage(message, attachments);
    }
  };

  // Handle voice recording
  const handleVoiceRecord = () => {
    setState(prev => ({
      ...prev,
      showVoicePanel: !prev.showVoicePanel
    }));

    if (onVoiceRecord) {
      onVoiceRecord();
    }
  };

  // Handle conversation selection
  const handleConversationSelect = (conversation: Conversation) => {
    selectConversation(conversation.id);
    setState(prev => ({
      ...prev,
      showHistoryPanel: false
    }));

    if (onConversationSelect) {
      onConversationSelect(conversation);
    }
  };

  // Handle conversation deletion
  const handleConversationDelete = (conversationId: string) => {
    deleteConversation(conversationId);

    if (onConversationDelete) {
      onConversationDelete(conversationId);
    }
  };

  // Handle conversation export
  const handleExport = (conversation: Conversation) => {
    const exportedData = exportConversation(conversation.id);
    
    if (exportedData) {
      // Create a download link
      const blob = new Blob([exportedData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-${conversation.id}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    setState(prev => ({
      ...prev,
      showExportDialog: false
    }));

    if (onExport) {
      onExport(conversation);
    }
  };

  // Handle search query change
  const handleSearchChange = (query: string) => {
    setState(prev => ({
      ...prev,
      searchQuery: query
    }));
  };

  // Toggle history panel
  const toggleHistoryPanel = () => {
    setState(prev => ({
      ...prev,
      showHistoryPanel: !prev.showHistoryPanel
    }));
  };

  // Close voice panel
  const closeVoicePanel = () => {
    setState(prev => ({
      ...prev,
      showVoicePanel: false
    }));
  };

  // Close export dialog
  const closeExportDialog = () => {
    setState(prev => ({
      ...prev,
      showExportDialog: false
    }));
  };

  // Handle voice recording complete
  const handleVoiceRecordingComplete = (audioBlob: Blob, transcript: string) => {
    setState(prev => ({
      ...prev,
      showVoicePanel: false
    }));

    // Send the transcript as a message
    if (transcript.trim()) {
      handleSendMessage(transcript);
    }
  };

  // Handle voice recording cancel
  const handleVoiceRecordingCancel = () => {
    setState(prev => ({
      ...prev,
      showVoicePanel: false
    }));
  };

  // Copy message to clipboard
  const handleCopyMessage = (messageId: string) => {
    const message = messages.find(m => m.id === messageId);
    if (message) {
      navigator.clipboard.writeText(message.content);
    }
  };

  // Retry message
  const handleRetryMessage = (messageId: string) => {
    const message = messages.find(m => m.id === messageId);
    if (message && message.role === 'user') {
      handleSendMessage(message.content);
    }
  };

  // Delete message
  const handleDeleteMessage = (messageId: string) => {
    deleteMessage(messageId);
  };

  // Highlight message in conversation
  const handleHighlightMessage = (messageId: string) => {
    setState(prev => ({
      ...prev,
      highlightedMessageId: messageId
    }));
    
    // Scroll to the highlighted message
    const messageElement = document.getElementById(`message-${messageId}`);
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      
      // Add a temporary highlight effect
      messageElement.classList.add('copilot-message-highlighted');
      setTimeout(() => {
        messageElement.classList.remove('copilot-message-highlighted');
      }, 2000);
    }
  };

  // Handle file input
  const handleFileInput = (files: any[]) => {
    if (files.length > 0) {
      // For now, just send a message about the files
      // In a real implementation, you would upload and attach the files
      const fileNames = files.map(file => file.name).join(', ');
      handleSendMessage(`I've attached the following files: ${fileNames}`);
    }
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (autoScroll) {
      scrollToBottom();
    }
  }, [messages, autoScroll]);

  // Limit messages to maxMessages
  useEffect(() => {
    if (messages.length > maxMessages) {
      // This is handled by the hook
    }
  }, [messages, maxMessages]);

  // Setup keyboard shortcuts
  useKeyboardShortcuts([
    {
      keys: [KeyboardKeys.ESCAPE],
      callback: () => {
        if (state.showHistoryPanel || state.showVoicePanel || state.showExportDialog) {
          setState(prev => ({
            ...prev,
            showHistoryPanel: false,
            showVoicePanel: false,
            showExportDialog: false
          }));
          announceToScreenReader('All panels closed', 'assertive');
          restoreFocus();
        }
      },
      description: 'Close all open panels'
    },
    {
      keys: ['h'],
      modifiers: [ModifierKeys.CONTROL],
      callback: () => {
        if (showHistory) {
          toggleHistoryPanel();
          announceToScreenReader(
            state.showHistoryPanel ? 'Conversation history closed' : 'Conversation history opened',
            'assertive'
          );
        }
      },
      description: 'Toggle conversation history panel'
    },
    {
      keys: ['k'],
      modifiers: [ModifierKeys.CONTROL],
      callback: () => {
        if (showVoiceRecorder) {
          handleVoiceRecord();
          announceToScreenReader(
            state.showVoicePanel ? 'Voice recorder closed' : 'Voice recorder opened',
            'assertive'
          );
        }
      },
      description: 'Toggle voice recorder panel'
    },
    {
      keys: ['e'],
      modifiers: [ModifierKeys.CONTROL],
      callback: () => {
        if (onExport) {
          setState(prev => ({ ...prev, showExportDialog: true }));
          announceToScreenReader('Export dialog opened', 'assertive');
        }
      },
      description: 'Open export dialog'
    },
    {
      keys: ['f'],
      modifiers: [ModifierKeys.CONTROL],
      callback: () => {
        // Toggle message search
        const searchButton = document.querySelector('.copilot-message-search button');
        if (searchButton instanceof HTMLElement) {
          searchButton.click();
          announceToScreenReader('Message search toggled', 'assertive');
        }
      },
      description: 'Toggle message search'
    },
    {
      keys: ['/'],
      callback: () => {
        // Focus on message input
        const messageInput = document.querySelector('.copilot-message-input textarea, .copilot-message-input input');
        if (messageInput instanceof HTMLElement) {
          messageInput.focus();
          announceToScreenReader('Message input focused', 'assertive');
        }
      },
      description: 'Focus on message input'
    },
    {
      keys: ['?'],
      callback: () => {
        announceToScreenReader(
          'Keyboard shortcuts: Ctrl+H for history, Ctrl+K for voice recorder, Ctrl+E for export, Ctrl+F for search, / to focus input, Escape to close panels',
          'assertive'
        );
      },
      description: 'Announce keyboard shortcuts'
    }
  ]);

  // Setup focus trapping for modal panels
  useEffect(() => {
    let removeTrap: (() => void) | undefined;
    
    if (state.showHistoryPanel && historyPanelRef.current) {
      saveFocus();
      removeTrap = trapFocus(historyPanelRef.current);
    } else if (state.showVoicePanel && voicePanelRef.current) {
      saveFocus();
      removeTrap = trapFocus(voicePanelRef.current);
    } else if (state.showExportDialog && exportDialogRef.current) {
      saveFocus();
      removeTrap = trapFocus(exportDialogRef.current);
    }
    
    return () => {
      if (removeTrap) {
        removeTrap();
      }
    };
  }, [state.showHistoryPanel, state.showVoicePanel, state.showExportDialog, saveFocus]);

  // Filter conversations based on search query
  const filteredConversations = state.searchQuery 
    ? searchConversations(state.searchQuery)
    : conversations;

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    width: '100%',
    backgroundColor: theme.colors.background,
    color: theme.colors.text,
    fontFamily: theme.typography.fontFamily,
    borderRadius: theme.borderRadius,
    overflow: 'hidden',
    position: 'relative'
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    borderBottom: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.surface
  };

  const messagesContainerStyle: React.CSSProperties = {
    flex: 1,
    overflowY: 'auto',
    padding: theme.spacing.md,
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing.sm
  };

  const inputContainerStyle: React.CSSProperties = {
    padding: theme.spacing.md,
    borderTop: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.surface
  };

  const historyPanelStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    width: '350px',
    backgroundColor: theme.colors.surface,
    borderLeft: `1px solid ${theme.colors.border}`,
    boxShadow: theme.shadows.lg,
    zIndex: 10,
    transform: state.showHistoryPanel ? 'translateX(0)' : 'translateX(100%)',
    transition: 'transform 0.3s ease'
  };

  const voicePanelStyle: React.CSSProperties = {
    position: 'absolute',
    bottom: '80px',
    right: '20px',
    width: '400px',
    backgroundColor: theme.colors.surface,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    boxShadow: theme.shadows.lg,
    zIndex: 20,
    transform: state.showVoicePanel ? 'scale(1)' : 'scale(0.9)',
    opacity: state.showVoicePanel ? 1 : 0,
    transition: 'all 0.3s ease',
    pointerEvents: state.showVoicePanel ? 'auto' : 'none'
  };

  const exportDialogStyle: React.CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '500px',
    maxWidth: '90vw',
    backgroundColor: theme.colors.surface,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    boxShadow: theme.shadows.lg,
    zIndex: 30,
    padding: theme.spacing.lg,
    display: state.showExportDialog ? 'block' : 'none'
  };

  const overlayStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 5,
    display: (state.showHistoryPanel || state.showVoicePanel || state.showExportDialog) ? 'block' : 'none'
  };

  return (
    <div
      ref={chatInterfaceRef}
      className={`copilot-chat-interface ${className}`}
      style={containerStyle}
      role="main"
      aria-label="Chat interface"
      aria-live="polite"
      onKeyDown={createReactKeyboardHandler({
        [KeyboardKeys.TAB]: (e) => {
          // Tab navigation is handled by the browser, but we can add custom behavior
          if (e.shiftKey) {
            // Shift+Tab navigation
            console.log('Shift+Tab navigation');
          }
        },
        [KeyboardKeys.FOCUS_FIRST]: (e) => {
          // Focus first interactive element
          const firstFocusable = chatInterfaceRef.current?.querySelector(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          ) as HTMLElement;
          if (firstFocusable) {
            firstFocusable.focus();
            announceToScreenReader('Focused on first interactive element', 'assertive');
          }
        },
        [KeyboardKeys.FOCUS_LAST]: (e) => {
          // Focus last interactive element
          const focusableElements = chatInterfaceRef.current?.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          ) as NodeListOf<HTMLElement>;
          if (focusableElements && focusableElements.length > 0) {
            const lastElement = focusableElements[focusableElements.length - 1];
            if (lastElement) {
              lastElement.focus();
              announceToScreenReader('Focused on last interactive element', 'assertive');
            }
          }
        }
      })}
    >
      {/* Header */}
      <header className="copilot-header" style={headerStyle} role="banner" aria-label="Chat header">
        <div className="copilot-header-title" style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
          <h2 style={{ margin: 0, fontSize: theme.typography.fontSize.lg }} tabIndex={0} id="chat-title">
            {activeConversation?.title || 'New Conversation'}
          </h2>
          {activeConversation?.agent && (
            <span
              className="copilot-agent-badge"
              style={{
                backgroundColor: `${theme.colors.primary}20`,
                color: theme.colors.primary,
                padding: `2px ${theme.spacing.sm}`,
                borderRadius: '12px',
                fontSize: theme.typography.fontSize.xs
              }}
              aria-label={`Agent: ${activeConversation.agent}`}
            >
              🤖 {activeConversation.agent}
            </span>
          )}
        </div>
        
        {showThemeToggle && <ThemeToggle />}
      </header>

      {/* Overlay for modals */}
      <div 
        className="copilot-overlay" 
        style={overlayStyle}
        onClick={() => {
          setState(prev => ({
            ...prev,
            showHistoryPanel: false,
            showVoicePanel: false,
            showExportDialog: false
          }));
        }}
      />

      {/* Messages container */}
      <main
        className="copilot-messages-container"
        style={messagesContainerStyle}
        role="region"
        aria-label="Messages"
        aria-describedby="messages-instructions"
        tabIndex={0}
        onKeyDown={(e) => {
          // Keyboard navigation for messages
          if (e.key === 'PageDown' || e.key === 'End') {
            e.preventDefault();
            scrollToBottom();
          }
        }}
      >
        {/* Screen reader instructions */}
        <div id="messages-instructions" style={{ display: 'none' }}>
          Use Tab to navigate between messages, Enter to select actions, and Page Down to scroll to the bottom.
        </div>
        {/* Message search */}
        <LazyMessageSearchComponent
          theme={theme}
          messages={messages}
          onHighlightMessage={handleHighlightMessage}
        />
        {isLoading ? (
          <div
            className="copilot-loading-state"
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: theme.colors.textSecondary
            }}
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
              aria-hidden="true"
            />
            <p>Loading conversations...</p>
          </div>
        ) : error ? (
          <div
            className="copilot-error-state"
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: theme.colors.error
            }}
            role="alert"
            aria-live="assertive"
          >
            <div style={{ fontSize: '2rem', marginBottom: theme.spacing.md }} aria-hidden="true">⚠️</div>
            <h3 style={{ margin: 0, marginBottom: theme.spacing.sm }}>Error</h3>
            <p>{error}</p>
          </div>
        ) : messages.length === 0 ? (
          <div
            className="copilot-empty-state"
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: theme.colors.textSecondary
            }}
            aria-label="No messages"
          >
            <div style={{ fontSize: '3rem', marginBottom: theme.spacing.md }} aria-hidden="true">💬</div>
            <h3 style={{ margin: 0, marginBottom: theme.spacing.sm }}>No messages yet</h3>
            <p>Start a conversation by typing a message below.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <LazyMessageBubbleComponent
              key={message.id}
              message={message}
              theme={theme}
              showTimestamp={showTimestamps}
              showActions={showActions}
              showAiData={showAiData}
              showConfidence={showConfidence}
              showKeywords={showKeywords}
              showReasoning={showReasoning}
              isHighlighted={state.highlightedMessageId === message.id}
              onCopyMessage={handleCopyMessage}
              onRetryMessage={handleRetryMessage}
              onDeleteMessage={handleDeleteMessage}
              ariaPosInSet={index + 1}
              ariaSetSize={messages.length}
            />
          ))
        )}
        
        {/* Typing indicator */}
        {isTyping && (
          <div
            className="copilot-typing-indicator"
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: theme.spacing.sm,
              backgroundColor: `${theme.colors.primary}10`,
              borderRadius: theme.borderRadius,
              maxWidth: '100px'
            }}
            role="status"
            aria-live="polite"
            aria-label="Assistant is typing"
            aria-busy="true"
          >
            <div style={{ display: 'flex', alignItems: 'center' }} aria-hidden="true">
              <span
                className="copilot-typing-dot"
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: theme.colors.primary,
                  margin: '0 2px',
                  animation: 'typing 1.4s infinite'
                }}
              />
              <span
                className="copilot-typing-dot"
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: theme.colors.primary,
                  margin: '0 2px',
                  animation: 'typing 1.4s infinite 0.2s'
                }}
              />
              <span
                className="copilot-typing-dot"
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: theme.colors.primary,
                  margin: '0 2px',
                  animation: 'typing 1.4s infinite 0.4s'
                }}
              />
            </div>
          </div>
        )}
        
        {/* Invisible element for scrolling to bottom */}
        <div ref={messagesEndRef} aria-hidden="true" />
      </main>

      {/* Input container */}
      <div className="copilot-input-container" style={inputContainerStyle} role="form" aria-label="Message input" aria-labelledby="chat-title">
        <MessageInputComponent
          theme={theme}
          placeholder={placeholder}
          disabled={disabled}
          onSendMessage={handleSendMessage}
          onVoiceRecord={handleVoiceRecord}
          onAttachFiles={handleFileInput}
          onTyping={setTyping}
        />
      </div>

      {/* History panel */}
      {showHistory && (
        <div ref={historyPanelRef} className="copilot-history-panel" style={historyPanelStyle}>
          <div 
            className="copilot-history-header"
            style={{
              padding: theme.spacing.md,
              borderBottom: `1px solid ${theme.colors.border}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <h3 style={{ margin: 0 }}>Conversation History</h3>
            <button 
              onClick={toggleHistoryPanel}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '1.2rem',
                cursor: 'pointer',
                color: theme.colors.textSecondary
              }}
            >
              ✕
            </button>
          </div>
          
          <LazyConversationHistoryComponent
            theme={theme}
            conversations={filteredConversations}
            selectedConversationId={activeConversation?.id}
            onSelectConversation={handleConversationSelect}
            onDeleteConversation={handleConversationDelete}
            onRenameConversation={(id, title) => updateConversation(id, { title })}
            onExportConversation={handleExport}
            onCreateNewConversation={() => {
              const newConversation = createConversation();
              setState(prev => ({
                ...prev,
                showHistoryPanel: false
              }));
            }}
            onSearchConversations={handleSearchChange}
            isLoading={isLoading}
          />
        </div>
      )}

      {/* Voice recorder panel */}
      {showVoiceRecorder && (
        <div ref={voicePanelRef} className="copilot-voice-panel" style={voicePanelStyle}>
          <LazyVoiceRecorderComponent
            theme={theme}
            onRecordingComplete={handleVoiceRecordingComplete}
            onRecordingCancel={handleVoiceRecordingCancel}
            onError={(error) => console.error('Voice recording error:', error)}
          />
        </div>
      )}

      {/* Export dialog */}
      <div ref={exportDialogRef} className="copilot-export-dialog" style={exportDialogStyle}>
        <h3 style={{ marginTop: 0, marginBottom: theme.spacing.md }}>Export Conversation</h3>
        <p>Select export format:</p>
        <div style={{ display: 'flex', gap: theme.spacing.sm, marginBottom: theme.spacing.md }}>
          <button 
            style={{
              padding: theme.spacing.sm,
              backgroundColor: theme.colors.primary,
              color: 'white',
              border: 'none',
              borderRadius: theme.borderRadius,
              cursor: 'pointer'
            }}
          >
            JSON
          </button>
          <button 
            style={{
              padding: theme.spacing.sm,
              backgroundColor: theme.colors.surface,
              color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              cursor: 'pointer'
            }}
          >
            Text
          </button>
          <button 
            style={{
              padding: theme.spacing.sm,
              backgroundColor: theme.colors.surface,
              color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              cursor: 'pointer'
            }}
          >
            Markdown
          </button>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: theme.spacing.sm }}>
          <button 
            onClick={closeExportDialog}
            style={{
              padding: theme.spacing.sm,
              backgroundColor: theme.colors.surface,
              color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button 
            onClick={() => activeConversation && handleExport(activeConversation)}
            style={{
              padding: theme.spacing.sm,
              backgroundColor: theme.colors.primary,
              color: 'white',
              border: 'none',
              borderRadius: theme.borderRadius,
              cursor: 'pointer'
            }}
          >
            Export
          </button>
        </div>
      </div>

      {/* Floating action button for history */}
      {showHistory && (
        <button
          onClick={toggleHistoryPanel}
          style={{
            position: 'absolute',
            top: theme.spacing.md,
            right: theme.spacing.md,
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: theme.colors.primary,
            color: 'white',
            border: 'none',
            boxShadow: theme.shadows.md,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.2rem',
            zIndex: 4
          }}
          aria-label={state.showHistoryPanel ? "Close conversation history" : "Open conversation history"}
          aria-expanded={state.showHistoryPanel}
          aria-controls="history-panel"
          title="Toggle conversation history (Ctrl+H)"
          accessKey="h"
          tabIndex={0}
        >
          📋
        </button>
      )}

      <style>{`
        @keyframes typing {
          0%, 60%, 100% {
            transform: translateY(0);
          }
          30% {
            transform: translateY(-10px);
          }
        }
        
        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
          .copilot-chat-interface {
            height: 100vh;
            width: 100vw;
            border-radius: 0;
          }
          
          .copilot-history-panel {
            width: 100%;
            max-width: 400px;
          }
          
          .copilot-voice-panel {
            width: calc(100% - 40px);
            max-width: 400px;
            right: 20px;
            bottom: 60px;
          }
          
          .copilot-export-dialog {
            width: calc(100% - 40px);
            max-width: 500px;
          }
        }
        
        @media (max-width: 480px) {
          .copilot-header {
            padding: 8px 12px;
          }
          
          .copilot-messages-container {
            padding: 12px;
          }
          
          .copilot-input-container {
            padding: 12px;
          }
          
          .copilot-history-panel {
            width: 100%;
            max-width: 100%;
          }
          
          .copilot-voice-panel {
            width: calc(100% - 20px);
            right: 10px;
            bottom: 50px;
          }
          
          .copilot-export-dialog {
            width: calc(100% - 20px);
            padding: 16px;
          }
          
          .copilot-typing-indicator {
            max-width: 80px;
          }
        }
        
        @media (min-width: 1200px) {
          .copilot-chat-interface {
            max-width: 1200px;
            margin: 0 auto;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
          }
          
          .copilot-history-panel {
            width: 400px;
          }
          
          .copilot-voice-panel {
            width: 450px;
          }
          
          .copilot-export-dialog {
            width: 600px;
          }
        }
      }
      
      .copilot-message-highlighted {
        animation: pulse 2s;
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
      `}</style>
    </div>
  );
};

export default ChatInterface;