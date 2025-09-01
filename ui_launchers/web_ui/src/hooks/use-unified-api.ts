/**
 * React Hook for Unified API Client
 * 
 * Features:
 * - Easy integration with React components
 * - State management for API requests
 * - Loading states and error handling
 * - Automatic retry logic
 * - Request caching and deduplication
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { 
  getUnifiedApiClient,
  type CopilotAssistRequest,
  type CopilotAssistResponse,
  type MemorySearchRequest,
  type MemorySearchResponse,
  type MemoryCommitRequest,
  type MemoryCommitResponse
} from '@/lib/unified-api-client';

interface UseUnifiedApiOptions {
  autoToast?: boolean;
  enableCaching?: boolean;
  cacheTimeout?: number;
  onError?: (error: Error, operation: string) => void;
  onSuccess?: (data: any, operation: string) => void;
}

interface UseUnifiedApiReturn {
  // Copilot operations
  copilotAssist: (request: Omit<CopilotAssistRequest, 'user_id'>) => Promise<CopilotAssistResponse>;
  
  // Memory operations
  memorySearch: (request: Omit<MemorySearchRequest, 'user_id'>) => Promise<MemorySearchResponse>;
  memoryCommit: (request: Omit<MemoryCommitRequest, 'user_id'>) => Promise<MemoryCommitResponse>;
  memoryUpdate: (memoryId: string, updates: Partial<MemoryCommitRequest>) => Promise<MemoryCommitResponse>;
  memoryDelete: (memoryId: string, options?: { hard_delete?: boolean }) => Promise<{ success: boolean; correlation_id: string }>;
  
  // Batch operations
  batchMemoryOperations: (operations: Array<{ type: string; data: any }>) => Promise<Array<{ success: boolean; result?: any; error?: string }>>;
  
  // Utility operations
  healthCheck: () => Promise<any>;
  
  // State
  isLoading: boolean;
  error: Error | null;
  lastResponse: any;
  
  // Cache management
  clearCache: () => void;
  getCacheStats: () => any;
}

interface CacheEntry {
  data: any;
  timestamp: number;
  key: string;
}

export function useUnifiedApi(options: UseUnifiedApiOptions = {}): UseUnifiedApiReturn {
  const {
    autoToast = true,
    enableCaching = true,
    cacheTimeout = 300000, // 5 minutes
    onError,
    onSuccess
  } = options;

  const { user } = useAuth();
  const { toast } = useToast();
  const apiClient = getUnifiedApiClient();
  
  // State
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastResponse, setLastResponse] = useState<any>(null);
  
  // Cache
  const cache = useRef<Map<string, CacheEntry>>(new Map());
  const activeRequests = useRef<Map<string, Promise<any>>>(new Map());

  // Generate cache key
  const generateCacheKey = useCallback((operation: string, params: any): string => {
    return `${operation}_${JSON.stringify(params)}`;
  }, []);

  // Check cache
  const getCachedData = useCallback((key: string): any | null => {
    if (!enableCaching) return null;
    
    const entry = cache.current.get(key);
    if (!entry) return null;
    
    const isExpired = Date.now() - entry.timestamp > cacheTimeout;
    if (isExpired) {
      cache.current.delete(key);
      return null;
    }
    
    return entry.data;
  }, [enableCaching, cacheTimeout]);

  // Set cache data
  const setCachedData = useCallback((key: string, data: any): void => {
    if (!enableCaching) return;
    
    cache.current.set(key, {
      data,
      timestamp: Date.now(),
      key
    });
  }, [enableCaching]);

  // Handle API request with caching and deduplication
  const handleApiRequest = useCallback(async <T>(
    operation: string,
    requestFn: () => Promise<T>,
    params?: any
  ): Promise<T> => {
    const cacheKey = params ? generateCacheKey(operation, params) : operation;
    
    // Check cache first
    const cachedData = getCachedData(cacheKey);
    if (cachedData) {
      setLastResponse(cachedData);
      return cachedData;
    }
    
    // Check for active request (deduplication)
    const activeRequest = activeRequests.current.get(cacheKey);
    if (activeRequest) {
      return activeRequest;
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
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      
      if (autoToast) {
        toast({
          variant: 'destructive',
          title: 'API Error',
          description: error.message,
          duration: 5000
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
  }, [generateCacheKey, getCachedData, setCachedData, autoToast, toast, onSuccess, onError]);

  // Copilot Assist
  const copilotAssist = useCallback(async (
    request: Omit<CopilotAssistRequest, 'user_id'>
  ): Promise<CopilotAssistResponse> => {
    if (!user?.user_id) {
      throw new Error('User authentication required');
    }

    return handleApiRequest(
      'copilot_assist',
      () => apiClient.copilotAssist({
        ...request,
        user_id: user.user_id,
        org_id: user.tenant_id
      }),
      request
    );
  }, [user, apiClient, handleApiRequest]);

  // Memory Search
  const memorySearch = useCallback(async (
    request: Omit<MemorySearchRequest, 'user_id'>
  ): Promise<MemorySearchResponse> => {
    if (!user?.user_id) {
      throw new Error('User authentication required');
    }

    return handleApiRequest(
      'memory_search',
      () => apiClient.memorySearch({
        ...request,
        user_id: user.user_id,
        org_id: user.tenant_id
      }),
      request
    );
  }, [user, apiClient, handleApiRequest]);

  // Memory Commit
  const memoryCommit = useCallback(async (
    request: Omit<MemoryCommitRequest, 'user_id'>
  ): Promise<MemoryCommitResponse> => {
    if (!user?.user_id) {
      throw new Error('User authentication required');
    }

    return handleApiRequest(
      'memory_commit',
      () => apiClient.memoryCommit({
        ...request,
        user_id: user.user_id,
        org_id: user.tenant_id
      }),
      request
    );
  }, [user, apiClient, handleApiRequest]);

  // Memory Update
  const memoryUpdate = useCallback(async (
    memoryId: string,
    updates: Partial<MemoryCommitRequest>
  ): Promise<MemoryCommitResponse> => {
    if (!user?.user_id) {
      throw new Error('User authentication required');
    }

    return handleApiRequest(
      'memory_update',
      () => apiClient.memoryUpdate(memoryId, {
        ...updates,
        user_id: user.user_id,
        org_id: user.tenant_id
      }),
      { memoryId, updates }
    );
  }, [user, apiClient, handleApiRequest]);

  // Memory Delete
  const memoryDelete = useCallback(async (
    memoryId: string,
    options: { hard_delete?: boolean } = {}
  ): Promise<{ success: boolean; correlation_id: string }> => {
    if (!user?.user_id) {
      throw new Error('User authentication required');
    }

    return handleApiRequest(
      'memory_delete',
      () => apiClient.memoryDelete(memoryId, {
        user_id: user.user_id,
        org_id: user.tenant_id,
        ...options
      }),
      { memoryId, options }
    );
  }, [user, apiClient, handleApiRequest]);

  // Batch Memory Operations
  const batchMemoryOperations = useCallback(async (
    operations: Array<{ type: string; data: any }>
  ): Promise<Array<{ success: boolean; result?: any; error?: string }>> => {
    if (!user?.user_id) {
      throw new Error('User authentication required');
    }

    // Add user context to all operations
    const operationsWithUser = operations.map(op => ({
      ...op,
      data: {
        ...op.data,
        user_id: user.user_id,
        org_id: user.tenant_id
      }
    }));

    return handleApiRequest(
      'batch_memory_operations',
      () => apiClient.batchMemoryOperations(operationsWithUser as Array<{ type: "search" | "delete" | "commit" | "update"; data: any }>),
      operations
    );
  }, [user, apiClient, handleApiRequest]);

  // Health Check
  const healthCheck = useCallback(async () => {
    return handleApiRequest(
      'health_check',
      () => apiClient.healthCheck()
    );
  }, [apiClient, handleApiRequest]);

  // Clear cache
  const clearCache = useCallback(() => {
    cache.current.clear();
    apiClient.clearCaches();
  }, [apiClient]);

  // Get cache stats
  const getCacheStats = useCallback(() => {
    return {
      cacheSize: cache.current.size,
      cacheKeys: Array.from(cache.current.keys()),
      apiStats: apiClient.getEndpointStats()
    };
  }, [apiClient]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      activeRequests.current.clear();
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
    getCacheStats
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
    lastResponse: api.lastResponse
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
    clearCache: api.clearCache
  };
}

// Export types
export type {
  UseUnifiedApiOptions,
  UseUnifiedApiReturn
};