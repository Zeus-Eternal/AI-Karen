'use client';
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ErrorReportingService } from '@/services/error-reporting';
import { ErrorRecoveryService } from '@/services/error-recovery';
interface Props {
  children: ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  level?: 'global' | 'feature' | 'component';
  featureName?: string;
  enableRecovery?: boolean;
  enableReporting?: boolean;
}
interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  isRecovering: boolean;
}
export interface ErrorFallbackProps {
  error: Error;
  errorInfo: ErrorInfo;
  resetError: () => void;
  retryCount: number;
  errorId: string | null;
  level: string;
  featureName?: string;
}
export class ErrorBoundary extends Component<Props, State> {
  private errorReporting: ErrorReportingService;
  private errorRecovery: ErrorRecoveryService;
  private retryTimeout: NodeJS.Timeout | null = null;
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRecovering: false,
    };
    this.errorReporting = new ErrorReportingService();
    this.errorRecovery = new ErrorRecoveryService();
  }
  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const errorId = this.generateErrorId();
    this.setState({
      errorInfo,
      errorId,
    });
    // Report error if enabled
    if (this.props.enableReporting !== false) {
      this.reportError(error, errorInfo, errorId);
    }
    // Call custom error handler
    this.props.onError?.(error, errorInfo);
    // Attempt automatic recovery if enabled
    if (this.props.enableRecovery !== false) {
      this.attemptRecovery(error);
    }
  }
  private generateErrorId(): string {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  private async reportError(error: Error, errorInfo: ErrorInfo, errorId: string) {
    try {
      await this.errorReporting.reportError({
        error,
        errorInfo,
        errorId,
        level: this.props.level || 'component',
        featureName: this.props.featureName,
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: new Date().toISOString(),
        userId: this.getCurrentUserId(),
        sessionId: this.getSessionId(),
      });
    } catch (reportingError) {
    }
  }
  private getCurrentUserId(): string | null {
    // Get from auth context or local storage
    return localStorage.getItem('userId') || null;
  }
  private getSessionId(): string | null {
    return sessionStorage.getItem('sessionId') || null;
  }
  private async attemptRecovery(error: Error) {
    const { retryCount } = this.state;
    const maxRetries = this.getMaxRetries();
    if (retryCount < maxRetries) {
      this.setState({ isRecovering: true });
      try {
        const recoveryStrategy = await this.errorRecovery.getRecoveryStrategy(error, {
          level: this.props.level || 'component',
          featureName: this.props.featureName,
          retryCount,
        });
        if (recoveryStrategy.canRecover) {
          await this.executeRecoveryStrategy(recoveryStrategy);
        }
      } catch (recoveryError) {
      } finally {
        this.setState({ isRecovering: false });
      }
    }
  }
  private getMaxRetries(): number {
    switch (this.props.level) {
      case 'global':
        return 1;
      case 'feature':
        return 2;
      case 'component':
      default:
        return 3;
    }
  }
  private async executeRecoveryStrategy(strategy: any) {
    const delay = strategy.retryDelay || 1000;
    this.retryTimeout = setTimeout(() => {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1,
        isRecovering: false,
      }));
    }, delay);
  }
  private resetError = () => {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
      this.retryTimeout = null;
    }
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRecovering: false,
    });
  };
  componentWillUnmount() {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
    }
  }
  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return (
        <FallbackComponent
          error={this.state.error!}
          errorInfo={this.state.errorInfo!}
          resetError={this.resetError}
          retryCount={this.state.retryCount}
          errorId={this.state.errorId}
          level={this.props.level || 'component'}
          featureName={this.props.featureName}
        />
      );
    }
    return this.props.children;
  }
}
// Default error fallback component
const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  resetError,
  retryCount,
  errorId,
  level,
  featureName,
}) => {
  const isGlobalError = level === 'global';
  const canRetry = retryCount < 3;
  const handleReportBug = () => {
    const bugReportUrl = `mailto:support@kari.ai?subject=Error Report - ${errorId}&body=${encodeURIComponent(
      `Error ID: ${errorId}\nFeature: ${featureName || 'Unknown'}\nError: ${error.message}\nStack: ${error.stack}`
    )}`;
    window.open(bugReportUrl);
  };
  const handleGoHome = () => {
    window.location.href = '/';
  };
  return (
    <div className="min-h-[400px] flex items-center justify-center p-4 sm:p-4 md:p-6">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20 sm:w-auto md:w-full">
            <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400 sm:w-auto md:w-full" />
          </div>
          <CardTitle className="text-xl">
            {isGlobalError ? 'Application Error' : 'Something went wrong'}
          </CardTitle>
          <CardDescription>
            {isGlobalError
              ? 'The application encountered an unexpected error'
              : `An error occurred in ${featureName || 'this section'}`}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {errorId && (
            <Alert>
              <AlertDescription className="text-sm md:text-base lg:text-lg">
                Error ID: <code className="font-mono">{errorId}</code>
              </AlertDescription>
            </Alert>
          )}
          <div className="flex flex-col gap-2">
            {canRetry && (
              <button onClick={resetError} className="w-full" aria-label="Button">
                <RefreshCw className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
                Try Again
              </Button>
            )}
            {!isGlobalError && (
              <button variant="outline" onClick={handleGoHome} className="w-full" aria-label="Button">
                <Home className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
                Go to Dashboard
              </Button>
            )}
            <button variant="outline" onClick={handleReportBug} className="w-full" aria-label="Button">
              <Bug className="mr-2 h-4 w-4 sm:w-auto md:w-full" />
              Report Bug
            </Button>
          </div>
          {process.env.NODE_ENV === 'development' && (
            <details className="mt-4">
              <summary className="cursor-pointer text-sm text-muted-foreground md:text-base lg:text-lg">
                Error Details (Development)
              </summary>
              <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-auto max-h-32 sm:text-sm md:text-base">
                {error.stack}
              </pre>
            </details>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
// Higher-order component for easy error boundary wrapping
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  return WrappedComponent;
}
