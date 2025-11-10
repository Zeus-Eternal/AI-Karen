"use client";

import React, { createContext, useContext, useCallback, useEffect } from 'react';
import { performanceMonitor } from '@/utils/performance-monitor';

// Context for performance monitoring
export interface PerformanceContextValue {
  recordMetric: (metric: {
    name: string;
    value: number;
    type: string;
    metadata?: Record<string, unknown>;
  }) => void;
  measureFunction: (name: string, fn: () => any) => any;
  measureAsyncFunction: (name: string, fn: () => Promise<any>) => Promise<any>;
  startMeasure: (name: string) => void;
  endMeasure: (name: string, metadata?: Record<string, unknown>) => void;
  monitor: typeof performanceMonitor;
}

const PerformanceContext = createContext<PerformanceContextValue | null>(null);

// PerformanceProvider props
export interface PerformanceProviderProps {
  children: React.ReactNode;
  enableReporting?: boolean;
}

export function PerformanceProvider({
  children,
  enableReporting = true,
}: PerformanceProviderProps) {
  const recordMetric = useCallback((metric: {
    name: string;
    value: number;
    type: string;
    metadata?: Record<string, unknown>;
  }) => {
    performanceMonitor.recordMetric(metric.name, metric.value, metric.metadata);
    if (enableReporting) {
      // Report to analytics if enabled
      reportToAnalytics(metric);
    }
  }, [enableReporting]);

  const measureFunction = useCallback((name: string, fn: () => any): any => {
    return performanceMonitor.measureFunction(name, fn);
  }, []);

  const measureAsyncFunction = useCallback(async (name: string, fn: () => Promise<any>): Promise<any> => {
    return performanceMonitor.measureAsyncFunction(name, fn);
  }, []);

  const startMeasure = useCallback((name: string) => {
    performanceMonitor.startMeasure(name);
  }, []);

  const endMeasure = useCallback((name: string, metadata?: Record<string, unknown>) => {
    performanceMonitor.endMeasure(name, metadata);
  }, []);

  const value: PerformanceContextValue = {
    recordMetric,
    measureFunction,
    measureAsyncFunction,
    startMeasure,
    endMeasure,
    monitor: performanceMonitor,
  };

  return (
    <PerformanceContext.Provider value={value}>
      {children}
    </PerformanceContext.Provider>
  );
}

export const usePerformanceContext = (): PerformanceContextValue => {
  const context = useContext(PerformanceContext);
  if (!context) {
    throw new Error('usePerformanceContext must be used within a PerformanceProvider');
  }
  return context;
};

// Higher-order component for measuring component render time
export function withPerformanceMeasurement(
  Component: React.ComponentType<any>,
  measurementName?: string
) {
  const WrappedComponent = React.forwardRef<any, any>((props, ref) => {
    const { measureFunction } = usePerformanceContext();
    const componentName = measurementName || Component.displayName || Component.name || 'Component';
    return measureFunction(`${componentName}-render`, () =>
      React.createElement(Component, { ...props, ref })
    );
  });

  WrappedComponent.displayName = `withPerformanceMeasurement(${Component.displayName || Component.name})`;
  return WrappedComponent;
}

// Hook for measuring component lifecycle
export function useComponentPerformance(componentName: string) {
  const { recordMetric, startMeasure, endMeasure } = usePerformanceContext();

  // Measure component mount/unmount time
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

  const measureRender = useCallback((fn: () => any): any => {
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

  const measureAsync = useCallback(async (name: string, fn: () => Promise<any>): Promise<any> => {
    const start = performance.now();
    const result = await fn();
    const end = performance.now();
    recordMetric({
      name: `${componentName}-${name}`,
      value: end - start,
      type: 'component-async',
      metadata: { componentName, operation: name }
    });
    return result;
  }, [componentName, recordMetric]);

  return {
    measureRender,
    measureAsync,
    startMeasure: (name: string) => startMeasure(`${componentName}-${name}`),
    endMeasure: (name: string, metadata?: Record<string, unknown>) =>
      endMeasure(`${componentName}-${name}`, metadata),
  };
}

// Hook for measuring user interactions
export function useInteractionPerformance() {
  const { recordMetric } = usePerformanceContext();

  const measureClick = useCallback((elementName: string, handler: () => void) => {
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
  }, [recordMetric]);

  const measureAsyncClick = useCallback((elementName: string, handler: () => Promise<void>) => {
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
  }, [recordMetric]);

  const measureFormSubmit = useCallback((formName: string, handler: () => void | Promise<void>) => {
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
  }, [recordMetric]);

  return {
    measureClick,
    measureAsyncClick,
    measureFormSubmit,
  };
}

// Helper function to report metrics to analytics
async function reportToAnalytics(metric: {
  name: string;
  value: number;
  type: string;
  metadata?: Record<string, unknown>;
}): Promise<void> {
  try {
    // This would integrate with your analytics service
    // For now, we'll just log to console in development
    console.log('Reporting metric:', metric);
  } catch (error) {
    console.error('Failed to report metric:', error);
  }
}

export default PerformanceProvider;
