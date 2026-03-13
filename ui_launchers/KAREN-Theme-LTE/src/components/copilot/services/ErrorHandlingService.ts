import { ExtensionError, ExtensionErrorCode } from '../types/extension';

/**
 * Error severity levels
 */
export enum ErrorSeverity {
  /** Low severity error that doesn't affect functionality */
  LOW = 'low',
  
  /** Medium severity error that partially affects functionality */
  MEDIUM = 'medium',
  
  /** High severity error that significantly affects functionality */
  HIGH = 'high',
  
  /** Critical error that causes complete failure */
  CRITICAL = 'critical'
}

/**
 * Error categories
 */
export enum ErrorCategory {
  /** Network related errors */
  NETWORK = 'network',
  
  /** API related errors */
  API = 'api',
  
  /** Authentication/authorization errors */
  AUTH = 'auth',
  
  /** Validation errors */
  VALIDATION = 'validation',
  
  /** Execution errors */
  EXECUTION = 'execution',
  
  /** Timeout errors */
  TIMEOUT = 'timeout',
  
  /** Configuration errors */
  CONFIGURATION = 'configuration',
  
  /** Extension errors */
  EXTENSION = 'extension',
  
  /** UI errors */
  UI = 'ui',
  
  /** User input errors */
  USER_INPUT = 'user_input',
  
  /** Hardware errors */
  HARDWARE = 'hardware',
  
  /** Permission errors */
  PERMISSION = 'permission',
  
  /** Unknown errors */
  UNKNOWN = 'unknown'
}

/**
 * Error context information
 */
export interface ErrorContext {
  /** Component where the error occurred */
  component?: string;
  
  /** Function where the error occurred */
  function?: string;
  
  /** User ID if available */
  userId?: string;
  
  /** Session ID if available */
  sessionId?: string;
  
  /** Additional data */
  [key: string]: any;
}

/**
 * Enhanced error information
 */
export interface ErrorInfo {
  /** Unique error ID */
  id: string;
  
  /** Error timestamp */
  timestamp: Date;
  
  /** Error severity */
  severity: ErrorSeverity;
  
  /** Error category */
  category: ErrorCategory;
  
  /** Error code */
  code: string;
  
  /** User-friendly error message */
  message: string;
  
  /** Technical error details */
  details?: any;
  
  /** Stack trace if available */
  stack?: string;
  
  /** Error context */
  context?: ErrorContext;
  
  /** Whether the error has been resolved */
  resolved: boolean;
  
  /** Number of times this error has occurred */
  count: number;
  
  /** First occurrence timestamp */
  firstOccurrence: Date;
  
  /** Last occurrence timestamp */
  lastOccurrence: Date;
}

/**
 * Error recovery options
 */
export interface ErrorRecoveryOptions {
  /** Whether to automatically retry the operation */
  autoRetry?: boolean;
  
  /** Maximum number of retry attempts */
  maxRetries?: number;
  
  /** Delay between retries in milliseconds */
  retryDelay?: number;
  
  /** Whether to use exponential backoff for retries */
  exponentialBackoff?: boolean;
  
  /** Callback function to execute on retry */
  onRetry?: (error: ErrorInfo, attempt: number) => void;
  
  /** Callback function to execute when all retries fail */
  onRetryFailed?: (error: ErrorInfo) => void;
  
  /** Alternative function to execute if the main function fails */
  fallback?: () => Promise<any> | any;
}

/**
 * Error notification options
 */
export interface ErrorNotificationOptions {
  /** Whether to show a notification to the user */
  showNotification?: boolean;
  
  /** Notification type */
  notificationType?: 'toast' | 'modal' | 'inline';
  
  /** Notification duration in milliseconds */
  notificationDuration?: number;
  
  /** Whether to allow the user to dismiss the notification */
  dismissible?: boolean;
  
  /** Custom notification message */
  message?: string;
  
  /** Custom notification title */
  title?: string;
}

/**
 * Error logging options
 */
export interface ErrorLoggingOptions {
  /** Whether to log the error */
  logError?: boolean;
  
  /** Log level */
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
  
  /** Additional data to log */
  additionalData?: any;
  
  /** Whether to send error to analytics */
  sendToAnalytics?: boolean;
  
  /** Whether to send error to external monitoring service */
  sendToMonitoring?: boolean;
}

/**
 * Centralized error handling service for CoPilot Architecture
 */
class ErrorHandlingService {
  private static instance: ErrorHandlingService;
  private errors: Map<string, ErrorInfo> = new Map();
  private errorListeners: Map<string, Function[]> = new Map();
  private errorStats: Map<string, number> = new Map();
  
  private constructor() {
    // Initialize with empty state
  }
  
  public static getInstance(): ErrorHandlingService {
    if (!ErrorHandlingService.instance) {
      ErrorHandlingService.instance = new ErrorHandlingService();
    }
    return ErrorHandlingService.instance;
  }
  
  /**
   * Handle an error
   */
  public handleError(
    error: Error | ExtensionError | any,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context?: ErrorContext,
    recoveryOptions?: ErrorRecoveryOptions,
    notificationOptions?: ErrorNotificationOptions,
    loggingOptions?: ErrorLoggingOptions
  ): string {
    // Generate error ID
    const errorId = this.generateErrorId();
    
    // Extract error information
    const errorCode = this.extractErrorCode(error);
    const errorMessage = this.extractErrorMessage(error);
    const errorStack = this.extractErrorStack(error);
    
    // Create error info
    const errorInfo: ErrorInfo = {
      id: errorId,
      timestamp: new Date(),
      severity,
      category,
      code: errorCode,
      message: errorMessage,
      details: error,
      stack: errorStack,
      context,
      resolved: false,
      count: 1,
      firstOccurrence: new Date(),
      lastOccurrence: new Date()
    };
    
    // Check if this error has occurred before
    const existingError = this.findSimilarError(errorInfo);
    if (existingError) {
      // Update existing error
      existingError.count++;
      existingError.lastOccurrence = new Date();
      this.errors.set(existingError.id, existingError);
      
      // Update error stats
      this.updateErrorStats(category);
      
      // Log the error
      if (loggingOptions?.logError !== false) {
        this.logError(existingError, loggingOptions);
      }
      
      // Show notification if enabled
      if (notificationOptions?.showNotification) {
        this.showErrorNotification(existingError, notificationOptions);
      }
      
      // Emit error event
      this.emitErrorEvent('error_occurred', { errorInfo: existingError });
      
      return existingError.id;
    }
    
    // Store the error
    this.errors.set(errorId, errorInfo);
    
    // Update error stats
    this.updateErrorStats(category);
    
    // Log the error
    if (loggingOptions?.logError !== false) {
      this.logError(errorInfo, loggingOptions);
    }
    
    // Show notification if enabled
    if (notificationOptions?.showNotification) {
      this.showErrorNotification(errorInfo, notificationOptions);
    }
    
    // Attempt recovery if options are provided
    if (recoveryOptions?.autoRetry) {
      this.attemptRecovery(errorInfo, recoveryOptions);
    }
    
    // Emit error event
    this.emitErrorEvent('error_occurred', { errorInfo });
    
    return errorId;
  }
  
  /**
   * Get error by ID
   */
  public getError(errorId: string): ErrorInfo | undefined {
    return this.errors.get(errorId);
  }
  
  /**
   * Get all errors
   */
  public getAllErrors(includeResolved: boolean = false): ErrorInfo[] {
    const errors = Array.from(this.errors.values());
    
    if (!includeResolved) {
      return errors.filter(error => !error.resolved);
    }
    
    return errors;
  }
  
  /**
   * Get errors by category
   */
  public getErrorsByCategory(category: ErrorCategory, includeResolved: boolean = false): ErrorInfo[] {
    const errors = Array.from(this.errors.values());
    
    return errors.filter(error => 
      error.category === category && (includeResolved || !error.resolved)
    );
  }
  
  /**
   * Get errors by severity
   */
  public getErrorsBySeverity(severity: ErrorSeverity, includeResolved: boolean = false): ErrorInfo[] {
    const errors = Array.from(this.errors.values());
    
    return errors.filter(error => 
      error.severity === severity && (includeResolved || !error.resolved)
    );
  }
  
  /**
   * Resolve an error
   */
  public resolveError(errorId: string): boolean {
    const error = this.errors.get(errorId);
    
    if (!error) {
      return false;
    }
    
    error.resolved = true;
    this.errors.set(errorId, error);
    
    // Emit error resolved event
    this.emitErrorEvent('error_resolved', { errorInfo: error });
    
    return true;
  }
  
  /**
   * Add error event listener
   */
  public addErrorEventListener(eventType: string, listener: (event: any) => void): void {
    if (!this.errorListeners.has(eventType)) {
      this.errorListeners.set(eventType, []);
    }
    this.errorListeners.get(eventType)?.push(listener);
  }
  
  /**
   * Remove error event listener
   */
  public removeErrorEventListener(eventType: string, listener: (event: any) => void): void {
    const listeners = this.errorListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }
  
  /**
   * Get error statistics
   */
  public getErrorStatistics(): {
    totalErrors: number;
    resolvedErrors: number;
    unresolvedErrors: number;
    errorsByCategory: Record<ErrorCategory, number>;
    errorsBySeverity: Record<ErrorSeverity, number>;
    mostCommonErrors: ErrorInfo[];
  } {
    const errors = Array.from(this.errors.values());
    
    const stats = {
      totalErrors: errors.length,
      resolvedErrors: errors.filter(error => error.resolved).length,
      unresolvedErrors: errors.filter(error => !error.resolved).length,
      errorsByCategory: {} as Record<ErrorCategory, number>,
      errorsBySeverity: {} as Record<ErrorSeverity, number>,
      mostCommonErrors: errors
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
    };
    
    // Initialize category and severity counts
    Object.values(ErrorCategory).forEach(category => {
      stats.errorsByCategory[category] = 0;
    });
    
    Object.values(ErrorSeverity).forEach(severity => {
      stats.errorsBySeverity[severity] = 0;
    });
    
    // Count errors by category and severity
    errors.forEach(error => {
      stats.errorsByCategory[error.category]++;
      stats.errorsBySeverity[error.severity]++;
    });
    
    return stats;
  }
  
  /**
   * Clear all errors
   */
  public clearAllErrors(): void {
    this.errors.clear();
    this.errorStats.clear();
    
    // Emit errors cleared event
    this.emitErrorEvent('errors_cleared', {});
  }
  
  /**
   * Execute a function with error handling
   */
  public async executeWithErrorHandling<T>(
    fn: () => Promise<T>,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context?: ErrorContext,
    recoveryOptions?: ErrorRecoveryOptions,
    notificationOptions?: ErrorNotificationOptions,
    loggingOptions?: ErrorLoggingOptions
  ): Promise<T> {
    try {
      return await fn();
    } catch (error) {
      this.handleError(
        error,
        category,
        severity,
        context,
        recoveryOptions,
        notificationOptions,
        loggingOptions
      );
      throw error; // Re-throw the error after handling it
    }
  }
  
  /**
   * Execute a function with retry logic
   */
  public async executeWithRetry<T>(
    fn: () => Promise<T>,
    options: ErrorRecoveryOptions = {}
  ): Promise<T> {
    const {
      maxRetries = 3,
      retryDelay = 1000,
      exponentialBackoff = true,
      onRetry,
      onRetryFailed,
      fallback
    } = options;
    
    let lastError: Error | null = null;
    
    for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        if (attempt <= maxRetries) {
          // Calculate delay with exponential backoff if enabled
          const delay = exponentialBackoff
            ? retryDelay * Math.pow(2, attempt - 1)
            : retryDelay;
          
          // Call onRetry callback if provided
          if (onRetry) {
            const errorId = this.handleError(
              error,
              ErrorCategory.UNKNOWN,
              ErrorSeverity.MEDIUM,
              undefined,
              { autoRetry: false }
            );
            const errorInfo = this.getError(errorId);
            if (errorInfo) {
              onRetry(errorInfo, attempt);
            }
          }
          
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    // All retries failed
    if (onRetryFailed && lastError) {
      const errorId = this.handleError(
        lastError,
        ErrorCategory.UNKNOWN,
        ErrorSeverity.HIGH,
        undefined,
        { autoRetry: false }
      );
      const errorInfo = this.getError(errorId);
      if (errorInfo) {
        onRetryFailed(errorInfo);
      }
    }
    
    // Try fallback if provided
    if (fallback) {
      try {
        return await fallback();
      } catch (fallbackError) {
        this.handleError(
          fallbackError,
          ErrorCategory.UNKNOWN,
          ErrorSeverity.HIGH,
          undefined,
          { autoRetry: false }
        );
      }
    }
    
    if (lastError) {
      throw lastError;
    } else {
      throw new Error('Unknown error occurred during retry');
    }
  }
  
  /**
   * Generate a unique error ID
   */
  private generateErrorId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  /**
   * Extract error code from error
   */
  private extractErrorCode(error: Error | ExtensionError | any): string {
    if (error && typeof error === 'object' && 'code' in error) {
      return String(error.code);
    }
    
    if (error instanceof Error) {
      return error.name;
    }
    
    return 'unknown_error';
  }
  
  /**
   * Extract error message from error
   */
  private extractErrorMessage(error: Error | ExtensionError | any): string {
    if (error && typeof error === 'object' && 'message' in error) {
      return String(error.message);
    }
    
    if (error instanceof Error) {
      return error.message;
    }
    
    return String(error);
  }
  
  /**
   * Extract error stack from error
   */
  private extractErrorStack(error: Error | ExtensionError | any): string | undefined {
    if (error instanceof Error) {
      return error.stack;
    }
    
    if (error && typeof error === 'object' && 'stack' in error) {
      return String(error.stack);
    }
    
    return undefined;
  }
  
  /**
   * Find a similar error in the errors map
   */
  private findSimilarError(errorInfo: ErrorInfo): ErrorInfo | undefined {
    for (const [_, existingError] of this.errors) {
      if (
        existingError.code === errorInfo.code &&
        existingError.category === errorInfo.category &&
        existingError.message === errorInfo.message &&
        !existingError.resolved
      ) {
        return existingError;
      }
    }
    
    return undefined;
  }
  
  /**
   * Update error statistics
   */
  private updateErrorStats(category: ErrorCategory): void {
    const count = this.errorStats.get(category) || 0;
    this.errorStats.set(category, count + 1);
  }
  
  /**
   * Log an error
   */
  private logError(errorInfo: ErrorInfo, options?: ErrorLoggingOptions): void {
    const logLevel = options?.logLevel || 'error';
    const additionalData = options?.additionalData || {};
    
    const logMessage = `[${errorInfo.category.toUpperCase()}] ${errorInfo.message}`;
    const logData = {
      errorId: errorInfo.id,
      code: errorInfo.code,
      severity: errorInfo.severity,
      category: errorInfo.category,
      context: errorInfo.context,
      ...additionalData
    };
    
    switch (logLevel) {
      case 'debug':
        console.debug(logMessage, logData);
        break;
      case 'info':
        console.info(logMessage, logData);
        break;
      case 'warn':
        console.warn(logMessage, logData);
        break;
      case 'error':
      default:
        console.error(logMessage, logData);
        break;
    }
    
    // Send to analytics if enabled
    if (options?.sendToAnalytics) {
      this.sendToAnalytics(errorInfo);
    }
    
    // Send to monitoring if enabled
    if (options?.sendToMonitoring) {
      this.sendToMonitoring(errorInfo);
    }
  }
  
  /**
   * Show error notification
   */
  private showErrorNotification(errorInfo: ErrorInfo, options?: ErrorNotificationOptions): void {
    // This would typically integrate with a notification system
    // For now, we'll just log to the console
    const message = options?.message || errorInfo.message;
    const title = options?.title || 'Error';
    
    console.warn(`[NOTIFICATION] ${title}: ${message}`);
    
    // Emit notification event
    this.emitErrorEvent('error_notification', { 
      errorInfo, 
      notificationOptions: options 
    });
  }
  
  /**
   * Attempt error recovery
   */
  private async attemptRecovery(errorInfo: ErrorInfo, options: ErrorRecoveryOptions): Promise<void> {
    // This would typically implement retry logic
    // For now, we'll just emit a recovery event
    this.emitErrorEvent('error_recovery_attempt', { 
      errorInfo, 
      recoveryOptions: options 
    });
  }
  
  /**
   * Send error to analytics
   */
  private sendToAnalytics(errorInfo: ErrorInfo): void {
    // This would typically send error data to an analytics service
    console.debug(`[ANALYTICS] Error sent: ${errorInfo.id}`);
  }
  
  /**
   * Send error to monitoring
   */
  private sendToMonitoring(errorInfo: ErrorInfo): void {
    // This would typically send error data to a monitoring service
    console.debug(`[MONITORING] Error sent: ${errorInfo.id}`);
  }
  
  /**
   * Emit error event
   */
  private emitErrorEvent(eventType: string, data: any): void {
    const listeners = this.errorListeners.get(eventType);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener({
            type: eventType,
            timestamp: new Date(),
            ...data
          });
        } catch (error) {
          console.error(`Error in error event listener for ${eventType}:`, error);
        }
      });
    }
  }
}

export default ErrorHandlingService;