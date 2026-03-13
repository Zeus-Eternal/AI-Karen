/**
 * Performance Monitoring System
 *
 * Tracks Core Web Vitals, custom metrics, and performance events
 * for production optimization and user experience monitoring.
 */

import { onCLS, onINP, onFCP, onLCP, onTTFB } from 'web-vitals';

// Performance metric types
export interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta?: number;
  id: string;
  timestamp: number;
  navigationType?: string;
}

export interface CustomMetric {
  name: string;
  value: number;
  unit: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

export interface PerformanceReport {
  timestamp: number;
  url: string;
  userAgent: string;
  connection: string;
  coreWebVitals: PerformanceMetric[];
  customMetrics: CustomMetric[];
  resourceTiming: PerformanceResourceTiming[];
  navigationTiming: PerformanceNavigationTiming;
}

// Performance thresholds based on Web Vitals standards
const THRESHOLDS = {
  CLS: { good: 0.1, poor: 0.25 },
  FID: { good: 100, poor: 300 },
  FCP: { good: 1800, poor: 3000 },
  LCP: { good: 2500, poor: 4000 },
  TTFB: { good: 800, poor: 1800 },
};

// Performance monitoring class
class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private customMetrics: CustomMetric[] = [];
  private observers: PerformanceObserver[] = [];
  private isMonitoring = false;
  private reportEndpoint?: string;

  constructor(reportEndpoint?: string) {
    this.reportEndpoint = reportEndpoint;
  }

  // Start monitoring performance
  start() {
    if (this.isMonitoring || typeof window === 'undefined') return;

    this.isMonitoring = true;
    if (process.env.NODE_ENV === 'development') {
      console.log('🔍 Performance monitoring started');
    }

    // Monitor Core Web Vitals
    this.monitorCoreWebVitals();

    // Monitor custom metrics
    this.monitorResourceTiming();
    this.monitorNavigationTiming();
    this.monitorLongTasks();
    this.monitorMemoryUsage();

    // Setup page visibility change tracking
    this.trackPageVisibility();

    // Setup error tracking
    this.trackPerformanceErrors();
  }

  // Stop monitoring and generate report
  stop(): PerformanceReport {
    if (!this.isMonitoring) return {} as PerformanceReport;

    this.isMonitoring = false;
    this.disconnectObservers();

    const report = this.generateReport();
    
    if (this.reportEndpoint) {
      this.sendReport(report);
    }

    return report;
  }

  // Monitor Core Web Vitals
  private monitorCoreWebVitals() {
    const handleMetric = (metric: any) => {
      const rating = this.getRating(metric.name, metric.value);
      const performanceMetric: PerformanceMetric = {
        name: metric.name,
        value: metric.value,
        rating,
        delta: metric.delta,
        id: metric.id,
        timestamp: Date.now(),
        navigationType: this.getNavigationType(),
      };

      this.metrics.push(performanceMetric);
      if (process.env.NODE_ENV === 'development') {
        console.log(`📊 ${metric.name}: ${metric.value} (${rating})`);
      }
    };

    onCLS(handleMetric);
    onINP(handleMetric);
    onFCP(handleMetric);
    onLCP(handleMetric);
    onTTFB(handleMetric);
  }

  // Monitor resource loading performance
  private monitorResourceTiming() {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.entryType === 'resource') {
            const resource = entry as PerformanceResourceTiming;
            
            // Track slow resources
            if (resource.duration > 1000) {
              if (process.env.NODE_ENV === 'development') {
                console.warn(`⚠️ Slow resource detected: ${resource.name} (${resource.duration}ms)`);
              }
            }

            // Track failed resources
            if ((resource as any).transferSize === 0 && resource.name.startsWith('http')) {
              if (process.env.NODE_ENV === 'development') {
                console.error(`❌ Failed resource: ${resource.name}`);
              }
            }
          }
        });
      });

      observer.observe({ entryTypes: ['resource'] });
      this.observers.push(observer);
    } catch (error) {
      console.warn('Resource timing monitoring not supported:', error);
    }
  }

  // Monitor navigation timing
  private monitorNavigationTiming() {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.entryType === 'navigation') {
            const nav = entry as PerformanceNavigationTiming;
            
            // Track key navigation metrics
            this.addCustomMetric('dom-interactive', nav.domInteractive, 'ms');
            this.addCustomMetric('dom-complete', nav.domComplete, 'ms');
            this.addCustomMetric('load-event', nav.loadEventEnd - nav.loadEventStart, 'ms');
            
            if (process.env.NODE_ENV === 'development') {
              console.log(`🚀 Page loaded in ${nav.loadEventEnd - nav.fetchStart}ms`);
            }
          }
        });
      });

      observer.observe({ entryTypes: ['navigation'] });
      this.observers.push(observer);
    } catch (error) {
      console.warn('Navigation timing monitoring not supported:', error);
    }
  }

  // Monitor long tasks that block the main thread
  private monitorLongTasks() {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.entryType === 'longtask') {
            this.addCustomMetric('long-task', entry.duration, 'ms', {
              startTime: entry.startTime,
              name: entry.name,
            });
            
            if (entry.duration > 100) {
              if (process.env.NODE_ENV === 'development') {
                console.warn(`⚠️ Long task detected: ${entry.duration}ms`);
              }
            }
          }
        });
      });

      observer.observe({ entryTypes: ['longtask'] });
      this.observers.push(observer);
    } catch (error) {
      console.warn('Long task monitoring not supported:', error);
    }
  }

  // Monitor memory usage (Chrome only)
  private monitorMemoryUsage() {
    if ('memory' in performance) {
      const checkMemory = () => {
        const memory = (performance as any).memory;
        this.addCustomMetric('memory-used', memory.usedJSHeapSize, 'bytes');
        this.addCustomMetric('memory-total', memory.totalJSHeapSize, 'bytes');
        this.addCustomMetric('memory-limit', memory.jsHeapSizeLimit, 'bytes');
      };

      // Check memory every 5 seconds
      const interval = setInterval(checkMemory, 5000);
      
      // Store interval ID for cleanup
      (window as any).__memoryInterval = interval;
    }
  }

  // Track page visibility changes
  private trackPageVisibility() {
    let visibilityStartTime = Date.now();
    
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        const timeOnPage = Date.now() - visibilityStartTime;
        this.addCustomMetric('time-on-page', timeOnPage, 'ms');
      } else if (document.visibilityState === 'visible') {
        visibilityStartTime = Date.now();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
  }

  // Track performance-related errors
  private trackPerformanceErrors() {
    window.addEventListener('error', (event) => {
      if (event.filename && event.filename.includes('.js')) {
        this.addCustomMetric('javascript-error', 1, 'count', {
          message: event.message,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        });
      }
    });

    window.addEventListener('unhandledrejection', (event) => {
      this.addCustomMetric('unhandled-promise-rejection', 1, 'count', {
        reason: event.reason,
      });
    });
  }

  // Add custom metric
  addCustomMetric(name: string, value: number, unit: string, metadata?: Record<string, any>) {
    const metric: CustomMetric = {
      name,
      value,
      unit,
      timestamp: Date.now(),
      metadata,
    };

    this.customMetrics.push(metric);
  }

  // Get rating for metric based on thresholds
  private getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
    const threshold = THRESHOLDS[name as keyof typeof THRESHOLDS];
    if (!threshold) return 'good';

    if (value <= threshold.good) return 'good';
    if (value <= threshold.poor) return 'needs-improvement';
    return 'poor';
  }

  // Get navigation type
  private getNavigationType(): string {
    if (typeof window === 'undefined' || !window.performance) return 'unknown';
    
    const navEntry = window.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (!navEntry) return 'unknown';

    switch (navEntry.type) {
      case 'navigate': return 'navigation';
      case 'reload': return 'reload';
      case 'back_forward': return 'back-forward';
      case 'prerender': return 'prerender';
      default: return 'unknown';
    }
  }

  // Generate performance report
  private generateReport(): PerformanceReport {
    return {
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      connection: this.getConnectionInfo(),
      coreWebVitals: this.metrics,
      customMetrics: this.customMetrics,
      resourceTiming: performance.getEntriesByType('resource') as PerformanceResourceTiming[],
      navigationTiming: performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming,
    };
  }

  // Get connection information
  private getConnectionInfo(): string {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      return `${connection.effectiveType || 'unknown'} (${connection.downlink || 'unknown'}Mbps)`;
    }
    return 'unknown';
  }

  // Send report to endpoint
  private async sendReport(report: PerformanceReport) {
    if (!this.reportEndpoint) return;

    try {
      await fetch(this.reportEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(report),
      });
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to send performance report:', error);
      }
    }
  }

  // Disconnect all observers
  private disconnectObservers() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];

    // Clear memory interval if exists
    if ((window as any).__memoryInterval) {
      clearInterval((window as any).__memoryInterval);
      delete (window as any).__memoryInterval;
    }
  }

  // Get current metrics
  getMetrics(): { coreWebVitals: PerformanceMetric[]; customMetrics: CustomMetric[] } {
    return {
      coreWebVitals: [...this.metrics],
      customMetrics: [...this.customMetrics],
    };
  }

  // Clear all metrics
  clearMetrics() {
    this.metrics = [];
    this.customMetrics = [];
  }
}

// Export the PerformanceMonitor class for external use
export { PerformanceMonitor };

// Singleton instance
let performanceMonitor: PerformanceMonitor | null = null;

// Initialize performance monitoring
export function initPerformanceMonitoring(reportEndpoint?: string): PerformanceMonitor {
  if (!performanceMonitor) {
    performanceMonitor = new PerformanceMonitor(reportEndpoint);
  }
  
  // Start monitoring after page load
  if (document.readyState === 'complete') {
    performanceMonitor!.start();
  } else {
    window.addEventListener('load', () => {
      performanceMonitor!.start();
    });
  }

  return performanceMonitor!;
}

// Get performance monitor instance
export function getPerformanceMonitor(): PerformanceMonitor | null {
  return performanceMonitor;
}

// Export utility functions
export function trackCustomEvent(name: string, value: number, unit: string, metadata?: Record<string, any>) {
  const monitor = getPerformanceMonitor();
  if (monitor) {
    monitor.addCustomMetric(name, value, unit, metadata);
  }
}

export function trackUserInteraction(action: string, element?: string) {
  trackCustomEvent('user-interaction', 1, 'count', {
    action,
    element,
    timestamp: Date.now(),
  });
}

export function trackPageTransition(from: string, to: string) {
  trackCustomEvent('page-transition', 1, 'count', {
    from,
    to,
    timestamp: Date.now(),
  });
}