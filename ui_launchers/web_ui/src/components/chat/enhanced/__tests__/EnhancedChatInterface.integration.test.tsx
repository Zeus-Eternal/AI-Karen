import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import EnhancedChatInterface from '../EnhancedChatInterface';
import { EnhancedChatMessage, ConversationExport, ConversationShare } from '@/types/enhanced-chat';

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock date-fns
vi.mock('date-fns', () => ({
  format: vi.fn((date) => '12:34'),
  formatDistanceToNow: vi.fn(() => '2 minutes ago'),
  addDays: vi.fn((date, days) => new Date(date.getTime() + days * 24 * 60 * 60 * 1000))
}));

// Mock ResizablePanel components
vi.mock('@/components/ui/resizable', () => ({
  ResizablePanelGroup: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  ResizablePanel: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  ResizableHandle: ({ ...props }: any) => <div {...props} />
}));

describe('EnhancedChatInterface Integration', () => {
  const mockOnMessageSent = vi.fn();
  const mockOnMessageReceived = vi.fn();
  const mockOnContextChange = vi.fn();
  const mockOnExport = vi.fn();
  const mockOnShare = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the complete enhanced chat interface', () => {
    render(
      <EnhancedChatInterface
        onMessageSent={mockOnMessageSent}
        onMessageReceived={mockOnMessageReceived}
        onContextChange={mockOnContextChange}
        onExport={mockOnExport}
        onShare={mockOnShare}
      />
    );

    expect(screen.getByText('Enhanced Chat')).toBeInTheDocument();
    expect(screen.getByText('Context-Aware')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument();
  });

  it('handles message sending and receiving flow', async () => {
    render(
      <EnhancedChatInterface
        onMessageSent={mockOnMessageSent}
        onMessageReceived={mockOnMessageReceived}
        onContextChange={mockOnContextChange}
      />
    );

    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    // Type a message
    fireEvent.change(input, { target: { value: 'Hello, how can you help me?' } });
    expect(input).toHaveValue('Hello, how can you help me?');

    // Send the message
    fireEvent.click(sendButton);

    // Check that user message appears
    await waitFor(() => {
      expect(screen.getByText('Hello, how can you help me?')).toBeInTheDocument();
    });

    // Check that onMessageSent was called
    expect(mockOnMessageSent).toHaveBeenCalledWith(
      expect.objectContaining({
        role: 'user',
        content: 'Hello, how can you help me?',
        type: 'text',
        status: 'sent'
      })
    );

    // Wait for AI response
    await waitFor(() => {
      expect(screen.getByText(/I understand you're asking about/)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Check that onMessageReceived was called
    expect(mockOnMessageReceived).toHaveBeenCalledWith(
      expect.objectContaining({
        role: 'assistant',
        type: 'text',
        status: 'completed'
      })
    );
  });

  it('displays context suggestions after messages', async () => {
    render(
      <EnhancedChatInterface
        enableSuggestions={true}
        onMessageSent={mockOnMessageSent}
        onMessageReceived={mockOnMessageReceived}
      />
    );

    const input = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(input, { target: { value: 'Show me some code examples' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    // Wait for messages to appear
    await waitFor(() => {
      expect(screen.getByText('Show me some code examples')).toBeInTheDocument();
    });

    // Wait for AI response and suggestions
    await waitFor(() => {
      expect(screen.getByText('Smart Suggestions')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('handles context panel toggle', () => {
    render(
      <EnhancedChatInterface
        enableContextPanel={true}
        onContextChange={mockOnContextChange}
      />
    );

    // Context panel should be visible by default
    expect(screen.getByText('Context')).toBeInTheDocument();

    // Find and click the panel toggle button
    const toggleButton = screen.getByRole('button', { name: /panel/i });
    fireEvent.click(toggleButton);

    // Context panel should still be visible (ResizablePanel is mocked)
    expect(screen.getByText('Context')).toBeInTheDocument();
  });

  it('handles conversation threading', async () => {
    render(
      <EnhancedChatInterface
        enableThreading={true}
        enableContextPanel={true}
        onContextChange={mockOnContextChange}
      />
    );

    // Should show conversation threading in context panel
    expect(screen.getByText('Conversations')).toBeInTheDocument();
    expect(screen.getByText('Current Conversation')).toBeInTheDocument();
  });

  it('handles export functionality', async () => {
    const mockExport = vi.fn().mockResolvedValue(undefined);
    
    render(
      <EnhancedChatInterface
        enableExport={true}
        onExport={mockExport}
        initialMessages={[
          {
            id: 'msg-1',
            role: 'user',
            content: 'Test message',
            timestamp: new Date(),
            type: 'text',
            status: 'sent'
          }
        ]}
      />
    );

    // Click export button
    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    // Should open export dialog
    await waitFor(() => {
      expect(screen.getByText('Export Conversation')).toBeInTheDocument();
    });

    // Click export in dialog
    const exportDialogButton = screen.getByRole('button', { name: /^Export$/ });
    fireEvent.click(exportDialogButton);

    await waitFor(() => {
      expect(mockExport).toHaveBeenCalledWith(
        expect.objectContaining({
          format: 'json',
          includeMetadata: true,
          includeReasoning: false,
          includeAttachments: true
        })
      );
    });
  });

  it('handles share functionality', async () => {
    const mockShare = vi.fn().mockResolvedValue('https://example.com/share/123');
    
    render(
      <EnhancedChatInterface
        enableSharing={true}
        onShare={mockShare}
        initialMessages={[
          {
            id: 'msg-1',
            role: 'user',
            content: 'Test message',
            timestamp: new Date(),
            type: 'text',
            status: 'sent'
          }
        ]}
      />
    );

    // Click share button
    const shareButton = screen.getByText('Share');
    fireEvent.click(shareButton);

    // Should open share dialog
    await waitFor(() => {
      expect(screen.getByText('Share Conversation')).toBeInTheDocument();
    });

    // Click create share link
    const createLinkButton = screen.getByText('Create Share Link');
    fireEvent.click(createLinkButton);

    await waitFor(() => {
      expect(mockShare).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'private',
          permissions: [],
          allowComments: false,
          allowDownload: false
        })
      );
    });
  });

  it('handles keyboard shortcuts for message sending', async () => {
    render(
      <EnhancedChatInterface
        onMessageSent={mockOnMessageSent}
      />
    );

    const input = screen.getByPlaceholderText('Type your message...');
    
    // Type message and press Enter
    fireEvent.change(input, { target: { value: 'Test keyboard shortcut' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(screen.getByText('Test keyboard shortcut')).toBeInTheDocument();
    });

    expect(mockOnMessageSent).toHaveBeenCalled();
  });

  it('prevents sending empty messages', () => {
    render(
      <EnhancedChatInterface
        onMessageSent={mockOnMessageSent}
      />
    );

    const sendButton = screen.getByRole('button', { name: /send/i });
    
    // Send button should be disabled when input is empty
    expect(sendButton).toBeDisabled();

    // Try to send empty message
    fireEvent.click(sendButton);
    expect(mockOnMessageSent).not.toHaveBeenCalled();
  });

  it('shows loading state during message processing', async () => {
    render(
      <EnhancedChatInterface />
    );

    const input = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(input, { target: { value: 'Test loading state' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    // Should show loading indicator
    await waitFor(() => {
      expect(screen.getByText('AI is thinking...')).toBeInTheDocument();
    });
  });

  it('displays message metadata correctly', async () => {
    const messageWithMetadata: EnhancedChatMessage = {
      id: 'msg-1',
      role: 'assistant',
      content: 'Response with metadata',
      timestamp: new Date(),
      type: 'text',
      status: 'completed',
      confidence: 0.95,
      metadata: {
        model: 'enhanced-ai-v1',
        tokens: 50,
        cost: 0.001
      }
    };

    render(
      <EnhancedChatInterface
        initialMessages={[messageWithMetadata]}
      />
    );

    expect(screen.getByText('Response with metadata')).toBeInTheDocument();
    expect(screen.getByText('95% confident')).toBeInTheDocument();
    expect(screen.getByText('enhanced-ai-v1')).toBeInTheDocument();
  });

  it('handles context changes and updates', async () => {
    render(
      <EnhancedChatInterface
        onContextChange={mockOnContextChange}
      />
    );

    const input = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(input, { target: { value: 'Context test message' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    // Wait for message to be added and context to update
    await waitFor(() => {
      expect(mockOnContextChange).toHaveBeenCalled();
    });

    const contextCall = mockOnContextChange.mock.calls[0][0];
    expect(contextCall.currentThread.messages).toHaveLength(1);
    expect(contextCall.currentThread.messages[0].content).toBe('Context test message');
  });
});