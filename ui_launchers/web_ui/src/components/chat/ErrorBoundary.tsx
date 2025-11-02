'use client';
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { safeError, safeDebug } from '@/lib/safe-console';
interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}
interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorId: string;
}
export class ChatErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      errorId: '',
    };
  }
  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };
  }
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    safeError('ChatErrorBoundary caught an error:', error);
    safe);
    this.setState({
      error,
      errorInfo,
    });
    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    // Report error to monitoring service if available
    this.reportError(error, errorInfo);
  }
  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    try {
      // In a production environment, you would send this to an error reporting service
      const errorReport = {
        errorId: this.state.errorId,
        timestamp: new Date().toISOString(),
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
        },
        errorInfo: {
          componentStack: errorInfo.componentStack,
        },
        userAgent: navigator.userAgent,
        url: window.location.href,
        userId: localStorage.getItem('karen_user_id') || 'anonymous',
      };
      safeDebug('Error Report:', errorReport);
      // Store error locally for debugging
      const existingErrors = JSON.parse(localStorage.getItem('karen_ui_errors') || '[]');
      existingErrors.push(errorReport);
      // Keep only last 10 errors
      if (existingErrors.length > 10) {
        existingErrors.splice(0, existingErrors.length - 10);
      }
      localStorage.setItem('karen_ui_errors', JSON.stringify(existingErrors));
    } catch (reportingError) {
      safeError('Failed to report error:', reportingError);
    }
  };
  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      errorId: '',
    });
  };
  private handleGoHome = () => {
    window.location.href = '/';
  };
  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="flex items-center justify-center min-h-[400px] p-4 sm:p-4 md:p-6">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-600">
                <AlertTriangle className="h-5 w-5 sm:w-auto md:w-full" />
                Something went wrong
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <AlertTriangle className="h-4 w-4 sm:w-auto md:w-full" />
                <AlertDescription>
                  The chat interface encountered an unexpected error. Your conversation data has been preserved.
                </AlertDescription>
              </Alert>
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                <p><strong>Error ID:</strong> {this.state.errorId}</p>
                <p><strong>Time:</strong> {new Date().toLocaleString()}</p>
              </div>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="text-xs bg-gray-50 dark:bg-gray-900 p-3 rounded border sm:text-sm md:text-base">
                  <summary className="cursor-pointer font-medium">Technical Details</summary>
                  <div className="mt-2 space-y-2">
                    <div>
                      <strong>Error:</strong> {this.state.error.message}
                    </div>
                    {this.state.error.stack && (
                      <div>
                        <strong>Stack:</strong>
                        <pre className="whitespace-pre-wrap text-xs mt-1 sm:text-sm md:text-base">
                          {this.state.error.stack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              )}
              <div className="flex gap-2">
                <button onClick={this.handleRetry} className="flex-1" aria-label="Button">
                  <RefreshCw className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Try Again
                </Button>
                <button variant="outline" onClick={this.handleGoHome} aria-label="Button">
                  <Home className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Home
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }
    return this.props.children;
  }
}
export default ChatErrorBoundary;
