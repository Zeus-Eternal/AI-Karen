"use client";

import React, { Suspense, ComponentType, LazyExoticComponent } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
export interface LazyComponentProps {
  fallback?: React.ComponentType;
  errorFallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  children: React.ReactNode;
}
export interface LazyLoadOptions {
  fallback?: React.ComponentType;
  errorFallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  delay?: number;
}
// Default loading fallback component
const DefaultLoadingFallback: React.FC = () => (
  <motion.div
    className="flex items-center justify-center p-8 sm:p-4 md:p-6"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.2 }}
  >
    <div className="flex items-center space-x-2 text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin " />
      <span className="text-sm md:text-base lg:text-lg">Loading...</span>
    </div>
  </motion.div>
);
// Default error fallback component
const DefaultErrorFallback: React.FC<{ error: Error; retry: () => void }> = ({ error, retry }) => (
  <motion.div
    className="flex flex-col items-center justify-center p-8 text-center sm:p-4 md:p-6"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
  >
    <div className="text-destructive mb-4">
      <svg
        className="h-12 w-12 mx-auto mb-2 "
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
        />
      </svg>
      <h3 className="text-lg font-semibold">Failed to load component</h3>
      <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
        {error.message || 'An unexpected error occurred'}
      </p>
    </div>
    <Button
      onClick={retry}
      className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
     aria-label="Button">
    </Button>
  </motion.div>
);
// Enhanced lazy component wrapper with error boundary
export class LazyComponentErrorBoundary extends React.Component<
  LazyComponentProps & { onRetry?: () => void },
  { hasError: boolean; error: Error | null; retryCount: number }
> {
  private maxRetries = 3;
  constructor(props: LazyComponentProps & { onRetry?: () => void }) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      retryCount: 0,
    };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
  }
  handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        retryCount: prevState.retryCount + 1,
      }));
      this.props.onRetry?.();
    }
  };
  render() {
    if (this.state.hasError && this.state.error) {
      const ErrorComponent = this.props.errorFallback || DefaultErrorFallback;
      return <ErrorComponent error={this.state.error} retry={this.handleRetry} />;
    }
    return this.props.children;
  }
}
// Main lazy component wrapper
export const LazyComponent: React.FC<LazyComponentProps> = ({
  fallback: FallbackComponent = DefaultLoadingFallback,
  errorFallback,
  children,
}) => {
  return (
    <LazyComponentErrorBoundary errorFallback={errorFallback}>
      <Suspense fallback={<FallbackComponent />}>
        {children}
      </Suspense>
    </LazyComponentErrorBoundary>
  );
};
// Utility function to create lazy components with options
export function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>, options: LazyLoadOptions = {} from "@/lib/placeholder";
): LazyExoticComponent<T> {
  const LazyComp = React.lazy(() => {
    // Add artificial delay if specified (useful for testing)
    if (options.delay) {
      return new Promise<{ default: T }>(resolve => {
        setTimeout(() => {
          importFn().then(resolve);
        }, options.delay);

    }
    return importFn();

  // Return a wrapped component that includes error boundary and fallback
  return React.lazy(() =>
    Promise.resolve({
      default: ((props: any) => (
        <LazyComponent
          fallback={options.fallback}
          errorFallback={options.errorFallback}
        >
          <LazyComp {...props} />
        </LazyComponent>
      )) as unknown as T,
    })
  );
}
// Hook for preloading lazy components
export function useLazyPreload() {
  const preloadComponent = React.useCallback(
    (importFn: () => Promise<{ default: ComponentType<any> }>) => {
      // Preload the component by calling the import function
      importFn().catch(error => { }); from "@/components/ui/placeholder";
    },
    []
  );
  return { preloadComponent };
}
export default LazyComponent;
