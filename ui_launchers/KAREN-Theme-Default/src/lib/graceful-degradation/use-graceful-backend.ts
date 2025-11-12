/**
 * React hook for using the backend service with graceful degradation
 * This integrates with the existing KarenBackendService to handle 4xx/5xx errors
 */
import * as React from 'react';
import { featureFlagManager, useFeatureFlag } from './feature-flags';
import { extensionCache } from './cache-manager';
import { EnhancedBackendService } from './enhanced-backend-service';

export interface UseGracefulBackendOptions {
  enableCaching?: boolean;
  useStaleOnError?: boolean;
  maxStaleAge?: number;
  retryAttempts?: number;
  retryDelay?: number;
}

export interface GracefulBackendResult<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  isStale: boolean;
  isFromCache: boolean;
  retry: () => void;
  refresh: () => void;
}

// Hook for making graceful backend requests
export function useGracefulBackend<T>(
  endpoint: string,
  options: UseGracefulBackendOptions & {
    cacheKey?: string;
    fallbackData?: T;
    serviceName?: string;
    enabled?: boolean;
    refetchInterval?: number;
  } = {}
): GracefulBackendResult<T> {
  const {
    enableCaching = true,
    useStaleOnError = true,
    maxStaleAge = 60 * 60 * 1000, // 1 hour
    cacheKey,
    fallbackData,
    serviceName,
    enabled = true,
    refetchInterval
  } = options;

  const [data, setData] = React.useState<T | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);
  const [isStale, setIsStale] = React.useState(false);
  const [isFromCache, setIsFromCache] = React.useState(false);

  // Get the enhanced backend service
  const enhancedService = React.useMemo(() => {
    if (typeof window === 'undefined') {
      return null;
    }

    const globalWindow = window as typeof window & {
      karenBackendService?: {
        makeRequest: (endpoint: string, init?: RequestInit) => Promise<unknown>;
      };
    };

    const originalService = globalWindow.karenBackendService;
    if (!originalService || typeof originalService.makeRequest !== 'function') {
      return null;
    }

    return new EnhancedBackendService(originalService);
  }, []);

  const fetchData = React.useCallback(async () => {
    if (!enabled || !enhancedService) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const result = await enhancedService.makeEnhancedRequest<T>({
        endpoint,
        cacheKey,
        enableCaching,
        useStaleOnError,
        maxStaleAge,
        fallbackData,
        serviceName
      });

      setData(result);
      setIsStale(false);
      setIsFromCache(false);

      // Check if data came from cache
      if (cacheKey && enableCaching) {
        const cachedEntry = extensionCache.getWithMetadata(cacheKey);
        if (cachedEntry) {
          const age = Date.now() - cachedEntry.metadata.timestamp;
          setIsFromCache(age < 1000); // Consider as from cache if less than 1 second old
          setIsStale(Date.now() > cachedEntry.metadata.expiresAt);
        }
      }
    } catch (err: unknown) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);

      // Try to get cached data as fallback
      if (cacheKey && useStaleOnError) {
        const staleData = extensionCache.getStale<T>(cacheKey, maxStaleAge);
        if (staleData) {
          setData(staleData);
          setIsStale(true);
          setIsFromCache(true);
        } else if (fallbackData !== undefined) {
          setData(fallbackData);
          setIsStale(false);
          setIsFromCache(false);
        }
      } else if (fallbackData !== undefined) {
        setData(fallbackData);
        setIsStale(false);
        setIsFromCache(false);
      }
    } finally {
      setIsLoading(false);
    }
  }, [
    enabled,
    enhancedService,
    endpoint,
    cacheKey,
    enableCaching,
    useStaleOnError,
    maxStaleAge,
    fallbackData,
    serviceName
  ]);

  // Initial fetch
  React.useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Refetch interval
  React.useEffect(() => {
    if (refetchInterval && enabled) {
      const interval = setInterval(fetchData, refetchInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, refetchInterval, enabled]);

  const retry = React.useCallback(() => {
    fetchData();
  }, [fetchData]);

  const refresh = React.useCallback(() => {
    if (cacheKey) {
      extensionCache.delete(cacheKey);
    }
    fetchData();
  }, [cacheKey, fetchData]);

  return {
    data,
    isLoading,
    error,
    isStale,
    isFromCache,
    retry,
    refresh
  };
}

// Global error handler for automatic feature flag management
// Hook for graceful degradation state management
export function useGracefulDegradation(featureName: string) {
  const { isEnabled, fallbackBehavior } = useFeatureFlag(featureName);
  const [showDegradedBanner, setShowDegradedBanner] = React.useState(false);

  const dismissBanner = React.useCallback(() => {
    setShowDegradedBanner(false);
  }, []);

  const forceRetry = React.useCallback(() => {
    featureFlagManager.handleServiceRecovery(featureName);
    setShowDegradedBanner(false);
  }, [featureName]);

  React.useEffect(() => {
    if (isEnabled) {
      setShowDegradedBanner(false);
    } else {
      setShowDegradedBanner(true);
    }
  }, [isEnabled]);

  return {
    isEnabled,
    fallbackBehavior,
    showDegradedBanner,
    dismissBanner,
    forceRetry
  };
}

// Hook for model providers with graceful degradation
export function useModelProviders(options: UseGracefulBackendOptions = {}) {
  return useGracefulBackend<unknown[]>('/api/models/providers', {
    ...options,
    cacheKey: 'model-providers',
    fallbackData: [],
    serviceName: 'Model Providers'
  });
}

export function setupGlobalErrorHandling() {
  if (typeof window === 'undefined') {
    return;
  }

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
    const error = event.reason as { message?: string; status?: number } | undefined;
    const message = error?.message ?? '';

    if (message.includes('403') || error?.status === 403) {
      featureFlagManager.handleServiceError('extension-auth', error);
    }
    if (message.includes('503') || error?.status === 503) {
      // Determine which service is affected based on the error
      if (message.includes('/api/extensions')) {
        featureFlagManager.handleServiceError('extension-api', error);
      } else if (message.includes('/api/models')) {
        featureFlagManager.handleServiceError('model-provider', error);
      }
    }
  });

  // Handle fetch errors
  const windowWithMutableFetch = window as typeof window & { fetch: typeof fetch };
  const originalFetch = windowWithMutableFetch.fetch.bind(window);

  const getRequestUrl = (input: Parameters<typeof fetch>[0]): string => {
    if (typeof input === 'string') {
      return input;
    }
    if (input instanceof URL) {
      return input.toString();
    }
    return input?.url ?? '';
  };

  windowWithMutableFetch.fetch = (async (
    ...args: Parameters<typeof fetch>
  ) => {
    try {
      const response = await originalFetch(...args);
      // Handle successful responses - re-enable services if they were disabled
      if (response.ok) {
        const url = getRequestUrl(args[0]);
        if (url.includes('/api/extensions')) {
          featureFlagManager.handleServiceRecovery('extension-api');
        } else if (url.includes('/api/models')) {
          featureFlagManager.handleServiceRecovery('model-provider');
        }
      }
      return response;
    } catch (error) {
      // Handle network errors
      const url = getRequestUrl(args[0]);
      if (url.includes('/api/extensions')) {
        featureFlagManager.handleServiceError('extension-api', error as Error);
      } else if (url.includes('/api/models')) {
        featureFlagManager.handleServiceError('model-provider', error as Error);
      }
      throw error;
    }
  }) as typeof fetch;
}
