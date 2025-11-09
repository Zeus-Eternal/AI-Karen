'use client';

import { useEffect, useRef } from 'react';

export interface PerformanceMetrics {
  name: string;
  duration: number;
  startTime: number;
  endTime: number;
}

export function usePerformanceMonitor(name: string, enabled = process.env.NODE_ENV === 'development') {
  const startTimeRef = useRef<number>();
  const metricsRef = useRef<PerformanceMetrics[]>([]);

  // Start performance measurement
  const start = () => {
    if (!enabled) return;
    startTimeRef.current = performance.now();
  };

  // End performance measurement and log the result
  const end = (metricName?: string) => {
    if (!enabled || !startTimeRef.current) return;
    const endTime = performance.now();
    const duration = endTime - startTimeRef.current;

    const metrics: PerformanceMetrics = {
      name: metricName || name,
      duration,
      startTime: startTimeRef.current,
      endTime,
    };

    metricsRef.current.push(metrics);

    // Log performance metrics
    console.log(`⚡ Performance: ${metrics.name} took ${duration.toFixed(2)}ms`);

    // Report to analytics if available
    if (typeof window !== 'undefined' && 'gtag' in window) {
      (window as any).gtag('event', 'timing_complete', {
        name: metrics.name,
        value: Math.round(duration),
      });
    }

    startTimeRef.current = undefined;
  };

  // Measure a function's execution time synchronously
  const measure = <T extends any>(fn: () => T, metricName?: string): T => {
    if (!enabled) return fn();
    start();
    const result = fn();
    end(metricName);
    return result;
  };

  // Measure an async function's execution time
  const measureAsync = async <T extends any>(
    fn: () => Promise<T>, 
    metricName?: string
  ): Promise<T> => {
    if (!enabled) return fn();
    start();
    try {
      const result = await fn();
      end(metricName);
      return result;
    } catch (error) {
      end(`${metricName || name}_error`);
      throw error;
    }
  };

  const getMetrics = () => metricsRef.current;
  const clearMetrics = () => {
    metricsRef.current = [];
  };

  // Auto-clear metrics periodically to prevent memory leaks
  useEffect(() => {
    if (!enabled) return;
    const interval = setInterval(() => {
      if (metricsRef.current.length > 100) {
        metricsRef.current = metricsRef.current.slice(-50);
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [enabled]);

  return {
    start,
    end,
    measure,
    measureAsync,
    getMetrics,
    clearMetrics,
  };
}

// Web Vitals monitoring
export function useWebVitals() {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Largest Contentful Paint (LCP)
    const observer = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      const lastEntry = entries[entries.length - 1];
      if ('gtag' in window) {
        (window as any).gtag('event', 'web_vitals', {
          metric_name: 'LCP',
          metric_value: Math.round(lastEntry.startTime),
        });
      }
    });

    try {
      observer.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (e) {
      // LCP not supported
    }

    // First Input Delay (FID)
    const fidObserver = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      entries.forEach((entry) => {
        const firstInputEntry = entry as any; // PerformanceEventTiming
        const fid = firstInputEntry.processingStart - firstInputEntry.startTime;
        if ('gtag' in window) {
          (window as any).gtag('event', 'web_vitals', {
            metric_name: 'FID',
            metric_value: Math.round(fid),
          });
        }
      });
    });

    try {
      fidObserver.observe({ entryTypes: ['first-input'] });
    } catch (e) {
      // FID not supported
    }

    return () => {
      observer.disconnect();
      fidObserver.disconnect();
    };
  }, []);
}
