// ui_launchers/KAREN-Theme-Default/src/lib/errors/error-utils.ts
/**
 * Error handling utility functions
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

import { ComprehensiveErrorHandler, ErrorHandlingOptions, ErrorHandlingResult } from './comprehensive-error-handler';

const errorHandler = ComprehensiveErrorHandler.getInstance();

/**
 * Handle an error with categorization and recovery
 */
export async function handleError(
  error: Error | string,
  options: ErrorHandlingOptions = {}
): Promise<ErrorHandlingResult> {
  return errorHandler.handleError(error, options);
}

/**
 * Wrap a function with error handling
 */
export function withErrorHandling<T extends unknown[], R>(
  fn: (...args: T) => Promise<R>,
  options: ErrorHandlingOptions = {}
): (...args: T) => Promise<R> {
  return async (...args: T): Promise<R> => {
    try {
      return await fn(...args);
    } catch (error) {
      const result = await errorHandler.handleError(error, options);
      if (!result.shouldRetry) {
        throw error;
      }
      // If retry is needed, wait for the specified delay
      await new Promise(resolve => setTimeout(resolve, result.retryDelay || 1000));
      // Retry the function
      return fn(...args);
    }
  };
}

/**
 * Execute a function with automatic retry logic
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: ErrorHandlingOptions = {}
): Promise<T> {
  const maxAttempts = options.maxRetryAttempts || 3;
  let lastError: Error;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      const result = await errorHandler.handleError(error, {
        ...options,
        maxRetryAttempts: 0 // Disable retry in the error handler since we're handling it here
      });
      
      if (attempt < maxAttempts && result.shouldRetry) {
        const delay = result.retryDelay || (attempt * 1000);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        break;
      }
    }
  }
  
  throw lastError!;
}