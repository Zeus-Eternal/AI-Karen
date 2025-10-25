/**
 * Error Reporting and Logging System
 * 
 * Provides comprehensive error reporting, logging, and monitoring capabilities
 * for the modern error boundary system.
 */

export interface ErrorReport {
  id: string;
  message: string;
  stack?: string;
  componentStack?: string;
  section?: string;
  timestamp: string;
  url?: string;
  userAgent?: string;
  userId?: string;
  sessionId?: string;
  retryCount: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: 'ui' | 'network' | 'server' | 'database' | 'auth' | 'unknown';
  context?: Record<string, any>;
  breadcrumbs?: ErrorBreadcrumb[];
}

export interface ErrorBreadcrumb {
  timestamp: string;
  category: 'navigation' | 'user' | 'http' | 'console' | 'dom';
  message: string;
  level: 'info' | 'warning' | 'error';
  data?: Record<string, any>;
}

export interface ErrorReportingConfig {
  enabled: boolean;
  endpoint?: string;
  apiKey?: string;
  maxBreadcrumbs: number;
  enableConsoleCapture: boolean;
  enableNetworkCapture: boolean;
  enableUserInteractionCapture: boolean;
  sampleRate: number;
  beforeSend?: (report: ErrorReport) => ErrorReport | null;
}

class ErrorReportingService {
  private config: ErrorReportingConfig;
  private breadcrumbs: ErrorBreadcrumb[] = [];
  private sessionId: string;

  constructor(config: Partial<ErrorReportingConfig> = {}) {
    this.config = {
      enabled: true,
      maxBreadcrumbs: 50,
      enableConsoleCapture: true,
      enableNetworkCapture: true,
      enableUserInteractionCapture: true,
      sampleRate: 1.0,
      ...config,
    };

    this.sessionId = this.generateSessionId();
    this.initializeBreadcrumbCapture();
  }

  private generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private initializeBreadcrumbCapture() {
    if (!this.config.enabled) return;

    // Capture console errors
    if (this.config.enableConsoleCapture) {
      this.captureConsoleErrors();
    }

    // Capture network errors
    if (this.config.enableNetworkCapture) {
      this.captureNetworkErrors();
    }

    // Capture user interactions
    if (this.config.enableUserInteractionCapture) {
      this.captureUserInteractions();
    }

    // Capture navigation events
    this.captureNavigationEvents();
  }

  private captureConsoleErrors() {
    const originalError = console.error;
    console.error = (...args) => {
      this.addBreadcrumb({
        category: 'console',
        message: args.join(' '),
        level: 'error',
        data: { arguments: args },
      });
      originalError.apply(console, args);
    };

    const originalWarn = console.warn;
    console.warn = (...args) => {
      this.addBreadcrumb({
        category: 'console',
        message: args.join(' '),
        level: 'warning',
        data: { arguments: args },
      });
      originalWarn.apply(console, args);
    };
  }

  private captureNetworkErrors() {
    // Capture fetch errors
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const startTime = Date.now();
      try {
        const response = await originalFetch(...args);
        const duration = Date.now() - startTime;

        this.addBreadcrumb({
          category: 'http',
          message: `${response.status} ${args[0]}`,
          level: response.ok ? 'info' : 'error',
          data: {
            url: args[0],
            status: response.status,
            duration,
            method: args[1]?.method || 'GET',
          },
        });

        return response;
      } catch (error) {
        const duration = Date.now() - startTime;
        this.addBreadcrumb({
          category: 'http',
          message: `Network error: ${args[0]}`,
          level: 'error',
          data: {
            url: args[0],
            error: error instanceof Error ? error.message : String(error),
            duration,
            method: args[1]?.method || 'GET',
          },
        });
        throw error;
      }
    };

    // Capture XMLHttpRequest errors
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method: string, url: string | URL, async: boolean = true, username?: string | null, password?: string | null) {
      (this as any)._errorReportingData = { method, url, startTime: Date.now() };
      return originalXHROpen.call(this, method, url, async, username, password);
    };

    XMLHttpRequest.prototype.send = function(body?: Document | XMLHttpRequestBodyInit | null) {
      const xhr = this;
      const data = (xhr as any)._errorReportingData;

      xhr.addEventListener('load', () => {
        if (data) {
          const duration = Date.now() - data.startTime;
          errorReportingService.addBreadcrumb({
            category: 'http',
            message: `${xhr.status} ${data.url}`,
            level: xhr.status >= 400 ? 'error' : 'info',
            data: {
              url: data.url,
              status: xhr.status,
              duration,
              method: data.method,
            },
          });
        }
      });

      xhr.addEventListener('error', () => {
        if (data) {
          const duration = Date.now() - data.startTime;
          errorReportingService.addBreadcrumb({
            category: 'http',
            message: `Network error: ${data.url}`,
            level: 'error',
            data: {
              url: data.url,
              error: 'Network error',
              duration,
              method: data.method,
            },
          });
        }
      });

      return originalXHRSend.call(this, body);
    };
  }

  private captureUserInteractions() {
    // Capture click events
    document.addEventListener('click', (event) => {
      const target = event.target as Element;
      const tagName = target.tagName.toLowerCase();
      const className = target.className;
      const id = target.id;

      this.addBreadcrumb({
        category: 'user',
        message: `Clicked ${tagName}${id ? `#${id}` : ''}${className ? `.${className}` : ''}`,
        level: 'info',
        data: {
          tagName,
          className,
          id,
          innerText: target.textContent?.slice(0, 100),
        },
      });
    });

    // Capture form submissions
    document.addEventListener('submit', (event) => {
      const target = event.target as HTMLFormElement;
      this.addBreadcrumb({
        category: 'user',
        message: `Form submitted: ${target.action || 'current page'}`,
        level: 'info',
        data: {
          action: target.action,
          method: target.method,
          formId: target.id,
        },
      });
    });
  }

  private captureNavigationEvents() {
    // Capture page navigation
    window.addEventListener('popstate', () => {
      this.addBreadcrumb({
        category: 'navigation',
        message: `Navigated to ${window.location.pathname}`,
        level: 'info',
        data: {
          pathname: window.location.pathname,
          search: window.location.search,
          hash: window.location.hash,
        },
      });
    });

    // Capture initial page load
    this.addBreadcrumb({
      category: 'navigation',
      message: `Page loaded: ${window.location.pathname}`,
      level: 'info',
      data: {
        pathname: window.location.pathname,
        search: window.location.search,
        hash: window.location.hash,
        referrer: document.referrer,
      },
    });
  }

  public addBreadcrumb(breadcrumb: Omit<ErrorBreadcrumb, 'timestamp'>) {
    if (!this.config.enabled) return;

    const fullBreadcrumb: ErrorBreadcrumb = {
      ...breadcrumb,
      timestamp: new Date().toISOString(),
    };

    this.breadcrumbs.push(fullBreadcrumb);

    // Keep only the most recent breadcrumbs
    if (this.breadcrumbs.length > this.config.maxBreadcrumbs) {
      this.breadcrumbs = this.breadcrumbs.slice(-this.config.maxBreadcrumbs);
    }
  }

  public async reportError(
    error: Error,
    errorInfo?: React.ErrorInfo,
    context?: {
      section?: string;
      retryCount?: number;
      userId?: string;
      [key: string]: any;
    }
  ): Promise<void> {
    if (!this.config.enabled) return;

    // Apply sampling rate
    if (Math.random() > this.config.sampleRate) return;

    const errorReport: ErrorReport = {
      id: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo?.componentStack || undefined,
      section: context?.section,
      timestamp: new Date().toISOString(),
      url: typeof window !== 'undefined' ? window.location.href : undefined,
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
      userId: context?.userId,
      sessionId: this.sessionId,
      retryCount: context?.retryCount || 0,
      severity: this.determineSeverity(error, context),
      category: this.categorizeError(error),
      context: context ? { ...context } : undefined,
      breadcrumbs: [...this.breadcrumbs],
    };

    // Apply beforeSend hook
    const processedReport = this.config.beforeSend ? this.config.beforeSend(errorReport) : errorReport;
    if (!processedReport) return;

    try {
      // Log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.group('🚨 Error Report');
        console.error('Error:', error);
        console.log('Report:', processedReport);
        console.groupEnd();
      }

      // Send to external service
      if (this.config.endpoint) {
        await this.sendToService(processedReport);
      }

      // Send to analytics
      this.sendToAnalytics(processedReport);

      // Store locally for offline support
      this.storeLocally(processedReport);

    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  }

  private determineSeverity(error: Error, context?: any): ErrorReport['severity'] {
    const message = error.message.toLowerCase();
    const stack = error.stack?.toLowerCase() || '';

    // Critical errors
    if (
      message.includes('chunk') ||
      message.includes('loading') ||
      message.includes('network') ||
      context?.section === 'global'
    ) {
      return 'critical';
    }

    // High severity errors
    if (
      message.includes('auth') ||
      message.includes('permission') ||
      message.includes('security') ||
      stack.includes('boundary')
    ) {
      return 'high';
    }

    // Medium severity errors
    if (
      message.includes('validation') ||
      message.includes('form') ||
      context?.retryCount > 2
    ) {
      return 'medium';
    }

    return 'low';
  }

  private categorizeError(error: Error): ErrorReport['category'] {
    const message = error.message.toLowerCase();
    const name = error.name.toLowerCase();

    if (message.includes('network') || message.includes('fetch') || name.includes('network')) {
      return 'network';
    }

    if (message.includes('server') || message.includes('500') || message.includes('502')) {
      return 'server';
    }

    if (message.includes('database') || message.includes('sql') || message.includes('query')) {
      return 'database';
    }

    if (message.includes('auth') || message.includes('token') || message.includes('401')) {
      return 'auth';
    }

    if (name.includes('type') || name.includes('reference') || name.includes('syntax')) {
      return 'ui';
    }

    return 'unknown';
  }

  private async sendToService(report: ErrorReport): Promise<void> {
    if (!this.config.endpoint || !this.config.apiKey) return;

    const response = await fetch(this.config.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config.apiKey}`,
      },
      body: JSON.stringify(report),
    });

    if (!response.ok) {
      throw new Error(`Failed to send error report: ${response.status}`);
    }
  }

  private sendToAnalytics(report: ErrorReport): void {
    // Send to Google Analytics if available
    if (typeof window !== 'undefined' && 'gtag' in window) {
      (window as any).gtag('event', 'exception', {
        description: `${report.section || 'Unknown'}: ${report.message}`,
        fatal: report.severity === 'critical',
        custom_map: {
          error_id: report.id,
          section: report.section,
          category: report.category,
          severity: report.severity,
          retry_count: report.retryCount,
        },
      });
    }

    // Send to other analytics services as needed
  }

  private storeLocally(report: ErrorReport): void {
    try {
      const key = `error_reports`;
      const stored = localStorage.getItem(key);
      const reports = stored ? JSON.parse(stored) : [];
      
      reports.push(report);
      
      // Keep only the most recent 10 reports
      const recentReports = reports.slice(-10);
      
      localStorage.setItem(key, JSON.stringify(recentReports));
    } catch (error) {
      console.warn('Failed to store error report locally:', error);
    }
  }

  public getStoredReports(): ErrorReport[] {
    try {
      const stored = localStorage.getItem('error_reports');
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.warn('Failed to retrieve stored error reports:', error);
      return [];
    }
  }

  public clearStoredReports(): void {
    try {
      localStorage.removeItem('error_reports');
    } catch (error) {
      console.warn('Failed to clear stored error reports:', error);
    }
  }

  public updateConfig(newConfig: Partial<ErrorReportingConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

// Create singleton instance
export const errorReportingService = new ErrorReportingService({
  enabled: process.env.NODE_ENV === 'production',
  sampleRate: process.env.NODE_ENV === 'development' ? 1.0 : 0.1,
  beforeSend: (report) => {
    // Filter out sensitive information
    if (report.context) {
      delete report.context.password;
      delete report.context.token;
      delete report.context.apiKey;
    }
    return report;
  },
});

// Initialize error reporting
if (typeof window !== 'undefined') {
  // Capture unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    errorReportingService.reportError(
      new Error(`Unhandled Promise Rejection: ${event.reason}`),
      undefined,
      { section: 'global', category: 'promise' }
    );
  });

  // Capture global errors
  window.addEventListener('error', (event) => {
    errorReportingService.reportError(
      event.error || new Error(event.message),
      undefined,
      { 
        section: 'global', 
        category: 'global',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      }
    );
  });
}

export default errorReportingService;