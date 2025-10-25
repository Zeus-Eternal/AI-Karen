'use client';

/**
 * Performance monitoring utilities for Web Vitals and custom metrics
 */

import React from 'react';

// Web Vitals types
export interface WebVitalsMetric {
  name: 'CLS' | 'FID' | 'FCP' | 'LCP' | 'TTFB' | 'INP';
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
  navigationType: 'navigate' | 'reload' | 'back-forward' | 'back-forward-cache';
}

// Custom performance metrics
export interface CustomMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

// Performance budget thresholds
export const PERFORMANCE_THRESHOLDS = {
  // Core Web Vitals thresholds
  CLS: { good: 0.1, poor: 0.25 },
  FID: { good: 100, poor: 300 },
  FCP: { good: 1800, poor: 3000 },
  LCP: { good: 2500, poor: 4000 },
  TTFB: { good: 800, poor: 1800 },
  INP: { good: 200, poor: 500 },
  
  // Custom thresholds
  ANIMATION_FRAME_TIME: { good: 16, poor: 32 }, // 60fps = 16ms per frame
  BUNDLE_LOAD_TIME: { good: 1000, poor: 3000 },
  ROUTE_CHANGE_TIME: { good: 200, poor: 500 },
  COMPONENT_RENDER_TIME: { good: 10, poor: 50 },
} as const;

export class PerformanceMonitor {
  private metrics: Map<string, CustomMetric[]> = new Map();
  private observers: Map<string, PerformanceObserver> = new Map();
  private isMonitoring = false;
  private reportCallback?: (metric: WebVitalsMetric | CustomMetric) => void;

  constructor(reportCallback?: (metric: WebVitalsMetric | CustomMetric) => void) {
    this.reportCallback = reportCallback;
  }

  /**
   * Start monitoring performance metrics
   */
  startMonitoring(): void {
    if (this.isMonitoring || typeof window === 'undefined') return;

    this.isMonitoring = true;
    
    // Monitor Web Vitals
    this.monitorWebVitals();
    
    // Monitor custom metrics
    this.monitorCustomMetrics();
    
    // Monitor resource loading
    this.monitorResourceLoading();
    
    // Monitor navigation
    this.monitorNavigation();
  }

  /**
   * Stop monitoring performance metrics
   */
  stopMonitoring(): void {
    if (!this.isMonitoring) return;

    this.isMonitoring = false;
    
    // Disconnect all observers
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
  }

  /**
   * Record a custom performance metric
   */
  recordMetric(name: string, value: number, metadata?: Record<string, any>): void {
    const metric: CustomMetric = {
      name,
      value,
      timestamp: performance.now(),
      metadata,
    };

    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    
    this.metrics.get(name)!.push(metric);
    this.reportCallback?.(metric);
  }

  /**
   * Measure function execution time
   */
  measureFunction<T>(name: string, fn: () => T): T {
    const start = performance.now();
    const result = fn();
    const duration = performance.now() - start;
    
    this.recordMetric(name, duration, { type: 'function-execution' });
    
    return result;
  }

  /**
   * Measure async function execution time
   */
  async measureAsyncFunction<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    const result = await fn();
    const duration = performance.now() - start;
    
    this.recordMetric(name, duration, { type: 'async-function-execution' });
    
    return result;
  }

  /**
   * Start measuring a custom metric
   */
  startMeasure(name: string): void {
    performance.mark(`${name}-start`);
  }

  /**
   * End measuring a custom metric
   */
  endMeasure(name: string, metadata?: Record<string, any>): void {
    const endMark = `${name}-end`;
    const measureName = `${name}-measure`;
    
    performance.mark(endMark);
    performance.measure(measureName, `${name}-start`, endMark);
    
    const measure = performance.getEntriesByName(measureName)[0];
    if (measure) {
      this.recordMetric(name, measure.duration, metadata);
    }
    
    // Clean up marks and measures
    performance.clearMarks(`${name}-start`);
    performance.clearMarks(endMark);
    performance.clearMeasures(measureName);
  }

  /**
   * Get all recorded metrics
   */
  getMetrics(): Map<string, CustomMetric[]> {
    return new Map(this.metrics);
  }

  /**
   * Get metrics for a specific name
   */
  getMetricsByName(name: string): CustomMetric[] {
    return this.metrics.get(name) || [];
  }

  /**
   * Get performance summary
   */
  getPerformanceSummary(): PerformanceSummary {
    const summary: PerformanceSummary = {
      webVitals: {},
      customMetrics: {},
      resourceTiming: this.getResourceTimingSummary(),
      navigationTiming: this.getNavigationTimingSummary(),
    };

    // Summarize custom metrics
    this.metrics.forEach((metrics, name) => {
      if (metrics.length > 0) {
        const values = metrics.map(m => m.value);
        summary.customMetrics[name] = {
          count: metrics.length,
          min: Math.min(...values),
          max: Math.max(...values),
          avg: values.reduce((sum, val) => sum + val, 0) / values.length,
          p95: this.calculatePercentile(values, 95),
          latest: metrics[metrics.length - 1],
        };
      }
    });

    return summary;
  }

  private monitorWebVitals(): void {
    // Use web-vitals library if available, otherwise implement basic monitoring
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      // Monitor LCP
      this.observePerformanceEntry('largest-contentful-paint', (entries) => {
        const lastEntry = entries[entries.length - 1];
        this.reportWebVital('LCP', lastEntry.startTime);
      });

      // Monitor FID
      this.observePerformanceEntry('first-input', (entries) => {
        const firstEntry = entries[0] as any;
        const fid = firstEntry.processingStart - firstEntry.startTime;
        this.reportWebVital('FID', fid);
      });

      // Monitor CLS
      let clsValue = 0;
      this.observePerformanceEntry('layout-shift', (entries) => {
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        });
        this.reportWebVital('CLS', clsValue);
      });

      // Monitor FCP
      this.observePerformanceEntry('paint', (entries) => {
        const fcpEntry = entries.find((entry: any) => entry.name === 'first-contentful-paint');
        if (fcpEntry) {
          this.reportWebVital('FCP', fcpEntry.startTime);
        }
      });
    }
  }

  private monitorCustomMetrics(): void {
    // Monitor animation frame timing
    let frameCount = 0;
    let lastFrameTime = performance.now();
    
    const measureFrameTime = () => {
      const currentTime = performance.now();
      const frameTime = currentTime - lastFrameTime;
      
      if (frameCount > 0) { // Skip first frame
        this.recordMetric('animation-frame-time', frameTime, { 
          type: 'animation-performance',
          frameCount 
        });
      }
      
      lastFrameTime = currentTime;
      frameCount++;
      
      if (this.isMonitoring) {
        requestAnimationFrame(measureFrameTime);
      }
    };
    
    requestAnimationFrame(measureFrameTime);
  }

  private monitorResourceLoading(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    this.observePerformanceEntry('resource', (entries) => {
      entries.forEach((entry: any) => {
        const resourceType = entry.initiatorType;
        const loadTime = entry.responseEnd - entry.startTime;
        
        this.recordMetric(`resource-load-${resourceType}`, loadTime, {
          type: 'resource-loading',
          url: entry.name,
          size: entry.transferSize,
          cached: entry.transferSize === 0,
        });
      });
    });
  }

  private monitorNavigation(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    this.observePerformanceEntry('navigation', (entries) => {
      const entry = entries[0] as any;
      if (entry) {
        this.recordMetric('navigation-total', entry.loadEventEnd - entry.startTime, {
          type: 'navigation',
          navigationType: entry.type,
        });
        
        this.recordMetric('navigation-dns', entry.domainLookupEnd - entry.domainLookupStart, {
          type: 'navigation-timing',
        });
        
        this.recordMetric('navigation-connect', entry.connectEnd - entry.connectStart, {
          type: 'navigation-timing',
        });
        
        this.recordMetric('navigation-ttfb', entry.responseStart - entry.requestStart, {
          type: 'navigation-timing',
        });
      }
    });
  }

  private observePerformanceEntry(
    entryType: string, 
    callback: (entries: PerformanceEntry[]) => void
  ): void {
    try {
      const observer = new PerformanceObserver((list) => {
        callback(list.getEntries());
      });
      
      observer.observe({ entryTypes: [entryType] });
      this.observers.set(entryType, observer);
    } catch (error) {
      console.warn(`Failed to observe ${entryType}:`, error);
    }
  }

  private reportWebVital(name: WebVitalsMetric['name'], value: number): void {
    const threshold = PERFORMANCE_THRESHOLDS[name];
    let rating: WebVitalsMetric['rating'] = 'good';
    
    if (value > threshold.poor) {
      rating = 'poor';
    } else if (value > threshold.good) {
      rating = 'needs-improvement';
    }

    const metric: WebVitalsMetric = {
      name,
      value,
      rating,
      delta: value,
      id: `${name}-${Date.now()}`,
      navigationType: 'navigate', // Simplified
    };

    this.reportCallback?.(metric);
  }

  private getResourceTimingSummary(): ResourceTimingSummary {
    const entries = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
    
    const summary: ResourceTimingSummary = {
      totalResources: entries.length,
      totalSize: 0,
      totalLoadTime: 0,
      byType: {},
    };

    entries.forEach(entry => {
      const type = entry.initiatorType || 'other';
      const loadTime = entry.responseEnd - entry.startTime;
      const size = entry.transferSize || 0;

      summary.totalSize += size;
      summary.totalLoadTime += loadTime;

      if (!summary.byType[type]) {
        summary.byType[type] = {
          count: 0,
          totalSize: 0,
          totalLoadTime: 0,
          avgLoadTime: 0,
        };
      }

      summary.byType[type].count++;
      summary.byType[type].totalSize += size;
      summary.byType[type].totalLoadTime += loadTime;
      summary.byType[type].avgLoadTime = summary.byType[type].totalLoadTime / summary.byType[type].count;
    });

    return summary;
  }

  private getNavigationTimingSummary(): NavigationTimingSummary {
    const entry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    
    if (!entry) {
      return {
        totalTime: 0,
        dnsTime: 0,
        connectTime: 0,
        ttfb: 0,
        domContentLoaded: 0,
        loadComplete: 0,
      };
    }

    return {
      totalTime: entry.loadEventEnd - entry.startTime,
      dnsTime: entry.domainLookupEnd - entry.domainLookupStart,
      connectTime: entry.connectEnd - entry.connectStart,
      ttfb: entry.responseStart - entry.requestStart,
      domContentLoaded: entry.domContentLoadedEventEnd - entry.startTime,
      loadComplete: entry.loadEventEnd - entry.startTime,
    };
  }

  private calculatePercentile(values: number[], percentile: number): number {
    const sorted = [...values].sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[index] || 0;
  }
}

// Types
export interface PerformanceSummary {
  webVitals: Record<string, any>;
  customMetrics: Record<string, MetricSummary>;
  resourceTiming: ResourceTimingSummary;
  navigationTiming: NavigationTimingSummary;
}

export interface MetricSummary {
  count: number;
  min: number;
  max: number;
  avg: number;
  p95: number;
  latest: CustomMetric;
}

export interface ResourceTimingSummary {
  totalResources: number;
  totalSize: number;
  totalLoadTime: number;
  byType: Record<string, {
    count: number;
    totalSize: number;
    totalLoadTime: number;
    avgLoadTime: number;
  }>;
}

export interface NavigationTimingSummary {
  totalTime: number;
  dnsTime: number;
  connectTime: number;
  ttfb: number;
  domContentLoaded: number;
  loadComplete: number;
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor();

// React hook for performance monitoring
export function usePerformanceMonitor() {
  const [isMonitoring, setIsMonitoring] = React.useState(false);
  const [metrics, setMetrics] = React.useState<Map<string, CustomMetric[]>>(new Map());

  React.useEffect(() => {
    const monitor = new PerformanceMonitor((metric) => {
      // Update metrics when new ones are recorded
      setMetrics(prev => new Map(prev));
    });

    monitor.startMonitoring();
    setIsMonitoring(true);

    return () => {
      monitor.stopMonitoring();
      setIsMonitoring(false);
    };
  }, []);

  const recordMetric = React.useCallback((name: string, value: number, metadata?: Record<string, any>) => {
    performanceMonitor.recordMetric(name, value, metadata);
    setMetrics(performanceMonitor.getMetrics());
  }, []);

  const measureFunction = React.useCallback(<T>(name: string, fn: () => T): T => {
    return performanceMonitor.measureFunction(name, fn);
  }, []);

  const measureAsyncFunction = React.useCallback(async <T>(name: string, fn: () => Promise<T>): Promise<T> => {
    return performanceMonitor.measureAsyncFunction(name, fn);
  }, []);

  return {
    isMonitoring,
    metrics,
    recordMetric,
    measureFunction,
    measureAsyncFunction,
    getPerformanceSummary: () => performanceMonitor.getPerformanceSummary(),
  };
}

// Performance budget checker
export function checkPerformanceBudget(metric: WebVitalsMetric | CustomMetric): {
  withinBudget: boolean;
  rating: 'good' | 'needs-improvement' | 'poor';
  threshold: { good: number; poor: number } | null;
} {
  const threshold = PERFORMANCE_THRESHOLDS[metric.name as keyof typeof PERFORMANCE_THRESHOLDS];
  
  if (!threshold) {
    return {
      withinBudget: true,
      rating: 'good',
      threshold: null,
    };
  }

  let rating: 'good' | 'needs-improvement' | 'poor' = 'good';
  
  if (metric.value > threshold.poor) {
    rating = 'poor';
  } else if (metric.value > threshold.good) {
    rating = 'needs-improvement';
  }

  return {
    withinBudget: rating === 'good',
    rating,
    threshold,
  };
}