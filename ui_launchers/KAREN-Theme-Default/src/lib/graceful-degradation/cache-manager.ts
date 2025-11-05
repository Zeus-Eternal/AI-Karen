// apps/web/src/services/runtime/cache-manager.ts
/**
 * Cache manager for serving cached data when backend services are down.
 * - SSR-safe (no localStorage on server)
 * - Version-aware entries with TTL + stale reads on demand
 * - Binary-safe size math, cleanup & stats
 * - Strong typing and guardrails
 */

export interface CacheEntry<T = any> {
  data: T;
  timestamp: number;   // when inserted
  expiresAt: number;   // hard expiry timestamp
  version: string;     // entry schema/app version guard
  metadata?: Record<string, any>;
}

export interface CacheOptions {
  ttl?: number;          // time to live in ms (default 5 minutes)
  maxAge?: number;       // optional: treat entries older than this as stale (soft)
  version?: string;      // app/schema version; mismatch invalidates cached entry
  metadata?: Record<string, any>;
}

type Stats = {
  totalEntries: number;
  expiredEntries: number;
  totalSize: number;         // approximate bytes (UTF-8)
  oldestEntry?: Date;
  newestEntry?: Date;
};

const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes
const STORAGE_PREFIX = "extension-cache-";

/** SSR/browser guards */
const hasWindow = typeof window !== "undefined";
const hasLocalStorage =
  hasWindow &&
  (() => {
    try {
      const k = "__km_probe__";
      window.localStorage.setItem(k, "1");
      window.localStorage.removeItem(k);
      return true;
    } catch {
      return false;
    }
  })();

/** UTF-8 length approximation for size stats */
const utf8Length = (s: string) => new Blob([s]).size;

export class CacheManager {
  private cache: Map<string, CacheEntry> = new Map();
  private readonly persistentStorage: boolean;
  private readonly storagePrefix: string;

  constructor(persistentStorage: boolean = true, storagePrefix: string = STORAGE_PREFIX) {
    this.persistentStorage = persistentStorage && hasLocalStorage;
    this.storagePrefix = storagePrefix;

    if (this.persistentStorage) {
      this.loadFromStorage();
      // prune immediately on load
      this.cleanup();
    }
  }

  /** ---------- Storage I/O ---------- */

  private loadFromStorage(): void {
    try {
      const ls = window.localStorage;
      for (let i = 0; i < ls.length; i++) {
        const key = ls.key(i);
        if (!key || !key.startsWith(this.storagePrefix)) continue;
        const cacheKey = key.substring(this.storagePrefix.length);
        const raw = ls.getItem(key);
        if (!raw) continue;
        try {
          const entry: CacheEntry = JSON.parse(raw);
          // basic structural guard
          if (entry && typeof entry === "object" && typeof entry.expiresAt === "number") {
            this.cache.set(cacheKey, entry);
          }
        } catch {
          // corrupted entry; drop it
          ls.removeItem(key);
        }
      }
    } catch {
      // ignore storage access issues (private mode/blocked)
    }
  }

  private saveToStorage(key: string, entry: CacheEntry): void {
    if (!this.persistentStorage) return;
    try {
      window.localStorage.setItem(this.storagePrefix + key, JSON.stringify(entry));
    } catch {
      // quota errors or blocked; degrade to memory-only
    }
  }

  private removeFromStorage(key: string): void {
    if (!this.persistentStorage) return;
    try {
      window.localStorage.removeItem(this.storagePrefix + key);
    } catch {
      // ignore
    }
  }

  /** ---------- Core API ---------- */

  set<T>(key: string, data: T, options: CacheOptions = {}): void {
    const now = Date.now();
    const ttl = options.ttl ?? DEFAULT_TTL;
    const entry: CacheEntry<T> = {
      data,
      timestamp: now,
      expiresAt: now + ttl,
      version: options.version ?? "1.0.0",
      metadata: options.metadata,
    };
    this.cache.set(key, entry);
    this.saveToStorage(key, entry);
  }

  /** Returns null if missing, expired, or version-mismatched (if version supplied) */
  get<T>(key: string, version?: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    // version guard (if caller provides expected version)
    if (version && entry.version !== version) {
      this.delete(key);
      return null;
    }

    // hard expiry
    const now = Date.now();
    if (now > entry.expiresAt) {
      this.delete(key);
      return null;
    }
    return entry.data as T;
  }

  /** Same as get(), but returns metadata wrapper */
  getWithMetadata<T>(key: string, version?: string): { data: T; metadata: CacheEntry } | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (version && entry.version !== version) {
      this.delete(key);
      return null;
    }
    const now = Date.now();
    if (now > entry.expiresAt) {
      this.delete(key);
      return null;
    }
    return { data: entry.data as T, metadata: entry };
  }

  /**
   * Stale read: ignores hard expiry but enforces optional maxAge (soft).
   * Useful for "stale-while-revalidate" or degraded-mode UX.
   */
  getStale<T>(key: string, maxAge?: number, version?: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (version && entry.version !== version) return null;

    if (typeof maxAge === "number") {
      const now = Date.now();
      if (now - entry.timestamp > maxAge) return null;
    }
    return entry.data as T;
  }

  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;
    const now = Date.now();
    if (now > entry.expiresAt) {
      this.delete(key);
      return false;
    }
    return true;
  }

  delete(key: string): boolean {
    const existed = this.cache.delete(key);
    if (existed) this.removeFromStorage(key);
    return existed;
  }

  clear(): void {
    this.cache.clear();
    if (this.persistentStorage) {
      try {
        const ls = window.localStorage;
        const toRemove: string[] = [];
        for (let i = 0; i < ls.length; i++) {
          const k = ls.key(i);
          if (k?.startsWith(this.storagePrefix)) toRemove.push(k);
        }
        toRemove.forEach((k) => ls.removeItem(k));
      } catch {
        // ignore
      }
    }
  }

  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  size(): number {
    return this.cache.size;
  }

  /** Remove expired entries; returns count removed */
  cleanup(): number {
    const now = Date.now();
    let removed = 0;
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.delete(key);
        removed++;
      }
    }
    return removed;
  }

  /** Stats for observability/UX */
  getStats(): Stats {
    const now = Date.now();
    let expired = 0;
    let totalSize = 0;
    let oldest = Infinity;
    let newest = 0;

    for (const entry of this.cache.values()) {
      if (now > entry.expiresAt) expired++;
      try {
        totalSize += utf8Length(JSON.stringify(entry.data));
      } catch {
        // non-serializable custom objects: fall back to zero
      }
      if (entry.timestamp < oldest) oldest = entry.timestamp;
      if (entry.timestamp > newest) newest = entry.timestamp;
    }

    return {
      totalEntries: this.cache.size,
      expiredEntries: expired,
      totalSize,
      oldestEntry: oldest !== Infinity ? new Date(oldest) : undefined,
      newestEntry: newest > 0 ? new Date(newest) : undefined,
    };
  }
}

/** ---------- Specialized extension cache ---------- */

export class ExtensionDataCache extends CacheManager {
  constructor() {
    super(true, STORAGE_PREFIX);
  }

  cacheExtensionList(extensions: any[]): void {
    this.set("extensions-list", extensions, {
      ttl: 10 * 60 * 1000,
      version: "1.0.0",
      metadata: { type: "extension-list", count: extensions.length },
    });
  }

  getCachedExtensionList(version?: string): any[] | null {
    return this.get<any[]>("extensions-list", version);
  }

  cacheExtensionHealth(extensionName: string, health: any): void {
    this.set(`extension-health-${extensionName}`, health, {
      ttl: 2 * 60 * 1000,
      version: "1.0.0",
      metadata: { type: "extension-health", extensionName },
    });
  }

  getCachedExtensionHealth(extensionName: string, version?: string): any | null {
    return this.get<any>(`extension-health-${extensionName}`, version);
  }

  cacheBackgroundTasks(tasks: any[]): void {
    this.set("background-tasks", tasks, {
      ttl: 5 * 60 * 1000,
      version: "1.0.0",
      metadata: { type: "background-tasks", count: tasks.length },
    });
  }

  getCachedBackgroundTasks(version?: string): any[] | null {
    return this.get<any[]>("background-tasks", version);
  }

  cacheModelProviders(providers: any[]): void {
    this.set("model-providers", providers, {
      ttl: 15 * 60 * 1000,
      version: "1.0.0",
      metadata: { type: "model-providers", count: providers.length },
    });
  }

  getCachedModelProviders(version?: string): any[] | null {
    return this.get<any[]>("model-providers", version);
  }

  // Stale reads for degraded mode
  getStaleExtensionList(maxAge: number = 60 * 60 * 1000, version?: string): any[] | null {
    return this.getStale<any[]>("extensions-list", maxAge, version);
  }

  getStaleModelProviders(maxAge: number = 60 * 60 * 1000, version?: string): any[] | null {
    return this.getStale<any[]>("model-providers", maxAge, version);
  }
}

/** Global instances (opt-in to persistence for general cache as well) */
export const extensionCache = new ExtensionDataCache();
export const generalCache = new CacheManager(true);

/** ---------- Cache-aware fetch wrapper ---------- */

export class CacheAwareDataFetcher {
  constructor(
    private cache: CacheManager,
    private fetchFunction: (key: string) => Promise<any>
  ) {}

  /**
   * Fetch with cache:
   * 1) Return fresh cached (if valid)
   * 2) Otherwise fetch, cache, and return
   * 3) On fetch error, optionally return stale value (useStaleOnError)
   */
  async fetchWithCache<T>(
    key: string,
    options: CacheOptions & {
      useStaleOnError?: boolean;
      maxStaleAge?: number;
    } = {}
  ): Promise<T> {
    const fresh = this.cache.get<T>(key, options.version);
    if (fresh !== null) return fresh;

    try {
      const data = await this.fetchFunction(key);
      this.cache.set<T>(key, data, options);
      return data;
    } catch (error) {
      if (options.useStaleOnError) {
        const stale = this.cache.getStale<T>(key, options.maxStaleAge, options.version);
        if (stale !== null) return stale;
      }
      throw error;
    }
  }
}
