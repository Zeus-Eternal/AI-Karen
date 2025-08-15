import { useMemo, useCallback, useRef, DependencyList } from 'react';

/**
 * Utility for creating stable dependency arrays
 * Prevents unnecessary re-renders due to object/array recreation
 */
export const useStableDeps = <T extends readonly unknown[]>(deps: T): T => {
  const ref = useRef<T>(deps);
  
  // Deep comparison for dependency arrays
  const isEqual = useMemo(() => {
    if (ref.current.length !== deps.length) return false;
    
    return ref.current.every((item, index) => {
      const currentItem = deps[index];
      
      // Handle primitive values
      if (typeof item !== 'object' || item === null) {
        return item === currentItem;
      }
      
      // Handle arrays
      if (Array.isArray(item) && Array.isArray(currentItem)) {
        return item.length === currentItem.length && 
               item.every((val, i) => val === currentItem[i]);
      }
      
      // Handle objects (shallow comparison)
      if (typeof currentItem === 'object' && currentItem !== null) {
        const itemKeys = Object.keys(item);
        const currentKeys = Object.keys(currentItem);
        
        return itemKeys.length === currentKeys.length &&
               itemKeys.every(key => (item as any)[key] === (currentItem as any)[key]);
      }
      
      return false;
    });
  }, deps);
  
  if (!isEqual) {
    ref.current = deps;
  }
  
  return ref.current;
};

/**
 * Memoized callback with stable dependencies
 */
export const useStableCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: DependencyList
): T => {
  const stableDeps = useStableDeps(deps);
  return useCallback(callback, stableDeps);
};

/**
 * Memoized value with stable dependencies
 */
export const useStableMemo = <T>(
  factory: () => T,
  deps: DependencyList
): T => {
  const stableDeps = useStableDeps(deps);
  return useMemo(factory, stableDeps);
};

/**
 * Debounced callback hook
 * Useful for expensive operations triggered by user input
 */
export const useDebouncedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: DependencyList
): T => {
  const timeoutRef = useRef<NodeJS.Timeout>();
  
  return useStableCallback(
    ((...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    }) as T,
    [callback, delay, ...deps]
  );
};

/**
 * Throttled callback hook
 * Limits the rate of function execution
 */
export const useThrottledCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: DependencyList
): T => {
  const lastCallRef = useRef<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout>();
  
  return useStableCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now();
      const timeSinceLastCall = now - lastCallRef.current;
      
      if (timeSinceLastCall >= delay) {
        lastCallRef.current = now;
        callback(...args);
      } else {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        
        timeoutRef.current = setTimeout(() => {
          lastCallRef.current = Date.now();
          callback(...args);
        }, delay - timeSinceLastCall);
      }
    }) as T,
    [callback, delay, ...deps]
  );
};

/**
 * Memoized expensive computation with cache
 * Useful for complex calculations that don't change often
 */
export const useExpensiveComputation = <T, Args extends readonly unknown[]>(
  computeFn: (...args: Args) => T,
  args: Args,
  cacheSize = 10
): T => {
  const cacheRef = useRef<Map<string, T>>(new Map());
  
  return useMemo(() => {
    const key = JSON.stringify(args);
    
    if (cacheRef.current.has(key)) {
      return cacheRef.current.get(key)!;
    }
    
    const result = computeFn(...args);
    
    // Implement LRU cache
    if (cacheRef.current.size >= cacheSize) {
      const firstKey = cacheRef.current.keys().next().value;
      cacheRef.current.delete(firstKey);
    }
    
    cacheRef.current.set(key, result);
    return result;
  }, [computeFn, ...args, cacheSize]);
};

/**
 * Memoized selector for Zustand stores
 * Prevents unnecessary re-renders when selecting specific store slices
 */
export const useStoreSelector = <T, R>(
  store: () => T,
  selector: (state: T) => R,
  equalityFn?: (a: R, b: R) => boolean
): R => {
  const selectorRef = useRef(selector);
  const equalityRef = useRef(equalityFn);
  
  // Update refs if functions change
  selectorRef.current = selector;
  equalityRef.current = equalityFn;
  
  return useMemo(() => {
    const state = store();
    return selectorRef.current(state);
  }, [store]);
};

/**
 * Performance measurement hook
 * Useful for identifying expensive renders
 */
export const usePerformanceMeasure = (name: string, enabled = false) => {
  const startTimeRef = useRef<number>();
  
  if (enabled && typeof performance !== 'undefined') {
    if (!startTimeRef.current) {
      startTimeRef.current = performance.now();
      performance.mark(`${name}-start`);
    }
    
    return () => {
      if (startTimeRef.current) {
        const endTime = performance.now();
        const duration = endTime - startTimeRef.current;
        
        performance.mark(`${name}-end`);
        performance.measure(name, `${name}-start`, `${name}-end`);
        
        console.log(`Performance: ${name} took ${duration.toFixed(2)}ms`);
        startTimeRef.current = undefined;
      }
    };
  }
  
  return () => {}; // No-op when disabled
};