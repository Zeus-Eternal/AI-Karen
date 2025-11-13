"use client";

import React, { lazy, useCallback, type ComponentType } from "react";

import RouteLazyLoader from "./route-lazy-loader";
import type { RouteLazyLoaderProps } from "./route-lazy-loader.types";

type RouteLoaderOptions = Pick<RouteLazyLoaderProps, "fallback" | "errorFallback"> & {
  preload?: boolean;
};

export function createLazyRoute<P extends object>(
  importFn: () => Promise<{ default: ComponentType<P> }>,
  options: RouteLoaderOptions = {}
): ComponentType<P> {
  const load = async () => importFn();

  if (options.preload) {
    void importFn().catch(() => undefined);
  }

  const LazyComponent = lazy(load);

  const Wrapped = (props: P): React.ReactElement => (
    <RouteLazyLoader fallback={options.fallback} errorFallback={options.errorFallback}>
      <LazyComponent {...props} />
    </RouteLazyLoader>
  );

  const lazyComponentMeta = LazyComponent as {
    displayName?: string;
    name?: string;
  };

  Wrapped.displayName = `LazyRouteWrapper(${
    lazyComponentMeta.displayName ?? lazyComponentMeta.name ?? "Component"
  })`;
  return Wrapped;
}

export function useRoutePreloader() {
  const preloadRoute = useCallback(
    (importFn: () => Promise<{ default: ComponentType<Record<string, unknown>> }>) => {
      void importFn().catch(() => undefined);
    },
    []
  );

  return { preloadRoute };
}

export function withLazyLoading<P extends object>(
  Component: ComponentType<P>,
  options: RouteLoaderOptions = {}
): ComponentType<P> {
  const WrappedComponent = (props: P) => (
    <RouteLazyLoader fallback={options.fallback} errorFallback={options.errorFallback}>
      <Component {...props} />
    </RouteLazyLoader>
  );

  WrappedComponent.displayName = `withLazyLoading(${
    Component.displayName ?? Component.name ?? "Component"
  })`;
  return WrappedComponent;
}

export default createLazyRoute;
