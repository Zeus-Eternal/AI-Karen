/**
 * Error Handler for KAREN Theme Default
 * Provides centralized error handling utilities
 */

export interface ErrorContext {
  type: 'error' | 'warning' | 'info';
  message: string;
  code?: string;
  details?: unknown;
  timestamp?: Date;
  component?: string;
  operation?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Safely log information without throwing errors
 */
export function safeLog(message: string, data?: unknown): void {
  if (process.env.NODE_ENV === 'development') {
    console.log(message, data);
  }
}

/**
 * Safely log warnings without throwing errors
 */
export function safeWarn(message: string, error?: unknown): void {
  if (process.env.NODE_ENV === 'development') {
    console.warn(message, error);
  }
}

/**
 * Safely log errors without throwing
 */
export function safeError(message: string, error?: unknown): void {
  if (process.env.NODE_ENV === 'development') {
    console.error(message, error);
  }
}

/**
 * Convert unknown error to ErrorContext
 */
export function toErrorContext(error: unknown, context?: Partial<ErrorContext>): ErrorContext {
  if (error instanceof Error) {
    return {
      type: 'error',
      message: error.message,
      details: {
        ...(typeof context?.details === 'object' ? context.details as Record<string, unknown> : {}),
        stack: error.stack,
        name: error.name
      },
      timestamp: new Date(),
      ...context
    };
  }

  if (typeof error === 'string') {
    return {
      type: 'error',
      message: error,
      timestamp: new Date(),
      ...context
    };
  }

  if (error && typeof error === 'object') {
    return {
      type: 'error',
      message: String(error),
      details: error,
      timestamp: new Date(),
      ...context
    };
  }

  return {
    type: 'error',
    message: 'Unknown error occurred',
    details: { originalError: error },
    timestamp: new Date(),
    ...context
  };
}

/**
 * Handle errors with context
 */
export function handleError(error: unknown, context?: Partial<ErrorContext>): ErrorContext {
  const errorContext = toErrorContext(error, context);
  safeError('Error occurred:', errorContext);
  return errorContext;
}

/**
 * Handle warnings with context
 */
export function handleWarning(message: string, context?: Partial<ErrorContext>): ErrorContext {
  const warningContext: ErrorContext = {
    type: 'warning',
    message,
    timestamp: new Date(),
    ...context
  };
  safeWarn('Warning:', warningContext);
  return warningContext;
}

export const errorHandler = {
  error: handleError,
  warn: handleWarning,
  safeWarn,
  safeError,
  toErrorContext
};

const errorHandlerDefault = {
  safeLog,
  safeWarn,
  safeError,
  toErrorContext,
  handleError,
  handleWarning,
  errorHandler
};

export default errorHandlerDefault;