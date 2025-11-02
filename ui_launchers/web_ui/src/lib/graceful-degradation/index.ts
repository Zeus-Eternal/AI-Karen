/**
 * Graceful degradation system for extension features
 * 
 * This module provides a comprehensive system for handling extension failures
 * and maintaining functionality when backend services are unavailable.
 */
// Feature flags - Types
export type {
  FeatureFlag,
  ExtensionFeatureFlags
} from './feature-flags';
// Feature flags - Values
export {
  FeatureFlagManager,
  featureFlagManager,
  useFeatureFlag,
  withFeatureFlag
} from './feature-flags';
// Fallback UI components - Types
export type {
  FallbackUIProps,
  ServiceUnavailableProps,
  ExtensionUnavailableProps
} from './fallback-ui';
// Fallback UI components - Values
export {
  ServiceUnavailable,
  ExtensionUnavailable,
  LoadingWithFallback,
  DegradedModeBanner,
  ProgressiveEnhancement
} from './fallback-ui';
// Cache management - Types
export type {
  CacheEntry,
  CacheOptions
} from './cache-manager';
// Cache management - Values
export {
  CacheManager,
  ExtensionDataCache,
  extensionCache,
  generalCache,
  CacheAwareDataFetcher
} from './cache-manager';
// Progressive enhancement - Types
export type {
  ProgressiveFeatureProps,
  EnhancedComponentProps
} from './progressive-enhancement';
// Progressive enhancement - Values
export {
  withProgressiveEnhancement,
  ProgressiveFeature,
  useProgressiveData,
  ProgressiveDataDisplay
} from './progressive-enhancement';
// Integration with existing systems
import { featureFlagManager } from './feature-flags';
import { extensionCache } from './cache-manager';
/**
 * Initialize the graceful degradation system
 */
export function initializeGracefulDegradation() {
  // Set up error handlers for automatic feature flag management
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason;
    // Check if it's a network error related to extensions
    if (error?.message?.includes('extension') || 
        error?.message?.includes('403') || 
        error?.message?.includes('503')) {
      // Auto-disable related features
      if (error.message.includes('background-task')) {
        featureFlagManager.handleServiceError('background-tasks', error);
      }
      if (error.message.includes('model-provider')) {
        featureFlagManager.handleServiceError('model-provider', error);
      }
      if (error.message.includes('/api/extensions')) {
        featureFlagManager.handleServiceError('extension-api', error);
      }
    }
  });
  // Clean up expired cache entries periodically
  setInterval(() => {
    const removedCount = extensionCache.cleanup();
    if (removedCount > 0) {
    }
  }, 5 * 60 * 1000); // Every 5 minutes
}
/**
 * Get system health status
 */
export function getSystemHealthStatus() {
  const flags = featureFlagManager.getAllFlags();
  const cacheStats = extensionCache.getStats();
  const enabledFeatures = flags.filter(f => f.enabled).length;
  const totalFeatures = flags.length;
  return {
    features: {
      enabled: enabledFeatures,
      total: totalFeatures,
      healthPercentage: (enabledFeatures / totalFeatures) * 100
    },
    cache: cacheStats,
    degradedServices: flags
      .filter(f => !f.enabled)
      .map(f => f.name),
    timestamp: new Date().toISOString()
  };
}
/**
 * Force refresh all cached data
 */
export function refreshAllCachedData() {
  extensionCache.clear();
}
/**
 * Enable development mode with relaxed error handling
 */
export function enableDevelopmentMode() {
  // Enable all features in development
  featureFlagManager.getAllFlags().forEach(flag => {
    featureFlagManager.setFlag(flag.name, true);
  });
}
/**
 * Simulate service failures for testing
 */
export function simulateServiceFailure(serviceName: string) {
  featureFlagManager.handleServiceError(serviceName, new Error(`Simulated failure for ${serviceName}`));
}
/**
 * Simulate service recovery for testing
 */
export function simulateServiceRecovery(serviceName: string) {
  featureFlagManager.handleServiceRecovery(serviceName);
}
// Export default configuration
export const defaultGracefulDegradationConfig = {
  cacheEnabled: true,
  cacheTTL: 5 * 60 * 1000, // 5 minutes
  maxStaleAge: 60 * 60 * 1000, // 1 hour
  autoRecoveryEnabled: true,
  developmentMode: process.env.NODE_ENV === 'development'
};
