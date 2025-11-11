// ui_launchers/KAREN-Theme-Default/src/components/performance/performance-monitor.tsx
"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Activity, Zap, X } from "lucide-react";

export interface PerformanceMetrics {
  // Core Web Vitals / key timings (milliseconds unless noted)
  lcp?: number; // Largest Contentful Paint (ms)
  fid?: number; // First Input Delay (ms)
  cls?: number; // Cumulative Layout Shift (unitless)
  // Other metrics
  fcp?: number; // First Contentful Paint (ms)
  ttfb?: number; // Time to First Byte (ms)
  // Bundle metrics (best-effort)
  bundleSize?: number; // bytes (approx)
  loadTime?: number; // ms (full load)
  // Memory usage (bytes)
  usedJSHeapSize?: number;
  totalJSHeapSize?: number;
  jsHeapSizeLimit?: number;
}

export interface PerformanceMonitorProps {
  /** Whether to show the performance overlay in development */
  showOverlay?: boolean;
  /** Whether to log metrics to console */
  logMetrics?: boolean;
  /** Callback when metrics are collected */
  onMetricsCollected?: (metrics: PerformanceMetrics) => void;
  /** Whether to send metrics to analytics */
  sendToAnalytics?: boolean;
  /** Analytics endpoint URL */
  analyticsEndpoint?: string;
}

/** Utility: now in ms with high resolution */
const nowMs = () => (typeof performance !== "undefined" ? performance.now() : Date.now());

/** Try to read modern NavigationTiming first, fallback to legacy */
function readNavigationTimings(): { ttfb?: number; loadTime?: number } {
  if (typeof performance === "undefined") return {};
  const nav = performance.getEntriesByType?.("navigation")?.[0] as PerformanceNavigationTiming | undefined;
  if (nav) {
    // All values are relative to startTime (typically 0)
    return {
      ttfb: nav.responseStart, // ms
      loadTime: nav.loadEventEnd - nav.startTime, // ms
    };
  }
  // Legacy fallback
  const t = (performance as unknown).timing;
  if (t) {
    return {
      ttfb: t.responseStart - t.navigationStart,
      loadTime: t.loadEventEnd - t.navigationStart,
    };
  }
  return {};
}

/** Best-effort bundle size estimation: sum transferSize of JS resources */
function estimateBundleSize(): number | undefined {
  if (typeof performance === "undefined" || !performance.getEntriesByType) return undefined;
  try {
    const resources = performance.getEntriesByType("resource") as (PerformanceResourceTiming & { transferSize?: number })[];
    const jsBytes = resources
      .filter((r) => r.initiatorType === "script")
      .map((r) => (typeof r.transferSize === "number" && r.transferSize > 0 ? r.transferSize : 0))
      .reduce((a, b) => a + b, 0);
    return jsBytes || undefined;
  } catch {
    return undefined;
  }
}

export function PerformanceMonitor({
  showOverlay = process.env.NODE_ENV === "development",
  logMetrics = process.env.NODE_ENV === "development",
  onMetricsCollected,
  sendToAnalytics = process.env.NODE_ENV === "production",
  analyticsEndpoint = "/api/analytics/performance",
}: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({});
  const [isVisible, setIsVisible] = useState(false);

  // Observers refs to disconnect on unmount
  const lcpObserverRef = useRef<PerformanceObserver | null>(null);
  const fidObserverRef = useRef<PerformanceObserver | null>(null);
  const clsObserverRef = useRef<PerformanceObserver | null>(null);
  const paintObserverRef = useRef<PerformanceObserver | null>(null);

  // Collect Core Web Vitals + timings
  const collectWebVitals = useCallback(() => {
    if (typeof window === "undefined") return;

    // ----- LCP -----
    try {
      if ("PerformanceObserver" in window) {
        const lcpObs = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const last = entries[entries.length - 1] as unknown;
          if (last) {
            setMetrics((prev) => ({ ...prev, lcp: last.startTime })); // ms
          }
        });
        lcpObs.observe({ type: "largest-contentful-paint", buffered: true } as unknown);
        lcpObserverRef.current = lcpObs;
      }
    } catch {
      // ignore
    }

    // ----- FID -----
    try {
      if ("PerformanceObserver" in window) {
        const fidObs = new PerformanceObserver((list) => {
          const entries = list.getEntries() as unknown[];
          for (const entry of entries) {
            if (entry.processingStart && entry.startTime) {
              const fid = entry.processingStart - entry.startTime; // ms
              setMetrics((prev) => ({ ...prev, fid }));
            }
          }
        });
        fidObs.observe({ type: "first-input", buffered: true } as unknown);
        fidObserverRef.current = fidObs;
      }
    } catch {
      // ignore
    }

    // ----- CLS -----
    try {
      if ("PerformanceObserver" in window) {
        let clsValue = 0;
        const clsObs = new PerformanceObserver((list) => {
          const entries = list.getEntries() as unknown[];
          for (const e of entries) {
            if (!e.hadRecentInput) clsValue += e.value;
          }
          setMetrics((prev) => ({ ...prev, cls: clsValue }));
        });
        clsObs.observe({ type: "layout-shift", buffered: true } as unknown);
        clsObserverRef.current = clsObs;
      }
    } catch {
      // ignore
    }

    // ----- Paint: FCP -----
    try {
      if ("PerformanceObserver" in window) {
        const paintObs = new PerformanceObserver((list) => {
          const entries = list.getEntries() as unknown[];
          for (const e of entries) {
            if (e.name === "first-contentful-paint") {
              setMetrics((prev) => ({ ...prev, fcp: e.startTime })); // ms
            }
          }
        });
        paintObs.observe({ type: "paint", buffered: true } as unknown);
        paintObserverRef.current = paintObs;
      }
    } catch {
      // ignore
    }

    // ----- Navigation Timing -----
    const nav = readNavigationTimings();
    setMetrics((prev) => ({ ...prev, ...nav }));

    // ----- Memory usage -----
    try {
      if ("memory" in performance) {
        const memory = (performance as unknown).memory;
        setMetrics((prev) => ({
          ...prev,
          usedJSHeapSize: memory?.usedJSHeapSize,
          totalJSHeapSize: memory?.totalJSHeapSize,
          jsHeapSizeLimit: memory?.jsHeapSizeLimit,
        }));
      }
    } catch {
      // ignore
    }

    // ----- Bundle size (best effort) -----
    const size = estimateBundleSize();
    if (typeof size === "number") {
      setMetrics((prev) => ({ ...prev, bundleSize: size }));
    }
  }, []);

  // Send metrics to analytics
  const sendMetrics = useCallback(
    async (metricsData: PerformanceMetrics) => {
      if (!sendToAnalytics || !analyticsEndpoint) return;
      try {
        await fetch(analyticsEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            metrics: metricsData,
            timestamp: Date.now(),
            userAgent: typeof navigator !== "undefined" ? navigator.userAgent : "unknown",
            url: typeof window !== "undefined" ? window.location.href : "unknown",
          }),
        });
      } catch {
        // intentionally silent; no UX disruption for telemetry issues
      }
    },
    [sendToAnalytics, analyticsEndpoint]
  );

  // Initialize + periodic re-collect
  useEffect(() => {
    collectWebVitals();
    const timer = window.setTimeout(() => collectWebVitals(), 2000);
    return () => {
      window.clearTimeout(timer);
    };
  }, [collectWebVitals]);

  // Cleanup observers on unmount
  useEffect(() => {
    return () => {
      lcpObserverRef.current?.disconnect();
      fidObserverRef.current?.disconnect();
      clsObserverRef.current?.disconnect();
      paintObserverRef.current?.disconnect();
    };
  }, []);

  // Handle metric updates
  useEffect(() => {
    if (Object.keys(metrics).length === 0) return;
    if (logMetrics) {
      // group for compact dev inspection
      // eslint-disable-next-line no-console
      console.group("🚀 Performance Metrics");
      // eslint-disable-next-line no-console
      console.table(metrics);
      // eslint-disable-next-line no-console
      console.groupEnd();
    }
    onMetricsCollected?.(metrics);
    void sendMetrics(metrics);
  }, [metrics, logMetrics, onMetricsCollected, sendMetrics]);

  // ---- UI helpers ----
  const formatMetric = (value: number | undefined, unit: "ms" | "MB" | "" = "ms") => {
    if (value === undefined || Number.isNaN(value)) return "N/A";
    if (unit === "ms") return `${Math.round(value)}ms`;
    if (unit === "MB") return `${(value / 1024 / 1024).toFixed(1)}MB`;
    return value.toFixed(3);
  };

  const getMetricStatus = (metric: keyof PerformanceMetrics, value: number | undefined) => {
    if (value === undefined) return "unknown";
    switch (metric) {
      case "lcp":
        return value <= 2500 ? "good" : value <= 4000 ? "needs-improvement" : "poor";
      case "fid":
        return value <= 100 ? "good" : value <= 300 ? "needs-improvement" : "poor";
      case "cls":
        return value <= 0.1 ? "good" : value <= 0.25 ? "needs-improvement" : "poor";
      case "fcp":
        return value <= 1800 ? "good" : value <= 3000 ? "needs-improvement" : "poor";
      case "ttfb":
        return value <= 800 ? "good" : value <= 1800 ? "needs-improvement" : "poor";
      default:
        return "unknown";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "good":
        return "text-green-600";
      case "needs-improvement":
        return "text-yellow-600";
      case "poor":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  if (!showOverlay) return null;

  return (
    <>
      {/* Toggle button */}
      <Button
        onClick={() => setIsVisible((v) => !v)}
        className="fixed bottom-4 right-4 z-[9999] rounded-full shadow-lg px-3 py-2"
        title="Toggle Performance Monitor"
        aria-pressed={isVisible}
        variant="default"
      >
        <Activity className="h-4 w-4" />
      </Button>

      {/* Performance overlay */}
      {isVisible && (
        <div className="fixed bottom-16 right-4 z-[9999] bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg shadow-xl p-4 max-w-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-sm flex items-center">
              <Zap className="h-4 w-4 mr-2" />
              Performance Monitor
            </h3>
            <button
              onClick={() => setIsVisible(false)}
              className="text-neutral-400 hover:text-neutral-600"
              aria-label="Close performance monitor"
              title="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-2 text-xs">
            {/* Core Web Vitals */}
            <div className="border-b border-neutral-200 dark:border-neutral-700 pb-2">
              <h4 className="font-medium mb-1">Core Web Vitals</h4>
              <div className="flex justify-between">
                <span>LCP:</span>
                <span className={getStatusColor(getMetricStatus("lcp", metrics.lcp))}>
                  {formatMetric(metrics.lcp)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>FID:</span>
                <span className={getStatusColor(getMetricStatus("fid", metrics.fid))}>
                  {formatMetric(metrics.fid)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>CLS:</span>
                <span className={getStatusColor(getMetricStatus("cls", metrics.cls))}>
                  {formatMetric(metrics.cls, "")}
                </span>
              </div>
            </div>

            {/* Loading metrics */}
            <div className="border-b border-neutral-200 dark:border-neutral-700 pb-2">
              <h4 className="font-medium mb-1">Loading</h4>
              <div className="flex justify-between">
                <span>FCP:</span>
                <span className={getStatusColor(getMetricStatus("fcp", metrics.fcp))}>
                  {formatMetric(metrics.fcp)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>TTFB:</span>
                <span className={getStatusColor(getMetricStatus("ttfb", metrics.ttfb))}>
                  {formatMetric(metrics.ttfb)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Load:</span>
                <span>{formatMetric(metrics.loadTime)}</span>
              </div>
            </div>

            {/* Bundle size (best effort) */}
            {typeof metrics.bundleSize === "number" && (
              <div className="border-b border-neutral-200 dark:border-neutral-700 pb-2">
                <h4 className="font-medium mb-1">Bundle</h4>
                <div className="flex justify-between">
                  <span>JS Transfer:</span>
                  <span>{(metrics.bundleSize / 1024).toFixed(0)} KB</span>
                </div>
              </div>
            )}

            {/* Memory usage */}
            {typeof metrics.usedJSHeapSize === "number" && (
              <div>
                <h4 className="font-medium mb-1">Memory</h4>
                <div className="flex justify-between">
                  <span>Used:</span>
                  <span>{formatMetric(metrics.usedJSHeapSize, "MB")}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total:</span>
                  <span>{formatMetric(metrics.totalJSHeapSize, "MB")}</span>
                </div>
                <div className="flex justify-between">
                  <span>Limit:</span>
                  <span>{formatMetric(metrics.jsHeapSizeLimit, "MB")}</span>
                </div>
              </div>
            )}
          </div>

          {/* Status indicator */}
          <div className="mt-3 pt-2 border-t border-neutral-200 dark:border-neutral-700">
            <div className="flex items-center text-xs">
              {Object.values(metrics).some((v) => v !== undefined) ? (
                <>
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2" />
                  <span>Monitoring active</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2" />
                  <span>Collecting metrics…</span>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Hook for using performance metrics in components (lightweight sampling)
export function usePerformanceMetrics() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({});

  useEffect(() => {
    if (typeof window === "undefined") return;

    const collect = () => {
      const out: PerformanceMetrics = {};
      const nav = readNavigationTimings();
      out.ttfb = nav.ttfb;
      out.loadTime = nav.loadTime;

      // Memory usage
      try {
        if ("memory" in performance) {
          const memory = (performance as unknown).memory;
          out.usedJSHeapSize = memory?.usedJSHeapSize;
          out.totalJSHeapSize = memory?.totalJSHeapSize;
          out.jsHeapSizeLimit = memory?.jsHeapSizeLimit;
        }
      } catch {
        // ignore
      }

      setMetrics(out);
    };

    collect();
    const timer = window.setTimeout(collect, 2000);
    return () => window.clearTimeout(timer);
  }, []);

  return metrics;
}

export default PerformanceMonitor;
