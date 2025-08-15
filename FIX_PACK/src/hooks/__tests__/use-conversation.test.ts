# Path: ui_launchers/web_ui/src/hooks/__tests__/use-conversation.test.ts

import { renderHook, act, waitFor } from '@testing-library/react';
import { useConversation } from '../use-conversation';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { useTelemetry } from '@/hooks/use-telemetry';
import { useNetworkResilience } from '@/hooks/use-network-resilience';

// Mock dependencies
jest.mock('@/contexts/AuthContext');
jest.mock('@/hooks/use-toast');
jest.mock('@/hooks/use-telemetry');
jest.mock('@/hooks/use-network-resilience');

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseToast = useToast as jest.MockedFunction<typeof useToast>;
const mockUseTelemetry = useTelemetry as jest.MockedFunction<typeof useTelemetry>;
const mockUseNetworkResilience = useNetworkResilience as jest.MockedFunction<typeof useNetworkResilience>;

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Mock crypto.randomUUID
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: jest.fn(() => 'mock-uuid-123')
  }
});

describe('useConversation', () => {
  const mockToast = jest.fn();
  const mockTrack = jest.fn();
  const mockSetCorrelationId = jest.fn();
  const mockExecuteWithRetry = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseAuth.mockReturnValue({
      user: { user_id: 'test-user-123' },
      isAuthenticated: true
    } as any);

    mockUseToast.mockReturnValue({
      toast: mockToast
    } as any);

    mockUseTelemetry.mockReturnValue({
      track: mockTrack,
      setCorrelationId: mockSetCorrelationId
    } as any);

    mockUseNetworkResilience.mockReturnValue({
      executeWithRetry: mockExecuteWithRetry
    } as any);

    mockExecuteWithRetry.mockImplementation((fn) => fn());
  });

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useConversation());

    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isTyping).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should initialize session and conversation IDs', async () => {
    const { result } = renderHook(() => useConversation());

    await waitFor(() => {
      expect(result.current.sessionId).toBe('mock-uuid-123');
      expect(result.current.conversationId).toBe('mock-uuid-123');
    });

    expect(mockSetCorrelationId).toHaveBeenCalledWith('mock-uuid-123');
    expect(mockTrack).toHaveBeenCalledWith('conversation_started', {
      sessionId: 'mock-uuid-123',
      conversationId: 'mock-uuid-123'
    });
  });

  it('should send message successfully', async () => {
    const mockResponse = {
      ok: true,
      body: {
        getReader: () => ({
          read: jest.fn()
            .mockResolvedValueOnce({
              value: new TextEncoder().encode('data: {"content": "Hello"}'),
              done: false
            })
            .mockResolvedValueOnce({
              value: new TextEncoder().encode('data: {"content": " World"}'),
              done: false
            })
            .mockResolvedValueOnce({
              done: true
            })
        })
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const { result } = renderHook(() => useConversation());

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe('user');
    expect(result.current.messages[0].content).toBe('Test message');
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.messages[1].content).toBe('Hello World');
  });

  it('should handle API errors gracefully', async () => {
    const mockResponse = {
      ok: false,
      status: 500,
      statusText: 'Internal Server Error'
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const { result } = renderHook(() => useConversation());

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    expect(result.current.error).toBe('HTTP 500: Internal Server Error');
    expect(mockToast).toHaveBeenCalledWith({
      variant: 'destructive',
      title: 'Message Failed',
      description: 'HTTP 500: Internal Server Error'
    });
  });

  it('should handle network errors', async () => {
    const networkError = new Error('Network error');
    mockFetch.mockRejectedValueOnce(networkError);

    const { result } = renderHook(() => useConversation());

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    expect(result.current.error).toBe('Network error');
    expect(mockTrack).toHaveBeenCalledWith('message_error', {
      error: 'Network error',
      conversationId: expect.any(String)
    });
  });

  it('should clear messages', async () => {
    const { result } = renderHook(() => useConversation({
      initialMessages: [
        {
          id: '1',
          role: 'user',
          content: 'Test',
          timestamp: new Date(),
          status: 'sent'
        }
      ]
    }));

    expect(result.current.messages).toHaveLength(1);

    act(() => {
      result.current.clearMessages();
    });

    expect(result.current.messages).toHaveLength(0);
    expect(mockTrack).toHaveBeenCalledWith('conversation_cleared', {
      conversationId: expect.any(String)
    });
  });

  it('should retry last message', async () => {
    const mockResponse = {
      ok: true,
      body: {
        getReader: () => ({
          read: jest.fn()
            .mockResolvedValueOnce({
              value: new TextEncoder().encode('data: {"content": "Retry response"}'),
              done: false
            })
            .mockResolvedValueOnce({
              done: true
            })
        })
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const { result } = renderHook(() => useConversation());

    // Send initial message
    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    // Clear fetch mock and set up retry response
    mockFetch.mockClear();
    mockFetch.mockResolvedValueOnce(mockResponse as any);

    // Retry last message
    await act(async () => {
      await result.current.retryLastMessage();
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('should abort current request', async () => {
    const { result } = renderHook(() => useConversation());

    // Start a message (this will set up the abort controller)
    act(() => {
      result.current.sendMessage('Test message');
    });

    // Abort the request
    act(() => {
      result.current.abortCurrentRequest();
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isTyping).toBe(false);
    expect(mockTrack).toHaveBeenCalledWith('message_aborted', {
      conversationId: expect.any(String)
    });
  });

  it('should update message', () => {
    const initialMessage = {
      id: 'test-message',
      role: 'user' as const,
      content: 'Original content',
      timestamp: new Date(),
      status: 'sent' as const
    };

    const { result } = renderHook(() => useConversation({
      initialMessages: [initialMessage]
    }));

    act(() => {
      result.current.updateMessage('test-message', {
        content: 'Updated content',
        status: 'completed'
      });
    });

    const updatedMessage = result.current.messages.find(m => m.id === 'test-message');
    expect(updatedMessage?.content).toBe('Updated content');
    expect(updatedMessage?.status).toBe('completed');
  });

  it('should delete message', () => {
    const initialMessage = {
      id: 'test-message',
      role: 'user' as const,
      content: 'Test content',
      timestamp: new Date(),
      status: 'sent' as const
    };

    const { result } = renderHook(() => useConversation({
      initialMessages: [initialMessage]
    }));

    expect(result.current.messages).toHaveLength(1);

    act(() => {
      result.current.deleteMessage('test-message');
    });

    expect(result.current.messages).toHaveLength(0);
    expect(mockTrack).toHaveBeenCalledWith('message_deleted', {
      messageId: 'test-message',
      conversationId: expect.any(String)
    });
  });

  it('should handle streaming response correctly', async () => {
    const mockResponse = {
      ok: true,
      body: {
        getReader: () => ({
          read: jest.fn()
            .mockResolvedValueOnce({
              value: new TextEncoder().encode('data: {"text": "Hello"}\n'),
              done: false
            })
            .mockResolvedValueOnce({
              value: new TextEncoder().encode('data: {"text": " there"}\n'),
              done: false
            })
            .mockResolvedValueOnce({
              value: new TextEncoder().encode('data: {"text": "!"}\n'),
              done: false
            })
            .mockResolvedValueOnce({
              done: true
            })
        })
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const { result } = renderHook(() => useConversation());

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    const assistantMessage = result.current.messages.find(m => m.role === 'assistant');
    expect(assistantMessage?.content).toBe('Hello there!');
    expect(assistantMessage?.status).toBe('completed');
  });

  it('should call callbacks when provided', async () => {
    const onMessageSent = jest.fn();
    const onMessageReceived = jest.fn();
    const onError = jest.fn();

    const mockResponse = {
      ok: true,
      body: {
        getReader: () => ({
          read: jest.fn()
            .mockResolvedValueOnce({
              value: new TextEncoder().encode('data: {"content": "Response"}'),
              done: false
            })
            .mockResolvedValueOnce({
              done: true
            })
        })
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse as any);

    const { result } = renderHook(() => useConversation({
      onMessageSent,
      onMessageReceived,
      onError
    }));

    await act(async () => {
      await result.current.sendMessage('Test message');
    });

    expect(onMessageSent).toHaveBeenCalledWith(
      expect.objectContaining({
        role: 'user',
        content: 'Test message'
      })
    );

    expect(onMessageReceived).toHaveBeenCalledWith(
      expect.objectContaining({
        role: 'assistant',
        content: 'Response'
      })
    );
  });
});