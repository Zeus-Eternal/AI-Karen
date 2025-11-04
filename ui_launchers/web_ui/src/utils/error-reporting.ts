/**
 * Error Reporting and Logging System
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
  sampleRate: number; // 0..1
  beforeSend?: (report: ErrorReport) => ErrorReport | null;
}

type ReactErrorInfoLike = { componentStack?: string };

function safeNowISO() {
  try {
    return new Date().toISOString();
  } catch {
    return '' + Date.now();
  }
}

function coerceError(err: unknown): Error {
  if (err instanceof Error) return err;
  if (typeof err === 'string') return new Error(err);
  try {
    return new Error(JSON.stringify(err));
  } catch {
    return new Error(String(err));
  }
}

function getEnvNodeEnv(): string | undefined {
  try {
    // Bundlers often inline this; guards keep SSR/tools happy.
    // @ts-ignore
    return typeof process !== 'undefined' ? process.env?.NODE_ENV : undefined;
  } catch {
    return undefined;
  }
}

class ErrorReportingService {
  private config: ErrorReportingConfig;
  private breadcrumbs: ErrorBreadcrumb[] = [];
  private sessionId: string;
  private consolePatched = false;
  private fetchPatched = false;
  private xhrPatched = false;
  private listenersBound = false;

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

  public updateConfig(newConfig: Partial<ErrorReportingConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  private generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
  }

  private initializeBreadcrumbCapture() {
    if (!this.config.enabled) return;
    if (typeof window === 'undefined' || typeof document === 'undefined') return;

    if (this.config.enableConsoleCapture && !this.consolePatched) {
      this.captureConsoleErrors();
      this.consolePatched = true;
    }
    if (this.config.enableNetworkCapture && !this.fetchPatched && !this.xhrPatched) {
      this.captureNetworkErrors();
      this.fetchPatched = true;
      this.xhrPatched = true;
    }
    if (this.config.enableUserInteractionCapture && !this.listenersBound) {
      this.captureUserInteractions();
      this.listenersBound = true;
    }
    this.captureNavigationEvents();
  }

  private captureConsoleErrors() {
    try {
      const originalError = console.error.bind(console);
      const originalWarn = console.warn.bind(console);

      console.error = (...args: any[]) => {
        try {
          this.addBreadcrumb({
            category: 'console',
            message: args.map(a => (typeof a === 'string' ? a : JSON.stringify(a))).join(' '),
            level: 'error',
            data: { arguments: args },
          });
        } catch {
          // swallow
        } finally {
          originalError(...args);
        }
      };

      console.warn = (...args: any[]) => {
        try {
          this.addBreadcrumb({
            category: 'console',
            message: args.map(a => (typeof a === 'string' ? a : JSON.stringify(a))).join(' '),
            level: 'warning',
            data: { arguments: args },
          });
        } catch {
          // swallow
        } finally {
          originalWarn(...args);
        }
      };
    } catch {
      // noop
    }
  }

  private captureNetworkErrors() {
    if (typeof window === 'undefined') return;

    // Patch fetch
    if (typeof window.fetch === 'function') {
      const originalFetch = window.fetch.bind(window);
      const self = this;
      window.fetch = async (...args: Parameters<typeof fetch>) => {
        const startTime = Date.now();
        try {
          const response = await originalFetch(...args);
          const duration = Date.now() - startTime;
          try {
            self.addBreadcrumb({
              category: 'http',
              message: `${response.status} ${String(args[0])}`,
              level: response.ok ? 'info' : 'error',
              data: {
                url: String(args[0]),
                status: response.status,
                duration,
                method: (args[1] as RequestInit | undefined)?.method || 'GET',
              },
            });
          } catch {
            // swallow
          }
          return response;
        } catch (error) {
          const duration = Date.now() - startTime;
          try {
            self.addBreadcrumb({
              category: 'http',
              message: `Network error: ${String(args[0])}`,
              level: 'error',
              data: {
                url: String(args[0]),
                error: error instanceof Error ? error.message : String(error),
                duration,
                method: (args[1] as RequestInit | undefined)?.method || 'GET',
              },
            });
          } catch {
            // swallow
          }
          throw error;
        }
      };
    }

    // Patch XHR
    if (typeof XMLHttpRequest !== 'undefined') {
      const originalXHROpen = XMLHttpRequest.prototype.open;
      const originalXHRSend = XMLHttpRequest.prototype.send;
      const self = this;

      XMLHttpRequest.prototype.open = function (
        method: string,
        url: string | URL,
        async: boolean = true,
        username?: string | null,
        password?: string | null
      ) {
        (this as any)._errorReportingData = { method, url: String(url), startTime: Date.now() };
        return originalXHROpen.call(this, method, url, async, username as any, password as any);
      };

      XMLHttpRequest.prototype.send = function (body?: Document | XMLHttpRequestBodyInit | null) {
        const xhr = this as XMLHttpRequest & { _errorReportingData?: any };
        const data = xhr._errorReportingData;
        const done = (statusLabel: 'info' | 'error') => {
          try {
            if (data) {
              const duration = Date.now() - data.startTime;
              self.addBreadcrumb({
                category: 'http',
                message: `${xhr.status} ${data.url}`,
                level: statusLabel,
                data: {
                  url: data.url,
                  status: xhr.status,
                  duration,
                  method: data.method,
                },
              });
            }
          } catch {
            // swallow
          }
        };

        xhr.addEventListener('load', () => {
          done(xhr.status >= 400 ? 'error' : 'info');
        });
        xhr.addEventListener('error', () => {
          try {
            if (data) {
              const duration = Date.now() - data.startTime;
              self.addBreadcrumb({
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
          } catch {
            // swallow
          }
        });

        return originalXHRSend.call(this, body as any);
      };
    }
  }

  private captureUserInteractions() {
    if (typeof document === 'undefined') return;

    // Click events
    document.addEventListener(
      'click',
      (event) => {
        try {
          const target = event.target as Element | null;
          if (!target) return;
          const tagName = target.tagName.toLowerCase();
          const className = (target as HTMLElement).className || '';
          const id = (target as HTMLElement).id || '';
          // Avoid leaking sensitive input values
          const isSensitiveInput =
            tagName === 'input' &&
            ['password', 'email'].includes(((target as HTMLInputElement).type || '').toLowerCase());

          this.addBreadcrumb({
            category: 'user',
            message: `Clicked ${tagName}${id ? `#${id}` : ''}${className ? `.${String(className).split(' ').join('.')}` : ''}`,
            level: 'info',
            data: {
              tagName,
              className,
              id,
              innerText: isSensitiveInput ? undefined : (target.textContent || '').slice(0, 100),
            },
          });
        } catch {
          // swallow
        }
      },
      { passive: true }
    );

    // Form submissions
    document.addEventListener(
      'submit',
      (event) => {
        try {
          const target = event.target as HTMLFormElement | null;
          if (!target) return;
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
        } catch {
          // swallow
        }
      },
      { passive: true }
    );
  }

  private captureNavigationEvents() {
    if (typeof window === 'undefined') return;

    try {
      // Initial load
      this.addBreadcrumb({
        category: 'navigation',
        message: `Page loaded: ${window.location.pathname}`,
        level: 'info',
        data: {
          pathname: window.location.pathname,
          search: window.location.search,
          hash: window.location.hash,
          referrer: typeof document !== 'undefined' ? document.referrer : undefined,
        },
      });

      // History navigation
      window.addEventListener('popstate', () => {
        try {
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
        } catch {
          // swallow
        }
      });
    } catch {
      // noop
    }
  }

  public addBreadcrumb(breadcrumb: Omit<ErrorBreadcrumb, 'timestamp'>) {
    if (!this.config.enabled) return;
    const fullBreadcrumb: ErrorBreadcrumb = {
      ...breadcrumb,
      timestamp: safeNowISO(),
    };
    this.breadcrumbs.push(fullBreadcrumb);
    // Keep only the most recent breadcrumbs
    if (this.breadcrumbs.length > this.config.maxBreadcrumbs) {
      this.breadcrumbs = this.breadcrumbs.slice(-this.config.maxBreadcrumbs);
    }
  }

  public async reportError(
    rawError: unknown,
    errorInfo?: ReactErrorInfoLike,
    context?: {
      section?: string;
      retryCount?: number;
      userId?: string;
      [key: string]: any;
    }
  ): Promise<void> {
    if (!this.config.enabled) return;
    // Sampling
    if (Math.random() > this.config.sampleRate) return;

    const error = coerceError(rawError);

    const errorReport: ErrorReport = {
      id: `error-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo?.componentStack || undefined,
      section: context?.section,
      timestamp: safeNowISO(),
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

    // beforeSend hook
    const processedReport = this.config.beforeSend ? this.config.beforeSend(errorReport) : errorReport;
    if (!processedReport) return;

    try {
      if (this.config.endpoint) {
        await this.sendToService(processedReport);
      }
    } catch {
      // swallow remote failure
    }

    try {
      this.sendToAnalytics(processedReport);
    } catch {
      // swallow analytics failure
    }

    try {
      this.storeLocally(processedReport);
    } catch {
      // localStorage can fail (quota/private mode)
    }
  }

  private determineSeverity(error: Error, context?: any): ErrorReport['severity'] {
    const message = (error.message || '').toLowerCase();
    const stack = (error.stack || '').toLowerCase();

    // Critical indicators
    if (
      message.includes('chunk') ||
      message.includes('loading') ||
      message.includes('network') ||
      context?.section === 'global'
    ) {
      return 'critical';
    }

    // High severity indicators
    if (
      message.includes('auth') ||
      message.includes('permission') ||
      message.includes('security') ||
      stack.includes('boundary')
    ) {
      return 'high';
    }

    // Medium severity indicators
    if (message.includes('validation') || message.includes('form') || (context?.retryCount ?? 0) > 2) {
      return 'medium';
    }

    return 'low';
  }

  private categorizeError(error: Error): ErrorReport['category'] {
    const message = (error.message || '').toLowerCase();
    const name = (error.name || '').toLowerCase();

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
    if (typeof fetch !== 'function') return;
    if (!this.config.endpoint || !this.config.apiKey) return;

    const controller = typeof AbortController !== 'undefined' ? new AbortController() : undefined;
    const id = controller ? setTimeout(() => controller.abort(), 8000) : undefined;

    const resp = await fetch(this.config.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`,
      } as Record<string, string>,
      body: JSON.stringify(report),
      signal: controller?.signal,
    });

    if (id) clearTimeout(id as any);

    if (!resp.ok) {
      throw new Error(`Failed to send error report: ${resp.status}`);
    }
  }

  private sendToAnalytics(report: ErrorReport): void {
    if (typeof window === 'undefined') return;

    // Google Analytics (gtag)
    const gtag = (window as any).gtag;
    if (typeof gtag === 'function') {
      gtag('event', 'exception', {
        description: `${report.section || 'Unknown'}: ${report.message}`,
        fatal: report.severity === 'critical',
        error_id: report.id,
        section: report.section,
        category: report.category,
        severity: report.severity,
        retry_count: report.retryCount,
      });
    }
    // Hook other analytics here as needed (Mixpanel, Segment, etc.)
  }

  private storeLocally(report: ErrorReport): void {
    if (typeof localStorage === 'undefined') return;
    const key = 'error_reports';
    const stored = localStorage.getItem(key);
    const reports: ErrorReport[] = stored ? JSON.parse(stored) : [];
    reports.push(report);
    const recentReports = reports.slice(-10);
    localStorage.setItem(key, JSON.stringify(recentReports));
  }

  public getStoredReports(): ErrorReport[] {
    try {
      if (typeof localStorage === 'undefined') return [];
      const stored = localStorage.getItem('error_reports');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  public clearStoredReports(): void {
    try {
      if (typeof localStorage === 'undefined') return;
      localStorage.removeItem('error_reports');
    } catch {
      // noop
    }
  }
}

// Singleton instance
const nodeEnv = getEnvNodeEnv();
const isProd = nodeEnv === 'production';

export const errorReportingService = new ErrorReportingService({
  enabled: isProd ?? true,
  sampleRate: nodeEnv === 'development' ? 1.0 : 0.1,
  beforeSend: (report) => {
    // Scrub obvious secrets
    if (report.context) {
      delete (report.context as any).password;
      delete (report.context as any).token;
      delete (report.context as any).apiKey;
      delete (report.context as any).authorization;
    }
    // Truncate overly long messages to keep payloads lean
    if (report.message && report.message.length > 2000) {
      report.message = report.message.slice(0, 2000) + '…';
    }
    return report;
  },
});

// Global hooks (browser only)
if (typeof window !== 'undefined') {
  // Unhandled Promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    try {
      const reason = (event as PromiseRejectionEvent).reason;
      const err = coerceError(reason);
      errorReportingService.reportError(err, undefined, { section: 'global', category: 'promise' });
    } catch {
      // swallow
    }
  });

  // Global errors
  window.addEventListener('error', (event: Event) => {
    try {
      const e = event as ErrorEvent;
      const err = e.error ? coerceError(e.error) : new Error(e.message || 'Unknown error');
      errorReportingService.reportError(err, undefined, {
        section: 'global',
        category: 'global',
        filename: (e as any).filename,
        lineno: (e as any).lineno,
        colno: (e as any).colno,
      });
    } catch {
      // swallow
    }
  });
}

export default errorReportingService;
