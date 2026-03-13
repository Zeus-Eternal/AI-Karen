import React, { useState, useEffect, useCallback } from 'react';

// Import components
import { ChatInterface } from './ChatInterfaceComponent';
import { ThemeProvider, useTheme } from './ThemeManagement';
import { AccessibilityEnhancements, useAnnouncer } from './AccessibilityEnhancements';
import { ResponsiveDesign, useResponsive } from './ResponsiveDesign';

// Type definitions
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

// Demo component
const ChatInterfaceDemo: React.FC = () => {
  const { theme } = useTheme();
  const { announce } = useAnnouncer();
  const { isMobile, isTablet, isDesktop } = useResponsive();
  
  const [messages, setMessages] = useState<ChatMessage[]>(sampleMessages);
  const [conversations, setConversations] = useState<ConversationSession[]>(sampleConversations);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [showAiData, setShowAiData] = useState<boolean>(false);
  const [showTimestamps, setShowTimestamps] = useState<boolean>(true);
  const [showActions, setShowActions] = useState<boolean>(true);
  const [showHistory, setShowHistory] = useState<boolean>(true);
  const [showVoiceInput, setShowVoiceInput] = useState<boolean>(true);
  const [showCharacterCount, setShowCharacterCount] = useState<boolean>(true);
  const [showSendButton, setShowSendButton] = useState<boolean>(true);
  const [showVoiceButton, setShowVoiceButton] = useState<boolean>(true);
  const [showAttachButton, setShowAttachButton] = useState<boolean>(true);
  const [allowAttachments, setAllowAttachments] = useState<boolean>(true);
  const [allowVoiceInput, setAllowVoiceInput] = useState<boolean>(true);
  const [autoFocus, setAutoFocus] = useState<boolean>(true);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  
  // Handle sending a message
  const handleSendMessage = useCallback((message: string, attachments?: any[]) => {
    if (message.trim() || (attachments && attachments.length > 0)) {
      const newMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date(),
        attachments
      };
      
      setMessages(prev => [...prev, newMessage]);
      
      // Simulate AI response
      setTimeout(() => {
        const aiResponse: ChatMessage = {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: `I received your message: "${message}". This is a simulated response from the AI assistant.`,
          timestamp: new Date(),
          aiData: {
            confidence: 0.9 + Math.random() * 0.1,
            keywords: ['response', 'simulated', 'ai'],
            reasoning: 'This is a simulated AI response for demonstration purposes.'
          }
        };
        
        setMessages(prev => [...prev, aiResponse]);
        setIsTyping(false);
        announce('AI response received');
      }, 1000 + Math.random() * 2000);
      
      setIsTyping(true);
      announce('Message sent');
    }
  }, [announce]);
  
  // Handle voice message
  const handleVoiceMessage = useCallback((message: string) => {
    if (message.trim()) {
      const newMessage: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, newMessage]);
      announce('Voice message sent');
    }
  }, [announce]);
  
  // Handle retry message
  const handleRetryMessage = useCallback((messageId: string) => {
    const message = messages.find(msg => msg.id === messageId);
    if (message && message.role === 'assistant') {
      // Remove the message and the user message that preceded it
      const userMessageIndex = messages.findIndex(msg => msg.id === messageId) - 1;
      if (userMessageIndex >= 0) {
        const userMessage = messages[userMessageIndex];
        
        setMessages(prev => 
          prev.filter(msg => msg.id !== messageId && msg.id !== userMessage.id)
        );
        
        // Resend the user message to get a new response
        handleSendMessage(userMessage.content);
        announce('Message retried');
      }
    }
  }, [messages, handleSendMessage, announce]);
  
  // Handle delete message
  const handleDeleteMessage = useCallback((messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
    announce('Message deleted');
  }, [announce]);
  
  // Handle copy message
  const handleCopyMessage = useCallback((messageId: string) => {
    const message = messages.find(msg => msg.id === messageId);
    if (message) {
      navigator.clipboard.writeText(message.content);
      announce('Message copied to clipboard');
    }
  }, [messages, announce]);
  
  // Handle conversation selection
  const handleSelectConversation = useCallback((conversation: ConversationSession) => {
    setMessages(conversation.messages);
    setCurrentConversationId(conversation.id);
    announce(`Loaded conversation: ${conversation.title}`);
  }, [announce]);
  
  // Handle conversation deletion
  const handleDeleteConversation = useCallback((conversationId: string) => {
    setConversations(prev => prev.filter(conv => conv.id !== conversationId));
    
    if (currentConversationId === conversationId) {
      setCurrentConversationId(null);
      setMessages([]);
    }
    
    announce('Conversation deleted');
  }, [currentConversationId, announce]);
  
  // Handle export conversations
  const handleExportConversations = useCallback((format: 'json' | 'text' | 'csv', conversationIds?: string[]) => {
    const conversationsToExport = conversationIds 
      ? conversations.filter(conv => conversationIds.includes(conv.id))
      : conversations;
    
    if (format === 'json') {
      const data = JSON.stringify(conversationsToExport, null, 2);
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'conversations.json';
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === 'text') {
      let text = '';
      conversationsToExport.forEach(conv => {
        text += `# ${conv.title}\n\n`;
        conv.messages.forEach(msg => {
          text += `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}\n\n`;
        });
        text += '---\n\n';
      });
      
      const blob = new Blob([text], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'conversations.txt';
      a.click();
      URL.revokeObjectURL(url);
    }
    
    announce(`Conversations exported as ${format.toUpperCase()}`);
    return '';
  }, [conversations, announce]);
  
  // Handle clear history
  const handleClearHistory = useCallback(() => {
    setConversations([]);
    setCurrentConversationId(null);
    setMessages([]);
    announce('Conversation history cleared');
  }, [announce]);
  
  // Handle typing indicator
  const handleTyping = useCallback((typing: boolean) => {
    setIsTyping(typing);
  }, []);
  
  // Demo controls
  const DemoControls = () => (
    <div 
      className="karen-demo-controls"
      style={{
        padding: '1rem',
        backgroundColor: theme.colors.surface,
        borderRadius: theme.borderRadius,
        marginBottom: '1rem',
        border: `1px solid ${theme.colors.border}`
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>Demo Controls</h3>
      
      <div 
        className="karen-demo-controls-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
          gap: '1rem'
        }}
      >
        <div>
          <h4>Display Options</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={showAiData}
                onChange={(e) => setShowAiData(e.target.checked)}
              />
              Show AI Data
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={showTimestamps}
                onChange={(e) => setShowTimestamps(e.target.checked)}
              />
              Show Timestamps
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={showActions}
                onChange={(e) => setShowActions(e.target.checked)}
              />
              Show Actions
            </label>
          </div>
        </div>
        
        <div>
          <h4>Interface Options</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={showHistory}
                onChange={(e) => setShowHistory(e.target.checked)}
              />
              Show History
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={showVoiceInput}
                onChange={(e) => setShowVoiceInput(e.target.checked)}
              />
              Show Voice Input
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={autoFocus}
                onChange={(e) => setAutoFocus(e.target.checked)}
              />
              Auto Focus Input
            </label>
          </div>
        </div>
        
        <div>
          <h4>Input Options</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={showCharacterCount}
                onChange={(e) => setShowCharacterCount(e.target.checked)}
              />
              Show Character Count
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={showSendButton}
                onChange={(e) => setShowSendButton(e.target.checked)}
              />
              Show Send Button
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={showVoiceButton}
                onChange={(e) => setShowVoiceButton(e.target.checked)}
              />
              Show Voice Button
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={showAttachButton}
                onChange={(e) => setShowAttachButton(e.target.checked)}
              />
              Show Attach Button
            </label>
          </div>
        </div>
        
        <div>
          <h4>Features</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={allowAttachments}
                onChange={(e) => setAllowAttachments(e.target.checked)}
              />
              Allow Attachments
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={allowVoiceInput}
                onChange={(e) => setAllowVoiceInput(e.target.checked)}
              />
              Allow Voice Input
            </label>
          </div>
        </div>
      </div>
      
      <div style={{ marginTop: '1rem' }}>
        <h4>Device Type</h4>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <span>Current: {isMobile ? 'Mobile' : isTablet ? 'Tablet' : 'Desktop'}</span>
          <span>Window: {typeof window !== 'undefined' ? `${window.innerWidth}px` : '0px'}</span>
        </div>
      </div>
    </div>
  );
  
  return (
    <ResponsiveDesign>
      <div 
        className="karen-chat-demo"
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          padding: isMobile ? '0.5rem' : '1rem',
          backgroundColor: theme.colors.background
        }}
      >
        <div 
          className="karen-demo-header"
          style={{
            marginBottom: '1rem',
            textAlign: 'center'
          }}
        >
          <h1 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Chat Interface Demo</h1>
          <p style={{ marginTop: 0, color: theme.colors.textSecondary }}>
            This is a demonstration of the Chat Interface components for the CoPilot Architecture.
          </p>
        </div>
        
        <DemoControls />
        
        <div 
          className="karen-chat-container"
          style={{
            flex: 1,
            minHeight: 0,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.borderRadius,
            overflow: 'hidden'
          }}
        >
          <ChatInterface
            theme={theme}
            messages={messages}
            conversations={conversations}
            currentConversationId={currentConversationId}
            onSendMessage={handleSendMessage}
            onRetryMessage={handleRetryMessage}
            onDeleteMessage={handleDeleteMessage}
            onCopyMessage={handleCopyMessage}
            onSelectConversation={handleSelectConversation}
            onDeleteConversation={handleDeleteConversation}
            onExportConversations={handleExportConversations}
            onClearHistory={handleClearHistory}
            onVoiceMessage={handleVoiceMessage}
            onTyping={handleTyping}
            placeholder="Type a message..."
            disabled={isTyping}
            maxLength={4000}
            showHistory={showHistory}
            showVoiceInput={showVoiceInput}
            showAiData={showAiData}
            showConfidence={showAiData}
            showKeywords={showAiData}
            showReasoning={showAiData}
            showTimestamps={showTimestamps}
            showActions={showActions}
            showCharacterCount={showCharacterCount}
            showSendButton={showSendButton}
            showVoiceButton={showVoiceButton}
            showAttachButton={showAttachButton}
            allowAttachments={allowAttachments}
            allowVoiceInput={allowVoiceInput}
            autoFocus={autoFocus}
          />
        </div>
        
        <div 
          className="karen-demo-footer"
          style={{
            marginTop: '1rem',
            textAlign: 'center',
            fontSize: '0.875rem',
            color: theme.colors.textSecondary
          }}
        >
          <p>Press ? to see keyboard shortcuts. This demo includes accessibility features, responsive design, and theme support.</p>
        </div>
      </div>
    </ResponsiveDesign>
  );
};

// Demo app with theme provider
export const ChatInterfaceDemoApp: React.FC = () => {
  return (
    <ThemeProvider>
      <AccessibilityEnhancements>
        <ChatInterfaceDemo />
      </AccessibilityEnhancements>
    </ThemeProvider>
  );
};

export default ChatInterfaceDemo;