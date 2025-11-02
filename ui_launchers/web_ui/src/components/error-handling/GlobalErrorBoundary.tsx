/**
 * Global Error Boundary for Production-Grade Error Handling
 * 
 * Provides comprehensive error handling with graceful degradation,
 * intelligent recovery mechanisms, and detailed error analytics.
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { errorReportingService, ErrorReport } from '../../utils/error-reporting';
import { ErrorRecoveryManager } from '../../lib/error-handling/error-recovery-manager';
import { ErrorAnalytics } from '../../lib/error-handling/error-analytics';
import { ProductionErrorFallback } from './ProductionErrorFallback';
interface Props {
  children: ReactNode;
  fallbackComponent?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo, report: ErrorReport) => void;
  enableRecovery?: boolean;
  enableAnalytics?: boolean;
  section?: string;
  level?: 'global' | 'feature' | 'component';
}
interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorReport: ErrorReport | null;
  recoveryAttempts: number;
  isRecovering: boolean;
  fallbackMode: 'full' | 'degraded' | 'minimal';
}
export interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorReport: ErrorReport | null;
  onRetry: () => void;
  onRecover: () => void;
  onReport: () => void;
  recoveryAttempts: number;
  maxRecoveryAttempts: number;
  fallbackMode: 'full' | 'degraded' | 'minimal';
  isRecovering: boolean;
}
export class GlobalErrorBoundary extends Component<Props, State> {
  private recoveryManager: ErrorRecoveryManager;
  private analytics: ErrorAnalytics;
  private maxRecoveryAttempts = 3;
  private recoveryTimeout: NodeJS.Timeout | null = null;
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorReport: null,
      recoveryAttempts: 0,
      isRecovering: false,
      fallbackMode: 'full'
    };
    this.recoveryManager = new ErrorRecoveryManager({
      maxAttempts: this.maxRecoveryAttempts,
      retryDelay: 1000,
      exponentialBackoff: true,
      section: props.section || 'unknown'
    });
    this.analytics = new ErrorAnalytics({
      enabled: props.enableAnalytics !== false,
      section: props.section || 'unknown'
    });
  }
  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      fallbackMode: 'full'
    };
  }
  async componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Generate comprehensive error report
    const errorReport = await this.generateErrorReport(error, errorInfo);
    // Update state with error details
    this.setState({
      errorInfo,
      errorReport,
      fallbackMode: this.determineFallbackMode(error, errorInfo)
    });
    // Report error to monitoring services
    await this.reportError(error, errorInfo, errorReport);
    // Track error analytics
    this.analytics.trackError(error, errorInfo, {
      section: this.props.section,
      level: this.props.level || 'component',
      recoveryAttempts: this.state.recoveryAttempts
    });
    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo, errorReport);
    }
    // Attempt automatic recovery if enabled
    if (this.props.enableRecovery !== false) {
      this.attemptRecovery();
    }
  }
  private async generateErrorReport(error: Error, errorInfo: ErrorInfo): Promise<ErrorReport> {
    const report: ErrorReport = {
      id: `global-error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack || undefined,
      section: this.props.section || 'global',
      timestamp: new Date().toISOString(),
      url: typeof window !== 'undefined' ? window.location.href : undefined,
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
      sessionId: this.getSessionId(),
      retryCount: this.state.recoveryAttempts,
      severity: this.determineSeverity(error),
      category: this.categorizeError(error),
      context: {
        level: this.props.level || 'component',
        section: this.props.section,
        recoveryEnabled: this.props.enableRecovery !== false,
        analyticsEnabled: this.props.enableAnalytics !== false,
        userAgent: navigator.userAgent,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        },
        memory: this.getMemoryInfo(),
        performance: this.getPerformanceInfo()
      },
      breadcrumbs: [] // TODO: Implement proper breadcrumbs
    };
    return report;
  }
  private determineSeverity(error: Error): ErrorReport['severity'] {
    const message = error.message.toLowerCase();
    const name = error.name.toLowerCase();
    // Critical errors that break the entire application
    if (
      this.props.level === 'global' ||
      message.includes('chunk') ||
      message.includes('loading') ||
      name.includes('chunkloaderror')
    ) {
      return 'critical';
    }
    // High severity errors that break major features
    if (
      this.props.level === 'feature' ||
      message.includes('network') ||
      message.includes('auth') ||
      message.includes('permission')
    ) {
      return 'high';
    }
    // Medium severity errors that break components
    if (
      message.includes('render') ||
      message.includes('hook') ||
      this.state.recoveryAttempts > 1
    ) {
      return 'medium';
    }
    return 'low';
  }
  private categorizeError(error: Error): ErrorReport['category'] {
    const message = error.message.toLowerCase();
    const name = error.name.toLowerCase();
    if (message.includes('network') || message.includes('fetch')) return 'network';
    if (message.includes('auth') || message.includes('token')) return 'auth';
    if (message.includes('chunk') || message.includes('loading')) return 'ui';
    if (name.includes('type') || name.includes('reference')) return 'ui';
    return 'unknown';
  }
  private determineFallbackMode(error: Error, errorInfo: ErrorInfo): 'full' | 'degraded' | 'minimal' {
    const severity = this.determineSeverity(error);
    const recoveryAttempts = this.state.recoveryAttempts;
    if (severity === 'critical' || recoveryAttempts >= this.maxRecoveryAttempts) {
      return 'minimal';
    }
    if (severity === 'high' || recoveryAttempts >= 2) {
      return 'degraded';
    }
    return 'full';
  }
  private async reportError(error: Error, errorInfo: ErrorInfo, errorReport: ErrorReport) {
    try {
      // Report to error reporting service
      await errorReportingService.reportError(error, errorInfo, {
        section: this.props.section,
        retryCount: this.state.recoveryAttempts,
        level: this.props.level
      });
      // Report to external monitoring services
      await this.reportToMonitoringServices(errorReport);
      // Store for offline analysis
      this.storeErrorForAnalysis(errorReport);
    } catch (reportingError) {
    }
  }
  private async reportToMonitoringServices(errorReport: ErrorReport) {
    // Report to Sentry if configured
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(this.state.error, {
        tags: {
          section: errorReport.section,
          severity: errorReport.severity,
          category: errorReport.category
        },
        extra: errorReport.context,
        fingerprint: [errorReport.message, errorReport.section]
      });
    }
    // Report to custom monitoring endpoint
    const monitoringEndpoint = process.env.NEXT_PUBLIC_ERROR_MONITORING_ENDPOINT;
    if (monitoringEndpoint) {
      try {
        await fetch(monitoringEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${process.env.NEXT_PUBLIC_ERROR_MONITORING_API_KEY}`
          },
          body: JSON.stringify(errorReport)
        });
      } catch (error) {
      }
    }
  }
  private storeErrorForAnalysis(errorReport: ErrorReport) {
    try {
      const key = `error_analysis_${this.props.section || 'global'}`;
      const stored = localStorage.getItem(key);
      const reports = stored ? JSON.parse(stored) : [];
      reports.push(errorReport);
      // Keep only the most recent 50 reports per section
      const recentReports = reports.slice(-50);
      localStorage.setItem(key, JSON.stringify(recentReports));
    } catch (error) {
    }
  }
  private attemptRecovery = async () => {
    if (this.state.recoveryAttempts >= this.maxRecoveryAttempts) {
      return;
    }
    this.setState({ isRecovering: true });
    try {
      const recoveryStrategy = await this.recoveryManager.getRecoveryStrategy(
        this.state.error!,
        this.state.errorInfo!,
        this.state.recoveryAttempts
      );
      await this.executeRecoveryStrategy(recoveryStrategy);
    } catch (recoveryError) {
      this.setState({ 
        isRecovering: false,
        fallbackMode: 'minimal'
      });
    }
  };
  private async executeRecoveryStrategy(strategy: any) {
    const delay = strategy.delay || 1000;
    this.recoveryTimeout = setTimeout(() => {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        errorReport: null,
        recoveryAttempts: prevState.recoveryAttempts + 1,
        isRecovering: false,
        fallbackMode: 'full'
      }));
    }, delay);
  }
  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorReport: null,
      isRecovering: false,
      fallbackMode: 'full'
    });
  };
  private handleRecover = async () => {
    await this.attemptRecovery();
  };
  private handleReport = async () => {
    if (this.state.error && this.state.errorInfo && this.state.errorReport) {
      await this.reportError(this.state.error, this.state.errorInfo, this.state.errorReport);
    }
  };
  private getSessionId(): string {
    let sessionId = sessionStorage.getItem('error_session_id');
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('error_session_id', sessionId);
    }
    return sessionId;
  }
  private getMemoryInfo(): any {
    if ('memory' in performance) {
      return {
        usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
        jsHeapSizeLimit: (performance as any).memory.jsHeapSizeLimit
      };
    }
    return null;
  }
  private getPerformanceInfo(): any {
    if ('getEntriesByType' in performance) {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || null,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || null
      };
    }
    return null;
  }
  componentWillUnmount() {
    if (this.recoveryTimeout) {
      clearTimeout(this.recoveryTimeout);
    }
  }
  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallbackComponent || ProductionErrorFallback;
      return (
        <FallbackComponent
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          errorReport={this.state.errorReport}
          onRetry={this.handleRetry}
          onRecover={this.handleRecover}
          onReport={this.handleReport}
          recoveryAttempts={this.state.recoveryAttempts}
          maxRecoveryAttempts={this.maxRecoveryAttempts}
          fallbackMode={this.state.fallbackMode}
          isRecovering={this.state.isRecovering}
        />
      );
    }
    return this.props.children;
  }
}
// Higher-order component for easy wrapping
export function withGlobalErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WithGlobalErrorBoundaryComponent = (props: P) => (
    <GlobalErrorBoundary {...errorBoundaryProps}>
      <WrappedComponent {...props} />
    </GlobalErrorBoundary>
  );
  WithGlobalErrorBoundaryComponent.displayName = 
    `withGlobalErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;
  return WithGlobalErrorBoundaryComponent;
}
export default GlobalErrorBoundary;
