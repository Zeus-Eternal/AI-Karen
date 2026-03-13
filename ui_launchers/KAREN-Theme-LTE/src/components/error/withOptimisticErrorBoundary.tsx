/**
 * Higher-Order Component for Optimistic Error Boundaries
 * 
 * This HOC wraps components with error boundary functionality
 * specifically designed for optimistic updates.
 */

import React, { Component, ReactNode, ErrorInfo } from 'react';

interface OptimisticErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode | ((props: {
    error: Error | null;
    retry: () => void;
    canRetry: boolean;
    retryCount: number;
  }) => ReactNode);
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  enableRetry?: boolean;
  maxRetries?: number;
}

interface OptimisticErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  retryCount: number;
}

class OptimisticErrorBoundary extends Component<OptimisticErrorBoundaryProps, OptimisticErrorBoundaryState> {
  constructor(props: OptimisticErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<OptimisticErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.props.onError?.(error, errorInfo);
    
    // Log error for debugging
    console.error('Optimistic Error Boundary caught an error:', error, errorInfo);
  }

  handleRetry = () => {
    const { maxRetries = 3 } = this.props;
    
    if (this.state.retryCount < maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        retryCount: prevState.retryCount + 1
      }));
    }
  };

  render() {
    if (this.state.hasError) {
      const { fallback, enableRetry = true, maxRetries = 3 } = this.props;
      const canRetry = enableRetry && this.state.retryCount < maxRetries;

      if (fallback) {
        return typeof fallback === 'function' 
          ? fallback({ 
              error: this.state.error, 
              retry: this.handleRetry, 
              canRetry,
              retryCount: this.state.retryCount 
            })
          : fallback;
      }

      return (
        <div className="optimistic-error-boundary-fallback">
          <h3>Something went wrong</h3>
          <p>{this.state.error?.message || 'An unexpected error occurred'}</p>
          {canRetry && (
            <button onClick={this.handleRetry} className="retry-button">
              Retry ({maxRetries - this.state.retryCount} attempts left)
            </button>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component that wraps a component with OptimisticErrorBoundary
 */
export function withOptimisticErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<OptimisticErrorBoundaryProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <OptimisticErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </OptimisticErrorBoundary>
  );

  WrappedComponent.displayName = `withOptimisticErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

export default OptimisticErrorBoundary;