import type { ErrorInfo } from 'react';

export interface ErrorAnalyticsConfig {
  enabled: boolean;
  section: string;
  sampleRate?: number;
  enableTrendAnalysis?: boolean;
  enablePerformanceTracking?: boolean;
  maxStoredErrors?: number;
}

export interface ErrorMetrics {
  errorId: string;
  timestamp: number;
  errorMessage: string;
  errorType: string;
  section: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: 'ui' | 'network' | 'server' | 'database' | 'auth' | 'unknown';
  userAgent: string;
  url: string;
  userId?: string;
  sessionId: string;
  recoveryAttempts: number;
  resolved: boolean;
  resolutionTime?: number;
  context: Record<string, any>;
  performanceMetrics?: PerformanceMetrics;
  breadcrumbs: ErrorBreadcrumb[];
}

export interface PerformanceMetrics {
  memoryUsage?: number;
  renderTime?: number;
  networkLatency?: number;
  bundleSize?: number;
  componentCount?: number;
}

export interface ErrorBreadcrumb {
  timestamp: number;
  category: 'navigation' | 'user' | 'http' | 'console' | 'dom';
  message: string;
  level: 'info' | 'warning' | 'error';
  data?: Record<string, any>;
}

export interface ErrorTrend {
  period: string;
  errorCount: number;
  uniqueErrors: number;
  resolutionRate: number;
}

export interface ErrorAnalyticsReport {
  summary: {
    totalErrors: number;
    uniqueErrors: number;
    resolutionRate: number;
    averageResolutionTime: number;
    criticalErrors: number;
  };
  trends: ErrorTrend[];
  topErrors: Array<{
    message: string;
    count: number;
    lastOccurrence: number;
    severity: string;
    category: string;
    section?: string;
  }>;
  sectionBreakdown: Record<string, { count: number; resolutionRate: number }>;
  performanceImpact: {
    averageMemoryIncrease: number;
    averageRenderDelay: number;
    networkErrorRate: number;
  };
}

export class ErrorAnalytics {
  private config: ErrorAnalyticsConfig;
  private errorMetrics: Map<string, ErrorMetrics> = new Map();
  private trendData: ErrorTrend[] = [];
  private performanceBaseline: PerformanceMetrics | null = null;

  constructor(config: ErrorAnalyticsConfig) {
    this.config = {
      sampleRate: 1.0,
      enableTrendAnalysis: true,
      enablePerformanceTracking: true,
      maxStoredErrors: 1000,
      ...config
    };
    this.initializePerformanceBaseline();
    this.startTrendAnalysis();
  }

  private initializePerformanceBaseline() {
    if (!this.config.enablePerformanceTracking) return;

    // Fallback to zero if performance APIs are not available
    try {
      this.performanceBaseline = {
        memoryUsage: this.getCurrentMemoryUsage(),
        renderTime: this.measureRenderTime(),
        networkLatency: this.getAverageNetworkLatency(),
        bundleSize: this.getBundleSize(),
        componentCount: this.getComponentCount()
      };
    } catch (error) {
      this.performanceBaseline = null; // Handle gracefully if performance API is unavailable
    }
  }

  private startTrendAnalysis() {
    if (!this.config.enableTrendAnalysis) return;

    // Update trends every hour
    setInterval(() => {
      this.updateTrends();
    }, 60 * 60 * 1000); // Every hour
  }

  public trackError(
    error: Error,
    errorInfo: ErrorInfo,
    context: {
      section?: string;
      level?: string;
      recoveryAttempts?: number;
      userId?: string;
      [key: string]: any;
    } = {}
  ) {
    if (!this.config.enabled) return;

    // Apply sampling rate
    if (Math.random() > (this.config.sampleRate || 1.0)) return;

    const errorId = this.generateErrorId(error, errorInfo);
    const timestamp = Date.now();
    const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown';
    const currentUrl = typeof window !== 'undefined' ? window.location.href : 'unknown';
    const metrics: ErrorMetrics = {
      errorId,
      timestamp,
      errorMessage: error.message,
      errorType: error.name,
      section: context.section || this.config.section,
      severity: this.determineSeverity(error, context),
      category: this.categorizeError(error),
      userAgent,
      url: currentUrl,
      userId: context.userId,
      sessionId: this.getSessionId(),
      recoveryAttempts: context.recoveryAttempts || 0,
      resolved: false,
      context: { ...context },
      performanceMetrics: this.config.enablePerformanceTracking 
        ? this.capturePerformanceMetrics() 
        : undefined,
      breadcrumbs: this.getBreadcrumbs()
    };

    this.errorMetrics.set(errorId, metrics);

    // Cleanup old errors if we exceed the limit
    this.cleanupOldErrors();
    
    // Send to analytics services
    this.sendToAnalyticsServices(metrics);

    // Update trends immediately for critical errors
    if (metrics.severity === 'critical') {
      this.updateTrends();
    }
  }

  private generateErrorId(error: Error, errorInfo: ErrorInfo): string {
    const message = error.message.replace(/[^a-zA-Z0-9]/g, '');
    const componentStack = errorInfo.componentStack ?? '';
    const component = componentStack.split('\n')[1]?.trim() || 'unknown';
    const hash = this.simpleHash(`${message}-${component}`);
    return `error-${hash}-${Date.now()}`;
  }

  private simpleHash(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }

  private determineSeverity(error: Error, context: any): ErrorMetrics['severity'] {
    const message = error.message.toLowerCase();
    const name = error.name.toLowerCase();

    if (context.level === 'global' || message.includes('chunk') || message.includes('loading') || name.includes('chunkloaderror') || context.recoveryAttempts >= 3) {
      return 'critical';
    }

    if (context.level === 'feature' || message.includes('network') || message.includes('auth') || message.includes('permission') || context.recoveryAttempts >= 2) {
      return 'high';
    }

    if (message.includes('render') || message.includes('hook') || message.includes('validation') || context.recoveryAttempts >= 1) {
      return 'medium';
    }

    return 'low';
  }

  private categorizeError(error: Error): ErrorMetrics['category'] {
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

  private capturePerformanceMetrics(): PerformanceMetrics {
    return {
      memoryUsage: this.getCurrentMemoryUsage(),
      renderTime: this.measureRenderTime(),
      networkLatency: this.getAverageNetworkLatency(),
      bundleSize: this.getBundleSize(),
      componentCount: this.getComponentCount()
    };
  }

  private getCurrentMemoryUsage(): number {
    if (typeof performance === 'undefined') {
      return 0;
    }

    if ('memory' in performance) {
      return (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize ?? 0;
    }
    return 0;
  }

  private measureRenderTime(): number {
    if (typeof performance === 'undefined') {
      return 0;
    }
    const paintEntries = performance.getEntriesByType('paint');
    if (paintEntries.length > 0) {
      const lastPaint = paintEntries[paintEntries.length - 1];
      return performance.now() - lastPaint.startTime;
    }
    return 0;
  }

  private getAverageNetworkLatency(): number {
    if (typeof performance === 'undefined') {
      return 0;
    }
    const navigationEntries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];
    if (navigationEntries.length > 0) {
      const nav = navigationEntries[0];
      return nav.responseEnd - nav.requestStart;
    }
    return 0;
  }

  private getBundleSize(): number {
    if (typeof performance === 'undefined') {
      return 0;
    }
    const resourceEntries = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
    return resourceEntries
      .filter(entry => entry.name.includes('.js') || entry.name.includes('.css'))
      .reduce((total, entry) => total + (entry.transferSize || 0), 0);
  }

  private getComponentCount(): number {
    if (typeof document === 'undefined') {
      return 0;
    }
    const elements = document.querySelectorAll('*');
    let componentCount = 0;
    elements.forEach(element => {
      const keys = Object.keys(element);
      if (keys.some(key => key.startsWith('__reactFiber') || key.startsWith('__reactInternalInstance'))) {
        componentCount++;
      }
    });
    return componentCount;
  }

  private getBreadcrumbs(): ErrorBreadcrumb[] {
    try {
      if (typeof localStorage === 'undefined') {
        return [];
      }
      const storedReports = localStorage.getItem('error_breadcrumbs');
      if (storedReports) {
        return JSON.parse(storedReports).slice(-10);
      }
    } catch (error) {
    }
    return [];
  }

  private getSessionId(): string {
    if (typeof sessionStorage === 'undefined') {
      return `session-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
    }

    let sessionId = sessionStorage.getItem('analytics_session_id');
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
      sessionStorage.setItem('analytics_session_id', sessionId);
    }
    return sessionId;
  }

  private cleanupOldErrors() {
    if (this.errorMetrics.size <= (this.config.maxStoredErrors || 1000)) return;
    const sortedErrors = Array.from(this.errorMetrics.entries())
      .sort(([, a], [, b]) => a.timestamp - b.timestamp);
    const toRemove = sortedErrors.slice(0, sortedErrors.length - (this.config.maxStoredErrors || 1000));
    toRemove.forEach(([errorId]) => {
      this.errorMetrics.delete(errorId);
    });
  }

  private sendToAnalyticsServices(metrics: ErrorMetrics) {
    if (typeof window !== 'undefined' && 'gtag' in window) {
      (window as any).gtag('event', 'exception', {
        description: `${metrics.section}: ${metrics.errorMessage}`,
        fatal: metrics.severity === 'critical',
        custom_map: {
          error_id: metrics.errorId,
          section: metrics.section,
          category: metrics.category,
          severity: metrics.severity,
          recovery_attempts: metrics.recoveryAttempts,
        },
      });
    }

    if (typeof window === 'undefined') {
      return;
    }

    const analyticsEndpoint = process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT;
    if (analyticsEndpoint) {
      window.fetch(analyticsEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.NEXT_PUBLIC_ANALYTICS_API_KEY}`
        },
        body: JSON.stringify(metrics)
      }).catch(error => {
        console.error('Error sending to analytics service:', error);
      });
    }
  }

  private updateTrends() {
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;
    const oneDayAgo = now - (24 * oneHour);

    const recentErrors = Array.from(this.errorMetrics.values())
      .filter(error => error.timestamp >= oneDayAgo);

    const hourlyData = new Map<string, ErrorMetrics[]>();
    recentErrors.forEach(error => {
      const hour = new Date(error.timestamp).toISOString().slice(0, 13);
      if (!hourlyData.has(hour)) {
        hourlyData.set(hour, []);
      }
      hourlyData.get(hour)!.push(error);
    });

    const trends: ErrorTrend[] = Array.from(hourlyData.entries()).map(([period, errors]) => {
      const uniqueErrors = new Set(errors.map(e => e.errorMessage)).size;
      const resolvedErrors = errors.filter(e => e.resolved).length;
      const resolutionTimes = errors
        .filter(e => e.resolved && e.resolutionTime)
        .map(e => e.resolutionTime!);
      const topErrors = this.getTopErrorsForPeriod(errors);

      return {
        period,
        errorCount: errors.length,
        uniqueErrors,
        resolutionRate: errors.length > 0 ? resolvedErrors / errors.length : 0,
        averageResolutionTime: resolutionTimes.length > 0
          ? resolutionTimes.reduce((a, b) => a + b, 0) / resolutionTimes.length
          : 0,
        topErrors
      };
    });

    this.trendData = trends;
  }

  private getTopErrorsForPeriod(errors: ErrorMetrics[]): Array<{
    message: string;
    count: number;
    severity: string;
  }> {
    const errorCounts = new Map<string, { count: number; severity: string }>();
    errors.forEach(error => {
      const key = error.errorMessage;
      if (!errorCounts.has(key)) {
        errorCounts.set(key, { count: 0, severity: error.severity });
      }
      errorCounts.get(key)!.count++;
    });

    return Array.from(errorCounts.entries())
      .map(([message, data]) => ({ message, ...data }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }

  public markErrorResolved(errorId: string, resolutionTime?: number) {
    const error = this.errorMetrics.get(errorId);
    if (error) {
      error.resolved = true;
      error.resolutionTime = resolutionTime || (Date.now() - error.timestamp);
    }
  }

  public getAnalyticsReport(): ErrorAnalyticsReport {
    const allErrors = Array.from(this.errorMetrics.values());
    const resolvedErrors = allErrors.filter(e => e.resolved);
    const criticalErrors = allErrors.filter(e => e.severity === 'critical');

    const errorCounts = new Map<string, {
      count: number;
      lastOccurrence: number;
      severity: string;
      category: string;
    }>();

    allErrors.forEach(error => {
      const key = error.errorMessage;
      if (!errorCounts.has(key)) {
        errorCounts.set(key, {
          count: 0,
          lastOccurrence: error.timestamp,
          severity: error.severity,
          category: error.category
        });
      }
      const data = errorCounts.get(key)!;
      data.count++;
      data.lastOccurrence = Math.max(data.lastOccurrence, error.timestamp);
    });

    const topErrors = Array.from(errorCounts.entries())
      .map(([message, data]) => ({ message, ...data }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    const sectionBreakdown: Record<string, { count: number; resolutionRate: number }> = {};
    allErrors.forEach(error => {
      if (!sectionBreakdown[error.section]) {
        sectionBreakdown[error.section] = { count: 0, resolutionRate: 0 };
      }
      sectionBreakdown[error.section].count++;
    });

    Object.keys(sectionBreakdown).forEach(section => {
      const sectionErrors = allErrors.filter(e => e.section === section);
      const sectionResolved = sectionErrors.filter(e => e.resolved);
      sectionBreakdown[section].resolutionRate =
        sectionErrors.length > 0 ? sectionResolved.length / sectionErrors.length : 0;
    });

    const performanceMetrics = allErrors
      .map(e => e.performanceMetrics)
      .filter(Boolean) as PerformanceMetrics[];

    const performanceImpact = {
      averageMemoryIncrease: this.calculateAverageMemoryIncrease(performanceMetrics),
      averageRenderDelay: this.calculateAverageRenderDelay(performanceMetrics),
      networkErrorRate: this.calculateNetworkErrorRate(allErrors)
    };

    return {
      summary: {
        totalErrors: allErrors.length,
        uniqueErrors: errorCounts.size,
        resolutionRate: allErrors.length > 0 ? resolvedErrors.length / allErrors.length : 0,
        averageResolutionTime: this.calculateAverageResolutionTime(resolvedErrors),
        criticalErrors: criticalErrors.length
      },
      trends: this.trendData,
      topErrors,
      sectionBreakdown,
      performanceImpact
    };
  }

  private calculateAverageMemoryIncrease(metrics: PerformanceMetrics[]): number {
    if (metrics.length === 0 || !this.performanceBaseline) return 0;
    const increases = metrics
      .map(m => (m.memoryUsage || 0) - (this.performanceBaseline!.memoryUsage || 0))
      .filter(increase => increase > 0);
    return increases.length > 0 ? increases.reduce((a, b) => a + b, 0) / increases.length : 0;
  }

  private calculateAverageRenderDelay(metrics: PerformanceMetrics[]): number {
    const renderTimes = metrics.map(m => m.renderTime || 0).filter(t => t > 0);
    return renderTimes.length > 0 ? renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length : 0;
  }

  private calculateNetworkErrorRate(errors: ErrorMetrics[]): number {
    const networkErrors = errors.filter(e => e.category === 'network');
    return errors.length > 0 ? networkErrors.length / errors.length : 0;
  }

  private calculateAverageResolutionTime(resolvedErrors: ErrorMetrics[]): number {
    const resolutionTimes = resolvedErrors
      .map(e => e.resolutionTime || 0)
      .filter(t => t > 0);
    return resolutionTimes.length > 0
      ? resolutionTimes.reduce((a, b) => a + b, 0) / resolutionTimes.length
      : 0;
  }

  public clearAnalytics() {
    this.errorMetrics.clear();
    this.trendData = [];
  }

  public exportAnalytics(): string {
    return JSON.stringify({
      config: this.config,
      metrics: Array.from(this.errorMetrics.entries()),
      trends: this.trendData,
      report: this.getAnalyticsReport()
    }, null, 2);
  }
}

export default ErrorAnalytics;
