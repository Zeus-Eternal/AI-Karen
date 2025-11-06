"use client";

import React from 'react';
import { ErrorBoundary } from './ErrorBoundary';

interface GlobalErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export function GlobalErrorBoundary({ children, fallback, onError }: GlobalErrorBoundaryProps) {
  return (
    <ErrorBoundary
      boundaryName="Global Error Boundary"
      fallback={fallback}
      onError={onError}
    >
      {children}
    </ErrorBoundary>
  );
}

/**
 * Higher-order component to wrap components with global error boundary
 */
export function withGlobalErrorBoundary<P extends object>(
  Wrapped: React.ComponentType<P>,
  errorBoundaryProps?: Omit<GlobalErrorBoundaryProps, "children">
) {
  return function WrappedComponent(props: P) {
    return (
      <GlobalErrorBoundary {...errorBoundaryProps}>
        <Wrapped {...props} />
      </GlobalErrorBoundary>
    );
  };
}

export default GlobalErrorBoundary;