"use client";

import * as React from 'react';
import { ErrorBoundary, type FallbackProps } from 'react-error-boundary';

import { SimpleErrorFallback } from './SimpleErrorFallback';

export interface GlobalErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: (
    error: Error,
    errorInfo: { componentStack: string },
    retry: () => void
  ) => React.ReactNode;
  onError?: (error: Error, errorInfo: { componentStack: string }) => void;
  showIntelligentResponse?: boolean;
  enableSessionRecovery?: boolean;
}

const SESSION_RECOVERY_KEY_PREFIX = 'karen';

function performSessionRecovery() {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    const storage = window.sessionStorage;
    for (const key of Object.keys(storage)) {
      if (key.toLowerCase().startsWith(SESSION_RECOVERY_KEY_PREFIX)) {
        storage.removeItem(key);
      }
    }
  } catch (error) {
    console.warn('GlobalErrorBoundary session recovery failed', error);
  }
}

const GlobalErrorBoundary: React.FC<GlobalErrorBoundaryProps> = ({
  children,
  fallback,
  onError,
  showIntelligentResponse = false,
  enableSessionRecovery = true,
}) => {
  const fallbackRender = React.useCallback(
    (props: FallbackProps) => {
      const { error, resetErrorBoundary } = props;
      const componentStack =
        'componentStack' in props && typeof props.componentStack === 'string'
          ? props.componentStack
          : '';

      if (fallback) {
        return fallback(error, { componentStack }, resetErrorBoundary);
      }

      return (
        <SimpleErrorFallback
          error={error}
          resetErrorBoundary={resetErrorBoundary}
          message={
            showIntelligentResponse
              ? 'Karen detected an issue and is attempting to recover automatically.'
              : undefined
          }
          showDetails={process.env.NODE_ENV !== 'production'}
        />
      );
    },
    [fallback, showIntelligentResponse]
  );

  const handleError = React.useCallback(
    (error: Error, info: { componentStack: string }) => {
      if (enableSessionRecovery) {
        performSessionRecovery();
      }

      onError?.(error, info);
    },
    [enableSessionRecovery, onError]
  );

  return (
    <ErrorBoundary
      fallbackRender={fallbackRender}
      onError={handleError}
      resetKeys={[showIntelligentResponse, enableSessionRecovery]}
    >
      {children}
    </ErrorBoundary>
  );
};

export { GlobalErrorBoundary };
export default GlobalErrorBoundary;
