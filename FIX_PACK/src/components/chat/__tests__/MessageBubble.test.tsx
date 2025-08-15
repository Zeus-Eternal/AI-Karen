# Path: ui_launchers/web_ui/src/components/chat/__tests__/MessageBubble.test.tsx

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MessageBubble } from '../MessageBubble';

// Mock dependencies
jest.mock('@/components/security/SanitizedMarkdown', () => ({
  SanitizedMarkdown: ({ content }: any) => <div data-testid="sanitized-markdown">{content}</div>
}));

jest.mock('@/components/security/RBACGuard', () => ({
  RBACGuard: ({ children, fallback }: any) => children || fallback
}));

jest.mock('date-fns', () => ({
  format: jest.fn(() => '10:30')
}));

describe('MessageBubble', () => {
  const mockOnAction = jest.fn();

  const userMessage = {
    id: 'user-msg-1',
    role: 'user' as const,
    content: 'Hello, how are you?',
    timestamp: new Date('2023-01-01T10:30:00Z'),
    status: 'sent' as const
  };

  const assistantMessage = {
    id: 'assistant-msg-1',
    role: 'assistant' as const,
    content: 'I am doing well, thank you for asking!',
    timestamp: new Date('2023-01-01T10:30:01Z'),
    status: 'completed' as const,
    metadata: {
      confidence: 0.95,
      model: 'gpt-4',
      latencyMs: 1200
    }
  };

  const errorMessage = {
    id: 'error-msg-1',
    role: 'assistant' as const,
    content: 'Sorry, I encountered an error processing your request.',
    timestamp: new Date('2023-01-01T10:30:02Z'),
    status: 'error' as const
  };

  const generatingMessage = {
    id: 'generating-msg-1',
    role: 'assistant' as const,
    content: 'I am thinking about your question...',
    timestamp: new Date('2023-01-01T10:30:03Z'),
    status: 'generating' as const
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render user message correctly', () => {
    render(<MessageBubble message={userMessage} onAction={mockOnAction} />);

    expect(screen.getByText('Hello, how are you?')).toBeInTheDocument();
    expect(screen.getByText('10:30')).toBeInTheDocument();
    
    // User messages should have user avatar
    const avatar = screen.getByRole('generic');
    expect(avatar).toHaveClass('from-blue-500', 'to-blue-600');
  });

  it('should render assistant message correctly', () => {
    render(<MessageBubble message={assistantMessage} onAction={mockOnAction} />);

    expect(screen.getByTestId('sanitized-markdown')).toBeInTheDocument();
    expect(screen.getByText('I am doing well, thank you for asking!')).toBeInTheDocument();
    
    // Should show metadata badges
    expect(screen.getByText('95% confidence')).toBeInTheDocument();
    expect(screen.getByText('gpt-4')).toBeInTheDocument();
    expect(screen.getByText('1200ms')).toBeInTheDocument();
  });

  it('should render error message with error styling', () => {
    render(<MessageBubble message={errorMessage} onAction={mockOnAction} />);

    expect(screen.getByText('Sorry, I encountered an error processing your request.')).toBeInTheDocument();
    
    // Error messages should have error styling
    const messageContent = screen.getByText('Sorry, I encountered an error processing your request.').closest('div');
    expect(messageContent).toHaveClass('from-red-50', 'to-red-100');
  });

  it('should show generating indicator for generating messages', () => {
    render(<MessageBubble message={generatingMessage} onAction={mockOnAction} />);

    expect(screen.getByText('Generating...')).toBeInTheDocument();
    expect(screen.getByText('I am thinking about your question...')).toBeInTheDocument();
  });

  it('should show action buttons on hover for assistant messages', async () => {
    render(<MessageBubble message={assistantMessage} onAction={mockOnAction} />);

    const messageContainer = screen.getByText('I am doing well, thank you for asking!').closest('.group');
    
    // Initially, action buttons should not be visible
    expect(screen.queryByTitle('Copy message')).not.toBeInTheDocument();

    // Hover over the message
    if (messageContainer) {
      fireEvent.mouseEnter(messageContainer);
    }

    await waitFor(() => {
      expect(screen.getByTitle('Copy message')).toBeInTheDocument();
      expect(screen.getByTitle('Rate up')).toBeInTheDocument();
      expect(screen.getByTitle('Rate down')).toBeInTheDocument();
    });
  });

  it('should not show action buttons for user messages', async () => {
    render(<MessageBubble message={userMessage} onAction={mockOnAction} />);

    const messageContainer = screen.getByText('Hello, how are you?').closest('.group');
    
    if (messageContainer) {
      fireEvent.mouseEnter(messageContainer);
    }

    // Should not show action buttons for user messages
    expect(screen.queryByTitle('Copy message')).not.toBeInTheDocument();
    expect(screen.queryByTitle('Rate up')).not.toBeInTheDocument();
  });

  it('should handle copy action', async () => {
    render(<MessageBubble message={assistantMessage} onAction={mockOnAction} />);

    const messageContainer = screen.getByText('I am doing well, thank you for asking!').closest('.group');
    
    if (messageContainer) {
      fireEvent.mouseEnter(messageContainer);
    }

    await waitFor(() => {
      const copyButton = screen.getByTitle('Copy message');
      fireEvent.click(copyButton);
    });

    expect(mockOnAction).toHaveBeenCalledWith({ type: 'copy' });
  });

  it('should handle rating actions', async () => {
    render(<MessageBubble message={assistantMessage} onAction={mockOnAction} />);

    const messageContainer = screen.getByText('I am doing well, thank you for asking!').closest('.group');
    
    if (messageContainer) {
      fireEvent.mouseEnter(messageContainer);
    }

    await waitFor(() => {
      const rateUpButton = screen.getByTitle('Rate up');
      fireEvent.click(rateUpButton);
    });

    expect(mockOnAction).toHaveBeenCalledWith({ type: 'rate', payload: { rating: 'up' } });

    // Clear previous calls
    mockOnAction.mockClear();

    await waitFor(() => {
      const rateDownButton = screen.getByTitle('Rate down');
      fireEvent.click(rateDownButton);
    });

    expect(mockOnAction).toHaveBeenCalledWith({ type: 'rate', payload: { rating: 'down' } });
  });

  it('should show retry button for error messages', async () => {
    render(<MessageBubble message={errorMessage} onAction={mockOnAction} />);

    const messageContainer = screen.getByText('Sorry, I encountered an error processing your request.').closest('.group');
    
    if (messageContainer) {
      fireEvent.mouseEnter(messageContainer);
    }

    await waitFor(() => {
      const retryButton = screen.getByTitle('Retry message');
      fireEvent.click(retryButton);
    });

    expect(mockOnAction).toHaveBeenCalledWith({ type: 'retry' });
  });

  it('should handle edit and delete actions', async () => {
    render(<MessageBubble message={assistantMessage} onAction={mockOnAction} />);

    const messageContainer = screen.getByText('I am doing well, thank you for asking!').closest('.group');
    
    if (messageContainer) {
      fireEvent.mouseEnter(messageContainer);
    }

    await waitFor(() => {
      const editButton = screen.getByTitle('Edit message');
      fireEvent.click(editButton);
    });

    expect(mockOnAction).toHaveBeenCalledWith({ type: 'edit' });

    // Clear previous calls
    mockOnAction.mockClear();

    await waitFor(() => {
      const deleteButton = screen.getByTitle('Delete message');
      fireEvent.click(deleteButton);
    });

    expect(mockOnAction).toHaveBeenCalledWith({ type: 'delete' });
  });

  it('should handle more actions button', async () => {
    render(<MessageBubble message={assistantMessage} onAction={mockOnAction} />);

    const messageContainer = screen.getByText('I am doing well, thank you for asking!').closest('.group');
    
    if (messageContainer) {
      fireEvent.mouseEnter(messageContainer);
    }

    await waitFor(() => {
      const moreButton = screen.getByTitle('More actions');
      fireEvent.click(moreButton);
    });

    // Should toggle showActions state (implementation detail)
    expect(screen.getByTitle('More actions')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <MessageBubble 
        message={userMessage} 
        onAction={mockOnAction} 
        className="custom-class" 
      />
    );

    expect(container.querySelector('.custom-class')).toBeInTheDocument();
  });

  it('should handle isLast prop', () => {
    render(<MessageBubble message={assistantMessage} onAction={mockOnAction} isLast={true} />);

    // The isLast prop doesn't directly affect rendering in this implementation,
    // but we can verify the component renders correctly
    expect(screen.getByText('I am doing well, thank you for asking!')).toBeInTheDocument();
  });

  it('should handle message without metadata', () => {
    const messageWithoutMetadata = {
      ...assistantMessage,
      metadata: undefined
    };

    render(<MessageBubble message={messageWithoutMetadata} onAction={mockOnAction} />);

    expect(screen.getByTestId('sanitized-markdown')).toBeInTheDocument();
    // Should not show metadata badges
    expect(screen.queryByText('95% confidence')).not.toBeInTheDocument();
    expect(screen.queryByText('gpt-4')).not.toBeInTheDocument();
  });

  it('should handle partial metadata', () => {
    const messageWithPartialMetadata = {
      ...assistantMessage,
      metadata: {
        confidence: 0.8
        // Missing model and latencyMs
      }
    };

    render(<MessageBubble message={messageWithPartialMetadata} onAction={mockOnAction} />);

    expect(screen.getByText('80% confidence')).toBeInTheDocument();
    expect(screen.queryByText('gpt-4')).not.toBeInTheDocument();
    expect(screen.queryByText('1200ms')).not.toBeInTheDocument();
  });

  it('should handle mouse leave event', async () => {
    render(<MessageBubble message={assistantMessage} onAction={mockOnAction} />);

    const messageContainer = screen.getByText('I am doing well, thank you for asking!').closest('.group');
    
    if (messageContainer) {
      fireEvent.mouseEnter(messageContainer);
      
      await waitFor(() => {
        expect(screen.getByTitle('Copy message')).toBeInTheDocument();
      });

      fireEvent.mouseLeave(messageContainer);
    }

    // Action buttons should be hidden after mouse leave
    // (This is handled by CSS/animation, so we can't easily test the hiding)
    expect(messageContainer).toBeInTheDocument();
  });
});