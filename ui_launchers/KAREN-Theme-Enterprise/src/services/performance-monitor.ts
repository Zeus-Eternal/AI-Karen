/**
 * Comprehensive Performance Monitoring Service (SSR-safe, INP-ready)
 * Tracks Web Vitals (CLS, FCP, LCP, TTFB, INP/FID), page load, interactions,
 * resource usage, long tasks, alerts, and exposes a clean subscription API.
 */

import { onCLS, onFCP, onLCP, onTTFB, onINP } from 'web-vitals';
import type { Metric } from 'web-vitals';

const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';
const hasPO = typeof PerformanceObserver !== 'undefined';

export interface WebVitalsMetrics {
  cls: number;
  fcp: number;
  lcp: number;
  ttfb: number;
  inp: number; // Primary in 2024+
  fid?: number; // Back-compat when INP not available
}

export type PerformanceMetricMetadata = Record<string, unknown>;

export interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: PerformanceMetricMetadata;
}

export interface ResourceUsage {
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  cpu?: {
    usage: number;   // Estimated (browser cannot read real CPU)
    cores: number;
  };
  network: {
    downlink: number;
    effectiveType: string;
    rtt: number;
  };
}

export interface PerformanceAlert {
  id: string;
  type: 'warning' | 'critical';
  metric: string;
  value: number;
  threshold: number;
  timestamp: number;
  message: string;
}

export interface PerformanceThresholds {
  lcp: { warning: number; critical: number };
  inp: { warning: number; critical: number }; // INP (replaces FID)
  fid: { warning: number; critical: number }; // fallback thresholds
  cls: { warning: number; critical: number };
  fcp: { warning: number; critical: number };
  ttfb: { warning: number; critical: number };
  pageLoad: { warning: number; critical: number };
  interaction: { warning: number; critical: number };
  memoryUsage: { warning: number; critical: number };
}

export type AlertListener = (alert: PerformanceAlert) => void;

export interface PerformanceMetrics {
  vitals: Partial<WebVitalsMetrics>;
  metrics: PerformanceMetric[];
  alerts: PerformanceAlert[];
  resourceUsage: ResourceUsage;
}

export type PerformanceEvent =
  | { type: 'metric'; metric: PerformanceMetric }
  | { type: 'alert'; alert: PerformanceAlert };

type PerformanceWithMemory = Performance & {
  memory?: {
    usedJSHeapSize?: number;
    totalJSHeapSize?: number;
  };
};

interface NetworkInformation {
  downlink?: number;
  effectiveType?: string;
  rtt?: number;
  addEventListener?: (type: string, listener: EventListenerOrEventListenerObject) => void;
  removeEventListener?: (type: string, listener: EventListenerOrEventListenerObject) => void;
}

type NavigatorWithConnection = Navigator & {
  connection?: NetworkInformation;
};

export class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private alerts: PerformanceAlert[] = [];
  private observers: PerformanceObserver[] = [];
  private intervals: number[] = [];
  private thresholds: PerformanceThresholds;
  private alertCallbacks: AlertListener[] = [];
  private vitalsCache: Partial<WebVitalsMetrics> = {};

  constructor(thresholds?: Partial<PerformanceThresholds>) {
    this.thresholds = {
      lcp: { warning: 2500, critical: 4000 },
      inp: { warning: 200, critical: 500 },  // good: <200ms, needs-improvement: 200–500, poor: >500
      fid: { warning: 100, critical: 300 },  // only as fallback
      cls: { warning: 0.1, critical: 0.25 },
      fcp: { warning: 1800, critical: 3000 },
      ttfb: { warning: 800, critical: 1800 },
      pageLoad: { warning: 3000, critical: 5000 },
      interaction: { warning: 100, critical: 300 },
      memoryUsage: { warning: 80, critical: 95 },
      ...thresholds,
    };

    if (isBrowser) {
      this.initializeWebVitalsTracking();
      this.initializeResourceMonitoring();
      this.initializeInteractionTracking();
      this.setupLifecycleGuards();
    }
  }

  // -------------------- Initialization --------------------

  private initializeWebVitalsTracking(): void {
    // CLS/FCP/LCP/TTFB always available
    try {
      onCLS((m) => {
        this.vitalsCache.cls = m.value;
        this.recordMetric('cls', m.value, { id: m.id });
        this.checkThreshold('cls', m.value);
      });
      onFCP((m) => {
        this.vitalsCache.fcp = m.value;
        this.recordMetric('fcp', m.value, { id: m.id });
        this.checkThreshold('fcp', m.value);
      });
      onLCP((m) => {
        this.vitalsCache.lcp = m.value;
        this.recordMetric('lcp', m.value, { id: m.id });
        this.checkThreshold('lcp', m.value);
      });
      onTTFB((m) => {
        this.vitalsCache.ttfb = m.value;
        this.recordMetric('ttfb', m.value, { id: m.id });
        this.checkThreshold('ttfb', m.value);
      });
    } catch (error) {
      void error;
    }

    // INP primary (replaces FID in web-vitals v4+)
    try {
      onINP((m: Metric) => {
        // web-vitals returns INP with .value
        this.vitalsCache.inp = m.value;
        this.recordMetric('inp', m.value, { id: m.id });
        this.checkThreshold('inp', m.value);
      });
    } catch (error) {
      void error;
    }
  }

  private initializeResourceMonitoring(): void {
    // Memory polling (Chrome-only)
    const memInterval = window.setInterval(() => {
      const perf = performance as PerformanceWithMemory;
      if (perf && perf.memory) {
        const used = perf.memory.usedJSHeapSize || 0;
        const total = perf.memory.totalJSHeapSize || 0;
        const pct = total > 0 ? (used / total) * 100 : 0;
        this.recordMetric('memory-usage', pct, { used, total });
        this.checkThreshold('memoryUsage', pct);
      }
    }, 5000);
    this.intervals.push(memInterval);

    // Network info snapshot + listener
    const conn = (navigator as NavigatorWithConnection).connection;
    if (conn) {
      const snapshot = () => {
        this.recordMetric('network-downlink', conn.downlink ?? 0, {
          effectiveType: conn.effectiveType,
          rtt: conn.rtt,
        });
      };
      try {
        conn.addEventListener?.('change', snapshot);
      } catch (error) {
        void error;
      }
      snapshot();
    }
  }

  private initializeInteractionTracking(): void {
    // Long tasks (UI jank)
    if (hasPO) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const dur = entry.duration ?? 0;
            this.recordMetric('long-task', dur, {
              startTime: entry.startTime,
              name: entry.name,
            });
            if (dur > this.thresholds.interaction.warning) {
              this.createAlert(
                'warning',
                'long-task',
                dur,
                this.thresholds.interaction.warning,
                `Long task detected: ${dur.toFixed(0)}ms`
              );
            }
          }
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.push(longTaskObserver);
      } catch (error) {
        void error;
      }
    }

    // Navigation timing (page load)
    if (hasPO) {
      try {
        const navigationObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const nav = entry as PerformanceNavigationTiming;
            const navigationStart = typeof nav.startTime === 'number' ? nav.startTime : 0;
            const pageLoadTime = nav.loadEventEnd - navigationStart;
            this.recordMetric('page-load', pageLoadTime, {
              domContentLoaded: nav.domContentLoadedEventEnd - navigationStart,
              firstByte: nav.responseStart - navigationStart,
              domComplete: nav.domComplete - navigationStart,
            });
            this.checkThreshold('pageLoad', pageLoadTime);
          }
        });
        navigationObserver.observe({ type: 'navigation', buffered: true });
        this.observers.push(navigationObserver);
      } catch (error) {
        void error;
      }
    }
  }

  private setupLifecycleGuards(): void {
    // Clear old metrics periodically
    const trimInterval = window.setInterval(() => {
      this.clearOldMetrics(24 * 60 * 60 * 1000);
    }, 60 * 1000);
    this.intervals.push(trimInterval);

    // Optional: flush point hooks (you can wire to your telemetry here)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        void 0;
      }
    });
    window.addEventListener('pagehide', () => {
      void 0;
    });
  }

  // -------------------- Public API --------------------

  trackPageLoad(route: string, startTime?: number): void {
    const t = typeof startTime === 'number' ? startTime : (performance.now ? performance.now() : Date.now());
    this.recordMetric('route-load', t, { route });
    this.checkThreshold('pageLoad', t);
  }

  trackUserInteraction(action: string, duration: number, metadata?: Record<string, unknown>): void {
    this.recordMetric('user-interaction', duration, { action, ...metadata });
    this.checkThreshold('interaction', duration);
  }

  trackAPICall(endpoint: string, duration: number, status: number, metadata?: Record<string, unknown>): void {
    this.recordMetric('api-call', duration, {
      endpoint,
      status,
      success: status >= 200 && status < 300,
      ...metadata,
    });
    if (duration > 2000) {
      this.createAlert('warning', 'api-call', duration, 2000, `Slow API call: ${endpoint} (${duration.toFixed(0)}ms)`);
    }
  }

  getCurrentResourceUsage(): ResourceUsage {
    if (!isBrowser) {
      return {
        memory: { used: 0, total: 0, percentage: 0 },
        network: { downlink: 0, effectiveType: 'unknown', rtt: 0 },
      };
    }

    const perf = performance as PerformanceWithMemory;
    const memory = perf.memory;
    const conn = (navigator as NavigatorWithConnection).connection;
    return {
      memory: memory
        ? {
            used: memory.usedJSHeapSize ?? 0,
            total: memory.totalJSHeapSize ?? 0,
            percentage: memory.usedJSHeapSize && memory.totalJSHeapSize 
              ? (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100 
              : 0,
          }
        : { used: 0, total: 0, percentage: 0 },
      network: conn
        ? { 
            downlink: conn.downlink ?? 0, 
            effectiveType: conn.effectiveType ?? 'unknown', 
            rtt: conn.rtt ?? 0 
          }
        : { downlink: 0, effectiveType: 'unknown', rtt: 0 },
      // cpu usage cannot be read in the browser; expose hint only if desired
    };
  }

  getWebVitalsMetrics(): Partial<WebVitalsMetrics> {
    // Use last recorded values
    const result: Partial<WebVitalsMetrics> = {};
    if (this.vitalsCache.cls != null) result.cls = this.vitalsCache.cls;
    if (this.vitalsCache.fcp != null) result.fcp = this.vitalsCache.fcp;
    if (this.vitalsCache.lcp != null) result.lcp = this.vitalsCache.lcp;
    if (this.vitalsCache.ttfb != null) result.ttfb = this.vitalsCache.ttfb;
    if (this.vitalsCache.inp != null) result.inp = this.vitalsCache.inp;
    if (this.vitalsCache.fid != null) result.fid = this.vitalsCache.fid;
    return result;
  }

  getMetrics(type?: string, limit?: number): PerformanceMetric[] {
    let filtered = type ? this.metrics.filter((m) => m.name === type) : this.metrics;
    if (limit) filtered = filtered.slice(-limit);
    return filtered.sort((a, b) => b.timestamp - a.timestamp);
  }

  getLatestMetrics(types: string[]): PerformanceMetric[] {
    return types
      .map((t) => this.metrics.filter((m) => m.name === t).pop())
      .filter(Boolean) as PerformanceMetric[];
  }

  getAlerts(limit?: number): PerformanceAlert[] {
    const sorted = [...this.alerts].sort((a, b) => b.timestamp - a.timestamp);
    return limit ? sorted.slice(0, limit) : sorted;
  }

  getPerformanceMetrics(limit: number = 100): PerformanceMetrics {
    return {
      vitals: this.getWebVitalsMetrics(),
      metrics: this.getMetrics(undefined, limit),
      alerts: this.getAlerts(limit),
      resourceUsage: this.getCurrentResourceUsage(),
    };
  }

  onAlert(callback: AlertListener): () => void {
    this.alertCallbacks.push(callback);
    return () => {
      const idx = this.alertCallbacks.indexOf(callback);
      if (idx > -1) this.alertCallbacks.splice(idx, 1);
    };
  }

  getOptimizationRecommendations(): string[] {
    const recs: string[] = [];
    const vitals = this.getWebVitalsMetrics();

    if (vitals.lcp != null && vitals.lcp > this.thresholds.lcp.warning) {
      recs.push('Improve LCP: optimize hero image, reduce server response time, inline critical CSS, preconnect origins.');
    }
    if (vitals.inp != null && vitals.inp > this.thresholds.inp.warning) {
      recs.push('Improve INP: break up long tasks, reduce JS on main thread, defer non-critical work, use Web Workers.');
    } else if (vitals.fid != null && vitals.fid > this.thresholds.fid.warning) {
      recs.push('FID high (fallback): reduce JS blocking, split bundles, offload heavy handlers.');
    }
    if (vitals.cls != null && vitals.cls > this.thresholds.cls.warning) {
      recs.push('Reduce CLS: set width/height on images/iframes, avoid layout shifts above the fold.');
    }

    const mem = this.getMetrics('memory-usage', 10);
    if (mem.length) {
      const avg = mem.reduce((s, m) => s + m.value, 0) / mem.length;
      if (avg > this.thresholds.memoryUsage.warning) {
        recs.push('Heap pressure high: release caches on route change, clean subscriptions, reduce object churn.');
      }
    }
    return recs;
  }

  clearOldMetrics(maxAge: number = 24 * 60 * 60 * 1000): void {
    const cutoff = Date.now() - maxAge;
    this.metrics = this.metrics.filter((m) => m.timestamp > cutoff);
    this.alerts = this.alerts.filter((a) => a.timestamp > cutoff);
  }

  destroy(): void {
    this.observers.forEach((o) => {
      try {
        o.disconnect();
      } catch (error) {
        void error;
      }
    });
    this.observers = [];
    this.alertCallbacks = [];
    this.intervals.forEach((id) => clearInterval(id));
    this.intervals = [];
  }

  // -------------------- Internals --------------------

  private recordMetric(name: string, value: number, metadata?: PerformanceMetricMetadata): void {
    this.metrics.push({ name, value, timestamp: Date.now(), metadata });
    // cap storage to avoid leaks
    if (this.metrics.length >= 5000) this.metrics = this.metrics.slice(-2500);
  }

  private checkThreshold(metricType: keyof PerformanceThresholds, value: number): void {
    const threshold = this.thresholds[metricType];
    if (!threshold) return;
    if (value > threshold.critical) {
      this.createAlert('critical', String(metricType), value, threshold.critical,
        `Critical: ${metricType} = ${value.toFixed(2)}`);
    } else if (value > threshold.warning) {
      this.createAlert('warning', String(metricType), value, threshold.warning,
        `Warning: ${metricType} = ${value.toFixed(2)}`);
    }
  }

  private createAlert(
    type: 'warning' | 'critical',
    metric: string,
    value: number,
    threshold: number,
    message: string
  ): void {
    const alert: PerformanceAlert = {
      id: `${metric}-${Date.now()}`,
      type,
      metric,
      value,
      threshold,
      timestamp: Date.now(),
      message,
    };
    this.alerts.push(alert);
    // trim
    if (this.alerts.length >= 1000) this.alerts = this.alerts.slice(-500);
    // notify
    this.alertCallbacks.forEach((cb) => {
      try {
        cb(alert);
      } catch (error) {
        void error;
      }
    });
  }
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor();
export default performanceMonitor;
