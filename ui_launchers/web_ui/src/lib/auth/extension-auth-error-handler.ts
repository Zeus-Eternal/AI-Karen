/**
 * Extension Authentication Error Handler
 * 
 * Provides comprehensive error handling for extension authentication failures,
 * graceful degradation, and user-friendly error messages.
 * 
 * Requirements addressed:
 * - 3.1: Extension integration service error handling
 * - 3.2: Extension API calls with proper authentication
 * - 3.3: Authentication failures and retry logic
 * - 9.1: Graceful degradation when authentication fails
 * - 9.2: User-friendly error messages and recovery suggestions
 */

import { logger } from '@/lib/logger';
import { ErrorCategory } from '@/lib/connection/connection-manager';
import { ExtensionApiError } from './enhanced-karen-backend-service';

// Error recovery strategy types
export enum RecoveryStrategy {
  RETRY = 'retry',
  REFRESH_TOKEN = 'refresh_token',
  FALLBACK_MODE = 'fallback_mode',
  USER_ACTION_REQUIRED = 'user_action_required',
  IGNORE = 'ignore',
}

// Error classification interface
export interface ErrorClassification {
  category: ErrorCategory;
  severity: 'low' | 'medium' | 'high' | 'critical';
  userMessage: string;
  technicalMessage: string;
  recoveryStrategy: RecoveryStrategy;
  retryable: boolean;
  requiresUserAction: boolean;
  fallbackAvailable: boolean;
}

// Recovery action interface
export interface RecoveryAction {
  type: RecoveryStrategy;
  description: string;
  action: () => Promise<void>;
  priority: number;
}

// Error context interface
export interface ErrorContext {
  endpoint: string;
  method: string;
  attempt: number;
  maxAttempts: number;
  timestamp: Date;
  userAgent?: string;
  sessionId?: string;
}

/**
 * Extension Authentication Error Handler
 * 
 * Handles authentication errors with intelligent classification,
 * recovery strategies, and user-friendly messaging.
 */
export class ExtensionAuthErrorHandler {
  private readonly errorHistory: Map<string, number> = new Map();
  private readonly maxHistorySize = 100;

  /**
   * Handle extension authentication error
   */
  handleError(
    error: any,
    context: ErrorContext
  ): ErrorClassification {
    const classification = this.classifyError(error, context);
    
    // Record error in history for pattern analysis
    this.recordError(error, context);
    
    // Log error with appropriate level
    this.logError(error, classification, context);
    
    return classification;
  }

  /**
   * Classify error and determine recovery strategy
   */
  private classifyError(
    error: any,
    context: ErrorContext
  ): ErrorClassification {
    // Handle ExtensionApiError
    if (error instanceof ExtensionApiError) {
      return this.classifyExtensionApiError(error, context);
    }

    // Handle network errors
    if (error instanceof TypeError || error.name === 'NetworkError') {
      return {
        category: ErrorCategory.NETWORK_ERROR,
        severity: 'high',
        userMessage: 'Unable to connect to extension services. Please check your internet connection.',
        technicalMessage: `Network error: ${error.message}`,
        recoveryStrategy: RecoveryStrategy.RETRY,
        retryable: true,
        requiresUserAction: false,
        fallbackAvailable: true,
      };
    }

    // Handle timeout errors
    if (error.name === 'AbortError' || error.message?.includes('timeout')) {
      return {
        category: ErrorCategory.TIMEOUT_ERROR,
        severity: 'medium',
        userMessage: 'Extension service is taking longer than expected. Please wait or try again.',
        technicalMessage: `Timeout error: ${error.message}`,
        recoveryStrategy: RecoveryStrategy.RETRY,
        retryable: true,
        requiresUserAction: false,
        fallbackAvailable: true,
      };
    }

    // Generic error classification
    return {
      category: ErrorCategory.UNKNOWN_ERROR,
      severity: 'medium',
      userMessage: 'An unexpected error occurred with extension services. Please try again.',
      technicalMessage: error.message || 'Unknown error',
      recoveryStrategy: RecoveryStrategy.RETRY,
      retryable: true,
      requiresUserAction: false,
      fallbackAvailable: false,
    };
  }

  /**
   * Classify ExtensionApiError specifically
   */
  private classifyExtensionApiError(
    error: ExtensionApiError,
    context: ErrorContext
  ): ErrorClassification {
    switch (error.status) {
      case 401:
        return {
          category: ErrorCategory.HTTP_ERROR,
          severity: 'high',
          userMessage: 'Authentication required. Please log in to access extension features.',
          technicalMessage: `Authentication failed: ${error.message}`,
          recoveryStrategy: RecoveryStrategy.REFRESH_TOKEN,
          retryable: true,
          requiresUserAction: true,
          fallbackAvailable: false,
        };

      case 403:
        return {
          category: ErrorCategory.HTTP_ERROR,
          severity: 'high',
          userMessage: 'You don\'t have permission to access this extension feature.',
          technicalMessage: `Authorization failed: ${error.message}`,
          recoveryStrategy: RecoveryStrategy.USER_ACTION_REQUIRED,
          retryable: false,
          requiresUserAction: true,
          fallbackAvailable: true,
        };

      case 404:
        return {
          category: ErrorCategory.HTTP_ERROR,
          severity: 'medium',
          userMessage: 'Extension service not found. It may be temporarily unavailable.',
          technicalMessage: `Service not found: ${error.message}`,
          recoveryStrategy: RecoveryStrategy.FALLBACK_MODE,
          retryable: false,
          requiresUserAction: false,
          fallbackAvailable: true,
        };

      case 429:
        return {
          category: ErrorCategory.HTTP_ERROR,
          severity: 'medium',
          userMessage: 'Too many requests. Please wait a moment before trying again.',
          technicalMessage: `Rate limited: ${error.message}`,
          recoveryStrategy: RecoveryStrategy.RETRY,
          retryable: true,
          requiresUserAction: false,
          fallbackAvailable: false,
        };

      case 500:
      case 502:
      case 503:
      case 504:
        return {
          category: ErrorCategory.HTTP_ERROR,
          severity: 'high',
          userMessage: 'Extension service is temporarily unavailable. Please try again later.',
          technicalMessage: `Server error: ${error.message}`,
          recoveryStrategy: RecoveryStrategy.FALLBACK_MODE,
          retryable: true,
          requiresUserAction: false,
          fallbackAvailable: true,
        };

      default:
        return {
          category: error.category,
          severity: 'medium',
          userMessage: 'Extension service encountered an error. Please try again.',
          technicalMessage: error.message,
          recoveryStrategy: RecoveryStrategy.RETRY,
          retryable: error.retryable,
          requiresUserAction: false,
          fallbackAvailable: false,
        };
    }
  }

  /**
   * Generate recovery actions based on error classification
   */
  generateRecoveryActions(
    classification: ErrorClassification,
    context: ErrorContext
  ): RecoveryAction[] {
    const actions: RecoveryAction[] = [];

    switch (classification.recoveryStrategy) {
      case RecoveryStrategy.RETRY:
        if (context.attempt < context.maxAttempts) {
          actions.push({
            type: RecoveryStrategy.RETRY,
            description: 'Retry the request',
            action: async () => {
              // Retry logic would be handled by the calling service
              logger.debug('Retry action triggered for:', context.endpoint);
            },
            priority: 1,

        }
        break;

      case RecoveryStrategy.REFRESH_TOKEN:
        actions.push({
          type: RecoveryStrategy.REFRESH_TOKEN,
          description: 'Refresh authentication token',
          action: async () => {
            // Token refresh would be handled by the auth manager
            logger.debug('Token refresh action triggered');
          },
          priority: 1,

        break;

      case RecoveryStrategy.FALLBACK_MODE:
        if (classification.fallbackAvailable) {
          actions.push({
            type: RecoveryStrategy.FALLBACK_MODE,
            description: 'Switch to fallback mode',
            action: async () => {
              logger.debug('Fallback mode activated for:', context.endpoint);
            },
            priority: 2,

        }
        break;

      case RecoveryStrategy.USER_ACTION_REQUIRED:
        actions.push({
          type: RecoveryStrategy.USER_ACTION_REQUIRED,
          description: 'User intervention required',
          action: async () => {
            logger.debug('User action required for:', context.endpoint);
          },
          priority: 3,

        break;

      case RecoveryStrategy.IGNORE:
        actions.push({
          type: RecoveryStrategy.IGNORE,
          description: 'Ignore error and continue',
          action: async () => {
            logger.debug('Ignoring error for:', context.endpoint);
          },
          priority: 4,

        break;
    }

    return actions.sort((a, b) => a.priority - b.priority);
  }

  /**
   * Check if error should trigger fallback mode
   */
  shouldUseFallbackMode(classification: ErrorClassification): boolean {
    return (
      classification.fallbackAvailable &&
      (classification.severity === 'high' || classification.severity === 'critical') &&
      !classification.requiresUserAction
    );
  }

  /**
   * Get user-friendly error message with recovery suggestions
   */
  getUserFriendlyMessage(
    classification: ErrorClassification,
    includeRecoveryTips: boolean = true
  ): string {
    let message = classification.userMessage;

    if (includeRecoveryTips) {
      const tips = this.getRecoveryTips(classification);
      if (tips.length > 0) {
        message += '\n\nSuggestions:\n' + tips.join('\n');
      }
    }

    return message;
  }

  /**
   * Get recovery tips based on error classification
   */
  private getRecoveryTips(classification: ErrorClassification): string[] {
    const tips: string[] = [];

    switch (classification.recoveryStrategy) {
      case RecoveryStrategy.RETRY:
        tips.push('• Try again in a few moments');
        if (classification.category === ErrorCategory.NETWORK_ERROR) {
          tips.push('• Check your internet connection');
        }
        break;

      case RecoveryStrategy.REFRESH_TOKEN:
        tips.push('• Try refreshing the page');
        tips.push('• Log out and log back in if the problem persists');
        break;

      case RecoveryStrategy.FALLBACK_MODE:
        tips.push('• Some features may be temporarily limited');
        tips.push('• Core functionality should still work');
        break;

      case RecoveryStrategy.USER_ACTION_REQUIRED:
        if (classification.userMessage.includes('permission')) {
          tips.push('• Contact your administrator for access');
        } else {
          tips.push('• Check your account settings');
        }
        break;
    }

    return tips;
  }

  /**
   * Record error for pattern analysis
   */
  private recordError(error: any, context: ErrorContext): void {
    const errorKey = `${context.endpoint}:${error.status || 'unknown'}`;
    const currentCount = this.errorHistory.get(errorKey) || 0;
    this.errorHistory.set(errorKey, currentCount + 1);

    // Limit history size
    if (this.errorHistory.size > this.maxHistorySize) {
      const firstKey = this.errorHistory.keys().next().value;
      if (firstKey !== undefined) {
        this.errorHistory.delete(firstKey);
      }
    }
  }

  /**
   * Log error with appropriate level
   */
  private logError(
    error: any,
    classification: ErrorClassification,
    context: ErrorContext
  ): void {
    const logData = {
      endpoint: context.endpoint,
      method: context.method,
      attempt: context.attempt,
      category: classification.category,
      severity: classification.severity,
      recoveryStrategy: classification.recoveryStrategy,
      retryable: classification.retryable,
    };

    switch (classification.severity) {
      case 'critical':
        logger.error('Critical extension auth error: ' + classification.technicalMessage, logData);
        break;
      case 'high':
        logger.error('High severity extension auth error: ' + classification.technicalMessage, logData);
        break;
      case 'medium':
        logger.warn('Medium severity extension auth error:', classification.technicalMessage, logData);
        break;
      case 'low':
        logger.debug('Low severity extension auth error:', classification.technicalMessage, logData);
        break;
    }
  }

  /**
   * Get error statistics for monitoring
   */
  getErrorStatistics(): Record<string, number> {
    return Object.fromEntries(this.errorHistory);
  }

  /**
   * Clear error history
   */
  clearErrorHistory(): void {
    this.errorHistory.clear();
  }
}

// Global instance
let extensionAuthErrorHandler: ExtensionAuthErrorHandler | null = null;

/**
 * Get the global extension auth error handler instance
 */
export function getExtensionAuthErrorHandler(): ExtensionAuthErrorHandler {
  if (!extensionAuthErrorHandler) {
    extensionAuthErrorHandler = new ExtensionAuthErrorHandler();
  }
  return extensionAuthErrorHandler;
}

/**
 * Initialize a new extension auth error handler instance
 */
export function initializeExtensionAuthErrorHandler(): ExtensionAuthErrorHandler {
  extensionAuthErrorHandler = new ExtensionAuthErrorHandler();
  return extensionAuthErrorHandler;
}