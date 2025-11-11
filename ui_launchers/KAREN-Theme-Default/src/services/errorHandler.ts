/**
 * Service Error Handler - Centralized error handling for all services
 * Provides consistent error handling, retry logic, and user-friendly error messages
 */
import { enhancedApiClient } from '@/lib/enhanced-api-client';

type ErrorRecord = Record<string, unknown> & {
  status?: number;
  isNetworkError?: boolean;
  isTimeoutError?: boolean;
  isCorsError?: boolean;
  endpoint?: string;
};

function normalizeError(error: unknown): ErrorRecord {
  if (typeof error === 'object' && error !== null) {
    return error as ErrorRecord;
  }
  return {};
}
export interface ServiceError extends Error {
  code: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  retryable: boolean;
  userMessage: string;
  technicalMessage: string;
  context?: Record<string, unknown>;
  timestamp: number;
}
export interface ErrorHandlerConfig {
  enableRetry: boolean;
  maxRetries: number;
  retryDelay: number;
  enableLogging: boolean;
  enableUserNotification: boolean;
  fallbackValues: Record<string, unknown>;
}
export interface RetryOptions {
  maxAttempts?: number;
  baseDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  retryCondition?: (error: Error, attempt: number) => boolean;
}
/**
 * Centralized error handler for all services
 */
export class ServiceErrorHandler {
  private config: ErrorHandlerConfig;
  private enhancedApiClient = enhancedApiClient;
  private errorLog: ServiceError[] = [];
  constructor(config?: Partial<ErrorHandlerConfig>) {
    this.config = {
      enableRetry: true,
      maxRetries: 3,
      retryDelay: 1000,
      enableLogging: true,
      enableUserNotification: true,
      fallbackValues: {},
      ...config,
    };
  }
  /**
   * Handle and transform errors into ServiceError format
   */
  public handleError(
    error: unknown,
    context: {
      service: string;
      method: string;
      endpoint?: string;
      userId?: string;
      sessionId?: string;
      additionalContext?: Record<string, unknown>;
    }
  ): ServiceError {
    const serviceError = this.transformError(error, context);
    if (this.config.enableLogging) {
      this.logError(serviceError);
    }
    return serviceError;
  }
  /**
   * Execute a function with automatic retry logic
   */
  public async withRetry<T>(
    fn: () => Promise<T>,
    context: {
      service: string;
      method: string;
      endpoint?: string;
    },
    options?: RetryOptions
  ): Promise<T> {
    const opts = {
      maxAttempts: options?.maxAttempts ?? this.config.maxRetries,
      baseDelay: options?.baseDelay ?? this.config.retryDelay,
      maxDelay: options?.maxDelay ?? 30000,
      backoffMultiplier: options?.backoffMultiplier ?? 2,
      retryCondition: options?.retryCondition ?? this.defaultRetryCondition,
    };
    let lastError: Error | null = null;
    let attempt = 0;
    while (attempt < opts.maxAttempts) {
      try {
        const result = await fn();
        // Log successful retry if this wasn't the first attempt
        if (attempt > 0 && this.config.enableLogging) {
          console.log(`ServiceErrorHandler: ${context.service}.${context.method} succeeded after ${attempt} retries`);
        }
        return result;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        attempt++;
        // Check if we should retry
        if (attempt >= opts.maxAttempts || !opts.retryCondition(lastError, attempt)) {
          break;
        }
        // Calculate delay with exponential backoff
        const delay = Math.min(
          opts.baseDelay * Math.pow(opts.backoffMultiplier, attempt - 1),
          opts.maxDelay
        );
        if (this.config.enableLogging) {
          console.log(`ServiceErrorHandler: ${context.service}.${context.method} failed (attempt ${attempt}), retrying in ${delay}ms`);
        }
        await this.sleep(delay);
      }
    }
    // All retries exhausted, handle the final error
    throw this.handleError(lastError!, context);
  }
  /**
   * Execute a function with fallback value on error
   */
  public async withFallback<T>(
    fn: () => Promise<T>,
    fallbackValue: T,
    context: {
      service: string;
      method: string;
      endpoint?: string;
    }
  ): Promise<T> {
    try {
      return await fn();
    } catch (error) {
      this.handleError(error, context);
      if (this.config.enableLogging) {
        console.log(`ServiceErrorHandler: ${context.service}.${context.method} failed, using fallback value`);
      }
      return fallbackValue;
    }
  }
  /**
   * Execute a function with both retry and fallback
   */
  public async withRetryAndFallback<T>(
    fn: () => Promise<T>,
    fallbackValue: T,
    context: {
      service: string;
      method: string;
      endpoint?: string;
    },
    retryOptions?: RetryOptions
  ): Promise<T> {
    try {
      return await this.withRetry(fn, context, retryOptions);
    } catch {
      if (this.config.enableLogging) {
        console.log(`ServiceErrorHandler: ${context.service}.${context.method} failed after retries, using fallback value`);
      }
      return fallbackValue;
    }
  }
  /**
   * Transform various error types into ServiceError
   */
  private transformError(error: unknown, context: Record<string, unknown>): ServiceError {
    let code = 'UNKNOWN_ERROR';
    let severity: 'low' | 'medium' | 'high' | 'critical' = 'medium';
    let retryable = false;
    let userMessage = 'An unexpected error occurred. Please try again.';
    const baseError = error instanceof Error ? error : undefined;
    let technicalMessage = baseError?.message || 'Unknown error';
    const record = normalizeError(error);

    // Handle API errors
    if (baseError?.name === 'ApiError' || baseError?.name === 'EnhancedApiError') {
      code = this.getApiErrorCode(record);
      severity = this.getApiErrorSeverity(record);
      retryable = this.isApiErrorRetryable(record);
      userMessage = this.getApiErrorUserMessage(record);
      technicalMessage = `${baseError.message} (${record.endpoint || 'unknown endpoint'})`;
    }
    // Handle network errors
    else if (record.isNetworkError || baseError?.message?.includes('fetch') || baseError?.message?.includes('Network')) {
      code = 'NETWORK_ERROR';
      severity = 'medium';
      retryable = true;
      userMessage = 'Network connection issue. Please check your internet connection and try again.';
    }
    // Handle timeout errors
    else if (record.isTimeoutError || baseError?.name === 'TimeoutError' || baseError?.message?.includes('timeout')) {
      code = 'TIMEOUT_ERROR';
      severity = 'medium';
      retryable = true;
      userMessage = 'Request timed out. Please try again.';
    }
    // Handle CORS errors
    else if (record.isCorsError || baseError?.message?.includes('CORS')) {
      code = 'CORS_ERROR';
      severity = 'high';
      retryable = false;
      userMessage = 'Configuration error. Please contact support.';
    }
    // Handle authentication errors
    else if (record.status === 401 || baseError?.message?.includes('unauthorized')) {
      code = 'AUTH_ERROR';
      severity = 'high';
      retryable = false;
      userMessage = 'Authentication required. Please log in again.';
    }
    // Handle authorization errors
    else if (record.status === 403 || baseError?.message?.includes('forbidden')) {
      code = 'AUTHORIZATION_ERROR';
      severity = 'high';
      retryable = false;
      userMessage = 'You do not have permission to perform this action.';
    }
    // Handle validation errors
    else if (record.status === 400 || baseError?.message?.includes('validation')) {
      code = 'VALIDATION_ERROR';
      severity = 'low';
      retryable = false;
      userMessage = 'Invalid input. Please check your data and try again.';
    }
    // Handle server errors
    else if (typeof record.status === 'number' && record.status >= 500) {
      code = 'SERVER_ERROR';
      severity = 'high';
      retryable = true;
      userMessage = 'Server error. Please try again in a moment.';
    }
    const serviceError = new Error(userMessage) as ServiceError;
    serviceError.name = 'ServiceError';
    serviceError.code = code;
    serviceError.severity = severity;
    serviceError.retryable = retryable;
    serviceError.userMessage = userMessage;
    serviceError.technicalMessage = technicalMessage;
    serviceError.context = {
      ...context,
      originalError: {
        name: (error as Error)?.name,
        message: (error as Error)?.message,
        stack: (error as Error)?.stack,
        status: record.status,
        endpoint: record.endpoint,
      },
    };
    serviceError.timestamp = Date.now();
    return serviceError;
  }
  private getApiErrorCode(error: ErrorRecord): string {
    const status = typeof error.status === 'number' ? error.status : undefined;
    if (status) {
      if (status >= 500) return 'API_SERVER_ERROR';
      if (status === 429) return 'API_RATE_LIMIT';
      if (status === 404) return 'API_NOT_FOUND';
      if (status === 403) return 'API_FORBIDDEN';
      if (status === 401) return 'API_UNAUTHORIZED';
      if (status === 400) return 'API_BAD_REQUEST';
    }
    return 'API_ERROR';
  }
  private getApiErrorSeverity(error: ErrorRecord): 'low' | 'medium' | 'high' | 'critical' {
    const status = typeof error.status === 'number' ? error.status : undefined;
    if (status && status >= 500) return 'high';
    if (status === 401 || status === 403) return 'high';
    if (status === 429) return 'medium';
    if (status && status >= 400) return 'low';
    if (error.isNetworkError || error.isTimeoutError) return 'medium';
    return 'medium';
  }
  private isApiErrorRetryable(error: ErrorRecord): boolean {
    const retryableStatuses = [408, 429, 500, 502, 503, 504];
    return (
      error.isNetworkError ||
      error.isTimeoutError ||
      (typeof error.status === 'number' && retryableStatuses.includes(error.status))
    );
  }
  private getApiErrorUserMessage(error: ErrorRecord): string {
    const status = typeof error.status === 'number' ? error.status : undefined;
    if (status === 401) return 'Please log in to continue.';
    if (status === 403) return 'You do not have permission to access this resource.';
    if (status === 404) return 'The requested resource was not found.';
    if (status === 429) return 'Too many requests. Please wait a moment and try again.';
    if (status && status >= 500) return 'Server error. Please try again in a moment.';
    if (error.isNetworkError) return 'Network connection issue. Please check your internet connection.';
    if (error.isTimeoutError) return 'Request timed out. Please try again.';
    return 'An error occurred while communicating with the server.';
  }
  private defaultRetryCondition = (error: Error, attempt: number): boolean => {
    // Don't retry if we've exceeded max attempts
    if (attempt >= this.config.maxRetries) {
      return false;
    }
    // Check if it's a retryable error
    if (error.name === 'ServiceError') {
      return (error as ServiceError).retryable;
    }
    // Default retry conditions for raw errors
    const normalized = normalizeError(error);
    const message = error.message.toLowerCase();
    const status = typeof normalized.status === 'number' ? normalized.status : undefined;
    return (
      message.includes('network') ||
      message.includes('timeout') ||
      message.includes('connection') ||
      message.includes('fetch') ||
      (status !== undefined && status >= 500)
    );
  };
  private logError(error: ServiceError): void {
    // Add to error log
    this.errorLog.push(error);
    // Keep only recent errors (last 100)
    if (this.errorLog.length > 100) {
      this.errorLog = this.errorLog.slice(-100);
    }
    // Console logging based on severity
    const logData = {
      code: error.code,
      severity: error.severity,
      service: error.context?.service,
      method: error.context?.method,
      endpoint: error.context?.endpoint,
      userMessage: error.userMessage,
      technicalMessage: error.technicalMessage,
      timestamp: new Date(error.timestamp).toISOString(),
    };
    switch (error.severity) {
      case 'critical':
        console.error('CRITICAL ERROR:', logData);
        break;
      case 'high':
        console.error('HIGH SEVERITY ERROR:', logData);
        break;
      case 'medium':
        console.warn('MEDIUM SEVERITY ERROR:', logData);
        break;
      case 'low':
        console.log('LOW SEVERITY ERROR:', logData);
        break;
    }
  }
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  /**
   * Public utility methods
   */
  public getErrorLog(): ServiceError[] {
    return [...this.errorLog];
  }
  public clearErrorLog(): void {
    this.errorLog = [];
  }
  public getErrorStats(): {
    total: number;
    bySeverity: Record<string, number>;
    byCode: Record<string, number>;
    byService: Record<string, number>;
  } {
    const stats = {
      total: this.errorLog.length,
      bySeverity: {} as Record<string, number>,
      byCode: {} as Record<string, number>,
      byService: {} as Record<string, number>,
    };
    this.errorLog.forEach(error => {
      // Count by severity
      stats.bySeverity[error.severity] = (stats.bySeverity[error.severity] || 0) + 1;
      // Count by code
      stats.byCode[error.code] = (stats.byCode[error.code] || 0) + 1;
      // Count by service
      const service = String(error.context?.service ?? 'unknown');
      stats.byService[service] = (stats.byService[service] || 0) + 1;
    });

    return stats;
  }
  public updateConfig(config: Partial<ErrorHandlerConfig>): void {
    this.config = { ...this.config, ...config };
  }
  public getConfig(): ErrorHandlerConfig {
    return { ...this.config };
  }
}
// Singleton instance
let serviceErrorHandler: ServiceErrorHandler | null = null;
/**
 * Get the global service error handler instance
 */
export function getServiceErrorHandler(): ServiceErrorHandler {
  if (!serviceErrorHandler) {
    serviceErrorHandler = new ServiceErrorHandler();
  }
  return serviceErrorHandler;
}
/**
 * Initialize service error handler with custom configuration
 */
export function initializeServiceErrorHandler(config?: Partial<ErrorHandlerConfig>): ServiceErrorHandler {
  serviceErrorHandler = new ServiceErrorHandler(config);
  return serviceErrorHandler;
}
/**
 * Utility function to create user-friendly error messages
 */
export function createUserFriendlyError(
  error: unknown,
  context: string = 'operation'
): string {
  if ((error as ServiceError)?.userMessage) {
    return (error as ServiceError).userMessage;
  }
  if ((error as Record<string, unknown>)?.status) {
    switch ((error as Record<string, unknown>).status) {
      case 401: return 'Please log in to continue.';
      case 403: return 'You do not have permission to perform this action.';
      case 404: return 'The requested resource was not found.';
      case 429: return 'Too many requests. Please wait a moment and try again.';
      case 500: return 'Server error. Please try again in a moment.';
      default: return `An error occurred during ${context}. Please try again.`;
    }
  }
  if ((error as Record<string, unknown>)?.isNetworkError || (error as Error)?.message?.includes('fetch')) {
    return 'Network connection issue. Please check your internet connection and try again.';
  }
  if ((error as Record<string, unknown>)?.isTimeoutError || (error as Error)?.message?.includes('timeout')) {
    return 'Request timed out. Please try again.';
  }
  return `An unexpected error occurred during ${context}. Please try again.`;
}
