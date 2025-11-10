'use client';
/**
 * Performance monitoring utilities for Web Vitals and custom metrics (production-grade)
 * - SSR-safe guards
 * - Uses PerformanceObserver directly (works without web-vitals lib)
 * - Handles INP (falls back to FID when INP not available)
 * - Handles BFCache (back-forward cache) & visibility changes
 * - Clean observer lifecycle + singleton + React hook that doesn't re-register
 */

import * as React from 'react';

// ===== Types =====
export interface WebVitalsMetric {
  name: 'CLS' | 'FID' | 'FCP' | 'LCP' | 'TTFB' | 'INP';
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
  navigationType: 'navigate' | 'reload' | 'back-forward' | 'back-forward-cache';
}

export interface CustomMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export type WebVitalsSummary = Partial<Record<WebVitalsMetric['name'], WebVitalsMetric>>;

export interface PerformanceSummary {
  webVitals: WebVitalsSummary;
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
  byType: Record<
    string,
    {
      count: number;
      totalSize: number;
      totalLoadTime: number;
      avgLoadTime: number;
    }
  >;
}

export interface NavigationTimingSummary {
  totalTime: number;
  dnsTime: number;
  connectTime: number;
  ttfb: number;
  domContentLoaded: number;
  loadComplete: number;
}

// ===== Thresholds (budgets) =====
export const PERFORMANCE_THRESHOLDS = {
  CLS: { good: 0.1, poor: 0.25 },
  FID: { good: 100, poor: 300 },
  FCP: { good: 1800, poor: 3000 },
  LCP: { good: 2500, poor: 4000 },
  TTFB: { good: 800, poor: 1800 },
  INP: { good: 200, poor: 500 },

  // Custom
  ANIMATION_FRAME_TIME: { good: 16, poor: 32 }, // 60fps -> ~16ms
  BUNDLE_LOAD_TIME: { good: 1000, poor: 3000 },
  ROUTE_CHANGE_TIME: { good: 200, poor: 500 },
  COMPONENT_RENDER_TIME: { good: 10, poor: 50 },
} as const;

// ===== Helpers =====
const isBrowser = typeof window !== 'undefined';
const hasPO = isBrowser && 'PerformanceObserver' in window;

function navType(): WebVitalsMetric['navigationType'] {
  if (!isBrowser) return 'navigate';
  const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
  if (!nav) return 'navigate';
  // Some browsers report 'back_forward' vs 'back-forward'
  const type = nav.type || 'navigate';
  if (type === 'back_forward') return 'back-forward';
  if (type === 'prerender') return 'navigate';
  return type as 'reload' | 'navigate' | 'back-forward' | 'back-forward-cache';
}

function ratingFor(name: WebVitalsMetric['name'], value: number): WebVitalsMetric['rating'] {
  const t = PERFORMANCE_THRESHOLDS[name];
  if (!t) return 'good';
  if (value > t.poor) return 'poor';
  if (value > t.good) return 'needs-improvement';
  return 'good';
}

function percentile(values: number[], p: number): number {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, Math.min(sorted.length - 1, idx))];
}

// ===== Core Monitor =====
export class PerformanceMonitor {
  private metrics: Map<string, CustomMetric[]> = new Map();
  private observers: Map<string, PerformanceObserver> = new Map();
  private isMonitoring = false;
  private reportCallback?: (metric: WebVitalsMetric | CustomMetric) => void;
  private webVitalsSummary: Map<WebVitalsMetric['name'], WebVitalsMetric> = new Map();

  // Internal accumulators for CLS
  private clsValue = 0;
  // INP capture state
  private inpCandidate = Infinity;

  constructor(reportCallback?: (metric: WebVitalsMetric | CustomMetric) => void) {
    this.reportCallback = reportCallback;
  }

  startMonitoring(): void {
    if (this.isMonitoring || !isBrowser) return;
    this.isMonitoring = true;

    this.webVitalsSummary.clear();

    this.monitorWebVitals();
    this.monitorCustomMetrics();
    this.monitorResourceLoading();
    this.monitorNavigation();

    // Handle BFCache restore (pageshow with persisted = true)
    window.addEventListener('pageshow', this.handlePageShow);
    // Flush on hide (ensure final LCP/CLS/INP are reported)
    document.addEventListener('visibilitychange', this.handleVisibilityChange);
  }

  stopMonitoring(): void {
    if (!this.isMonitoring) return;
    this.isMonitoring = false;

    this.observers.forEach((obs) => {
      try {
        obs.disconnect();
      } catch (error) {
        console.debug('PerformanceObserver disconnect failed', error);
      }
    });
    this.observers.clear();
    this.webVitalsSummary.clear();

    window.removeEventListener('pageshow', this.handlePageShow);
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
  }

  // ---- Public API for custom metrics ----
  recordMetric(name: string, value: number, metadata?: Record<string, unknown>): void {
    const metric: CustomMetric = {
      name,
      value,
      timestamp: performance.now(),
      metadata,
    };
    if (!this.metrics.has(name)) this.metrics.set(name, []);
    this.metrics.get(name)!.push(metric);
    this.reportCallback?.(metric);
  }

  measureFunction<T>(name: string, fn: () => T): T {
    const start = isBrowser ? performance.now() : 0;
    const result = fn();
    const duration = isBrowser ? performance.now() - start : 0;
    if (isBrowser) this.recordMetric(name, duration, { type: 'function-execution' });
    return result;
  }

  async measureAsyncFunction<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = isBrowser ? performance.now() : 0;
    const result = await fn();
    const duration = isBrowser ? performance.now() - start : 0;
    if (isBrowser) this.recordMetric(name, duration, { type: 'async-function-execution' });
    return result;
  }

  startMeasure(name: string): void {
    if (!isBrowser || !('mark' in performance)) return;
    performance.mark(`${name}-start`);
  }

  endMeasure(name: string, metadata?: Record<string, unknown>): void {
    if (!isBrowser || !('measure' in performance)) return;
    const endMark = `${name}-end`;
    const measureName = `${name}-measure`;
    performance.mark(endMark);
    performance.measure(measureName, `${name}-start`, endMark);
    const measure = performance.getEntriesByName(measureName).pop();
    if (measure) {
      this.recordMetric(name, measure.duration, metadata);
    }
    performance.clearMarks(`${name}-start`);
    performance.clearMarks(endMark);
    performance.clearMeasures(measureName);
  }

  getMetrics(): Map<string, CustomMetric[]> {
    return new Map(this.metrics);
  }

  getMetricsByName(name: string): CustomMetric[] {
    return this.metrics.get(name) || [];
  }

  getPerformanceSummary(): PerformanceSummary {
    const summary: PerformanceSummary = {
      webVitals: Object.fromEntries(this.webVitalsSummary) as WebVitalsSummary,
      customMetrics: {},
      resourceTiming: this.getResourceTimingSummary(),
      navigationTiming: this.getNavigationTimingSummary(),
    };

    this.metrics.forEach((arr, name) => {
      if (!arr.length) return;
      const values = arr.map((m) => m.value);
      summary.customMetrics[name] = {
        count: arr.length,
        min: Math.min(...values),
        max: Math.max(...values),
        avg: values.reduce((a, b) => a + b, 0) / values.length,
        p95: percentile(values, 95),
        latest: arr[arr.length - 1],
      };
    });

    return summary;
  }

  // ---- Internal: Web Vitals ----
  private monitorWebVitals(): void {
    if (!hasPO) return;

    // LCP
    this.observe('largest-contentful-paint', (entries) => {
      const last = entries[entries.length - 1] as PerformanceEntry | undefined;
      if (!last) return;
      this.dispatchVital('LCP', last.startTime);
    });

    // FCP
    this.observe('paint', (entries) => {
      const fcp = entries.find((e) => (e as PerformanceEntry).name === 'first-contentful-paint') as PerformanceEntry | undefined;
      if (fcp) this.dispatchVital('FCP', fcp.startTime);
    });

    // TTFB (navigation entry gives us this deterministically)
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
    if (nav) {
      const ttfb = nav.responseStart - nav.requestStart;
      this.dispatchVital('TTFB', ttfb);
    }

    // CLS
    this.clsValue = 0;
    this.observe('layout-shift', (entries) => {
      entries.forEach((entry) => {
        const shift = entry as LayoutShift;
        if (!shift.hadRecentInput) this.clsValue += shift.value || 0;
      });
      this.dispatchVital('CLS', this.clsValue);
    });

    // INP (EventTiming; Chromium supports 'event' entryType and 'interactionId')
    // If INP unavailable, fall back to FID via 'first-input'
    let inpSupported = false;
    try {
      const observerCtor = PerformanceObserver as typeof PerformanceObserver & {
        supportedEntryTypes?: readonly string[];
      };
      const types = observerCtor.supportedEntryTypes ?? [];
      inpSupported = types.includes('event') || types.includes('event-timing');
    } catch (error) {
      console.debug('PerformanceObserver supportedEntryTypes check failed', error);
    }
    if (inpSupported) {
      this.observe('event', (entries) => {
        const eventEntries = entries as PerformanceEventTiming[];
        eventEntries.forEach((entry) => {
          const dur = entry.duration || 0;
          const name = (entry.name || '').toLowerCase();
          const continuous =
            name.includes('scroll') ||
            name.includes('drag') ||
            name.includes('mousemove') ||
            name.includes('pointermove');
          if (!continuous) {
            this.inpCandidate = Math.max(this.inpCandidate, dur);
          }
        });
        if (this.inpCandidate !== Infinity) {
          this.dispatchVital('INP', this.inpCandidate);
        }
      });
    } else {
      // Fallback: FID
      this.observe('first-input', (entries) => {
        const first = entries[0] as PerformanceEventTiming | undefined;
        if (!first) return;
        const fid = first.processingStart - first.startTime;
        this.dispatchVital('FID', fid);
      });
    }
  }

  // ---- Internal: Custom continuous monitors ----
  private monitorCustomMetrics(): void {
    if (!isBrowser) return;

    // Animation frame times
    let last = performance.now();
    let rafId = 0;
    const tick = () => {
      const now = performance.now();
      const dt = now - last;
      // Skip first frame
      if (last !== 0) {
        this.recordMetric('ANIMATION_FRAME_TIME', dt, { type: 'animation-performance' });
      }
      last = now;
      if (this.isMonitoring) rafId = requestAnimationFrame(tick);
    };
    rafId = requestAnimationFrame(tick);

    // Ensure we stop this RAF when monitoring stops
    const stopRAF = () => cancelAnimationFrame(rafId);
    window.addEventListener('pagehide', stopRAF, { once: true });
  }

  private monitorResourceLoading(): void {
    if (!hasPO) return;
    this.observe('resource', (entries) => {
      entries.forEach((entry) => {
        const resource = entry as PerformanceResourceTiming;
        const loadTime = resource.responseEnd - resource.startTime;
        const type = resource.initiatorType || 'other';
        this.recordMetric(`resource-load-${type}`, loadTime, {
          type: 'resource-loading',
          url: resource.name,
          size: resource.transferSize,
          cached: resource.transferSize === 0,
        });
      });
    });
  }

  private monitorNavigation(): void {
    if (!hasPO) return;
    this.observe('navigation', (entries) => {
      const entry = entries[0] as PerformanceNavigationTiming | undefined;
      if (!entry) return;

      // Overall
      this.recordMetric('navigation-total', entry.loadEventEnd - entry.startTime, {
        type: 'navigation',
        navigationType: entry.type,
      });
      // Timing slices
      this.recordMetric('navigation-dns', entry.domainLookupEnd - entry.domainLookupStart, {
        type: 'navigation-timing',
      });
      this.recordMetric('navigation-connect', entry.connectEnd - entry.connectStart, {
        type: 'navigation-timing',
      });
      this.recordMetric('navigation-ttfb', entry.responseStart - entry.requestStart, {
        type: 'navigation-timing',
      });
    });
  }

  // ---- Observers ----
  private observe(entryType: string, cb: (entries: PerformanceEntry[]) => void): void {
    try {
      const observer = new PerformanceObserver((list) => {
        cb(list.getEntries());
      });
      observer.observe({ type: entryType, buffered: true });
      this.observers.set(entryType, observer);
    } catch (error) {
      console.debug('PerformanceObserver observe failed', error);
    }
  }

  // ---- Vital dispatch ----
  private dispatchVital(name: WebVitalsMetric['name'], value: number): void {
    const metric: WebVitalsMetric = {
      name,
      value,
      rating: ratingFor(name, value),
      delta: value,
      id: `${name}-${Date.now()}`,
      navigationType: navType(),
    };
    this.webVitalsSummary.set(name, metric);
    this.reportCallback?.(metric);
  }

  public tapReportCallback(tap: (metric: WebVitalsMetric | CustomMetric) => void): () => void {
    const previous = this.reportCallback;
    this.reportCallback = (metric) => {
      previous?.(metric);
      tap(metric);
    };
    return () => {
      this.reportCallback = previous;
    };
  }

  // ---- Summaries ----
  private getResourceTimingSummary(): ResourceTimingSummary {
    const entries = (performance.getEntriesByType('resource') as PerformanceResourceTiming[]) || [];
    const summary: ResourceTimingSummary = {
      totalResources: entries.length,
      totalSize: 0,
      totalLoadTime: 0,
      byType: {},
    };
    entries.forEach((e) => {
      const type = e.initiatorType || 'other';
      const load = e.responseEnd - e.startTime;
      const size = e.transferSize || 0;
      summary.totalSize += size;
      summary.totalLoadTime += load;

      if (!summary.byType[type]) {
        summary.byType[type] = { count: 0, totalSize: 0, totalLoadTime: 0, avgLoadTime: 0 };
      }
      const slot = summary.byType[type];
      slot.count += 1;
      slot.totalSize += size;
      slot.totalLoadTime += load;
      slot.avgLoadTime = slot.totalLoadTime / slot.count;
    });
    return summary;
    }

  private getNavigationTimingSummary(): NavigationTimingSummary {
    const e = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
    if (!e) {
      return { totalTime: 0, dnsTime: 0, connectTime: 0, ttfb: 0, domContentLoaded: 0, loadComplete: 0 };
    }
    return {
      totalTime: e.loadEventEnd - e.startTime,
      dnsTime: e.domainLookupEnd - e.domainLookupStart,
      connectTime: e.connectEnd - e.connectStart,
      ttfb: e.responseStart - e.requestStart,
      domContentLoaded: e.domContentLoadedEventEnd - e.startTime,
      loadComplete: e.loadEventEnd - e.startTime,
    };
  }

  // ---- Event handlers ----
  private handlePageShow = (ev: PageTransitionEvent) => {
    // If restored from BFCache, re-emit navigation context & keep observers alive
    // Consumers can detect via navigationType === 'back-forward'
    if (ev.persisted) {
      // Make a small synthetic mark so downstream can associate new session slice
      this.recordMetric('bf-cache-restore', 0, { type: 'lifecycle' });
    }
  };

  private handleVisibilityChange = () => {
    if (document.visibilityState === 'hidden') {
      // Flush final INP/CLS/LCP values by dispatching current accumulated values
      if (this.clsValue > 0) this.dispatchVital('CLS', this.clsValue);
      if (this.inpCandidate !== Infinity) this.dispatchVital('INP', this.inpCandidate);
      // LCP is handled via observer buffered entries already, but we could sample last paint here if needed.
    }
  };
}

// ===== Singleton instance =====
export const performanceMonitor = new PerformanceMonitor();

// ===== React hook: uses the singleton (no duplicate observers) =====
export function usePerformanceMonitor() {
  const [isMonitoring, setIsMonitoring] = React.useState(false);
  const [metrics, setMetrics] = React.useState<Map<string, CustomMetric[]>>(new Map());

  React.useEffect(() => {
    if (!isBrowser) return;

    // Wire a one-time reporter to update state snapshots (without re-registering observers)
    const reporter = (metric: WebVitalsMetric | CustomMetric) => {
      // For custom metrics, update the local Map snapshot
      if ('timestamp' in metric && metric.timestamp != null) {
        setMetrics(new Map(performanceMonitor.getMetrics()));
      }
      // Optionally, send Web Vitals to analytics here.
      // Example:
      // if ('gtag' in window) (window as Window & { gtag?: (...args: unknown[]) => void }).gtag?.('event', 'web_vital', {
      //   name: metric.name,
      //   value: metric.value,
      // });
    };

    // Temporarily replace the monitor’s callback so this hook can receive updates too.
    const restoreReport = performanceMonitor.tapReportCallback(reporter);

    performanceMonitor.startMonitoring();
    setIsMonitoring(true);

    // Initial snapshot (if any custom metrics recorded before mount)
    setMetrics(new Map(performanceMonitor.getMetrics()));

    return () => {
      // Restore original callback and stop monitor
      restoreReport();
      performanceMonitor.stopMonitoring();
      setIsMonitoring(false);
    };
  }, []);

  const recordMetric = React.useCallback(
    (name: string, value: number, metadata?: Record<string, unknown>) => {
      performanceMonitor.recordMetric(name, value, metadata);
      setMetrics(new Map(performanceMonitor.getMetrics()));
    },
    []
  );

  const measureFunction = React.useCallback(<T,>(name: string, fn: () => T): T => {
    return performanceMonitor.measureFunction(name, fn);
  }, []);

  const measureAsyncFunction = React.useCallback(async <T,>(name: string, fn: () => Promise<T>): Promise<T> => {
    return performanceMonitor.measureAsyncFunction(name, fn);
  }, []);

  const getPerformanceSummary = React.useCallback(() => performanceMonitor.getPerformanceSummary(), []);

  return {
    isMonitoring,
    metrics,
    recordMetric,
    measureFunction,
    measureAsyncFunction,
    getPerformanceSummary,
  };
}

// ===== Budget checker =====
export function checkPerformanceBudget(
  metric: WebVitalsMetric | CustomMetric
): {
  withinBudget: boolean;
  rating: 'good' | 'needs-improvement' | 'poor';
  threshold: { good: number; poor: number } | null;
} {
  const thresholds = PERFORMANCE_THRESHOLDS as Record<string, { good: number; poor: number }>;
  const threshold = thresholds[metric.name];
  if (!threshold) {
    return { withinBudget: true, rating: 'good', threshold: null };
  }
  let r: 'good' | 'needs-improvement' | 'poor' = 'good';
  if (metric.value > threshold.poor) r = 'poor';
  else if (metric.value > threshold.good) r = 'needs-improvement';
  return { withinBudget: r === 'good', rating: r, threshold };
}
