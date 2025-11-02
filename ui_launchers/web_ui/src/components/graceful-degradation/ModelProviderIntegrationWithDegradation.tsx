/**
 * Enhanced ModelProviderIntegration component with graceful degradation
 * This demonstrates how to wrap existing components with graceful degradation capabilities
 */

import React from 'react';
import { 
  ProgressiveFeature,
  useProgressiveData,
  ServiceUnavailable,
  ExtensionUnavailable,
  DegradedModeBanner,
  useFeatureFlag
} from '../../lib/graceful-degradation';
import { EnhancedBackendService } from '../../lib/graceful-degradation/enhanced-backend-service';

interface ModelProvider {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive' | 'error';
  models?: string[];
}

interface ModelProviderIntegrationProps {
  onProviderSelect?: (provider: ModelProvider) => void;
  selectedProvider?: string;
  className?: string;
}

// Mock data for fallback scenarios
const mockModelProviders: ModelProvider[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    type: 'cloud',
    status: 'active',
    models: ['gpt-4', 'gpt-3.5-turbo']
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    type: 'cloud',
    status: 'active',
    models: ['claude-3-opus', 'claude-3-sonnet']
  },
  {
    id: 'local-llama',
    name: 'Local Llama',
    type: 'local',
    status: 'inactive',
    models: ['llama-2-7b', 'llama-2-13b']
  }
];

// Enhanced component with graceful degradation
export function ModelProviderIntegrationWithDegradation({
  onProviderSelect,
  selectedProvider,
  className = ''
}: ModelProviderIntegrationProps) {
  const { isEnabled, fallbackBehavior } = useFeatureFlag('modelProviderIntegration');
  const [enhancedService] = React.useState(() => {
    // In a real implementation, you'd get the original service instance
    const originalService = (window as any).karenBackendService;
    return new EnhancedBackendService(originalService);
  });

  const {
    data: providers,
    isLoading,
    error,
    isStale,
    retry
  } = useProgressiveData(
    'modelProviderIntegration',
    async () => {
      try {
        return await enhancedService.getModelProviders(true);
      } catch (err) {
        // If the enhanced service fails, throw to trigger fallback
        throw err;
      }
    },
    {
      cacheKey: 'model-providers',
      enableCaching: true,
      useStaleOnError: true,
      maxStaleAge: 60 * 60 * 1000, // 1 hour
      refetchInterval: isEnabled ? 5 * 60 * 1000 : undefined // 5 minutes if enabled
    }
  );

  // Show degraded mode banner if using stale data or fallback
  const showDegradedBanner = isStale || !isEnabled || error;

  return (
    <ProgressiveFeature
      featureName="modelProviderIntegration"
      fallbackComponent={
        <ModelProviderFallback
          providers={mockModelProviders}
          onProviderSelect={onProviderSelect}
          selectedProvider={selectedProvider}
          className={className}
          error={error || undefined}
          onRetry={retry}
        />
      }
      loadingComponent={
        <ModelProviderSkeleton className={className} />
      }
    >
      <div className={`model-provider-integration ${className}`}>
        {showDegradedBanner && (
          <DegradedModeBanner
            affectedServices={['Model Provider Integration']}
            showDetails={true}
          />
        )}

        {isLoading && !providers && (
          <ModelProviderSkeleton className="mb-4" />
        )}

        {error && !providers && (
          <ServiceUnavailable
            serviceName="Model Provider Integration"
            error={error}
            onRetry={retry}
            showRetry={true}
          />
        )}

        {providers && (
          <ModelProviderList
            providers={providers}
            onProviderSelect={onProviderSelect}
            selectedProvider={selectedProvider}
            isStale={isStale}
            onRefresh={retry}
          />
        )}
      </div>
    </ProgressiveFeature>
  );
}

// Fallback component when service is unavailable
function ModelProviderFallback({
  providers,
  onProviderSelect,
  selectedProvider,
  className,
  error,
  onRetry
}: {
  providers: ModelProvider[];
  onProviderSelect?: (provider: ModelProvider) => void;
  selectedProvider?: string;
  className: string;
  error?: Error;
  onRetry?: () => void;
}) {
  return (
    <div className={`model-provider-fallback ${className}`}>
      <ExtensionUnavailable
        serviceName="Model Provider Integration"
        extensionName="Model Provider Integration"
        error={error || 'Service temporarily unavailable'}
        onRetry={onRetry}
        showFallbackData={true}
        fallbackData={providers}
      >
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 md:text-base lg:text-lg">
            Available Providers (Cached):
          </h4>
          <ModelProviderList
            providers={providers}
            onProviderSelect={onProviderSelect}
            selectedProvider={selectedProvider}
            isStale={true}
            disabled={true}
          />
        </div>
      </ExtensionUnavailable>
    </div>
  );
}

// Loading skeleton
function ModelProviderSkeleton({ className }: { className?: string }) {
  return (
    <div className={`model-provider-skeleton ${className}`}>
      <div className="animate-pulse space-y-3">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 sm:w-auto md:w-full"></div>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center space-x-3">
              <div className="h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded sm:w-auto md:w-full"></div>
              <div className="flex-1 space-y-1">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 sm:w-auto md:w-full"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2 sm:w-auto md:w-full"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Provider list component
function ModelProviderList({
  providers,
  onProviderSelect,
  selectedProvider,
  isStale = false,
  disabled = false,
  onRefresh
}: {
  providers: ModelProvider[];
  onProviderSelect?: (provider: ModelProvider) => void;
  selectedProvider?: string;
  isStale?: boolean;
  disabled?: boolean;
  onRefresh?: () => void;
}) {
  return (
    <div className="model-provider-list">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
          Model Providers
          {isStale && (
            <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded sm:text-sm md:text-base">
              Cached Data
            </span>
          )}
        </h3>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="text-sm text-blue-600 hover:text-blue-700 underline md:text-base lg:text-lg"
            disabled={disabled}
           aria-label="Button">
            Refresh
          </button>
        )}
      </div>

      <div className="space-y-2">
        {providers.map((provider) => (
          <div
            key={provider.id}
            className={`
              flex items-center justify-between p-3 border rounded-lg cursor-pointer
              ${selectedProvider === provider.id 
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
            `}
            onClick={() => !disabled && onProviderSelect?.(provider)}
          >
            <div className="flex items-center space-x-3">
              <div className={`
                w-3 h-3 rounded-full
                ${provider.status === 'active' ? 'bg-green-500' : 
                  provider.status === 'inactive' ? 'bg-yellow-500' : 'bg-red-500'}
              `} />
              <div>
                <div className="font-medium text-gray-900 dark:text-gray-100">
                  {provider.name}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 md:text-base lg:text-lg">
                  {provider.type} • {provider.models?.length || 0} models
                </div>
              </div>
            </div>
            <div className="text-sm text-gray-400 md:text-base lg:text-lg">
              {provider.status}
            </div>
          </div>
        ))}
      </div>

      {providers.length === 0 && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No model providers available
        </div>
      )}
    </div>
  );
}

// Hook for using the enhanced model provider service
export function useModelProviders() {
  const [enhancedService] = React.useState(() => {
    const originalService = (window as any).karenBackendService;
    return new EnhancedBackendService(originalService);
  });

  const {
    data: providers,
    isLoading,
    error,
    isStale,
    retry
  } = useProgressiveData(
    'modelProviderIntegration',
    () => enhancedService.getModelProviders(true),
    {
      cacheKey: 'model-providers',
      enableCaching: true,
      useStaleOnError: true,
      maxStaleAge: 60 * 60 * 1000
    }
  );

  return {
    providers: providers || [],
    isLoading,
    error,
    isStale,
    retry,
    refreshCache: () => enhancedService.refreshCache('model-providers')
  };
}