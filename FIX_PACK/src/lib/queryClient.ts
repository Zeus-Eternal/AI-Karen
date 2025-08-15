import { QueryClient, DefaultOptions } from '@tanstack/react-query';

// Default query options with cache invalidation strategies
const defaultOptions: DefaultOptions = {
  queries: {
    // Cache for 5 minutes by default
    staleTime: 5 * 60 * 1000,
    // Keep in cache for 10 minutes
    gcTime: 10 * 60 * 1000,
    // Retry failed requests 3 times with exponential backoff
    retry: (failureCount, error: any) => {
      // Don't retry on 4xx errors (client errors)
      if (error?.status >= 400 && error?.status < 500) {
        return false;
      }
      return failureCount < 3;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    // Refetch on window focus for real-time data
    refetchOnWindowFocus: true,
    // Don't refetch on reconnect by default (can be overridden per query)
    refetchOnReconnect: 'always',
  },
  mutations: {
    // Retry mutations once on network errors
    retry: (failureCount, error: any) => {
      if (error?.name === 'NetworkError' && failureCount < 1) {
        return true;
      }
      return false;
    },
  },
};

// Create the query client with optimized settings
export const queryClient = new QueryClient({
  defaultOptions,
});

// Query keys factory for consistent cache management
export const queryKeys = {
  // Chat-related queries
  chat: {
    all: ['chat'] as const,
    conversations: () => [...queryKeys.chat.all, 'conversations'] as const,
    conversation: (id: string) => [...queryKeys.chat.conversations(), id] as const,
    messages: (conversationId: string) => [...queryKeys.chat.conversation(conversationId), 'messages'] as const,
    message: (conversationId: string, messageId: string) => 
      [...queryKeys.chat.messages(conversationId), messageId] as const,
  },
  // User-related queries
  user: {
    all: ['user'] as const,
    profile: () => [...queryKeys.user.all, 'profile'] as const,
    preferences: () => [...queryKeys.user.all, 'preferences'] as const,
    sessions: () => [...queryKeys.user.all, 'sessions'] as const,
  },
  // AI provider queries
  ai: {
    all: ['ai'] as const,
    providers: () => [...queryKeys.ai.all, 'providers'] as const,
    models: (providerId?: string) => 
      providerId 
        ? [...queryKeys.ai.providers(), providerId, 'models'] as const
        : [...queryKeys.ai.all, 'models'] as const,
    capabilities: (providerId: string) => [...queryKeys.ai.providers(), providerId, 'capabilities'] as const,
  },
} as const;

// Cache invalidation utilities
export const invalidateQueries = {
  // Invalidate all chat-related data
  allChat: () => queryClient.invalidateQueries({ queryKey: queryKeys.chat.all }),
  
  // Invalidate specific conversation
  conversation: (id: string) => 
    queryClient.invalidateQueries({ queryKey: queryKeys.chat.conversation(id) }),
  
  // Invalidate messages for a conversation
  conversationMessages: (conversationId: string) => 
    queryClient.invalidateQueries({ queryKey: queryKeys.chat.messages(conversationId) }),
  
  // Invalidate user data
  userProfile: () => 
    queryClient.invalidateQueries({ queryKey: queryKeys.user.profile() }),
  
  // Invalidate AI provider data
  aiProviders: () => 
    queryClient.invalidateQueries({ queryKey: queryKeys.ai.providers() }),
};

// Prefetch utilities for performance optimization
export const prefetchQueries = {
  // Prefetch user preferences on app load
  userPreferences: () => 
    queryClient.prefetchQuery({
      queryKey: queryKeys.user.preferences(),
      queryFn: () => fetch('/api/user/preferences').then(res => res.json()),
      staleTime: 10 * 60 * 1000, // 10 minutes
    }),
  
  // Prefetch available AI providers
  aiProviders: () => 
    queryClient.prefetchQuery({
      queryKey: queryKeys.ai.providers(),
      queryFn: () => fetch('/api/ai/providers').then(res => res.json()),
      staleTime: 30 * 60 * 1000, // 30 minutes (providers don't change often)
    }),
};