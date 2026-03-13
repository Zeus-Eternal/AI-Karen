/**
 * Environment utilities for production-ready frontend
 * Provides environment checks for logging, error messages, and development features
 */

/**
 * Check if the current environment is development
 */
export const isDevelopment = (): boolean => {
  return process.env.NODE_ENV === 'development';
};

/**
 * Check if the current environment is production
 */
export const isProduction = (): boolean => {
  return process.env.NODE_ENV === 'production';
};

/**
 * Check if debug logging is enabled
 */
export const isDebugLoggingEnabled = (): boolean => {
  return isDevelopment() || process.env.NEXT_PUBLIC_DEBUG_LOGGING === 'true';
};

/**
 * Conditional console logging that only logs in development or when debug is enabled
 */
export const debugLog = {
  log: (...args: any[]) => {
    if (isDebugLoggingEnabled()) {
      console.log(...args);
    }
  },
  warn: (...args: any[]) => {
    if (isDebugLoggingEnabled()) {
      console.warn(...args);
    }
  },
  error: (...args: any[]) => {
    // Always log errors, but with context in development
    if (isDevelopment()) {
      console.error('[DEV]', ...args);
    } else {
      console.error(...args);
    }
  },
  info: (...args: any[]) => {
    if (isDebugLoggingEnabled()) {
      console.info(...args);
    }
  },
  debug: (...args: any[]) => {
    if (isDebugLoggingEnabled()) {
      console.debug(...args);
    }
  }
};

/**
 * Sanitize error messages for production
 * Removes sensitive information and internal structure details
 */
export const sanitizeErrorMessage = (message: string): string => {
  if (isDevelopment()) {
    return message; // Return full message in development
  }

  // Remove file paths, stack traces, and internal structure
  const sanitized = message
    .replace(/\/[^\s]+/g, '[path]') // Replace file paths
    .replace(/at\s+.*\(\d+:\d+\)/g, '[location]') // Replace stack trace locations
    .replace(/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, '[IP]') // Replace IP addresses
    .replace(/\b[a-f0-9]{8,}-[a-f0-9]{4,}-[a-f0-9]{4,}-[a-f0-9]{4,}-[a-f0-9]{8,}\b/gi, '[ID]'); // Replace UUIDs

  return sanitized;
};

/**
 * Get a generic error message for production
 */
export const getGenericErrorMessage = (originalMessage: string): string => {
  if (isDevelopment()) {
    return originalMessage;
  }

  // Categorize errors and return appropriate generic messages
  if (originalMessage.includes('401') || originalMessage.includes('unauthorized')) {
    return 'Authentication failed. Please check your credentials and try again.';
  }

  if (originalMessage.includes('403') || originalMessage.includes('forbidden')) {
    return 'Access denied. You do not have permission to perform this action.';
  }

  if (originalMessage.includes('404') || originalMessage.includes('not found')) {
    return 'The requested resource was not found.';
  }

  if (originalMessage.includes('500') || originalMessage.includes('internal server')) {
    return 'An internal server error occurred. Please try again later.';
  }

  if (originalMessage.includes('network') || originalMessage.includes('connection')) {
    return 'Network error. Please check your connection and try again.';
  }

  if (originalMessage.includes('timeout')) {
    return 'Request timed out. Please try again.';
  }

  // Default generic message
  return 'An error occurred. Please try again or contact support if the problem persists.';
};

/**
 * Check if developer tools should be enabled
 */
export const shouldEnableDeveloperTools = (): boolean => {
  return isDevelopment() && process.env.NEXT_PUBLIC_ENABLE_DEVELOPER_TOOLS !== 'false';
};

/**
 * Get environment-appropriate error details
 */
export const getErrorDetails = (error: any): { message: string; details?: string } => {
  const originalMessage = typeof error === 'string' ? error : error?.message || 'Unknown error';
  
  if (isDevelopment()) {
    return {
      message: originalMessage,
      details: error?.stack || JSON.stringify(error, null, 2)
    };
  }

  return {
    message: getGenericErrorMessage(originalMessage)
  };
};