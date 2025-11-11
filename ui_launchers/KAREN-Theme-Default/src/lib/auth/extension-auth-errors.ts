/**
 * Extension Authentication Error Handling
 * 
 * Provides specific error types for authentication failures, graceful degradation,
 * user-friendly error messages, and recovery suggestions for extension authentication.
 * 
 * Requirements addressed:
 * - 3.1: Extension integration service error handling
 * - 3.2: Extension API calls with proper authentication
 * - 3.3: Authentication failures and retry logic
 * - 9.1: Graceful degradation when authentication fails
 * - 9.2: Fallback behavior for extension unavailability
 */

import { logger } from '@/lib/logger';
import { ErrorInfo } from '@/lib/error-handler';

/**
 * Extension authentication error categories
 */
export enum ExtensionAuthErrorCategory {
  TOKEN_EXPIRED = 'token_expired',
  TOKEN_INVALID = 'token_invalid',
  TOKEN_MISSING = 'token_missing',
  REFRESH_FAILED = 'refresh_failed',
  PERMISSION_DENIED = 'permission_denied',
  SERVICE_UNAVAILABLE = 'service_unavailable',
  NETWORK_ERROR = 'network_error',
  CONFIGURATION_ERROR = 'configuration_error',
  RATE_LIMITED = 'rate_limited',
  DEVELOPMENT_MODE = 'development_mode'
}

/**
 * Extension authentication error severity levels
 */
export enum ExtensionAuthErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

/**
 * Extension authentication error recovery strategies
 */
export enum ExtensionAuthRecoveryStrategy {
  RETRY_WITH_REFRESH = 'retry_with_refresh',
  RETRY_WITH_BACKOFF = 'retry_with_backoff',
  FALLBACK_TO_READONLY = 'fallback_to_readonly',
  FALLBACK_TO_CACHED = 'fallback_to_cached',
  REDIRECT_TO_LOGIN = 'redirect_to_login',
  SHOW_ERROR_MESSAGE = 'show_error_message',
  GRACEFUL_DEGRADATION = 'graceful_degradation',
  NO_RECOVERY = 'no_recovery'
}

/**
 * Extension authentication error interface
 */
export interface ExtensionAuthError {
  category: ExtensionAuthErrorCategory;
  severity: ExtensionAuthErrorSeverity;
  code: string;
  title: string;
  message: string;
  technicalDetails?: string;
  recoveryStrategy: ExtensionAuthRecoveryStrategy;
  retryable: boolean;
  userActionRequired: boolean;
  resolutionSteps: string[];
  context?: Record<string, unknown>;
  timestamp: Date;
}

/**
 * Extension authentication error factory
 */
export class ExtensionAuthErrorFactory {
  /**
   * Create token expired error
   */
  static createTokenExpiredError(context?: Record<string, unknown>): ExtensionAuthError {
    return {
      category: ExtensionAuthErrorCategory.TOKEN_EXPIRED,
      severity: ExtensionAuthErrorSeverity.MEDIUM,
      code: 'EXT_AUTH_TOKEN_EXPIRED',
      title: 'Authentication Token Expired',
      message: 'Your authentication token has expired. The system will attempt to refresh it automatically.',
      technicalDetails: 'JWT token has exceeded its expiration time',
      recoveryStrategy: ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH,
      retryable: true,
      userActionRequired: false,
      resolutionSteps: [
        'The system will automatically refresh your authentication token',
        'If automatic refresh fails, you may need to log in again',
        'Check your internet connection if the problem persists'
      ],
      context,
      timestamp: new Date()
    };
  }

  /**
   * Create token invalid error
   */
  static createTokenInvalidError(context?: Record<string, unknown>): ExtensionAuthError {
    return {
      category: ExtensionAuthErrorCategory.TOKEN_INVALID,
      severity: ExtensionAuthErrorSeverity.HIGH,
      code: 'EXT_AUTH_TOKEN_INVALID',
      title: 'Invalid Authentication Token',
      message: 'Your authentication token is invalid. Please log in again to continue using extensions.',
      technicalDetails: 'JWT token signature validation failed or token is malformed',
      recoveryStrategy: ExtensionAuthRecoveryStrategy.REDIRECT_TO_LOGIN,
      retryable: false,
      userActionRequired: true,
      resolutionSteps: [
        'Click the "Log In" button to authenticate again',
        'Clear your browser cache if the problem persists',
        'Contact support if you continue to experience issues'
      ],
      context,
      timestamp: new Date()
    };
  }

  /**
   * Create token missing error
   */
  static createTokenMissingError(context?: Record<string, unknown>): ExtensionAuthError {
    return {
      category: ExtensionAuthErrorCategory.TOKEN_MISSING,
      severity: ExtensionAuthErrorSeverity.HIGH,
      code: 'EXT_AUTH_TOKEN_MISSING',
      title: 'Authentication Required',
      message: 'You need to be logged in to use extension features. Please log in to continue.',
      technicalDetails: 'No authentication token found in storage',
      recoveryStrategy: ExtensionAuthRecoveryStrategy.REDIRECT_TO_LOGIN,
      retryable: false,
      userActionRequired: true,
      resolutionSteps: [
        'Click the "Log In" button to authenticate',
        'Make sure cookies are enabled in your browser',
        'Try refreshing the page if the login button is not visible'
      ],
      context,
      timestamp: new Date()
    };
  }

  /**
   * Create refresh failed error
   */
  static createRefreshFailedError(context?: Record<string, unknown>): ExtensionAuthError {
    return {
      category: ExtensionAuthErrorCategory.REFRESH_FAILED,
      severity: ExtensionAuthErrorSeverity.HIGH,
      code: 'EXT_AUTH_REFRESH_FAILED',
      title: 'Token Refresh Failed',
      message: 'Unable to refresh your authentication token. Please log in again to continue.',
      technicalDetails: 'Token refresh request failed or returned invalid response',
      recoveryStrategy: ExtensionAuthRecoveryStrategy.REDIRECT_TO_LOGIN,
      retryable: false,
      userActionRequired: true,
      resolutionSteps: [
        'Log out and log back in to get a fresh authentication token',
        'Check your internet connection',
        'Clear browser cookies and try again',
        'Contact support if the problem persists'
      ],
      context,
      timestamp: new Date()
    };
  }

  /**
   * Create permission denied error
   */
  static createPermissionDeniedError(context?: Record<string, unknown>): ExtensionAuthError {
    return {
      category: ExtensionAuthErrorCategory.PERMISSION_DENIED,
      severity: ExtensionAuthErrorSeverity.HIGH,
      code: 'EXT_AUTH_PERMISSION_DENIED',
      title: 'Permission Denied',
      message: 'You do not have permission to access this extension feature. Contact your administrator for access.',
      technicalDetails: 'User lacks required permissions for the requested extension operation',
      recoveryStrategy: ExtensionAuthRecoveryStrategy.FALLBACK_TO_READONLY,
      retryable: false,
      userActionRequired: true,
      resolutionSteps: [
        'Contact your system administrator to request access',
        'Check if you have the correct user role assigned',
        'Try logging out and back in to refresh your permissions',
        'Some features may be available in read-only mode'
      ],
      context,
      timestamp: new Date()
    };
  }

  /**
   * Create service unavailable error
   */
  static createServiceUnavailableError(context?: Record<string, unknown>): ExtensionAuthError {
    return {
      category: ExtensionAuthErrorCategory.SERVICE_UNAVAILABLE,
      severity: ExtensionAuthErrorSeverity.MEDIUM,
      code: 'EXT_AUTH_SERVICE_UNAVAILABLE',
      title: 'Extension Service Unavailable',
      message: 'The extension authentication service is temporarily unavailable. Some features may be limited.',
      technicalDetails: 'Extension authentication service returned 503 or is not responding',
      recoveryStrategy: ExtensionAuthRecoveryStrategy.GRACEFUL_DEGRADATION,
      retryable: true,
      userActionRequired: false,
      resolutionSteps: [
        'The system will retry automatically in a few moments',
        'Some extension features may be temporarily unavailable',
        'Core platform features will continue to work normally',
        'Contact support if the service remains unavailable'
      ],
      context,
      timestamp: new Date()
    };
  }

  /**
   * Create network error
   */
  static createNetworkError(context?: Record<string, unknown>): ExtensionAuthError {
    return {
      category: ExtensionAuthErrorCategory.NETWORK_ERROR,
      severity: ExtensionAuthErrorSeverity.MEDIUM,
      code: 'EXT_AUTH_NETWORK_ERROR',
      title: 'Network Connection Error',
      message: 'Unable to connect to the extension authentication service. Check your internet connection.',
      technicalDetails: 'Network request failed due to connectivity issues',
      recoveryStrategy: ExtensionAuthRecoveryStrategy.RETRY_WITH_BACKOFF,
      retryable: true,
      userActionRequired: false,
      resolutionSteps: [
        'Check your internet connection',
        'The system will retry automatically',
        'Try refreshing the page if the problem persists',
        'Contact your network administrator if you\'re on a corporate network'
      ],
      context,
      timestamp: new Date()
    };
  }

  /**
   * Create configuration error
   */
  static createConfigurationError(context?: Record<string, unknown>): ExtensionAuthError {
    return {
      category: ExtensionAuthErrorCategory.CONFIGURATION_ERROR,
      severity: ExtensionAuthErrorSeverity.CRITICAL,
      code: 'EXT_AUTH_CONFIG_ERROR',
      title: 'Authentication Configuration Error',
      message: 'There is a configuration issue with the extension authentication system. Contact support.',
      technicalDetails: 'Authentication configuration is missing or invalid',
      recoveryStrategy: ExtensionAuthRecoveryStrategy.NO_RECOVERY,
      retryable: false,
      userActionRequired: true,
      resolutionSteps: [
        'Contact your system administrator immediately',
        'This is a system configuration issue that requires technical support',
        'Core platform features may still be available',
        'Do not attempt to fix this yourself'
      ],
      context,
      timestamp: new Date()
    };
  }

  /**
   * Create rate limited error
   */
  static createRateLimitedError(context?: Record<string, unknown>): ExtensionAuthError {
    return {
      category: ExtensionAuthErrorCategory.RATE_LIMITED,
      severity: ExtensionAuthErrorSeverity.MEDIUM,
      code: 'EXT_AUTH_RATE_LIMITED',
      title: 'Too Many Authentication Attempts',
      message: 'You have made too many authentication attempts. Please wait before trying again.',
      technicalDetails: 'Authentication rate limit exceeded',
      recoveryStrategy: ExtensionAuthRecoveryStrategy.RETRY_WITH_BACKOFF,
      retryable: true,
      userActionRequired: false,
      resolutionSteps: [
        'Wait a few minutes before trying again',
        'The system will automatically retry when the rate limit resets',
        'Avoid making rapid repeated requests',
        'Contact support if you believe this is an error'
      ],
      context,
      timestamp: new Date()
    };
  }

  /**
   * Create development mode error
   */
  static createDevelopmentModeError(context?: Record<string, unknown>): ExtensionAuthError {
    return {
      category: ExtensionAuthErrorCategory.DEVELOPMENT_MODE,
      severity: ExtensionAuthErrorSeverity.LOW,
      code: 'EXT_AUTH_DEV_MODE',
      title: 'Development Mode Authentication',
      message: 'Running in development mode with simplified authentication. Some security features are disabled.',
      technicalDetails: 'Development mode authentication bypass is active',
      recoveryStrategy: ExtensionAuthRecoveryStrategy.GRACEFUL_DEGRADATION,
      retryable: false,
      userActionRequired: false,
      resolutionSteps: [
        'This is normal in development environments',
        'Full authentication will be required in production',
        'Some features may behave differently in development mode',
        'Switch to production mode for full security'
      ],
      context,
      timestamp: new Date()
    };
  }

  /**
   * Create error from HTTP status code
   */
  static createFromHttpStatus(
    status: number, 
    message?: string, 
    context?: Record<string, unknown>
  ): ExtensionAuthError {
    switch (status) {
      case 401:
        return this.createTokenExpiredError(context);
      case 403:
        return this.createPermissionDeniedError(context);
      case 429:
        return this.createRateLimitedError(context);
      case 503:
        return this.createServiceUnavailableError(context);
      default:
        return this.createNetworkError({
          ...context,
          httpStatus: status,
          httpMessage: message
        });

    }
  }

  /**
   * Create error from exception
   */
  static createFromException(
    error: Error, 
    context?: Record<string, unknown>
  ): ExtensionAuthError {
    const errorMessage = error.message.toLowerCase();

    if (errorMessage.includes('token') && errorMessage.includes('expired')) {
      return this.createTokenExpiredError(context);
    }

    if (errorMessage.includes('token') && errorMessage.includes('invalid')) {
      return this.createTokenInvalidError(context);
    }

    if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
      return this.createNetworkError(context);
    }

    if (errorMessage.includes('timeout')) {
      return this.createNetworkError({
        ...context,
        errorType: 'timeout'
      });
    }

    if (errorMessage.includes('permission') || errorMessage.includes('forbidden')) {
      return this.createPermissionDeniedError(context);
    }

    if (errorMessage.includes('service') && errorMessage.includes('unavailable')) {
      return this.createServiceUnavailableError(context);
    }

    if (errorMessage.includes('config')) {
      return this.createConfigurationError(context);
    }

    // Default to network error for unknown exceptions
    return this.createNetworkError({
      ...context,
      originalError: error.message,
      errorName: error.name
    });
  }
}

/**
 * Extension authentication error handler
 */
export class ExtensionAuthErrorHandler {
  private static instance: ExtensionAuthErrorHandler;
  private errorHistory: ExtensionAuthError[] = [];
  private readonly MAX_ERROR_HISTORY = 50;

  static getInstance(): ExtensionAuthErrorHandler {
    if (!ExtensionAuthErrorHandler.instance) {
      ExtensionAuthErrorHandler.instance = new ExtensionAuthErrorHandler();
    }
    return ExtensionAuthErrorHandler.instance;
  }

  /**
   * Handle extension authentication error
   */
  handleError(error: ExtensionAuthError): ErrorInfo {
    // Add to error history
    this.addToHistory(error);

    // Log the error
    this.logError(error);

    // Convert to ErrorInfo format for compatibility with existing error handler
    const errorInfo: ErrorInfo = {
      category: error.category,
      severity: error.severity,
      title: error.title,
      message: error.message,
      technical_details: error.technicalDetails,
      resolution_steps: error.resolutionSteps,
      retry_possible: error.retryable,
      user_action_required: error.userActionRequired,
      error_code: error.code,
      context: {
        ...error.context,
        timestamp: error.timestamp.toISOString(),
        recoveryStrategy: error.recoveryStrategy
      }
    };

    return errorInfo;
  }

  /**
   * Get recovery strategy for error
   */
  getRecoveryStrategy(error: ExtensionAuthError): ExtensionAuthRecoveryStrategy {
    return error.recoveryStrategy;
  }

  /**
   * Check if error is retryable
   */
  isRetryable(error: ExtensionAuthError): boolean {
    return error.retryable;
  }

  /**
   * Check if user action is required
   */
  requiresUserAction(error: ExtensionAuthError): boolean {
    return error.userActionRequired;
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(error: ExtensionAuthError): string {
    return error.message;
  }

  /**
   * Get resolution steps as formatted text
   */
  getResolutionStepsText(error: ExtensionAuthError): string {
    return error.resolutionSteps
      .map((step, index) => `${index + 1}. ${step}`)
      .join('\n');
  }

  /**
   * Get error history
   */
  getErrorHistory(): ExtensionAuthError[] {
    return [...this.errorHistory];
  }

  /**
   * Clear error history
   */
  clearErrorHistory(): void {
    this.errorHistory = [];
  }

  /**
   * Get error statistics
   */
  getErrorStatistics(): Record<string, number> {
    const stats: Record<string, number> = {};
    
    for (const error of this.errorHistory) {
      const key = error.category;
      stats[key] = (stats[key] || 0) + 1;
    }

    return stats;
  }

  /**
   * Check if error pattern indicates systemic issue
   */
  detectSystemicIssue(): boolean {
    if (this.errorHistory.length < 5) return false;

    const recentErrors = this.errorHistory.slice(-5);
    const now = Date.now();
    const fiveMinutesAgo = now - (5 * 60 * 1000);

    // Check if we have 5 errors in the last 5 minutes
    const recentErrorCount = recentErrors.filter(
      error => error.timestamp.getTime() > fiveMinutesAgo
    ).length;

    return recentErrorCount >= 5;
  }

  /**
   * Add error to history
   */
  private addToHistory(error: ExtensionAuthError): void {
    this.errorHistory.push(error);

    // Maintain history size limit
    if (this.errorHistory.length > this.MAX_ERROR_HISTORY) {
      this.errorHistory = this.errorHistory.slice(-this.MAX_ERROR_HISTORY);
    }
  }

  /**
   * Log error with appropriate level
   */
  private logError(error: ExtensionAuthError): void {
    const logData = {
      code: error.code,
      category: error.category,
      severity: error.severity,
      message: error.message,
      context: error.context,
      timestamp: error.timestamp.toISOString()
    };

    switch (error.severity) {
      case ExtensionAuthErrorSeverity.CRITICAL:
        logger.error(`[EXT_AUTH_CRITICAL] ${error.title}:`, logData);
        break;
      case ExtensionAuthErrorSeverity.HIGH:
        logger.error(`[EXT_AUTH_HIGH] ${error.title}:`, logData);
        break;
      case ExtensionAuthErrorSeverity.MEDIUM:
        logger.warn(`[EXT_AUTH_MEDIUM] ${error.title}:`, logData);
        break;
      case ExtensionAuthErrorSeverity.LOW:
        logger.info(`[EXT_AUTH_LOW] ${error.title}:`, logData);
        break;
      default:
        logger.warn(`[EXT_AUTH] ${error.title}:`, logData);
    }
  }
}

// Export singleton instance
export const extensionAuthErrorHandler = ExtensionAuthErrorHandler.getInstance();

// Export convenience functions
export const handleExtensionAuthError = (error: ExtensionAuthError) => 
  extensionAuthErrorHandler.handleError(error);

export const createExtensionAuthError = ExtensionAuthErrorFactory;

export const getExtensionAuthRecoveryStrategy = (error: ExtensionAuthError) => 
  extensionAuthErrorHandler.getRecoveryStrategy(error);

export const isExtensionAuthErrorRetryable = (error: ExtensionAuthError) => 
  extensionAuthErrorHandler.isRetryable(error);
