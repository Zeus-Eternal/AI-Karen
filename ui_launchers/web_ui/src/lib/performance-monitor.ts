'use client';
/**
 * Performance Monitoring for API Requests (production-grade)
 * - SSR-safe (guards on window/document)
 * - Percentiles (median/p95/p99)
 * - Bounded memory (keeps last N + 1h age trim)
 * - Realtime alerts: slow_request / high_error_rate / performance_degradation
 * - Listener API for dashboards
 * - wrapFetch() to auto-record timings & sizes
 */

import { webUIConfig } from './config';
import { safeError, safeWarn } from './safe-console';

export interface RequestMetrics {
  endpoint: string;
  method: string;
  startTime: number; // performance.now()
  endTime: number;   // performance.now()
  duration: number;  // ms
  status: number;
  success: boolean;
  size?: number;     // bytes, if known (from Content-Length or hint)
  error?: string;
  timestamp: string; // ISO time (wall clock)
}

export interface PerformanceStats {
  totalRequests: number;
  averageResponseTime: number;
  medianResponseTime: number;
  p95ResponseTime: number;
  p99ResponseTime: number;
  slowestRequest: RequestMetrics | null;
  fastestRequest: RequestMetrics | null;
  errorRate: number;
  requestsPerMinute: number;
  endpointStats: Record<
    string,
    {
      count: number;
      averageTime: number;
      errorRate: number;
      lastRequest: string;
    }
  >;
}

export type PerformanceAlertType =
  | 'slow_request'
  | 'high_error_rate'
  | 'performance_degradation';

export interface PerformanceAlert {
  id: string;
  type: PerformanceAlertType;
  message: string;
  severity: 'low' | 'medium' | 'high';
  timestamp: string;
  metrics: RequestMetrics | PerformanceStats;
}

type MetricsListener = (metrics: RequestMetrics) => void;
type AlertListener = (alert: PerformanceAlert) => void;

const isBrowser =
  typeof window !== 'undefined' && typeof document !== 'undefined';

class PerformanceMonitor {
  private metrics: RequestMetrics[] = [];
  private maxMetrics = 1000; // Keep last 1000 requests
  private listeners: MetricsListener[] = [];
  private alertListeners: AlertListener[] = [];
  private slowRequestThreshold = 5000; // 5 seconds
  private verySlowRequestThreshold = 10000; // 10 seconds
  private trimTimer: ReturnType<typeof setInterval> | null = null;

  constructor() {
    // Periodic cleanup (browser only)
    if (isBrowser) {
      this.trimTimer = setInterval(() => this.cleanupOldMetrics(), 60_000);
    }
  }

  // -------------------- Recording --------------------

  public recordRequest(
    endpoint: string,
    method: string,
    startTime: number,
    endTime: number,
    status: number,
    size?: number,
    error?: string
  ): void {
    const duration = endTime - startTime;
    const success = status >= 200 && status < 400;

    const metric: RequestMetrics = {
      endpoint,
      method,
      startTime,
      endTime,
      duration,
      status,
      success,
      size,
      error,
      timestamp: new Date().toISOString(),
    };

    // Add newest first
    this.metrics.unshift(metric);

    // Bound memory
    if (this.metrics.length > this.maxMetrics) {
      this.metrics.length = this.maxMetrics;
    }

    // Alerts + listeners
    this.checkPerformanceAlerts(metric);
    this.notifyListeners(metric);

    // Slow logging (optional)
    if (webUIConfig?.performanceMonitoring && duration > this.slowRequestThreshold) {
      const isVerySlow = duration > this.verySlowRequestThreshold;
      const payload = { duration, status, success, size, error, endpoint, method };
      if (isVerySlow) {
        safeWarn('🐌 Very slow request', payload);
      } else {
        safeWarn('🐌 Slow request', payload);
      }
    }
  }

  // -------------------- Alerts --------------------

  private checkPerformanceAlerts(metric: RequestMetrics): void {
    // Slow request alert
    if (metric.duration > this.slowRequestThreshold) {
      const severity: 'medium' | 'high' =
        metric.duration > this.verySlowRequestThreshold ? 'high' : 'medium';
      this.triggerAlert({
        id: `slow_request_${Date.now()}`,
        type: 'slow_request',
        message: `Slow request: ${metric.method} ${metric.endpoint} took ${Math.round(
          metric.duration
        )}ms`,
        severity,
        timestamp: new Date().toISOString(),
        metrics: metric,
      });
    }

    // Perf degradation: compare last 10 vs previous 10
    if (this.metrics.length >= 20) {
      const recent = this.metrics.slice(0, 10);
      const older = this.metrics.slice(10, 20);
      const avgRecent = avg(recent.map((m) => m.duration));
      const avgOlder = avg(older.map((m) => m.duration));
      if (avgOlder > 0 && avgRecent > avgOlder * 1.5 && avgRecent > 2000) {
        this.triggerAlert({
          id: `performance_degradation_${Date.now()}`,
          type: 'performance_degradation',
          message: `Recent requests are ${Math.round(
            ((avgRecent / avgOlder - 1) * 100)
          )}% slower`,
          severity: 'medium',
          timestamp: new Date().toISOString(),
          metrics: this.getStats(),
        });
      }
    }

    // High error rate (last 20)
    if (this.metrics.length >= 20) {
      const recent = this.metrics.slice(0, 20);
      const errRate =
        recent.filter((m) => !m.success).length / recent.length;
      if (errRate > 0.3) {
        this.triggerAlert({
          id: `high_error_rate_${Date.now()}`,
          type: 'high_error_rate',
          message: `High error rate: ${Math.round(errRate * 100)}% of last 20 requests`,
          severity: 'high',
          timestamp: new Date().toISOString(),
          metrics: this.getStats(),
        });
      }
    }
  }

  private triggerAlert(alert: PerformanceAlert): void {
    if (isBrowser) {
      // Lazy import service; if missing, fallback to console
      import('./performance-alert-service')
        .then(({ performanceAlertService }) => {
          performanceAlertService.handleAlert(alert);
        })
        .catch((err) => {
          safeWarn('Performance alert service unavailable; falling back to console', err);
          const level = alert.severity === 'high' ? 'warn' : 'info';
          console[level](`Karen Performance: ${alert.message}`, {
            type: alert.type,
            severity: alert.severity,
            endpoint: (alert.metrics as any)?.endpoint ?? 'unknown',
          });
        });
    } else {
      const level = alert.severity === 'high' ? 'warn' : 'info';
      console[level](`Karen Performance: ${alert.message}`, {
        type: alert.type,
        severity: alert.severity,
        endpoint: (alert.metrics as any)?.endpoint ?? 'unknown',
      });
    }

    // Local listeners
    for (const listener of this.alertListeners) {
      try {
        listener(alert);
      } catch (e) {
        safeError('Error in performance alert listener:', e);
      }
    }
  }

  private notifyListeners(metric: RequestMetrics): void {
    for (const listener of this.listeners) {
      try {
        listener(metric);
      } catch (e) {
        safeError('Error in performance metrics listener:', e);
      }
    }
  }

  private cleanupOldMetrics(): void {
    const oneHourAgo = Date.now() - 60 * 60 * 1000;
    this.metrics = this.metrics.filter((m) => m.startTime > oneHourAgo);
  }

  // -------------------- Stats & Queries --------------------

  public getStats(): PerformanceStats {
    if (this.metrics.length === 0) {
      return {
        totalRequests: 0,
        averageResponseTime: 0,
        medianResponseTime: 0,
        p95ResponseTime: 0,
        p99ResponseTime: 0,
        slowestRequest: null,
        fastestRequest: null,
        errorRate: 0,
        requestsPerMinute: 0,
        endpointStats: {},
      };
    }

    const durations = this.metrics.map((m) => m.duration).sort((a, b) => a - b);
    const fastest =
      this.metrics.reduce<RequestMetrics | null>(
        (acc, cur) => (!acc || cur.duration < acc.duration ? cur : acc),
        null
      ) ?? null;
    const slowest =
      this.metrics.reduce<RequestMetrics | null>(
        (acc, cur) => (!acc || cur.duration > acc.duration ? cur : acc),
        null
      ) ?? null;

    // Requests per minute over the observed window
    const oldestStart = Math.min(...this.metrics.map((m) => m.startTime));
    const minutes = Math.max((Date.now() - oldestStart) / (1000 * 60), 0.0001);
    const rpm = this.metrics.length / minutes;

    // Endpoint aggregates
    const map: Record<
      string,
      { count: number; totalTime: number; errors: number; lastRequest: string }
    > = {};
    for (const m of this.metrics) {
      const key = `${m.method} ${m.endpoint}`;
      if (!map[key]) {
        map[key] = { count: 0, totalTime: 0, errors: 0, lastRequest: m.timestamp };
      }
      map[key].count++;
      map[key].totalTime += m.duration;
      if (!m.success) map[key].errors++;
      if (m.timestamp > map[key].lastRequest) map[key].lastRequest = m.timestamp;
    }
    const endpointStats: PerformanceStats['endpointStats'] = {};
    for (const [key, v] of Object.entries(map)) {
      endpointStats[key] = {
        count: v.count,
        averageTime: v.totalTime / v.count,
        errorRate: v.errors / v.count,
        lastRequest: v.lastRequest,
      };
    }

    return {
      totalRequests: this.metrics.length,
      averageResponseTime: avg(durations),
      medianResponseTime: percentile(durations, 50),
      p95ResponseTime: percentile(durations, 95),
      p99ResponseTime: percentile(durations, 99),
      slowestRequest: slowest,
      fastestRequest: fastest,
      errorRate:
        this.metrics.filter((m) => !m.success).length / this.metrics.length,
      requestsPerMinute: rpm,
      endpointStats,
    };
  }

  public getRecentMetrics(limit = 50): RequestMetrics[] {
    return this.metrics.slice(0, limit);
  }

  public getEndpointMetrics(endpoint: string, method?: string): RequestMetrics[] {
    return this.metrics.filter(
      (m) => m.endpoint === endpoint && (!method || m.method === method)
    );
  }

  public getSlowRequests(threshold = this.slowRequestThreshold): RequestMetrics[] {
    return this.metrics.filter((m) => m.duration > threshold);
  }

  public getFailedRequests(): RequestMetrics[] {
    return this.metrics.filter((m) => !m.success);
  }

  // -------------------- Listeners & Config --------------------

  public onMetrics(listener: MetricsListener): () => void {
    this.listeners.push(listener);
    return () => {
      const i = this.listeners.indexOf(listener);
      if (i >= 0) this.listeners.splice(i, 1);
    };
  }

  public onAlert(listener: AlertListener): () => void {
    this.alertListeners.push(listener);
    return () => {
      const i = this.alertListeners.indexOf(listener);
      if (i >= 0) this.alertListeners.splice(i, 1);
    };
  }

  public clearMetrics(): void {
    this.metrics = [];
  }

  public setSlowRequestThreshold(ms: number): void {
    this.slowRequestThreshold = ms;
  }

  public setVerySlowRequestThreshold(ms: number): void {
    this.verySlowRequestThreshold = ms;
  }

  public exportMetrics(): string {
    return JSON.stringify(
      {
        metrics: this.metrics,
        stats: this.getStats(),
        exportedAt: new Date().toISOString(),
      },
      null,
      2
    );
  }

  public destroy(): void {
    if (this.trimTimer) {
      clearInterval(this.trimTimer);
      this.trimTimer = null;
    }
  }

  // -------------------- Helpers --------------------

  /**
   * Wrap fetch to auto-capture metrics (status, duration, size if available).
   * Returns the original Response.
   */
  public async wrapFetch(
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> {
    const start = performance.now();
    let status = 0;
    let size: number | undefined = undefined;
    let errMsg: string | undefined = undefined;

    const endpoint =
      typeof input === 'string'
        ? input
        : input instanceof URL
        ? input.toString()
        : (input as Request).url ?? 'unknown';

    const method =
      (init?.method || (input as Request)?.method || 'GET').toUpperCase();

    try {
      const res = await fetch(input as any, init);
      status = res.status;

      // Try content-length header
      const len = res.headers.get('content-length');
      if (len) {
        const parsed = parseInt(len, 10);
        if (Number.isFinite(parsed)) size = parsed;
      }

      // Record before returning
      const end = performance.now();
      this.recordRequest(endpoint, method, start, end, status, size);

      return res;
    } catch (e: any) {
      status = 0; // network error
      errMsg = e?.message ?? String(e);
      const end = performance.now();
      this.recordRequest(endpoint, method, start, end, status, size, errMsg);
      throw e;
    }
  }
}

// -------------------- Utilities --------------------

function avg(arr: number[]): number {
  if (arr.length === 0) return 0;
  return arr.reduce((s, v) => s + v, 0) / arr.length;
}

function percentile(sortedAsc: number[], p: number): number {
  if (sortedAsc.length === 0) return 0;
  const rank = (p / 100) * (sortedAsc.length - 1);
  const low = Math.floor(rank);
  const high = Math.ceil(rank);
  if (low === high) return sortedAsc[low];
  const w = rank - low;
  return sortedAsc[low] * (1 - w) + sortedAsc[high] * w;
}

// -------------------- Singleton accessors --------------------

let _perfMon: PerformanceMonitor | null = null;

export function getPerformanceMonitor(): PerformanceMonitor {
  if (!_perfMon) _perfMon = new PerformanceMonitor();
  return _perfMon;
}

export function initializePerformanceMonitor(): PerformanceMonitor {
  _perfMon = new PerformanceMonitor();
  return _perfMon;
}

export { PerformanceMonitor };
