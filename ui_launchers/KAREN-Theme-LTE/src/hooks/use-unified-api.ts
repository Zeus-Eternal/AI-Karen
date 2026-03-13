// ui_launchers/KAREN-Theme-Default/src/hooks/use-unified-api.ts
"use client";

import React from 'react';
const { useState, useCallback, useRef, useEffect } = React;
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/hooks/use-auth";
import { apiClient } from "@/lib/base-api-client";

// Define the missing User interface with the properties we need
export interface ExtendedUser {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: string;
  permissions: string[];
  preferences?: Record<string, unknown>;
  createdAt: string;
  lastLogin?: string;
  userId?: string;  // Adding userId property
  tenantId?: string; // Adding tenantId property
}

// Define interfaces for the API requests/responses since they're not exported from base-api-client
export interface CopilotAssistRequest {
  input: string;
  context?: Record<string, unknown>;
  user_id?: string;
  org_id?: string;
}

export interface CopilotAssistResponse {
  response: string;
  suggestions?: Array<{ text: string; confidence: number }>;
  actions?: Array<{ id: string; title: string; description: string }>;
  workflows?: Array<{ id: string; name: string; description: string }>;
  artifacts?: Array<{ id: string; title: string; type: string }>;
}

export interface MemorySearchRequest {
  query: string;
  limit?: number;
  user_id?: string;
  org_id?: string;
}

export interface MemorySearchResponse {
  results: Array<{ id: string; content: string; relevance: number }>;
  total: number;
  page?: number;
}

export interface MemoryCommitRequest {
  content: string;
  type?: string;
  metadata?: Record<string, unknown>;
  user_id?: string;
  org_id?: string;
}

export interface MemoryCommitResponse {
  success: boolean;
  id?: string;
  timestamp?: string;
}

export interface UseUnifiedApiOptions {
  autoToast?: boolean;
  enableCaching?: boolean;
  cacheTimeout?: number;
  onError?: (error: Error, operation: string) => void;
  onSuccess?: (data: unknown, operation: string) => void;
}

export interface UseUnifiedApiReturn {
  // Copilot operations
  copilotAssist: (
    request: Omit<CopilotAssistRequest, "user_id">
  ) => Promise<CopilotAssistResponse>;

  // Memory operations
  memorySearch: (
    request: Omit<MemorySearchRequest, "user_id">
  ) => Promise<MemorySearchResponse>;
  memoryCommit: (
    request: Omit<MemoryCommitRequest, "user_id">
  ) => Promise<MemoryCommitResponse>;
  memoryUpdate: (
    memoryId: string,
    updates: Partial<MemoryCommitRequest>
  ) => Promise<MemoryCommitResponse>;
  memoryDelete: (
    memoryId: string,
    options?: { hard_delete?: boolean }
  ) => Promise<{ success: boolean; correlation_id: string }>;

  // Batch operations
  batchMemoryOperations: (
    operations: Array<{ type: string; data: unknown }>
  ) => Promise<Array<{ success: boolean; result?: unknown; error?: string }>>;

  // Utility operations
  healthCheck: () => Promise<unknown>;

  // State
  isLoading: boolean;
  error: Error | null;
  lastResponse: unknown;

  // Cache management
  clearCache: () => void;
  getCacheStats: () => Record<string, unknown>;
}

export interface CacheEntry {
  data: unknown;
  timestamp: number;
  key: string;
}

export function useUnifiedApi(
  options: UseUnifiedApiOptions = {}
): UseUnifiedApiReturn {
  const {
    autoToast = true,
    enableCaching = true,
    cacheTimeout = 300000, // 5 minutes
    onError,
    onSuccess,
  } = options;

  const { user } = useAuth() as { user: ExtendedUser | null };
  const toastState = useToast();
  const api = apiClient;

  // State
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastResponse, setLastResponse] = useState<unknown>(null);

  // Cache
  const cache = useRef<Map<string, CacheEntry>>(new Map());
  const activeRequests = useRef<Map<string, Promise<unknown>>>(new Map());

  // Generate cache key
  const generateCacheKey = useCallback(
    (operation: string, params: Record<string, unknown> = {}): string => {
      return `${operation}_${JSON.stringify(params)}`;
    },
    []
  );

  // Check cache
  const getCachedData = useCallback(
    (key: string): unknown | null => {
      if (!enableCaching) return null;

      const entry = cache.current.get(key);
      if (!entry) return null;

      const isExpired = Date.now() - entry.timestamp > cacheTimeout;
      if (isExpired) {
        cache.current.delete(key);
        return null;
      }

      return entry.data;
    },
    [enableCaching, cacheTimeout]
  );

  // Set cache data
  const setCachedData = useCallback(
    (key: string, data: unknown): void => {
      if (!enableCaching) return;

      cache.current.set(key, {
        data,
        timestamp: Date.now(),
        key,
      });
    },
    [enableCaching]
  );

  // Handle API request with caching and deduplication
  const handleApiRequest = useCallback(
    async <T>(
      operation: string,
      requestFn: () => Promise<T>,
      params?: Record<string, unknown>
    ): Promise<T> => {
      const cacheKey = params ? generateCacheKey(operation, params) : operation;

      // Check cache first
      const cachedData = getCachedData(cacheKey);
      if (cachedData) {
        setLastResponse(cachedData);
        return cachedData as T;
      }

      // Check for active request (deduplication)
      const activeRequest = activeRequests.current.get(cacheKey);
      if (activeRequest) {
        return activeRequest as Promise<T>;
      }

      setIsLoading(true);
      setError(null);

      const requestPromise = requestFn();
      activeRequests.current.set(cacheKey, requestPromise);

      try {
        const result = await requestPromise;

        // Cache the result
        setCachedData(cacheKey, result);
        setLastResponse(result);

        if (onSuccess) {
          onSuccess(result, operation);
        }

        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Unknown error");
        setError(error);

        if (autoToast && toastState.addToast) {
          toastState.addToast({
            type: "error",
            title: "API Error",
            message: error.message,
            duration: 5000,
          });
        }

        if (onError) {
          onError(error, operation);
        }

        throw error;
      } finally {
        setIsLoading(false);
        activeRequests.current.delete(cacheKey);
      }
    },
    [
      generateCacheKey,
      getCachedData,
      setCachedData,
      autoToast,
      toastState,
      onSuccess,
      onError,
    ]
  );

  // Copilot Assist
  const copilotAssist = useCallback(
    async (
      request: Omit<CopilotAssistRequest, "user_id">
    ): Promise<CopilotAssistResponse> => {
      if (!user?.id) {
        throw new Error("User authentication required");
      }

      return handleApiRequest(
        "copilot_assist",
        async () => {
          const response = await api.post('/api/copilot/assist', {
            ...request,
            user_id: user?.id || '',
            org_id: user?.tenantId || '',
          });
          return response.data as CopilotAssistResponse;
        },
        request
      );
    },
    [user, api, handleApiRequest]
  );

  // Memory Search
  const memorySearch = useCallback(
    async (
      request: Omit<MemorySearchRequest, "user_id">
    ): Promise<MemorySearchResponse> => {
      if (!user?.id) {
        throw new Error("User authentication required");
      }

      return handleApiRequest(
        "memory_search",
        async () => {
          const response = await api.post('/api/memory/search', {
            ...request,
            user_id: user?.id || '',
            org_id: user?.tenantId || '',
          });
          return response.data as MemorySearchResponse;
        },
        request
      );
    },
    [user, api, handleApiRequest]
  );

  // Memory Commit
  const memoryCommit = useCallback(
    async (
      request: Omit<MemoryCommitRequest, "user_id">
    ): Promise<MemoryCommitResponse> => {
      if (!user?.id) {
        throw new Error("User authentication required");
      }

      return handleApiRequest(
        "memory_commit",
        async () => {
          const response = await api.post('/api/memory/commit', {
            ...request,
            user_id: user?.id || '',
            org_id: user?.tenantId || '',
          });
          return response.data as MemoryCommitResponse;
        },
        request
      );
    },
    [user, api, handleApiRequest]
  );

  // Memory Update
  const memoryUpdate = useCallback(
    async (
      memoryId: string,
      updates: Partial<MemoryCommitRequest>
    ): Promise<MemoryCommitResponse> => {
      if (!user?.id) {
        throw new Error("User authentication required");
      }

      return handleApiRequest(
        "memory_update",
        async () => {
          const response = await api.put(`/api/memory/${memoryId}`, {
            ...updates,
            user_id: user?.id || '',
            org_id: user?.tenantId || '',
          });
          return response.data as MemoryCommitResponse;
        },
        { memoryId, updates }
      );
    },
    [user, api, handleApiRequest]
  );

  // Memory Delete
  const memoryDelete = useCallback(
    async (
      memoryId: string,
      options: { hard_delete?: boolean } = {}
    ): Promise<{ success: boolean; correlation_id: string }> => {
      if (!user?.id) {
        throw new Error("User authentication required");
      }

      return handleApiRequest(
        "memory_delete",
        async () => {
          const response = await api.delete(`/api/memory/${memoryId}`, {
            params: {
              user_id: user?.id || '',
              org_id: user?.tenantId || '',
              ...options,
            }
          });
          return response.data as { success: boolean; correlation_id: string };
        },
        { memoryId, options }
      );
    },
    [user, api, handleApiRequest]
  );

  // Batch Memory Operations
  const batchMemoryOperations = useCallback(
    async (
      operations: Array<{ type: string; data: unknown }>
    ): Promise<
      Array<{ success: boolean; result?: unknown; error?: string }>
    > => {
      if (!user?.id) {
        throw new Error("User authentication required");
      }

      // Add user context to all operations
      const operationsWithUser = operations.map((op) => ({
        ...op,
        data: {
          ...(typeof op.data === "object" && op.data !== null
            ? (op.data as Record<string, unknown>)
            : { value: op.data }),
          user_id: user?.id || '',
          org_id: user?.tenantId || '',
        },
      }));

      return handleApiRequest(
        "batch_memory_operations",
        async () => {
          const response = await api.post('/api/memory/batch', {
            operations: operationsWithUser
          });
          return response.data as Array<{ success: boolean; result?: unknown; error?: string }>;
        },
        { operations }
      );
    },
    [user, api, handleApiRequest]
  );

  // Health Check
  const healthCheck = useCallback(async () => {
    return handleApiRequest("health_check", async () => {
      const response = await api.get('/api/health');
      return response.data;
    });
  }, [api, handleApiRequest]);

  // Clear cache
  const clearCache = useCallback(() => {
    cache.current.clear();
    // apiClient doesn't have clearCaches method, so we'll just clear our local cache
  }, []);

  // Get cache stats
  const getCacheStats = useCallback(() => {
    return {
      cacheSize: cache.current.size,
      cacheKeys: Array.from(cache.current.keys()),
      apiStats: {}, // apiClient doesn't have getEndpointStats method
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    const currentActiveRequests = activeRequests.current;
    return () => {
      currentActiveRequests.clear();
    };
  }, []);

  return {
    // Operations
    copilotAssist,
    memorySearch,
    memoryCommit,
    memoryUpdate,
    memoryDelete,
    batchMemoryOperations,
    healthCheck,

    // State
    isLoading,
    error,
    lastResponse,

    // Cache management
    clearCache,
    getCacheStats,
  };
}

/**
 * Hook for copilot-specific operations
 */
export function useCopilotApi(options?: UseUnifiedApiOptions) {
  const api = useUnifiedApi(options);

  return {
    assist: api.copilotAssist,
    isLoading: api.isLoading,
    error: api.error,
    lastResponse: api.lastResponse,
  };
}

/**
 * Hook for memory-specific operations
 */
export function useMemoryApi(options?: UseUnifiedApiOptions) {
  const api = useUnifiedApi(options);

  return {
    search: api.memorySearch,
    commit: api.memoryCommit,
    update: api.memoryUpdate,
    delete: api.memoryDelete,
    batch: api.batchMemoryOperations,
    isLoading: api.isLoading,
    error: api.error,
    lastResponse: api.lastResponse,
    clearCache: api.clearCache,
  };
}
