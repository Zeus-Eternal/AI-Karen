import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useConversations,
  useConversation,
  useMessages,
  useSendMessage,
  useCreateConversation,
  useDeleteConversation,
  type Conversation,
  type ChatMessage,
} from '../use-chat-queries';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Test data
const mockConversation: Conversation = {
  id: 'conv-1',
  title: 'Test Conversation',
  userId: 'user-1',
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01'),
  messageCount: 2,
};

const mockMessage: ChatMessage = {
  id: 'msg-1',
  role: 'user',
  content: 'Hello',
  timestamp: new Date('2024-01-01'),
  correlationId: 'corr-1',
  status: 'completed',
};

// Test wrapper
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('useConversations', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch conversations successfully', async () => {
    const mockResponse = {
      conversations: [mockConversation],
      hasMore: false,
      total: 1,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const { result } = renderHook(() => useConversations(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.pages[0]).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith('/api/conversations?page=0&limit=20');
  });

  it('should handle fetch error', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    const { result } = renderHook(() => useConversations(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });

  it('should support infinite loading', async () => {
    const page1Response = {
      conversations: [mockConversation],
      hasMore: true,
      total: 2,
    };

    const page2Response = {
      conversations: [{ ...mockConversation, id: 'conv-2' }],
      hasMore: false,
      total: 2,
    };

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(page1Response),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(page2Response),
      });

    const { result } = renderHook(() => useConversations(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Fetch next page
    result.current.fetchNextPage();

    await waitFor(() => {
      expect(result.current.data?.pages).toHaveLength(2);
    });

    expect(result.current.data?.pages[0]).toEqual(page1Response);
    expect(result.current.data?.pages[1]).toEqual(page2Response);
  });
});

describe('useConversation', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should fetch single conversation', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockConversation),
    });

    const { result } = renderHook(() => useConversation('conv-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockConversation);
    expect(mockFetch).toHaveBeenCalledWith('/api/conversations/conv-1');
  });

  it('should not fetch when id is empty', () => {
    const { result } = renderHook(() => useConversation(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isIdle).toBe(true);
    expect(mockFetch).not.toHaveBeenCalled();
  });
});

describe('useMessages', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should fetch messages for conversation', async () => {
    const mockResponse = {
      messages: [mockMessage],
      hasMore: false,
      total: 1,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const { result } = renderHook(() => useMessages('conv-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.pages[0]).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith('/api/conversations/conv-1/messages?page=0&limit=50');
  });
});

describe('useSendMessage', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should send message successfully', async () => {
    const mockResponse = {
      message: mockMessage,
      conversationId: 'conv-1',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const { result } = renderHook(() => useSendMessage(), {
      wrapper: createWrapper(),
    });

    const sendRequest = {
      conversationId: 'conv-1',
      content: 'Hello',
      role: 'user' as const,
    };

    result.current.mutate(sendRequest);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sendRequest),
    });
  });
});

describe('useCreateConversation', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should create conversation successfully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockConversation),
    });

    const { result } = renderHook(() => useCreateConversation(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('New Conversation');

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockConversation);
    expect(mockFetch).toHaveBeenCalledWith('/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'New Conversation' }),
    });
  });
});

describe('useDeleteConversation', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should delete conversation successfully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
    });

    const { result } = renderHook(() => useDeleteConversation(), {
      wrapper: createWrapper(),
    });

    result.current.mutate('conv-1');

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/conversations/conv-1', {
      method: 'DELETE',
    });
  });
});