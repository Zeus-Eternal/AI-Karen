"use client";

import React, { useCallback, useMemo } from 'react';
import { performanceMonitor } from '@/utils/performance-monitor';

import {
  PerformanceContext,
  type PerformanceContextValue,
  type PerformanceMetric,
} from './performance-context';

export interface PerformanceProviderProps {
  children: React.ReactNode;
  enableReporting?: boolean;
}

export function PerformanceProvider({
  children,
  enableReporting = true,
}: PerformanceProviderProps) {
  const recordMetric = useCallback((metric: PerformanceMetric) => {
    performanceMonitor.recordMetric(metric.name, metric.value, metric.metadata);
    if (enableReporting) {
      // Report to analytics if enabled
      reportToAnalytics(metric);
    }
  }, [enableReporting]);

  const measureFunction = useCallback(<T,>(name: string, fn: () => T): T => {
    return performanceMonitor.measureFunction(name, fn);
  }, []);

  const measureAsyncFunction = useCallback(<T,>(
    name: string,
    fn: () => Promise<T>
  ): Promise<T> => {
    return performanceMonitor.measureAsyncFunction(name, fn);
  }, []);

  const startMeasure = useCallback((name: string) => {
    performanceMonitor.startMeasure(name);
  }, []);

  const endMeasure = useCallback((name: string, metadata?: Record<string, unknown>) => {
    performanceMonitor.endMeasure(name, metadata);
  }, []);

  const value: PerformanceContextValue = useMemo(() => ({
    recordMetric,
    measureFunction,
    measureAsyncFunction,
    startMeasure,
    endMeasure,
    monitor: performanceMonitor,
  }), [recordMetric, measureFunction, measureAsyncFunction, startMeasure, endMeasure]);

  return (
    <PerformanceContext.Provider value={value}>
      {children}
    </PerformanceContext.Provider>
  );
}

// Helper function to report metrics to analytics
async function reportToAnalytics(metric: PerformanceMetric): Promise<void> {
  try {
    // This would integrate with your analytics service
    // For now, we'll just log to console in development
    console.log('Reporting metric:', metric);
  } catch (error) {
    console.error('Failed to report metric:', error);
  }
}

export default PerformanceProvider;
