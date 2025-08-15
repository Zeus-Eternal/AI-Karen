import { getTelemetryService } from './telemetry';

export interface ErrorContext {
  userId?: string;
  sessionId?: string;
  correlationId?: string;
  url?: string;
  userAgent?: string;
  timestamp: string;
  
  // Component context
  componentName?: string;
  componentProps?: Record<string, any>;
  componentState?: Record<string, any>;
  
  // User context
  userActions?: string[];
  breadcrumbs?: Breadcrumb[];
  
  // Technical context
  stackTrace?: string;
  errorBoundary?: string;
  reactVersion?: string;
  buildVersion?: string;
  
  // Network context
  networkStatus?: 'online' | 'offline';
  connectionType?: string;
  
  // Performance context
  memoryUsage?: number;
  performanceMetrics?: Record<string, number>;
  
  // Custom context
  tags?: Record<string, string>;
  extra?: Record<string, any>;
}

export interface Breadcrumb {
  timestamp: string;
  category: 'navigation' | 'user' | 'http' | 'console' | 'error' | 'custom';
  message: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  data?: Record<string, any>;
}

export interface ErrorReport {
  id: string;
  error: {
    name: string;
    message: string;
    stack?: string;
  };
  context: ErrorContext;
  severity: 'low' | 'medium' | 'high' | 'critical';
  fingerprint?: string;
  resolved?: boolean;
  occurrenceCount?: number;
}

export interface ErrorTrackingConfig {
  enabled: boolean;
  maxBreadcrumbs: number;
  maxStackTraceLength: number;
  captureUnhandledRejections: boolean;
  captureConsoleErrors: boolean;
  beforeSend?: (report: ErrorReport) => ErrorReport | null;
  onError?: (report: ErrorReport) => void;
  endpoint?: string;
  apiKey?: string;
  environment?: string;
  release?: string;
  sampleRate: number;
}

class ErrorTracker {
  private config: ErrorTrackingConfig;
  private breadcrumbs: Breadcrumb[] = [];
  private userActions: string[] = [];
  private sessionId: string;
  private isInitialized = false;

  constructor(config: Partial<ErrorTrackingConfig> = {}) {
    this.config = {
      enabled: true,
      maxBreadcrumbs: 50,
      maxStackTraceLength: 10000,
      captureUnhandledRejections: true,
      captureConsoleErrors: true,
      sampleRate: 1.0,
      environment: process.env.NODE_ENV || 'development',
      ...config
    };

    this.sessionId = this.generateId();
    this.initialize();
  }

  private initialize(): void {
    if (this.isInitialized || !this.config.enabled || typeof window === 'undefined') {
      return;
    }

    this.setupGlobalErrorHandlers();
    this.setupUnhandledRejectionHandler();
    this.setupConsoleErrorCapture();
    this.setupNetworkMonitoring();
    this.setupUserActionTracking();
    
    this.isInitialized = true;
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupGlobalErrorHandlers(): void {
    // Capture global JavaScript errors
    window.addEventListener('error', (event) => {
      this.captureError(event.error || new Error(event.message), {
        componentName: 'GlobalErrorHandler',
        extra: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        }
      });
    });

    // Capture resource loading errors
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.captureError(new Error(`Resource loading failed: ${(event.target as any)?.src || 'unknown'}`), {
          componentName: 'ResourceLoader',
          extra: {
            tagName: (event.target as any)?.tagName,
            src: (event.target as any)?.src,
            href: (event.target as any)?.href,
          }
        });
      }
    }, true);
  }

  private setupUnhandledRejectionHandler(): void {
    if (!this.config.captureUnhandledRejections) return;

    window.addEventListener('unhandledrejection', (event) => {
      const error = event.reason instanceof Error 
        ? event.reason 
        : new Error(`Unhandled promise rejection: ${event.reason}`);
      
      this.captureError(error, {
        componentName: 'UnhandledPromiseRejection',
        extra: {
          reason: event.reason,
          promise: event.promise,
        }
      });
    });
  }

  private setupConsoleErrorCapture(): void {
    if (!this.config.captureConsoleErrors) return;

    const originalConsoleError = console.error;
    console.error = (...args) => {
      // Call original console.error
      originalConsoleError.apply(console, args);
      
      // Capture as breadcrumb
      this.addBreadcrumb({
        category: 'console',
        message: args.map(arg => String(arg)).join(' '),
        level: 'error',
        data: { args }
      });
      
      // If first argument is an Error, capture it
      if (args[0] instanceof Error) {
        this.captureError(args[0], {
          componentName: 'ConsoleError',
          extra: { consoleArgs: args.slice(1) }
        });
      }
    };
  }

  private setupNetworkMonitoring(): void {
    // Monitor network status
    window.addEventListener('online', () => {
      this.addBreadcrumb({
        category: 'custom',
        message: 'Network connection restored',
        level: 'info'
      });
    });

    window.addEventListener('offline', () => {
      this.addBreadcrumb({
        category: 'custom',
        message: 'Network connection lost',
        level: 'warning'
      });
    });

    // Monitor fetch requests
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const url = typeof args[0] === 'string' ? args[0] : args[0].url;
      const method = args[1]?.method || 'GET';
      
      this.addBreadcrumb({
        category: 'http',
        message: `${method} ${url}`,
        level: 'info',
        data: { url, method }
      });

      try {
        const response = await originalFetch(...args);
        
        if (!response.ok) {
          this.addBreadcrumb({
            category: 'http',
            message: `${method} ${url} - ${response.status} ${response.statusText}`,
            level: 'warning',
            data: { url, method, status: response.status, statusText: response.statusText }
          });
        }
        
        return response;
      } catch (error) {
        this.addBreadcrumb({
          category: 'http',
          message: `${method} ${url} - Network Error`,
          level: 'error',
          data: { url, method, error: error.message }
        });
        
        this.captureError(error as Error, {
          componentName: 'NetworkRequest',
          extra: { url, method }
        });
        
        throw error;
      }
    };
  }

  private setupUserActionTracking(): void {
    // Track clicks
    document.addEventListener('click', (event) => {
      const target = event.target as HTMLElement;
      const tagName = target.tagName.toLowerCase();
      const id = target.id;
      const className = target.className;
      const text = target.textContent?.slice(0, 100);
      
      const action = `click:${tagName}${id ? `#${id}` : ''}${className ? `.${className}` : ''} "${text}"`;
      this.addUserAction(action);
      
      this.addBreadcrumb({
        category: 'user',
        message: `Clicked ${tagName}`,
        level: 'info',
        data: { tagName, id, className, text }
      });
    });

    // Track form submissions
    document.addEventListener('submit', (event) => {
      const form = event.target as HTMLFormElement;
      const action = form.action;
      const method = form.method;
      
      this.addUserAction(`submit:form[action="${action}"][method="${method}"]`);
      
      this.addBreadcrumb({
        category: 'user',
        message: `Submitted form`,
        level: 'info',
        data: { action, method }
      });
    });

    // Track navigation
    window.addEventListener('popstate', () => {
      this.addUserAction(`navigate:${window.location.pathname}`);
      
      this.addBreadcrumb({
        category: 'navigation',
        message: `Navigated to ${window.location.pathname}`,
        level: 'info',
        data: { pathname: window.location.pathname, search: window.location.search }
      });
    });
  }

  private addUserAction(action: string): void {
    this.userActions.push(action);
    
    // Keep only recent actions
    if (this.userActions.length > 20) {
      this.userActions = this.userActions.slice(-20);
    }
  }

  public addBreadcrumb(breadcrumb: Omit<Breadcrumb, 'timestamp'>): void {
    const fullBreadcrumb: Breadcrumb = {
      ...breadcrumb,
      timestamp: new Date().toISOString()
    };
    
    this.breadcrumbs.push(fullBreadcrumb);
    
    // Keep only recent breadcrumbs
    if (this.breadcrumbs.length > this.config.maxBreadcrumbs) {
      this.breadcrumbs = this.breadcrumbs.slice(-this.config.maxBreadcrumbs);
    }
  }

  public captureError(error: Error, context: Partial<ErrorContext> = {}): string {
    if (!this.config.enabled || !this.shouldSample()) {
      return '';
    }

    const errorId = this.generateId();
    const errorContext = this.buildErrorContext(context);
    const severity = this.determineSeverity(error, errorContext);
    
    const report: ErrorReport = {
      id: errorId,
      error: {
        name: error.name,
        message: error.message,
        stack: this.sanitizeStackTrace(error.stack)
      },
      context: errorContext,
      severity,
      fingerprint: this.generateFingerprint(error),
      occurrenceCount: 1
    };

    // Apply beforeSend hook
    const processedReport = this.config.beforeSend ? this.config.beforeSend(report) : report;
    if (!processedReport) {
      return errorId; // Report was filtered out
    }

    // Send to telemetry
    getTelemetryService().track('error_captured', {
      errorId,
      errorName: error.name,
      errorMessage: error.message,
      severity,
      fingerprint: processedReport.fingerprint,
      componentName: context.componentName,
      url: window.location.href,
      userAgent: navigator.userAgent,
      breadcrumbCount: this.breadcrumbs.length,
      userActionCount: this.userActions.length,
    }, errorContext.correlationId);

    // Store detailed report locally
    this.storeErrorReport(processedReport);

    // Send to external service if configured
    if (this.config.endpoint) {
      this.sendToEndpoint(processedReport);
    }

    // Call onError hook
    if (this.config.onError) {
      this.config.onError(processedReport);
    }

    return errorId;
  }

  private buildErrorContext(context: Partial<ErrorContext> = {}): ErrorContext {
    const baseContext: ErrorContext = {
      sessionId: this.sessionId,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      breadcrumbs: [...this.breadcrumbs],
      userActions: [...this.userActions],
      networkStatus: navigator.onLine ? 'online' : 'offline',
      ...context
    };

    // Add performance context if available
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      baseContext.memoryUsage = memory.usedJSHeapSize;
    }

    // Add connection info if available
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      baseContext.connectionType = connection.effectiveType;
    }

    // Add build info
    baseContext.buildVersion = process.env.REACT_APP_VERSION || 'unknown';
    baseContext.reactVersion = React.version;

    return baseContext;
  }

  private determineSeverity(error: Error, context: ErrorContext): 'low' | 'medium' | 'high' | 'critical' {
    // Critical errors
    if (error.name === 'ChunkLoadError' || error.message.includes('Loading chunk')) {
      return 'critical';
    }
    
    if (error.name === 'SecurityError' || error.message.includes('Permission denied')) {
      return 'critical';
    }

    // High severity errors
    if (context.componentName === 'ChatInterface' || context.componentName === 'MessageList') {
      return 'high';
    }
    
    if (error.name === 'TypeError' && error.message.includes('Cannot read property')) {
      return 'high';
    }

    // Medium severity errors
    if (error.name === 'NetworkError' || context.componentName === 'NetworkRequest') {
      return 'medium';
    }

    // Default to low
    return 'low';
  }

  private generateFingerprint(error: Error): string {
    // Create a fingerprint based on error name, message, and stack trace
    const key = `${error.name}:${error.message}:${error.stack?.split('\n')[1] || ''}`;
    
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      const char = key.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(36);
  }

  private sanitizeStackTrace(stack?: string): string | undefined {
    if (!stack) return undefined;
    
    // Limit stack trace length
    if (stack.length > this.config.maxStackTraceLength) {
      return stack.substring(0, this.config.maxStackTraceLength) + '\n... (truncated)';
    }
    
    return stack;
  }

  private shouldSample(): boolean {
    return Math.random() <= this.config.sampleRate;
  }

  private storeErrorReport(report: ErrorReport): void {
    if (typeof localStorage === 'undefined') return;

    try {
      const existing = JSON.parse(localStorage.getItem('error_reports') || '[]');
      existing.push(report);
      
      // Keep only last 100 reports
      const trimmed = existing.slice(-100);
      
      localStorage.setItem('error_reports', JSON.stringify(trimmed));
    } catch (error) {
      console.warn('Failed to store error report locally:', error);
    }
  }

  private async sendToEndpoint(report: ErrorReport): Promise<void> {
    if (!this.config.endpoint) return;

    try {
      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify({
          ...report,
          environment: this.config.environment,
          release: this.config.release,
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.warn('Failed to send error report to endpoint:', error);
    }
  }

  public getStoredReports(): ErrorReport[] {
    if (typeof localStorage === 'undefined') return [];

    try {
      return JSON.parse(localStorage.getItem('error_reports') || '[]');
    } catch {
      return [];
    }
  }

  public clearStoredReports(): void {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('error_reports');
    }
  }

  public setUser(userId: string, userData?: Record<string, any>): void {
    getTelemetryService().setUserId(userId);
    
    this.addBreadcrumb({
      category: 'custom',
      message: `User identified: ${userId}`,
      level: 'info',
      data: userData
    });
  }

  public setTag(key: string, value: string): void {
    // Tags will be included in the next error context
    this.addBreadcrumb({
      category: 'custom',
      message: `Tag set: ${key}=${value}`,
      level: 'debug',
      data: { tag: key, value }
    });
  }

  public setContext(key: string, context: Record<string, any>): void {
    this.addBreadcrumb({
      category: 'custom',
      message: `Context set: ${key}`,
      level: 'debug',
      data: { contextKey: key, context }
    });
  }

  public clearBreadcrumbs(): void {
    this.breadcrumbs = [];
  }

  public getStats(): {
    breadcrumbCount: number;
    userActionCount: number;
    storedReportCount: number;
    sessionId: string;
    isInitialized: boolean;
  } {
    return {
      breadcrumbCount: this.breadcrumbs.length,
      userActionCount: this.userActions.length,
      storedReportCount: this.getStoredReports().length,
      sessionId: this.sessionId,
      isInitialized: this.isInitialized,
    };
  }

  public destroy(): void {
    this.breadcrumbs = [];
    this.userActions = [];
    this.isInitialized = false;
  }
}

// Singleton instance
let errorTrackerInstance: ErrorTracker | null = null;

export const getErrorTracker = (config?: Partial<ErrorTrackingConfig>): ErrorTracker => {
  if (!errorTrackerInstance) {
    errorTrackerInstance = new ErrorTracker(config);
  }
  return errorTrackerInstance;
};

// Convenience functions
export const captureError = (error: Error, context?: Partial<ErrorContext>): string => {
  return getErrorTracker().captureError(error, context);
};

export const addBreadcrumb = (breadcrumb: Omit<Breadcrumb, 'timestamp'>): void => {
  getErrorTracker().addBreadcrumb(breadcrumb);
};

export const setUser = (userId: string, userData?: Record<string, any>): void => {
  getErrorTracker().setUser(userId, userData);
};

export const setTag = (key: string, value: string): void => {
  getErrorTracker().setTag(key, value);
};

export const setContext = (key: string, context: Record<string, any>): void => {
  getErrorTracker().setContext(key, context);
};

export default ErrorTracker;