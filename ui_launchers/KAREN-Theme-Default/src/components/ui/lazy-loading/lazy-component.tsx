"use client";

import React, {
  Suspense,
  type ComponentType,
  type LazyExoticComponent,
} from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
type SimpleComponent = React.ComponentType<Record<string, unknown>>;

export interface LazyComponentProps {
  fallback?: SimpleComponent;
  errorFallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  children: React.ReactNode;
}

export interface LazyLoadOptions {
  fallback?: SimpleComponent;
  errorFallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  delay?: number;
}

const DefaultLoadingFallback: React.FC = () => (
  <motion.div
    className="flex items-center justify-center p-8 sm:p-4 md:p-6"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.2 }}
  >
    <div className="flex items-center space-x-2 text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span className="text-sm md:text-base lg:text-lg">Loading...</span>
    </div>
  </motion.div>
);

const DefaultErrorFallback: React.FC<{ error: Error; retry: () => void }> = ({ error, retry }) => (
  <motion.div
    className="flex flex-col items-center justify-center p-8 text-center sm:p-4 md:p-6"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
  >
    <div className="mb-4 text-destructive">
      <svg
        className="mx-auto mb-2 h-12 w-12"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01M5.062 19h13.876c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.33 16.5c-.77.833.192 2.5 1.732 2.5z"
        />
      </svg>
      <h3 className="text-lg font-semibold">Failed to load component</h3>
      <p className="mt-1 text-sm text-muted-foreground md:text-base lg:text-lg">
        {error.message || "An unexpected error occurred"}
      </p>
    </div>
    <Button
      type="button"
      onClick={retry}
      className="mt-2 bg-primary text-primary-foreground hover:bg-primary/90"
    >
      Try again
    </Button>
  </motion.div>
);

interface LazyComponentErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  retryCount: number;
}

export class LazyComponentErrorBoundary extends React.Component<
  LazyComponentProps & { onRetry?: () => void },
  LazyComponentErrorBoundaryState
> {
  private readonly maxRetries = 3;

  state: LazyComponentErrorBoundaryState = {
    hasError: false,
    error: null,
    retryCount: 0,
  };

  static getDerivedStateFromError(error: Error): LazyComponentErrorBoundaryState {
    return { hasError: true, error, retryCount: 0 };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    if (process.env.NODE_ENV !== "production") {
      // eslint-disable-next-line no-console
      console.error("LazyComponentErrorBoundary caught", error, errorInfo);
    }
  }

  private handleRetry = () => {
    if (this.state.retryCount >= this.maxRetries) {
      return;
    }

    this.setState((prev) => ({
      hasError: false,
      error: null,
      retryCount: prev.retryCount + 1,
    }));
    this.props.onRetry?.();
  };

  override render() {
    if (this.state.hasError && this.state.error) {
      const ErrorFallback = this.props.errorFallback ?? DefaultErrorFallback;
      return <ErrorFallback error={this.state.error} retry={this.handleRetry} />;
    }

    return this.props.children;
  }
}

export const LazyComponent: React.FC<LazyComponentProps> = ({
  fallback: FallbackComponent = DefaultLoadingFallback,
  errorFallback,
  children,
}) => (
  <LazyComponentErrorBoundary errorFallback={errorFallback}>
    <Suspense fallback={<FallbackComponent />}>{children}</Suspense>
  </LazyComponentErrorBoundary>
);

export function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
): LazyExoticComponent<T> {
  let loader: Promise<{ default: T }> | null = null;

  const loadComponent = async () => {
    if (!loader) {
      loader = (async () => {
        if (options.delay && options.delay > 0) {
          await new Promise((resolve) => setTimeout(resolve, options.delay));
        }
        return importFn();
      })();
    }

    return loader;
  };

  const LazyInner = React.lazy(loadComponent);

  const WrappedComponent = ((props: React.ComponentProps<T>) => (
    <LazyComponent fallback={options.fallback} errorFallback={options.errorFallback}>
      <LazyInner {...props} />
    </LazyComponent>
  )) as React.FC<React.ComponentProps<T>> & { preload?: () => Promise<void> };

  WrappedComponent.displayName = `LazyComponent(${LazyInner.displayName ?? LazyInner.name ?? "Component"})`;
  WrappedComponent.preload = () => loadComponent().then(() => undefined);

  return WrappedComponent as unknown as LazyExoticComponent<T>;
}

export function useLazyPreload() {
  const preloadComponent = React.useCallback((importFn: () => Promise<unknown>) => {
    void importFn();
  }, []);

  return { preloadComponent };
}

export default LazyComponent;
