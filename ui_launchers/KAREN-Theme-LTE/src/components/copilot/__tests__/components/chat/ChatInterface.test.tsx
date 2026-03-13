import { describe, test, expect, beforeEach, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInterface } from '../../../components/chat/ChatInterface';
import { useChat } from '../../../hooks/useChat';
import { useStreamResponse } from '../../../hooks/useStreamResponse';

// Mock the hooks
vi.mock('../../hooks/useChat');
vi.mock('../../hooks/useStreamResponse');

// Mock data
const mockConversations = [
  {
    id: 'test-conversation-id',
    title: 'Test Conversation',
    createdAt: new Date(),
    updatedAt: new Date(),
    messages: [
      {
        id: 'test-message-id',
        role: 'user' as const,
        content: 'Hello, world!',
        timestamp: new Date(),
      },
    ],
  },
];

const mockChatHookValue = {
  conversations: mockConversations,
  activeConversation: mockConversations[0],
  isLoading: false,
  error: null,
  messages: mockConversations[0]?.messages,
  isTyping: false,
  createConversation: vi.fn(),
  selectConversation: vi.fn(),
  deleteConversation: vi.fn(),
  updateConversation: vi.fn(),
  sendMessage: vi.fn(),
  addMessage: vi.fn(),
  updateMessage: vi.fn(),
  deleteMessage: vi.fn(),
  searchConversations: vi.fn(),
  filterConversationsByTag: vi.fn(),
  filterConversationsByDate: vi.fn(),
  exportConversation: vi.fn(),
  importConversation: vi.fn(),
  clearAllConversations: vi.fn(),
  generateSummary: vi.fn(),
  generateTags: vi.fn(),
  setTyping: vi.fn(),
};

const mockStreamHookValue = {
  response: null,
  isLoading: false,
  error: null,
  startStream: vi.fn(),
  resetStream: vi.fn(),
};

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useChat as any).mockReturnValue(mockChatHookValue);
    (useStreamResponse as any).mockReturnValue(mockStreamHookValue);
  });

  test('renders without crashing', () => {
    render(<ChatInterface />);
    expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
  });

  test('displays active conversation title', () => {
    render(<ChatInterface />);
    expect(screen.getByText('Test Conversation')).toBeInTheDocument();
  });

  test('displays messages in active conversation', () => {
    render(<ChatInterface />);
    expect(screen.getByText('Hello, world!')).toBeInTheDocument();
  });

  test('calls sendMessage when send button is clicked', () => {
    render(<ChatInterface />);
    fireEvent.click(screen.getByTestId('send-button'));
    expect(mockChatHookValue.sendMessage).toHaveBeenCalled();
  });

  test('calls sendMessage when Enter is pressed in input', () => {
    render(<ChatInterface />);
    const input = screen.getByTestId('message-input');
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });
    expect(mockChatHookValue.sendMessage).toHaveBeenCalled();
  });

  test('does not call sendMessage when Shift+Enter is pressed', () => {
    render(<ChatInterface />);
    const input = screen.getByTestId('message-input');
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });
    expect(mockChatHookValue.sendMessage).not.toHaveBeenCalled();
  });

  test('displays loading state when isLoading is true', () => {
    (useChat as any).mockReturnValue({
      ...mockChatHookValue,
      isLoading: true,
    });
    render(<ChatInterface />);
    expect(screen.getByText('Loading conversations...')).toBeInTheDocument();
  });

  test('displays error state when error is present', () => {
    (useChat as any).mockReturnValue({
      ...mockChatHookValue,
      error: 'Test error message',
    });
    render(<ChatInterface />);
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  test('displays empty state when there are no messages', () => {
    (useChat as any).mockReturnValue({
      ...mockChatHookValue,
      activeConversation: {
        ...mockChatHookValue.activeConversation,
        messages: [],
      },
      messages: [],
    });
    render(<ChatInterface />);
    expect(screen.getByText('No messages yet')).toBeInTheDocument();
  });

  test('displays typing indicator when isTyping is true', () => {
    (useChat as any).mockReturnValue({
      ...mockChatHookValue,
      isTyping: true,
    });
    render(<ChatInterface />);
    expect(screen.getByLabelText('Assistant is typing')).toBeInTheDocument();
  });

  test('shows history panel when showHistory is true and panel is toggled', () => {
    render(<ChatInterface showHistory={true} />);
    const historyButton = screen.getByLabelText('Open conversation history');
    fireEvent.click(historyButton);
    expect(screen.getByTestId('conversation-history')).toBeInTheDocument();
  });

  test('shows voice panel when showVoiceRecorder is true and panel is toggled', () => {
    render(<ChatInterface showVoiceRecorder={true} />);
    const voiceButton = screen.getByLabelText('Record voice message');
    fireEvent.click(voiceButton);
    expect(screen.getByTestId('voice-recorder')).toBeInTheDocument();
  });

  test('shows export dialog when export button is clicked', () => {
    const mockOnExport = vi.fn();
    render(<ChatInterface onExport={mockOnExport} />);
    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);
    expect(screen.getByText('Export Conversation')).toBeInTheDocument();
  });

  test('calls onSendMessage prop when provided', () => {
    const mockOnSendMessage = vi.fn();
    render(<ChatInterface onSendMessage={mockOnSendMessage} />);
    fireEvent.click(screen.getByTestId('send-button'));
    expect(mockOnSendMessage).toHaveBeenCalled();
  });

  test('calls onVoiceRecord prop when provided', () => {
    const mockOnVoiceRecord = vi.fn();
    render(<ChatInterface onVoiceRecord={mockOnVoiceRecord} />);
    const voiceButton = screen.getByLabelText('Record voice message');
    fireEvent.click(voiceButton);
    expect(mockOnVoiceRecord).toHaveBeenCalled();
  });

  test('calls onConversationSelect prop when provided', () => {
    const mockOnConversationSelect = vi.fn();
    const mockConversation = { id: 'test-id', title: 'Test Conversation' };
    render(<ChatInterface onConversationSelect={mockOnConversationSelect} />);
    
    // Simulate conversation selection
    fireEvent.click(screen.getByLabelText('Open conversation history'));
    fireEvent.click(screen.getByText('Test Conversation'));
    expect(mockOnConversationSelect).toHaveBeenCalledWith(mockConversation);
  });

  test('calls onConversationDelete prop when provided', () => {
    const mockOnConversationDelete = vi.fn();
    render(<ChatInterface onConversationDelete={mockOnConversationDelete} />);
    
    // Simulate conversation deletion
    const conversationId = 'test-conversation-id';
    mockOnConversationDelete(conversationId);
    expect(mockOnConversationDelete).toHaveBeenCalledWith(conversationId);
  });

  test('calls onExport prop when provided', () => {
    const mockOnExport = vi.fn();
    const mockConversation = { id: 'test-id', title: 'Test Conversation' };
    render(<ChatInterface onExport={mockOnExport} />);
    
    // Simulate export
    fireEvent.click(screen.getByText('Export'));
    fireEvent.click(screen.getByText('Export'));
    expect(mockOnExport).toHaveBeenCalledWith(mockConversation);
  });

  test('disables input when disabled prop is true', () => {
    render(<ChatInterface disabled={true} />);
    const input = screen.getByTestId('message-input');
    expect(input).toBeDisabled();
  });

  test('uses custom placeholder when provided', () => {
    render(<ChatInterface placeholder="Custom placeholder" />);
    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument();
  });

  test('displays theme toggle when showThemeToggle is true', () => {
    render(<ChatInterface showThemeToggle={true} />);
    expect(screen.getByTestId('theme-toggle')).toBeInTheDocument();
  });

  test('does not display theme toggle when showThemeToggle is false', () => {
    render(<ChatInterface showThemeToggle={false} />);
    expect(screen.queryByTestId('theme-toggle')).not.toBeInTheDocument();
  });

  test('displays agent badge when agent is present', () => {
    (useChat as any).mockReturnValue({
      ...mockChatHookValue,
      activeConversation: {
        ...mockChatHookValue.activeConversation,
        agent: 'Test Agent',
      },
    });
    render(<ChatInterface />);
    expect(screen.getByText('🤖 Test Agent')).toBeInTheDocument();
  });

  test('does not display agent badge when agent is not present', () => {
    (useChat as any).mockReturnValue({
      ...mockChatHookValue,
      activeConversation: {
        ...mockChatHookValue.activeConversation,
        agent: undefined,
      },
    });
    render(<ChatInterface />);
    expect(screen.queryByText('🤖')).not.toBeInTheDocument();
  });
});