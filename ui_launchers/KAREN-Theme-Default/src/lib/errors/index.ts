/**
 * Comprehensive error handling system exports
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

// Core types and enums
export {
  ErrorCategory,
  ErrorSeverity,
  type CategorizedError,
  type ErrorPattern
} from './error-categories';

// Error categorization
export {
  ErrorCategorizer
} from './error-categorizer';

// Error recovery
export {
  type RecoveryAction,
  type RecoveryStrategy,
  type RecoveryResult
} from './error-recovery';

// Comprehensive error handler
export {
  type ErrorHandlingOptions,
  type ErrorHandlingResult
} from './comprehensive-error-handler';

// Import for internal use
import { ComprehensiveErrorHandler } from './comprehensive-error-handler';
import { ErrorCategorizer } from './error-categorizer';
import { ErrorRecoveryManager } from './error-recovery';

// Convenience exports for common usage - lazy initialization to avoid circular dependencies
let _errorHandler: ComprehensiveErrorHandler | null = null;
let _errorCategorizer: ErrorCategorizer | null = null;
let _recoveryManager: ErrorRecoveryManager | null = null;

export const errorHandler = {
  getInstance: () => {
    if (!_errorHandler) {
      _errorHandler = ComprehensiveErrorHandler.getInstance();
    }
    return _errorHandler;
  }
};

export const errorCategorizer = {
  getInstance: () => {
    if (!_errorCategorizer) {
      _errorCategorizer = ErrorCategorizer.getInstance();
    }
    return _errorCategorizer;
  }
};

export const recoveryManager = {
  getInstance: () => {
    if (!_recoveryManager) {
      _recoveryManager = ErrorRecoveryManager.getInstance();
    }
    return _recoveryManager;
  }
};

/**
 * Quick error handling function for simple use cases
 */
export async function handleError(
  error: Error | string,
  options?: {
    enableRecovery?: boolean;
    enableLogging?: boolean;
    context?: Record<string, any>;
  }
) {
  return errorHandler.getInstance().handleError(error, options);
}

/**
 * Create an error-handled version of an async function
 */
export function withErrorHandling<T extends any[], R>(
  fn: (...args: T) => Promise<R>,
  options?: {
    maxRetryAttempts?: number;
    enableRecovery?: boolean;
    context?: Record<string, any>;
  }
): (...args: T) => Promise<R> {
  return errorHandler.getInstance().createErrorHandledFunction(fn, options);
}

/**
 * Handle errors with automatic retry
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  options?: {
    maxRetryAttempts?: number;
    baseRetryDelay?: number;
    context?: Record<string, any>;
  }
): Promise<T> {
  return errorHandler.getInstance().handleWithRetry(operation, options);
}
