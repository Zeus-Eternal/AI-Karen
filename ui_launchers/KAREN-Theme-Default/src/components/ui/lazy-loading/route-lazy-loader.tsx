"use client";

import React, { Suspense, ComponentType } from 'react';
import { motion } from 'framer-motion';
import { Loader2, AlertTriangle } from 'lucide-react';
import { ErrorBoundary } from 'react-error-boundary';
export interface RouteLazyLoaderProps {
  children: React.ReactNode;
  fallback?: React.ComponentType;
  errorFallback?: React.ComponentType<{ error: Error; resetErrorBoundary: () => void }>;
}
// Enhanced loading fallback for routes
const DefaultRouteFallback: React.FC = () => (
  <motion.div
    className="min-h-screen flex items-center justify-center bg-background"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.3 }}
  >
    <div className="text-center">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        className="inline-block mb-4"
      >
        <Loader2 className="h-8 w-8 text-primary " />
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h2 className="text-lg font-semibold text-foreground mb-2">Loading page...</h2>
        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Please wait while we prepare your content</p>
      </motion.div>
    </div>
  </motion.div>
);
// Enhanced error fallback for routes
const DefaultRouteErrorFallback: React.FC<{ error: Error; resetErrorBoundary: () => void }> = ({
  error,
  resetErrorBoundary,
}) => (
  <motion.div
    className="min-h-screen flex items-center justify-center bg-background p-4 sm:p-4 md:p-6"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4 }}
  >
    <div className="text-center max-w-md">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
        className="mb-6"
      >
        <AlertTriangle className="h-16 w-16 text-destructive mx-auto " />
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h1 className="text-2xl font-bold text-foreground mb-2">
          Oops! Something went wrong
        </h1>
        <p className="text-muted-foreground mb-6">
          We encountered an error while loading this page. This might be a temporary issue.
        </p>
        <details className="mb-6 text-left">
          <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground transition-colors md:text-base lg:text-lg">
          </summary>
          <pre className="mt-2 p-3 bg-muted rounded-md text-xs overflow-auto max-h-32 sm:text-sm md:text-base">
            {error.message}
            {error.stack && `\n\n${error.stack}`}
          </pre>
        </details>
        <div className="space-y-3">
          <Button
            onClick={resetErrorBoundary}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
           aria-label="Button">
          </Button>
          <Button
            onClick={() => window.location.href = '/'}
            className="w-full px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90 transition-colors"
          >
          </Button>
        </div>
      </motion.div>
    </div>
  </motion.div>
);
// Main route lazy loader component
export const RouteLazyLoader: React.FC<RouteLazyLoaderProps> = ({
  children,
  fallback: FallbackComponent = DefaultRouteFallback,
  errorFallback: ErrorFallbackComponent = DefaultRouteErrorFallback,
}) => {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallbackComponent}
      onError={(error, errorInfo) => {
        // Here you could send error to monitoring service
      }}
    >
      <Suspense fallback={<FallbackComponent />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
};
// Utility function to create lazy route components
export function createLazyRoute<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: {
    fallback?: React.ComponentType;
    errorFallback?: React.ComponentType<{ error: Error; resetErrorBoundary: () => void }>;
    preload?: boolean;
  } = {}
) {
  const LazyRouteComponent = React.lazy(importFn);
  // Preload the component if requested
  if (options.preload) {
    importFn().catch(error => { });
  }
  return ((props: any) => (
    <RouteLazyLoader
      fallback={options.fallback}
      errorFallback={options.errorFallback}
    >
      <LazyRouteComponent {...props} />
    </RouteLazyLoader>
  )) as unknown as T;
}
// Hook for route preloading
export function useRoutePreloader() {
  const preloadRoute = React.useCallback(
    (importFn: () => Promise<{ default: ComponentType<any> }>) => {
      importFn().catch(error => { });
    },
    []
  );
  return { preloadRoute };
}
// Higher-order component for wrapping pages with lazy loading
export function withLazyLoading<P extends object>(
  Component: ComponentType<P>,
  options: {
    fallback?: React.ComponentType;
    errorFallback?: React.ComponentType<{ error: Error; resetErrorBoundary: () => void }>;
  } = {}
) {
  const WrappedComponent = (props: P) => (
    <RouteLazyLoader
      fallback={options.fallback}
      errorFallback={options.errorFallback}
    >
      <Component {...props} />
    </RouteLazyLoader>
  );
  WrappedComponent.displayName = `withLazyLoading(${Component.displayName || Component.name})`;
  return WrappedComponent;
}
export default RouteLazyLoader;
