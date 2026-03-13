/**
 * Admin Error Handler
 * Provides error handling utilities for admin operations
 */

export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface ErrorContext {
  operation?: string;
  userId?: string;
  timestamp?: Date;
  [key: string]: unknown;
}

export interface AdminError {
  code: string;
  message: string;
  severity: ErrorSeverity;
  context?: ErrorContext;
  timestamp?: Date;
  details?: Record<string, unknown>;
}

export class AdminErrorHandler {
  /**
   * Create a new error
   */
  static createError(code: string, message: string, context?: Partial<ErrorContext>): AdminError {
    return {
      code,
      message,
      severity: 'medium',
      context: {
        timestamp: new Date(),
        ...context
      }
    };
  }

  /**
   * Create error from HTTP response
   */
  static fromHttpError(status: number, data: unknown, context?: Partial<ErrorContext>): AdminError {
    const severity = status >= 500 ? 'critical' : status >= 400 ? 'high' : 'medium';
    return {
      code: `HTTP_${status}`,
      message: `HTTP Error: ${status}`,
      severity,
      context: {
        timestamp: new Date(),
        ...context
      }
    };
  }

  /**
   * Create error from network error
   */
  static fromNetworkError(error: Error, context?: Partial<ErrorContext>): AdminError {
    return {
      code: 'NETWORK_ERROR',
      message: error.message || 'Network error occurred',
      severity: 'high',
      context: {
        timestamp: new Date(),
        ...context
      }
    };
  }

  /**
   * Determine if an error should be retried
   */
  static shouldRetry(error: AdminError, attemptNumber: number): boolean {
    // Don't retry critical errors
    if (error.severity === 'critical') {
      return false;
    }
    
    // Retry network errors up to 3 times
    if (error.code === 'NETWORK_ERROR' && attemptNumber < 3) {
      return true;
    }
    
    // Don't retry other errors
    return false;
  }

  /**
   * Get retry delay based on error and attempt number
   */
  static getRetryDelay(error: AdminError, attemptNumber: number): number {
    // Exponential backoff
    return Math.min(1000 * Math.pow(2, attemptNumber), 10000);
  }

  /**
   * Log error to console
   */
  static logError(error: AdminError, context?: Partial<ErrorContext>): void {
    console.error('[AdminErrorHandler]', {
      code: error.code,
      message: error.message,
      severity: error.severity,
      context: {
        ...error.context,
        ...context
      }
    });
  }
}

export default AdminErrorHandler;
