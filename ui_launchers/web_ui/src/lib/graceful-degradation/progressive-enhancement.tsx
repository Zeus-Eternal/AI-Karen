/**
 * Progressive enhancement system for extension features
 */

import React from 'react';
import { featureFlagManager, useFeatureFlag } from './feature-flags';
import { extensionCache, CacheAwareDataFetcher } from './cache-manager';
import { ServiceUnavailable, ExtensionUnavailable, LoadingWithFallback } from './fallback-ui';

export interface ProgressiveFeatureProps {
  featureName: string;
  fallbackComponent?: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  children: React.ReactNode;
  cacheKey?: string;
  enableCaching?: boolean;
}

export interface EnhancedComponentProps {
  isEnhanced: boolean;
  fallbackMode: 'hide' | 'disable' | 'cache' | 'mock';
  cachedData?: any;
  onRetry?: () => void;
}

// Higher-order component for progressive enhancement
export function withProgressiveEnhancement<P extends object>(
  Component: React.ComponentType<P & EnhancedComponentProps>,
  featureName: string,
  options: {
    fallbackComponent?: React.ComponentType<P>;
    cacheKey?: string;
    enableCaching?: boolean;
  } = {}
) {
  return function ProgressivelyEnhancedComponent(props: P) {
    const { isEnabled, fallbackBehavior } = useFeatureFlag(featureName);
    const [cachedData, setCachedData] = React.useState<any>(null);
    const [retryCount, setRetryCount] = React.useState(0);

    // Load cached data if caching is enabled
    React.useEffect(() => {
      if (options.enableCaching && options.cacheKey) {
        const cached = extensionCache.get(options.cacheKey);
        if (cached) {
          setCachedData(cached);
        }
      }
    }, [options.cacheKey, options.enableCaching]);

    const handleRetry = React.useCallback(() => {
      setRetryCount(prev => prev + 1);
      // Try to re-enable the feature flag
      featureFlagManager.setFlag(featureName, true);
    }, [featureName]);

    if (!isEnabled) {
      switch (fallbackBehavior) {
        case 'hide':
          return null;
        
        case 'disable':
          if (options.fallbackComponent) {
            const FallbackComponent = options.fallbackComponent;
            return <FallbackComponent {...props} />;
          }
          return (
            <ExtensionUnavailable
              serviceName={featureName}
              extensionName={featureName}
              error="Feature is currently disabled"
              onRetry={handleRetry}
            />
          );
        
        case 'cache':
          return (
            <Component
              {...props}
              isEnhanced={false}
              fallbackMode="cache"
              cachedData={cachedData}
              onRetry={handleRetry}
            />
          );
        
        case 'mock':
          return (
            <Component
              {...props}
              isEnhanced={false}
              fallbackMode="mock"
              cachedData={cachedData}
              onRetry={handleRetry}
            />
          );
        
        default:
          return null;
      }
    }

    return (
      <Component
        {...props}
        isEnhanced={true}
        fallbackMode={fallbackBehavior}
        cachedData={cachedData}
        onRetry={handleRetry}
      />
    );
  };
}

// Progressive feature wrapper component
export function ProgressiveFeature({
  featureName,
  fallbackComponent,
  loadingComponent,
  errorComponent,
  children,
  cacheKey,
  enableCaching = false
}: ProgressiveFeatureProps) {
  const { isEnabled, fallbackBehavior } = useFeatureFlag(featureName);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);
  const [cachedData, setCachedData] = React.useState<any>(null);

  // Simulate feature loading/detection
  React.useEffect(() => {
    const loadFeature = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Load cached data if available
        if (enableCaching && cacheKey) {
          const cached = extensionCache.get(cacheKey);
          if (cached) {
            setCachedData(cached);
          }
        }

        // Simulate feature detection
        await new Promise(resolve => setTimeout(resolve, 500));
        
        if (!isEnabled) {
          throw new Error(`Feature '${featureName}' is disabled`);
        }

        setIsLoading(false);
      } catch (err) {
        setError(err as Error);
        setIsLoading(false);
      }
    };

    loadFeature();
  }, [featureName, isEnabled, cacheKey, enableCaching]);

  if (isLoading) {
    return loadingComponent || (
      <LoadingWithFallback
        serviceName={featureName}
        timeout={10000}
        onTimeout={() => setError(new Error('Feature loading timeout'))}
      />
    );
  }

  if (error || !isEnabled) {
    switch (fallbackBehavior) {
      case 'hide':
        return null;
      
      case 'disable':
        return fallbackComponent || (
          <ExtensionUnavailable
            serviceName={featureName}
            extensionName={featureName}
            error={error || 'Feature is disabled'}
            onRetry={() => window.location.reload()}
          />
        );
      
      case 'cache':
        if (cachedData) {
          return (
            <div className="relative">
              <div className="absolute top-0 right-0 bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-bl">
              </div>
              {children}
            </div>
          );
        }
        return fallbackComponent || null;
      
      case 'mock':
        return (
          <div className="relative">
            <div className="absolute top-0 right-0 bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-bl">
            </div>
            {children}
          </div>
        );
      
      default:
        return errorComponent || fallbackComponent || null;
    }
  }

  return <>{children}</>;
}

// Hook for progressive data loading
export function useProgressiveData<T>(
  featureName: string,
  fetchFunction: () => Promise<T>,
  options: {
    cacheKey?: string;
    enableCaching?: boolean;
    useStaleOnError?: boolean;
    maxStaleAge?: number;
    refetchInterval?: number;
  } = {}
) {
  const { isEnabled, fallbackBehavior } = useFeatureFlag(featureName);
  const [data, setData] = React.useState<T | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);
  const [isStale, setIsStale] = React.useState(false);

  const fetchData = React.useCallback(async () => {
    if (!isEnabled) {
      // Try to get cached data when feature is disabled
      if (options.enableCaching && options.cacheKey) {
        const cached = extensionCache.getStale<T>(options.cacheKey, options.maxStaleAge);
        if (cached) {
          setData(cached);
          setIsStale(true);
          setError(null);
        }
      }
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      let result: T;

      if (options.enableCaching && options.cacheKey) {
        // Use cache-aware fetcher
        const fetcher = new CacheAwareDataFetcher(
          extensionCache,
          async () => await fetchFunction()
        );

        result = await fetcher.fetchWithCache<T>(options.cacheKey, {
          useStaleOnError: options.useStaleOnError,
          maxStaleAge: options.maxStaleAge

      } else {
        result = await fetchFunction();
      }

      setData(result);
      setIsStale(false);
    } catch (err) {
      setError(err as Error);
      
      // Try to use stale data on error
      if (options.useStaleOnError && options.enableCaching && options.cacheKey) {
        const staleData = extensionCache.getStale<T>(options.cacheKey, options.maxStaleAge);
        if (staleData) {
          setData(staleData);
          setIsStale(true);
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, [isEnabled, fetchFunction, options]);

  // Initial fetch
  React.useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Refetch interval
  React.useEffect(() => {
    if (options.refetchInterval && isEnabled) {
      const interval = setInterval(fetchData, options.refetchInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, options.refetchInterval, isEnabled]);

  const retry = React.useCallback(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    isLoading,
    error,
    isStale,
    isEnabled,
    fallbackBehavior,
    retry
  };
}

// Component for displaying progressive data
export function ProgressiveDataDisplay<T>({
  featureName,
  fetchFunction,
  renderData,
  renderLoading,
  renderError,
  renderFallback,
  cacheKey,
  enableCaching = true
}: {
  featureName: string;
  fetchFunction: () => Promise<T>;
  renderData: (data: T, isStale: boolean) => React.ReactNode;
  renderLoading?: () => React.ReactNode;
  renderError?: (error: Error, retry: () => void) => React.ReactNode;
  renderFallback?: (cachedData: T | null) => React.ReactNode;
  cacheKey?: string;
  enableCaching?: boolean;
}) {
  const {
    data,
    isLoading,
    error,
    isStale,
    isEnabled,
    fallbackBehavior,
    retry
  } = useProgressiveData(featureName, fetchFunction, {
    cacheKey,
    enableCaching,
    useStaleOnError: true,
    maxStaleAge: 60 * 60 * 1000 // 1 hour

  if (isLoading && !data) {
    return renderLoading ? renderLoading() : (
      <LoadingWithFallback serviceName={featureName} />
    );
  }

  if (error && !data) {
    if (!isEnabled) {
      switch (fallbackBehavior) {
        case 'hide':
          return null;
        case 'cache':
        case 'mock':
          return renderFallback ? renderFallback(data) : null;
        default:
          return renderError ? renderError(error, retry) : (
            <ExtensionUnavailable
              serviceName={featureName}
              extensionName={featureName}
              error={error}
              onRetry={retry}
            />
          );
      }
    }

    return renderError ? renderError(error, retry) : (
      <ServiceUnavailable
        serviceName={featureName}
        error={error}
        onRetry={retry}
      />
    );
  }

  if (data) {
    return renderData(data, isStale);
  }

  return renderFallback ? renderFallback(null) : null;
}