/**
 * Performance Optimization Utilities
 * 
 * This module provides utilities for optimizing performance across the application,
 * including code splitting, lazy loading, virtualization, and memory management.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

// Intersection Observer for lazy loading
export const useIntersectionObserver = (
  ref: React.RefObject<Element>,
  callback: () => void,
  options: IntersectionObserverInit = {}
) => {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          callback();
          observer.disconnect();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
        ...options,
      }
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [ref, callback, options]);
};

// Virtual scrolling hook for large lists
export const useVirtualScroll = <T,>(
  items: T[],
  itemHeight: number,
  containerHeight: number,
  overscan: number = 5
) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );
  
  const visibleItems = items.slice(startIndex, endIndex + 1);
  const offsetY = startIndex * itemHeight;
  const totalHeight = items.length * itemHeight;
  
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);
  
  return {
    visibleItems,
    offsetY,
    totalHeight,
    handleScroll,
    startIndex,
    endIndex,
  };
};

// Debounce hook for performance optimization
export const useDebounce = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const timeoutRef = useRef<NodeJS.Timeout>();
  
  return useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]) as T;
};

// Throttle hook for performance optimization
export const useThrottle = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const lastCall = useRef<number>(0);
  
  return useCallback((...args: Parameters<T>) => {
    const now = Date.now();
    if (now - lastCall.current >= delay) {
      lastCall.current = now;
      callback(...args);
    }
  }, [callback, delay]) as T;
};

// Memoization hook with dependency tracking
export const useDeepMemo = <T>(value: T, deps: React.DependencyList) => {
  const ref = useRef<{ deps: React.DependencyList; value: T }>({
    deps: [],
    value,
  });
  
  const hasChanged = !deps.every((dep, i) => {
    const prevDep = ref.current.deps[i];
    return Object.is(dep, prevDep);
  });
  
  if (hasChanged) {
    ref.current = { deps, value };
  }
  
  return ref.current.value;
};

// Memory management utilities
export const MemoryManager = {
  // Clear unused event listeners
  cleanupEventListeners: (element: Element) => {
    const clone = element.cloneNode(true);
    element.parentNode?.replaceChild(clone, element);
    return clone;
  },
  
  // Optimize images for memory
  optimizeImages: (container: Element) => {
    const images = container.querySelectorAll('img');
    images.forEach(img => {
      if (img.complete) {
        (img as any).loading = 'lazy';
      }
    });
  },
  
  // Debounced resize observer
  createResizeObserver: (callback: () => void, delay: number = 100) => {
    let timeoutId: NodeJS.Timeout;
    
    return new ResizeObserver(() => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(callback, delay);
    });
  },
};

// Performance monitoring
export const PerformanceMonitor = {
  // Measure render performance
  measureRender: (name: string, fn: () => void) => {
    const start = performance.now();
    fn();
    const end = performance.now();
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Performance] ${name}: ${end - start}ms`);
    }
    
    return end - start;
  },
  
  // Monitor memory usage
  getMemoryUsage: () => {
    if ('memory' in performance) {
      return {
        used: (performance as any).memory.usedJSHeapSize,
        total: (performance as any).memory.totalJSHeapSize,
        limit: (performance as any).memory.jsHeapSizeLimit,
      };
    }
    return null;
  },
  
  // Log performance metrics
  logMetrics: (action: string, metrics: Record<string, number>) => {
    if (process.env.NODE_ENV === 'development') {
      console.table({ action, ...metrics });
    }
    
    // Here you could send metrics to your analytics service
  },
};

// Bundle optimization utilities
export const BundleOptimizer = {
  // Preload critical resources
  preloadResource: (href: string, as: string) => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = href;
    link.as = as;
    document.head.appendChild(link);
  },
  
  // Prefetch next pages
  prefetchPage: (url: string) => {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = url;
    document.head.appendChild(link);
  },
  
  // Dynamic import with retry
  dynamicImport: async <T>(
    importFunc: () => Promise<T>,
    retries: number = 3
  ): Promise<T> => {
    try {
      return await importFunc();
    } catch (error) {
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        return BundleOptimizer.dynamicImport(importFunc, retries - 1);
      }
      throw error;
    }
  },
};

// Animation performance utilities
export const AnimationOptimizer = {
  // Request animation frame with cleanup
  requestAnimationFrame: (callback: (time: number) => void) => {
    let rafId: number;
    
    const wrappedCallback = (time: number) => {
      callback(time);
      rafId = 0;
    };
    
    rafId = requestAnimationFrame(wrappedCallback);
    
    return () => {
      if (rafId) {
        cancelAnimationFrame(rafId);
      }
    };
  },
  
  // Reduce motion for users who prefer it
  shouldReduceMotion: () => {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  },
};

export default {
  useIntersectionObserver,
  useVirtualScroll,
  useDebounce,
  useThrottle,
  useDeepMemo,
  MemoryManager,
  PerformanceMonitor,
  BundleOptimizer,
  AnimationOptimizer,
};