/**
 * React hook for using the backend service with graceful degradation
 * This integrates with the existing KarenBackendService to handle 4xx/5xx errors
 */
import React from 'react';
import { featureFlagManager, extensionCache, useFeatureFlag, type FeatureFlag } from './index';
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
  const [retryCount, setRetryCount] = React.useState(0);

  // Get the enhanced backend service
  const enhancedService = React.useMemo(() => {
    const originalService = (window as any).karenBackendService;
    if (!originalService) {
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
    } catch (err) {
      const error = err as Error;
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
    serviceName,
    retryCount
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
    setRetryCount(prev => prev + 1);
  }, []);

  const refresh = React.useCallback(() => {
    if (cacheKey) {
      extensionCache.delete(cacheKey);
    }
    setRetryCount(prev => prev + 1);
  }, [cacheKey]);

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
  const featureFlag = useFeatureFlag(featureName);
  const [showDegradedBanner, setShowDegradedBanner] = React.useState(false);

  const dismissBanner = React.useCallback(() => {
    setShowDegradedBanner(false);
  }, []);

  const forceRetry = React.useCallback(() => {
    featureFlagManager.handleServiceRecovery(featureName);
    setShowDegradedBanner(false);
  }, [featureName]);

  React.useEffect(() => {
    if (!featureFlag.enabled) {
      setShowDegradedBanner(true);
    }
  }, [featureFlag.enabled]);

  return {
    isEnabled: featureFlag.enabled,
    fallbackBehavior: featureFlag.fallbackBehavior,
    showDegradedBanner,
    dismissBanner,
    forceRetry
  };
}

// Hook for model providers with graceful degradation
export function useModelProviders(options: UseGracefulBackendOptions = {}) {
  return useGracefulBackend<any[]>('/api/models/providers', {
    ...options,
    cacheKey: 'model-providers',
    fallbackData: [],
    serviceName: 'Model Providers'
  });
}

export function setupGlobalErrorHandling() {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason;
    if (error?.message?.includes('403') || error?.status === 403) {
      featureFlagManager.handleServiceError('extension-auth', error);
    }
    if (error?.message?.includes('503') || error?.status === 503) {
      // Determine which service is affected based on the error
      if (error.message?.includes('/api/extensions')) {
        featureFlagManager.handleServiceError('extension-api', error);
      } else if (error.message?.includes('/api/models')) {
        featureFlagManager.handleServiceError('model-provider', error);
      }
    }
  });

  // Handle fetch errors
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    try {
      const response = await originalFetch(...args);
      // Handle successful responses - re-enable services if they were disabled
      if (response.ok) {
        const url = args[0] as string;
        if (url.includes('/api/extensions')) {
          featureFlagManager.handleServiceRecovery('extension-api');
        } else if (url.includes('/api/models')) {
          featureFlagManager.handleServiceRecovery('model-provider');
        }
      }
      return response;
    } catch (error) {
      // Handle network errors
      const url = args[0] as string;
      if (url.includes('/api/extensions')) {
        featureFlagManager.handleServiceError('extension-api', error as Error);
      } else if (url.includes('/api/models')) {
        featureFlagManager.handleServiceError('model-provider', error as Error);
      }
      throw error;
    }
  };
}
