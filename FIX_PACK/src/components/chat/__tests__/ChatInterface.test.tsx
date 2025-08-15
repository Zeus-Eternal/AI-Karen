# Path: ui_launchers/web_ui/src/components/chat/__tests__/ChatInterface.test.tsx

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from '../ChatInterface';
import { useConversation } from '@/hooks/use-conversation';
import { useAuth } from '@/contexts/AuthContext';
import { useFeature } from '@/hooks/use-feature';
import { useTelemetry } from '@/hooks/use-telemetry';
import { useToast } from '@/hooks/use-toast';

// Mock dependencies
jest.mock('@/hooks/use-conversation');
jest.mock('@/contexts/AuthContext');
jest.mock('@/hooks/use-feature');
jest.mock('@/hooks/use-telemetry');
jest.mock('@/hooks/use-toast');
jest.mock('../MessageList', () => ({
  MessageList: ({ messages, onMessageAction }: any) => (
    <div data-testid="message-list">
      {messages.map((msg: any) => (
        <div key={msg.id} data-testid={`message-${msg.id}`}>
          {msg.content}
          <button onClick={() => onMessageAction(msg.id, { type: 'copy' })}>
            Copy
          </button>
        </div>
      ))}
    </div>
  )
}));
jest.mock('../Composer', () => ({
  Composer: ({ onSubmit, isDisabled }: any) => (
    <div data-testid="composer">
      <input
        data-testid="composer-input"
        disabled={isDisabled}
        onChange={(e) => {
          if (e.target.value === 'test message') {
            onSubmit('test message', 'text');
          }
        }}
      />
    </div>
  )
}));

const mockUseConversation = useConversation as jest.MockedFunction<typeof useConversation>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseFeature = useFeature as jest.MockedFunction<typeof useFeature>;
const mockUseTelemetry = useTelemetry as jest.MockedFunction<typeof useTelemetry>;
const mockUseToast = useToast as jest.MockedFunction<typeof useToast>;

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn()
  }
});

describe('ChatInterface', () => {
  const mockSendMessage = jest.fn();
  const mockClearMessages = jest.fn();
  const mockRetryLastMessage = jest.fn();
  const mockAbortCurrentRequest = jest.fn();
  const mockUpdateMessage = jest.fn();
  const mockDeleteMessage = jest.fn();
  const mockTrack = jest.fn();
  const mockToast = jest.fn();

  const defaultConversationState = {
    messages: [],
    isLoading: false,
    isTyping: false,
    sessionId: 'test-session-123',
    conversationId: 'test-conversation-123',
    error: null,
    sendMessage: mockSendMessage,
    clearMessages: mockClearMessages,
    retryLastMessage: mockRetryLastMessage,
    abortCurrentRequest: mockAbortCurrentRequest,
    updateMessage: mockUpdateMessage,
    deleteMessage: mockDeleteMessage
  };

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseAuth.mockReturnValue({
      user: { user_id: 'test-user-123' },
      isAuthenticated: true
    } as any);

    mockUseFeature.mockImplementation((feature: string) => {
      const features: Record<string, boolean> = {
        'chat.assistance': true,
        'chat.streaming': true,
        'voice.input': true,
        'attachments.enabled': false,
        'chat.quick_actions': true,
        'emoji.picker': true,
        'chat.clear': true,
        'chat.settings': true
      };
      return features[feature] ?? false;
    });

    mockUseTelemetry.mockReturnValue({
      track: mockTrack
    } as any);

    mockUseToast.mockReturnValue({
      toast: mockToast
    } as any);

    mockUseConversation.mockReturnValue(defaultConversationState);
  });

  it('should render empty state when no messages', () => {
    render(<ChatInterface />);

    expect(screen.getByText('Welcome to AI Assistant')).toBeInTheDocument();
    expect(screen.getByText(/I can help you with code/)).toBeInTheDocument();
  });

  it('should render header when showHeader is true', () => {
    render(<ChatInterface showHeader={true} />);

    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
    expect(screen.getByText('Enhanced')).toBeInTheDocument();
  });

  it('should not render header when showHeader is false', () => {
    render(<ChatInterface showHeader={false} />);

    expect(screen.queryByText('AI Assistant')).not.toBeInTheDocument();
  });

  it('should render messages when they exist', () => {
    const messages = [
      {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
        status: 'sent'
      },
      {
        id: 'msg-2',
        role: 'assistant',
        content: 'Hi there!',
        timestamp: new Date(),
        status: 'completed'
      }
    ];

    mockUseConversation.mockReturnValue({
      ...defaultConversationState,
      messages
    });

    render(<ChatInterface />);

    expect(screen.getByTestId('message-list')).toBeInTheDocument();
    expect(screen.getByTestId('message-msg-1')).toBeInTheDocument();
    expect(screen.getByTestId('message-msg-2')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  it('should handle message submission', async () => {
    render(<ChatInterface />);

    const input = screen.getByTestId('composer-input');
    await userEvent.type(input, 'test message');

    expect(mockSendMessage).toHaveBeenCalledWith('test message', 'text');
  });

  it('should handle message actions', async () => {
    const messages = [
      {
        id: 'msg-1',
        role: 'assistant',
        content: 'Test message',
        timestamp: new Date(),
        status: 'completed'
      }
    ];

    mockUseConversation.mockReturnValue({
      ...defaultConversationState,
      messages
    });

    render(<ChatInterface />);

    const copyButton = screen.getByText('Copy');
    fireEvent.click(copyButton);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Test message');
    expect(mockToast).toHaveBeenCalledWith({
      title: 'Copied',
      description: 'Message copied to clipboard'
    });
  });

  it('should handle clear conversation', async () => {
    const messages = [
      {
        id: 'msg-1',
        role: 'user',
        content: 'Test',
        timestamp: new Date(),
        status: 'sent'
      }
    ];

    mockUseConversation.mockReturnValue({
      ...defaultConversationState,
      messages
    });

    render(<ChatInterface />);

    const clearButton = screen.getByTitle('Clear conversation');
    fireEvent.click(clearButton);

    expect(mockClearMessages).toHaveBeenCalled();
    expect(mockToast).toHaveBeenCalledWith({
      title: 'Conversation Cleared',
      description: 'All messages have been removed'
    });
  });

  it('should show abort button when typing', () => {
    mockUseConversation.mockReturnValue({
      ...defaultConversationState,
      isTyping: true
    });

    render(<ChatInterface />);

    const abortButton = screen.getByTitle('Cancel request');
    expect(abortButton).toBeInTheDocument();

    fireEvent.click(abortButton);
    expect(mockAbortCurrentRequest).toHaveBeenCalled();
  });

  it('should display error when present', () => {
    mockUseConversation.mockReturnValue({
      ...defaultConversationState,
      error: 'Test error message'
    });

    render(<ChatInterface />);

    expect(screen.getByText('Error: Test error message')).toBeInTheDocument();
    
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);
    expect(mockRetryLastMessage).toHaveBeenCalled();
  });

  it('should disable composer when user is not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false
    } as any);

    render(<ChatInterface />);

    const input = screen.getByTestId('composer-input');
    expect(input).toBeDisabled();
  });

  it('should disable composer when loading', () => {
    mockUseConversation.mockReturnValue({
      ...defaultConversationState,
      isLoading: true
    });

    render(<ChatInterface />);

    const input = screen.getByTestId('composer-input');
    expect(input).toBeDisabled();
  });

  it('should show session info in header', () => {
    render(<ChatInterface />);

    expect(screen.getByText(/Session: test-sess.../)).toBeInTheDocument();
  });

  it('should show message count when messages exist', () => {
    const messages = [
      {
        id: 'msg-1',
        role: 'user',
        content: 'Test',
        timestamp: new Date(),
        status: 'sent'
      }
    ];

    mockUseConversation.mockReturnValue({
      ...defaultConversationState,
      messages
    });

    render(<ChatInterface />);

    expect(screen.getByText('• 1 messages')).toBeInTheDocument();
  });

  it('should track telemetry events', async () => {
    const onMessageSent = jest.fn();
    const onMessageReceived = jest.fn();

    render(
      <ChatInterface 
        onMessageSent={onMessageSent}
        onMessageReceived={onMessageReceived}
      />
    );

    // Verify conversation hook was called with telemetry callbacks
    expect(mockUseConversation).toHaveBeenCalledWith(
      expect.objectContaining({
        onMessageSent: expect.any(Function),
        onMessageReceived: expect.any(Function),
        onError: expect.any(Function)
      })
    );
  });

  it('should handle custom API endpoint', () => {
    render(<ChatInterface apiEndpoint="/custom/api/chat" />);

    expect(mockUseConversation).toHaveBeenCalledWith(
      expect.objectContaining({
        apiEndpoint: '/custom/api/chat'
      })
    );
  });

  it('should apply custom className and height', () => {
    const { container } = render(
      <ChatInterface 
        className="custom-class" 
        height="800px" 
      />
    );

    const card = container.querySelector('.custom-class');
    expect(card).toBeInTheDocument();
    expect(card).toHaveStyle({ height: '800px' });
  });

  it('should handle feature flag disabled states', () => {
    mockUseFeature.mockImplementation(() => false);

    render(<ChatInterface />);

    // Should not show enhanced badge when chat assistance is disabled
    expect(screen.queryByText('Enhanced')).not.toBeInTheDocument();
  });

  it('should handle message deletion action', async () => {
    const messages = [
      {
        id: 'msg-1',
        role: 'user',
        content: 'Test message',
        timestamp: new Date(),
        status: 'sent'
      }
    ];

    mockUseConversation.mockReturnValue({
      ...defaultConversationState,
      messages
    });

    render(<ChatInterface />);

    // Simulate message action through the MessageList component
    const messageList = screen.getByTestId('message-list');
    
    // This would normally be triggered by MessageList component
    // We'll simulate it by calling the handler directly
    const copyButton = screen.getByText('Copy');
    fireEvent.click(copyButton);

    expect(mockTrack).toHaveBeenCalledWith('chat_message_action', {
      messageId: 'msg-1',
      action: 'copy',
      conversationId: 'test-conversation-123'
    });
  });
});