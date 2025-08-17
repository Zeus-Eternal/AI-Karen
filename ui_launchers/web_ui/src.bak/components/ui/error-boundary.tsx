'use client';

/**
 * Enhanced Error Boundary Component
 * 
 * Features:
 * - Consistent with Next.js error handling patterns
 * - React component architecture compliance
 * - Graceful error recovery
 * - User-friendly error messages
 * - Development vs production error display
 * - Error reporting integration
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  AlertTriangle, 
  RefreshCw, 
  Bug, 
  Home, 
  ChevronDown, 
  ChevronUp,
  Copy,
  ExternalLink
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  enableRecovery?: boolean;
  className?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  showDetails: boolean;
  retryCount: number;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: props.showDetails || false,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 Error Boundary Caught Error');
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.error('Component Stack:', errorInfo.componentStack);
      console.groupEnd();
    }

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Report error to monitoring service
    this.reportError(error, errorInfo);
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    // In a real application, this would send to error reporting service
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'exception', {
        description: error.toString(),
        fatal: false,
        custom_map: {
          component_stack: errorInfo.componentStack
        }
      });
    }
  };

  private handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }));
  };

  private handleRefresh = () => {
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  private handleGoHome = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  };

  private toggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails
    }));
  };

  private copyErrorDetails = async () => {
    if (!this.state.error) return;

    const errorDetails = {
      message: this.state.error.message,
      stack: this.state.error.stack,
      componentStack: this.state.errorInfo?.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    try {
      await navigator.clipboard.writeText(JSON.stringify(errorDetails, null, 2));
      // Could show a toast here
    } catch (err) {
      console.error('Failed to copy error details:', err);
    }
  };

  private getErrorMessage = (error: Error): string => {
    // Provide user-friendly error messages
    if (error.message.includes('ChunkLoadError')) {
      return 'Failed to load application resources. This usually happens after an update.';
    }
    
    if (error.message.includes('Network Error')) {
      return 'Network connection error. Please check your internet connection.';
    }
    
    if (error.message.includes('TypeError')) {
      return 'A technical error occurred. Our team has been notified.';
    }
    
    if (error.message.includes('ReferenceError')) {
      return 'A component failed to load properly. Please try refreshing the page.';
    }

    // Return original message if it's already user-friendly
    if (error.message.length < 100 && !error.message.includes('at ')) {
      return error.message;
    }

    return 'An unexpected error occurred. Please try again.';
  };

  private getSuggestions = (error: Error): string[] => {
    const suggestions: string[] = [];

    if (error.message.includes('ChunkLoadError')) {
      suggestions.push('Refresh the page to load the latest version');
      suggestions.push('Clear your browser cache and cookies');
    } else if (error.message.includes('Network')) {
      suggestions.push('Check your internet connection');
      suggestions.push('Try again in a few moments');
    } else {
      suggestions.push('Refresh the page');
      suggestions.push('Try navigating to a different page');
      if (this.state.retryCount < 3) {
        suggestions.push('Click the retry button below');
      }
    }

    return suggestions;
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const error = this.state.error!;
      const errorMessage = this.getErrorMessage(error);
      const suggestions = this.getSuggestions(error);
      const isDevelopment = process.env.NODE_ENV === 'development';

      return (
        <div className={cn(
          'min-h-screen flex items-center justify-center p-4 bg-gray-50 dark:bg-gray-900',
          this.props.className
        )}>
          <Card className="w-full max-w-2xl shadow-lg">
            <CardHeader className="text-center pb-4">
              <div className="flex justify-center mb-4">
                <div className="p-3 bg-red-100 dark:bg-red-900/20 rounded-full">
                  <AlertTriangle className="h-8 w-8 text-red-600 dark:text-red-400" />
                </div>
              </div>
              
              <CardTitle className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Something went wrong
              </CardTitle>
              
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                {errorMessage}
              </p>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Suggestions */}
              {suggestions.length > 0 && (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                    Try these solutions:
                  </h4>
                  <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
                    {suggestions.map((suggestion, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-blue-500 mt-0.5">•</span>
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3 justify-center">
                {this.props.enableRecovery !== false && this.state.retryCount < 3 && (
                  <Button onClick={this.handleRetry} className="flex items-center gap-2">
                    <RefreshCw className="h-4 w-4" />
                    Try Again
                  </Button>
                )}
                
                <Button onClick={this.handleRefresh} variant="outline" className="flex items-center gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Refresh Page
                </Button>
                
                <Button onClick={this.handleGoHome} variant="outline" className="flex items-center gap-2">
                  <Home className="h-4 w-4" />
                  Go Home
                </Button>
              </div>

              {/* Error Details (Development or when requested) */}
              {(isDevelopment || this.state.showDetails) && (
                <>
                  <Separator />
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100 flex items-center gap-2">
                        <Bug className="h-4 w-4" />
                        Error Details
                        {isDevelopment && (
                          <Badge variant="secondary" className="text-xs">
                            Development
                          </Badge>
                        )}
                      </h4>
                      
                      <div className="flex items-center gap-2">
                        <Button
                          onClick={this.copyErrorDetails}
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0"
                          title="Copy error details"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                        
                        <Button
                          onClick={this.toggleDetails}
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0"
                        >
                          {this.state.showDetails ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>

                    {this.state.showDetails && (
                      <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 text-sm font-mono">
                        <div className="space-y-3">
                          <div>
                            <strong className="text-red-600 dark:text-red-400">Error:</strong>
                            <pre className="mt-1 whitespace-pre-wrap text-gray-800 dark:text-gray-200">
                              {error.message}
                            </pre>
                          </div>
                          
                          {error.stack && (
                            <div>
                              <strong className="text-red-600 dark:text-red-400">Stack Trace:</strong>
                              <pre className="mt-1 whitespace-pre-wrap text-xs text-gray-600 dark:text-gray-400 max-h-40 overflow-y-auto">
                                {error.stack}
                              </pre>
                            </div>
                          )}
                          
                          {this.state.errorInfo?.componentStack && (
                            <div>
                              <strong className="text-red-600 dark:text-red-400">Component Stack:</strong>
                              <pre className="mt-1 whitespace-pre-wrap text-xs text-gray-600 dark:text-gray-400 max-h-40 overflow-y-auto">
                                {this.state.errorInfo.componentStack}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* Show details toggle for production */}
              {!isDevelopment && !this.state.showDetails && (
                <div className="text-center">
                  <Button
                    onClick={this.toggleDetails}
                    variant="ghost"
                    size="sm"
                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    Show technical details
                    <ChevronDown className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              )}

              {/* Retry count indicator */}
              {this.state.retryCount > 0 && (
                <div className="text-center text-sm text-gray-500">
                  Retry attempts: {this.state.retryCount}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Hook-based error boundary for functional components
 */
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = React.useCallback(() => {
    setError(null);
  }, []);

  const captureError = React.useCallback((error: Error) => {
    setError(error);
  }, []);

  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  return { captureError, resetError };
}

/**
 * Higher-order component for wrapping components with error boundary
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

export default ErrorBoundary;