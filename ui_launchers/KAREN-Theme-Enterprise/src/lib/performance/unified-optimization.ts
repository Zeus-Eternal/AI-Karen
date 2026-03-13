/**
 * Unified Performance Optimization Utilities
 * Consolidates duplicate performance optimization implementations
 * across the codebase to ensure DRY principles and consistency
 */

import React, { useCallback, useRef, useEffect, useMemo, useState } from 'react';

// Performance monitoring configuration
interface PerformanceConfig {
  enableMonitoring: boolean;
  sampleRate: number;
  maxSamples: number;
}

// Performance measurement interface
interface PerformanceMeasurement {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
}

// Default configuration
const DEFAULT_CONFIG: PerformanceConfig = {
  enableMonitoring: process.env.NODE_ENV === 'development',
  sampleRate: 1.0,
  maxSamples: 100
};

/**
 * Unified performance optimization utilities
 */
export class UnifiedPerformanceOptimizer {
  private config: PerformanceConfig;
  private measurements: Map<string, PerformanceMeasurement[]> = new Map();
  private observers: PerformanceObserver[] = [];

  constructor(config: Partial<PerformanceConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.initializeObservers();
  }

  /**
   * Initialize performance observers for browser APIs
   */
  private initializeObservers(): void {
    if (typeof window === 'undefined' || !window.PerformanceObserver) return;

    try {
      // Observe long tasks
      const longTaskObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.duration > 50) { // Tasks longer than 50ms
            this.recordMeasurement('long-task', entry.startTime, entry.startTime + entry.duration);
          }
        });
      });

      longTaskObserver.observe({ entryTypes: ['longtask'] });
      this.observers.push(longTaskObserver);

      // Observe navigation timing
      const navigationObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.entryType === 'navigation') {
            const navEntry = entry as PerformanceNavigationTiming;
            this.recordMeasurement('page-load', navEntry.fetchStart, navEntry.loadEventEnd);
          }
        });
      });

      navigationObserver.observe({ entryTypes: ['navigation'] });
      this.observers.push(navigationObserver);
    } catch (error) {
      console.warn('Performance observers not fully supported:', error);
    }
  }

  /**
   * Record a performance measurement
   */
  public recordMeasurement(name: string, startTime: number, endTime: number): void {
    if (!this.config.enableMonitoring) return;

    const measurement: PerformanceMeasurement = {
      name,
      startTime,
      endTime,
      duration: endTime - startTime
    };

    const measurements = this.measurements.get(name) || [];
    measurements.push(measurement);

    // Keep only the most recent measurements
    if (measurements.length > this.config.maxSamples) {
      measurements.shift();
    }

    this.measurements.set(name, measurements);
  }

  /**
   * Get performance statistics for a specific measurement
   */
  getStats(name: string): { avg: number; min: number; max: number; count: number } | null {
    const measurements = this.measurements.get(name);
    if (!measurements || measurements.length === 0) return null;

    const durations = measurements
      .map(m => m.duration || 0)
      .filter(d => d > 0);

    if (durations.length === 0) return null;

    return {
      avg: durations.reduce((sum, d) => sum + d, 0) / durations.length,
      min: Math.min(...durations),
      max: Math.max(...durations),
      count: durations.length
    };
  }

  /**
   * Get all performance measurements
   */
  getAllMeasurements(): Record<string, PerformanceMeasurement[]> {
    const result: Record<string, PerformanceMeasurement[]> = {};
    this.measurements.forEach((measurements, name) => {
      result[name] = [...measurements];
    });
    return result;
  }

  /**
   * Clear all measurements
   */
  clearMeasurements(): void {
    this.measurements.clear();
  }

  /**
   * Cleanup observers
   */
  cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Singleton instance
let unifiedPerformanceOptimizer: UnifiedPerformanceOptimizer | null = null;

/**
 * Get the performance optimizer instance
 */
export function getPerformanceOptimizer(): UnifiedPerformanceOptimizer {
  if (!unifiedPerformanceOptimizer) {
    unifiedPerformanceOptimizer = new UnifiedPerformanceOptimizer();
  }
  return unifiedPerformanceOptimizer;
}

/**
 * React hook for debouncing values with performance tracking
 */
export function useDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T {
  const timeoutRef = useRef<NodeJS.Timeout>();
  const callbackRef = useRef(callback);
  const optimizer = getPerformanceOptimizer();

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  return useCallback((...args: Parameters<T>) => {
    const startTime = performance.now();
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      const endTime = performance.now();
      optimizer.recordMeasurement('debounce', startTime, endTime);
      callbackRef.current(...args);
    }, delay);
  }, deps) as T;
}

/**
 * React hook for throttling values with performance tracking
 */
export function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T {
  const lastCallRef = useRef<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const callbackRef = useRef(callback);
  const optimizer = getPerformanceOptimizer();

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  return useCallback((...args: Parameters<T>) => {
    const startTime = performance.now();
    const now = Date.now();

    if (now - lastCallRef.current >= delay) {
      lastCallRef.current = now;
      const endTime = performance.now();
      optimizer.recordMeasurement('throttle', startTime, endTime);
      callbackRef.current(...args);
    } else {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        lastCallRef.current = Date.now();
        const endTime = performance.now();
        optimizer.recordMeasurement('throttle-delayed', startTime, endTime);
        callbackRef.current(...args);
      }, delay - (now - lastCallRef.current));
    }
  }, deps) as T;
}

/**
 * React hook for deep memoization with performance tracking
 */
export function useDeepMemo<T>(value: T, deps: React.DependencyList): T {
  const ref = useRef<{ deps: React.DependencyList; value: T }>({
    deps: [],
    value: value as T
  });
  const optimizer = getPerformanceOptimizer();

  const startTime = performance.now();

  if (!deps || !ref.current.deps || !areDepsEqual(deps, ref.current.deps)) {
    const endTime = performance.now();
    optimizer.recordMeasurement('deep-memo-calculation', startTime, endTime);
    
    ref.current.deps = [...(deps || [])];
    ref.current.value = value;
  } else {
    const endTime = performance.now();
    optimizer.recordMeasurement('deep-memo-cache-hit', startTime, endTime);
  }

  return ref.current.value;
}

/**
 * React hook for intersection observer with performance tracking
 */
export function useIntersectionObserver(
  ref: React.RefObject<Element>,
  callback: (entries: IntersectionObserverEntry[]) => void,
  options: IntersectionObserverInit = {}
): void {
  const callbackRef = useRef(callback);
  const optimizer = getPerformanceOptimizer();

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const startTime = performance.now();

    const observer = new IntersectionObserver((entries) => {
      const endTime = performance.now();
      optimizer.recordMeasurement('intersection-observer', startTime, endTime);
      callbackRef.current(entries);
    }, options);

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [ref.current, JSON.stringify(options)]);
}

/**
 * React hook for virtual scrolling with performance tracking
 */
export function useVirtualScroll<T>({
  items,
  itemHeight,
  containerHeight,
  overscan = 5
}: {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}) {
  const [scrollTop, setScrollTop] = useState(0);
  const optimizer = getPerformanceOptimizer();

  const visibleItems = useMemo(() => {
    const startTime = performance.now();
    
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    
    const result = items.slice(startIndex, endIndex + 1).map((item, index) => ({
      item,
      index: startIndex + index
    }));
    
    const endTime = performance.now();
    optimizer.recordMeasurement('virtual-scroll-calculation', startTime, endTime);
    
    return result;
  }, [items, itemHeight, containerHeight, scrollTop, overscan]);

  const totalHeight = items.length * itemHeight;

  return {
    visibleItems,
    totalHeight,
    onScroll: useCallback((e: React.UIEvent<HTMLDivElement>) => {
      const startTime = performance.now();
      setScrollTop(e.currentTarget.scrollTop);
      const endTime = performance.now();
      optimizer.recordMeasurement('virtual-scroll', startTime, endTime);
    }, [])
  };
}

/**
 * Memory management utilities
 */
export const MemoryManager = {
  /**
   * Clear unused event listeners
   */
  clearEventListeners: (element: Element) => {
    const clone = element.cloneNode(true);
    element.parentNode?.replaceChild(clone, element);
    return clone;
  },

  /**
   * Force garbage collection hint
   */
  forceGC: () => {
    if (typeof window !== 'undefined' && 'gc' in window) {
      (window as any).gc();
    }
  },

  /**
   * Check memory usage
   */
  getMemoryUsage: () => {
    if (typeof window !== 'undefined' && 'memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit
      };
    }
    return null;
  }
};

/**
 * Bundle optimization utilities
 */
export const BundleOptimizer = {
  /**
   * Preload critical resources
   */
  preloadResource: (url: string, as: 'script' | 'style' | 'image' = 'script') => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = url;
    link.as = as;
    document.head.appendChild(link);
  },

  /**
   * Lazy load component
   */
  lazyLoad: <T extends React.ComponentType<any>>(
    importFunc: () => Promise<{ default: T }>
  ) => {
    return React.lazy(importFunc);
  }
};

/**
 * Animation performance utilities
 */
export const AnimationOptimizer = {
  /**
   * Request animation frame with cleanup
   */
  requestAnimationFrame: (callback: FrameRequestCallback): (() => void) => {
    let rafId: number;
    
    const wrappedCallback = () => {
      rafId = requestAnimationFrame(callback);
    };
    
    rafId = requestAnimationFrame(wrappedCallback);
    
    return () => {
      if (rafId) {
        cancelAnimationFrame(rafId);
      }
    };
  },

  /**
   * Optimize animation for reduced motion
   */
  shouldReduceMotion: () => {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }
};

// Helper function to compare dependency arrays
function areDepsEqual(a: React.DependencyList, b: React.DependencyList): boolean {
  if (a === b) return true;
  if (a.length !== b.length) return false;
  
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  
  return true;
}

// Export singleton instance
export const performanceOptimizer = getPerformanceOptimizer();

// Export for backward compatibility
export {
  useDebounce as debounce,
  useThrottle as throttle,
  useDeepMemo as deepMemo,
  useIntersectionObserver as intersectionObserver,
  useVirtualScroll as virtualScroll
};