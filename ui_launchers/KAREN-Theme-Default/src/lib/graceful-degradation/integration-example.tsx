/**
 * Integration example showing how to fix the ModelProviderIntegration 4xx/5xx errors
 * This demonstrates the practical application of the graceful degradation system
 */
import React from 'react';
import { useModelProviders, useGracefulDegradation } from './use-graceful-backend';
import { DegradedModeBanner, ServiceUnavailable } from './fallback-ui';
import { Button } from '@/components/ui/button';

// Example of how to fix the existing ModelProviderIntegration component
export function FixedModelProviderIntegration() {
  const {
    data: providers,
    isLoading,
    error,
    isStale,
    isFromCache,
    retry,
    refresh
  } = useModelProviders({
    enableCaching: true,
    useStaleOnError: true,
    maxStaleAge: 60 * 60 * 1000 // 1 hour
  });

  const {
    isEnabled,
    showDegradedBanner,
    dismissBanner,
    forceRetry
  } = useGracefulDegradation('modelProviderIntegration');

  // Show degraded mode banner when appropriate
  const shouldShowBanner = showDegradedBanner || isStale || isFromCache || error;

  return (
    <div className="model-provider-integration">
      {shouldShowBanner && (
        <DegradedModeBanner
          affectedServices={['Model Provider Integration']}
          onDismiss={dismissBanner}
          showDetails={true}
        />
      )}
      {isLoading && !providers && (
        <div className="flex items-center justify-center p-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="ml-2">Loading model providers...</span>
        </div>
      )}
      {error && !providers && (
        <ServiceUnavailable
          serviceName="Model Provider Integration"
          error={error}
          onRetry={retry}
          showRetry={true}
        >
          <div className="mt-4">
            <Button
              onClick={forceRetry}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Retry
            </Button>
          </div>
        </ServiceUnavailable>
      )}
      {providers && providers.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">
              {isStale && (
                <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                  Stale
                </span>
              )}
              {isFromCache && (
                <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  Cached
                </span>
              )}
            </h3>
            <Button
              onClick={refresh}
              className="text-sm text-blue-600 hover:text-blue-700 underline"
            >
              Refresh
            </Button>
          </div>
          <div className="grid gap-4">
            {providers.map((provider: any) => (
              <div
                key={provider.id}
                className="p-4 border rounded-lg hover:border-gray-300"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{provider.name}</h4>
                    <p className="text-sm text-gray-600">{provider.description}</p>
                  </div>
                  <div className={`
                    px-2 py-1 rounded text-xs
                    ${provider.status === 'active' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                    }
                  `}>
                    {provider.status}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {providers && providers.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No providers available. Please try again later.
        </div>
      )}
    </div>
  );
}

// Example of how to wrap any existing component with graceful degradation
export function withGracefulDegradation<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  featureName: string
) {
  return function GracefullyDegradedComponent(props: P) {
    const {
      isEnabled,
      fallbackBehavior,
      showDegradedBanner,
      dismissBanner
    } = useGracefulDegradation(featureName);

    if (!isEnabled) {
      switch (fallbackBehavior) {
        case 'hide':
          return null;
        case 'disable':
          return (
            <div className="p-4 bg-gray-100 rounded-lg">
              <p className="text-gray-600">
                This feature is currently unavailable.
              </p>
            </div>
          );
        case 'cache':
        case 'mock':
          return (
            <div className="relative">
              {showDegradedBanner && (
                <DegradedModeBanner
                  affectedServices={[featureName]}
                  onDismiss={dismissBanner}
                />
              )}
              <WrappedComponent {...props} />
            </div>
          );
        default:
          return null;
      }
    }
    return <WrappedComponent {...props} />;
  };
}

// Example usage of the wrapper
const GracefulModelProviderIntegration = withGracefulDegradation(
  FixedModelProviderIntegration,
  'modelProviderIntegration'
);

export { GracefulModelProviderIntegration };

// Hook for handling the specific error you're experiencing
export function useModelProviderSuggestions() {
  const {
    data: suggestions,
    isLoading,
    error,
    retry
  } = useModelProviders();

  // This is the specific function that was causing the 4xx/5xx error
  const loadProviderModelSuggestions = React.useCallback(async () => {
    try {
      // The graceful degradation system will handle errors automatically
      return suggestions || [];
    } catch (err) {
      // Return empty array as fallback instead of throwing
      return [];
    }
  }, [suggestions]);

  return {
    loadProviderModelSuggestions,
    suggestions: suggestions || [],
    isLoading,
    error,
    retry
  };
}

// Example of how to initialize the system in your app
export function initializeGracefulDegradationInApp() {
  // Import the init function
  import('./init').then(({ initGracefulDegradation }) => { 
    initGracefulDegradation({
      enableCaching: true,
      enableGlobalErrorHandling: true,
      developmentMode: process.env.NODE_ENV === 'development',
      logLevel: 'info',
      featureFlags: {
        modelProviderIntegration: { enabled: true, fallbackBehavior: 'cache' },
        extensionSystem: { enabled: true, fallbackBehavior: 'disable' },
        backgroundTasks: { enabled: true, fallbackBehavior: 'hide' }
      }
    });
  });
}
