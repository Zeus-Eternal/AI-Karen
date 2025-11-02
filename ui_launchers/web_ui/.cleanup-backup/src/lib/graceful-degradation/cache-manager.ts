/**
 * Cache manager for serving cached data when backend services are down
 */

export interface CacheEntry<T = any> {
  data: T;
  timestamp: number;
  expiresAt: number;
  version: string;
  metadata?: Record<string, any>;
}

export interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  maxAge?: number; // Maximum age before considering stale
  version?: string;
  metadata?: Record<string, any>;
}

export class CacheManager {
  private cache: Map<string, CacheEntry> = new Map();
  private persistentStorage: boolean;
  private storagePrefix: string = 'extension-cache-';

  constructor(persistentStorage: boolean = true) {
    this.persistentStorage = persistentStorage;
    if (persistentStorage) {
      this.loadFromStorage();
    }
  }

  private loadFromStorage(): void {
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith(this.storagePrefix)) {
          const cacheKey = key.substring(this.storagePrefix.length);
          const stored = localStorage.getItem(key);
          if (stored) {
            const entry: CacheEntry = JSON.parse(stored);
            this.cache.set(cacheKey, entry);
          }
        }
      }
    } catch (error) {
      console.warn('Failed to load cache from storage:', error);
    }
  }

  private saveToStorage(key: string, entry: CacheEntry): void {
    if (!this.persistentStorage) return;

    try {
      localStorage.setItem(
        this.storagePrefix + key,
        JSON.stringify(entry)
      );
    } catch (error) {
      console.warn(`Failed to save cache entry '${key}' to storage:`, error);
    }
  }

  private removeFromStorage(key: string): void {
    if (!this.persistentStorage) return;

    try {
      localStorage.removeItem(this.storagePrefix + key);
    } catch (error) {
      console.warn(`Failed to remove cache entry '${key}' from storage:`, error);
    }
  }

  set<T>(key: string, data: T, options: CacheOptions = {}): void {
    const now = Date.now();
    const ttl = options.ttl || 5 * 60 * 1000; // Default 5 minutes
    
    const entry: CacheEntry<T> = {
      data,
      timestamp: now,
      expiresAt: now + ttl,
      version: options.version || '1.0.0',
      metadata: options.metadata
    };

    this.cache.set(key, entry);
    this.saveToStorage(key, entry);
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    const now = Date.now();
    
    // Check if expired
    if (now > entry.expiresAt) {
      this.delete(key);
      return null;
    }

    return entry.data as T;
  }

  getWithMetadata<T>(key: string): { data: T; metadata: CacheEntry } | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    const now = Date.now();
    
    // Check if expired
    if (now > entry.expiresAt) {
      this.delete(key);
      return null;
    }

    return {
      data: entry.data as T,
      metadata: entry
    };
  }

  getStale<T>(key: string, maxAge?: number): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    // If maxAge is specified, check against it
    if (maxAge) {
      const now = Date.now();
      if (now - entry.timestamp > maxAge) {
        return null;
      }
    }

    return entry.data as T;
  }

  has(key: string): boolean {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return false;
    }

    const now = Date.now();
    
    // Check if expired
    if (now > entry.expiresAt) {
      this.delete(key);
      return false;
    }

    return true;
  }

  delete(key: string): boolean {
    const existed = this.cache.has(key);
    this.cache.delete(key);
    this.removeFromStorage(key);
    return existed;
  }

  clear(): void {
    // Clear memory cache
    this.cache.clear();

    // Clear persistent storage
    if (this.persistentStorage) {
      try {
        const keysToRemove: string[] = [];
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key?.startsWith(this.storagePrefix)) {
            keysToRemove.push(key);
          }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key));
      } catch (error) {
        console.warn('Failed to clear cache from storage:', error);
      }
    }
  }

  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  size(): number {
    return this.cache.size;
  }

  // Clean up expired entries
  cleanup(): number {
    const now = Date.now();
    let removedCount = 0;

    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.delete(key);
        removedCount++;
      }
    }

    return removedCount;
  }

  // Get cache statistics
  getStats(): {
    totalEntries: number;
    expiredEntries: number;
    totalSize: number;
    oldestEntry?: Date;
    newestEntry?: Date;
  } {
    const now = Date.now();
    let expiredCount = 0;
    let totalSize = 0;
    let oldestTimestamp = Infinity;
    let newestTimestamp = 0;

    for (const entry of this.cache.values()) {
      if (now > entry.expiresAt) {
        expiredCount++;
      }
      
      totalSize += JSON.stringify(entry.data).length;
      
      if (entry.timestamp < oldestTimestamp) {
        oldestTimestamp = entry.timestamp;
      }
      
      if (entry.timestamp > newestTimestamp) {
        newestTimestamp = entry.timestamp;
      }
    }

    return {
      totalEntries: this.cache.size,
      expiredEntries: expiredCount,
      totalSize,
      oldestEntry: oldestTimestamp !== Infinity ? new Date(oldestTimestamp) : undefined,
      newestEntry: newestTimestamp > 0 ? new Date(newestTimestamp) : undefined
    };
  }
}

// Specialized cache managers for different data types
export class ExtensionDataCache extends CacheManager {
  constructor() {
    super(true);
  }

  cacheExtensionList(extensions: any[]): void {
    this.set('extensions-list', extensions, {
      ttl: 10 * 60 * 1000, // 10 minutes
      version: '1.0.0',
      metadata: { type: 'extension-list', count: extensions.length }
    });
  }

  getCachedExtensionList(): any[] | null {
    return this.get('extensions-list');
  }

  cacheExtensionHealth(extensionName: string, health: any): void {
    this.set(`extension-health-${extensionName}`, health, {
      ttl: 2 * 60 * 1000, // 2 minutes
      version: '1.0.0',
      metadata: { type: 'extension-health', extensionName }
    });
  }

  getCachedExtensionHealth(extensionName: string): any | null {
    return this.get(`extension-health-${extensionName}`);
  }

  cacheBackgroundTasks(tasks: any[]): void {
    this.set('background-tasks', tasks, {
      ttl: 5 * 60 * 1000, // 5 minutes
      version: '1.0.0',
      metadata: { type: 'background-tasks', count: tasks.length }
    });
  }

  getCachedBackgroundTasks(): any[] | null {
    return this.get('background-tasks');
  }

  cacheModelProviders(providers: any[]): void {
    this.set('model-providers', providers, {
      ttl: 15 * 60 * 1000, // 15 minutes
      version: '1.0.0',
      metadata: { type: 'model-providers', count: providers.length }
    });
  }

  getCachedModelProviders(): any[] | null {
    return this.get('model-providers');
  }

  // Get stale data when fresh data is unavailable
  getStaleExtensionList(maxAge: number = 60 * 60 * 1000): any[] | null {
    return this.getStale('extensions-list', maxAge);
  }

  getStaleModelProviders(maxAge: number = 60 * 60 * 1000): any[] | null {
    return this.getStale('model-providers', maxAge);
  }
}

// Global cache instances
export const extensionCache = new ExtensionDataCache();
export const generalCache = new CacheManager(true);

// Cache-aware data fetcher
export class CacheAwareDataFetcher {
  constructor(
    private cache: CacheManager,
    private fetchFunction: (key: string) => Promise<any>
  ) {}

  async fetchWithCache<T>(
    key: string,
    options: CacheOptions & { 
      useStaleOnError?: boolean;
      maxStaleAge?: number;
    } = {}
  ): Promise<T> {
    // Try to get fresh data from cache first
    const cached = this.cache.get<T>(key);
    if (cached) {
      return cached;
    }

    try {
      // Fetch fresh data
      const data = await this.fetchFunction(key);
      
      // Cache the result
      this.cache.set(key, data, options);
      
      return data;
    } catch (error) {
      // If fetch fails and we allow stale data, try to get it
      if (options.useStaleOnError) {
        const staleData = this.cache.getStale<T>(key, options.maxStaleAge);
        if (staleData) {
          console.warn(`Using stale data for '${key}' due to fetch error:`, error);
          return staleData;
        }
      }
      
      throw error;
    }
  }
}