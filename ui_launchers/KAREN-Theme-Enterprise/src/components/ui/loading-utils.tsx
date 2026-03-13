"use client";

import React from 'react';

import { Loading } from './loading';

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

export function useLoadingState(initialState = false) {
  const [isLoading, setIsLoading] = React.useState(initialState);
  const [error, setError] = React.useState<Error | null>(null);

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

  const withLoadingAsync = React.useCallback(
    async <T,>(asyncFn: () => Promise<T>): Promise<T | null> => {
      try {
        startLoading();
        const result = await asyncFn();
        stopLoading();
        return result;
      } catch (err) {
        setLoadingError(err instanceof Error ? err : new Error('Unknown error'));
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
    withLoading: withLoadingAsync,
  };
}
