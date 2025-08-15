import { getTelemetryService } from './telemetry';

export interface PerformanceMetrics {
  // Core Web Vitals
  fcp?: number; // First Contentful Paint
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  
  // Custom metrics
  tti?: number; // Time to Interactive
  firstToken?: number; // Time to first AI token
  streamComplete?: number; // Time to complete stream
  
  // Resource metrics
  bundleSize?: number;
  memoryUsage?: number;
  networkLatency?: number;
  
  // User interaction metrics
  interactionLatency?: number;
  renderTime?: number;
}

export interface PerformanceMark {
  name: string;
  startTime: number;
  duration?: number;
  metadata?: Record<string, any>;
}

class PerformanceMonitor {
  private marks: Map<string, PerformanceMark> = new Map();
  private observer: PerformanceObserver | null = null;
  private memoryObserver: any = null;
  private isInitialized = false;

  constructor() {
    this.initialize();
  }

  private initialize(): void {
    if (this.isInitialized || typeof window === 'undefined') {
      return;
    }

    this.setupPerformanceObserver();
    this.setupMemoryMonitoring();
    this.trackCoreWebVitals();
    this.trackBundleSize();
    
    this.isInitialized = true;
  }

  private setupPerformanceObserver(): void {
    if (!('PerformanceObserver' in window)) {
      console.warn('PerformanceObserver not supported');
      return;
    }

    try {
      this.observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        
        entries.forEach((entry) => {
          this.handlePerformanceEntry(entry);
        });
      });

      // Observe different types of performance entries
      this.observer.observe({ 
        entryTypes: ['navigation', 'paint', 'largest-contentful-paint', 'first-input', 'layout-shift', 'measure', 'mark']
      });
    } catch (error) {
      console.warn('Failed to setup PerformanceObserver:', error);
    }
  }

  private handlePerformanceEntry(entry: PerformanceEntry): void {
    const telemetry = getTelemetryService();

    switch (entry.entryType) {
      case 'navigation':
        const navEntry = entry as PerformanceNavigationTiming;
        telemetry.track('performance_navigation', {
          domContentLoaded: navEntry.domContentLoadedEventEnd - navEntry.domContentLoadedEventStart,
          loadComplete: navEntry.loadEventEnd - navEntry.loadEventStart,
          domInteractive: navEntry.domInteractive - navEntry.navigationStart,
          redirectTime: navEntry.redirectEnd - navEntry.redirectStart,
          dnsTime: navEntry.domainLookupEnd - navEntry.domainLookupStart,
          connectTime: navEntry.connectEnd - navEntry.connectStart,
          requestTime: navEntry.responseEnd - navEntry.requestStart,
          responseTime: navEntry.responseEnd - navEntry.responseStart,
          renderTime: navEntry.domComplete - navEntry.domLoading,
        });
        break;

      case 'paint':
        telemetry.track('performance_paint', {
          name: entry.name,
          startTime: entry.startTime,
          duration: entry.duration,
        });
        break;

      case 'largest-contentful-paint':
        telemetry.track('performance_lcp', {
          startTime: entry.startTime,
          renderTime: entry.startTime,
          size: (entry as any).size,
          element: (entry as any).element?.tagName,
        });
        break;

      case 'first-input':
        const fidEntry = entry as PerformanceEventTiming;
        telemetry.track('performance_fid', {
          startTime: entry.startTime,
          processingStart: fidEntry.processingStart,
          processingEnd: fidEntry.processingEnd,
          duration: entry.duration,
          delay: fidEntry.processingStart - entry.startTime,
        });
        break;

      case 'layout-shift':
        const clsEntry = entry as any;
        if (!clsEntry.hadRecentInput) {
          telemetry.track('performance_cls', {
            startTime: entry.startTime,
            value: clsEntry.value,
            sources: clsEntry.sources?.map((source: any) => ({
              node: source.node?.tagName,
              currentRect: source.currentRect,
              previousRect: source.previousRect,
            })),
          });
        }
        break;

      case 'measure':
      case 'mark':
        telemetry.track('performance_custom', {
          type: entry.entryType,
          name: entry.name,
          startTime: entry.startTime,
          duration: entry.duration,
        });
        break;
    }
  }

  private setupMemoryMonitoring(): void {
    if (!('memory' in performance)) {
      return;
    }

    // Monitor memory usage periodically
    this.memoryObserver = setInterval(() => {
      const memory = (performance as any).memory;
      if (memory) {
        getTelemetryService().track('performance_memory', {
          usedJSHeapSize: memory.usedJSHeapSize,
          totalJSHeapSize: memory.totalJSHeapSize,
          jsHeapSizeLimit: memory.jsHeapSizeLimit,
          memoryUsagePercent: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100,
        });
      }
    }, 30000); // Every 30 seconds
  }

  private trackCoreWebVitals(): void {
    // Track FCP (First Contentful Paint)
    this.whenPaintMetricAvailable('first-contentful-paint', (value) => {
      getTelemetryService().track('performance_fcp', { value });
    });

    // Track LCP (Largest Contentful Paint)
    this.whenLCPAvailable((value) => {
      getTelemetryService().track('performance_lcp_final', { value });
    });

    // Track CLS (Cumulative Layout Shift)
    this.whenCLSAvailable((value) => {
      getTelemetryService().track('performance_cls_final', { value });
    });
  }

  private whenPaintMetricAvailable(metricName: string, callback: (value: number) => void): void {
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const entry = entries.find(e => e.name === metricName);
        if (entry) {
          callback(entry.startTime);
          observer.disconnect();
        }
      });
      observer.observe({ entryTypes: ['paint'] });
    }
  }

  private whenLCPAvailable(callback: (value: number) => void): void {
    if ('PerformanceObserver' in window) {
      let lcpValue = 0;
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        lcpValue = lastEntry.startTime;
      });
      
      observer.observe({ entryTypes: ['largest-contentful-paint'] });
      
      // Report final LCP value when page becomes hidden
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden' && lcpValue > 0) {
          callback(lcpValue);
          observer.disconnect();
        }
      });
    }
  }

  private whenCLSAvailable(callback: (value: number) => void): void {
    if ('PerformanceObserver' in window) {
      let clsValue = 0;
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        });
      });
      
      observer.observe({ entryTypes: ['layout-shift'] });
      
      // Report final CLS value when page becomes hidden
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
          callback(clsValue);
          observer.disconnect();
        }
      });
    }
  }

  private trackBundleSize(): void {
    // Estimate bundle size from loaded resources
    if ('performance' in window && 'getEntriesByType' in performance) {
      const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
      let totalSize = 0;
      let jsSize = 0;
      let cssSize = 0;

      resources.forEach((resource) => {
        if (resource.transferSize) {
          totalSize += resource.transferSize;
          
          if (resource.name.endsWith('.js')) {
            jsSize += resource.transferSize;
          } else if (resource.name.endsWith('.css')) {
            cssSize += resource.transferSize;
          }
        }
      });

      getTelemetryService().track('performance_bundle_size', {
        totalSize,
        jsSize,
        cssSize,
        resourceCount: resources.length,
      });
    }
  }

  // Public API methods
  public markTTI(): void {
    this.mark('tti', { type: 'time_to_interactive' });
  }

  public markFirstToken(): void {
    this.mark('first_token', { type: 'ai_response_start' });
  }

  public markStreamComplete(): void {
    this.mark('stream_complete', { type: 'ai_response_complete' });
  }

  public mark(name: string, metadata?: Record<string, any>): void {
    const startTime = performance.now();
    
    const mark: PerformanceMark = {
      name,
      startTime,
      metadata,
    };
    
    this.marks.set(name, mark);
    
    // Also create a performance mark for browser DevTools
    if ('mark' in performance) {
      performance.mark(name);
    }
    
    getTelemetryService().track('performance_mark', {
      name,
      startTime,
      metadata,
    });
  }

  public measure(name: string, startMark: string, endMark?: string): number {
    const start = this.marks.get(startMark);
    if (!start) {
      console.warn(`Start mark "${startMark}" not found`);
      return 0;
    }

    const endTime = endMark ? this.marks.get(endMark)?.startTime : performance.now();
    if (endMark && !endTime) {
      console.warn(`End mark "${endMark}" not found`);
      return 0;
    }

    const duration = (endTime || performance.now()) - start.startTime;
    
    // Create performance measure for browser DevTools
    if ('measure' in performance) {
      try {
        performance.measure(name, startMark, endMark);
      } catch (error) {
        // Fallback if marks don't exist in performance timeline
        console.warn('Failed to create performance measure:', error);
      }
    }
    
    getTelemetryService().track('performance_measure', {
      name,
      startMark,
      endMark,
      duration,
      startTime: start.startTime,
      endTime: endTime || performance.now(),
    });
    
    return duration;
  }

  public measureLatency(startMark: string, endMark?: string): number {
    return this.measure(`${startMark}_latency`, startMark, endMark);
  }

  public getMetrics(): PerformanceMetrics {
    const metrics: PerformanceMetrics = {};
    
    // Get paint metrics
    if ('getEntriesByType' in performance) {
      const paintEntries = performance.getEntriesByType('paint');
      const fcpEntry = paintEntries.find(entry => entry.name === 'first-contentful-paint');
      if (fcpEntry) {
        metrics.fcp = fcpEntry.startTime;
      }
      
      const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
      if (lcpEntries.length > 0) {
        metrics.lcp = lcpEntries[lcpEntries.length - 1].startTime;
      }
    }
    
    // Get custom marks
    const ttiMark = this.marks.get('tti');
    if (ttiMark) {
      metrics.tti = ttiMark.startTime;
    }
    
    const firstTokenMark = this.marks.get('first_token');
    if (firstTokenMark) {
      metrics.firstToken = firstTokenMark.startTime;
    }
    
    const streamCompleteMark = this.marks.get('stream_complete');
    if (streamCompleteMark) {
      metrics.streamComplete = streamCompleteMark.startTime;
    }
    
    // Get memory usage
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      if (memory) {
        metrics.memoryUsage = memory.usedJSHeapSize;
      }
    }
    
    return metrics;
  }

  public clearMarks(): void {
    this.marks.clear();
    
    if ('clearMarks' in performance) {
      performance.clearMarks();
    }
    
    if ('clearMeasures' in performance) {
      performance.clearMeasures();
    }
  }

  public destroy(): void {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
    
    if (this.memoryObserver) {
      clearInterval(this.memoryObserver);
      this.memoryObserver = null;
    }
    
    this.clearMarks();
    this.isInitialized = false;
  }
}

// Singleton instance
let performanceMonitorInstance: PerformanceMonitor | null = null;

export const getPerformanceMonitor = (): PerformanceMonitor => {
  if (!performanceMonitorInstance) {
    performanceMonitorInstance = new PerformanceMonitor();
  }
  return performanceMonitorInstance;
};

// Convenience functions
export const markTTI = (): void => {
  getPerformanceMonitor().markTTI();
};

export const markFirstToken = (): void => {
  getPerformanceMonitor().markFirstToken();
};

export const markStreamComplete = (): void => {
  getPerformanceMonitor().markStreamComplete();
};

export const measureLatency = (startMark: string, endMark?: string): number => {
  return getPerformanceMonitor().measureLatency(startMark, endMark);
};

export const getPerformanceMetrics = (): PerformanceMetrics => {
  return getPerformanceMonitor().getMetrics();
};

export default PerformanceMonitor;