"use client";
import React, { useEffect, useState, useCallback } from "react";
import { AlertTriangle, Activity, Clock, Zap } from "lucide-react";
interface PerformanceMetrics {
  // Core Web Vitals
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  // Other metrics
  fcp?: number; // First Contentful Paint
  ttfb?: number; // Time to First Byte
  // Bundle metrics
  bundleSize?: number;
  loadTime?: number;
  // Memory usage
  usedJSHeapSize?: number;
  totalJSHeapSize?: number;
  jsHeapSizeLimit?: number;
}
interface PerformanceMonitorProps {
  /**
   * Whether to show the performance overlay in development
   */
  showOverlay?: boolean;
  /**
   * Whether to log metrics to console
   */
  logMetrics?: boolean;
  /**
   * Callback when metrics are collected
   */
  onMetricsCollected?: (metrics: PerformanceMetrics) => void;
  /**
   * Whether to send metrics to analytics
   */
  sendToAnalytics?: boolean;
  /**
   * Analytics endpoint URL
   */
  analyticsEndpoint?: string;
}
export function PerformanceMonitor({
  showOverlay = process.env.NODE_ENV === 'development',
  logMetrics = process.env.NODE_ENV === 'development',
  onMetricsCollected,
  sendToAnalytics = process.env.NODE_ENV === 'production',
  analyticsEndpoint = '/api/analytics/performance'
}: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({});
  const [isVisible, setIsVisible] = useState(false);
  // Collect Core Web Vitals
  const collectWebVitals = useCallback(() => {
    if (typeof window === 'undefined') return;
    // Use Web Vitals library if available, otherwise use Performance API
    if ('PerformanceObserver' in window) {
      // Largest Contentful Paint
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1] as any;
          if (lastEntry) {
            setMetrics(prev => ({ ...prev, lcp: lastEntry.startTime }));
          }
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      } catch (e) {
        // LCP not supported
      }
      // First Input Delay
      try {
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            if (entry.processingStart && entry.startTime) {
              const fid = entry.processingStart - entry.startTime;
              setMetrics(prev => ({ ...prev, fid }));
            }
          });
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
      } catch (e) {
        // FID not supported
      }
      // Cumulative Layout Shift
      try {
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });
          setMetrics(prev => ({ ...prev, cls: clsValue }));
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
      } catch (e) {
        // CLS not supported
      }
      // First Contentful Paint
      try {
        const fcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            if (entry.name === 'first-contentful-paint') {
              setMetrics(prev => ({ ...prev, fcp: entry.startTime }));
            }
          });
        });
        fcpObserver.observe({ entryTypes: ['paint'] });
      } catch (e) {
        // FCP not supported
      }
    }
    // Navigation timing
    if ('performance' in window && window.performance.timing) {
      const timing = window.performance.timing;
      const ttfb = timing.responseStart - timing.navigationStart;
      const loadTime = timing.loadEventEnd - timing.navigationStart;
      setMetrics(prev => ({
        ...prev,
        ttfb,
        loadTime
      }));
    }
    // Memory usage
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      setMetrics(prev => ({
        ...prev,
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit
      }));
    }
  }, []);
  // Send metrics to analytics
  const sendMetrics = useCallback(async (metricsData: PerformanceMetrics) => {
    if (!sendToAnalytics || !analyticsEndpoint) return;
    try {
      await fetch(analyticsEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          metrics: metricsData,
          timestamp: Date.now(),
          userAgent: navigator.userAgent,
          url: window.location.href
        })
      });
    } catch (error) {
    }
  }, [sendToAnalytics, analyticsEndpoint]);
  // Initialize performance monitoring
  useEffect(() => {
    collectWebVitals();
    // Collect metrics after page load
    const timer = setTimeout(() => {
      collectWebVitals();
    }, 2000);
    return () => clearTimeout(timer);
  }, [collectWebVitals]);
  // Handle metrics updates
  useEffect(() => {
    if (Object.keys(metrics).length === 0) return;
    if (logMetrics) {
      console.group('🚀 Performance Metrics');
      console.table(metrics);
      console.groupEnd();
    }
    onMetricsCollected?.(metrics);
    sendMetrics(metrics);
  }, [metrics, logMetrics, onMetricsCollected, sendMetrics]);
  // Format metrics for display
  const formatMetric = (value: number | undefined, unit: string = 'ms') => {
    if (value === undefined) return 'N/A';
    if (unit === 'ms') return `${Math.round(value)}ms`;
    if (unit === 'MB') return `${(value / 1024 / 1024).toFixed(1)}MB`;
    return value.toFixed(3);
  };
  // Get metric status (good, needs improvement, poor)
  const getMetricStatus = (metric: keyof PerformanceMetrics, value: number | undefined) => {
    if (value === undefined) return 'unknown';
    switch (metric) {
      case 'lcp':
        return value <= 2500 ? 'good' : value <= 4000 ? 'needs-improvement' : 'poor';
      case 'fid':
        return value <= 100 ? 'good' : value <= 300 ? 'needs-improvement' : 'poor';
      case 'cls':
        return value <= 0.1 ? 'good' : value <= 0.25 ? 'needs-improvement' : 'poor';
      case 'fcp':
        return value <= 1800 ? 'good' : value <= 3000 ? 'needs-improvement' : 'poor';
      case 'ttfb':
        return value <= 800 ? 'good' : value <= 1800 ? 'needs-improvement' : 'poor';
      default:
        return 'unknown';
    }
  };
  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'text-green-600';
      case 'needs-improvement': return 'text-yellow-600';
      case 'poor': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };
  if (!showOverlay) return null;
  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() = aria-label="Button"> setIsVisible(!isVisible)}
        className="fixed bottom-4 right-4 z-50 bg-blue-600 text-white p-2 rounded-full shadow-lg hover:bg-blue-700 transition-colors sm:p-4 md:p-6"
        title="Toggle Performance Monitor"
      >
        <Activity className="h-4 w-4 sm:w-auto md:w-full" />
      </button>
      {/* Performance overlay */}
      {isVisible && (
        <div className="fixed bottom-16 right-4 z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-4 max-w-sm sm:p-4 md:p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-sm flex items-center md:text-base lg:text-lg">
              <Zap className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
              Performance
            </h3>
            <button
              onClick={() = aria-label="Button"> setIsVisible(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          <div className="space-y-2 text-xs sm:text-sm md:text-base">
            {/* Core Web Vitals */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-2">
              <h4 className="font-medium mb-1">Core Web Vitals</h4>
              <div className="flex justify-between">
                <span>LCP:</span>
                <span className={getStatusColor(getMetricStatus('lcp', metrics.lcp))}>
                  {formatMetric(metrics.lcp)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>FID:</span>
                <span className={getStatusColor(getMetricStatus('fid', metrics.fid))}>
                  {formatMetric(metrics.fid)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>CLS:</span>
                <span className={getStatusColor(getMetricStatus('cls', metrics.cls))}>
                  {formatMetric(metrics.cls, '')}
                </span>
              </div>
            </div>
            {/* Other metrics */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-2">
              <h4 className="font-medium mb-1">Loading</h4>
              <div className="flex justify-between">
                <span>FCP:</span>
                <span className={getStatusColor(getMetricStatus('fcp', metrics.fcp))}>
                  {formatMetric(metrics.fcp)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>TTFB:</span>
                <span className={getStatusColor(getMetricStatus('ttfb', metrics.ttfb))}>
                  {formatMetric(metrics.ttfb)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Load:</span>
                <span>{formatMetric(metrics.loadTime)}</span>
              </div>
            </div>
            {/* Memory usage */}
            {metrics.usedJSHeapSize && (
              <div>
                <h4 className="font-medium mb-1">Memory</h4>
                <div className="flex justify-between">
                  <span>Used:</span>
                  <span>{formatMetric(metrics.usedJSHeapSize, 'MB')}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total:</span>
                  <span>{formatMetric(metrics.totalJSHeapSize, 'MB')}</span>
                </div>
                <div className="flex justify-between">
                  <span>Limit:</span>
                  <span>{formatMetric(metrics.jsHeapSizeLimit, 'MB')}</span>
                </div>
              </div>
            )}
          </div>
          {/* Status indicator */}
          <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center text-xs sm:text-sm md:text-base">
              {Object.values(metrics).some(v => v !== undefined) ? (
                <>
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2 sm:w-auto md:w-full"></div>
                  <span>Monitoring active</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2 sm:w-auto md:w-full"></div>
                  <span>Collecting metrics...</span>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
// Hook for using performance metrics in components
export function usePerformanceMetrics() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({});
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const collectMetrics = () => {
      const newMetrics: PerformanceMetrics = {};
      // Navigation timing
      if (window.performance?.timing) {
        const timing = window.performance.timing;
        newMetrics.ttfb = timing.responseStart - timing.navigationStart;
        newMetrics.loadTime = timing.loadEventEnd - timing.navigationStart;
      }
      // Memory usage
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        newMetrics.usedJSHeapSize = memory.usedJSHeapSize;
        newMetrics.totalJSHeapSize = memory.totalJSHeapSize;
        newMetrics.jsHeapSizeLimit = memory.jsHeapSizeLimit;
      }
      setMetrics(newMetrics);
    };
    // Collect initial metrics
    collectMetrics();
    // Collect metrics after load
    const timer = setTimeout(collectMetrics, 2000);
    return () => clearTimeout(timer);
  }, []);
  return metrics;
}
