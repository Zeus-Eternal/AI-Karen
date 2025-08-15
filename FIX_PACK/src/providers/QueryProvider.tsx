import React, { Suspense } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from '../lib/queryClient';
import { ErrorBoundary } from 'react-error-boundary';

interface QueryErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

// Error fallback component for query errors
const QueryErrorFallback: React.FC<QueryErrorFallbackProps> = ({ 
  error, 
  resetErrorBoundary 
}) => (
  <div className="query-error-fallback" role="alert">
    <h2>Something went wrong with data loading</h2>
    <details style={{ whiteSpace: 'pre-wrap' }}>
      <summary>Error details</summary>
      {error.message}
    </details>
    <button onClick={resetErrorBoundary}>Try again</button>
  </div>
);

// Loading fallback for suspense
const QueryLoadingFallback: React.FC = () => (
  <div className="query-loading-fallback" aria-label="Loading">
    <div className="loading-spinner" />
    <span>Loading...</span>
  </div>
);

interface QueryProviderProps {
  children: React.ReactNode;
  enableDevtools?: boolean;
}

export const QueryProvider: React.FC<QueryProviderProps> = ({ 
  children, 
  enableDevtools = process.env.NODE_ENV === 'development' 
}) => {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary
        FallbackComponent={QueryErrorFallback}
        onError={(error, errorInfo) => {
          console.error('Query Error Boundary caught an error:', error, errorInfo);
          // Here you could send to error reporting service
        }}
        onReset={() => {
          // Reset query client on error boundary reset
          queryClient.clear();
        }}
      >
        <Suspense fallback={<QueryLoadingFallback />}>
          {children}
        </Suspense>
      </ErrorBoundary>
      {enableDevtools && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
};