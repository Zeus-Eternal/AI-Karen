/**
 * Caching utilities for model selection services
 */

/**
 * Simple in-memory cache with TTL support
 */
export class MemoryCache<T> {
  private cache = new Map<string, { value: T; expiry: number }>();
  private defaultTTL: number;

  constructor(defaultTTL: number = 30000) {
    this.defaultTTL = defaultTTL;
  }

  /**
   * Set a value in the cache with optional TTL
   */
  set(key: string, value: T, ttl?: number): void {
    const expiry = Date.now() + (ttl || this.defaultTTL);
    this.cache.set(key, { value, expiry });
  }

  /**
   * Get a value from the cache
   */
  get(key: string): T | undefined {
    const item = this.cache.get(key);
    if (!item) {
      return undefined;
    }

    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return undefined;
    }

    return item.value;
  }

  /**
   * Check if a key exists and is not expired
   */
  has(key: string): boolean {
    const item = this.cache.get(key);
    if (!item) {
      return false;
    }

    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Delete a specific key
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Clear all cached items
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Get all valid (non-expired) keys
   */
  keys(): string[] {
    const now = Date.now();
    const validKeys: string[] = [];

    this.cache.forEach((item, key) => {
      if (now <= item.expiry) {
        validKeys.push(key);
      } else {
        this.cache.delete(key);
      }
    });
    return validKeys;
  }

  /**
   * Get cache size (number of valid entries)
   */
  size(): number {
    return this.keys().length;
  }

  /**
   * Clean up expired entries
   */
  cleanup(): number {
    const now = Date.now();
    let cleaned = 0;

    this.cache.forEach((item, key) => {
      if (now > item.expiry) {
        this.cache.delete(key);
        cleaned++;
      }
    });
    return cleaned;
  }
}

/**
 * Cache key generator utilities
 */
export class CacheKeyGenerator {
  /**
   * Generate a cache key from multiple parameters
   */
  static generate(...parts: (string | number | boolean | undefined | null)[]): string {
    return parts
      .filter(part => part !== undefined && part !== null)
      .map(part => String(part))
      .join(':');
  }

  /**
   * Generate a cache key for model selection options
   */
  static forModelSelection(options: Record<string, any>): string {
    const sortedKeys = Object.keys(options).sort();
    const keyParts = sortedKeys.map(key => `${key}=${options[key]}`);
    return `model_selection:${keyParts.join(':')}`;
  }

  /**
   * Generate a cache key for directory scan
   */
  static forDirectoryScan(directory: string, options?: Record<string, any>): string {
    const optionsPart = options ? `:${JSON.stringify(options)}` : '';
    return `directory_scan:${directory}${optionsPart}`;
  }

  /**
   * Generate a cache key for model health check
   */
  static forModelHealth(modelId: string): string {
    return `model_health:${modelId}`;
  }

  /**
   * Generate a cache key for resource check
   */
  static forResourceCheck(modelId: string, checkType: string = 'feasibility'): string {
    return `resource_check:${checkType}:${modelId}`;
  }

  /**
   * Generate a cache key for performance metrics
   */
  static forPerformanceMetrics(modelId: string, timeframe?: string): string {
    const timeframePart = timeframe ? `:${timeframe}` : '';
    return `performance:${modelId}${timeframePart}`;
  }
}

/**
 * Debounce utility for caching expensive operations
 */
export class DebouncedCache<T> {
  private cache: MemoryCache<T>;
  private pendingOperations = new Map<string, Promise<T>>();
  private debounceMs: number;

  constructor(defaultTTL: number = 30000, debounceMs: number = 1000) {
    this.cache = new MemoryCache<T>(defaultTTL);
    this.debounceMs = debounceMs;
  }

  /**
   * Get or compute a value with debouncing
   */
  async getOrCompute(
    key: string,
    computeFn: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    // Check if we have a cached value
    const cached = this.cache.get(key);
    if (cached !== undefined) {
      return cached;
    }

    // Check if there's already a pending operation for this key
    const pending = this.pendingOperations.get(key);
    if (pending) {
      return pending;
    }

    // Start a new operation
    const operation = this.executeWithDebounce(key, computeFn, ttl);
    this.pendingOperations.set(key, operation);

    try {
      const result = await operation;
      return result;
    } finally {
      this.pendingOperations.delete(key);
    }
  }

  private async executeWithDebounce(
    key: string,
    computeFn: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    // Wait for debounce period
    await new Promise(resolve => setTimeout(resolve, this.debounceMs));

    // Check again if value was cached during debounce
    const cached = this.cache.get(key);
    if (cached !== undefined) {
      return cached;
    }

    // Execute the computation
    const result = await computeFn();
    this.cache.set(key, result, ttl);
    return result;
  }

  /**
   * Clear all caches
   */
  clear(): void {
    this.cache.clear();
    this.pendingOperations.clear();
  }

  /**
   * Get cache statistics
   */
  getStats(): {
    cacheSize: number;
    pendingOperations: number;
    cacheKeys: string[];
  } {
    return {
      cacheSize: this.cache.size(),
      pendingOperations: this.pendingOperations.size,
      cacheKeys: this.cache.keys()
    };
  }
}

/**
 * Simple hash function for cache keys
 */
export function simpleHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash;
}

/**
 * Create a cache key from an object by hashing its JSON representation
 */
export function createHashedKey(prefix: string, obj: any): string {
  const jsonStr = JSON.stringify(obj, Object.keys(obj).sort());
  const hash = simpleHash(jsonStr);
  return `${prefix}:${hash}`;
}

/**
 * Cache decorator for methods (experimental)
 */
export function cached(ttl: number = 30000) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    const cache = new MemoryCache<any>(ttl);

    descriptor.value = async function (...args: any[]) {
      const cacheKey = createHashedKey(propertyKey, args);
      
      const cached = cache.get(cacheKey);
      if (cached !== undefined) {
        return cached;
      }

      const result = await originalMethod.apply(this, args);
      cache.set(cacheKey, result);
      return result;
    };

    return descriptor;
  };
}