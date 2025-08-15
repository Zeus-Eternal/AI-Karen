import { 
  useQuery, 
  useMutation, 
  useQueryClient,
  UseQueryOptions,
  UseMutationOptions,
  useInfiniteQuery
} from '@tanstack/react-query';
import { queryKeys, invalidateQueries } from '../../lib/queryClient';

// Types for chat operations
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  correlationId: string;
  metadata?: {
    confidence?: number;
    latencyMs?: number;
    model?: string;
    sources?: string[];
    reasoning?: string;
    tokens?: number;
  };
  status: 'sending' | 'sent' | 'streaming' | 'completed' | 'error';
  retryCount?: number;
}

export interface Conversation {
  id: string;
  title: string;
  userId: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  lastMessage?: ChatMessage;
}

export interface SendMessageRequest {
  conversationId: string;
  content: string;
  role?: 'user' | 'system';
  parentMessageId?: string;
}

export interface SendMessageResponse {
  message: ChatMessage;
  conversationId: string;
}

// API functions
const chatApi = {
  // Fetch conversations with pagination
  getConversations: async (page = 0, limit = 20): Promise<{
    conversations: Conversation[];
    hasMore: boolean;
    total: number;
  }> => {
    const response = await fetch(`/api/conversations?page=${page}&limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch conversations');
    return response.json();
  },

  // Fetch specific conversation
  getConversation: async (id: string): Promise<Conversation> => {
    const response = await fetch(`/api/conversations/${id}`);
    if (!response.ok) throw new Error('Failed to fetch conversation');
    return response.json();
  },

  // Fetch messages for a conversation
  getMessages: async (conversationId: string, page = 0, limit = 50): Promise<{
    messages: ChatMessage[];
    hasMore: boolean;
    total: number;
  }> => {
    const response = await fetch(
      `/api/conversations/${conversationId}/messages?page=${page}&limit=${limit}`
    );
    if (!response.ok) throw new Error('Failed to fetch messages');
    return response.json();
  },

  // Send a message
  sendMessage: async (request: SendMessageRequest): Promise<SendMessageResponse> => {
    const response = await fetch('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to send message');
    return response.json();
  },

  // Create new conversation
  createConversation: async (title?: string): Promise<Conversation> => {
    const response = await fetch('/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    if (!response.ok) throw new Error('Failed to create conversation');
    return response.json();
  },

  // Delete conversation
  deleteConversation: async (id: string): Promise<void> => {
    const response = await fetch(`/api/conversations/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete conversation');
  },
};

// Query hooks
export const useConversations = (
  options?: Omit<UseQueryOptions<{
    conversations: Conversation[];
    hasMore: boolean;
    total: number;
  }>, 'queryKey' | 'queryFn'>
) => {
  return useInfiniteQuery({
    queryKey: queryKeys.chat.conversations(),
    queryFn: ({ pageParam = 0 }) => chatApi.getConversations(pageParam),
    getNextPageParam: (lastPage, pages) => 
      lastPage.hasMore ? pages.length : undefined,
    initialPageParam: 0,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  });
};

export const useConversation = (
  id: string,
  options?: Omit<UseQueryOptions<Conversation>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.chat.conversation(id),
    queryFn: () => chatApi.getConversation(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
};

export const useMessages = (
  conversationId: string,
  options?: Omit<UseQueryOptions<{
    messages: ChatMessage[];
    hasMore: boolean;
    total: number;
  }>, 'queryKey' | 'queryFn'>
) => {
  return useInfiniteQuery({
    queryKey: queryKeys.chat.messages(conversationId),
    queryFn: ({ pageParam = 0 }) => chatApi.getMessages(conversationId, pageParam),
    getNextPageParam: (lastPage, pages) => 
      lastPage.hasMore ? pages.length : undefined,
    initialPageParam: 0,
    enabled: !!conversationId,
    staleTime: 1 * 60 * 1000, // 1 minute (messages change frequently)
    ...options,
  });
};

// Mutation hooks
export const useSendMessage = (
  options?: UseMutationOptions<SendMessageResponse, Error, SendMessageRequest>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: chatApi.sendMessage,
    onSuccess: (data, variables) => {
      // Optimistically update the messages cache
      queryClient.setQueryData(
        queryKeys.chat.messages(variables.conversationId),
        (old: any) => {
          if (!old) return old;
          return {
            ...old,
            pages: old.pages.map((page: any, index: number) => 
              index === 0 
                ? { ...page, messages: [data.message, ...page.messages] }
                : page
            ),
          };
        }
      );

      // Invalidate related queries
      invalidateQueries.conversation(variables.conversationId);
      invalidateQueries.allChat();
    },
    onError: (error, variables) => {
      console.error('Failed to send message:', error);
      // Could implement optimistic rollback here
    },
    ...options,
  });
};

export const useCreateConversation = (
  options?: UseMutationOptions<Conversation, Error, string | undefined>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: chatApi.createConversation,
    onSuccess: (data) => {
      // Add new conversation to the cache
      queryClient.setQueryData(
        queryKeys.chat.conversations(),
        (old: any) => {
          if (!old) return old;
          return {
            ...old,
            pages: old.pages.map((page: any, index: number) => 
              index === 0 
                ? { ...page, conversations: [data, ...page.conversations] }
                : page
            ),
          };
        }
      );

      invalidateQueries.allChat();
    },
    ...options,
  });
};

export const useDeleteConversation = (
  options?: UseMutationOptions<void, Error, string>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: chatApi.deleteConversation,
    onSuccess: (_, conversationId) => {
      // Remove conversation from cache
      queryClient.setQueryData(
        queryKeys.chat.conversations(),
        (old: any) => {
          if (!old) return old;
          return {
            ...old,
            pages: old.pages.map((page: any) => ({
              ...page,
              conversations: page.conversations.filter(
                (conv: Conversation) => conv.id !== conversationId
              ),
            })),
          };
        }
      );

      // Remove conversation-specific data
      queryClient.removeQueries({ 
        queryKey: queryKeys.chat.conversation(conversationId) 
      });

      invalidateQueries.allChat();
    },
    ...options,
  });
};