import { useEffect, useState } from "react";

export interface PerformanceMetrics {
  lcp?: number;
  fid?: number;
  cls?: number;
  fcp?: number;
  ttfb?: number;
  bundleSize?: number;
  loadTime?: number;
  usedJSHeapSize?: number;
  totalJSHeapSize?: number;
  jsHeapSizeLimit?: number;
}

interface PerformanceMemory {
  usedJSHeapSize?: number;
  totalJSHeapSize?: number;
  jsHeapSizeLimit?: number;
}

export interface PerformanceMonitorProps {
  showOverlay?: boolean;
  logMetrics?: boolean;
  onMetricsCollected?: (metrics: PerformanceMetrics) => void;
  sendToAnalytics?: boolean;
  analyticsEndpoint?: string;
}

export function readNavigationTimings(): { ttfb?: number; loadTime?: number } {
  if (typeof performance === "undefined") return {};
  const nav = performance.getEntriesByType?.("navigation")?.[0] as PerformanceNavigationTiming | undefined;
  if (nav) {
    return {
      ttfb: nav.responseStart,
      loadTime: nav.loadEventEnd - nav.startTime,
    };
  }
  const t = (performance as unknown as { timing?: PerformanceTiming | undefined }).timing;
  if (t) {
    return {
      ttfb: t.responseStart - t.navigationStart,
      loadTime: t.loadEventEnd - t.navigationStart,
    };
  }
  return {};
}

export function estimateBundleSize(): number | undefined {
  if (typeof performance === "undefined" || !performance.getEntriesByType) return undefined;
  try {
    const resources = performance.getEntriesByType("resource") as (PerformanceResourceTiming & {
      transferSize?: number;
    })[];
    const jsBytes = resources
      .filter((r) => r.initiatorType === "script")
      .map((r) => (typeof r.transferSize === "number" && r.transferSize > 0 ? r.transferSize : 0))
      .reduce((a, b) => a + b, 0);
    return jsBytes || undefined;
  } catch {
    return undefined;
  }
}

export function usePerformanceMetrics() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({});

  useEffect(() => {
    if (typeof window === "undefined") return;

    const collect = () => {
      const out: PerformanceMetrics = {};
      const nav = readNavigationTimings();
      out.ttfb = nav.ttfb;
      out.loadTime = nav.loadTime;

      try {
        if ("memory" in performance) {
          const memory = (performance as unknown as { memory?: PerformanceMemory }).memory;
          out.usedJSHeapSize = memory?.usedJSHeapSize;
          out.totalJSHeapSize = memory?.totalJSHeapSize;
          out.jsHeapSizeLimit = memory?.jsHeapSizeLimit;
        }
      } catch {
        // ignore failures in restricted environments
      }

      setMetrics(out);
    };

    collect();
    const timer = window.setTimeout(collect, 2000);
    return () => window.clearTimeout(timer);
  }, []);

  return metrics;
}
