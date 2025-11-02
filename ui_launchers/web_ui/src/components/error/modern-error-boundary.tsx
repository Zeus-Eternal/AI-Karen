'use client';
import React, { Component, ReactNode, ErrorInfo } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug, ExternalLink, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
interface ModernErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, errorInfo: ErrorInfo, retry: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  maxRetries?: number;
  retryDelay?: number;
  section?: string;
  enableAutoRetry?: boolean;
  showTechnicalDetails?: boolean;
  enableErrorReporting?: boolean;
  className?: string;
}
interface ModernErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  isRetrying: boolean;
  showDetails: boolean;
  retryProgress: number;
}
export class ModernErrorBoundary extends Component<
  ModernErrorBoundaryProps,
  ModernErrorBoundaryState
> {
  private retryTimeoutId: NodeJS.Timeout | null = null;
  private progressIntervalId: NodeJS.Timeout | null = null;
  constructor(props: ModernErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRetrying: false,
      showDetails: false,
      retryProgress: 0,
    };
  }
  static getDerivedStateFromError(error: Error): Partial<ModernErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
  }
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`ModernErrorBoundary (${this.props.section || 'unknown'}) caught an error:`, error, errorInfo);
    this.setState({ errorInfo });
    // Call the onError callback if provided
    this.props.onError?.(error, errorInfo);
    // Report error to monitoring service
    this.reportError(error, errorInfo);
    // Auto-retry if enabled and within retry limits
    if (this.props.enableAutoRetry && this.state.retryCount < (this.props.maxRetries || 3)) {
      this.scheduleRetry();
    }
  }
  componentWillUnmount() {
    this.clearRetryTimeout();
    this.clearProgressInterval();
  }
  private clearRetryTimeout = () => {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
      this.retryTimeoutId = null;
    }
  };
  private clearProgressInterval = () => {
    if (this.progressIntervalId) {
      clearInterval(this.progressIntervalId);
      this.progressIntervalId = null;
    }
  };
  private reportError = async (error: Error, errorInfo: ErrorInfo) => {
    if (!this.props.enableErrorReporting) return;
    try {
      const errorReport = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        section: this.props.section,
        timestamp: new Date().toISOString(),
        url: typeof window !== 'undefined' ? window.location.href : undefined,
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
        errorId: this.state.errorId,
        retryCount: this.state.retryCount,
      };
      // Send to error reporting service (implement based on your service)
      // await errorReportingService.report(errorReport);
      // For now, we'll just log to console and could integrate with services like Sentry
      if (typeof window !== 'undefined' && 'gtag' in window) {
        (window as any).gtag('event', 'exception', {
          description: `${this.props.section || 'Unknown'}: ${error.message}`,
          fatal: false,
          custom_map: {
            error_id: this.state.errorId,
            section: this.props.section,
            retry_count: this.state.retryCount,
          },
        });
      }
    } catch (reportingError) {
    }
  };
  private scheduleRetry = () => {
    const delay = this.props.retryDelay || 2000;
    this.setState({ isRetrying: true, retryProgress: 0 });
    // Start progress animation
    const progressStep = 100 / (delay / 100);
    this.progressIntervalId = setInterval(() => {
      this.setState(prevState => {
        const newProgress = Math.min(prevState.retryProgress + progressStep, 100);
        return { retryProgress: newProgress };
      });
    }, 100);
    this.retryTimeoutId = setTimeout(() => {
      this.handleRetry();
    }, delay);
  };
  private handleRetry = () => {
    this.clearRetryTimeout();
    this.clearProgressInterval();
    const maxRetries = this.props.maxRetries || 3;
    if (this.state.retryCount < maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: null,
        retryCount: prevState.retryCount + 1,
        isRetrying: false,
        showDetails: false,
        retryProgress: 0,
      }));
    } else {
      this.setState({ isRetrying: false, retryProgress: 0 });
    }
  };
  private handleManualRetry = () => {
    this.clearRetryTimeout();
    this.clearProgressInterval();
    this.handleRetry();
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
    const subject = encodeURIComponent(`Bug Report: ${this.props.section || 'App'} - ${this.state.error.message}`);
    const body = encodeURIComponent(`
Error Details:
- Section: ${this.props.section || 'Unknown'}
- Message: ${this.state.error.message}
- Stack: ${this.state.error.stack}
- Component Stack: ${this.state.errorInfo?.componentStack || 'N/A'}
- Error ID: ${this.state.errorId}
- Retry Count: ${this.state.retryCount}
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
  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }
    const { error, errorInfo, retryCount, isRetrying, showDetails, retryProgress } = this.state;
    const { fallback, maxRetries = 3, section, showTechnicalDetails = false, className } = this.props;
    // Use custom fallback if provided
    if (fallback && error && errorInfo) {
      return fallback(error, errorInfo, this.handleManualRetry);
    }
    const canRetry = retryCount < maxRetries;
    const sectionName = section ? section.charAt(0).toUpperCase() + section.slice(1) : 'Application';
    return (
      <div className={`flex items-center justify-center p-4 ${className || ''}`}>
        <Card className="w-full max-w-lg border-destructive/50">
          <CardHeader>
            <div className="flex items-center space-x-3">
              <AlertTriangle className="h-6 w-6 text-destructive flex-shrink-0 sm:w-auto md:w-full" />
              <div className="min-w-0 flex-1 sm:w-auto md:w-full">
                <CardTitle className="text-lg">{sectionName} Error</CardTitle>
                <CardDescription className="flex items-center space-x-2 mt-1">
                  <span>Something went wrong in this section</span>
                  {this.state.errorId && (
                    <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                      {this.state.errorId.slice(-8)}
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
                <p className="font-medium text-sm md:text-base lg:text-lg">{error?.message || 'Unknown error occurred'}</p>
                {retryCount > 0 && (
                  <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                    Retry attempt {retryCount} of {maxRetries}
                  </p>
                )}
              </AlertDescription>
            </Alert>
            {/* Auto-retry Progress */}
            {isRetrying && (
              <div className="space-y-2">
                <div className="flex items-center space-x-2 text-sm text-muted-foreground md:text-base lg:text-lg">
                  <Clock className="h-4 w-4 sm:w-auto md:w-full" />
                  <span>Retrying automatically...</span>
                </div>
                <Progress value={retryProgress} className="h-2" />
              </div>
            )}
            {/* Action Buttons */}
            <div className="flex flex-wrap gap-2">
              {canRetry && !isRetrying && (
                <button 
                  onClick={this.handleManualRetry} 
                  size="sm"
                  className="flex items-center gap-2"
                 aria-label="Button">
                  <RefreshCw className="h-4 w-4 sm:w-auto md:w-full" />
                  Try Again
                </Button>
              )}
              <button 
                variant="outline" 
                size="sm"
                onClick={this.handleReload} 
                className="flex items-center gap-2"
               aria-label="Button">
                <RefreshCw className="h-4 w-4 sm:w-auto md:w-full" />
                Reload
              </Button>
              {section !== 'global' && (
                <button 
                  variant="outline" 
                  size="sm"
                  onClick={this.handleGoHome} 
                  className="flex items-center gap-2"
                 aria-label="Button">
                  <Home className="h-4 w-4 sm:w-auto md:w-full" />
                  Home
                </Button>
              )}
              <button 
                variant="outline" 
                size="sm"
                onClick={this.handleReportBug} 
                className="flex items-center gap-2"
               aria-label="Button">
                <ExternalLink className="h-4 w-4 sm:w-auto md:w-full" />
                Report
              </Button>
            </div>
            {/* Technical Details Toggle */}
            {(showTechnicalDetails || process.env.NODE_ENV === 'development') && (
              <div className="pt-2">
                <button
                  variant="ghost"
                  size="sm"
                  onClick={this.toggleDetails}
                  className="text-muted-foreground h-8"
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
                    <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-32 font-mono sm:text-sm md:text-base">
                      {error.stack}
                    </pre>
                  </div>
                )}
                {errorInfo?.componentStack && (
                  <div>
                    <h4 className="font-medium text-sm mb-2 md:text-base lg:text-lg">Component Stack:</h4>
                    <pre className="text-xs bg-muted p-3 rounded overflow-auto max-h-32 font-mono sm:text-sm md:text-base">
                      {errorInfo.componentStack}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }
}
export default ModernErrorBoundary;
