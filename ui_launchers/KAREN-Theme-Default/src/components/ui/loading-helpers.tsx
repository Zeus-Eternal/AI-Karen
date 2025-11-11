"use client";

import * as React from "react";

import { Loading } from "./loading";

/**
 * Higher-order component for adding loading states without impacting
 * Next.js fast refresh behaviour in the main loading component module.
 */
export function withLoading<P extends object>(
  Component: React.ComponentType<P>,
  LoadingComponent: React.ComponentType = Loading
) {
  return function WithLoadingComponent(props: P & { isLoading?: boolean }) {
    const { isLoading, ...componentProps } = props;

    if (isLoading) {
      return <LoadingComponent />;
    }

    return <Component {...(componentProps as P)} />;
  };
}

/**
 * Loading state hook for consistent loading management.
 */
export function useLoadingState(initialState = false) {
  const [isLoading, setIsLoading] = React.useState(initialState);
  const [error, setError] = React.useState<Error | null>(null);

  type WithLoadingHandler = <T>(asyncFn: () => Promise<T>) => Promise<T | null>;

  const startLoading = React.useCallback(() => {
    setIsLoading(true);
    setError(null);
  }, []);

  const stopLoading = React.useCallback(() => {
    setIsLoading(false);
  }, []);

  const setLoadingError = React.useCallback((error: Error) => {
    setError(error);
    setIsLoading(false);
  }, []);

  const withLoadingHandler = React.useCallback<WithLoadingHandler>(
    async (asyncFn) => {
      try {
        startLoading();
        const result = await asyncFn();
        stopLoading();
        return result;
      } catch (err) {
        setLoadingError(err instanceof Error ? err : new Error("Unknown error"));
        return null;
      }
    },
    [startLoading, stopLoading, setLoadingError]
  );

  return {
    isLoading,
    error,
    startLoading,
    stopLoading,
    setLoadingError,
    withLoading: withLoadingHandler,
  };
}
