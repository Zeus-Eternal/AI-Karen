/**
 * Caching Strategies Implementation
 * Advanced caching system with multiple strategies and optimizations
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { CacheConfig, CacheEntry, UseCacheResult } from '../types';
import { usePerformanceOptimizationStore } from '../store/performanceOptimizationStore';

type CacheValue = unknown;

interface CacheStorageWithStats extends CacheStorage {
  getStats?: () => CacheStorageStats;
}

interface CacheStorageStats {
  entries: number;
  totalSize: number;
  averageSize: number;
  totalAccesses: number;
  averageAccesses: number;
  hitRate: number;
}

interface CacheManagerStats {
  hits: number;
  misses: number;
  sets: number;
  deletes: number;
  clears: number;
  hitRate: number;
  missRate: number;
  caches: Array<{
    name: string;
    stats: CacheStorageStats | null;
  }>;
}

// Cache storage interfaces
interface CacheStorage {
  get(key: string): Promise<CacheValue>;
  set(key: string, value: CacheValue, options?: CacheSetOptions): Promise<void>;
  remove(key: string): Promise<void>;
  clear(): Promise<void>;
  keys(): Promise<string[]>;
  size(): Promise<number>;
}

interface CacheSetOptions {
  ttl?: number; // Time to live in seconds
  compressionEnabled?: boolean;
  encryptionEnabled?: boolean;
  tags?: string[];
}

// Memory cache implementation
class MemoryCache implements CacheStorage {
  private cache = new Map<string, CacheEntry>();
  private maxSize: number;
  private defaultTTL: number;

  constructor(maxSize: number = 100, defaultTTL: number = 3600) {
    this.maxSize = maxSize;
    this.defaultTTL = defaultTTL;
  }

  async get(key: string): Promise<CacheValue> {
    const entry = this.cache.get(key);
    if (!entry) return null;

    // Check if expired
    if (new Date() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    // Update access statistics
    entry.accessCount++;
    entry.lastAccessed = new Date();

    return entry.value;
  }

  async set(key: string, value: CacheValue, options: CacheSetOptions = {}): Promise<void> {
    const now = new Date();
    const ttl = options.ttl || this.defaultTTL;
    const expiresAt = new Date(now.getTime() + ttl * 1000);
    
    const entry: CacheEntry = {
      key,
      value,
      timestamp: now,
      expiresAt,
      size: this.calculateSize(value),
      accessCount: 0,
      lastAccessed: now,
      metadata: {
        tags: options.tags || [],
        compressed: options.compressionEnabled || false,
        encrypted: options.encryptionEnabled || false,
      },
    };

    // Check if we need to evict entries
    if (this.cache.size >= this.maxSize) {
      this.evictLeastRecentlyUsed();
    }

    this.cache.set(key, entry);
  }

  async remove(key: string): Promise<void> {
    this.cache.delete(key);
  }

  async clear(): Promise<void> {
    this.cache.clear();
  }

  async keys(): Promise<string[]> {
    return Array.from(this.cache.keys());
  }

  async size(): Promise<number> {
    return this.cache.size;
  }

  private calculateSize(value: CacheValue): number {
    return JSON.stringify(value).length;
  }

  private evictLeastRecentlyUsed(): void {
    let lruKey: string | null = null;
    let oldestAccess = new Date();

    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccessed < oldestAccess) {
        oldestAccess = entry.lastAccessed;
        lruKey = key;
      }
    }

    if (lruKey) {
      this.cache.delete(lruKey);
    }
  }

  // Get cache statistics
  getStats(): CacheStorageStats {
    const entries = Array.from(this.cache.values());
    const totalSize = entries.reduce((sum, entry) => sum + entry.size, 0);
    const totalAccesses = entries.reduce((sum, entry) => sum + entry.accessCount, 0);
    
    return {
      entries: entries.length,
      totalSize,
      averageSize: entries.length > 0 ? totalSize / entries.length : 0,
      totalAccesses,
      averageAccesses: entries.length > 0 ? totalAccesses / entries.length : 0,
      hitRate: 0, // Would be calculated by the cache manager
    };
  }
}

// Local storage cache implementation
class LocalStorageCache implements CacheStorage {
  private prefix: string;
  private maxSize: number;
  private defaultTTL: number;

  constructor(prefix: string = 'cache_', maxSize: number = 50, defaultTTL: number = 3600) {
    this.prefix = prefix;
    this.maxSize = maxSize;
    this.defaultTTL = defaultTTL;
  }

  private getKey(key: string): string {
    return `${this.prefix}${key}`;
  }

  async get(key: string): Promise<CacheValue> {
    try {
      const item = localStorage.getItem(this.getKey(key));
      if (!item) return null;

      const entry: CacheEntry = JSON.parse(item);
      
      // Check if expired
      if (new Date() > new Date(entry.expiresAt)) {
        localStorage.removeItem(this.getKey(key));
        return null;
      }

      // Update access statistics
      entry.accessCount++;
      entry.lastAccessed = new Date();
      
      // Save updated access stats
      localStorage.setItem(this.getKey(key), JSON.stringify(entry));

      return entry.value;
    } catch (error) {
      console.error('LocalStorage get error:', error);
      return null;
    }
  }

  async set(key: string, value: CacheValue, options: CacheSetOptions = {}): Promise<void> {
    try {
      const now = new Date();
      const ttl = options.ttl || this.defaultTTL;
      const expiresAt = new Date(now.getTime() + ttl * 1000);
      
      const entry: CacheEntry = {
        key,
        value,
        timestamp: now,
        expiresAt,
        size: this.calculateSize(value),
        accessCount: 0,
        lastAccessed: now,
        metadata: {
          tags: options.tags || [],
          compressed: options.compressionEnabled || false,
          encrypted: options.encryptionEnabled || false,
        },
      };

      // Check if we need to evict entries
      if (await this.size() >= this.maxSize) {
        await this.evictLeastRecentlyUsed();
      }

      localStorage.setItem(this.getKey(key), JSON.stringify(entry));
    } catch (error) {
      console.error('LocalStorage set error:', error);
    }
  }

  async remove(key: string): Promise<void> {
    try {
      localStorage.removeItem(this.getKey(key));
    } catch (error) {
      console.error('LocalStorage remove error:', error);
    }
  }

  async clear(): Promise<void> {
    try {
      const keys = await this.keys();
      for (const key of keys) {
        localStorage.removeItem(this.getKey(key));
      }
    } catch (error) {
      console.error('LocalStorage clear error:', error);
    }
  }

  async keys(): Promise<string[]> {
    try {
      const keys: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.prefix)) {
          keys.push(key.substring(this.prefix.length));
        }
      }
      return keys;
    } catch (error) {
      console.error('LocalStorage keys error:', error);
      return [];
    }
  }

  async size(): Promise<number> {
    return (await this.keys()).length;
  }

  private calculateSize(value: CacheValue): number {
    return JSON.stringify(value).length;
  }

  private async evictLeastRecentlyUsed(): Promise<void> {
    try {
      const keys = await this.keys();
      let lruKey: string | null = null;
      let oldestAccess = new Date();

      for (const key of keys) {
        const item = localStorage.getItem(this.getKey(key));
        if (item) {
          const entry: CacheEntry = JSON.parse(item);
          if (new Date(entry.lastAccessed) < oldestAccess) {
            oldestAccess = new Date(entry.lastAccessed);
            lruKey = key;
          }
        }
      }

      if (lruKey) {
        localStorage.removeItem(this.getKey(lruKey));
      }
    } catch (error) {
      console.error('LocalStorage eviction error:', error);
    }
  }
}

// IndexedDB cache implementation for larger datasets
class IndexedDBCache implements CacheStorage {
  private dbName: string;
  private storeName: string;
  private version: number;
  private db: IDBDatabase | null = null;

  constructor(dbName: string = 'performanceCache', storeName: string = 'cache', version: number = 1) {
    this.dbName = dbName;
    this.storeName = storeName;
    this.version = version;
  }

  private async initDB(): Promise<IDBDatabase> {
    if (this.db) return this.db;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve(this.db);
      };

      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, { keyPath: 'key' });
          store.createIndex('expiresAt', 'expiresAt', { unique: false });
          store.createIndex('lastAccessed', 'lastAccessed', { unique: false });
        }
      };
    });
  }

  async get(key: string): Promise<CacheValue> {
    const db = await this.initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const request = store.get(key);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const entry: CacheEntry = request.result;
        if (!entry) {
          resolve(null);
          return;
        }

        // Check if expired
        if (new Date() > new Date(entry.expiresAt)) {
          this.remove(key);
          resolve(null);
          return;
        }

        // Update access statistics
        entry.accessCount++;
        entry.lastAccessed = new Date();
        
        // Save updated access stats
        const updateTransaction = db.transaction([this.storeName], 'readwrite');
        const updateStore = updateTransaction.objectStore(this.storeName);
        updateStore.put(entry);

        resolve(entry.value);
      };
    });
  }

  async set(key: string, value: CacheValue, options: CacheSetOptions = {}): Promise<void> {
    const db = await this.initDB();
    
    return new Promise((resolve, reject) => {
      const now = new Date();
      const ttl = options.ttl || 3600;
      const expiresAt = new Date(now.getTime() + ttl * 1000);
      
      const entry: CacheEntry = {
        key,
        value,
        timestamp: now,
        expiresAt,
        size: this.calculateSize(value),
        accessCount: 0,
        lastAccessed: now,
        metadata: {
          tags: options.tags || [],
          compressed: options.compressionEnabled || false,
          encrypted: options.encryptionEnabled || false,
        },
      };

      const transaction = db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.put(entry);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async remove(key: string): Promise<void> {
    const db = await this.initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.delete(key);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async clear(): Promise<void> {
    const db = await this.initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.clear();

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async keys(): Promise<string[]> {
    const db = await this.initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const request = store.getAllKeys();

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result as string[]);
    });
  }

  async size(): Promise<number> {
    const db = await this.initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const request = store.count();

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  private calculateSize(value: CacheValue): number {
    return JSON.stringify(value).length;
  }
}

// Cache manager that handles multiple strategies
class CacheManager {
  private caches: Map<string, CacheStorage> = new Map();
  private config: CacheConfig;
  private stats: {
    hits: number;
    misses: number;
    sets: number;
    deletes: number;
    clears: number;
  } = {
    hits: 0,
    misses: 0,
    sets: 0,
    deletes: 0,
    clears: 0,
  };

  constructor(config: CacheConfig) {
    this.config = config;
    this.initializeCaches();
  }

  private initializeCaches(): void {
    switch (this.config.strategy) {
      case 'memory':
        this.caches.set('memory', new MemoryCache());
        break;
      case 'disk':
        this.caches.set('disk', this.createDiskCache());
        break;
      case 'service-worker':
        // Service worker cache would be initialized here
        console.warn('Service worker cache not implemented in this demo');
        this.caches.set('memory', new MemoryCache());
        break;
      case 'hybrid':
        // Use memory for fast access and localStorage for persistence
        this.caches.set('memory', new MemoryCache(50));
        this.caches.set('disk', this.createDiskCache());
        break;
      default:
        this.caches.set('memory', new MemoryCache());
    }
  }

  private createDiskCache(): CacheStorage {
    if (typeof indexedDB !== 'undefined') {
      return new IndexedDBCache();
    }

    return new LocalStorageCache('perf_', 100);
  }

  async get(key: string): Promise<CacheValue> {
    const startTime = performance.now();
    
    try {
      // Try memory cache first
      if (this.caches.has('memory')) {
        const memoryCache = this.caches.get('memory')!;
        const value = await memoryCache.get(key);
        
        if (value !== null) {
          this.stats.hits++;
          this.recordMetric('cache-hit', performance.now() - startTime);
          return value;
        }
      }

      // Try disk cache if memory miss
      if (this.caches.has('disk')) {
        const diskCache = this.caches.get('disk')!;
        const value = await diskCache.get(key);
        
        if (value !== null) {
          this.stats.hits++;
          this.recordMetric('cache-hit', performance.now() - startTime);
          
          // Store in memory cache for faster future access
          if (this.caches.has('memory')) {
            const memoryCache = this.caches.get('memory')!;
            await memoryCache.set(key, value, { ttl: 300 }); // 5 minutes in memory
          }
          
          return value;
        }
      }

      this.stats.misses++;
      this.recordMetric('cache-miss', performance.now() - startTime);
      return null;
    } catch (error) {
      console.error('Cache get error:', error);
      this.stats.misses++;
      return null;
    }
  }

  async set(key: string, value: CacheValue, options: CacheSetOptions = {}): Promise<void> {
    const startTime = performance.now();
    
    try {
      // Store in all configured caches
      const promises = Array.from(this.caches.entries()).map(async ([, cache]) => {
        await cache.set(key, value, options);
      });

      await Promise.allSettled(promises);
      
      this.stats.sets++;
      this.recordMetric('cache-set', performance.now() - startTime);
    } catch (error) {
      console.error('Cache set error:', error);
    }
  }

  async remove(key: string): Promise<void> {
    const startTime = performance.now();
    
    try {
      // Remove from all configured caches
      const promises = Array.from(this.caches.entries()).map(async ([, cache]) => {
        await cache.remove(key);
      });

      await Promise.allSettled(promises);
      
      this.stats.deletes++;
      this.recordMetric('cache-delete', performance.now() - startTime);
    } catch (error) {
      console.error('Cache remove error:', error);
    }
  }

  async clear(): Promise<void> {
    const startTime = performance.now();
    
    try {
      // Clear all configured caches
      const promises = Array.from(this.caches.entries()).map(async ([, cache]) => {
        await cache.clear();
      });

      await Promise.allSettled(promises);
      
      this.stats.clears++;
      this.recordMetric('cache-clear', performance.now() - startTime);
    } catch (error) {
      console.error('Cache clear error:', error);
    }
  }

  async getByTag(tag: string): Promise<Map<string, CacheValue>> {
    void tag;
    const results = new Map<string, CacheValue>();
    
    // This would need to be implemented based on the cache storage
    // For now, we'll just return empty map
    return results;
  }

  async removeByTag(tag: string): Promise<void> {
    void tag;
    // This would need to be implemented based on the cache storage
    console.warn('Tag-based removal not implemented in this demo');
  }

  getStats(): CacheManagerStats {
    const hitRate = this.stats.hits + this.stats.misses > 0 
      ? (this.stats.hits / (this.stats.hits + this.stats.misses)) * 100 
      : 0;

    return {
      ...this.stats,
      hitRate: Math.round(hitRate),
      missRate: Math.round(100 - hitRate),
      caches: Array.from(this.caches.entries()).map(([name, cache]) => ({
        name,
        stats: (cache as CacheStorageWithStats).getStats?.() ?? null,
      })),
    };
  }

  updateConfig(config: Partial<CacheConfig>): void {
    this.config = { ...this.config, ...config };
    
    // Reinitialize caches if strategy changed
    if (config.strategy) {
      this.caches.clear();
      this.initializeCaches();
    }
  }

  private recordMetric(name: string, duration: number): void {
    const store = usePerformanceOptimizationStore.getState();
    store.measureMetric({
      name,
      value: duration,
      unit: 'ms',
      timestamp: new Date(),
      rating: duration < 10 ? 'good' : duration < 50 ? 'needs-improvement' : 'poor',
      threshold: { good: 10, poor: 50 },
    });
  }
}

// Hook for using cache
export function useCache<T = unknown>(
  key: string,
  options?: {
    ttl?: number;
    compressionEnabled?: boolean;
    encryptionEnabled?: boolean;
    tags?: string[];
  }
): UseCacheResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const cacheManagerRef = useRef<CacheManager | null>(null);
  const store = usePerformanceOptimizationStore();

  // Initialize cache manager
  useEffect(() => {
    const config = store.cacheConfig;
    cacheManagerRef.current = new CacheManager(config);
  }, [store.cacheConfig]);

  const get = useCallback(async (): Promise<T | null> => {
    if (!cacheManagerRef.current) return null;
    
    setIsLoading(true);
    setHasError(false);
    setError(null);

    try {
      const result = await cacheManagerRef.current.get(key);
      setData(result);
      return result;
    } catch (err) {
      setHasError(true);
      setError(err as Error);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [key]);

  const set = useCallback(async (value: T, ttl?: number): Promise<void> => {
    if (!cacheManagerRef.current) return;
    
    setIsLoading(true);
    setHasError(false);
    setError(null);

    try {
      await cacheManagerRef.current.set(key, value, {
        ttl: ttl || options?.ttl,
        compressionEnabled: options?.compressionEnabled,
        encryptionEnabled: options?.encryptionEnabled,
        tags: options?.tags,
      });
      setData(value);
    } catch (err) {
      setHasError(true);
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [key, options]);

  const remove = useCallback(async (): Promise<void> => {
    if (!cacheManagerRef.current) return;
    
    setIsLoading(true);
    setHasError(false);
    setError(null);

    try {
      await cacheManagerRef.current.remove(key);
      setData(null);
    } catch (err) {
      setHasError(true);
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [key]);

  const clear = useCallback(async (): Promise<void> => {
    if (!cacheManagerRef.current) return;
    
    setIsLoading(true);
    setHasError(false);
    setError(null);

    try {
      await cacheManagerRef.current.clear();
      setData(null);
    } catch (err) {
      setHasError(true);
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Auto-load on mount
  useEffect(() => {
    get();
  }, [get]);

  return {
    data,
    isLoading,
    hasError,
    error,
    set,
    get: get as () => T | null,
    remove,
    clear,
  };
}

// Hook for cache statistics
export function useCacheStats() {
  const [stats, setStats] = useState<CacheManagerStats | null>(null);
  const cacheManagerRef = useRef<CacheManager | null>(null);
  const store = usePerformanceOptimizationStore();

  useEffect(() => {
    const config = store.cacheConfig;
    cacheManagerRef.current = new CacheManager(config);
    
    // Update stats periodically
    const interval = setInterval(() => {
      if (cacheManagerRef.current) {
        setStats(cacheManagerRef.current.getStats());
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [store.cacheConfig]);

  return stats;
}

// Export cache manager instance
export const cacheManager = new CacheManager({
  strategy: 'hybrid',
  maxSize: 50,
  ttl: 3600,
  compressionEnabled: true,
  encryptionEnabled: false,
});

// Utility functions for cache management
export async function preloadCache(entries: Array<{ key: string; value: CacheValue; options?: CacheSetOptions }>): Promise<void> {
  const promises = entries.map(entry => 
    cacheManager.set(entry.key, entry.value, entry.options)
  );
  
  await Promise.allSettled(promises);
}

export async function warmupCache(keys: string[]): Promise<void> {
  // This would typically fetch data from APIs and store in cache
  console.log('Warming up cache for keys:', keys);
}

export function invalidateCachePattern(pattern: string): void {
  // This would invalidate cache entries matching a pattern
  console.log('Invalidating cache pattern:', pattern);
}
