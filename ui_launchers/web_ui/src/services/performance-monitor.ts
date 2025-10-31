/**
 * Comprehensive Performance Monitoring Service
 * Tracks page load times, interaction latency, resource usage, and Web Vitals
 */

import { getCLS, getFCP, getFID, getLCP, getTTFB } from 'web-vitals';

export interface WebVitalsMetrics {
  cls: number;
  fcp: number;
  fid: number;
  lcp: number;
  ttfb: number;
}

export interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

export interface ResourceUsage {
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  cpu?: {
    usage: number;
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
  fid: { warning: number; critical: number };
  cls: { warning: number; critical: number };
  fcp: { warning: number; critical: number };
  ttfb: { warning: number; critical: number };
  pageLoad: { warning: number; critical: number };
  interaction: { warning: number; critical: number };
  memoryUsage: { warning: number; critical: number };
}

export class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private alerts: PerformanceAlert[] = [];
  private observers: PerformanceObserver[] = [];
  private thresholds: PerformanceThresholds;
  private alertCallbacks: ((alert: PerformanceAlert) => void)[] = [];

  constructor(thresholds?: Partial<PerformanceThresholds>) {
    this.thresholds = {
      lcp: { warning: 2500, critical: 4000 },
      fid: { warning: 100, critical: 300 },
      cls: { warning: 0.1, critical: 0.25 },
      fcp: { warning: 1800, critical: 3000 },
      ttfb: { warning: 800, critical: 1800 },
      pageLoad: { warning: 3000, critical: 5000 },
      interaction: { warning: 100, critical: 300 },
      memoryUsage: { warning: 80, critical: 95 },
      ...thresholds,
    };

    this.initializeWebVitalsTracking();
    this.initializeResourceMonitoring();
    this.initializeInteractionTracking();
  }

  /**
   * Initialize Web Vitals tracking
   */
  private initializeWebVitalsTracking(): void {
    getCLS((metric) => {
      this.recordMetric('cls', metric.value, { id: metric.id });
      this.checkThreshold('cls', metric.value);
    });

    getFCP((metric) => {
      this.recordMetric('fcp', metric.value, { id: metric.id });
      this.checkThreshold('fcp', metric.value);
    });

    getFID((metric) => {
      this.recordMetric('fid', metric.value, { id: metric.id });
      this.checkThreshold('fid', metric.value);
    });

    getLCP((metric) => {
      this.recordMetric('lcp', metric.value, { id: metric.id });
      this.checkThreshold('lcp', metric.value);
    });

    getTTFB((metric) => {
      this.recordMetric('ttfb', metric.value, { id: metric.id });
      this.checkThreshold('ttfb', metric.value);
    });
  }

  /**
   * Initialize resource monitoring
   */
  private initializeResourceMonitoring(): void {
    // Monitor memory usage
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        const memoryUsage = {
          used: memory.usedJSHeapSize,
          total: memory.totalJSHeapSize,
          percentage: (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100,
        };

        this.recordMetric('memory-usage', memoryUsage.percentage, {
          used: memoryUsage.used,
          total: memoryUsage.total,
        });

        this.checkThreshold('memoryUsage', memoryUsage.percentage);
      }, 5000);
    }

    // Monitor network information
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      this.recordMetric('network-downlink', connection.downlink, {
        effectiveType: connection.effectiveType,
        rtt: connection.rtt,
      });
    }
  }

  /**
   * Initialize interaction tracking
   */
  private initializeInteractionTracking(): void {
    // Track long tasks
    if ('PerformanceObserver' in window) {
      const longTaskObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.recordMetric('long-task', entry.duration, {
            startTime: entry.startTime,
            name: entry.name,
          });

          if (entry.duration > this.thresholds.interaction.warning) {
            this.createAlert(
              'warning',
              'long-task',
              entry.duration,
              this.thresholds.interaction.warning,
              `Long task detected: ${entry.duration.toFixed(2)}ms`
            );
          }
        }
      });

      try {
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.push(longTaskObserver);
      } catch (error) {
        console.warn('Long task observer not supported:', error);
      }
    }

    // Track navigation timing
    if ('PerformanceObserver' in window) {
      const navigationObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const navEntry = entry as PerformanceNavigationTiming;
          const pageLoadTime = navEntry.loadEventEnd - navEntry.navigationStart;

          this.recordMetric('page-load', pageLoadTime, {
            domContentLoaded: navEntry.domContentLoadedEventEnd - navEntry.navigationStart,
            firstByte: navEntry.responseStart - navEntry.navigationStart,
            domComplete: navEntry.domComplete - navEntry.navigationStart,
          });

          this.checkThreshold('pageLoad', pageLoadTime);
        }
      });

      try {
        navigationObserver.observe({ entryTypes: ['navigation'] });
        this.observers.push(navigationObserver);
      } catch (error) {
        console.warn('Navigation observer not supported:', error);
      }
    }
  }

  /**
   * Track page load time for specific routes
   */
  trackPageLoad(route: string, startTime?: number): void {
    const loadTime = startTime || (performance.now ? performance.now() : Date.now());
    this.recordMetric('route-load', loadTime, { route });
    this.checkThreshold('pageLoad', loadTime);
  }

  /**
   * Track user interaction latency
   */
  trackUserInteraction(action: string, duration: number, metadata?: Record<string, any>): void {
    this.recordMetric('user-interaction', duration, { action, ...metadata });
    this.checkThreshold('interaction', duration);
  }

  /**
   * Track API call performance
   */
  trackAPICall(endpoint: string, duration: number, status: number, metadata?: Record<string, any>): void {
    this.recordMetric('api-call', duration, {
      endpoint,
      status,
      success: status >= 200 && status < 300,
      ...metadata,
    });

    // Alert on slow API calls
    if (duration > 2000) {
      this.createAlert(
        'warning',
        'api-call',
        duration,
        2000,
        `Slow API call to ${endpoint}: ${duration.toFixed(2)}ms`
      );
    }
  }

  /**
   * Get current resource usage
   */
  getCurrentResourceUsage(): ResourceUsage {
    const memory = (performance as any).memory;
    const connection = (navigator as any).connection;

    return {
      memory: memory
        ? {
            used: memory.usedJSHeapSize,
            total: memory.totalJSHeapSize,
            percentage: (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100,
          }
        : { used: 0, total: 0, percentage: 0 },
      network: connection
        ? {
            downlink: connection.downlink,
            effectiveType: connection.effectiveType,
            rtt: connection.rtt,
          }
        : { downlink: 0, effectiveType: 'unknown', rtt: 0 },
    };
  }

  /**
   * Get Web Vitals metrics
   */
  getWebVitalsMetrics(): Partial<WebVitalsMetrics> {
    const vitals: Partial<WebVitalsMetrics> = {};
    const latestMetrics = this.getLatestMetrics(['cls', 'fcp', 'fid', 'lcp', 'ttfb']);

    latestMetrics.forEach((metric) => {
      (vitals as any)[metric.name] = metric.value;
    });

    return vitals;
  }

  /**
   * Get performance metrics by type
   */
  getMetrics(type?: string, limit?: number): PerformanceMetric[] {
    let filtered = type ? this.metrics.filter((m) => m.name === type) : this.metrics;
    
    if (limit) {
      filtered = filtered.slice(-limit);
    }

    return filtered.sort((a, b) => b.timestamp - a.timestamp);
  }

  /**
   * Get latest metrics for specified types
   */
  getLatestMetrics(types: string[]): PerformanceMetric[] {
    return types
      .map((type) => this.metrics.filter((m) => m.name === type).pop())
      .filter(Boolean) as PerformanceMetric[];
  }

  /**
   * Get performance alerts
   */
  getAlerts(limit?: number): PerformanceAlert[] {
    const sorted = this.alerts.sort((a, b) => b.timestamp - a.timestamp);
    return limit ? sorted.slice(0, limit) : sorted;
  }

  /**
   * Subscribe to performance alerts
   */
  onAlert(callback: (alert: PerformanceAlert) => void): () => void {
    this.alertCallbacks.push(callback);
    return () => {
      const index = this.alertCallbacks.indexOf(callback);
      if (index > -1) {
        this.alertCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Get performance recommendations
   */
  getOptimizationRecommendations(): string[] {
    const recommendations: string[] = [];
    const vitals = this.getWebVitalsMetrics();

    if (vitals.lcp && vitals.lcp > this.thresholds.lcp.warning) {
      recommendations.push('Consider optimizing images and reducing server response times to improve LCP');
    }

    if (vitals.fid && vitals.fid > this.thresholds.fid.warning) {
      recommendations.push('Reduce JavaScript execution time and break up long tasks to improve FID');
    }

    if (vitals.cls && vitals.cls > this.thresholds.cls.warning) {
      recommendations.push('Add size attributes to images and avoid inserting content above existing content to improve CLS');
    }

    const memoryMetrics = this.getMetrics('memory-usage', 10);
    const avgMemoryUsage = memoryMetrics.reduce((sum, m) => sum + m.value, 0) / memoryMetrics.length;
    
    if (avgMemoryUsage > this.thresholds.memoryUsage.warning) {
      recommendations.push('Consider implementing memory optimization strategies and garbage collection');
    }

    return recommendations;
  }

  /**
   * Clear old metrics to prevent memory leaks
   */
  clearOldMetrics(maxAge: number = 24 * 60 * 60 * 1000): void {
    const cutoff = Date.now() - maxAge;
    this.metrics = this.metrics.filter((m) => m.timestamp > cutoff);
    this.alerts = this.alerts.filter((a) => a.timestamp > cutoff);
  }

  /**
   * Record a performance metric
   */
  private recordMetric(name: string, value: number, metadata?: Record<string, any>): void {
    this.metrics.push({
      name,
      value,
      timestamp: Date.now(),
      metadata,
    });

    // Prevent memory leaks by limiting metrics
    if (this.metrics.length >= 5000) {
      this.metrics = this.metrics.slice(-2500);
    }
  }

  /**
   * Check if a metric exceeds thresholds and create alerts
   */
  private checkThreshold(metricType: keyof PerformanceThresholds, value: number): void {
    const threshold = this.thresholds[metricType];
    
    if (value > threshold.critical) {
      this.createAlert('critical', metricType, value, threshold.critical, 
        `Critical performance issue: ${metricType} is ${value.toFixed(2)}`);
    } else if (value > threshold.warning) {
      this.createAlert('warning', metricType, value, threshold.warning,
        `Performance warning: ${metricType} is ${value.toFixed(2)}`);
    }
  }

  /**
   * Create a performance alert
   */
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
    this.alertCallbacks.forEach((callback) => callback(alert));

    // Prevent memory leaks
    if (this.alerts.length >= 1000) {
      this.alerts = this.alerts.slice(-500);
    }
  }

  /**
   * Cleanup observers and intervals
   */
  destroy(): void {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers = [];
    this.alertCallbacks = [];
  }
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor();