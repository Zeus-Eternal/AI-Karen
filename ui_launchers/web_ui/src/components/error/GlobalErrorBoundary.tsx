/**
 * Global Error Boundary with Intelligent Response Integration
 * 
 * Catches all unhandled errors in the React component tree and provides
 * intelligent error analysis and recovery options.
 * 
 * Requirements: 5.4, 5.5, 3.2, 3.3
 */
'use client';
import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { IntelligentErrorPanel } from './IntelligentErrorPanel';
import { SessionErrorBoundary } from '@/components/auth/SessionErrorBoundary';
interface GlobalErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, errorInfo: React.ErrorInfo, retry: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  showIntelligentResponse?: boolean;
  enableSessionRecovery?: boolean;
  showTechnicalDetails?: boolean;
}
interface GlobalErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  showDetails: boolean;
}
export class GlobalErrorBoundary extends Component<
  GlobalErrorBoundaryProps,
  GlobalErrorBoundaryState
> {
  private maxRetries = 3;
  constructor(props: GlobalErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      showDetails: false,
    };
  }
  static getDerivedStateFromError(error: Error): Partial<GlobalErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
  }
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });
    // Call the onError callback if provided
    this.props.onError?.(error, errorInfo);
    // Report error to monitoring service (if available)
    this.reportError(error, errorInfo);
  }
  private reportError = (error: Error, errorInfo: React.ErrorInfo) => {
    try {
      // This could be integrated with error reporting services like Sentry
      const errorReport = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        url: typeof window !== 'undefined' ? window.location.href : undefined,
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
        errorId: this.state.errorId,
      };
      // Send to error reporting service
      // await errorReportingService.report(errorReport);
    } catch (reportingError) {
    }
  };
  private handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: null,
        retryCount: prevState.retryCount + 1,
        showDetails: false,
      }));
    }
  };
  private handleReload = () => {
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };
  private handleGoHome = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  };
  private handleReportBug = () => {
    if (!this.state.error) return;
    const subject = encodeURIComponent(`Bug Report: ${this.state.error.message}`);
    const body = encodeURIComponent(`
Error Details:
- Message: ${this.state.error.message}
- Stack: ${this.state.error.stack}
- Component Stack: ${this.state.errorInfo?.componentStack || 'N/A'}
- Error ID: ${this.state.errorId}
- URL: ${typeof window !== 'undefined' ? window.location.href : 'N/A'}
- Timestamp: ${new Date().toISOString()}
- User Agent: ${typeof navigator !== 'undefined' ? navigator.userAgent : 'N/A'}
Please describe what you were doing when this error occurred:
[Your description here]
    `);
    const mailtoUrl = `mailto:support@example.com?subject=${subject}&body=${body}`;
    window.open(mailtoUrl, '_blank');
  };
  private toggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails,
    }));
  };
  private isAuthenticationError = (error: Error): boolean => {
    const message = error.message.toLowerCase();
    return (
      message.includes('401') ||
      message.includes('unauthorized') ||
      message.includes('authentication') ||
      message.includes('token') ||
      message.includes('session')
    );
  };
  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }
    const { error, errorInfo, retryCount, showDetails } = this.state;
    const { 
      fallback, 
      showIntelligentResponse = true, 
      enableSessionRecovery = true,
      showTechnicalDetails = false 
    } = this.props;
    // Use custom fallback if provided
    if (fallback && error && errorInfo) {
      return fallback(error, errorInfo, this.handleRetry);
    }
    // If this is an authentication error and session recovery is enabled,
    // wrap with SessionErrorBoundary
    if (enableSessionRecovery && error && this.isAuthenticationError(error)) {
      return (
        <SessionErrorBoundary
          onAuthError={(authError) => {
            // Handle retry logic here if needed
            this.handleRetry();
          }}
        >
          {this.props.children}
        </SessionErrorBoundary>
      );
    }
    const canRetry = retryCount < this.maxRetries;
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4 sm:p-4 md:p-6">
        <div className="w-full max-w-2xl space-y-6 sm:w-auto md:w-full">
          {/* Main Error Card */}
          <Card className="border-destructive/50">
            <CardHeader>
              <div className="flex items-center space-x-3">
                <AlertTriangle className="h-8 w-8 text-destructive sm:w-auto md:w-full" />
                <div>
                  <CardTitle className="text-xl">Application Error</CardTitle>
                  <CardDescription className="flex items-center space-x-2 mt-1">
                    <span>Something unexpected happened</span>
                    {this.state.errorId && (
                      <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                        ID: {this.state.errorId.slice(-8)}
                      </Badge>
                    )}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Error Summary */}
              <Alert>
                <Bug className="h-4 w-4 sm:w-auto md:w-full" />
                <AlertTitle>Error Details</AlertTitle>
                <AlertDescription className="mt-2">
                  <p className="font-medium">{error?.message || 'Unknown error occurred'}</p>
                  {retryCount > 0 && (
                    <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                      Retry attempt {retryCount} of {this.maxRetries}
                    </p>
                  )}
                </AlertDescription>
              </Alert>
              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3">
                {canRetry && (
                  <button onClick={this.handleRetry} className="flex items-center gap-2" aria-label="Button">
                    <RefreshCw className="h-4 w-4 sm:w-auto md:w-full" />
                    Try Again
                  </Button>
                )}
                <button variant="outline" onClick={this.handleReload} className="flex items-center gap-2" aria-label="Button">
                  <RefreshCw className="h-4 w-4 sm:w-auto md:w-full" />
                  Reload Page
                </Button>
                <button variant="outline" onClick={this.handleGoHome} className="flex items-center gap-2" aria-label="Button">
                  <Home className="h-4 w-4 sm:w-auto md:w-full" />
                  Go Home
                </Button>
                <button variant="outline" onClick={this.handleReportBug} className="flex items-center gap-2" aria-label="Button">
                  <ExternalLink className="h-4 w-4 sm:w-auto md:w-full" />
                  Report Bug
                </Button>
              </div>
              {/* Technical Details Toggle */}
              {(showTechnicalDetails || error?.stack || errorInfo?.componentStack) && (
                <div className="pt-2">
                  <button
                    variant="ghost"
                    size="sm"
                    onClick={this.toggleDetails}
                    className="text-muted-foreground"
                   aria-label="Button">
                    {showDetails ? 'Hide' : 'Show'} Technical Details
                  </Button>
                </div>
              )}
              {/* Technical Details */}
              {showDetails && (
                <div className="space-y-3 pt-2 border-t">
                  {error?.stack && (
                    <div>
                      <h4 className="font-medium text-sm mb-2 md:text-base lg:text-lg">Error Stack:</h4>
                      <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-40 font-mono sm:text-sm md:text-base">
                        {error.stack}
                      </pre>
                    </div>
                  )}
                  {errorInfo?.componentStack && (
                    <div>
                      <h4 className="font-medium text-sm mb-2 md:text-base lg:text-lg">Component Stack:</h4>
                      <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-40 font-mono sm:text-sm md:text-base">
                        {errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
          {/* Intelligent Error Response */}
          {showIntelligentResponse && error && (
            <IntelligentErrorPanel
              error={error}
              errorType={error.name}
              userContext={{
                component_stack: errorInfo?.componentStack,
                error_boundary: true,
                error_id: this.state.errorId,
                retry_count: retryCount,
                timestamp: new Date().toISOString(),
                url: typeof window !== 'undefined' ? window.location.href : undefined,
              }}
              onRetry={canRetry ? this.handleRetry : undefined}
              onDismiss={() => {
                // Could implement dismissal logic here
              }}
              autoFetch={true}
              showTechnicalDetails={false}
              maxRetries={this.maxRetries}
            />
          )}
          {/* Help Text */}
          <div className="text-center text-sm text-muted-foreground md:text-base lg:text-lg">
            <p>
              If this error persists, please{' '}
              <button
                onClick={this.handleReportBug}
                className="underline hover:text-foreground transition-colors"
               aria-label="Button">
                report it to our support team
              </button>
              {' '}with the error ID above.
            </p>
          </div>
        </div>
      </div>
    );
  }
}
/**
 * Higher-order component to wrap the entire app with global error boundary
 */
export function withGlobalErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<GlobalErrorBoundaryProps, 'children'>
) {
  return function WrappedComponent(props: P) {
    return (
      <GlobalErrorBoundary {...errorBoundaryProps}>
        <Component {...props} />
      </GlobalErrorBoundary>
    );
  };
}
export default GlobalErrorBoundary;
