"use client";

import React, { Suspense, type ComponentType } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, Loader2 } from "lucide-react";
import { ErrorBoundary } from "react-error-boundary";

import { Button } from "@/components/ui/button";

type FallbackComponent = React.ComponentType<Record<string, unknown>>;
type RouteErrorFallback = React.ComponentType<{ error: Error; resetErrorBoundary: () => void }>;
type PropsOf<T> = T extends ComponentType<infer P> ? P : never;

export interface RouteLazyLoaderProps {
  children: React.ReactNode;
  fallback?: FallbackComponent;
  errorFallback?: RouteErrorFallback;
}

const DefaultRouteFallback: React.FC = () => (
  <motion.div
    className="flex min-h-screen items-center justify-center bg-background"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.3 }}
  >
    <div className="text-center">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        className="mb-4 inline-block"
      >
        <Loader2 className="h-8 w-8 text-primary" />
      </motion.div>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <h2 className="text-lg font-semibold text-foreground">Loading page…</h2>
        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
          Please wait while we prepare your content.
        </p>
      </motion.div>
    </div>
  </motion.div>
);

const DefaultRouteErrorFallback: React.FC<{ error: Error; resetErrorBoundary: () => void }> = ({
  error,
  resetErrorBoundary,
}) => (
  <motion.div
    className="flex min-h-screen items-center justify-center bg-background p-4 sm:p-6"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4 }}
  >
    <div className="max-w-md text-center">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
        className="mb-6"
      >
        <AlertTriangle className="mx-auto h-16 w-16 text-destructive" />
      </motion.div>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <h1 className="text-2xl font-bold text-foreground">Something went wrong</h1>
        <p className="mt-2 text-muted-foreground">
          We encountered an error while loading this page. This might be a temporary issue.
        </p>
        <details className="mt-4 text-left">
          <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
            Technical details
          </summary>
          <pre className="mt-2 max-h-40 overflow-auto rounded bg-muted p-3 text-xs">
            {error.message}
          </pre>
        </details>
        <div className="mt-6 space-y-3">
          <Button type="button" className="w-full" onClick={resetErrorBoundary}>
            Try again
          </Button>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={() => {
              if (typeof window !== "undefined") {
                window.location.assign("/");
              }
            }}
          >
            Go to dashboard
          </Button>
        </div>
      </motion.div>
    </div>
  </motion.div>
);

export const RouteLazyLoader: React.FC<RouteLazyLoaderProps> = ({
  children,
  fallback: FallbackComponent = DefaultRouteFallback,
  errorFallback: ErrorFallbackComponent = DefaultRouteErrorFallback,
}) => (
  <ErrorBoundary
    FallbackComponent={ErrorFallbackComponent}
    onError={(error) => {
      if (process.env.NODE_ENV !== "production") {
        // eslint-disable-next-line no-console
        console.error("RouteLazyLoader error", error);
      }
    }}
  >
    <Suspense fallback={<FallbackComponent />}>{children}</Suspense>
  </ErrorBoundary>
);

export function createLazyRoute<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: {
    fallback?: FallbackComponent;
    errorFallback?: RouteErrorFallback;
    preload?: boolean;
  } = {}
): ComponentType<PropsOf<T>> {
  const load = async () => importFn();

  if (options.preload) {
    void importFn().catch(() => undefined);
  }

  const LazyComponent = React.lazy(load);

  const Wrapped: React.FC<PropsOf<T>> = (props) => (
    <RouteLazyLoader fallback={options.fallback} errorFallback={options.errorFallback}>
      <LazyComponent {...props} />
    </RouteLazyLoader>
  );

  Wrapped.displayName = "LazyRouteWrapper";
  return Wrapped;
}

export function useRoutePreloader() {
  const preloadRoute = React.useCallback(
    (importFn: () => Promise<{ default: ComponentType<any> }>) => {
      void importFn().catch(() => undefined);
    },
    []
  );
  return { preloadRoute };
}

export function withLazyLoading<P extends object>(
  Component: ComponentType<P>,
  options: {
    fallback?: FallbackComponent;
    errorFallback?: RouteErrorFallback;
  } = {}
) {
  const WrappedComponent = (props: P) => (
    <RouteLazyLoader fallback={options.fallback} errorFallback={options.errorFallback}>
      <Component {...props} />
    </RouteLazyLoader>
  );

  WrappedComponent.displayName = `withLazyLoading(${Component.displayName ?? Component.name ?? "Component"})`;
  return WrappedComponent;
}

export default RouteLazyLoader;
