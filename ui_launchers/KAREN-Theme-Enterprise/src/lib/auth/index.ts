/**
 * Extension Authentication Error Handling System
 * 
 * Comprehensive authentication error handling for extension APIs with:
 * - Specific error types for different authentication failures
 * - Graceful degradation when authentication fails
 * - User-friendly error messages and recovery suggestions
 * - Fallback behavior for extension unavailability
 * 
 * Requirements addressed:
 * - 3.1: Extension integration service error handling
 * - 3.2: Extension API calls with proper authentication
 * - 3.3: Authentication failures and retry logic
 * - 9.1: Graceful degradation when authentication fails
 * - 9.2: Fallback behavior for extension unavailability
 */
import { logger } from '@/lib/logger';
import { extensionAuthRecoveryManager } from './extension-auth-recovery';
import { extensionAuthDegradationManager, ExtensionFeatureLevel, getExtensionFallbackData, isExtensionFeatureAvailable } from './extension-auth-degradation';
import { ExtensionAuthErrorHandler, extensionAuthErrorHandler, ExtensionAuthErrorFactory, ExtensionAuthError } from './extension-auth-errors';
import { getExtensionAuthManager } from './extension-auth-manager';
// Error types and factories
export {
  extensionAuthErrorHandler,
  handleExtensionAuthError,
  createExtensionAuthError,
  getExtensionAuthRecoveryStrategy,
  isExtensionAuthErrorRetryable,
  type ExtensionAuthError
} from './extension-auth-errors';
// Graceful degradation
export {
  extensionAuthDegradationManager,
  applyExtensionAuthDegradation,
  restoreExtensionAuthFunctionality,
  isExtensionFeatureAvailable,
  getExtensionFallbackData,
  cacheExtensionData,
  type ExtensionDegradationState,
  type ExtensionFeatureConfig,
  type CachedExtensionData
} from './extension-auth-degradation';
// Error recovery
export {
  extensionAuthRecoveryManager,
  attemptExtensionAuthRecovery,
  getExtensionAuthRecoveryStats,
  cancelExtensionAuthRecovery,
  type RecoveryAttemptResult,
  type RecoveryContext,
  type RecoveryStatistics
} from './extension-auth-recovery';
// Authentication manager
export {
  getExtensionAuthManager,
  initializeExtensionAuthManager
} from './extension-auth-manager';
// Development authentication
export {
  getDevelopmentAuthManager,
  initializeDevelopmentAuthManager,
  resetDevelopmentAuthManager,
  isDevelopmentFeaturesEnabled
} from './development-auth';
// Hot reload authentication
export {
  getHotReloadAuthManager,
  initializeHotReloadAuthManager,
  resetHotReloadAuthManager
} from './hot-reload-auth';
/**
 * Convenience function to handle extension authentication errors with full recovery
 */
export async function handleExtensionAuthenticationError(
  error: Error | Response,
  endpoint: string,
  operation?: string
): Promise<unknown> {
  try {
    let authError: ExtensionAuthError;
    // Convert error to ExtensionAuthError
    if (error instanceof Response) {
      authError = ExtensionAuthErrorFactory.createFromHttpStatus(
        error.status,
        error.statusText,
        { endpoint, operation }
      );
    } else {
      authError = ExtensionAuthErrorFactory.createFromException(
        error,
        { endpoint, operation }
      );
    }
    // Handle the error through the error handler
    extensionAuthErrorHandler.handleError(authError);
    // Attempt recovery
    const recoveryResult = await extensionAuthRecoveryManager.attemptRecovery(
      authError,
      endpoint,
      operation || 'extension_operation'
    );
    // Return fallback data if available
    if (recoveryResult.fallbackData) {
      return recoveryResult.fallbackData;
    }
    // If recovery was successful but no fallback data, return null to indicate retry
    if (recoveryResult.success) {
      return null;
    }
    // If recovery failed, throw the original error
    throw authError;
  } catch (handlingError: unknown) {
    logger.error('Failed to handle extension authentication error', {
      handlingError,
      originalError: error instanceof Error ? error.message : String(error),
      endpoint,
      operation,
    });
    // If error handling itself fails, rethrow original error
    throw error;
  }
}
/**
 * Check if extension feature is currently available
 */
export function checkExtensionFeatureAvailability(featureName: string): {
  available: boolean;
  level: ExtensionFeatureLevel;
  reason?: string;
  fallbackData?: unknown;
} {
  const available = isExtensionFeatureAvailable(featureName);
  const degradationState = extensionAuthDegradationManager.getDegradationState();
  const fallbackData = available ? null : getExtensionFallbackData(featureName);
  return {
    available,
    level: degradationState.level,
    reason: available ? undefined : degradationState.reason,
    fallbackData
  };
}
/**
 * Get current extension authentication status
 */
export function getExtensionAuthStatus(): {
  degradationLevel: ExtensionFeatureLevel;
  affectedFeatures: string[];
  availableFeatures: string[];
  lastUpdate: Date;
  userMessage: string;
  recoveryEstimate?: Date;
} {
  const state = extensionAuthDegradationManager.getDegradationState();
  return {
    degradationLevel: state.level,
    affectedFeatures: state.affectedFeatures,
    availableFeatures: state.availableFeatures,
    lastUpdate: state.lastUpdate,
    userMessage: state.userMessage,
    recoveryEstimate: state.recoveryEstimate
  };
}
/**
 * Initialize extension authentication error handling system
 */
export function initializeExtensionAuthErrorHandling(): void {
  // Initialize all managers
  getExtensionAuthManager();
  ExtensionAuthErrorHandler.getInstance();
  // Log initialization
}
/**
 * Reset extension authentication error handling system
 */
export function resetExtensionAuthErrorHandling(): void {
  // Clear all state
  const errorHandler = ExtensionAuthErrorHandler.getInstance();
  errorHandler.clearErrorHistory();
  extensionAuthDegradationManager.restoreFullFunctionality();
  extensionAuthDegradationManager.clearCache();
  extensionAuthRecoveryManager.clearRecoveryHistory();
  extensionAuthRecoveryManager.cancelAllRecoveries();
}
