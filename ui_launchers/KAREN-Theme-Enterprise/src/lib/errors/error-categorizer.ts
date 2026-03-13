/**
 * Error categorization and classification system
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

import { ErrorCategory, ErrorSeverity, CategorizedError, ERROR_PATTERNS, USER_ERROR_MESSAGES } from './index';

export class ErrorCategorizer {
  private static instance: ErrorCategorizer;
  private correlationCounter = 0;

  static getInstance(): ErrorCategorizer {
    if (!ErrorCategorizer.instance) {
      ErrorCategorizer.instance = new ErrorCategorizer();
    }
    return ErrorCategorizer.instance;
  }

  /**
   * Categorize an error based on its message and context
   */
  categorizeError(
    error: Error | string, 
    context?: Record<string, unknown>
  ): CategorizedError {
    const errorMessage = typeof error === 'string' ? error : (error?.message || 'Unknown error');
    const errorStack = typeof error === 'object' && error ? error.stack : undefined;
    
    // Find matching pattern
    const matchedPattern = ERROR_PATTERNS.find(pattern => {
      if (typeof pattern.pattern === 'string') {
        return errorMessage.toLowerCase().includes(pattern.pattern.toLowerCase());
      }
      return pattern.pattern.test(errorMessage);
    });

    const category = matchedPattern?.category || ErrorCategory.UNKNOWN;
    const severity = matchedPattern?.severity || ErrorSeverity.MEDIUM;
    
    // Generate error code
    const errorCode = this.generateErrorCode(category, severity);
    
    // Get user-friendly message
    const userMessage = this.getUserMessage(category, errorMessage, context);
    
    return {
      category,
      severity,
      code: errorCode,
      message: errorMessage,
      userMessage,
      retryable: matchedPattern?.retryable || false,
      maxRetries: matchedPattern?.maxRetries || 0,
      backoffStrategy: matchedPattern?.backoffStrategy || 'fixed',
      fallbackAction: matchedPattern?.fallbackAction,
      timestamp: new Date(),
      correlationId: this.generateCorrelationId(),
      context: {
        ...context,
        stack: errorStack,
        originalError: typeof error === 'object' ? error.constructor.name : 'StringError'
      }
    };
  }

  /**
   * Generate a unique error code
   */
  private generateErrorCode(category: ErrorCategory, severity: ErrorSeverity): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 5);
    return `${category}_${severity}_${timestamp}_${random}`.toUpperCase();
  }

  /**
   * Generate a correlation ID for tracking related errors
   */
  private generateCorrelationId(): string {
    this.correlationCounter = (this.correlationCounter + 1) % 10000;
    const timestamp = Date.now().toString(36);
    const counter = this.correlationCounter.toString(36).padStart(3, '0');
    return `corr_${timestamp}_${counter}`;
  }

  /**
   * Get user-friendly error message based on category and context
   */
  private getUserMessage(
    category: ErrorCategory, 
    errorMessage: string, 
    context?: Record<string, unknown>
  ): string {
    const categoryMessages = USER_ERROR_MESSAGES[category];
    
    // Try to find specific message based on error content
    if (category === ErrorCategory.AUTHENTICATION) {
      if (errorMessage.toLowerCase().includes('expired')) {
        return categoryMessages.expired;
      }
      if (errorMessage.toLowerCase().includes('timeout')) {
        return categoryMessages.timeout;
      }
      if (errorMessage.toLowerCase().includes('invalid') || errorMessage.includes('401')) {
        return categoryMessages.invalid;
      }
    }
    
    if (category === ErrorCategory.DATABASE) {
      if (errorMessage.toLowerCase().includes('connection')) {
        return categoryMessages.connection;
      }
      if (errorMessage.toLowerCase().includes('timeout')) {
        return categoryMessages.timeout;
      }
    }
    
    if (category === ErrorCategory.NETWORK) {
      if (context?.isRetrying) {
        return categoryMessages.retry;
      }
      if (context?.usingFallback) {
        return categoryMessages.fallback;
      }
    }
    
    if (category === ErrorCategory.TIMEOUT) {
      if (context?.isRetrying) {
        return categoryMessages.retry;
      }
      if (context?.isExtended) {
        return categoryMessages.extended;
      }
    }
    
    if (category === ErrorCategory.VALIDATION) {
      if (errorMessage.toLowerCase().includes('required')) {
        return categoryMessages.required;
      }
      if (errorMessage.toLowerCase().includes('format') || errorMessage.toLowerCase().includes('invalid')) {
        return categoryMessages.format;
      }
    }
    
    return categoryMessages.default;
  }

  /**
   * Check if an error should be retried based on its category
   */
  shouldRetry(categorizedError: CategorizedError, currentAttempt: number): boolean {
    return categorizedError.retryable && currentAttempt < categorizedError.maxRetries;
  }

  /**
   * Calculate retry delay based on backoff strategy
   */
  calculateRetryDelay(
    categorizedError: CategorizedError, 
    attempt: number, 
    baseDelay: number = 1000
  ): number {
    switch (categorizedError.backoffStrategy) {
      case 'exponential':
        return Math.min(baseDelay * Math.pow(2, attempt), 30000); // Max 30 seconds
      case 'linear':
        return Math.min(baseDelay * (attempt + 1), 15000); // Max 15 seconds
      case 'fixed':
      default:
        return baseDelay;
    }
  }

  /**
   * Get severity level as number for comparison
   */
  getSeverityLevel(severity: ErrorSeverity): number {
    switch (severity) {
      case ErrorSeverity.LOW: return 1;
      case ErrorSeverity.MEDIUM: return 2;
      case ErrorSeverity.HIGH: return 3;
      case ErrorSeverity.CRITICAL: return 4;
      default: return 2;
    }
  }

  /**
   * Check if error requires immediate attention
   */
  requiresImmediateAttention(categorizedError: CategorizedError): boolean {
    return this.getSeverityLevel(categorizedError.severity) >= 3 || 
           categorizedError.category === ErrorCategory.CONFIGURATION;
  }
}
