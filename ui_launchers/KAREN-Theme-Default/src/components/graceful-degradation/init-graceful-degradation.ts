/**
 * Graceful degradation initialization
 */
import { featureFlagManager } from '@/lib/graceful-degradation';

export interface GracefulDegradationConfig {
  enableCaching?: boolean;
  enableGlobalErrorHandling?: boolean;
  developmentMode?: boolean;
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
  featureFlags?: Record<string, {
    enabled: boolean;
    fallbackBehavior: 'hide' | 'disable' | 'cache' | 'mock';
  }>;
}

export function initGracefulDegradation(config: GracefulDegradationConfig = {}) {
  const {
    enableCaching: _enableCaching = true,
    enableGlobalErrorHandling = true,
    developmentMode = false,
    logLevel = 'warn',
    featureFlags = {}
  } = config;

  // Initialize feature flags
  Object.entries(featureFlags).forEach(([name, flag]) => {
    featureFlagManager.updateFlag(name, {
      enabled: flag.enabled,
      fallbackBehavior: flag.fallbackBehavior,
    });
  });

  // Setup global error handling if enabled
  if (enableGlobalErrorHandling) {
    void import('@/lib/graceful-degradation/use-graceful-backend')
      .then(({ setupGlobalErrorHandling }) => {
        setupGlobalErrorHandling();
      })
      .catch((error) => {
        if (developmentMode) {
          console.error('Failed to initialize graceful degradation handlers', error);
        }
      });
  }

  // Log initialization
  if (developmentMode && logLevel === 'debug') {
    console.log('Graceful degradation initialized with config:', config);
  }
}