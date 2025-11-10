"use client";

import * as React from "react";

import {
  fetchWithTimeout,
  retryMechanism,
  type RetryConfig,
} from "@/utils/retry-mechanisms";

import { LoadingRetry, RetryCard } from "./retry-components";

export interface WithRetryOptions extends Partial<RetryConfig> {
  retryOnMount?: boolean;
  showLoadingState?: boolean;
  showRetryCard?: boolean;
  loadingComponent?: React.ReactNode;
  errorComponent?: (error: Error, retry: () => void) => React.ReactNode;
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

export interface WithRetryInjectedProps {
  retryState: WithRetryState;
  onRetry: () => void;
}

export function withRetry<P extends object>(
  WrappedComponent: React.ComponentType<P & WithRetryInjectedProps>,
  defaultOptions: WithRetryOptions = {},
) {
  return function WithRetryComponent(props: P & WithRetryProps) {
    const { retryConfig = {}, ...rest } = props;

    const options = React.useMemo<WithRetryOptions>(
      () => ({
        showLoadingState: true,
        showRetryCard: true,
        maxAttempts: 3,
        baseDelay: 1000,
        backoffFactor: 2,
        ...defaultOptions,
        ...retryConfig,
      }),
      [defaultOptions, retryConfig],
    );

    const [state, setState] = React.useState<WithRetryState>({
      error: null,
      isLoading: options.retryOnMount ?? false,
      isRetrying: false,
      attempt: 0,
      hasRetried: false,
    });

    const retryOperation = React.useCallback(async () => {
      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
        isRetrying: prev.hasRetried,
      }));

      try {
        await new Promise((resolve) => setTimeout(resolve, 100));
        setState((prev) => ({
          ...prev,
          isLoading: false,
          isRetrying: false,
          error: null,
        }));
      } catch (error) {
        const resolvedError = error instanceof Error ? error : new Error(String(error));
        setState((prev) => ({
          ...prev,
          error: resolvedError,
          isLoading: false,
          isRetrying: false,
          attempt: prev.attempt + 1,
          hasRetried: true,
        }));
      }
    }, []);

    const handleRetry = React.useCallback(() => {
      void retryOperation();
    }, [retryOperation]);

    React.useEffect(() => {
      if (options.retryOnMount) {
        void retryOperation();
      }
    }, [options.retryOnMount, retryOperation]);

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

    return (
      <WrappedComponent
        {...(rest as P)}
        retryState={state}
        onRetry={handleRetry}
      />
    );
  };
}

export function useAsyncRetry<T>(
  asyncOperation: () => Promise<T>,
  options: WithRetryOptions = {},
) {
  const merged: WithRetryOptions = React.useMemo(
    () => ({
      maxAttempts: 3,
      baseDelay: 1000,
      backoffFactor: 2,
      ...options,
    }),
    [options],
  );

  const [state, setState] = React.useState({
    data: null as T | null,
    error: null as Error | null,
    isLoading: false,
    isRetrying: false,
    attempt: 0,
  });

  const execute = React.useCallback(async () => {
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
          onRetry: (error, attempt, nextDelayMs) => {
            setState((prev) => ({
              ...prev,
              attempt,
              isRetrying: true,
              error: error instanceof Error ? error : new Error(String(error)),
            }));
            merged.onRetry?.(error, attempt, nextDelayMs);
          },
        },
        merged.retryKey,
      );

      setState({
        data: result,
        error: null,
        isLoading: false,
        isRetrying: false,
        attempt: 0,
      });
      return result;
    } catch (error) {
      const resolvedError = error instanceof Error ? error : new Error(String(error));
      setState((prev) => ({
        ...prev,
        error: resolvedError,
        isLoading: false,
        isRetrying: false,
        attempt: prev.attempt + 1,
      }));
      throw resolvedError;
    }
  }, [asyncOperation, merged]);

  const retry = React.useCallback(() => execute(), [execute]);

  const reset = React.useCallback(() => {
    setState({ data: null, error: null, isLoading: false, isRetrying: false, attempt: 0 });
  }, []);

  React.useEffect(() => {
    if (merged.retryOnMount) {
      void execute();
    }
  }, [execute, merged.retryOnMount]);

  return {
    ...state,
    execute,
    retry,
    reset,
    canRetry: state.attempt < (merged.maxAttempts ?? 3),
  };
}

export interface RetryBoundaryProps {
  children: React.ReactNode;
  fallback?: (error: Error, retry: () => void) => React.ReactNode;
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
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  handleRetry = () => {
    const maxRetries = this.props.maxRetries ?? 3;
    if (this.state.retryCount >= maxRetries) {
      return;
    }

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

export function useRetryFetch(
  url: string,
  options: RequestInit = {},
  retryOptions: WithRetryOptions = {},
) {
  const mergedOptions = React.useMemo<WithRetryOptions>(
    () => ({
      ...retryOptions,
      retryKey: retryOptions.retryKey ?? `fetch-${url}`,
    }),
    [retryOptions, url],
  );

  return useAsyncRetry(
    async () => {
      const response = await fetchWithTimeout(
        url,
        options,
        mergedOptions.timeoutMs ?? 0,
      );

      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
        (error as Error & { status?: number }).status = response.status;
        (error as Error & { response?: Response }).response = response;
        throw error;
      }

      return response;
    },
    mergedOptions,
  );
}
