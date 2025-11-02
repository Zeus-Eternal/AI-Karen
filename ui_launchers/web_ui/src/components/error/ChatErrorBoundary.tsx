import React, { Component, ErrorInfo, ReactNode } from 'react';
import { useEffect } from 'react';
import { getTelemetryService } from '@/lib/telemetry';
interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  correlationId?: string;
  maxRetries?: number;
  enableRecovery?: boolean;
  enableReporting?: boolean;
  className?: string;
}
interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  isRetrying: boolean;
  lastErrorTime: number;
}
export class ChatErrorBoundary extends Component<Props, State> {
  private maxRetries: number;
  private retryTimeouts: NodeJS.Timeout[] = [];
  private telemetryService = getTelemetryService();
  private errorReportingEnabled: boolean;
  private recoveryEnabled: boolean;
  constructor(props: Props) {
    super(props);
    this.maxRetries = props.maxRetries ?? 3;
    this.errorReportingEnabled = props.enableReporting ?? true;
    this.recoveryEnabled = props.enableRecovery ?? true;
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRetrying: false,
      lastErrorTime: 0,
    };
  }
  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      lastErrorTime: Date.now(),
    };
  }
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { correlationId, onError } = this.props;
    const { errorId } = this.state;
    // Store error info in state
    this.setState({ errorInfo });
    // Track error with comprehensive telemetry
    if (this.errorReportingEnabled) {
      this.telemetryService.track('error.boundary.caught', {
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
          toString: error.toString(),
        },
        errorInfo: {
          componentStack: errorInfo.componentStack,
        },
        errorId,
        correlationId,
        retryCount: this.state.retryCount,
        timestamp: new Date().toISOString(),
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
        url: typeof window !== 'undefined' ? window.location.href : 'unknown',
        viewport: typeof window !== 'undefined' ? {
          width: window.innerWidth,
          height: window.innerHeight,
        } : null,
        memory: typeof (performance as any)?.memory !== 'undefined' ? {
          usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
          totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
          jsHeapSizeLimit: (performance as any).memory.jsHeapSizeLimit,
        } : null,
      }, correlationId);
    }
    // Report to external error tracking service
    this.reportToExternalService(error, errorInfo, errorId, correlationId);
    // Call custom error handler if provided
    if (onError) {
      try {
        onError(error, errorInfo);
      } catch (handlerError) {
        if (this.errorReportingEnabled) {
          this.telemetryService.track('error.boundary.handler_failed', {
            originalError: error.message,
            handlerError: handlerError instanceof Error ? handlerError.message : 'Unknown',
            errorId,

        }
      }
    }
  }
  componentWillUnmount() {
    // Clear any pending retry timeouts
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout));
    // Track boundary unmount
    if (this.errorReportingEnabled) {
      this.telemetryService.track('error.boundary.unmounted', {
        hadError: this.state.hasError,
        retryCount: this.state.retryCount,
        errorId: this.state.errorId,

    }
  }
  private reportToExternalService = async (
    error: Error, 
    errorInfo: ErrorInfo, 
    errorId: string | null, 
    correlationId?: string
  ) => {
    if (!this.errorReportingEnabled) return;
    try {
      // This would integrate with services like Sentry, Bugsnag, etc.
      const errorReport = {
        errorId,
        correlationId,
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
        },
        errorInfo: {
          componentStack: errorInfo.componentStack,
        },
        context: {
          timestamp: new Date().toISOString(),
          url: typeof window !== 'undefined' ? window.location.href : 'unknown',
          userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
          retryCount: this.state.retryCount,
        }
      };
      // In production, this would send to your error reporting service
      // Example: Send to error reporting endpoint
      // await fetch('/api/errors', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(errorReport)
      // });
    } catch (reportingError) {
    }
  };
  handleRetry = () => {
    const { retryCount } = this.state;
    if (retryCount >= this.maxRetries) {
      if (this.errorReportingEnabled) {
        this.telemetryService.track('error.boundary.max_retries_exceeded', {
          errorId: this.state.errorId,
          retryCount,
          maxRetries: this.maxRetries,
          correlationId: this.props.correlationId,
        }, this.props.correlationId);
      }
      return;
    }
    // Prevent rapid retries
    const timeSinceLastError = Date.now() - this.state.lastErrorTime;
    const minRetryDelay = 1000; // 1 second minimum
    if (timeSinceLastError < minRetryDelay) {
      setTimeout(() => this.handleRetry(), minRetryDelay - timeSinceLastError);
      return;
    }
    // Exponential backoff with jitter: 1s, 2s, 4s + random jitter
    const baseDelay = Math.pow(2, retryCount) * 1000;
    const jitter = Math.random() * 1000; // 0-1s jitter
    const delay = baseDelay + jitter;
    this.setState({ isRetrying: true });
    if (this.errorReportingEnabled) {
      this.telemetryService.track('error.boundary.retry_attempted', {
        errorId: this.state.errorId,
        retryCount: retryCount + 1,
        delay,
        correlationId: this.props.correlationId,
      }, this.props.correlationId);
    }
    const timeout = setTimeout(() => {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: null,
        retryCount: retryCount + 1,
        isRetrying: false,
        lastErrorTime: 0,

    }, delay);
    this.retryTimeouts.push(timeout);
  };
  handleReload = () => {
    if (this.errorReportingEnabled) {
      this.telemetryService.track('error.boundary.page_reload', {
        errorId: this.state.errorId,
        correlationId: this.props.correlationId,
      }, this.props.correlationId);
      // Flush telemetry before reload
      this.telemetryService.flush();
    }
    // Small delay to ensure telemetry is sent
    setTimeout(() => {
      window.location.reload();
    }, 100);
  };
  handleReportIssue = () => {
    if (this.errorReportingEnabled) {
      this.telemetryService.track('error.boundary.issue_reported', {
        errorId: this.state.errorId,
        correlationId: this.props.correlationId,
      }, this.props.correlationId);
    }
    // Open issue reporting (could be a modal, external link, etc.)
    const issueUrl = `mailto:support@example.com?subject=Error Report&body=Error ID: ${this.state.errorId}%0AError: ${encodeURIComponent(this.state.error?.message || 'Unknown error')}`;
    window.open(issueUrl, '_blank');
  };
  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

      return (
        <ErrorFallbackUI
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          errorId={this.state.errorId}
          retryCount={this.state.retryCount}
          maxRetries={this.maxRetries}
          isRetrying={this.state.isRetrying}
          onRetry={this.recoveryEnabled ? this.handleRetry : undefined}
          onReload={this.handleReload}
          onReportIssue={this.handleReportIssue}
          className={this.props.className}
        />
      );
    }
    return this.props.children;
  }
}
interface ErrorFallbackUIProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  maxRetries: number;
  isRetrying: boolean;
  onRetry?: () => void;
  onReload: () => void;
  onReportIssue: () => void;
  className?: string;
}
const ErrorFallbackUI: React.FC<ErrorFallbackUIProps> = ({
  error,
  errorInfo,
  errorId,
  retryCount,
  maxRetries,
  isRetrying,
  onRetry,
  onReload,
  onReportIssue,
  className = '',
}) => {
  const canRetry = onRetry && retryCount < maxRetries && !isRetrying;
  return (
    <div 
      className={`flex flex-col items-center justify-center p-8 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 ${className}`} 
      role="alert"
      aria-live="assertive"
    >
      <div className="text-center space-y-4 max-w-2xl ">
        <div className="text-red-500 dark:text-red-400">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mx-auto">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-red-800 dark:text-red-200">
        </h2>
        <p className="text-red-700 dark:text-red-300">
          We encountered an unexpected error. This has been automatically reported to our team.
        </p>
        {process.env.NODE_ENV === 'development' && error && (
          <details className="text-left bg-red-100 dark:bg-red-900/40 p-4 rounded border sm:p-4 md:p-6">
            <summary className="cursor-pointer font-medium text-red-800 dark:text-red-200 mb-2">
              Error Details (Development)
            </summary>
            <div className="space-y-2">
              <div>
                <strong className="text-red-800 dark:text-red-200">Error:</strong>
                <pre className="mt-1 text-sm text-red-700 dark:text-red-300 overflow-auto bg-red-50 dark:bg-red-900/20 p-2 rounded md:text-base lg:text-lg">
                  <code>{error.name}: {error.message}</code>
                </pre>
              </div>
              {error.stack && (
                <div>
                  <strong className="text-red-800 dark:text-red-200">Stack Trace:</strong>
                  <pre className="mt-1 text-xs text-red-700 dark:text-red-300 overflow-auto bg-red-50 dark:bg-red-900/20 p-2 rounded max-h-40 sm:text-sm md:text-base">
                    <code>{error.stack}</code>
                  </pre>
                </div>
              )}
              {errorInfo?.componentStack && (
                <div>
                  <strong className="text-red-800 dark:text-red-200">Component Stack:</strong>
                  <pre className="mt-1 text-xs text-red-700 dark:text-red-300 overflow-auto bg-red-50 dark:bg-red-900/20 p-2 rounded max-h-40 sm:text-sm md:text-base">
                    <code>{errorInfo.componentStack}</code>
                  </pre>
                </div>
              )}
            </div>
          </details>
        )}
        <div className="flex flex-wrap gap-3 justify-center">
          {canRetry && (
            <button
              onClick={onRetry}
              disabled={isRetrying}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white rounded-md transition-colors flex items-center gap-2"
              type="button"
             aria-label="Button">
              {isRetrying ? (
                <>
                  <svg className="animate-spin h-4 w-4 " fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Retrying...
                </>
              ) : (
                <>
                  Try Again {retryCount > 0 && `(${retryCount}/${maxRetries})`}
                </>
              )}
            </button>
          )}
          <button
            onClick={onReload}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
            type="button"
           aria-label="Button">
          </button>
          <button
            onClick={onReportIssue}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
            type="button"
           aria-label="Button">
          </button>
        </div>
        {errorId && (
          <div className="text-sm text-red-600 dark:text-red-400 space-y-1 md:text-base lg:text-lg">
            <p>
              Error ID: <code className="bg-red-100 dark:bg-red-900/40 px-2 py-1 rounded text-xs font-mono sm:text-sm md:text-base">{errorId}</code>
            </p>
            <p className="text-xs opacity-75 sm:text-sm md:text-base">
            </p>
          </div>
        )}
        {retryCount >= maxRetries && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 sm:p-4 md:p-6">
            <p className="text-yellow-800 dark:text-yellow-200 text-sm md:text-base lg:text-lg">
              <strong>Maximum retry attempts reached.</strong> Please reload the page or report this issue if it persists.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
export default ChatErrorBoundary;
