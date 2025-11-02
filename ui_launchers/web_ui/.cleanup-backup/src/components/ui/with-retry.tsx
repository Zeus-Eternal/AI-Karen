'use client';

import React, { ComponentType, ReactNode } from 'react';
import { retryMechanism, RetryConfig } from '@/utils/retry-mechanisms';
import { RetryCard, LoadingRetry } from './retry-components';

interface WithRetryOptions extends Partial<RetryConfig> {
  retryOnMount?: boolean;
  showLoadingState?: boolean;
  showRetryCard?: boolean;
  loadingComponent?: ReactNode;
  errorComponent?: (error: Error, retry: () => void) => ReactNode;
  retryKey?: string;
}

interface WithRetryProps {
  retryConfig?: WithRetryOptions;
}

interface WithRetryState {
  error: Error | null;
  isLoading: boolean;
  isRetrying: boolean;
  attempt: number;
  hasRetried: boolean;
}

/**
 * Higher-order component that adds retry functionality to any component
 */
export function withRetry<P extends object>(
  WrappedComponent: ComponentType<P>,
  defaultOptions: WithRetryOptions = {}
) {
  return function WithRetryComponent(props: P & WithRetryProps) {
    const { retryConfig = {}, ...componentProps } = props;
    const options = { ...defaultOptions, ...retryConfig };
    
    const [state, setState] = React.useState<WithRetryState>({
      error: null,
      isLoading: options.retryOnMount ?? false,
      isRetrying: false,
      attempt: 0,
      hasRetried: false,
    });

    const retryOperation = React.useCallback(async () => {
      setState(prev => ({ 
        ...prev, 
        isLoading: true, 
        error: null,
        isRetrying: prev.hasRetried,
      }));

      try {
        // Simulate the component rendering as the "operation"
        // In practice, this would be used with components that perform async operations
        await new Promise(resolve => setTimeout(resolve, 100));
        
        setState(prev => ({ 
          ...prev, 
          isLoading: false, 
          isRetrying: false,
          error: null,
        }));
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        setState(prev => ({ 
          ...prev, 
          error: err, 
          isLoading: false,
          isRetrying: false,
          attempt: prev.attempt + 1,
          hasRetried: true,
        }));
      }
    }, []);

    const handleRetry = React.useCallback(() => {
      retryOperation();
    }, [retryOperation]);

    React.useEffect(() => {
      if (options.retryOnMount) {
        retryOperation();
      }
    }, [options.retryOnMount, retryOperation]);

    // Show loading state
    if (state.isLoading && options.showLoadingState) {
      if (options.loadingComponent) {
        return <>{options.loadingComponent}</>;
      }
      
      return (
        <LoadingRetry
          isLoading={state.isLoading}
          isRetrying={state.isRetrying}
          error={null}
          onRetry={handleRetry}
        >
          <div />
        </LoadingRetry>
      );
    }

    // Show error state with retry option
    if (state.error && options.showRetryCard) {
      if (options.errorComponent) {
        return <>{options.errorComponent(state.error, handleRetry)}</>;
      }
      
      return (
        <RetryCard
          error={state.error}
          onRetry={handleRetry}
          isRetrying={state.isRetrying}
          attempt={state.attempt}
          maxAttempts={options.maxAttempts || 3}
          canRetry={state.attempt < (options.maxAttempts || 3)}
        />
      );
    }

    // Render the wrapped component with retry props
    return (
      <WrappedComponent
        {...(componentProps as P)}
        retryState={state}
        onRetry={handleRetry}
      />
    );
  };
}

/**
 * Hook for adding retry functionality to async operations
 */
export function useAsyncRetry<T>(
  asyncOperation: () => Promise<T>,
  options: WithRetryOptions = {}
) {
  const [state, setState] = React.useState<{
    data: T | null;
    error: Error | null;
    isLoading: boolean;
    isRetrying: boolean;
    attempt: number;
  }>({
    data: null,
    error: null,
    isLoading: false,
    isRetrying: false,
    attempt: 0,
  });

  const execute = React.useCallback(async () => {
    setState(prev => ({ 
      ...prev, 
      isLoading: true, 
      error: null,
      isRetrying: prev.attempt > 0,
    }));

    try {
      const result = await retryMechanism.withRetry(
        asyncOperation,
        {
          maxAttempts: options.maxAttempts || 3,
          baseDelay: options.baseDelay || 1000,
          backoffFactor: options.backoffFactor || 2,
          ...options,
          onRetry: (error, attempt) => {
            setState(prev => ({ 
              ...prev, 
              attempt,
              isRetrying: true,
              error: error instanceof Error ? error : new Error(String(error)),
            }));
            options.onRetry?.(error, attempt);
          },
        },
        options.retryKey
      );

      setState(prev => ({ 
        ...prev, 
        data: result, 
        isLoading: false,
        isRetrying: false,
        error: null,
      }));

      return result;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      setState(prev => ({ 
        ...prev, 
        error: err, 
        isLoading: false,
        isRetrying: false,
        attempt: prev.attempt + 1,
      }));
      throw err;
    }
  }, [asyncOperation, options]);

  const retry = React.useCallback(() => {
    return execute();
  }, [execute]);

  const reset = React.useCallback(() => {
    setState({
      data: null,
      error: null,
      isLoading: false,
      isRetrying: false,
      attempt: 0,
    });
  }, []);

  React.useEffect(() => {
    if (options.retryOnMount) {
      execute();
    }
  }, [options.retryOnMount, execute]);

  return {
    ...state,
    execute,
    retry,
    reset,
    canRetry: state.attempt < (options.maxAttempts || 3),
  };
}

/**
 * Component that wraps children with automatic retry on error boundaries
 */
interface RetryBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, retry: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  maxRetries?: number;
  retryDelay?: number;
  className?: string;
}

interface RetryBoundaryState {
  hasError: boolean;
  error: Error | null;
  retryCount: number;
  isRetrying: boolean;
}

export class RetryBoundary extends React.Component<RetryBoundaryProps, RetryBoundaryState> {
  private retryTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: RetryBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      retryCount: 0,
      isRetrying: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<RetryBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('RetryBoundary caught an error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  handleRetry = () => {
    const maxRetries = this.props.maxRetries || 3;
    
    if (this.state.retryCount >= maxRetries) {
      return;
    }

    this.setState({ isRetrying: true });

    const delay = this.props.retryDelay || 1000;
    this.retryTimeoutId = setTimeout(() => {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        retryCount: prevState.retryCount + 1,
        isRetrying: false,
      }));
    }, delay);
  };

  render() {
    if (this.state.hasError) {
      const maxRetries = this.props.maxRetries || 3;
      const canRetry = this.state.retryCount < maxRetries;

      if (this.props.fallback) {
        return this.props.fallback(this.state.error!, this.handleRetry);
      }

      return (
        <div className={this.props.className}>
          <RetryCard
            title="Component Error"
            description="This component encountered an error and stopped working."
            error={this.state.error}
            onRetry={this.handleRetry}
            isRetrying={this.state.isRetrying}
            attempt={this.state.retryCount}
            maxAttempts={maxRetries}
            canRetry={canRetry}
          />
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Hook for creating retry-enabled fetch operations
 */
export function useRetryFetch(
  url: string,
  options: RequestInit = {},
  retryOptions: WithRetryOptions = {}
) {
  return useAsyncRetry(
    () => retryMechanism.retryFetch(url, options, retryOptions),
    {
      ...retryOptions,
      retryKey: `fetch-${url}`,
    }
  );
}

// Exports are already declared above with the function definitions