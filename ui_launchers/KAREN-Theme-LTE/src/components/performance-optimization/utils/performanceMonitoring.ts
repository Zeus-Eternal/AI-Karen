/**
 * Performance Monitoring and Metrics Collection
 * Comprehensive performance monitoring system with metrics collection
 */

'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { PerformanceMetric, PerformanceReport } from '../types';
import { usePerformanceOptimizationStore } from '../store/performanceOptimizationStore';

// Core Web Vitals monitoring
export interface CoreWebVitals {
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  fcp: number; // First Contentful Paint
  ttfb: number; // Time to First Byte
}

// Performance monitoring configuration
interface PerformanceMonitoringConfig {
  enableCoreWebVitals: boolean;
  enableResourceTiming: boolean;
  enableUserTiming: boolean;
  enableLongTaskMonitoring: boolean;
  enableMemoryMonitoring: boolean;
  enableNetworkMonitoring: boolean;
  samplingRate: number; // 0.0 to 1.0
  maxMetrics: number;
  reportInterval: number; // ms
}

// Default configuration
const DEFAULT_CONFIG: PerformanceMonitoringConfig = {
  enableCoreWebVitals: true,
  enableResourceTiming: true,
  enableUserTiming: true,
  enableLongTaskMonitoring: true,
  enableMemoryMonitoring: true,
  enableNetworkMonitoring: true,
  samplingRate: 1.0,
  maxMetrics: 1000,
  reportInterval: 30000, // 30 seconds
};

// Performance monitoring class
class PerformanceMonitor {
  private config: PerformanceMonitoringConfig;
  private observers: Map<string, PerformanceObserver> = new Map();
  private metrics: PerformanceMetric[] = [];
  private coreWebVitals: Partial<CoreWebVitals> = {};
  private isMonitoring = false;
  private reportTimer: NodeJS.Timeout | null = null;
  private onMetricCallback?: (metric: PerformanceMetric) => void;
  private onReportCallback?: (report: PerformanceReport) => void;

  constructor(config: Partial<PerformanceMonitoringConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  // Start performance monitoring
  start(
    onMetric?: (metric: PerformanceMetric) => void,
    onReport?: (report: PerformanceReport) => void
  ): void {
    if (this.isMonitoring) return;

    this.onMetricCallback = onMetric;
    this.onReportCallback = onReport;
    this.isMonitoring = true;

    // Initialize observers based on configuration
    if (this.config.enableCoreWebVitals) {
      this.initializeCoreWebVitalsMonitoring();
    }

    if (this.config.enableResourceTiming) {
      this.initializeResourceTimingMonitoring();
    }

    if (this.config.enableUserTiming) {
      this.initializeUserTimingMonitoring();
    }

    if (this.config.enableLongTaskMonitoring) {
      this.initializeLongTaskMonitoring();
    }

    // Start periodic reporting
    this.startPeriodicReporting();

    // Collect initial metrics
    this.collectInitialMetrics();
  }

  // Stop performance monitoring
  stop(): void {
    if (!this.isMonitoring) return;

    this.isMonitoring = false;

    // Disconnect all observers
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();

    // Clear report timer
    if (this.reportTimer) {
      clearInterval(this.reportTimer);
      this.reportTimer = null;
    }
  }

  // Initialize Core Web Vitals monitoring
  private initializeCoreWebVitalsMonitoring(): void {
    // Largest Contentful Paint (LCP)
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1] as PerformanceEntry & { startTime: number };
          
          if (lastEntry && lastEntry.startTime) {
            const lcp = lastEntry.startTime;
            this.coreWebVitals.lcp = lcp;
            
            this.recordMetric({
              name: 'lcp',
              value: lcp,
              unit: 'ms',
              timestamp: new Date(),
              rating: this.getLcpRating(lcp),
              threshold: { good: 2500, poor: 4000 },
            });
          }
        });
        
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.set('lcp', lcpObserver);
      } catch (e) {
        console.warn('LCP monitoring not supported:', e);
      }

      // First Input Delay (FID)
      try {
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: PerformanceEntry & { processingStart?: number; startTime?: number }) => {
            if (entry.processingStart && entry.startTime) {
              const fid = entry.processingStart - entry.startTime;
              this.coreWebVitals.fid = fid;
              
              this.recordMetric({
                name: 'fid',
                value: fid,
                unit: 'ms',
                timestamp: new Date(),
                rating: this.getFidRating(fid),
                threshold: { good: 100, poor: 300 },
              });
            }
          });
        });
        
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.set('fid', fidObserver);
      } catch (e) {
        console.warn('FID monitoring not supported:', e);
      }

      // Cumulative Layout Shift (CLS)
      try {
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: PerformanceEntry & { value?: number; hadRecentInput?: boolean }) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value || 0;
              this.coreWebVitals.cls = clsValue;
              
              this.recordMetric({
                name: 'cls',
                value: clsValue,
                unit: 'score',
                timestamp: new Date(),
                rating: this.getClsRating(clsValue),
                threshold: { good: 0.1, poor: 0.25 },
              });
            }
          });
        });
        
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.set('cls', clsObserver);
      } catch (e) {
        console.warn('CLS monitoring not supported:', e);
      }

      // First Contentful Paint (FCP) and Time to First Byte (TTFB)
      try {
        const paintObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: PerformanceEntry & { name?: string; startTime?: number }) => {
            if (entry.name === 'first-contentful-paint') {
              const fcp = entry.startTime || 0;
              this.coreWebVitals.fcp = fcp;
              
              this.recordMetric({
                name: 'fcp',
                value: fcp,
                unit: 'ms',
                timestamp: new Date(),
                rating: this.getFcpRating(fcp),
                threshold: { good: 1800, poor: 3000 },
              });
            }
          });
        });
        
        paintObserver.observe({ entryTypes: ['paint'] });
        this.observers.set('paint', paintObserver);
      } catch (e) {
        console.warn('Paint timing not supported:', e);
      }
    }
  }

  // Initialize Resource Timing monitoring
  private initializeResourceTimingMonitoring(): void {
    if ('PerformanceObserver' in window) {
      try {
        const resourceObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: PerformanceEntry & { duration?: number; name?: string; transferSize?: number }) => {
            if (entry.duration) {
              this.recordMetric({
                name: 'resource-load',
                value: entry.duration,
                unit: 'ms',
                timestamp: new Date(),
                rating: this.getResourceRating(entry.duration),
                threshold: { good: 100, poor: 500 },
                metadata: {
                  name: entry.name,
                  type: this.getResourceType(entry.name),
                  size: entry.transferSize || 0,
                },
              });
            }
          });
        });
        
        resourceObserver.observe({ entryTypes: ['resource'] });
        this.observers.set('resource', resourceObserver);
      } catch (e) {
        console.warn('Resource timing not supported:', e);
      }
    }
  }

  // Initialize User Timing monitoring
  private initializeUserTimingMonitoring(): void {
    if ('PerformanceObserver' in window) {
      try {
        const userTimingObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: PerformanceEntry & { duration?: number; name?: string; startTime?: number }) => {
            if (entry.duration) {
              this.recordMetric({
                name: `user-timing-${entry.name}`,
                value: entry.duration,
                unit: 'ms',
                timestamp: new Date(),
                rating: this.getUserTimingRating(entry.duration),
                threshold: { good: 50, poor: 200 },
                metadata: {
                  name: entry.name,
                  startTime: entry.startTime,
                },
              });
            }
          });
        });
        
        userTimingObserver.observe({ entryTypes: ['measure'] });
        this.observers.set('user-timing', userTimingObserver);
      } catch (e) {
        console.warn('User timing not supported:', e);
      }
    }
  }

  // Initialize Long Task monitoring
  private initializeLongTaskMonitoring(): void {
    if ('PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: PerformanceEntry & { duration?: number; startTime?: number; attribution?: unknown }) => {
            if (entry.duration) {
              this.recordMetric({
                name: 'long-task',
                value: entry.duration,
                unit: 'ms',
                timestamp: new Date(),
                rating: this.getLongTaskRating(entry.duration),
                threshold: { good: 50, poor: 100 },
                metadata: {
                  startTime: entry.startTime,
                  attribution: entry.attribution,
                },
              });
            }
          });
        });
        
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.set('long-task', longTaskObserver);
      } catch (e) {
        console.warn('Long task monitoring not supported:', e);
      }
    }
  }

  // Collect initial metrics
  private collectInitialMetrics(): void {
    // Navigation timing
    if ('performance' in window && 'getEntriesByType' in performance) {
      const navigationEntries = performance.getEntriesByType('navigation');
      if (navigationEntries.length > 0) {
        const nav = navigationEntries[0] as PerformanceNavigationTiming;
        
        // Time to First Byte (TTFB)
        if (nav.responseStart && nav.requestStart) {
          const ttfb = nav.responseStart - nav.requestStart;
          this.coreWebVitals.ttfb = ttfb;
          
          this.recordMetric({
            name: 'ttfb',
            value: ttfb,
            unit: 'ms',
            timestamp: new Date(),
            rating: this.getTtfbRating(ttfb),
            threshold: { good: 800, poor: 1800 },
          });
        }

        // Page load time
        if (nav.loadEventEnd && nav.requestStart) {
          const loadTime = nav.loadEventEnd - nav.requestStart;
          
          this.recordMetric({
            name: 'page-load-time',
            value: loadTime,
            unit: 'ms',
            timestamp: new Date(),
            rating: this.getPageLoadRating(loadTime),
            threshold: { good: 2000, poor: 4000 },
          });
        }
      }
    }

    // Memory usage
    if (this.config.enableMemoryMonitoring && 'memory' in performance) {
      const memory = (performance as Performance & { memory?: { usedJSHeapSize: number; totalJSHeapSize: number; jsHeapSizeLimit: number } }).memory;
      if (memory) {
        this.recordMetric({
          name: 'memory-usage',
          value: Math.round(memory.usedJSHeapSize / 1048576), // Convert to MB
          unit: 'MB',
          timestamp: new Date(),
          rating: this.getMemoryRating(memory.usedJSHeapSize),
          threshold: { good: 50 * 1048576, poor: 100 * 1048576 },
          metadata: {
            total: Math.round(memory.totalJSHeapSize / 1048576),
            limit: Math.round(memory.jsHeapSizeLimit / 1048576),
          },
        });
      }
    }
  }

  // Start periodic reporting
  private startPeriodicReporting(): void {
    this.reportTimer = setInterval(() => {
      this.generateReport();
    }, this.config.reportInterval);
  }

  // Record a metric
  private recordMetric(metric: PerformanceMetric): void {
    // Apply sampling
    if (Math.random() > this.config.samplingRate) {
      return;
    }

    // Add to metrics array
    this.metrics.push(metric);

    // Trim if exceeding max metrics
    if (this.metrics.length > this.config.maxMetrics) {
      this.metrics = this.metrics.slice(-this.config.maxMetrics);
    }

    // Store in global state
    const store = usePerformanceOptimizationStore.getState();
    store.measureMetric(metric);

    // Call callback if provided
    if (this.onMetricCallback) {
      this.onMetricCallback(metric);
    }
  }

  // Generate performance report
  private generateReport(): void {
    const report: PerformanceReport = {
      id: `report-${Date.now()}`,
      timestamp: new Date(),
      metrics: [...this.metrics],
      budgets: {}, // Would be populated from store
      alerts: [], // Would be populated from store
      cacheStats: {
        size: 0,
        entries: 0,
        hitRate: 0,
        missRate: 0,
      },
      deviceProfile: {
        type: 'desktop', // Would be detected
        os: '',
        browser: '',
        connectionType: 'wifi',
        memory: 0,
        cpuCores: 0,
        screenResolution: { width: 0, height: 0 },
        pixelRatio: 1,
        capabilities: {
          webp: false,
          avif: false,
          wasm: false,
          webgl: false,
          webgl2: false,
          serviceWorker: false,
          pushNotifications: false,
          bluetooth: false,
          geolocation: false,
          camera: false,
          microphone: false,
          touchEvents: false,
          pointerEvents: false,
          deviceMemory: false,
          connectionApi: false,
          batteryApi: false,
          performanceTimeline: false,
          userActivation: false,
        },
      },
      recommendations: this.generateRecommendations(),
      score: this.calculatePerformanceScore(),
    };

    // Call callback if provided
    if (this.onReportCallback) {
      this.onReportCallback(report);
    }
  }

  // Calculate performance score
  private calculatePerformanceScore(): number {
    if (this.metrics.length === 0) return 0;

    const recentMetrics = this.metrics.slice(-20); // Last 20 metrics
    let totalScore = 0;
    let metricCount = 0;

    recentMetrics.forEach((metric) => {
      let score = 0;
      switch (metric.rating) {
        case 'good':
          score = 100;
          break;
        case 'needs-improvement':
          score = 50;
          break;
        case 'poor':
          score = 0;
          break;
      }
      totalScore += score;
      metricCount++;
    });

    return Math.round(totalScore / metricCount);
  }

  // Generate recommendations
  private generateRecommendations(): string[] {
    const recommendations: string[] = [];

    // Analyze Core Web Vitals
    if (this.coreWebVitals.lcp && this.coreWebVitals.lcp > 4000) {
      recommendations.push('Optimize Largest Contentful Paint by reducing server response time and optimizing images');
    }

    if (this.coreWebVitals.fid && this.coreWebVitals.fid > 300) {
      recommendations.push('Reduce First Input Delay by minimizing JavaScript execution time and breaking up long tasks');
    }

    if (this.coreWebVitals.cls && this.coreWebVitals.cls > 0.25) {
      recommendations.push('Reduce Cumulative Layout Shift by ensuring proper dimensions for images and ads');
    }

    // Analyze other metrics
    const resourceMetrics = this.metrics.filter(m => m.name === 'resource-load');
    if (resourceMetrics.length > 0) {
      const avgResourceTime = resourceMetrics.reduce((sum, m) => sum + m.value, 0) / resourceMetrics.length;
      if (avgResourceTime > 500) {
        recommendations.push('Optimize resource loading by implementing better caching and compression');
      }
    }

    return recommendations;
  }

  // Rating helper methods
  private getLcpRating(value: number): 'good' | 'needs-improvement' | 'poor' {
    return value < 2500 ? 'good' : value < 4000 ? 'needs-improvement' : 'poor';
  }

  private getFidRating(value: number): 'good' | 'needs-improvement' | 'poor' {
    return value < 100 ? 'good' : value < 300 ? 'needs-improvement' : 'poor';
  }

  private getClsRating(value: number): 'good' | 'needs-improvement' | 'poor' {
    return value < 0.1 ? 'good' : value < 0.25 ? 'needs-improvement' : 'poor';
  }

  private getFcpRating(value: number): 'good' | 'needs-improvement' | 'poor' {
    return value < 1800 ? 'good' : value < 3000 ? 'needs-improvement' : 'poor';
  }

  private getTtfbRating(value: number): 'good' | 'needs-improvement' | 'poor' {
    return value < 800 ? 'good' : value < 1800 ? 'needs-improvement' : 'poor';
  }

  private getPageLoadRating(value: number): 'good' | 'needs-improvement' | 'poor' {
    return value < 2000 ? 'good' : value < 4000 ? 'needs-improvement' : 'poor';
  }

  private getResourceRating(value: number): 'good' | 'needs-improvement' | 'poor' {
    return value < 100 ? 'good' : value < 500 ? 'needs-improvement' : 'poor';
  }

  private getUserTimingRating(value: number): 'good' | 'needs-improvement' | 'poor' {
    return value < 50 ? 'good' : value < 200 ? 'needs-improvement' : 'poor';
  }

  private getLongTaskRating(value: number): 'good' | 'needs-improvement' | 'poor' {
    return value < 50 ? 'good' : value < 100 ? 'needs-improvement' : 'poor';
  }

  private getMemoryRating(value: number): 'good' | 'needs-improvement' | 'poor' {
    return value < 50 * 1048576 ? 'good' : value < 100 * 1048576 ? 'needs-improvement' : 'poor';
  }

  private getResourceType(url: string): string {
    if (url.includes('.js')) return 'script';
    if (url.includes('.css')) return 'stylesheet';
    if (url.match(/\.(jpg|jpeg|png|gif|webp|avif)$/i)) return 'image';
    if (url.match(/\.(woff|woff2|ttf|eot)$/i)) return 'font';
    return 'other';
  }

  // Public methods
  public getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  public getCoreWebVitals(): Partial<CoreWebVitals> {
    return { ...this.coreWebVitals };
  }

  public clearMetrics(): void {
    this.metrics = [];
  }

  public updateConfig(config: Partial<PerformanceMonitoringConfig>): void {
    this.config = { ...this.config, ...config };
    
    // Restart monitoring if it was already running
    if (this.isMonitoring) {
      this.stop();
      this.start(this.onMetricCallback, this.onReportCallback);
    }
  }
}

// Hook for performance monitoring
export function usePerformanceMonitoring(config?: Partial<PerformanceMonitoringConfig>) {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [coreWebVitals, setCoreWebVitals] = useState<Partial<CoreWebVitals>>({});
  const [reports, setReports] = useState<PerformanceReport[]>([]);
  const monitorRef = useRef<PerformanceMonitor | null>(null);

  useEffect(() => {
    // Initialize monitor
    monitorRef.current = new PerformanceMonitor(config);

    return () => {
      // Cleanup on unmount
      if (monitorRef.current) {
        monitorRef.current.stop();
      }
    };
  }, [config]);

  const startMonitoring = useCallback(() => {
    if (!monitorRef.current) return;

    monitorRef.current.start(
      (metric) => {
        setMetrics(prev => [...prev, metric]);
      },
      (report) => {
        setReports(prev => [...prev, report]);
      }
    );

    setIsMonitoring(true);
  }, []);

  const stopMonitoring = useCallback(() => {
    if (!monitorRef.current) return;

    monitorRef.current.stop();
    setIsMonitoring(false);
  }, []);

  const getLatestCoreWebVitals = useCallback(() => {
    if (!monitorRef.current) return {};
    
    return monitorRef.current.getCoreWebVitals();
  }, []);

  const clearMetrics = useCallback(() => {
    if (!monitorRef.current) return;

    monitorRef.current.clearMetrics();
    setMetrics([]);
  }, []);

  const updateConfig = useCallback((newConfig: Partial<PerformanceMonitoringConfig>) => {
    if (!monitorRef.current) return;

    monitorRef.current.updateConfig(newConfig);
  }, []);

  // Update core web vitals when metrics change
  useEffect(() => {
    setCoreWebVitals(getLatestCoreWebVitals());
  }, [metrics, getLatestCoreWebVitals]);

  return {
    isMonitoring,
    metrics,
    coreWebVitals,
    reports,
    startMonitoring,
    stopMonitoring,
    clearMetrics,
    updateConfig,
    getLatestCoreWebVitals,
  };
}

// Custom performance mark and measure utilities
export function markPerformance(name: string): void {
  if ('performance' in window && 'mark' in performance) {
    performance.mark(name);
  }
}

export function measurePerformance(
  name: string,
  startMark?: string,
  endMark?: string
): number | null {
  if ('performance' in window && 'measure' in performance) {
    try {
      performance.measure(name, startMark, endMark);
      const measures = performance.getEntriesByName(name, 'measure');
      if (measures && measures.length > 0 && measures[measures.length - 1]) {
        return measures[measures.length - 1]?.duration || 0;
      }
    } catch (e) {
      console.warn('Performance measure failed:', e);
    }
  }
  return null;
}

// Performance timing utility
export function usePerformanceTimer(name: string) {
  const startTimeRef = useRef<number | null>(null);

  const start = useCallback(() => {
    startTimeRef.current = performance.now();
    markPerformance(`${name}-start`);
  }, [name]);

  const end = useCallback(() => {
    if (startTimeRef.current === null) {
      console.warn(`Timer ${name} was not started`);
      return null;
    }

    const endTime = performance.now();
    const duration = endTime - startTimeRef.current;
    
    markPerformance(`${name}-end`);
    const measuredDuration = measurePerformance(name, `${name}-start`, `${name}-end`);
    
    // Record metric
    const store = usePerformanceOptimizationStore.getState();
    store.measureMetric({
      name,
      value: measuredDuration || duration,
      unit: 'ms',
      timestamp: new Date(),
      rating: duration < 100 ? 'good' : duration < 300 ? 'needs-improvement' : 'poor',
      threshold: { good: 100, poor: 300 },
    });

    startTimeRef.current = null;
    return measuredDuration || duration;
  }, [name]);

  return { start, end };
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor();
