import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorType?: 'network' | 'server' | 'client' | 'unknown';
}

/**
 * Global Error Boundary Component
 * Catches JavaScript errors in child component tree, logs them, and displays a fallback UI
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    // Categorize error type for better handling
    let errorType: 'network' | 'server' | 'client' | 'unknown' = 'unknown';
    
    if (error.message.includes('fetch') ||
        error.message.includes('network') ||
        error.message.includes('connection') ||
        error.message.includes('huggingface.co') ||
        error.message.includes('offline mode')) {
      errorType = 'network';
    } else if (error.message.includes('500') ||
               error.message.includes('server') ||
               error.message.includes('model loading failed') ||
               error.message.includes('DISTILBERT MODEL LOADING FAILED')) {
      errorType = 'server';
    } else if (error.message.includes('component') ||
               error.message.includes('render') ||
               error.message.includes('React')) {
      errorType = 'client';
    }
    
    return { hasError: true, error, errorType };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log the error to console in development
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Store error info in state for potential display in development
    this.setState({
      error,
      errorInfo
    });
    
    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    
    // In production, you might want to send error to an error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Example: sendErrorToService(error, errorInfo);
      console.error('Production error captured:', {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      });
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined, errorType: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      // Default fallback UI with enhanced error handling
      const errorType = this.state.errorType || 'unknown';
      const getErrorIcon = () => {
        switch (errorType) {
          case 'network':
            return (
              <svg className="h-6 w-6 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
              </svg>
            );
          case 'server':
            return (
              <svg className="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
              </svg>
            );
          default:
            return (
              <svg className="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            );
        }
      };

      const getErrorTitle = () => {
        switch (errorType) {
          case 'network':
            return 'Connection Error';
          case 'server':
            return 'Service Unavailable';
          case 'client':
            return 'Application Error';
          default:
            return 'Something went wrong';
        }
      };

      const getErrorDescription = () => {
        const { error } = this.state;
        
        if (error?.message.includes('huggingface.co') || error?.message.includes('offline mode')) {
          return 'The AI model service is currently unavailable in offline mode. This may affect memory and chat features. Please check your internet connection or try again later.';
        }
        
        switch (errorType) {
          case 'network':
            return 'Unable to connect to the server. Please check your internet connection and try again.';
          case 'server':
            return 'The server is temporarily unavailable or experiencing issues. Please try again in a few moments.';
          case 'client':
            return 'An unexpected error occurred in the application. Please try refreshing the page.';
          default:
            return error?.message || 'We\'re sorry, but something unexpected happened. The error has been logged.';
        }
      };

      return (
        <div className="error-boundary min-h-screen flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border border-red-200 dark:border-red-800">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                {getErrorIcon()}
              </div>
              <div className="ml-3">
                <h1 className="text-lg font-medium text-gray-900 dark:text-white">{getErrorTitle()}</h1>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {getErrorDescription()}
                </p>
              </div>
            </div>
            
            {/* Show error details in development */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-4 p-3 bg-gray-100 dark:bg-gray-700 rounded text-sm">
                <summary className="cursor-pointer font-medium text-gray-800 dark:text-gray-200">
                  Error Details (Development Only)
                </summary>
                <div className="mt-2 space-y-2">
                  <div>
                    <strong>Error Type:</strong> {errorType}
                  </div>
                  <div>
                    <strong>Error Message:</strong>
                    <pre className="mt-1 p-2 bg-red-50 dark:bg-red-900/20 rounded text-red-800 dark:text-red-400 overflow-auto">
                      {this.state.error.message}
                    </pre>
                  </div>
                  
                  {this.state.error.stack && (
                    <div>
                      <strong>Stack Trace:</strong>
                      <pre className="mt-1 p-2 bg-red-50 dark:bg-red-900/20 rounded text-red-800 dark:text-red-400 text-xs overflow-auto">
                        {this.state.error.stack}
                      </pre>
                    </div>
                  )}
                  
                  {this.state.errorInfo?.componentStack && (
                    <div>
                      <strong>Component Stack:</strong>
                      <pre className="mt-1 p-2 bg-red-50 dark:bg-red-900/20 rounded text-red-800 dark:text-red-400 text-xs overflow-auto">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            {/* Additional help for specific error types */}
            {errorType === 'network' && (
              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded text-sm">
                <div className="text-blue-800 dark:text-blue-200 space-y-1">
                  <p>• Check your internet connection</p>
                  <p>• Verify the server is running</p>
                  <p>• Try disabling any VPN or proxy</p>
                </div>
              </div>
            )}

            {errorType === 'server' && (
              <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-900/20 rounded text-sm">
                <div className="text-orange-800 dark:text-orange-200 space-y-1">
                  <p>• The server may be restarting or updating</p>
                  <p>• Check server logs for more details</p>
                  <p>• Some features may be temporarily unavailable</p>
                </div>
              </div>
            )}
            
            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <button
                onClick={this.handleReset}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="flex-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-medium py-2 px-4 rounded focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Hook for using ErrorBoundary in functional components
 */
export const useErrorHandler = (onError?: (error: Error, errorInfo: ErrorInfo) => void) => {
  return React.useCallback((error: Error, errorInfo: ErrorInfo) => {
    console.error('Error caught by error handler:', error, errorInfo);
    
    if (onError) {
      onError(error, errorInfo);
    }
    
    // In production, send to error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Example: sendErrorToService(error, errorInfo);
    }
  }, [onError]);
};

/**
 * Higher-order component for wrapping components with error boundary
 */
export const withErrorBoundary = function<P extends object>(
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
};

export default ErrorBoundary;