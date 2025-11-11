export function readNavigationTimings(): { ttfb?: number; loadTime?: number } {
  if (typeof performance === "undefined") return {};
  const nav = performance.getEntriesByType?.("navigation")?.[0] as PerformanceNavigationTiming | undefined;
  if (nav) {
    return {
      ttfb: nav.responseStart,
      loadTime: nav.loadEventEnd - nav.startTime,
    };
  }
  const t = (performance as unknown as { timing?: PerformanceTiming }).timing;
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
