import { logger } from '@/lib/logger';
import { errorHandler, type ErrorInfo } from '@/lib/error-handler';
import { getExtensionAuthManager } from './extension-auth-manager';
import {
  extensionAuthErrorHandler,
  ExtensionAuthError,
  ExtensionAuthRecoveryStrategy,
} from './extension-auth-errors';
import { extensionAuthDegradationManager } from './extension-auth-degradation';
/**
 * Extension Authentication Error Recovery Manager
 * 
 * Implements comprehensive error recovery strategies for extension authentication failures,
 * including automatic retry logic, fallback mechanisms, and user-friendly error handling.
 * 
 * Requirements addressed:
 * - 3.1: Extension integration service error handling
 * - 3.2: Extension API calls with proper authentication
 * - 3.3: Authentication failures and retry logic
 * - 9.1: Graceful degradation when authentication fails
 * - 9.2: Fallback behavior for extension unavailability
 */
/**
 * Recovery attempt result
 */
export interface RecoveryAttemptResult {
  success: boolean;
  strategy: ExtensionAuthRecoveryStrategy;
  message: string;
  nextAttemptDelay?: number;
  fallbackData?: any;
  requiresUserAction: boolean;
}

/**
 * Recovery context for tracking recovery attempts
 */
export interface RecoveryContext {
  originalError: ExtensionAuthError;
  attemptCount: number;
  maxAttempts: number;
  lastAttemptTime: Date;
  nextAttemptTime?: Date;
  recoveryStrategy: ExtensionAuthRecoveryStrategy;
  endpoint: string;
  operation: string;
}

/**
 * Recovery statistics
 */
export interface RecoveryStatistics {
  totalAttempts: number;
  successfulRecoveries: number;
  failedRecoveries: number;
  averageRecoveryTime: number;
  mostCommonErrors: Array<{ category: string; count: number }>;
  recoveryStrategiesUsed: Array<{ strategy: string; count: number; successRate: number }>;
}

/**
 * Extension authentication error recovery manager
 */
export class ExtensionAuthRecoveryManager {
  private static instance: ExtensionAuthRecoveryManager;
  private activeRecoveries: Map<string, RecoveryContext> = new Map();
  private recoveryHistory: RecoveryAttemptResult[] = [];
  private readonly MAX_RECOVERY_HISTORY = 100;
  private readonly DEFAULT_MAX_ATTEMPTS = 3;
  private readonly BASE_RETRY_DELAY = 1000; // 1 second

  static getInstance(): ExtensionAuthRecoveryManager {
    if (!ExtensionAuthRecoveryManager.instance) {
      ExtensionAuthRecoveryManager.instance = new ExtensionAuthRecoveryManager();
    }
    return ExtensionAuthRecoveryManager.instance;
  }

  /**
   * Attempt to recover from extension authentication error
   */
  async attemptRecovery(
    error: ExtensionAuthError,
    endpoint: string,
    operation: string = 'extension operation'
  ): Promise<RecoveryAttemptResult> {
    const recoveryKey = `${endpoint}:${operation}`;
    let context = this.activeRecoveries.get(recoveryKey);

    if (!context) {
      context = {
        originalError: error,
        attemptCount: 0,
        maxAttempts: this.getMaxAttemptsForStrategy(error.recoveryStrategy),
        lastAttemptTime: new Date(),
        recoveryStrategy: error.recoveryStrategy,
        endpoint,
        operation
      };
      this.activeRecoveries.set(recoveryKey, context);
    }

    context.attemptCount++;
    context.lastAttemptTime = new Date();

    logger.info(`Attempting extension auth recovery (${context.attemptCount}/${context.maxAttempts}):`, {
      strategy: error.recoveryStrategy,
      endpoint,
      operation,
      errorCategory: error.category
    });

    let result: RecoveryAttemptResult;

    try {
      result = await this.executeRecoveryStrategy(error, context);
    } catch (recoveryError) {
      logger.error('Recovery strategy execution failed:', recoveryError);
      result = {
        success: false,
        strategy: error.recoveryStrategy,
        message: 'Recovery attempt failed due to internal error',
        requiresUserAction: true
      };
    }

    // Update recovery context
    if (result.success || context.attemptCount >= context.maxAttempts) {
      this.activeRecoveries.delete(recoveryKey);
    } else if (result.nextAttemptDelay) {
      context.nextAttemptTime = new Date(Date.now() + result.nextAttemptDelay);
    }

    // Add to history
    this.addToRecoveryHistory(result);

    // Handle the error through the error handler system
    const errorInfo = extensionAuthErrorHandler.handleError(error);
    this.showUserFeedback(errorInfo, result);

    return result;
  }

  /**
   * Execute specific recovery strategy
   */
  private async executeRecoveryStrategy(
    error: ExtensionAuthError,
    context: RecoveryContext
  ): Promise<RecoveryAttemptResult> {
    switch (error.recoveryStrategy) {
      case ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH:
        return this.retryWithRefresh(error, context);

      case ExtensionAuthRecoveryStrategy.RETRY_WITH_BACKOFF:
        return this.retryWithBackoff(error, context);

      case ExtensionAuthRecoveryStrategy.FALLBACK_TO_READONLY:
        return this.fallbackToReadonly(error, context);

      case ExtensionAuthRecoveryStrategy.FALLBACK_TO_CACHED:
        return this.fallbackToCached(error, context);

      case ExtensionAuthRecoveryStrategy.REDIRECT_TO_LOGIN:
        return this.redirectToLogin(error, context);

      case ExtensionAuthRecoveryStrategy.GRACEFUL_DEGRADATION:
        return this.gracefulDegradation(error, context);

      case ExtensionAuthRecoveryStrategy.SHOW_ERROR_MESSAGE:
        return this.showErrorMessage(error, context);

      case ExtensionAuthRecoveryStrategy.NO_RECOVERY:
        return this.noRecovery(error, context);

      default:
        return this.defaultRecovery(error, context);
    }
  }

  /**
   * Retry with token refresh
   */
  private async retryWithRefresh(
    error: ExtensionAuthError,
    context: RecoveryContext
  ): Promise<RecoveryAttemptResult> {
    try {
      const authManager = getExtensionAuthManager();
      const newToken = await authManager.forceRefresh();

      if (newToken) {
        logger.info('Extension auth token refreshed successfully');
        return {
          success: true,
          strategy: ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH,
          message: 'Authentication token refreshed successfully',
          requiresUserAction: false
        };
      } else {
        return {
          success: false,
          strategy: ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH,
          message: 'Token refresh failed, user authentication required',
          requiresUserAction: true,
          nextAttemptDelay: this.calculateBackoffDelay(context.attemptCount)
        };
      }
    } catch (refreshError) {
      logger.error('Token refresh failed:', refreshError);
      return {
        success: false,
        strategy: ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH,
        message: 'Token refresh failed, please log in again',
        requiresUserAction: true
      };
    }
  }

  /**
   * Retry with exponential backoff
   */
  private async retryWithBackoff(
    error: ExtensionAuthError,
    context: RecoveryContext
  ): Promise<RecoveryAttemptResult> {
    const delay = this.calculateBackoffDelay(context.attemptCount);
    
    if (context.attemptCount >= context.maxAttempts) {
      return {
        success: false,
        strategy: ExtensionAuthRecoveryStrategy.RETRY_WITH_BACKOFF,
        message: 'Maximum retry attempts reached, falling back to limited functionality',
        requiresUserAction: false
      };
    }

    return {
      success: false,
      strategy: ExtensionAuthRecoveryStrategy.RETRY_WITH_BACKOFF,
      message: `Retrying in ${Math.round(delay / 1000)} seconds...`,
      nextAttemptDelay: delay,
      requiresUserAction: false
    };
  }

  /**
   * Fallback to read-only mode
   */
  private async fallbackToReadonly(
    error: ExtensionAuthError,
    context: RecoveryContext
  ): Promise<RecoveryAttemptResult> {
    const degradationState = extensionAuthDegradationManager.applyDegradation(error);
    const fallbackData = extensionAuthDegradationManager.getFallbackData(context.operation);

    return {
      success: true,
      strategy: ExtensionAuthRecoveryStrategy.FALLBACK_TO_READONLY,
      message: 'Extension features are available in read-only mode',
      fallbackData,
      requiresUserAction: false
    };
  }

  /**
   * Fallback to cached data
   */
  private async fallbackToCached(
    error: ExtensionAuthError,
    context: RecoveryContext
  ): Promise<RecoveryAttemptResult> {
    const degradationState = extensionAuthDegradationManager.applyDegradation(error);
    const cachedData = extensionAuthDegradationManager.getCachedData(context.operation);

    if (cachedData) {
      return {
        success: true,
        strategy: ExtensionAuthRecoveryStrategy.FALLBACK_TO_CACHED,
        message: 'Using cached data while reconnecting to extension services',
        fallbackData: cachedData,
        requiresUserAction: false
      };
    } else {
      const staticFallback = extensionAuthDegradationManager.getFallbackData(context.operation);
      return {
        success: true,
        strategy: ExtensionAuthRecoveryStrategy.FALLBACK_TO_CACHED,
        message: 'No cached data available, using limited functionality',
        fallbackData: staticFallback,
        requiresUserAction: false
      };
    }
  }

  /**
   * Redirect to login
   */
  private async redirectToLogin(
    error: ExtensionAuthError,
    context: RecoveryContext
  ): Promise<RecoveryAttemptResult> {
    // Clear any existing auth state
    const authManager = getExtensionAuthManager();
    authManager.clearAuth();

    // In a real application, this would trigger a redirect to login
    // For now, we'll just indicate that user action is required
    if (typeof window !== 'undefined') {
      // Store the current location for redirect after login
      sessionStorage.setItem('extension_auth_redirect', window.location.pathname);
      
      // In a real app, you might do: window.location.href = '/login';
      logger.info('User authentication required, should redirect to login');
    }

    return {
      success: false,
      strategy: ExtensionAuthRecoveryStrategy.REDIRECT_TO_LOGIN,
      message: 'Please log in to continue using extension features',
      requiresUserAction: true
    };
  }

  /**
   * Apply graceful degradation
   */
  private async gracefulDegradation(
    error: ExtensionAuthError,
    context: RecoveryContext
  ): Promise<RecoveryAttemptResult> {
    const degradationState = extensionAuthDegradationManager.applyDegradation(error);
    const fallbackData = extensionAuthDegradationManager.getFallbackData(context.operation);

    let message: string;
    switch (degradationState.level) {
      case ExtensionFeatureLevel.LIMITED:
        message = 'Some extension features are temporarily unavailable';
        break;
      case ExtensionFeatureLevel.READONLY:
        message = 'Extension features are available in read-only mode';
        break;
      case ExtensionFeatureLevel.CACHED:
        message = 'Using cached extension data while reconnecting';
        break;
      case ExtensionFeatureLevel.DISABLED:
        message = 'Extension features are temporarily disabled';
        break;
      default:
        message = 'Extension functionality has been adjusted';
    }

    return {
      success: true,
      strategy: ExtensionAuthRecoveryStrategy.GRACEFUL_DEGRADATION,
      message,
      fallbackData,
      requiresUserAction: false
    };
  }

  /**
   * Show error message only
   */
  private async showErrorMessage(
    error: ExtensionAuthError,
    context: RecoveryContext
  ): Promise<RecoveryAttemptResult> {
    return {
      success: false,
      strategy: ExtensionAuthRecoveryStrategy.SHOW_ERROR_MESSAGE,
      message: error.message,
      requiresUserAction: error.userActionRequired
    };
  }

  /**
   * No recovery possible
   */
  private async noRecovery(
    error: ExtensionAuthError,
    context: RecoveryContext
  ): Promise<RecoveryAttemptResult> {
    return {
      success: false,
      strategy: ExtensionAuthRecoveryStrategy.NO_RECOVERY,
      message: 'Extension features are unavailable due to a system configuration issue',
      requiresUserAction: true
    };
  }

  /**
   * Default recovery strategy
   */
  private async defaultRecovery(
    error: ExtensionAuthError,
    context: RecoveryContext
  ): Promise<RecoveryAttemptResult> {
    // Default to graceful degradation
    return this.gracefulDegradation(error, context);
  }

  /**
   * Calculate exponential backoff delay
   */
  private calculateBackoffDelay(attemptCount: number): number {
    const maxDelay = 30000; // 30 seconds max
    const delay = this.BASE_RETRY_DELAY * Math.pow(2, attemptCount - 1);
    return Math.min(delay, maxDelay);
  }

  /**
   * Get maximum attempts for recovery strategy
   */
  private getMaxAttemptsForStrategy(strategy: ExtensionAuthRecoveryStrategy): number {
    switch (strategy) {
      case ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH:
        return 2;
      case ExtensionAuthRecoveryStrategy.RETRY_WITH_BACKOFF:
        return 3;
      case ExtensionAuthRecoveryStrategy.FALLBACK_TO_READONLY:
      case ExtensionAuthRecoveryStrategy.FALLBACK_TO_CACHED:
      case ExtensionAuthRecoveryStrategy.GRACEFUL_DEGRADATION:
        return 1; // These are immediate fallbacks
      case ExtensionAuthRecoveryStrategy.REDIRECT_TO_LOGIN:
      case ExtensionAuthRecoveryStrategy.SHOW_ERROR_MESSAGE:
      case ExtensionAuthRecoveryStrategy.NO_RECOVERY:
        return 1; // These don't retry
      default:
        return this.DEFAULT_MAX_ATTEMPTS;
    }
  }

  /**
   * Show user feedback based on recovery result
   */
  private showUserFeedback(errorInfo: ErrorInfo, result: RecoveryAttemptResult): void {
    if (typeof window === 'undefined') return;

    // Use the existing error handler to show appropriate feedback
    if (result.success) {
      if (result.fallbackData) {
        errorHandler.showWarning(
          'Limited Functionality',
          result.message,
          5000
        );
      } else {
        errorHandler.showSuccess(
          'Recovered',
          result.message,
          3000
        );
      }
    } else {
      if (result.requiresUserAction) {
        errorHandler.showWarning(
          'Action Required',
          result.message
        );
      } else {
        errorHandler.showWarning(
          'Temporary Issue',
          result.message,
          4000
        );
      }
    }
  }

  /**
   * Add recovery result to history
   */
  private addToRecoveryHistory(result: RecoveryAttemptResult): void {
    this.recoveryHistory.push(result);

    // Maintain history size limit
    if (this.recoveryHistory.length > this.MAX_RECOVERY_HISTORY) {
      this.recoveryHistory = this.recoveryHistory.slice(-this.MAX_RECOVERY_HISTORY);
    }
  }

  /**
   * Get recovery statistics
   */
  getRecoveryStatistics(): RecoveryStatistics {
    const total = this.recoveryHistory.length;
    const successful = this.recoveryHistory.filter(r => r.success).length;
    const failed = total - successful;

    // Calculate strategy usage and success rates
    const strategyStats = new Map<string, { count: number; successes: number }>();
    
    for (const result of this.recoveryHistory) {
      const strategy = result.strategy;
      const stats = strategyStats.get(strategy) || { count: 0, successes: 0 };
      stats.count++;
      if (result.success) stats.successes++;
      strategyStats.set(strategy, stats);
    }

    const recoveryStrategiesUsed = Array.from(strategyStats.entries()).map(([strategy, stats]) => ({
      strategy,
      count: stats.count,
      successRate: stats.count > 0 ? stats.successes / stats.count : 0
    }));

    return {
      totalAttempts: total,
      successfulRecoveries: successful,
      failedRecoveries: failed,
      averageRecoveryTime: 0, // Would need to track timing
      mostCommonErrors: [], // Would need to track error categories
      recoveryStrategiesUsed
    };
  }

  /**
   * Clear recovery history
   */
  clearRecoveryHistory(): void {
    this.recoveryHistory = [];
    logger.info('Extension auth recovery history cleared');
  }

  /**
   * Get active recovery contexts
   */
  getActiveRecoveries(): Array<{ key: string; context: RecoveryContext }> {
    return Array.from(this.activeRecoveries.entries()).map(([key, context]) => ({
      key,
      context: { ...context }
    }));
  }

  /**
   * Cancel active recovery
   */
  cancelRecovery(endpoint: string, operation: string): boolean {
    const recoveryKey = `${endpoint}:${operation}`;
    const deleted = this.activeRecoveries.delete(recoveryKey);
    
    if (deleted) {
      logger.info(`Cancelled active recovery for ${recoveryKey}`);
    }
    
    return deleted;
  }

  /**
   * Cancel all active recoveries
   */
  cancelAllRecoveries(): void {
    const count = this.activeRecoveries.size;
    this.activeRecoveries.clear();
    logger.info(`Cancelled ${count} active recoveries`);
  }
}

// Export singleton instance
export const extensionAuthRecoveryManager = ExtensionAuthRecoveryManager.getInstance();

// Export convenience functions
export const attemptExtensionAuthRecovery = (
  error: ExtensionAuthError,
  endpoint: string,
  operation?: string
) => extensionAuthRecoveryManager.attemptRecovery(error, endpoint, operation);

export const getExtensionAuthRecoveryStats = () => 
  extensionAuthRecoveryManager.getRecoveryStatistics();

export const cancelExtensionAuthRecovery = (endpoint: string, operation: string) => 
  extensionAuthRecoveryManager.cancelRecovery(endpoint, operation);
