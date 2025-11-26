// ui_launchers/KAREN-Theme-Default/src/lib/errors/comprehensive-error-handler.ts
/**
 * Comprehensive error handler that integrates categorization and recovery
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */
import { CategorizedError, ErrorCategory, ErrorSeverity, ErrorCategorizer, ErrorRecoveryManager, RecoveryResult } from './index';

export interface ErrorHandlingOptions {
  enableRecovery?: boolean;
  enableLogging?: boolean;
  enableUserNotification?: boolean;
  maxRetryAttempts?: number;
  baseRetryDelay?: number;
  context?: Record<string, unknown>;
}

export interface ErrorHandlingResult {
  categorizedError: CategorizedError;
  recoveryResult?: RecoveryResult;
  shouldRetry: boolean;
  retryDelay?: number;
  userMessage: string;
  requiresUserAction: boolean;
}

export class ComprehensiveErrorHandler {
  private static instance: ComprehensiveErrorHandler;
  private categorizer = ErrorCategorizer.getInstance();
  private recoveryManager = ErrorRecoveryManager.getInstance();
  private errorListeners: Array<(error: CategorizedError) => void> = [];

  static getInstance(): ComprehensiveErrorHandler {
    if (!ComprehensiveErrorHandler.instance) {
      ComprehensiveErrorHandler.instance = new ComprehensiveErrorHandler();
    }
    return ComprehensiveErrorHandler.instance;
  }

  /**
   * Handle an error with full categorization and recovery
   */
  async handleError(
    error: Error | string,
    options: ErrorHandlingOptions = {}
  ): Promise<ErrorHandlingResult> {
    const {
      enableRecovery = true,
      enableLogging = true,
      enableUserNotification = true,
      context = {}
    } = options;

    // Categorize the error
    const categorizedError = this.categorizer.categorizeError(error, context);

    // Log the error if enabled
    if (enableLogging) {
      this.logError(categorizedError);
    }

    // Notify error listeners
    this.notifyErrorListeners(categorizedError);

    if (enableUserNotification) {
      this.notifyUserNotification(categorizedError);
    }

    let recoveryResult: RecoveryResult | undefined;
    let shouldRetry = false;
    let retryDelay: number | undefined;

    // Attempt recovery if enabled and error is retryable
    if (enableRecovery && categorizedError.retryable) {
      try {
        recoveryResult = await this.recoveryManager.attemptRecovery(categorizedError);
        shouldRetry = recoveryResult.shouldRetry;
        retryDelay = recoveryResult.nextRetryDelay;
      } catch (recoveryError) {
        console.warn('[ComprehensiveErrorHandler] Recovery attempt failed', recoveryError);
        shouldRetry = this.categorizer.shouldRetry(categorizedError, 0);
        retryDelay = this.categorizer.calculateRetryDelay(categorizedError, 0);
      }
    } else if (categorizedError.retryable) {
      // Basic retry without recovery
      shouldRetry = this.categorizer.shouldRetry(categorizedError, 0);
      retryDelay = this.categorizer.calculateRetryDelay(categorizedError, 0);
    }

    // Determine user message
    let userMessage = categorizedError.userMessage;
    if (recoveryResult) {
      if (recoveryResult.success) {
        userMessage = recoveryResult.message;
      } else if (shouldRetry) {
        userMessage = `${categorizedError.userMessage} Retrying in ${Math.ceil((retryDelay || 1000) / 1000)} seconds...`;
      }
    }

    // Determine if user action is required
    const requiresUserAction = this.requiresUserAction(categorizedError, recoveryResult);

    return {
      categorizedError,
      recoveryResult,
      shouldRetry,
      retryDelay,
      userMessage,
      requiresUserAction
    };
  }

  /**
   * Handle errors with automatic retry logic
   */
  async handleWithRetry<T>(
    operation: () => Promise<T>,
    options: ErrorHandlingOptions = {}
  ): Promise<T> {
    const maxAttempts = options.maxRetryAttempts || 3;
    let lastError: Error | undefined;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        const handlingResult = await this.handleError(lastError, {
          ...options,
          context: { ...options.context, attempt, maxAttempts }
        });

        // If this is the last attempt or retry is not recommended, throw
        if (attempt === maxAttempts - 1 || !handlingResult.shouldRetry) {
          throw lastError;
        }

        // Wait before retrying
        if (handlingResult.retryDelay) {
          await this.delay(handlingResult.retryDelay);
        }
      }
    }
    throw lastError;
  }

  /**
   * Create a wrapper function that automatically handles errors
   */
  createErrorHandledFunction<T extends unknown[], R>(
    fn: (...args: T) => Promise<R>,
    options: ErrorHandlingOptions = {}
  ): (...args: T) => Promise<R> {
    return async (...args: T): Promise<R> => {
      return this.handleWithRetry(() => fn(...args), options);
    };
  }

  /**
   * Log error with appropriate level based on severity
   */
  private logError(error: CategorizedError): void {
    const logData = {
      code: error.code,
      category: error.category,
      severity: error.severity,
      message: error.message,
      userMessage: error.userMessage,
      correlationId: error.correlationId,
      timestamp: error.timestamp,
      context: error.context
    };
    switch (error.severity) {
      case ErrorSeverity.CRITICAL:
        console.error('[ComprehensiveErrorHandler]', logData);
        break;
      case ErrorSeverity.HIGH:
        console.warn('[ComprehensiveErrorHandler]', logData);
        break;
      case ErrorSeverity.MEDIUM:
        console.info('[ComprehensiveErrorHandler]', logData);
        break;
      case ErrorSeverity.LOW:
        console.debug('[ComprehensiveErrorHandler]', logData);
        break;
    }
  }

  /**
   * Determine if user action is required
   */
  private requiresUserAction(
    error: CategorizedError,
    recoveryResult?: RecoveryResult
  ): boolean {
    if (error.category === ErrorCategory.CONFIGURATION) {
      return true;
    }
    if (error.category === ErrorCategory.AUTHENTICATION && 
        error.message.toLowerCase().includes('invalid')) {
      return true;
    }
    if (error.category === ErrorCategory.VALIDATION) {
      return true;
    }
    if (recoveryResult && !recoveryResult.success && !recoveryResult.shouldRetry) {
      return true;
    }
    if (error.severity === ErrorSeverity.CRITICAL && !error.retryable) {
      return true;
    }
    return false;
  }

  /**
   * Add error listener for custom error handling
   */
  addErrorListener(listener: (error: CategorizedError) => void): void {
    this.errorListeners.push(listener);
  }

  /**
   * Remove error listener
   */
  removeErrorListener(listener: (error: CategorizedError) => void): void {
    const index = this.errorListeners.indexOf(listener);
    if (index > -1) {
      this.errorListeners.splice(index, 1);
    }
  }

  /**
   * Notify all error listeners
   */
  private notifyErrorListeners(error: CategorizedError): void {
    this.errorListeners.forEach(listener => {
      try {
        listener(error);
      } catch (listenerError) {
        console.warn('[ComprehensiveErrorHandler] Listener failed', listenerError);
      }
    });
  }

  private notifyUserNotification(error: CategorizedError): void {
    if (typeof window !== 'undefined') {
      console.info('[ComprehensiveErrorHandler] User notification', error.userMessage);
    }
  }

  /**
   * Utility function to create a delay
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get error statistics for monitoring
   */
  getErrorStatistics(): {
    totalErrors: number;
    errorsByCategory: Record<ErrorCategory, number>;
    errorsBySeverity: Record<ErrorSeverity, number>;
  } {
    return {
      totalErrors: 0,
      errorsByCategory: {
        [ErrorCategory.NETWORK]: 0,
        [ErrorCategory.AUTHENTICATION]: 0,
        [ErrorCategory.DATABASE]: 0,
        [ErrorCategory.CONFIGURATION]: 0,
        [ErrorCategory.TIMEOUT]: 0,
        [ErrorCategory.VALIDATION]: 0,
        [ErrorCategory.UNKNOWN]: 0
      },
      errorsBySeverity: {
        [ErrorSeverity.LOW]: 0,
        [ErrorSeverity.MEDIUM]: 0,
        [ErrorSeverity.HIGH]: 0,
        [ErrorSeverity.CRITICAL]: 0
      }
    };
  }

  /**
   * Clear all error tracking data
   */
  clearErrorTracking(): void {
    this.recoveryManager = ErrorRecoveryManager.getInstance();
  }
}
