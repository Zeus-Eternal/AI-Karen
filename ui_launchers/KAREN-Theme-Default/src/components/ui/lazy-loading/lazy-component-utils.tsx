"use client";

import React, {
  lazy,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ComponentPropsWithoutRef,
  type ComponentType,
  type LazyExoticComponent,
} from 'react';

import LazyComponent from './lazy-component';
import type { LazyLoadOptions } from './lazy-component.types';

type ComponentProps<T extends ComponentType<unknown>> = ComponentPropsWithoutRef<T> extends object
  ? ComponentPropsWithoutRef<T>
  : Record<string, never>;

export function createLazyComponent<T extends ComponentType<unknown>>(
  importFn: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
): LazyExoticComponent<T> {
  const { delay = 0, fallback, errorFallback } = options;

  return lazy(async () => {
    if (delay > 0) {
      await new Promise<void>((resolve) => {
        setTimeout(resolve, delay);
      });
    }

    const module = await importFn();
    const LoadedComponent = module.default;

    const WrappedComponent = (props: ComponentProps<T>) => (
      <LazyComponent fallback={fallback} errorFallback={errorFallback}>
        <LoadedComponent {...props} />
      </LazyComponent>
    );

    WrappedComponent.displayName = `LazyComponent(${LoadedComponent.displayName ?? LoadedComponent.name ?? 'Component'})`;

    return {
      default: WrappedComponent as unknown as T,
    };
  });
}

export function useLazyPreload<T extends ComponentType<unknown>>(
  importFn: () => Promise<{ default: T }>,
  options: { preloadOnMount?: boolean } = {}
): {
  preload: () => void;
  isPreloaded: boolean;
} {
  const { preloadOnMount = false } = options;
  const importFnRef = useRef(importFn);
  const [isPreloaded, setIsPreloaded] = useState(false);

  useEffect(() => {
    importFnRef.current = importFn;
  }, [importFn]);

  const preload = useCallback(() => {
    if (isPreloaded) {
      return;
    }

    void importFnRef.current()
      .then(() => {
        setIsPreloaded(true);
      })
      .catch(() => {
        // ignore preload errors; they'll surface during actual render
      });
  }, [isPreloaded]);

  useEffect(() => {
    if (preloadOnMount) {
      preload();
    }
  }, [preload, preloadOnMount]);

  return { preload, isPreloaded };
}

export default createLazyComponent;
