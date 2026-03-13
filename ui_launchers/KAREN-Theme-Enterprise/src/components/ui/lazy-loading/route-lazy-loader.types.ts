import type React from "react";

type FallbackComponent = React.ComponentType<Record<string, unknown>>;
type RouteErrorFallback = React.ComponentType<{ error: Error; resetErrorBoundary: () => void }>;

export interface RouteLazyLoaderProps {
  children: React.ReactNode;
  fallback?: FallbackComponent;
  errorFallback?: RouteErrorFallback;
}

export type { FallbackComponent, RouteErrorFallback };
