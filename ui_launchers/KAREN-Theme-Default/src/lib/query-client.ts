/**
 * TanStack Query Client Configuration
 * 
 * Server state management with caching and error handling.
 * Based on requirements: 12.2, 12.3
 */
import {
  QueryClient,
  DefaultOptions,
  MutationCache,
  QueryCache,
} from '@tanstack/react-query';
import { useAppStore } from '@/store/app-store';
// Default query options
const defaultOptions: DefaultOptions = {
  queries: {
    // Stale time - how long data is considered fresh
    staleTime: 5 * 60 * 1000, // 5 minutes
    // Cache time - how long data stays in cache after becoming unused
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    // Retry configuration
    retry: (failureCount, error: any) => {
      // Don't retry on 4xx errors (client errors)
      if (error?.status >= 400 && error?.status < 500) {
        return false;
      }
      // Retry up to 3 times for other errors
      return failureCount < 3;
    },
    // Retry delay with exponential backoff
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    // Refetch on window focus (disabled by default for better UX)
    refetchOnWindowFocus: false,
    // Refetch on reconnect
    refetchOnReconnect: true,
    // Refetch on mount if data is stale
    refetchOnMount: true,
  },
  mutations: {
    // Retry mutations once
    retry: 1,
    // Retry delay for mutations
    retryDelay: 1000,
  },
};
const resolveErrorMessage = (error: unknown, fallback: string): string => {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  if (error && typeof error === 'object' && 'message' in error) {
    const message = (error as { message?: unknown }).message;
    if (typeof message === 'string') {
      return message;
    }
  }
  return fallback;
};

// Create query client with error handling
export const createQueryClient = () => {
  return new QueryClient({
    defaultOptions,
    mutationCache: new MutationCache({
      onError: (error, variables, context, _mutation) => {
        const { setError, addNotification } = useAppStore.getState();
        const message = resolveErrorMessage(error, 'An error occurred');
        setError('mutation', message);
        addNotification({
          type: 'error',
          title: 'Operation Failed',
          message,
        });
      },
      onSuccess: () => {
        const { clearError } = useAppStore.getState();
        clearError('mutation');
      },
    }),
    queryCache: new QueryCache({
      onError: (error, query) => {
        const { setError, addNotification } = useAppStore.getState();
        const message = resolveErrorMessage(error, 'Failed to load data');

        if (query.state.fetchStatus === 'fetching' && query.state.data !== undefined) {
          addNotification({
            type: 'warning',
            title: 'Data Sync Issue',
            message: 'Unable to refresh data. Using cached version.',
          });
        } else {
          setError('query', message);
        }
      },
      onSuccess: () => {
        const { clearError } = useAppStore.getState();
        clearError('query');
      },
    }),
  });
};
// Query keys factory for consistent key management
export const queryKeys = {
  // Authentication
  auth: {
    user: () => ['auth', 'user'] as const,
    permissions: () => ['auth', 'permissions'] as const,
  },
  // Dashboard
  dashboard: {
    all: () => ['dashboard'] as const,
    metrics: () => ['dashboard', 'metrics'] as const,
    health: () => ['dashboard', 'health'] as const,
  },
  // Chat
  chat: {
    all: () => ['chat'] as const,
    conversations: () => ['chat', 'conversations'] as const,
    conversation: (id: string) => ['chat', 'conversations', id] as const,
    messages: (conversationId: string) => ['chat', 'messages', conversationId] as const,
  },
  // Memory
  memory: {
    all: () => ['memory'] as const,
    analytics: () => ['memory', 'analytics'] as const,
    search: (query: string) => ['memory', 'search', query] as const,
    network: () => ['memory', 'network'] as const,
  },
  // Plugins
  plugins: {
    all: () => ['plugins'] as const,
    installed: () => ['plugins', 'installed'] as const,
    marketplace: () => ['plugins', 'marketplace'] as const,
    plugin: (id: string) => ['plugins', 'plugin', id] as const,
  },
  // Providers
  providers: {
    all: () => ['providers'] as const,
    list: () => ['providers', 'list'] as const,
    provider: (id: string) => ['providers', 'provider', id] as const,
    models: (providerId: string) => ['providers', 'models', providerId] as const,
  },
  // Users
  users: {
    all: () => ['users'] as const,
    list: () => ['users', 'list'] as const,
    user: (id: string) => ['users', 'user', id] as const,
    roles: () => ['users', 'roles'] as const,
  },
  // System
  system: {
    all: () => ['system'] as const,
    health: () => ['system', 'health'] as const,
    metrics: () => ['system', 'metrics'] as const,
    logs: () => ['system', 'logs'] as const,
  },
} as const;
// Query client instance
export const queryClient = createQueryClient();
// Helper function to invalidate related queries
export const invalidateQueries = {
  auth: () => queryClient.invalidateQueries({ queryKey: queryKeys.auth.user() }),
  dashboard: () => queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all() }),
  chat: () => queryClient.invalidateQueries({ queryKey: queryKeys.chat.all() }),
  memory: () => queryClient.invalidateQueries({ queryKey: queryKeys.memory.all() }),
  plugins: () => queryClient.invalidateQueries({ queryKey: queryKeys.plugins.all() }),
  providers: () => queryClient.invalidateQueries({ queryKey: queryKeys.providers.all() }),
  users: () => queryClient.invalidateQueries({ queryKey: queryKeys.users.all() }),
  system: () => queryClient.invalidateQueries({ queryKey: queryKeys.system.all() }),
  all: () => queryClient.invalidateQueries(),
};
// Helper function to prefetch common queries
export const prefetchQueries = {
  dashboard: async () => {
    await Promise.all([
      queryClient.prefetchQuery({
        queryKey: queryKeys.dashboard.metrics(),
        queryFn: () => fetch('/api/dashboard/metrics').then(res => res.json()),
      }),
      queryClient.prefetchQuery({
        queryKey: queryKeys.dashboard.health(),
        queryFn: () => fetch('/api/system/health').then(res => res.json()),
      }),
    ]);
  },
  user: async (userId: string) => {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.users.user(userId),
      queryFn: () => fetch(`/api/users/${userId}`).then(res => res.json()),
    });
  },
};
// Helper function to set query data optimistically
export const setQueryData = {
  user: (userData: any) => {
    queryClient.setQueryData(queryKeys.auth.user(), userData);
  },
  conversation: (conversationId: string, data: any) => {
    queryClient.setQueryData(queryKeys.chat.conversation(conversationId), data);
  },
  plugin: (pluginId: string, data: any) => {
    queryClient.setQueryData(queryKeys.plugins.plugin(pluginId), data);
  },
};
