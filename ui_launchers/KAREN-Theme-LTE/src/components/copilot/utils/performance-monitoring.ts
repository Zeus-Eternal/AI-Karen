import React, { useEffect, useRef, useState } from 'react';

interface PerformanceMetrics {
  renderTime: number;
  memoryUsage?: {
    used: number;
    total: number;
    percentage: number;
    limit: number;
  };
  timestamp: number;
}

interface PerformanceEntry {
  name: string;
  duration: number;
  startTime: number;
  type: 'measure' | 'mark';
}

interface PerformanceMonitorOptions {
  enableMemoryTracking?: boolean;
  maxEntries?: number;
  sampleInterval?: number;
  onMetricsUpdate?: (metrics: PerformanceMetrics) => void;
  onMemoryWarning?: (usage: NonNullable<PerformanceMetrics['memoryUsage']>) => void;
  onMemoryCritical?: (usage: NonNullable<PerformanceMetrics['memoryUsage']>) => void;
}

interface PerformanceMemory {
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
}

type AnyFunction<TArgs extends unknown[] = unknown[], TResult = unknown> = (...args: TArgs) => TResult;

const getPerformanceMemory = (): PerformanceMemory | null => {
  if (typeof performance === 'undefined' || !('memory' in performance)) {
    return null;
  }

  const memory = (performance as Performance & { memory?: PerformanceMemory }).memory;
  return memory ?? null;
};

/**
 * Performance monitoring utility for tracking component performance
 */
export class PerformanceMonitor {
  private entries: PerformanceEntry[] = [];
  private maxEntries: number;
  private enableMemoryTracking: boolean;
  private sampleInterval: number;
  private onMetricsUpdate?: (metrics: PerformanceMetrics) => void;
  private onMemoryWarning?: (usage: NonNullable<PerformanceMetrics['memoryUsage']>) => void;
  private onMemoryCritical?: (usage: NonNullable<PerformanceMetrics['memoryUsage']>) => void;
  private intervalId: number | null = null;

  constructor(options: PerformanceMonitorOptions = {}) {
    this.maxEntries = options.maxEntries || 100;
    this.enableMemoryTracking = options.enableMemoryTracking || false;
    this.sampleInterval = options.sampleInterval || 5000;
    this.onMetricsUpdate = options.onMetricsUpdate;
    this.onMemoryWarning = options.onMemoryWarning;
    this.onMemoryCritical = options.onMemoryCritical;
  }

  /**
   * Start measuring performance
   */
  start(name: string): void {
    if (typeof performance !== 'undefined' && performance.mark) {
      performance.mark(`${name}-start`);
    }
  }

  /**
   * End measuring performance and record the result
   */
  end(name: string): number {
    if (typeof performance !== 'undefined' && performance.mark && performance.measure) {
      try {
        performance.mark(`${name}-end`);
        performance.measure(name, `${name}-start`, `${name}-end`);
        
        // Get the measurement
        const measures = performance.getEntriesByName(name);
        if (measures.length > 0) {
          const measure = measures[measures.length - 1];
          if (measure) {
            this.addEntry({
              name,
              duration: measure.duration,
              startTime: measure.startTime,
              type: 'measure'
            });

            // Clean up marks
            performance.clearMarks(`${name}-start`);
            performance.clearMarks(`${name}-end`);

            return measure.duration;
          }
        }
      } catch (error) {
        console.warn(`Performance measurement failed for ${name}:`, error);
      }
    }
    return 0;
  }

  /**
   * Add a performance entry
   */
  private addEntry(entry: PerformanceEntry): void {
    this.entries.push(entry);
    
    // Keep only the most recent entries
    if (this.entries.length > this.maxEntries) {
      this.entries.shift();
    }
  }

  /**
   * Get all performance entries
   */
  getEntries(): PerformanceEntry[] {
    return [...this.entries];
  }

  /**
   * Get performance metrics
   */
  getMetrics(): PerformanceMetrics {
    const now = Date.now();
    const memoryUsage = this.enableMemoryTracking ? this.getMemoryUsage() : undefined;
    
    // Calculate average render time from recent entries
    const recentEntries = this.entries
      .filter(entry => entry.type === 'measure')
      .slice(-10); // Last 10 measurements
    
    const avgRenderTime = recentEntries.length > 0
      ? recentEntries.reduce((sum, entry) => sum + entry.duration, 0) / recentEntries.length
      : 0;
    
    return {
      renderTime: avgRenderTime,
      memoryUsage: memoryUsage || undefined,
      timestamp: now
    };
  }

  /**
   * Get current memory usage
   */
  private getMemoryUsage(): { used: number; total: number; percentage: number; limit: number } | null {
    const memory = getPerformanceMemory();
    
    if (!memory) {
      return null;
    }

    const used = memory.usedJSHeapSize;
    const total = memory.totalJSHeapSize;
    const limit = memory.jsHeapSizeLimit;
    
    return {
      used,
      total,
      percentage: limit ? (used / limit) * 100 : 0,
      limit
    };
  }

  /**
   * Start continuous monitoring
   */
  startMonitoring(): void {
    if (this.intervalId) return;
    
    this.intervalId = window.setInterval(() => {
      const metrics = this.getMetrics();
      
      if (this.onMetricsUpdate) {
        this.onMetricsUpdate(metrics);
      }
      
      if (this.enableMemoryTracking && metrics.memoryUsage) {
        const { percentage } = metrics.memoryUsage;
        
        if (percentage > 90 && this.onMemoryCritical) {
          this.onMemoryCritical(metrics.memoryUsage);
        } else if (percentage > 70 && this.onMemoryWarning) {
          this.onMemoryWarning(metrics.memoryUsage);
        }
      }
    }, this.sampleInterval);
  }

  /**
   * Stop continuous monitoring
   */
  stopMonitoring(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  /**
   * Clear all performance entries
   */
  clear(): void {
    this.entries = [];
    if (typeof performance !== 'undefined' && performance.clearMarks) {
      performance.clearMarks();
      performance.clearMeasures();
    }
  }

  /**
   * Destroy the monitor and clean up resources
   */
  destroy(): void {
    this.stopMonitoring();
    this.clear();
  }
}

/**
 * React hook for performance monitoring
 */
export function usePerformanceMonitor(
  name: string,
  options: PerformanceMonitorOptions = {}
): {
  metrics: PerformanceMetrics | null;
  start: () => void;
  end: () => number;
  clear: () => void;
} {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const monitorRef = useRef<PerformanceMonitor | null>(null);
  
  useEffect(() => {
    // Create performance monitor
    monitorRef.current = new PerformanceMonitor({
      ...options,
      onMetricsUpdate: (newMetrics) => {
        setMetrics(newMetrics);
        if (options.onMetricsUpdate) {
          options.onMetricsUpdate(newMetrics);
        }
      }
    });
    
    // Start monitoring
    monitorRef.current.startMonitoring();
    
    // Measure initial render time
    monitorRef.current.start(`${name}-initial-render`);
    
    return () => {
      // Measure cleanup time
      if (monitorRef.current) {
        monitorRef.current.end(`${name}-initial-render`);
        monitorRef.current.destroy();
      }
    };
  }, [name, options]);
  
  const start = React.useCallback(() => {
    if (monitorRef.current) {
      monitorRef.current.start(`${name}-${Date.now()}`);
    }
  }, [name]);
  
  const end = React.useCallback(() => {
    if (monitorRef.current) {
      return monitorRef.current.end(`${name}-${Date.now()}`);
    }
    return 0;
  }, [name]);
  
  const clear = React.useCallback(() => {
    if (monitorRef.current) {
      monitorRef.current.clear();
    }
  }, []);
  
  return {
    metrics,
    start,
    end,
    clear
  };
}

/**
 * Higher-order component for performance monitoring
 */
export function withPerformanceMonitoring<P extends object>(
  Component: React.ComponentType<P>,
  options: PerformanceMonitorOptions & { componentName?: string } = {}
): React.ComponentType<P> {
  const { componentName, ...monitorOptions } = options;
  const name = componentName || Component.displayName || Component.name || 'Component';
  
  const WrappedComponent: React.ComponentType<P> = (props) => {
    const { start, end } = usePerformanceMonitor(name, monitorOptions);
    
    useEffect(() => {
      start();
      return () => {
        end();
      };
    }, [end, start]);
    
    return React.createElement(Component, props);
  };
  
  WrappedComponent.displayName = `WithPerformanceMonitoring(${name})`;
  
  return WrappedComponent;
}

/**
 * Performance utilities
 */
export class PerformanceUtils {
  /**
   * Debounce function to limit rapid calls
   */
  static debounce<TArgs extends unknown[], TResult>(
    func: AnyFunction<TArgs, TResult>,
    delay: number
  ): (...args: TArgs) => void {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    
    return (...args: TArgs) => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      
      timeoutId = setTimeout(() => {
        func(...args);
      }, delay);
    };
  }

  /**
   * Throttle function to limit rapid calls
   */
  static throttle<TArgs extends unknown[], TResult>(
    func: AnyFunction<TArgs, TResult>,
    limit: number
  ): (...args: TArgs) => TResult | null {
    let inThrottle = false;
    let lastResult: TResult | null = null;
    
    return (...args: TArgs) => {
      if (!inThrottle) {
        inThrottle = true;
        
        setTimeout(() => {
          inThrottle = false;
        }, limit);
        
        lastResult = func(...args);
        return lastResult;
      }
      
      return lastResult;
    };
  }

  /**
   * Measure execution time of a function
   */
  static measureTime<TArgs extends unknown[], TResult>(
    name: string,
    func: AnyFunction<TArgs, TResult>
  ): (...args: TArgs) => TResult {
    return (...args: TArgs): TResult => {
      const monitor = new PerformanceMonitor();
      monitor.start(name);
      
      try {
        const result = func(...args);
        monitor.end(name);
        return result;
      } catch (error) {
        monitor.end(name);
        throw error;
      }
    };
  }
}
