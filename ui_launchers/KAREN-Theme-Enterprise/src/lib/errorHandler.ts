/**
 * Consolidated Production-Ready Error Handler
 * 
 * Consolidates error handling from multiple files into a unified system that:
 * - Properly logs all errors (no suppression in production)
 * - Provides meaningful user feedback while maintaining security
 * - Implements error recovery and fallback mechanisms
 * - Supports error monitoring and reporting
 * - Handles extension-specific errors gracefully
 * - Includes AG-UI error handling capabilities
 * - Provides safe console utilities
 */

import { useToast } from "../hooks/use-toast";

// Error Categories
export enum ErrorCategory {
  NETWORK = 'network',
  AUTHENTICATION = 'authentication', 
  AUTHORIZATION = 'authorization',
  VALIDATION = 'validation',
  SYSTEM = 'system',
  EXTENSION = 'extension',
  PLUGIN = 'plugin',
  MEMORY = 'memory',
  AI_PROCESSING = 'ai_processing',
  TIMEOUT = 'timeout',
  RATE_LIMIT = 'rate_limit',
  SERVICE_UNAVAILABLE = 'service_unavailable',
  AG_UI = 'ag_ui',
  UNKNOWN = 'unknown'
}

// Error Severity Levels
export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// Standardized Error Response Structure
export interface ErrorInfo {
  category: ErrorCategory;
  severity: ErrorSeverity;
  code: string;
  title: string;
  message: string;
  userMessage: string;
  technicalDetails?: string;
  timestamp: string;
  requestId: string;
  context?: Record<string, unknown>;
  retryable: boolean;
  userActionRequired: boolean;
  resolutionSteps?: string[];
  fallbackData?: unknown;
  reportedToMonitoring: boolean;
}

// Error Context for additional information
export interface ErrorContext extends Record<string, unknown> {
  operation?: string;
  userId?: string;
  sessionId?: string;
  component?: string;
  endpoint?: string;
  additionalData?: Record<string, unknown>;
}

// Error Reporting Configuration
export interface ErrorReportingConfig {
  enableTelemetry: boolean;
  enableConsoleLogging: boolean;
  enableUserNotifications: boolean;
  maxLogEntries: number;
  reportingEndpoint?: string;
  environment: 'development' | 'production' | 'test';
}

// Recovery Action Types
export interface RecoveryAction {
  type: 'retry' | 'fallback' | 'redirect' | 'refresh' | 'none';
  delay?: number; // seconds
  maxRetries?: number;
  fallbackData?: unknown;
  redirectUrl?: string;
}

// Error Monitoring Event
export interface ErrorMonitoringEvent {
  errorId: string;
  timestamp: string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  message: string;
  context: ErrorContext;
  userAgent?: string;
  url?: string;
  resolved: boolean;
}

// AG-UI Error Types (from ag-ui-error-handler.ts)
export enum AGUIErrorType {
  GRID_LOAD_ERROR = 'grid_load_error',
  GRID_RENDER_ERROR = 'grid_render_error',
  CHART_RENDER_ERROR = 'chart_render_error',
  DATA_FETCH_ERROR = 'data_fetch_error',
  COMPONENT_CRASH = 'component_crash',
  MEMORY_ERROR = 'memory_error',
  TIMEOUT_ERROR = 'timeout_error',
}

export enum FallbackStrategy {
  SIMPLE_TABLE = 'simple_table',
  CACHED_DATA = 'cached_data',
  LOADING_STATE = 'loading_state',
  ERROR_MESSAGE = 'error_message',
  RETRY_MECHANISM = 'retry_mechanism',
}

export interface AGUIErrorContext {
  component: string;
  errorType: AGUIErrorType;
  originalError: Error;
  data?: unknown[];
  columns?: unknown[];
  timestamp: string;
  retryCount: number;
}

export interface FallbackResponse {
  strategy: FallbackStrategy;
  component: React.ComponentType<Record<string, unknown>> | null;
  data: unknown[];
  columns: unknown[];
  message: string;
  retryAvailable: boolean;
  degradedFeatures: string[];
}

// Safe Console Options
export interface SafeConsoleOptions {
  skipInProduction?: boolean;
  useStructuredLogging?: boolean;
}

type ErrorLike = {
  name?: string;
  message?: string;
  stack?: string;
};

function isErrorLike(error: unknown): error is Error | ErrorLike {
  if (error instanceof Error) {
    return true;
  }

  if (!error || typeof error !== "object") {
    return false;
  }

  const candidate = error as Record<string, unknown>;
  return (
    "name" in candidate ||
    "message" in candidate ||
    "stack" in candidate
  );
}

class ConsolidatedErrorHandler {
  private static instance: ConsolidatedErrorHandler;
  private errorLog: ErrorInfo[] = [];
  private monitoringEvents: ErrorMonitoringEvent[] = [];
  private config: ErrorReportingConfig;
  private recoveryStrategies: Map<string, () => RecoveryAction> = new Map();
  private originalConsole: Console;
  private isConsolePatched = false;

  // AG-UI Error Handler State
  private errorCache: Map<string, { payload: unknown; timestamp: string }> = new Map();
  private circuitBreakers: Map<string, { isOpen: boolean; failureCount: number; lastFailureTime: number; halfOpenAttempts: number }> = new Map();
  private retryAttempts: Map<string, number> = new Map();

  // Configuration
  private readonly maxRetries = 3;
  private readonly circuitBreakerThreshold = 5;
  private readonly circuitBreakerTimeout = 60_000; // 1 minute
  private readonly cacheTimeout = 300_000; // 5 minutes

  private constructor() {
    this.originalConsole = { ...console };
    this.config = this.initializeConfig();
    this.setupRecoveryStrategies();
    this.setupGlobalErrorHandlers();
    this.patchConsole();
    this.initializeCircuitBreakers();
  }

  static getInstance(): ConsolidatedErrorHandler {
    if (!ConsolidatedErrorHandler.instance) {
      ConsolidatedErrorHandler.instance = new ConsolidatedErrorHandler();
    }
    return ConsolidatedErrorHandler.instance;
  }

  /**
   * Initialize configuration based on environment
   */
  private initializeConfig(): ErrorReportingConfig {
    const isDevelopment = process.env.NODE_ENV === 'development';
    const isProduction = process.env.NODE_ENV === 'production';
    
    return {
      enableTelemetry: isProduction,
      enableConsoleLogging: true, // Always enable console logging, never suppress
      enableUserNotifications: true,
      maxLogEntries: 100,
      reportingEndpoint: isProduction ? '/api/telemetry/errors' : undefined,
      environment: isProduction ? 'production' : (isDevelopment ? 'development' : 'test')
    };
  }

  /**
   * Patch console to prevent interceptor issues
   */
  private patchConsole(): void {
    if (this.isConsolePatched || typeof window === 'undefined') return;
    this.isConsolePatched = true;

    const self = this;

    // Patch console.error
    console.error = function patchedConsoleError(...args: unknown[]) {
      try {
        // Filter out known interceptor signatures
        const first = args[0];
        const msg = typeof first === 'string' ? first : String(first);
        
        if (
          msg.includes('console-error.js') ||
          msg.includes('use-error-handler.js') ||
          msg.includes('intercept-console-error.js') ||
          msg.includes('[ERROR] "KarenBackendService 4xx/5xx"') ||
          msg.includes('[ERROR] "[EXT_AUTH_HIGH] Permission Denied"')
        ) {
          self.originalConsole.info('[SAFE]', ...args);
          return;
        }

        self.originalConsole.error(...args);
      } catch {
        self.originalConsole.error(...args);
      }
    };

    // Patch console.warn
    console.warn = function patchedConsoleWarn(...args: unknown[]) {
      try {
        const first = args[0];
        const msg = typeof first === 'string' ? first : String(first);
        
        if (
          msg.includes('console-error.js') ||
          msg.includes('use-error-handler.js') ||
          msg.includes('intercept-console-error.js')
        ) {
          self.originalConsole.info('[SAFE]', ...args);
          return;
        }

        self.originalConsole.warn(...args);
      } catch {
        self.originalConsole.warn(...args);
      }
    };
  }

  /**
   * Initialize circuit breakers for AG-UI components
   */
  private initializeCircuitBreakers(): void {
    const components = ['grid', 'chart', 'analytics', 'memory'];
    const now = Date.now();
    components.forEach((component) => {
      if (!this.circuitBreakers.has(component)) {
        this.circuitBreakers.set(component, {
          isOpen: false,
          failureCount: 0,
          lastFailureTime: now,
          halfOpenAttempts: 0,
        });
      }
    });
  }

  /**
   * Setup recovery strategies for different error types
   */
  private setupRecoveryStrategies(): void {
    // Network errors - retry with exponential backoff
    this.recoveryStrategies.set(ErrorCategory.NETWORK, () => ({
      type: 'retry',
      delay: 2,
      maxRetries: 3
    }));

    // Timeout errors - retry with longer delay
    this.recoveryStrategies.set(ErrorCategory.TIMEOUT, () => ({
      type: 'retry',
      delay: 5,
      maxRetries: 2
    }));

    // Rate limit errors - retry with significant delay
    this.recoveryStrategies.set(ErrorCategory.RATE_LIMIT, () => ({
      type: 'retry',
      delay: 60,
      maxRetries: 1
    }));

    // Extension errors - use fallback data
    this.recoveryStrategies.set(ErrorCategory.EXTENSION, () => ({
      type: 'fallback',
      fallbackData: this.getExtensionFallbackData()
    }));

    // AG-UI errors - use AG-UI specific fallbacks
    this.recoveryStrategies.set(ErrorCategory.AG_UI, () => ({
      type: 'fallback',
      fallbackData: this.getAGUIFallbackData()
    }));

    // Service unavailable - retry with fallback
    this.recoveryStrategies.set(ErrorCategory.SERVICE_UNAVAILABLE, () => ({
      type: 'retry',
      delay: 30,
      maxRetries: 2,
      fallbackData: this.getServiceUnavailableFallback()
    }));
  }

  /**
   * Setup global error handlers for unhandled errors
   */
  private setupGlobalErrorHandlers(): void {
    if (typeof window !== 'undefined') {
      // Handle unhandled JavaScript errors
      window.addEventListener('error', (event) => {
        this.handleError(event.error, {
          operation: 'global_error_handler',
          component: 'window',
          additionalData: {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
          }
        });
      });

      // Handle unhandled promise rejections
      window.addEventListener('unhandledrejection', (event) => {
        this.handleError(event.reason, {
          operation: 'unhandled_promise_rejection',
          component: 'window'
        });
      });
    }
  }

  /**
   * Main error handling method - consolidates all error handling logic
   */
  public handleError(
    error: unknown,
    context: ErrorContext = {}
  ): ErrorInfo {
    const errorInfo = this.createErrorInfo(error, context);
    
    // Always log errors - never suppress in production
    this.logError(errorInfo);
    
    // Report to monitoring if enabled
    if (this.config.enableTelemetry) {
      this.reportToMonitoring(errorInfo);
    }
    
    // Show user notification if enabled
    if (this.config.enableUserNotifications) {
      this.showUserNotification(errorInfo);
    }
    
    // Store in error log
    this.addToErrorLog(errorInfo);
    
    return errorInfo;
  }

  /**
   * Handle AG-UI specific errors
   */
  public async handleAGUIError(
    error: Error,
    component: string,
    data?: unknown[],
    columns?: unknown[]
  ): Promise<FallbackResponse> {
    const context: AGUIErrorContext = {
      component,
      errorType: this.classifyAGUIError(error),
      originalError: error,
      data,
      columns,
      timestamp: new Date().toISOString(),
      retryCount: this.getRetryCount(component),
    };

    // Convert to standard error info for logging
    this.handleError(error, {
      operation: 'ag_ui_error',
      component,
      additionalData: { context }
    });

    // Handle AG-UI specific fallback logic
    return this.createAGUIFallback(context);
  }

  /**
   * Create standardized ErrorInfo from various error types
   */
  private createErrorInfo(error: unknown, context: ErrorContext): ErrorInfo {
    const timestamp = new Date().toISOString();
    const requestId = this.generateRequestId();
    
    // Handle different error types
    if (error instanceof Error) {
      return this.createErrorFromNativeError(error, context, timestamp, requestId);
    } else if (this.isHttpError(error)) {
      return this.createErrorFromHttpError(error, context, timestamp, requestId);
    } else if (typeof error === 'string') {
      return this.createErrorFromString(error, context, timestamp, requestId);
    } else {
      return this.createErrorFromUnknown(error, context, timestamp, requestId);
    }
  }

  /**
   * Create error from native JavaScript Error
   */
  private createErrorFromNativeError(
    error: Error,
    context: ErrorContext,
    timestamp: string,
    requestId: string
  ): ErrorInfo {
    const category = this.categorizeError(error);
    const severity = this.assessSeverity(error, category);
    const { code, title, userMessage, resolutionSteps } = this.getErrorMessage(error, category);
    
    return {
      category,
      severity,
      code,
      title,
      message: error.message,
      userMessage,
      timestamp,
      requestId,
      context,
      technicalDetails: error.stack,
      retryable: this.isRetryable(category, error),
      userActionRequired: this.requiresUserAction(category, error),
      resolutionSteps,
      reportedToMonitoring: false
    };
  }

  /**
   * Create error from HTTP response error
   */
  private createErrorFromHttpError(
    error: any,
    context: ErrorContext,
    timestamp: string,
    requestId: string
  ): ErrorInfo {
    const status = error.response?.status || error.status || 0;
    const category = this.categorizeHttpError(status);
    const severity = this.assessHttpSeverity(status);
    const { code, title, userMessage, resolutionSteps } = this.getHttpErrorMessage(status);
    
    return {
      category,
      severity,
      code,
      title,
      message: `HTTP ${status}: ${error.message || 'Unknown error'}`,
      userMessage,
      timestamp,
      requestId,
      context: {
        ...context,
        endpoint: error.config?.url || context.endpoint,
        status,
        statusText: error.response?.statusText
      },
      technicalDetails: JSON.stringify({
        status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        config: error.config
      }),
      retryable: this.isHttpRetryable(status),
      userActionRequired: this.requiresHttpUserAction(status),
      resolutionSteps,
      fallbackData: this.getHttpFallbackData(status, error.config?.url),
      reportedToMonitoring: false
    };
  }

  /**
   * Create error from string message
   */
  private createErrorFromString(
    error: string,
    context: ErrorContext,
    timestamp: string,
    requestId: string
  ): ErrorInfo {
    const category = ErrorCategory.UNKNOWN;
    const severity = ErrorSeverity.MEDIUM;
    
    return {
      category,
      severity,
      code: 'STRING_ERROR',
      title: 'Error',
      message: error,
      userMessage: error.startsWith('Karen:') ? error : 'An error occurred',
      timestamp,
      requestId,
      context,
      retryable: true,
      userActionRequired: false,
      resolutionSteps: ['Try the operation again', 'Refresh the page if the problem persists'],
      reportedToMonitoring: false
    };
  }

  /**
   * Create error from unknown type
   */
  private createErrorFromUnknown(
    error: unknown,
    context: ErrorContext,
    timestamp: string,
    requestId: string
  ): ErrorInfo {
    const category = ErrorCategory.UNKNOWN;
    const severity = ErrorSeverity.HIGH;
    
    return {
      category,
      severity,
      code: 'UNKNOWN_ERROR',
      title: 'Unexpected Error',
      message: 'An unexpected error occurred',
      userMessage: 'Something went wrong. Please try again.',
      timestamp,
      requestId,
      context,
      technicalDetails: JSON.stringify(error),
      retryable: false,
      userActionRequired: true,
      resolutionSteps: ['Refresh the page', 'Try again later', 'Contact support if the problem persists'],
      reportedToMonitoring: false
    };
  }

  /**
   * Categorize JavaScript errors
   */
  private categorizeError(error: Error): ErrorCategory {
    const message = error.message.toLowerCase();
    
    if (message.includes('network') || message.includes('fetch')) {
      return ErrorCategory.NETWORK;
    }
    if (message.includes('timeout')) {
      return ErrorCategory.TIMEOUT;
    }
    if (message.includes('api key') || message.includes('authentication')) {
      return ErrorCategory.AUTHENTICATION;
    }
    if (message.includes('permission') || message.includes('unauthorized')) {
      return ErrorCategory.AUTHORIZATION;
    }
    if (message.includes('validation') || message.includes('schema')) {
      return ErrorCategory.VALIDATION;
    }
    if (message.includes('extension')) {
      return ErrorCategory.EXTENSION;
    }
    if (message.includes('plugin')) {
      return ErrorCategory.PLUGIN;
    }
    if (message.includes('memory')) {
      return ErrorCategory.MEMORY;
    }
    if (message.includes('ai') || message.includes('processing')) {
      return ErrorCategory.AI_PROCESSING;
    }
    if (message.includes('ag-grid') || message.includes('ag-chart')) {
      return ErrorCategory.AG_UI;
    }
    
    return ErrorCategory.SYSTEM;
  }

  /**
   * Categorize HTTP errors
   */
  private categorizeHttpError(status: number): ErrorCategory {
    if (status === 401) return ErrorCategory.AUTHENTICATION;
    if (status === 403) return ErrorCategory.AUTHORIZATION;
    if (status === 404) return ErrorCategory.VALIDATION;
    if (status === 429) return ErrorCategory.RATE_LIMIT;
    if (status >= 500) return ErrorCategory.SERVICE_UNAVAILABLE;
    if (status >= 400) return ErrorCategory.VALIDATION;
    
    return ErrorCategory.NETWORK;
  }

  /**
   * Assess error severity
   */
  private assessSeverity(error: Error, category: ErrorCategory): ErrorSeverity {
    // Critical errors that completely break functionality
    if (category === ErrorCategory.SYSTEM || category === ErrorCategory.AUTHENTICATION) {
      return ErrorSeverity.CRITICAL;
    }
    
    // High severity errors that significantly impact user experience
    if (category === ErrorCategory.SERVICE_UNAVAILABLE || category === ErrorCategory.AI_PROCESSING) {
      return ErrorSeverity.HIGH;
    }
    
    // Medium severity for common recoverable errors
    if (category === ErrorCategory.NETWORK || category === ErrorCategory.TIMEOUT) {
      return ErrorSeverity.MEDIUM;
    }
    
    // Low severity for minor issues
    return ErrorSeverity.LOW;
  }

  /**
   * Assess HTTP error severity
   */
  private assessHttpSeverity(status: number): ErrorSeverity {
    if (status >= 500) return ErrorSeverity.HIGH;
    if (status === 429) return ErrorSeverity.MEDIUM;
    if (status >= 400) return ErrorSeverity.LOW;
    
    return ErrorSeverity.MEDIUM;
  }

  /**
   * Get appropriate error messages
   */
  private getErrorMessage(error: Error, category: ErrorCategory): {
    code: string;
    title: string;
    userMessage: string;
    resolutionSteps: string[];
  } {
    switch (category) {
      case ErrorCategory.NETWORK:
        return {
          code: 'NETWORK_ERROR',
          title: 'Network Error',
          userMessage: 'Unable to connect to the server. Please check your internet connection.',
          resolutionSteps: ['Check your internet connection', 'Try again in a few moments', 'Contact support if the problem persists']
        };
      
      case ErrorCategory.TIMEOUT:
        return {
          code: 'TIMEOUT_ERROR',
          title: 'Request Timeout',
          userMessage: 'The request took too long to complete. Please try again.',
          resolutionSteps: ['Check your connection speed', 'Try again', 'Contact support if timeouts persist']
        };
      
      case ErrorCategory.AUTHENTICATION:
        return {
          code: 'AUTH_ERROR',
          title: 'Authentication Error',
          userMessage: 'Please log in to access this feature.',
          resolutionSteps: ['Log in to your account', 'Check your credentials', 'Contact support if you cannot log in']
        };
      
      case ErrorCategory.EXTENSION:
        return {
          code: 'EXTENSION_ERROR',
          title: 'Extension Error',
          userMessage: 'Extension features are temporarily unavailable.',
          resolutionSteps: ['Try again later', 'Check extension permissions', 'Use core features while extensions are unavailable']
        };
      
      case ErrorCategory.AG_UI:
        return {
          code: 'AG_UI_ERROR',
          title: 'UI Component Error',
          userMessage: 'A display component encountered an error. Using simplified view.',
          resolutionSteps: ['Refresh the page if issues persist', 'Try with reduced data set', 'Contact support if the problem continues']
        };
      
      default:
        return {
          code: 'SYSTEM_ERROR',
          title: 'System Error',
          userMessage: 'An error occurred. Please try again.',
          resolutionSteps: ['Try the operation again', 'Refresh the page', 'Contact support if the problem persists']
        };
    }
  }

  /**
   * Get HTTP error messages
   */
  private getHttpErrorMessage(status: number): {
    code: string;
    title: string;
    userMessage: string;
    resolutionSteps: string[];
  } {
    switch (status) {
      case 400:
        return {
          code: 'BAD_REQUEST',
          title: 'Invalid Request',
          userMessage: 'The request was invalid. Please check your input and try again.',
          resolutionSteps: ['Check your input', 'Refresh the page', 'Contact support']
        };
      
      case 401:
        return {
          code: 'UNAUTHORIZED',
          title: 'Authentication Required',
          userMessage: 'Please log in to access this feature.',
          resolutionSteps: ['Log in to your account', 'Check your credentials']
        };
      
      case 403:
        return {
          code: 'FORBIDDEN',
          title: 'Access Denied',
          userMessage: 'You do not have permission to access this feature.',
          resolutionSteps: ['Check your permissions', 'Contact your administrator', 'Log in with appropriate account']
        };
      
      case 404:
        return {
          code: 'NOT_FOUND',
          title: 'Not Found',
          userMessage: 'The requested resource was not found.',
          resolutionSteps: ['Check the URL', 'Search for the resource', 'Contact support']
        };
      
      case 429:
        return {
          code: 'RATE_LIMITED',
          title: 'Too Many Requests',
          userMessage: 'Please wait before making more requests.',
          resolutionSteps: ['Wait a few minutes', 'Reduce request frequency', 'Contact support for limits']
        };
      
      case 500:
        return {
          code: 'SERVER_ERROR',
          title: 'Server Error',
          userMessage: 'The server encountered an error. Please try again later.',
          resolutionSteps: ['Try again in a few minutes', 'Contact support if the problem persists']
        };
      
      default:
        return {
          code: 'HTTP_ERROR',
          title: 'HTTP Error',
          userMessage: 'An HTTP error occurred. Please try again.',
          resolutionSteps: ['Try again', 'Refresh the page', 'Contact support']
        };
    }
  }

  /**
   * Check if error is retryable
   */
  private isRetryable(category: ErrorCategory, error: Error): boolean {
    return [
      ErrorCategory.NETWORK,
      ErrorCategory.TIMEOUT,
      ErrorCategory.SERVICE_UNAVAILABLE,
      ErrorCategory.RATE_LIMIT
    ].includes(category);
  }

  /**
   * Check if HTTP error is retryable
   */
  private isHttpRetryable(status: number): boolean {
    return status === 429 || status >= 500 || status === 0;
  }

  /**
   * Check if user action is required
   */
  private requiresUserAction(category: ErrorCategory, error: Error): boolean {
    return [
      ErrorCategory.AUTHENTICATION,
      ErrorCategory.AUTHORIZATION,
      ErrorCategory.VALIDATION
    ].includes(category);
  }

  /**
   * Check if HTTP error requires user action
   */
  private requiresHttpUserAction(status: number): boolean {
    return status === 401 || status === 403 || status === 422;
  }

  /**
   * Get fallback data for HTTP errors
   */
  private getHttpFallbackData(status: number, url?: string): unknown {
    if (url?.includes('/api/extensions')) {
      return this.getExtensionFallbackData();
    }
    
    if (status >= 500) {
      return this.getServiceUnavailableFallback();
    }
    
    return null;
  }

  /**
   * Get extension fallback data
   */
  private getExtensionFallbackData(): unknown {
    return {
      extensions: {
        'offline-mode': {
          id: 'offline-mode',
          name: 'Extensions (Offline Mode)',
          display_name: 'Extensions (Offline Mode)',
          description: 'Extension service is temporarily unavailable. Core functionality continues to work.',
          version: '1.0.0',
          author: 'System',
          category: 'system',
          status: 'offline',
          capabilities: {
            provides_ui: false,
            provides_api: false,
            provides_background_tasks: false,
            provides_webhooks: false
          }
        }
      },
      total: 1,
      message: 'Extension service is temporarily unavailable',
      access_level: 'offline',
      available_features: [],
      restricted_features: ['all'],
      fallback_mode: true
    };
  }

  /**
   * Get service unavailable fallback
   */
  private getServiceUnavailableFallback(): unknown {
    return {
      status: 'degraded',
      message: 'Service is temporarily unavailable',
      fallback_data: true,
      retry_after: 30
    };
  }

  /**
   * Get AG-UI fallback data
   */
  private getAGUIFallbackData(): unknown {
    return {
      strategy: FallbackStrategy.SIMPLE_TABLE,
      message: 'UI component failed to load. Using simplified view.',
      retryAvailable: true,
      degradedFeatures: ['advanced-features', 'custom-renderers', 'complex-interactions']
    };
  }

  /**
   * Classify AG-UI errors
   */
  private classifyAGUIError(error: Error): AGUIErrorType {
    const message = (error.message || '').toLowerCase();
    if (message.includes('load') || message.includes('fetch')) {
      return AGUIErrorType.GRID_LOAD_ERROR;
    } else if (message.includes('render') || message.includes('display')) {
      return AGUIErrorType.GRID_RENDER_ERROR;
    } else if (message.includes('data')) {
      return AGUIErrorType.DATA_FETCH_ERROR;
    } else if (message.includes('memory') || message.includes('heap')) {
      return AGUIErrorType.MEMORY_ERROR;
    } else if (message.includes('timeout')) {
      return AGUIErrorType.TIMEOUT_ERROR;
    } else {
      return AGUIErrorType.COMPONENT_CRASH;
    }
  }

  /**
   * Create AG-UI fallback response
   */
  private createAGUIFallback(context: AGUIErrorContext): FallbackResponse {
    return {
      strategy: FallbackStrategy.SIMPLE_TABLE,
      component: null, // Consuming code renders a basic table
      data: context.data || [],
      columns: this.extractSimpleColumns(context.data || []),
      message: 'UI component failed to load. Using simplified view.',
      retryAvailable: true,
      degradedFeatures: ['sorting', 'filtering', 'pagination', 'cell-editing', 'advanced-features']
    };
  }

  /**
   * Extract simple columns from data
   */
  private extractSimpleColumns(data: unknown[]): unknown[] {
    if (!Array.isArray(data) || data.length === 0) {
      return [{ field: 'message', headerName: 'Status' }];
    }
    const firstRow = (data[0] ?? {}) as Record<string, unknown>;
    return Object.keys(firstRow).map((key) => ({
      field: key,
      headerName: key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
    }));
  }

  /**
   * Get retry count for component
   */
  private getRetryCount(component: string): number {
    return this.retryAttempts.get(component) ?? 0;
  }

  /**
   * Log error appropriately based on environment
   */
  private logError(errorInfo: ErrorInfo): void {
    if (!this.config.enableConsoleLogging) {
      return;
    }

    const logMessage = `[${errorInfo.category.toUpperCase()}] ${errorInfo.title}: ${errorInfo.message}`;
    const logData = {
      requestId: errorInfo.requestId,
      timestamp: errorInfo.timestamp,
      context: errorInfo.context,
      severity: errorInfo.severity,
      code: errorInfo.code
    };

    // Always log errors - never suppress in production
    switch (errorInfo.severity) {
      case ErrorSeverity.CRITICAL:
        this.originalConsole.error(logMessage, logData);
        break;
      case ErrorSeverity.HIGH:
        this.originalConsole.error(logMessage, logData);
        break;
      case ErrorSeverity.MEDIUM:
        this.originalConsole.warn(logMessage, logData);
        break;
      case ErrorSeverity.LOW:
        this.originalConsole.info(logMessage, logData);
        break;
    }

    // In development, include more details
    if (this.config.environment === 'development') {
      this.originalConsole.debug('Error details:', {
        ...errorInfo,
        technicalDetails: errorInfo.technicalDetails
      });
    }
  }

  /**
   * Report error to monitoring system
   */
  private async reportToMonitoring(errorInfo: ErrorInfo): Promise<void> {
    if (!this.config.reportingEndpoint || errorInfo.reportedToMonitoring) {
      return;
    }

    try {
      const monitoringEvent: ErrorMonitoringEvent = {
        errorId: errorInfo.requestId,
        timestamp: errorInfo.timestamp,
        category: errorInfo.category,
        severity: errorInfo.severity,
        message: errorInfo.message,
        context: errorInfo.context || {},
        userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : undefined,
        url: typeof window !== 'undefined' ? window.location.href : undefined,
        resolved: false
      };

      // Store monitoring event
      this.monitoringEvents.push(monitoringEvent);

      // Send to monitoring endpoint
      await fetch(this.config.reportingEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(monitoringEvent)
      });

      // Mark as reported
      errorInfo.reportedToMonitoring = true;
      
      this.originalConsole.info('Error reported to monitoring system', { errorId: errorInfo.requestId });
    } catch (reportingError) {
      // Don't let reporting errors break the application
      this.originalConsole.warn('Failed to report error to monitoring system', reportingError);
    }
  }

  /**
   * Show user notification
   */
  private showUserNotification(errorInfo: ErrorInfo): void {
    if (typeof window === 'undefined') {
      return; // Skip on server-side
    }

    const variant = errorInfo.severity === ErrorSeverity.CRITICAL || errorInfo.severity === ErrorSeverity.HIGH 
      ? 'destructive' 
      : 'default';

    const { toast } = useToast();
    toast({
      title: errorInfo.title,
      description: errorInfo.userMessage,
      variant,
      duration: this.getNotificationDuration(errorInfo.severity)
    });
  }

  /**
   * Get notification duration based on severity
   */
  private getNotificationDuration(severity: ErrorSeverity): number {
    switch (severity) {
      case ErrorSeverity.CRITICAL: return 10000; // 10 seconds
      case ErrorSeverity.HIGH: return 7000; // 7 seconds
      case ErrorSeverity.MEDIUM: return 5000; // 5 seconds
      case ErrorSeverity.LOW: return 3000; // 3 seconds
      default: return 5000;
    }
  }

  /**
   * Add error to internal log
   */
  private addToErrorLog(errorInfo: ErrorInfo): void {
    this.errorLog.push(errorInfo);
    
    // Maintain log size
    if (this.errorLog.length > this.config.maxLogEntries) {
      this.errorLog = this.errorLog.slice(-this.config.maxLogEntries);
    }
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  }

  /**
   * Check if error is HTTP error
   */
  private isHttpError(error: any): boolean {
    return error && (
      (error.response && typeof error.response.status === 'number') ||
      (typeof error.status === 'number') ||
      (error.config && error.config.url)
    );
  }

  /**
   * Get recovery action for error
   */
  public getRecoveryAction(errorInfo: ErrorInfo): RecoveryAction {
    const strategy = this.recoveryStrategies.get(errorInfo.category);
    return strategy ? strategy() : { type: 'none' as const };
  }

  /**
   * Get recent error log
   */
  public getErrorLog(limit: number = 10): ErrorInfo[] {
    return this.errorLog.slice(-limit);
  }

  /**
   * Get error statistics
   */
  public getErrorStats(): {
    total: number;
    byCategory: Record<ErrorCategory, number>;
    bySeverity: Record<ErrorSeverity, number>;
    recent: ErrorInfo[];
  } {
    const byCategory: Record<ErrorCategory, number> = {} as Record<ErrorCategory, number>;
    const bySeverity: Record<ErrorSeverity, number> = {} as Record<ErrorSeverity, number>;
    
    // Initialize counters
    Object.values(ErrorCategory).forEach(category => {
      byCategory[category] = 0;
    });
    Object.values(ErrorSeverity).forEach(severity => {
      bySeverity[severity] = 0;
    });
    
    // Count errors
    this.errorLog.forEach(error => {
      byCategory[error.category]++;
      bySeverity[error.severity]++;
    });
    
    return {
      total: this.errorLog.length,
      byCategory,
      bySeverity,
      recent: this.errorLog.slice(-5)
    };
  }

  /**
   * Clear error log
   */
  public clearErrorLog(): void {
    this.errorLog = [];
    this.monitoringEvents = [];
  }

  /**
   * Update configuration
   */
  public updateConfig(newConfig: Partial<ErrorReportingConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get current configuration
   */
  public getConfig(): ErrorReportingConfig {
    return { ...this.config };
  }

  // Safe Console Methods
  
  /**
   * Safe error logging that prevents console interceptor issues
   */
  public safeError(
    message: string,
    error?: unknown,
    options: SafeConsoleOptions = {}
  ) {
    const { skipInProduction = false, useStructuredLogging = true } = options;

    // Skip in production if requested
    if (skipInProduction && process.env.NODE_ENV === "production") {
      return;
    }

    try {
      if (useStructuredLogging && error) {
        // Use structured logging to avoid interceptor issues
        const errorObj = isErrorLike(error) ? error : undefined;

        const errorName = errorObj?.name ?? "Unknown";
        const errorMessage = errorObj?.message ?? "No message";
        const errorStack = errorObj?.stack;
        
        const errorData = {
          message,
          error: {
            name: errorName,
            message: errorMessage,
            stack: errorStack,
          },
          timestamp: new Date().toISOString(),
          environment: process.env.NODE_ENV,
        };

        // Use original console methods to bypass interceptors
        this.originalConsole.error(
          "🚨 Safe Console Error:",
          JSON.stringify(errorData, null, 2)
        );
      } else {
        this.originalConsole.error(message, error);
      }
    } catch {
      // Fallback if even safe logging fails
      try {
        this.originalConsole.warn("Console error occurred:", message);
      } catch {
        // Last resort - do nothing to prevent infinite loops
      }
    }
  }

  /**
   * Safe warning logging
   */
  public safeWarn(message: string, data?: unknown) {
    try {
      this.originalConsole.warn(message, data);
    } catch {
      // Silently fail to prevent issues
    }
  }

  /**
   * Safe info logging
   */
  public safeInfo(message: string, data?: unknown) {
    try {
      this.originalConsole.info(message, data);
    } catch {
      // Silently fail to prevent issues
    }
  }

  /**
   * Safe debug logging (only in development)
   */
  public safeDebug(message: string, data?: unknown) {
    if (process.env.NODE_ENV === "development") {
      try {
        this.originalConsole.debug(message, data);
      } catch {
        // Silently fail to prevent issues
      }
    }
  }
}

// Export singleton instance
export const errorHandler = ConsolidatedErrorHandler.getInstance();

// Export convenience functions
export const handleError = (error: unknown, context?: ErrorContext): ErrorInfo => 
  errorHandler.handleError(error, context);

export const handleAGUIError = (
  error: Error,
  component: string,
  data?: unknown[],
  columns?: unknown[]
): Promise<FallbackResponse> => 
  errorHandler.handleAGUIError(error, component, data, columns);

export const getErrorLog = (limit?: number): ErrorInfo[] => 
  errorHandler.getErrorLog(limit);

export const getErrorStats = () => 
  errorHandler.getErrorStats();

export const clearErrorLog = (): void => 
  errorHandler.clearErrorLog();

export const getRecoveryAction = (errorInfo: ErrorInfo): RecoveryAction => 
  errorHandler.getRecoveryAction(errorInfo);

// Safe console exports
export const safeError = (
  message: string,
  error?: unknown,
  options?: SafeConsoleOptions
) => errorHandler.safeError(message, error, options);

export const safeWarn = (message: string, data?: unknown) =>
  errorHandler.safeWarn(message, data);

export const safeInfo = (message: string, data?: unknown) =>
  errorHandler.safeInfo(message, data);

export const safeDebug = (message: string, data?: unknown) =>
  errorHandler.safeDebug(message, data);

export const safeLog = (message: string, data?: unknown) =>
  errorHandler.safeInfo(message, data);

// Legacy compatibility exports
export const showSuccess = (title: string, message: string, duration: number = 3000) => {
  const { toast } = useToast();
  toast({ title, description: message, variant: "default", duration });
};

export const showInfo = (title: string, message: string, duration: number = 4000) => {
  const { toast } = useToast();
  toast({ title, description: message, variant: "default", duration });
};

export const showWarning = (title: string, message: string, duration: number = 5000) => {
  const { toast } = useToast();
  toast({ title, description: message, variant: "default", duration });
};

// Extension-specific error handling
export const handleExtensionError = (
  status: number,
  url: string,
  operation: string = 'extension_api'
): ErrorInfo => {
  return handleError(
    new Error(`Extension error: ${status} for ${url}`),
    {
      operation,
      endpoint: url,
      additionalData: { status, url }
    }
  );
};

// Error recovery function
export const attemptErrorRecovery = async (
  errorInfo: ErrorInfo,
  retryFunction?: () => Promise<unknown>
): Promise<unknown> => {
  const recoveryAction = getRecoveryAction(errorInfo);
  
  switch (recoveryAction.type) {
    case 'retry':
      if (retryFunction) {
        const delay = recoveryAction.delay || 0;
        if (delay > 0) {
          await new Promise(resolve => setTimeout(resolve, delay * 1000));
        }
        return retryFunction();
      }
      break;
      
    case 'fallback':
      return recoveryAction.fallbackData;
      
    case 'redirect':
      if (typeof window !== 'undefined' && recoveryAction.redirectUrl) {
        window.location.href = recoveryAction.redirectUrl;
      }
      break;
      
    case 'refresh':
      if (typeof window !== 'undefined') {
        window.location.reload();
      }
      break;
      
    case 'none':
    default:
      throw errorInfo;
  }
  
  return null;
};

// All types and interfaces are already exported above, no need to re-export