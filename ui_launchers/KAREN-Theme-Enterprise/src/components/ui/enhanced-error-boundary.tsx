"use client";

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';
import { Alert, AlertDescription, AlertTitle } from './alert';
import { Card, CardContent, CardFooter, CardHeader } from './card';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
}

interface EnhancedErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  maxRetries?: number;
  showRetry?: boolean;
  showHomeButton?: boolean;
  customMessage?: string;
  level?: 'page' | 'section' | 'component';
}

export class EnhancedErrorBoundary extends Component<
  EnhancedErrorBoundaryProps,
  ErrorBoundaryState
> {
  private retryTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: EnhancedErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log error details for debugging
    console.error('Enhanced Error Boundary caught an error:', error, errorInfo);
  }

  handleRetry = () => {
    const { maxRetries = 3 } = this.props;
    
    if (this.state.retryCount < maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1,
      }));
    }
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  render() {
    const { 
      children, 
      fallback, 
      showRetry = true, 
      showHomeButton = true,
      customMessage,
      level = 'component',
      maxRetries = 3
    } = this.props;

    if (this.state.hasError) {
      // If custom fallback is provided, use it
      if (fallback) {
        return fallback;
      }

      const canRetry = showRetry && this.state.retryCount < maxRetries;
      const isPageLevel = level === 'page';

      return (
        <div className={cn(
          "flex items-center justify-center",
          isPageLevel ? "min-h-screen p-4" : "p-6"
        )}>
          <Card className={cn(
            "w-full max-w-md",
            isPageLevel ? "max-w-lg" : "max-w-md"
          )}>
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="h-6 w-6 text-destructive" />
              </div>
              <AlertTitle className="text-lg">
                {customMessage || 'Something went wrong'}
              </AlertTitle>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <Alert variant="destructive">
                <AlertDescription>
                  {isPageLevel 
                    ? 'The page encountered an unexpected error. This could be due to a temporary issue or a problem with the data being loaded.'
                    : 'This component encountered an error while trying to display its content.'
                  }
                </AlertDescription>
              </Alert>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4 rounded-md border border-border bg-muted p-4">
                  <summary className="cursor-pointer font-mono text-sm font-medium">
                    Error Details (Development Only)
                  </summary>
                  <pre className="mt-2 overflow-x-auto text-xs">
                    <code>
                      {this.state.error.toString()}
                      {this.state.errorInfo && (
                        <div className="mt-2">
                          <strong>Component Stack:</strong>
                          <br />
                          {this.state.errorInfo.componentStack}
                        </div>
                      )}
                    </code>
                  </pre>
                </details>
              )}

              {this.state.retryCount > 0 && (
                <Alert>
                  <AlertDescription>
                    Retry attempt {this.state.retryCount} of {maxRetries}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>

            <CardFooter className="flex flex-col gap-2">
              {canRetry && (
                <Button 
                  onClick={this.handleRetry}
                  className="w-full"
                  aria-label="Retry loading the component"
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Try Again
                </Button>
              )}
              
              {showHomeButton && isPageLevel && (
                <Button 
                  variant="outline" 
                  onClick={this.handleGoHome}
                  className="w-full"
                  aria-label="Go to home page"
                >
                  <Home className="mr-2 h-4 w-4" />
                  Go to Home
                </Button>
              )}
            </CardFooter>
          </Card>
        </div>
      );
    }

    return children;
  }
}

// Hook for functional components to use error boundaries
export const useErrorHandler = () => {
  return React.useCallback((error: Error, errorInfo?: ErrorInfo) => {
    console.error('Error caught by error handler:', error, errorInfo);
    
    // Here you could integrate with error reporting services
    // like Sentry, LogRocket, etc.
  }, []);
};

export default EnhancedErrorBoundary;