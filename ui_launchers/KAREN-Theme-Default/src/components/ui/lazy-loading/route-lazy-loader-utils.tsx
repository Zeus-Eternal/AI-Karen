"use client";

import React, { lazy, useCallback, type ComponentType } from 'react';

import RouteLazyLoader from './route-lazy-loader';
import type { RouteLazyLoaderProps } from './route-lazy-loader.types';

type PropsOf<T extends ComponentType<unknown>> = T extends ComponentType<infer P>
  ? P extends object
    ? P
    : never
  : never;

type RouteLoaderOptions = Pick<RouteLazyLoaderProps, 'fallback' | 'errorFallback'> & {
  preload?: boolean;
};

export function createLazyRoute<T extends ComponentType<unknown>>(
  importFn: () => Promise<{ default: T }>,
  options: RouteLoaderOptions = {}
): ComponentType<PropsOf<T>> {
  const load = async () => importFn();

  if (options.preload) {
    void importFn().catch(() => undefined);
  }

  const LazyComponent = lazy(load);

  const Wrapped: React.FC<PropsOf<T>> = (props) => (
    <RouteLazyLoader fallback={options.fallback} errorFallback={options.errorFallback}>
      <LazyComponent {...props} />
    </RouteLazyLoader>
  );

  const lazyComponentMeta = LazyComponent as {
    displayName?: string;
    name?: string;
  };

  Wrapped.displayName = `LazyRouteWrapper(${lazyComponentMeta.displayName ?? lazyComponentMeta.name ?? 'Component'})`;
  return Wrapped;
}

export function useRoutePreloader() {
  const preloadRoute = useCallback((importFn: () => Promise<{ default: ComponentType<unknown> }>) => {
    void importFn().catch(() => undefined);
  }, []);

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

  WrappedComponent.displayName = `withLazyLoading(${Component.displayName ?? Component.name ?? 'Component'})`;
  return WrappedComponent;
}

export default createLazyRoute;
