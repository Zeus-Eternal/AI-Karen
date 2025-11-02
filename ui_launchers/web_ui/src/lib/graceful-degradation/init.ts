/**
 * Initialization script for graceful degradation system
 * This should be called early in the application lifecycle
 */
import { 
  featureFlagManager,
  extensionCache,
  initializeGracefulDegradation,
  defaultGracefulDegradationConfig
} from './index';
import { setupGlobalErrorHandling } from './use-graceful-backend';
export interface GracefulDegradationConfig {
  enableCaching?: boolean;
  cacheCleanupInterval?: number;
  enableGlobalErrorHandling?: boolean;
  developmentMode?: boolean;
  logLevel?: '' | 'warn' | 'error';
  featureFlags?: {
    [key: string]: {
      enabled?: boolean;
      fallbackBehavior?: 'hide' | 'disable' | 'cache' | 'mock';
    };
  };
}
let isInitialized = false;
export function initGracefulDegradation(config: GracefulDegradationConfig = {}) {
  if (isInitialized) {
    return;
  }
  const finalConfig = {
    ...defaultGracefulDegradationConfig,
    ...config
  };
  try {
    // Initialize core system
    initializeGracefulDegradation();
    // Set up global error handling
    if (finalConfig.enableGlobalErrorHandling !== false) {
      setupGlobalErrorHandling();
    }
    // Configure feature flags
    if (finalConfig.featureFlags) {
      Object.entries(finalConfig.featureFlags).forEach(([flagName, flagConfig]) => {
        if (flagConfig.enabled !== undefined) {
          featureFlagManager.setFlag(flagName, flagConfig.enabled);
        }
        if (flagConfig.fallbackBehavior) {
          featureFlagManager.updateFlag(flagName, {
            fallbackBehavior: flagConfig.fallbackBehavior
          });
        }
      });
    }
    // Set up cache cleanup
    if (finalConfig.enableCaching !== false) {
      const cleanupInterval = finalConfig.cacheCleanupInterval || 5 * 60 * 1000; // 5 minutes
      setInterval(() => {
        const removedCount = extensionCache.cleanup();
        if (removedCount > 0 && finalConfig.logLevel === 'debug') {
        }
      }, cleanupInterval);
    }
    // Development mode setup
    if (finalConfig.developmentMode) {
      enableDevelopmentMode();
    }
    // Set up periodic health checks
    setupPeriodicHealthChecks();
    // Set up service recovery monitoring
    setupServiceRecoveryMonitoring();
    isInitialized = true;
  } catch (error) {
    throw error;
  }
}
function enableDevelopmentMode() {
  // Enable all features in development
  featureFlagManager.getAllFlags().forEach(flag => {
    featureFlagManager.setFlag(flag.name, true);
  });
  // Add development helpers to window object
  (window as any).gracefulDegradation = {
    featureFlagManager,
    extensionCache,
    simulateFailure: (serviceName: string) => {
      featureFlagManager.handleServiceError(serviceName, new Error(`Simulated failure for ${serviceName}`));
    },
    simulateRecovery: (serviceName: string) => {
      featureFlagManager.handleServiceRecovery(serviceName);
    },
    getSystemHealth: () => {
      const flags = featureFlagManager.getAllFlags();
      const cacheStats = extensionCache.getStats();
      return {
        features: flags.map(f => ({
          name: f.name,
          enabled: f.enabled,
          fallbackBehavior: f.fallbackBehavior
        })),
        cache: cacheStats,
        timestamp: new Date().toISOString()
      };
    },
    clearCache: () => {
      extensionCache.clear();
    }
  };
}
function setupPeriodicHealthChecks() {
  // Check system health every 2 minutes
  setInterval(() => {
    const flags = featureFlagManager.getAllFlags();
    const disabledServices = flags.filter(f => !f.enabled);
    if (disabledServices.length > 0) {
      console.debug('Disabled services detected:', disabledServices.map(f => f.name));
      // Attempt to re-enable services that might have recovered
      disabledServices.forEach(flag => {
        // Only attempt recovery for certain types of failures
        if (flag.fallbackBehavior === 'cache' || flag.fallbackBehavior === 'disable') {
          attemptServiceRecovery(flag.name);
        }
      });
    }
  }, 2 * 60 * 1000); // 2 minutes
}
function setupServiceRecoveryMonitoring() {
  // Monitor for successful requests to re-enable services
  const originalFetch = window.fetch;
  let successfulRequests: Record<string, number> = {};
  window.fetch = async (...args) => {
    const response = await originalFetch(...args);
    if (response.ok) {
      const url = args[0] as string;
      const serviceName = getServiceNameFromUrl(url);
      if (serviceName) {
        successfulRequests[serviceName] = (successfulRequests[serviceName] || 0) + 1;
        // If we have multiple successful requests, consider the service recovered
        if (successfulRequests[serviceName] >= 3) {
          const featureName = getFeatureNameFromService(serviceName);
          if (!featureFlagManager.isEnabled(featureName)) {
            featureFlagManager.handleServiceRecovery(serviceName);
          }
          successfulRequests[serviceName] = 0; // Reset counter
        }
      }
    }
    return response;
  };
}
async function attemptServiceRecovery(flagName: string) {
  try {
    // Attempt a lightweight health check
    const serviceName = getServiceNameFromFlag(flagName);
    const healthEndpoint = getHealthEndpointForService(serviceName);
    if (healthEndpoint) {
      const response = await fetch(healthEndpoint, {
        method: 'GET',
        timeout: 5000 // 5 second timeout
      } as any);
      if (response.ok) {
        featureFlagManager.setFlag(flagName, true);
      }
    }
  } catch (error) {
    // Health check failed, keep service disabled
  }
}
function getServiceNameFromUrl(url: string): string | null {
  if (url.includes('/api/extensions')) return 'extension-api';
  if (url.includes('/api/models')) return 'model-provider';
  if (url.includes('/api/health')) return 'extension-health';
  if (url.includes('background-task')) return 'background-tasks';
  return null;
}
function getFeatureNameFromService(serviceName: string): string {
  const mapping: Record<string, string> = {
    'extension-api': 'extensionSystem',
    'model-provider': 'modelProviderIntegration',
    'extension-health': 'extensionHealth',
    'background-tasks': 'backgroundTasks'
  };
  return mapping[serviceName] || 'extensionSystem';
}
function getServiceNameFromFlag(flagName: string): string {
  const mapping: Record<string, string> = {
    'extensionSystem': 'extension-api',
    'modelProviderIntegration': 'model-provider',
    'extensionHealth': 'extension-health',
    'backgroundTasks': 'background-tasks'
  };
  return mapping[flagName] || 'extension-api';
}
function getHealthEndpointForService(serviceName: string): string | null {
  const mapping: Record<string, string> = {
    'extension-api': '/api/extensions/health',
    'model-provider': '/api/models/health',
    'extension-health': '/api/health',
    'background-tasks': '/api/extensions/background-tasks/health'
  };
  return mapping[serviceName] || null;
}
// Export for manual initialization
export { isInitialized };
// Auto-initialize if in browser environment
if (typeof window !== 'undefined' && !isInitialized) {
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initGracefulDegradation();
    });
  } else {
    // DOM is already ready
    setTimeout(() => {
      initGracefulDegradation();
    }, 0);
  }
}
