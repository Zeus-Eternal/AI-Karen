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
// Default query options
const defaultOptions: DefaultOptions = {
  queries: {
    // Stale time - how long data is considered fresh
    staleTime: 5 * 60 * 1000, // 5 minutes
    // Cache time - how long data stays in cache after becoming unused
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    // Retry configuration
    retry: (failureCount, error: unknown) => {
      // Don't retry on 4xx errors (client errors)
      const errorWithStatus = error as { status?: number };
      if (errorWithStatus?.status && errorWithStatus.status >= 400 && errorWithStatus.status < 500) {
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
      onError: (error, _variables, _context, _mutation) => {
        // Log errors to console instead of using store to avoid SSR issues
        if (typeof window !== 'undefined') {
          const message = resolveErrorMessage(error, 'An error occurred');
          console.error('Mutation error:', message);
        }
      },
      onSuccess: () => {
        // Clear errors on success
        if (typeof window !== 'undefined') {
          console.log('Mutation succeeded');
        }
      },
    }),
    queryCache: new QueryCache({
      onError: (error, query) => {
        // Log errors to console instead of using store to avoid SSR issues
        if (typeof window !== 'undefined') {
          const message = resolveErrorMessage(error, 'Failed to load data');
          console.error('Query error:', message);

          if (query.state.fetchStatus === 'fetching' && query.state.data !== undefined) {
            console.warn('Data sync issue: Unable to refresh data. Using cached version.');
          }
        }
      },
      onSuccess: () => {
        // Clear errors on success
        if (typeof window !== 'undefined') {
          console.log('Query succeeded');
        }
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
// Query client instance - create it lazily to avoid SSR issues
let queryClientInstance: QueryClient | null = null;

export const getQueryClient = () => {
  if (!queryClientInstance) {
    queryClientInstance = createQueryClient();
  }
  return queryClientInstance;
};

// For backward compatibility, we export a getter that creates the client if needed
export const queryClient = () => {
  console.log('queryClient: Function called');
  const client = getQueryClient();
  console.log('queryClient: Client retrieved successfully');
  return client;
};
// Helper function to invalidate related queries
export const invalidateQueries = {
  auth: () => getQueryClient().invalidateQueries({ queryKey: queryKeys.auth.user() }),
  dashboard: () => getQueryClient().invalidateQueries({ queryKey: queryKeys.dashboard.all() }),
  chat: () => getQueryClient().invalidateQueries({ queryKey: queryKeys.chat.all() }),
  memory: () => getQueryClient().invalidateQueries({ queryKey: queryKeys.memory.all() }),
  plugins: () => getQueryClient().invalidateQueries({ queryKey: queryKeys.plugins.all() }),
  providers: () => getQueryClient().invalidateQueries({ queryKey: queryKeys.providers.all() }),
  users: () => getQueryClient().invalidateQueries({ queryKey: queryKeys.users.all() }),
  system: () => getQueryClient().invalidateQueries({ queryKey: queryKeys.system.all() }),
  all: () => getQueryClient().invalidateQueries(),
};
// Helper function to prefetch common queries
export const prefetchQueries = {
  dashboard: async () => {
    const client = getQueryClient();
    await Promise.all([
      client.prefetchQuery({
        queryKey: queryKeys.dashboard.metrics(),
        queryFn: () => fetch('/api/dashboard/metrics').then(res => res.json()),
      }),
      client.prefetchQuery({
        queryKey: queryKeys.dashboard.health(),
        queryFn: () => fetch('/api/system/health').then(res => res.json()),
      }),
    ]);
  },
  user: async (userId: string) => {
    const client = getQueryClient();
    await client.prefetchQuery({
      queryKey: queryKeys.users.user(userId),
      queryFn: () => fetch(`/api/users/${userId}`).then(res => res.json()),
    });
  },
};
// Helper function to set query data optimistically
export const setQueryData = {
  user: (userData: unknown) => {
    getQueryClient().setQueryData(queryKeys.auth.user(), userData);
  },
  conversation: (conversationId: string, data: unknown) => {
    getQueryClient().setQueryData(queryKeys.chat.conversation(conversationId), data);
  },
  plugin: (pluginId: string, data: unknown) => {
    getQueryClient().setQueryData(queryKeys.plugins.plugin(pluginId), data);
  },
};
