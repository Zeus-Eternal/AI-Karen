import { useRef, useEffect } from 'react';

interface MemoryCacheOptions {
  maxSize?: number;
  ttl?: number; // Time to live in milliseconds
  cleanupInterval?: number; // Cleanup interval in milliseconds
}

interface CacheEntry<T> {
  value: T;
  timestamp: number;
  ttl: number;
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
 * Memory-efficient cache with automatic cleanup
 */
export class MemoryCache<T> {
  private cache: Map<string, CacheEntry<T>> = new Map();
  private maxSize: number;
  private defaultTtl: number;
  private cleanupInterval: number;
  private cleanupTimer: number | null = null;

  constructor(options: MemoryCacheOptions = {}) {
    this.maxSize = options.maxSize || 100;
    this.defaultTtl = options.ttl || 60000; // 1 minute default
    this.cleanupInterval = options.cleanupInterval || 30000; // 30 seconds default
    
    this.startCleanupTimer();
  }

  /**
   * Get a value from cache
   */
  get(key: string): T | undefined {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return undefined;
    }
    
    // Check if entry has expired
    if (Date.now() > entry.timestamp + entry.ttl) {
      this.cache.delete(key);
      return undefined;
    }
    
    // Update access time (LRU strategy)
    entry.timestamp = Date.now();
    return entry.value;
  }

  /**
   * Set a value in cache
   */
  set(key: string, value: T, ttl?: number): void {
    // Check if we need to evict entries
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      this.evictEntries();
    }
    
    this.cache.set(key, {
      value,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTtl
    });
  }

  /**
   * Check if key exists in cache
   */
  has(key: string): boolean {
    return this.get(key) !== undefined;
  }

  /**
   * Delete a key from cache
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Clear all entries from cache
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Get the current size of the cache
   */
  size(): number {
    return this.cache.size;
  }

  /**
   * Get all keys in the cache
   */
  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  /**
   * Evict least recently used entries if cache is full
   */
  private evictEntries(): void {
    // Convert to array and sort by timestamp (oldest first)
    const entries = Array.from(this.cache.entries())
      .sort((a, b) => a[1].timestamp - b[1].timestamp);
    
    // Remove oldest 10% of entries or at least 1 entry
    const evictCount = Math.max(1, Math.floor(this.cache.size * 0.1));
    
    for (let i = 0; i < evictCount && entries.length > 0; i++) {
      const [key] = entries.shift() || [];
      if (key) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Clean up expired entries
   */
  private cleanupExpiredEntries(): void {
    const now = Date.now();
    const keysToDelete: string[] = [];
    
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.timestamp + entry.ttl) {
        keysToDelete.push(key);
      }
    }
    
    for (const key of keysToDelete) {
      this.cache.delete(key);
    }
  }

  /**
   * Start the cleanup timer
   */
  private startCleanupTimer(): void {
    if (typeof window !== 'undefined') {
      this.cleanupTimer = window.setInterval(() => {
        this.cleanupExpiredEntries();
      }, this.cleanupInterval);
    }
  }

  /**
   * Stop the cleanup timer
   */
  stopCleanupTimer(): void {
    if (this.cleanupTimer && typeof window !== 'undefined') {
      window.clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }

  /**
   * Destroy the cache and clean up resources
   */
  destroy(): void {
    this.stopCleanupTimer();
    this.clear();
  }
}

/**
 * Memory usage monitoring utility
 */
export interface MemoryUsage {
  used: number;
  total: number;
  percentage: number;
  limit: number;
}

export class MemoryMonitor {
  private warnings: Array<{ percentage: number; timestamp: number }> = [];
  private warningThreshold: number;
  private criticalThreshold: number;
  private maxWarnings: number;

  constructor(options: {
    warningThreshold?: number; // Percentage (0-100)
    criticalThreshold?: number; // Percentage (0-100)
    maxWarnings?: number; // Maximum number of warnings to track
  } = {}) {
    this.warningThreshold = options.warningThreshold || 70;
    this.criticalThreshold = options.criticalThreshold || 90;
    this.maxWarnings = options.maxWarnings || 10;
  }

  /**
   * Get current memory usage
   */
  getMemoryUsage(): MemoryUsage | null {
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
   * Check if memory usage is above threshold
   */
  checkMemoryUsage(): {
    isWarning: boolean;
    isCritical: boolean;
    usage: MemoryUsage | null;
  } {
    const usage = this.getMemoryUsage();
    
    if (!usage) {
      return {
        isWarning: false,
        isCritical: false,
        usage: null
      };
    }

    const isWarning = usage.percentage >= this.warningThreshold;
    const isCritical = usage.percentage >= this.criticalThreshold;

    if (isWarning) {
      this.addWarning(usage.percentage);
    }

    return {
      isWarning,
      isCritical,
      usage
    };
  }

  /**
   * Add a warning to the warning history
   */
  private addWarning(percentage: number): void {
    this.warnings.push({
      percentage,
      timestamp: Date.now()
    });

    // Keep only the most recent warnings
    if (this.warnings.length > this.maxWarnings) {
      this.warnings.shift();
    }
  }

  /**
   * Get warning history
   */
  getWarningHistory(): Array<{ percentage: number; timestamp: number }> {
    return [...this.warnings];
  }

  /**
   * Clear warning history
   */
  clearWarningHistory(): void {
    this.warnings = [];
  }
}

/**
 * Memory optimization utilities for React components
 */
export interface UseMemoryOptimizationOptions {
  maxCacheSize?: number;
  cacheTtl?: number;
  warningThreshold?: number;
  criticalThreshold?: number;
  onMemoryWarning?: (usage: MemoryUsage) => void;
  onMemoryCritical?: (usage: MemoryUsage) => void;
}

export function useMemoryOptimization<T = unknown>(options: UseMemoryOptimizationOptions = {}) {
  const cacheRef = useRef<MemoryCache<T> | null>(null);
  const monitorRef = useRef<MemoryMonitor | null>(null);
  const intervalRef = useRef<number | null>(null);
  
  // Initialize cache and monitor
  useEffect(() => {
    cacheRef.current = new MemoryCache({
      maxSize: options.maxCacheSize || 100,
      ttl: options.cacheTtl || 60000
    });
    
    monitorRef.current = new MemoryMonitor({
      warningThreshold: options.warningThreshold || 70,
      criticalThreshold: options.criticalThreshold || 90
    });
    
    // Set up memory monitoring interval
    intervalRef.current = window.setInterval(() => {
      if (monitorRef.current) {
        const { isWarning, isCritical, usage } = monitorRef.current.checkMemoryUsage();
        
        if (usage) {
          if (isCritical && options.onMemoryCritical) {
            options.onMemoryCritical(usage);
          } else if (isWarning && options.onMemoryWarning) {
            options.onMemoryWarning(usage);
          }
        }
      }
    }, 5000); // Check every 5 seconds
    
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
      }
      
      if (cacheRef.current) {
        cacheRef.current.destroy();
      }
    };
  }, [options]);
  
  return {
    cache: cacheRef.current,
    monitor: monitorRef.current
  };
}

/**
 * Utility to optimize large data sets
 */
export class DataOptimizer {
  /**
   * Chunk a large array into smaller batches
   */
  static chunkArray<T>(array: T[], chunkSize: number): T[][] {
    const chunks: T[][] = [];
    
    for (let i = 0; i < array.length; i += chunkSize) {
      chunks.push(array.slice(i, i + chunkSize));
    }
    
    return chunks;
  }

  /**
   * Paginate data for virtualization
   */
  static paginate<T>(array: T[], pageSize: number, pageNumber: number): {
    data: T[];
    totalPages: number;
    totalItems: number;
  } {
    const startIndex = (pageNumber - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedData = array.slice(startIndex, endIndex);
    
    return {
      data: paginatedData,
      totalPages: Math.ceil(array.length / pageSize),
      totalItems: array.length
    };
  }

  /**
   * Debounce function to limit memory usage from rapid calls
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
   * Throttle function to limit memory usage from rapid calls
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
   * Memoize function to cache results and save memory
   */
  static memoize<TArgs extends unknown[], TResult>(
    func: AnyFunction<TArgs, TResult>,
    keyGenerator?: (...args: TArgs) => string
  ): AnyFunction<TArgs, TResult> {
    const cache = new Map<string, TResult>();
    
    return (...args: TArgs): TResult => {
      const key = keyGenerator ? keyGenerator(...args) : JSON.stringify(args);
      
      if (cache.has(key)) {
        return cache.get(key)!;
      }
      
      const result = func(...args);
      cache.set(key, result);
      
      // Simple cache eviction - keep only last 50 results
      if (cache.size > 50) {
        const firstKey = cache.keys().next().value as string | undefined;
        if (firstKey) {
          cache.delete(firstKey);
        }
      }
      
      return result;
    };
  }
}
