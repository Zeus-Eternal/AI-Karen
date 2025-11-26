import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { PerformanceMonitor } from '../utils/performance';

/**
 * Hook for monitoring component performance
 */
export function usePerformance(componentName: string) {
  const mountTime = useRef<number>(Date.now());
  const renderCount = useRef<number>(0);
  
  useEffect(() => {
    const endMeasure = PerformanceMonitor.startMeasure(`${componentName}-mount`);
    const currentMountTime = mountTime.current;
    
    return () => {
      endMeasure();
      const unmountTime = Date.now();
      const duration = unmountTime - currentMountTime;
      console.log(`${componentName} unmounted after ${duration}ms`);
    };
  }, [componentName]);
  
  useEffect(() => {
    renderCount.current += 1;
    console.log(`${componentName} rendered ${renderCount.current} times`);
  });
  
  return {
    renderCount: renderCount.current,
    mountTime: mountTime.current
  };
}

/**
 * Hook for debouncing values
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  
  return debouncedValue;
}

/**
 * Hook for throttling functions
 */
export function useThrottle<T extends (...args: unknown[]) => unknown>(
  callback: T,
  delay: number
): T {
  const lastRan = useRef<number>(Date.now());
  
  return useCallback((...args: Parameters<T>) => {
    if (Date.now() - lastRan.current >= delay) {
      callback(...args);
      lastRan.current = Date.now();
    }
  }, [callback, delay]) as T;
}

/**
 * Hook for lazy loading images
 */
export function useLazyImage(
  src: string,
  options: {
    threshold?: number;
    rootMargin?: string;
  } = {}
) {
  const [isLoaded, setIsLoaded] = useState<boolean>(false);
  const [imageSrc, setImageSrc] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setImageSrc(src);
            observer.disconnect();
          }
        });
      },
      {
        threshold: options.threshold || 0.1,
        rootMargin: options.rootMargin || '0px'
      }
    );
    
    if (imgRef.current) {
      observer.observe(imgRef.current);
    }
    
    return () => {
      observer.disconnect();
    };
  }, [src, options.threshold, options.rootMargin]);
  
  const handleLoad = useCallback(() => {
    setIsLoaded(true);
    setError(null);
  }, []);
  
  const handleError = useCallback(() => {
    setError('Failed to load image');
    setIsLoaded(false);
  }, []);
  
  return {
    ref: imgRef,
    src: imageSrc,
    isLoaded,
    error,
    onLoad: handleLoad,
    onError: handleError
  };
}

/**
 * Hook for virtual scrolling
 */
export function useVirtualScroll<T>(
  items: T[],
  itemHeight: number,
  containerHeight: number
) {
  const [scrollTop, setScrollTop] = useState<number>(0);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop);
  }, []);
  
  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - 2);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + 2
    );
    
    return { startIndex, endIndex };
  }, [scrollTop, itemHeight, containerHeight, items.length]);
  
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.startIndex, visibleRange.endIndex + 1);
  }, [items, visibleRange]);
  
  const totalHeight = useMemo(() => {
    return items.length * itemHeight;
  }, [items.length, itemHeight]);
  
  const getItemOffset = useCallback((index: number) => {
    return index * itemHeight;
  }, [itemHeight]);
  
  return {
    containerRef,
    visibleItems,
    totalHeight,
    getItemOffset,
    handleScroll,
    scrollTop
  };
}

/**
 * Hook for memoizing expensive computations
 */
export function useMemoize<T extends (...args: unknown[]) => unknown>(
  fn: T,
  _deps: unknown[]
): T {
  const cacheRef = useRef<Map<string, ReturnType<T>>>(new Map());
  
  return useCallback((...args: Parameters<T>): ReturnType<T> => {
    const key = JSON.stringify(args);
    
    if (cacheRef.current.has(key)) {
      return cacheRef.current.get(key)!;
    }
    
    const result = fn(...args);
    cacheRef.current.set(key, result as ReturnType<T>);
    
    return result as ReturnType<T>;
  }, [fn]) as T;
}

/**
 * Hook for measuring component render time
 */
export function useRenderTime(componentName: string) {
  const renderTimes = useRef<number[]>([]);
  
  useEffect(() => {
    const startTime = performance.now();
    const currentRenderTimes = renderTimes.current;
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      currentRenderTimes.push(renderTime);
      
      // Keep only the last 10 render times
      if (currentRenderTimes.length > 10) {
        currentRenderTimes.shift();
      }
      
      const averageRenderTime = currentRenderTimes.reduce((a, b) => a + b, 0) / currentRenderTimes.length;
      console.log(`${componentName} render time: ${renderTime.toFixed(2)}ms (avg: ${averageRenderTime.toFixed(2)}ms)`);
    };
  }, [componentName]);
  
  const getAverageRenderTime = useCallback(() => {
    if (renderTimes.current.length === 0) {
      return 0;
    }
    
    return renderTimes.current.reduce((a, b) => a + b, 0) / renderTimes.current.length;
  }, []);
  
  const getMaxRenderTime = useCallback(() => {
    if (renderTimes.current.length === 0) {
      return 0;
    }
    
    return Math.max(...renderTimes.current);
  }, []);
  
  return {
    getAverageRenderTime,
    getMaxRenderTime,
    renderCount: renderTimes.current.length
  };
}

/**
 * Hook for optimizing re-renders
 */
export function useShouldUpdate<T extends Record<string, unknown>>(
  props: T,
  dependencies: (keyof T)[] = Object.keys(props) as (keyof T)[]
): boolean {
  const prevPropsRef = useRef<T>(props);
  
  const shouldUpdate = useMemo(() => {
    for (const key of dependencies) {
      if (prevPropsRef.current[key] !== props[key]) {
        prevPropsRef.current = props;
        return true;
      }
    }
    
    return false;
  }, [props, dependencies]);
  
  return shouldUpdate;
}

/**
 * Hook for measuring and optimizing API calls
 */
export function useApiCall<T extends (...args: unknown[]) => Promise<unknown>, R = unknown>(
  apiCall: T,
  options: {
    debounceMs?: number;
    cacheKey?: string;
    cacheTtl?: number;
  } = {}
) {
  const [data, setData] = useState<R | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const cacheRef = useRef<Map<string, { data: unknown; timestamp: number }>>(new Map());
  
  const execute = useCallback(async (...args: Parameters<T>) => {
    setLoading(true);
    setError(null);
    
    try {
      const cacheKey = options.cacheKey ? `${options.cacheKey}-${JSON.stringify(args)}` : null;
      
      // Check cache
      if (cacheKey) {
        const cached = cacheRef.current.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < (options.cacheTtl || 60000)) {
          setData(cached.data as R);
          setLoading(false);
          return cached.data;
        }
      }
      
      // Execute API call
      const result = await apiCall(...args);
      
      // Update cache
      if (cacheKey) {
        cacheRef.current.set(cacheKey, {
          data: result,
          timestamp: Date.now()
        });
      }
      
      setData(result as R);
      setLoading(false);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
      throw err;
    }
  }, [apiCall, options.cacheKey, options.cacheTtl]);
  
  // Create debounced version if requested
  const debouncedExecute = useMemo(() => {
    if (!options.debounceMs) {
      return execute;
    }
    
    let timeout: NodeJS.Timeout | null = null;
    
    return (...args: Parameters<T>) => {
      if (timeout) {
        clearTimeout(timeout);
      }
      
      return new Promise((resolve, reject) => {
        timeout = setTimeout(() => {
          execute(...args).then(resolve).catch(reject);
        }, options.debounceMs);
      });
    };
  }, [execute, options.debounceMs]);
  
  return {
    data,
    loading,
    error,
    execute: debouncedExecute,
    clearCache: useCallback(() => {
      cacheRef.current.clear();
    }, [])
  };
}