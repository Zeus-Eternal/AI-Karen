"use client";

import React, { createContext, useCallback, useContext, useEffect } from 'react';

import type { PerformanceMonitor } from '@/utils/performance-monitor';

export interface PerformanceMetric {
  name: string;
  value: number;
  type: string;
  metadata?: Record<string, unknown>;
}

export interface PerformanceContextValue {
  recordMetric: (metric: PerformanceMetric) => void;
  measureFunction: <T>(name: string, fn: () => T) => T;
  measureAsyncFunction: <T>(name: string, fn: () => Promise<T>) => Promise<T>;
  startMeasure: (name: string) => void;
  endMeasure: (name: string, metadata?: Record<string, unknown>) => void;
  monitor: PerformanceMonitor;
}

export const PerformanceContext = createContext<PerformanceContextValue | null>(null);

export const usePerformanceContext = (): PerformanceContextValue => {
  const context = useContext(PerformanceContext);
  if (context === null) {
    throw new Error('usePerformanceContext must be used within a PerformanceProvider');
  }
  return context;
};

export function withPerformanceMeasurement<P>(
  Component: React.ComponentType<P>,
  measurementName?: string
): React.FC<P> {
  const WrappedComponent: React.FC<P> = (props) => {
    const { measureFunction } = usePerformanceContext();
    const componentName =
      measurementName || Component.displayName || Component.name || 'Component';

    return measureFunction(`${componentName}-render`, () =>
      React.createElement(Component, props)
    );
  };

  WrappedComponent.displayName = `withPerformanceMeasurement(${Component.displayName || Component.name || 'Component'})`;

  return WrappedComponent;
}

export function useComponentPerformance(componentName: string) {
  const { recordMetric, startMeasure, endMeasure } = usePerformanceContext();

  useEffect(() => {
    const mountStart = performance.now();
    return () => {
      const mountEnd = performance.now();
      recordMetric({
        name: `${componentName}-lifecycle`,
        value: mountEnd - mountStart,
        type: 'component-lifecycle',
        metadata: { componentName, phase: 'mount-unmount' }
      });
    };
  }, [componentName, recordMetric]);

  const measureRender = useCallback(<T,>(fn: () => T): T => {
    const start = performance.now();
    const result = fn();
    const end = performance.now();
    recordMetric({
      name: `${componentName}-render`,
      value: end - start,
      type: 'component-lifecycle',
      metadata: { componentName }
    });
    return result;
  }, [componentName, recordMetric]);

  const measureAsync = useCallback(<T,>(name: string, fn: () => Promise<T>): Promise<T> => {
    const start = performance.now();
    return fn().then((result) => {
      const end = performance.now();
      recordMetric({
        name: `${componentName}-${name}`,
        value: end - start,
        type: 'component-async',
        metadata: { componentName, operation: name }
      });
      return result;
    });
  }, [componentName, recordMetric]);

  return {
    measureRender,
    measureAsync,
    startMeasure: (name: string) => startMeasure(`${componentName}-${name}`),
    endMeasure: (name: string, metadata?: Record<string, unknown>) =>
      endMeasure(`${componentName}-${name}`, metadata),
  };
}

export function useInteractionPerformance() {
  const { recordMetric } = usePerformanceContext();

  const measureClick = useCallback(
    (elementName: string, handler: () => void) => {
      return () => {
        const start = performance.now();
        handler();
        const end = performance.now();
        recordMetric({
          name: `click-${elementName}`,
          value: end - start,
          type: 'user-interaction',
          metadata: { elementName, interaction: 'click' }
        });
      };
    },
    [recordMetric]
  );

  const measureAsyncClick = useCallback(
    (elementName: string, handler: () => Promise<void>) => {
      return async () => {
        const start = performance.now();
        await handler();
        const end = performance.now();
        recordMetric({
          name: `async-click-${elementName}`,
          value: end - start,
          type: 'user-interaction',
          metadata: { elementName, interaction: 'async-click' }
        });
      };
    },
    [recordMetric]
  );

  const measureFormSubmit = useCallback(
    (formName: string, handler: () => void | Promise<void>) => {
      return async () => {
        const start = performance.now();
        await handler();
        const end = performance.now();
        recordMetric({
          name: `form-submit-${formName}`,
          value: end - start,
          type: 'user-interaction',
          metadata: { formName, interaction: 'form-submit' }
        });
      };
    },
    [recordMetric]
  );

  return {
    measureClick,
    measureAsyncClick,
    measureFormSubmit,
  };
}
