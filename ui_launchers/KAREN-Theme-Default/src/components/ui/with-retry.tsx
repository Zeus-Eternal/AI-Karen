"use client";

import React, {
  ComponentType,
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { retryMechanism, type RetryConfig } from "@/utils/retry-mechanisms";
import { RetryCard, LoadingRetry } from "./retry-components";

export interface WithRetryOptions extends Partial<RetryConfig> {
  retryOnMount?: boolean;
  showLoadingState?: boolean;
  showRetryCard?: boolean;
  loadingComponent?: ReactNode;
  errorComponent?: (error: Error, retry: () => void) => ReactNode;
  retryKey?: string;
}

export interface WithRetryProps {
  retryConfig?: WithRetryOptions;
}

export interface WithRetryState {
  error: Error | null;
  isLoading: boolean;
  isRetrying: boolean;
  attempt: number;
  hasRetried: boolean;
}

/**
 * Higher-order component that adds retry functionality to any component.
 * It does not assume what the wrapped component does; it simply exposes retry controls + state.
 */
export function withRetry<P extends object>(
  WrappedComponent: ComponentType<P>,
  defaultOptions: WithRetryOptions = {}
) {
  return function WithRetryComponent(props: P & WithRetryProps) {
    const { retryConfig = {}, ...componentProps } = props as WithRetryProps & P;

    const options: WithRetryOptions = useMemo(
      () => ({
        // sensible visual defaults
        showLoadingState: true,
        showRetryCard: true,
        maxAttempts: 3,
        baseDelay: 1000,
        backoffFactor: 2,
        ...defaultOptions,
        ...retryConfig,
      }),
      [defaultOptions, retryConfig]
    );

    const [state, setState] = useState<WithRetryState>({
      error: null,
      isLoading: options.retryOnMount ?? false,
      isRetrying: false,
      attempt: 0,
      hasRetried: false,
    });

    /**
     * This "operation" is intentionally generic. In practice, use the
     * `useAsyncRetry` hook below for concrete async work; this HOC mainly
     * gives you a consistent visual + control surface for retries.
     */
    const retryOperation = useCallback(async () => {
      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
        isRetrying: prev.hasRetried,
      }));
      try {
        // tiny async tick to simulate work; real work belongs in wrapped component logic
        await new Promise((resolve) => setTimeout(resolve, 100));
        setState((prev) => ({
          ...prev,
          isLoading: false,
          isRetrying: false,
          error: null,
        }));
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        setState((prev) => ({
          ...prev,
          error: err,
          isLoading: false,
          isRetrying: false,
          attempt: prev.attempt + 1,
          hasRetried: true,
        }));
      }
    }, []);

    const handleRetry = useCallback(() => {
      void retryOperation();
    }, [retryOperation]);

    useEffect(() => {
      if (options.retryOnMount) {
        void retryOperation();
      }
    }, [options.retryOnMount, retryOperation]);

    // Loading presentation
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

    // Error presentation
    if (state.error && options.showRetryCard) {
      if (options.errorComponent) {
        return <>{options.errorComponent(state.error, handleRetry)}</>;
      }
      const maxAttempts = options.maxAttempts ?? 3;
      return (
        <RetryCard
          error={state.error}
          onRetry={handleRetry}
          isRetrying={state.isRetrying}
          attempt={state.attempt}
          maxAttempts={maxAttempts}
          canRetry={state.attempt < maxAttempts}
        />
      );
    }

    // Render wrapped component with retry controls injected
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
 * Hook for adding retry functionality to async operations.
 * Uses retryMechanism.withRetry for backoff, caps, and onRetry callbacks.
 */
export function useAsyncRetry<T>(
  asyncOperation: () => Promise<T>,
  options: WithRetryOptions = {}
) {
  const merged: WithRetryOptions = {
    maxAttempts: 3,
    baseDelay: 1000,
    backoffFactor: 2,
    ...options,
  };

  const [state, setState] = useState<{
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

  const execute = useCallback(async () => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
      isRetrying: prev.attempt > 0,
    }));

    try {
      const result = await retryMechanism.withRetry(
        asyncOperation,
        {
          maxAttempts: merged.maxAttempts ?? 3,
          baseDelay: merged.baseDelay ?? 1000,
          backoffFactor: merged.backoffFactor ?? 2,
          jitter: merged.jitter ?? true,
          onRetry: (error, attempt) => {
            setState((prev) => ({
              ...prev,
              attempt,
              isRetrying: true,
              error: error instanceof Error ? error : new Error(String(error)),
            }));
            merged.onRetry?.(error, attempt);
          },
        },
        merged.retryKey
      );

      setState((prev) => ({
        ...prev,
        data: result,
        isLoading: false,
        isRetrying: false,
        error: null,
      }));
      return result;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      setState((prev) => ({
        ...prev,
        error: err,
        isLoading: false,
        isRetrying: false,
        attempt: prev.attempt + 1,
      }));
      throw err;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [asyncOperation, merged.maxAttempts, merged.baseDelay, merged.backoffFactor, merged.jitter, merged.retryKey]);

  const retry = useCallback(() => execute(), [execute]);

  const reset = useCallback(() => {
    setState({
      data: null,
      error: null,
      isLoading: false,
      isRetrying: false,
      attempt: 0,
    });
  }, []);

  useEffect(() => {
    if (merged.retryOnMount) {
      void execute();
    }
  }, [merged.retryOnMount, execute]);

  return {
    ...state,
    execute,
    retry,
    reset,
    canRetry: state.attempt < (merged.maxAttempts ?? 3),
  };
}

/**
 * Component that wraps children with automatic retry on error boundaries.
 * Useful for rendering-time crashes that hooks can't intercept.
 */
export interface RetryBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, retry: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  maxRetries?: number;
  retryDelay?: number;
  className?: string;
}

export interface RetryBoundaryState {
  hasError: boolean;
  error: Error | null;
  retryCount: number;
  isRetrying: boolean;
}

export class RetryBoundary extends React.Component<
  RetryBoundaryProps,
  RetryBoundaryState
> {
  private retryTimeoutId: ReturnType<typeof setTimeout> | null = null;

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
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.props.onError?.(error, errorInfo);
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) clearTimeout(this.retryTimeoutId);
  }

  handleRetry = () => {
    const maxRetries = this.props.maxRetries ?? 3;
    if (this.state.retryCount >= maxRetries) return;

    this.setState({ isRetrying: true });
    const delay = this.props.retryDelay ?? 1000;

    this.retryTimeoutId = setTimeout(() => {
      this.setState((prev) => ({
        hasError: false,
        error: null,
        retryCount: prev.retryCount + 1,
        isRetrying: false,
      }));
    }, delay);
  };

  render() {
    if (this.state.hasError) {
      const maxRetries = this.props.maxRetries ?? 3;
      const canRetry = this.state.retryCount < maxRetries;

      if (this.props.fallback) {
        return this.props.fallback(this.state.error!, this.handleRetry);
      }

      return (
        <div className={this.props.className}>
          <RetryCard
            title="Component Error"
            description="This component encountered an error and stopped working."
            error={this.state.error!}
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
 * Hook for creating retry-enabled fetch operations.
 * Uses retryMechanism.retryFetch internally (with backoff/jitter/caps).
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
