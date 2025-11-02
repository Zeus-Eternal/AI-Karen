/**
 * React hook for using the backend service with graceful degradation
 * This integrates with the existing KarenBackendService to handle 4xx/5xx errors
 */
import React from 'react';
import { 
  featureFlagManager, 
  extensionCache, 
  useFeatureFlag,
  type FeatureFlag 
} from './index';
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
// Hook for extension-specific endpoints
export function useExtensions(options: UseGracefulBackendOptions = {}) {
  const { isEnabled } = useFeatureFlag('extensionSystem');
  return useGracefulBackend('/api/extensions/', {
    ...options,
    cacheKey: 'extensions-list',
    serviceName: 'extension-api',
    enabled: isEnabled,
    fallbackData: [],
    refetchInterval: 5 * 60 * 1000 // 5 minutes
  });
}
export function useBackgroundTasks(options: UseGracefulBackendOptions = {}) {
  const { isEnabled } = useFeatureFlag('backgroundTasks');
  return useGracefulBackend('/api/extensions/background-tasks/', {
    ...options,
    cacheKey: 'background-tasks',
    serviceName: 'background-tasks',
    enabled: isEnabled,
    fallbackData: [],
    refetchInterval: 2 * 60 * 1000 // 2 minutes
  });
}
export function useModelProviders(options: UseGracefulBackendOptions = {}) {
  const { isEnabled } = useFeatureFlag('modelProviderIntegration');
  return useGracefulBackend('/api/models/providers/', {
    ...options,
    cacheKey: 'model-providers',
    serviceName: 'model-provider',
    enabled: isEnabled,
    fallbackData: [],
    refetchInterval: 10 * 60 * 1000 // 10 minutes
  });
}
export function useExtensionHealth(extensionName: string, options: UseGracefulBackendOptions = {}) {
  const { isEnabled } = useFeatureFlag('extensionHealth');
  return useGracefulBackend(`/api/extensions/${extensionName}/health/`, {
    ...options,
    cacheKey: `extension-health-${extensionName}`,
    serviceName: 'extension-health',
    enabled: isEnabled && !!extensionName,
    fallbackData: { status: 'unknown', message: 'Health check unavailable' },
    refetchInterval: 30 * 1000 // 30 seconds
  });
}
// Hook for monitoring overall system health
export function useSystemHealth() {
  const [healthStatus, setHealthStatus] = React.useState({
    overallHealth: 'unknown' as 'healthy' | 'degraded' | 'unhealthy' | 'unknown',
    services: {} as Record<string, any>,
    lastUpdate: new Date()
  });
  const enhancedService = React.useMemo(() => {
    const originalService = (window as any).karenBackendService;
    return originalService ? new EnhancedBackendService(originalService) : null;
  }, []);
  React.useEffect(() => {
    if (!enhancedService) return;
    const updateHealthStatus = () => {
      const serviceHealth = enhancedService.getServiceHealthStatus();
      const flags = featureFlagManager.getAllFlags();
      const enabledServices = flags.filter(f => f.enabled).length;
      const totalServices = flags.length;
      let overallHealth: 'healthy' | 'degraded' | 'unhealthy' | 'unknown' = 'healthy';
      if (enabledServices === 0) {
        overallHealth = 'unhealthy';
      } else if (enabledServices < totalServices) {
        overallHealth = 'degraded';
      }
      setHealthStatus({
        overallHealth,
        services: serviceHealth,
        lastUpdate: new Date()
      });
    };
    // Initial update
    updateHealthStatus();
    // Update every 30 seconds
    const interval = setInterval(updateHealthStatus, 30 * 1000);
    return () => clearInterval(interval);
  }, [enhancedService]);
  return healthStatus;
}
// Hook for handling graceful degradation in components
export function useGracefulDegradation(featureName: string) {
  const { isEnabled, fallbackBehavior, flag } = useFeatureFlag(featureName);
  const [showDegradedBanner, setShowDegradedBanner] = React.useState(false);
  React.useEffect(() => {
    setShowDegradedBanner(!isEnabled);
  }, [isEnabled]);
  const dismissBanner = React.useCallback(() => {
    setShowDegradedBanner(false);
  }, []);
  const forceRetry = React.useCallback(() => {
    featureFlagManager.setFlag(featureName, true);
    setShowDegradedBanner(false);
  }, [featureName]);
  return {
    isEnabled,
    fallbackBehavior,
    showDegradedBanner,
    dismissBanner,
    forceRetry,
    flag
  };
}
// Global error handler for automatic feature flag management
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
