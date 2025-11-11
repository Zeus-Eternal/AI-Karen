"use client";

import { useEffect, useState } from "react";

import type { PerformanceMetrics } from "./performance-monitor";
import { readNavigationTimings } from "./performance-utils";

type PerformanceMemory = {
  usedJSHeapSize?: number;
  totalJSHeapSize?: number;
  jsHeapSizeLimit?: number;
};

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
        // ignore memory probe failures
      }

      setMetrics(out);
    };

    collect();
    const timer = window.setTimeout(collect, 2000);
    return () => window.clearTimeout(timer);
  }, []);

  return metrics;
}
