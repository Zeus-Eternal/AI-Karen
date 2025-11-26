/**
 * Performance utilities for the Copilot system
 * Implements performance optimizations for the innovative Copilot-first approach
 */

/**
 * Debounce function to limit how often a function can be called
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout);
    }
    
    timeout = setTimeout(() => {
      func(...args);
    }, wait);
  };
}

/**
 * Throttle function to limit how often a function can be called
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

/**
 * Memoize function to cache results of expensive computations
 */
export function memoize<T extends (...args: unknown[]) => unknown>(
  func: T,
  keyGenerator?: (...args: Parameters<T>) => string
): (...args: Parameters<T>) => ReturnType<T> {
  const cache = new Map<string, ReturnType<T>>();
  
  return (...args: Parameters<T>): ReturnType<T> => {
    const key = keyGenerator ? keyGenerator(...args) : JSON.stringify(args);
    
    if (cache.has(key)) {
      return cache.get(key)!;
    }
    
    const result = func(...args);
    cache.set(key, result as ReturnType<T>);
    return result as ReturnType<T>;
  };
}

/**
 * Virtual list utilities for handling large lists efficiently
 */
export class VirtualListUtils {
  /**
   * Calculate visible items in a virtual list
   */
  static calculateVisibleItems(
    totalCount: number,
    itemHeight: number,
    containerHeight: number,
    scrollTop: number
  ): { startIndex: number; endIndex: number } {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - 2);
    const endIndex = Math.min(
      totalCount - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + 2
    );
    
    return { startIndex, endIndex };
  }
  
  /**
   * Calculate offset for a specific item in a virtual list
   */
  static calculateItemOffset(index: number, itemHeight: number): number {
    return index * itemHeight;
  }
  
  /**
   * Calculate total height of a virtual list
   */
  static calculateTotalHeight(totalCount: number, itemHeight: number): number {
    return totalCount * itemHeight;
  }
}

/**
 * Performance monitoring utilities
 */
export class PerformanceMonitor {
  private static metrics: Map<string, number[]> = new Map();
  
  /**
   * Start a performance measurement
   */
  static startMeasure(label: string): () => void {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      if (!this.metrics.has(label)) {
        this.metrics.set(label, []);
      }
      
      this.metrics.get(label)!.push(duration);
    };
  }
  
  /**
   * Get average performance metric
   */
  static getAverageMetric(label: string): number | null {
    const values = this.metrics.get(label);
    if (!values || values.length === 0) {
      return null;
    }
    
    const sum = values.reduce((acc, val) => acc + val, 0);
    return sum / values.length;
  }
  
  /**
   * Get all performance metrics
   */
  static getAllMetrics(): Record<string, { average: number; count: number }> {
    const result: Record<string, { average: number; count: number }> = {};
    
    this.metrics.forEach((values, label) => {
      const sum = values.reduce((acc, val) => acc + val, 0);
      result[label] = {
        average: sum / values.length,
        count: values.length
      };
    });
    
    return result;
  }
  
  /**
   * Clear all performance metrics
   */
  static clearMetrics(): void {
    this.metrics.clear();
  }
}

/**
 * Lazy loading utilities
 */
export class LazyLoader {
  private static observer: IntersectionObserver | null = null;
  
  /**
   * Initialize the intersection observer
   */
  private static getObserver(): IntersectionObserver {
    if (!this.observer) {
      this.observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const element = entry.target as HTMLElement;
              const callback = (element as unknown as Record<string, unknown>).__lazyLoadCallback as (() => void) | undefined;
              
              if (callback) {
                callback();
                delete (element as unknown as Record<string, unknown>).__lazyLoadCallback;
                this.observer?.unobserve(element);
              }
            }
          });
        },
        { rootMargin: '100px' }
      );
    }
    
    return this.observer;
  }
  
  /**
   * Register an element for lazy loading
   */
  static register(
    element: HTMLElement,
    callback: () => void
  ): void {
    const observer = this.getObserver();
    
    // Store callback on element
    (element as unknown as Record<string, unknown>).__lazyLoadCallback = callback;
    
    observer.observe(element);
  }
  
  /**
   * Unregister an element from lazy loading
   */
  static unregister(element: HTMLElement): void {
    if (this.observer) {
      this.observer.unobserve(element);
      delete (element as unknown as Record<string, unknown>).__lazyLoadCallback;
    }
  }
}

/**
 * Image optimization utilities
 */
export class ImageOptimizer {
  /**
   * Generate optimized image URL with proper sizing
   */
  static getOptimizedImageUrl(
    url: string,
    width: number,
    height?: number,
    quality: number = 80
  ): string {
    // If the URL is already optimized, return it as is
    if (url.includes('?') && (url.includes('width=') || url.includes('w='))) {
      return url;
    }
    
    // For different image services, we'd have different optimization strategies
    // This is a generic implementation
    const separator = url.includes('?') ? '&' : '?';
    const heightParam = height ? `&height=${height}` : '';
    
    return `${url}${separator}width=${width}${heightParam}&quality=${quality}`;
  }
  
  /**
   * Generate responsive image srcset
   */
  static generateSrcset(
    url: string,
    widths: number[],
    quality: number = 80
  ): string {
    return widths
      .map(width => `${this.getOptimizedImageUrl(url, width, undefined, quality)} ${width}w`)
      .join(', ');
  }
  
  /**
   * Generate responsive image sizes attribute
   */
  static generateSizes(
    breakpoints: { maxWidth: number; size: string }[]
  ): string {
    return breakpoints
      .map(bp => `(max-width: ${bp.maxWidth}px) ${bp.size}`)
      .join(', ');
  }
}

/**
 * Code highlighting optimization utilities
 */
export class CodeHighlighter {
  private static highlightedCache = new Map<string, string>();
  
  /**
   * Highlight code with caching
   */
  static async highlightCode(
    code: string,
    language: string,
    highlightFn: (code: string, language: string) => Promise<string>
  ): Promise<string> {
    const cacheKey = `${language}:${code.length}:${code.slice(0, 100)}`;
    
    if (this.highlightedCache.has(cacheKey)) {
      return this.highlightedCache.get(cacheKey)!;
    }
    
    const highlighted = await highlightFn(code, language);
    this.highlightedCache.set(cacheKey, highlighted);
    
    return highlighted;
  }
  
  /**
   * Clear the highlight cache
   */
  static clearCache(): void {
    this.highlightedCache.clear();
  }
  
  /**
   * Get cache size
   */
  static getCacheSize(): number {
    return this.highlightedCache.size;
  }
}

/**
 * Component rendering optimization utilities
 */
export class ComponentOptimizer {
  /**
   * Create a component with shouldComponentUpdate optimization
   */
  static shouldComponentUpdate(
    prevProps: Record<string, unknown>,
    nextProps: Record<string, unknown>,
    dependencies: string[] = Object.keys(nextProps)
  ): boolean {
    for (const key of dependencies) {
      if (prevProps[key] !== nextProps[key]) {
        return true;
      }
    }
    
    return false;
  }
  
  /**
   * Deep comparison for complex props
   */
  static deepEqual(a: unknown, b: unknown): boolean {
    if (a === b) {
      return true;
    }
    
    if (typeof a !== typeof b) {
      return false;
    }
    
    if (typeof a === 'object' && a !== null && b !== null) {
      const keysA = Object.keys(a as object);
      const keysB = Object.keys(b as object);
      
      if (keysA.length !== keysB.length) {
        return false;
      }
      
      for (const key of keysA) {
        if (!keysB.includes(key) || !this.deepEqual((a as Record<string, unknown>)[key], (b as Record<string, unknown>)[key])) {
          return false;
        }
      }
      
      return true;
    }
    
    return false;
  }
}