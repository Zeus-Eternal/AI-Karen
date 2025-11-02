"use client";

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { useUIStore } from '../../store';
interface OptimisticErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
  errorId: string;
}
interface OptimisticErrorBoundaryProps {
  children: ReactNode;
  fallback?: (props: {
    error: Error | null;
    errorInfo: ErrorInfo | null;
    retry: () => void;
    reset: () => void;
    retryCount: number;
    canRetry: boolean;
  }) => ReactNode;
  maxRetries?: number;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onRetry?: (retryCount: number) => void;
  onReset?: () => void;
  resetKeys?: Array<string | number>;
  resetOnPropsChange?: boolean;
}
class OptimisticErrorBoundaryClass extends Component<
> {
  private resetTimeoutId: number | null = null;
  private maxRetries: number;
  constructor(props: OptimisticErrorBoundaryProps) {
    super(props);
    this.maxRetries = props.maxRetries || 3;
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      errorId: '',
    };
  }
  static getDerivedStateFromError(error: Error): Partial<OptimisticErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
  }
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    // Log error to UI store
    const { setError } = useUIStore.getState();
    setError(this.state.errorId, error.message);
    // Call onError callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    // Log to console in development
  }
  componentDidUpdate(prevProps: OptimisticErrorBoundaryProps) {
    const { resetKeys, resetOnPropsChange } = this.props;
    const { hasError } = this.state;
    // Reset on props change if enabled
    if (hasError && resetOnPropsChange && prevProps.children !== this.props.children) {
      this.resetErrorBoundary();
    }
    // Reset on resetKeys change
    if (hasError && resetKeys && prevProps.resetKeys) {
      const hasResetKeyChanged = resetKeys.some(
        (key, index) => key !== prevProps.resetKeys![index]
      );
      if (hasResetKeyChanged) {
        this.resetErrorBoundary();
      }
    }
  }
  componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
    // Clear error from store
    const { clearError } = useUIStore.getState();
    clearError(this.state.errorId);
  }
  resetErrorBoundary = () => {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
    // Clear error from store
    const { clearError } = useUIStore.getState();
    clearError(this.state.errorId);
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      errorId: '',

    if (this.props.onReset) {
      this.props.onReset();
    }
  };
  retryRender = () => {
    const { retryCount } = this.state;
    const newRetryCount = retryCount + 1;
    if (newRetryCount <= this.maxRetries) {
      this.setState({ retryCount: newRetryCount });
      if (this.props.onRetry) {
        this.props.onRetry(newRetryCount);
      }
      // Reset after a short delay to allow for state updates
      this.resetTimeoutId = window.setTimeout(() => {
        this.resetErrorBoundary();
      }, 100);
    }
  };
  render() {
    const { hasError, error, errorInfo, retryCount } = this.state;
    const { fallback, children } = this.props;
    const canRetry = retryCount < this.maxRetries;
    if (hasError) {
      if (fallback) {
        return fallback({
          error,
          errorInfo,
          retry: this.retryRender,
          reset: this.resetErrorBoundary,
          retryCount,
          canRetry,

      }
      return (
        <DefaultErrorFallback
          error={error}
          errorInfo={errorInfo}
          retry={this.retryRender}
          reset={this.resetErrorBoundary}
          retryCount={retryCount}
          canRetry={canRetry}
        />
      );
    }
    return children;
  }
}
// Default error fallback component
function DefaultErrorFallback({
  error,
  retry,
  reset,
  retryCount,
  canRetry,
}: {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retry: () => void;
  reset: () => void;
  retryCount: number;
  canRetry: boolean;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 bg-red-50 border border-red-200 rounded-lg sm:p-4 md:p-6">
      <div className="text-red-600 mb-4">
        <svg className="w-12 h-12 " fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-red-800 mb-2">
      </h3>
      <p className="text-red-600 text-center mb-4 max-w-md">
        {error?.message || 'An unexpected error occurred'}
      </p>
      {retryCount > 0 && (
        <p className="text-sm text-red-500 mb-4 md:text-base lg:text-lg">
          Retry attempt: {retryCount}
        </p>
      )}
      <div className="flex gap-2">
        {canRetry && (
          <button
            onClick={retry}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
           aria-label="Button">
          </button>
        )}
        <button
          onClick={reset}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
         aria-label="Button">
        </button>
      </div>
      {process.env.NODE_ENV === 'development' && error && (
        <details className="mt-4 w-full max-w-2xl ">
          <summary className="cursor-pointer text-sm text-red-600 hover:text-red-800 md:text-base lg:text-lg">
            Error Details (Development)
          </summary>
          <pre className="mt-2 p-4 bg-red-100 rounded text-xs overflow-auto sm:text-sm md:text-base">
            {error.stack}
          </pre>
        </details>
      )}
    </div>
  );
}
// Wrapper component with hooks support
export function OptimisticErrorBoundary(props: OptimisticErrorBoundaryProps) {
  return <OptimisticErrorBoundaryClass {...props} />;
}
// Higher-order component for wrapping components with error boundary
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
