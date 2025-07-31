/**
 * Connection Error Handler
 * Provides user-friendly error messages and troubleshooting information for API errors
 */

import type { ApiError } from './api-client';

export interface ErrorInfo {
  title: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
  isRetryable: boolean;
  troubleshooting: {
    possibleCauses: string[];
    suggestedFixes: string[];
    technicalDetails?: string;
  };
  userActions: {
    primary?: {
      label: string;
      action: () => void;
    };
    secondary?: {
      label: string;
      action: () => void;
    };
  };
}

export interface ConnectionDiagnostics {
  endpoint: string;
  timestamp: string;
  networkStatus: 'online' | 'offline' | 'unknown';
  connectionType: string;
  responseTime?: number;
  httpStatus?: number;
  errorType: 'network' | 'cors' | 'timeout' | 'server' | 'client' | 'unknown';
  details: Record<string, any>;
}

/**
 * Service for handling and categorizing API errors
 */
export class ErrorHandler {
  /**
   * Convert API error to user-friendly error information
   */
  public static handleApiError(error: ApiError, context?: string): ErrorInfo {
    // Network errors
    if (error.isNetworkError) {
      return this.handleNetworkError(error, context);
    }

    // CORS errors
    if (error.isCorsError) {
      return this.handleCorsError(error, context);
    }

    // Timeout errors
    if (error.isTimeoutError) {
      return this.handleTimeoutError(error, context);
    }

    // HTTP status errors
    if (error.status) {
      return this.handleHttpStatusError(error, context);
    }

    // Unknown errors
    return this.handleUnknownError(error, context);
  }

  /**
   * Handle network connectivity errors
   */
  private static handleNetworkError(error: ApiError, context?: string): ErrorInfo {
    return {
      title: 'Connection Failed',
      message: 'Unable to connect to the server. Please check your internet connection and try again.',
      severity: 'error',
      isRetryable: true,
      troubleshooting: {
        possibleCauses: [
          'No internet connection',
          'Server is temporarily unavailable',
          'Firewall or proxy blocking the connection',
          'DNS resolution issues',
          'Backend server is not running',
        ],
        suggestedFixes: [
          'Check your internet connection',
          'Try refreshing the page',
          'Wait a moment and try again',
          'Check if other websites are working',
          'Contact your network administrator if on a corporate network',
        ],
        technicalDetails: `Network error on ${error.endpoint}: ${error.message}`,
      },
      userActions: {
        primary: {
          label: 'Retry',
          action: () => window.location.reload(),
        },
        secondary: {
          label: 'Check Connection',
          action: () => this.openNetworkDiagnostics(),
        },
      },
    };
  }

  /**
   * Handle CORS (Cross-Origin Resource Sharing) errors
   */
  private static handleCorsError(error: ApiError, context?: string): ErrorInfo {
    return {
      title: 'Access Blocked',
      message: 'The browser blocked the request due to security restrictions. This usually indicates a configuration issue.',
      severity: 'error',
      isRetryable: false,
      troubleshooting: {
        possibleCauses: [
          'Backend server CORS configuration is incorrect',
          'Accessing from an unauthorized domain',
          'Mixed HTTP/HTTPS content issues',
          'Browser security settings blocking the request',
        ],
        suggestedFixes: [
          'Contact the system administrator',
          'Try accessing from the correct domain',
          'Clear browser cache and cookies',
          'Disable browser extensions temporarily',
          'Try a different browser',
        ],
        technicalDetails: `CORS error on ${error.endpoint}: ${error.message}`,
      },
      userActions: {
        primary: {
          label: 'Contact Support',
          action: () => this.openSupportDialog(),
        },
        secondary: {
          label: 'Clear Cache',
          action: () => this.clearBrowserCache(),
        },
      },
    };
  }

  /**
   * Handle request timeout errors
   */
  private static handleTimeoutError(error: ApiError, context?: string): ErrorInfo {
    return {
      title: 'Request Timed Out',
      message: 'The server took too long to respond. This might be due to a slow connection or server overload.',
      severity: 'warning',
      isRetryable: true,
      troubleshooting: {
        possibleCauses: [
          'Slow internet connection',
          'Server is overloaded or processing slowly',
          'Large request taking too long to process',
          'Network congestion',
        ],
        suggestedFixes: [
          'Wait a moment and try again',
          'Check your internet connection speed',
          'Try during off-peak hours',
          'Break large requests into smaller ones',
        ],
        technicalDetails: `Timeout after ${error.responseTime}ms on ${error.endpoint}`,
      },
      userActions: {
        primary: {
          label: 'Try Again',
          action: () => window.location.reload(),
        },
        secondary: {
          label: 'Check Speed',
          action: () => this.openSpeedTest(),
        },
      },
    };
  }

  /**
   * Handle HTTP status code errors
   */
  private static handleHttpStatusError(error: ApiError, context?: string): ErrorInfo {
    const status = error.status!;

    // Client errors (4xx)
    if (status >= 400 && status < 500) {
      return this.handleClientError(error, context);
    }

    // Server errors (5xx)
    if (status >= 500) {
      return this.handleServerError(error, context);
    }

    // Other status codes
    return this.handleUnknownError(error, context);
  }

  /**
   * Handle client errors (4xx status codes)
   */
  private static handleClientError(error: ApiError, context?: string): ErrorInfo {
    const status = error.status!;

    switch (status) {
      case 401:
        return {
          title: 'Authentication Required',
          message: 'You need to log in to access this feature.',
          severity: 'warning',
          isRetryable: false,
          troubleshooting: {
            possibleCauses: [
              'Session has expired',
              'Invalid or missing authentication credentials',
              'Account has been deactivated',
            ],
            suggestedFixes: [
              'Log in again',
              'Clear browser cookies and cache',
              'Contact support if account issues persist',
            ],
            technicalDetails: `HTTP 401 on ${error.endpoint}`,
          },
          userActions: {
            primary: {
              label: 'Log In',
              action: () => this.redirectToLogin(),
            },
          },
        };

      case 403:
        return {
          title: 'Access Denied',
          message: 'You don\'t have permission to access this resource.',
          severity: 'error',
          isRetryable: false,
          troubleshooting: {
            possibleCauses: [
              'Insufficient user permissions',
              'Account restrictions',
              'Resource access limitations',
            ],
            suggestedFixes: [
              'Contact your administrator for access',
              'Check if you\'re using the correct account',
              'Verify your account permissions',
            ],
            technicalDetails: `HTTP 403 on ${error.endpoint}`,
          },
          userActions: {
            primary: {
              label: 'Contact Admin',
              action: () => this.openSupportDialog(),
            },
          },
        };

      case 404:
        return {
          title: 'Not Found',
          message: 'The requested resource could not be found.',
          severity: 'error',
          isRetryable: false,
          troubleshooting: {
            possibleCauses: [
              'Resource has been moved or deleted',
              'Incorrect URL or endpoint',
              'Server configuration issues',
            ],
            suggestedFixes: [
              'Check the URL for typos',
              'Go back and try a different path',
              'Contact support if the issue persists',
            ],
            technicalDetails: `HTTP 404 on ${error.endpoint}`,
          },
          userActions: {
            primary: {
              label: 'Go Back',
              action: () => window.history.back(),
            },
          },
        };

      case 429:
        return {
          title: 'Too Many Requests',
          message: 'You\'ve made too many requests. Please wait a moment before trying again.',
          severity: 'warning',
          isRetryable: true,
          troubleshooting: {
            possibleCauses: [
              'Rate limiting is active',
              'Too many requests in a short time',
              'API quota exceeded',
            ],
            suggestedFixes: [
              'Wait a few minutes before trying again',
              'Reduce the frequency of requests',
              'Contact support for quota increases',
            ],
            technicalDetails: `HTTP 429 on ${error.endpoint}`,
          },
          userActions: {
            primary: {
              label: 'Wait and Retry',
              action: () => setTimeout(() => window.location.reload(), 60000),
            },
          },
        };

      default:
        return {
          title: 'Request Failed',
          message: `The request failed with status ${status}. ${error.statusText || ''}`,
          severity: 'error',
          isRetryable: false,
          troubleshooting: {
            possibleCauses: [
              'Invalid request format',
              'Missing required parameters',
              'Client-side validation errors',
            ],
            suggestedFixes: [
              'Check your input and try again',
              'Refresh the page and retry',
              'Contact support if the issue persists',
            ],
            technicalDetails: `HTTP ${status} on ${error.endpoint}: ${error.message}`,
          },
          userActions: {
            primary: {
              label: 'Try Again',
              action: () => window.location.reload(),
            },
          },
        };
    }
  }

  /**
   * Handle server errors (5xx status codes)
   */
  private static handleServerError(error: ApiError, context?: string): ErrorInfo {
    return {
      title: 'Server Error',
      message: 'The server encountered an error while processing your request. Please try again later.',
      severity: 'error',
      isRetryable: true,
      troubleshooting: {
        possibleCauses: [
          'Server is temporarily overloaded',
          'Database connection issues',
          'Internal server error',
          'Maintenance in progress',
        ],
        suggestedFixes: [
          'Wait a few minutes and try again',
          'Check the system status page',
          'Contact support if the issue persists',
          'Try again during off-peak hours',
        ],
        technicalDetails: `HTTP ${error.status} on ${error.endpoint}: ${error.message}`,
      },
      userActions: {
        primary: {
          label: 'Try Again Later',
          action: () => setTimeout(() => window.location.reload(), 30000),
        },
        secondary: {
          label: 'Check Status',
          action: () => this.openStatusPage(),
        },
      },
    };
  }

  /**
   * Handle unknown errors
   */
  private static handleUnknownError(error: ApiError, context?: string): ErrorInfo {
    return {
      title: 'Unexpected Error',
      message: 'An unexpected error occurred. Please try again or contact support if the issue persists.',
      severity: 'error',
      isRetryable: true,
      troubleshooting: {
        possibleCauses: [
          'Unexpected application error',
          'Browser compatibility issues',
          'Temporary system glitch',
        ],
        suggestedFixes: [
          'Refresh the page and try again',
          'Clear browser cache and cookies',
          'Try using a different browser',
          'Contact support with error details',
        ],
        technicalDetails: `Unknown error on ${error.endpoint}: ${error.message}`,
      },
      userActions: {
        primary: {
          label: 'Refresh Page',
          action: () => window.location.reload(),
        },
        secondary: {
          label: 'Report Issue',
          action: () => this.openSupportDialog(),
        },
      },
    };
  }

  /**
   * Generate connection diagnostics
   */
  public static generateDiagnostics(error: ApiError): ConnectionDiagnostics {
    const networkStatus = navigator.onLine ? 'online' : 'offline';
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
    
    let errorType: ConnectionDiagnostics['errorType'] = 'unknown';
    if (error.isNetworkError) errorType = 'network';
    else if (error.isCorsError) errorType = 'cors';
    else if (error.isTimeoutError) errorType = 'timeout';
    else if (error.status && error.status >= 500) errorType = 'server';
    else if (error.status && error.status >= 400) errorType = 'client';

    return {
      endpoint: error.endpoint || 'unknown',
      timestamp: new Date().toISOString(),
      networkStatus,
      connectionType: connection?.effectiveType || 'unknown',
      responseTime: error.responseTime,
      httpStatus: error.status,
      errorType,
      details: {
        userAgent: navigator.userAgent,
        language: navigator.language,
        cookieEnabled: navigator.cookieEnabled,
        onLine: navigator.onLine,
        connectionDownlink: connection?.downlink,
        connectionRtt: connection?.rtt,
        errorMessage: error.message,
        originalError: error.originalError?.message,
      },
    };
  }

  /**
   * Helper methods for user actions
   */
  private static openNetworkDiagnostics(): void {
    // Open network diagnostics or speed test
    window.open('https://fast.com', '_blank');
  }

  private static openSupportDialog(): void {
    // Open support dialog or contact form
    console.log('Opening support dialog...');
    // Implementation would depend on your support system
  }

  private static clearBrowserCache(): void {
    // Clear browser cache and reload
    if ('caches' in window) {
      caches.keys().then(names => {
        names.forEach(name => caches.delete(name));
      });
    }
    window.location.reload();
  }

  private static openSpeedTest(): void {
    window.open('https://speedtest.net', '_blank');
  }

  private static redirectToLogin(): void {
    window.location.href = '/login';
  }

  private static openStatusPage(): void {
    // Open system status page
    console.log('Opening status page...');
    // Implementation would depend on your status page
  }

  /**
   * Format error for logging
   */
  public static formatErrorForLogging(error: ApiError, context?: string): string {
    const diagnostics = this.generateDiagnostics(error);
    
    return JSON.stringify({
      timestamp: diagnostics.timestamp,
      context: context || 'unknown',
      endpoint: diagnostics.endpoint,
      errorType: diagnostics.errorType,
      httpStatus: diagnostics.httpStatus,
      responseTime: diagnostics.responseTime,
      networkStatus: diagnostics.networkStatus,
      message: error.message,
      userAgent: navigator.userAgent,
    }, null, 2);
  }

  /**
   * Check if error should trigger automatic retry
   */
  public static shouldAutoRetry(error: ApiError): boolean {
    // Auto-retry for network errors, timeouts, and 5xx server errors
    return error.isNetworkError || 
           error.isTimeoutError || 
           (error.status !== undefined && error.status >= 500);
  }

  /**
   * Get retry delay based on error type and attempt number
   */
  public static getRetryDelay(error: ApiError, attemptNumber: number): number {
    const baseDelay = 1000; // 1 second
    const maxDelay = 30000; // 30 seconds
    
    let multiplier = 1;
    
    if (error.isTimeoutError) {
      multiplier = 2; // Longer delays for timeouts
    } else if (error.status === 429) {
      multiplier = 5; // Much longer delays for rate limiting
    } else if (error.status && error.status >= 500) {
      multiplier = 1.5; // Moderate delays for server errors
    }
    
    const delay = Math.min(baseDelay * multiplier * Math.pow(2, attemptNumber - 1), maxDelay);
    return delay;
  }
}

// Export utility functions
export function handleApiError(error: ApiError, context?: string): ErrorInfo {
  return ErrorHandler.handleApiError(error, context);
}

export function generateDiagnostics(error: ApiError): ConnectionDiagnostics {
  return ErrorHandler.generateDiagnostics(error);
}

export function shouldAutoRetry(error: ApiError): boolean {
  return ErrorHandler.shouldAutoRetry(error);
}

export function getRetryDelay(error: ApiError, attemptNumber: number): number {
  return ErrorHandler.getRetryDelay(error, attemptNumber);
}

export function formatErrorForLogging(error: ApiError, context?: string): string {
  return ErrorHandler.formatErrorForLogging(error, context);
}