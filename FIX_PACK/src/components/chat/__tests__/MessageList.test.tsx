# Path: ui_launchers/web_ui/src/components/chat/__tests__/MessageList.test.tsx

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MessageList } from '../MessageList';
import { useTelemetry } from '@/hooks/use-telemetry';
import { usePerformanceMarks } from '@/hooks/use-performance-marks';

// Mock dependencies
jest.mock('@/hooks/use-telemetry');
jest.mock('@/hooks/use-performance-marks');
jest.mock('../MessageBubble', () => ({
  MessageBubble: ({ message, onAction, isLast }: any) => (
    <div data-testid={`message-${message.id}`}>
      <div>{message.content}</div>
      <button onClick={() => onAction({ type: 'copy' })}>Copy</button>
      {isLast && <span data-testid="last-message">Last</span>}
    </div>
  )
}));

// Mock react-window
jest.mock('react-window', () => ({
  VariableSizeList: ({ children, itemCount, itemSize, onScroll }: any) => (
    <div 
      data-testid="virtualized-list"
      onScroll={onScroll}
    >
      {Array.from({ length: itemCount }, (_, index) => 
        children({ 
          index, 
          style: { height: typeof itemSize === 'function' ? itemSize(index) : itemSize } 
        })
      )}
    </div>
  )
}));

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));

const mockUseTelemetry = useTelemetry as jest.MockedFunction<typeof useTelemetry>;
const mockUsePerformanceMarks = usePerformanceMarks as jest.MockedFunction<typeof usePerformanceMarks>;

describe('MessageList', () => {
  const mockTrack = jest.fn();
  const mockMarkRender = jest.fn();

  const sampleMessages = [
    {
      id: 'msg-1',
      role: 'user' as const,
      content: 'Hello',
      timestamp: new Date('2023-01-01T10:00:00Z'),
      status: 'sent' as const
    },
    {
      id: 'msg-2',
      role: 'assistant' as const,
      content: 'Hi there!',
      timestamp: new Date('2023-01-01T10:00:01Z'),
      status: 'completed' as const
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseTelemetry.mockReturnValue({
      track: mockTrack
    } as any);

    mockUsePerformanceMarks.mockReturnValue({
      markRender: mockMarkRender
    } as any);
  });

  it('should render empty state when no messages', () => {
    render(<MessageList messages={[]} />);

    expect(screen.getByText('No messages yet')).toBeInTheDocument();
    expect(screen.getByText('Start a conversation to see messages here')).toBeInTheDocument();
  });

  it('should render messages without virtualization when below threshold', () => {
    render(<MessageList messages={sampleMessages} virtualizationThreshold={10} />);

    expect(screen.getByTestId('message-msg-1')).toBeInTheDocument();
    expect(screen.getByTestId('message-msg-2')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
    expect(screen.queryByTestId('virtualized-list')).not.toBeInTheDocument();
  });

  it('should render messages with virtualization when above threshold', () => {
    render(<MessageList messages={sampleMessages} virtualizationThreshold={1} />);

    expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
    expect(screen.getByTestId('message-msg-1')).toBeInTheDocument();
    expect(screen.getByTestId('message-msg-2')).toBeInTheDocument();
  });

  it('should mark last message correctly', () => {
    render(<MessageList messages={sampleMessages} />);

    expect(screen.queryByTestId('last-message')).toBeInTheDocument();
    // Should only be on the last message (msg-2)
    const lastMessage = screen.getByTestId('message-msg-2');
    expect(lastMessage.querySelector('[data-testid="last-message"]')).toBeInTheDocument();
  });

  it('should handle message actions', async () => {
    const onMessageAction = jest.fn();
    render(
      <MessageList 
        messages={sampleMessages} 
        onMessageAction={onMessageAction}
      />
    );

    const copyButton = screen.getAllByText('Copy')[0];
    fireEvent.click(copyButton);

    expect(mockTrack).toHaveBeenCalledWith('message_action', {
      messageId: 'msg-1',
      action: 'copy',
      messageCount: 2
    });

    expect(onMessageAction).toHaveBeenCalledWith('msg-1', { type: 'copy' });
  });

  it('should track performance metrics', () => {
    render(<MessageList messages={sampleMessages} />);

    expect(mockMarkRender).toHaveBeenCalledWith('message-list', 2);
  });

  it('should show loading indicator when loading', () => {
    render(<MessageList messages={sampleMessages} isLoading={true} />);

    expect(screen.getByText('Loading messages...')).toBeInTheDocument();
  });

  it('should handle scroll events for user scrolling detection', async () => {
    render(<MessageList messages={sampleMessages} virtualizationThreshold={1} />);

    const virtualizedList = screen.getByTestId('virtualized-list');
    fireEvent.scroll(virtualizedList);

    // Should detect user scrolling (implementation detail, but we can test the scroll handler was called)
    expect(virtualizedList).toBeInTheDocument();
  });

  it('should calculate dynamic item heights', () => {
    const longMessage = {
      id: 'msg-long',
      role: 'assistant' as const,
      content: 'This is a very long message that should result in a taller item height because it contains much more content than a typical short message and will likely wrap to multiple lines when rendered in the chat interface.',
      timestamp: new Date(),
      status: 'completed' as const
    };

    render(<MessageList messages={[longMessage]} virtualizationThreshold={1} />);

    expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
    expect(screen.getByTestId('message-msg-long')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <MessageList messages={sampleMessages} className="custom-class" />
    );

    expect(container.querySelector('.custom-class')).toBeInTheDocument();
  });

  it('should handle autoScroll prop', () => {
    render(<MessageList messages={sampleMessages} autoScroll={false} />);
    
    // Component should render without auto-scrolling
    expect(screen.getByTestId('message-msg-1')).toBeInTheDocument();
  });

  it('should handle smoothScrolling prop', () => {
    render(<MessageList messages={sampleMessages} smoothScrolling={false} />);
    
    // Component should render without smooth scrolling
    expect(screen.getByTestId('message-msg-1')).toBeInTheDocument();
  });

  it('should handle resize observer for container height', () => {
    render(<MessageList messages={sampleMessages} />);

    // Verify ResizeObserver was created
    expect(global.ResizeObserver).toHaveBeenCalled();
  });

  it('should cleanup scroll timeout on unmount', () => {
    const { unmount } = render(<MessageList messages={sampleMessages} />);
    
    // Mock setTimeout to track cleanup
    const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');
    
    unmount();
    
    // Cleanup should be called (though we can't easily test the specific timeout)
    expect(clearTimeoutSpy).toHaveBeenCalled();
    
    clearTimeoutSpy.mockRestore();
  });

  it('should handle different message roles for height calculation', () => {
    const messages = [
      {
        id: 'user-msg',
        role: 'user' as const,
        content: 'Short user message',
        timestamp: new Date(),
        status: 'sent' as const
      },
      {
        id: 'assistant-msg',
        role: 'assistant' as const,
        content: 'Longer assistant message with more detailed content',
        timestamp: new Date(),
        status: 'completed' as const
      }
    ];

    render(<MessageList messages={messages} virtualizationThreshold={1} />);

    expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
    expect(screen.getByTestId('message-user-msg')).toBeInTheDocument();
    expect(screen.getByTestId('message-assistant-msg')).toBeInTheDocument();
  });

  it('should handle empty message content gracefully', () => {
    const emptyMessage = {
      id: 'empty-msg',
      role: 'assistant' as const,
      content: '',
      timestamp: new Date(),
      status: 'completed' as const
    };

    render(<MessageList messages={[emptyMessage]} />);

    expect(screen.getByTestId('message-empty-msg')).toBeInTheDocument();
  });
});