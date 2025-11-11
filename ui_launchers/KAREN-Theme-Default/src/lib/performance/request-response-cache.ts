/**
 * Request/Response Cache Manager
 * 
 * Implements intelligent caching for HTTP requests and responses to improve performance.
 * Provides cache invalidation, TTL management, and memory-efficient storage.
 * 
 * Requirements: 1.4, 4.4
 */
export interface CacheConfig {
  maxSize: number;
  defaultTtl: number;
  maxMemoryUsage: number; // in bytes
  enableCompression: boolean;
  enablePersistence: boolean;
  persistenceKey: string;
}
export interface CacheEntry<Data = unknown> {
  key: string;
  data: Data;
  headers: Record<string, string>;
  status: number;
  timestamp: number;
  ttl: number;
  accessCount: number;
  lastAccessed: number;
  size: number;
  compressed: boolean;
}
export interface CacheMetrics {
  totalEntries: number;
  memoryUsage: number;
  hitRate: number;
  missRate: number;
  totalRequests: number;
  cacheHits: number;
  cacheMisses: number;
  evictions: number;
  compressionRatio: number;
}
export interface CacheOptions {
  ttl?: number;
  tags?: string[];
  compress?: boolean;
  persist?: boolean;
  skipCache?: boolean;
  cacheKey?: string;
}
/**
 * Request/Response Cache Manager
 * 
 * Provides intelligent caching with LRU eviction, compression, and persistence.
 */
export class RequestResponseCache {
  private config: CacheConfig;
  private cache: Map<string, CacheEntry> = new Map();
  private accessOrder: string[] = [];
  private tagIndex: Map<string, Set<string>> = new Map();
  private metrics: CacheMetrics;
  private cleanupInterval: NodeJS.Timeout | null = null;
  constructor(config?: Partial<CacheConfig>) {
    this.config = {
      maxSize: 1000,
      defaultTtl: 300000, // 5 minutes
      maxMemoryUsage: 50 * 1024 * 1024, // 50MB
      enableCompression: true,
      enablePersistence: false,
      persistenceKey: 'ai-karen-request-cache',
      ...config,
    };
    this.metrics = {
      totalEntries: 0,
      memoryUsage: 0,
      hitRate: 0,
      missRate: 0,
      totalRequests: 0,
      cacheHits: 0,
      cacheMisses: 0,
      evictions: 0,
      compressionRatio: 0,
    };
    this.startCleanupTimer();
    this.loadFromPersistence();
  }
  /**
   * Get cached response for a request
   */
  async get(key: string, options?: CacheOptions): Promise<CacheEntry | null> {
    this.metrics.totalRequests++;
    if (options?.skipCache) {
      this.metrics.cacheMisses++;
      return null;
    }
    const cacheKey = options?.cacheKey || this.generateCacheKey(key);
    const entry = this.cache.get(cacheKey);
    if (!entry) {
      this.metrics.cacheMisses++;
      return null;
    }
    // Check if entry is expired
    if (this.isExpired(entry)) {
      this.delete(cacheKey);
      this.metrics.cacheMisses++;
      return null;
    }
    // Update access information
    entry.accessCount++;
    entry.lastAccessed = Date.now();
    this.updateAccessOrder(cacheKey);
    this.metrics.cacheHits++;
    this.updateHitRate();
    // Decompress data if needed
    if (entry.compressed && this.config.enableCompression) {
      entry.data = await this.decompress(entry.data as Uint8Array);
      entry.compressed = false;
    }
    return { ...entry };
  }
  /**
   * Store response in cache
   */
  async set(
    key: string,
    data: unknown,
    headers: Record<string, string> = {},
    status: number = 200,
    options?: CacheOptions
  ): Promise<void> {
    if (options?.skipCache) {
      return;
    }
    const cacheKey = options?.cacheKey || this.generateCacheKey(key);
    const ttl = options?.ttl || this.getTtlFromHeaders(headers) || this.config.defaultTtl;
    const timestamp = Date.now();
    // Prepare data for storage
    let processedData = data;
    let compressed = false;
    let size = this.estimateSize(data);
    // Compress data if enabled and beneficial
    if (this.config.enableCompression && options?.compress !== false && size > 1024) {
    try {
      processedData = await this.compress(data);
        const compressedSize = this.estimateSize(processedData);
        if (compressedSize < size * 0.8) { // Only use compression if it saves at least 20%
          size = compressedSize;
          compressed = true;
        } else {
          processedData = data; // Revert to original if compression not beneficial
        }
    } catch {
      processedData = data;
    }
    }
    const entry: CacheEntry = {
      key: cacheKey,
      data: processedData,
      headers,
      status,
      timestamp,
      ttl,
      accessCount: 1,
      lastAccessed: timestamp,
      size,
      compressed,
    };
    // Check if we need to evict entries
    await this.ensureCapacity(size);
    // Store the entry
    this.cache.set(cacheKey, entry);
    this.updateAccessOrder(cacheKey);
    // Update tag index
    if (options?.tags) {
      for (const tag of options.tags) {
        if (!this.tagIndex.has(tag)) {
          this.tagIndex.set(tag, new Set());
        }
        this.tagIndex.get(tag)!.add(cacheKey);
      }
    }
    // Update metrics
    this.metrics.totalEntries = this.cache.size;
    this.metrics.memoryUsage += size;
    this.updateCompressionRatio();
    // Persist if enabled
    if (this.config.enablePersistence && options?.persist !== false) {
      this.saveToPersistence();
    }
  }
  /**
   * Delete entry from cache
   */
  delete(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) {
      return false;
    }
    // Remove from cache
    this.cache.delete(key);
    // Remove from access order
    const index = this.accessOrder.indexOf(key);
    if (index !== -1) {
      this.accessOrder.splice(index, 1);
    }
    // Remove from tag index
    const emptyTags: string[] = [];
    this.tagIndex.forEach((keys, tag) => {
      keys.delete(key);
      if (keys.size === 0) {
        emptyTags.push(tag);
      }
    });
    emptyTags.forEach(tag => {
      this.tagIndex.delete(tag);
    });
    // Update metrics
    this.metrics.totalEntries = this.cache.size;
    this.metrics.memoryUsage -= entry.size;
    return true;
  }
  /**
   * Clear cache by tags
   */
  clearByTags(tags: string[]): number {
    let cleared = 0;
    tags.forEach(tag => {
      const keys = this.tagIndex.get(tag);
      if (keys) {
        keys.forEach(cacheKey => {
          if (this.delete(cacheKey)) {
            cleared++;
          }
        });
      }
    });
    return cleared;
  }
  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.accessOrder.length = 0;
    this.tagIndex.clear();
    this.metrics.totalEntries = 0;
    this.metrics.memoryUsage = 0;
    this.metrics.evictions = 0;
    if (this.config.enablePersistence) {
      this.clearPersistence();
    }
  }
  /**
   * Get cache metrics
   */
  getMetrics(): CacheMetrics {
    this.updateHitRate();
    return { ...this.metrics };
  }
  /**
   * Get cache configuration
   */
  getConfig(): CacheConfig {
    return { ...this.config };
  }
  /**
   * Shutdown the cache
   */
  shutdown(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    if (this.config.enablePersistence) {
      this.saveToPersistence();
    }
    this.clear();
  }
  /**
   * Generate cache key from request details
   */
  private generateCacheKey(key: string): string {
    // Simple hash function for cache key
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      const char = key.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return `cache_${Math.abs(hash).toString(36)}`;
  }
  /**
   * Check if cache entry is expired
   */
  private isExpired(entry: CacheEntry): boolean {
    return Date.now() - entry.timestamp > entry.ttl;
  }
  /**
   * Get TTL from response headers
   */
  private getTtlFromHeaders(headers: Record<string, string>): number | null {
    const cacheControl = headers['cache-control'] || headers['Cache-Control'];
    if (cacheControl) {
      const maxAgeMatch = cacheControl.match(/max-age=(\d+)/);
      if (maxAgeMatch) {
        return parseInt(maxAgeMatch[1]) * 1000; // Convert to milliseconds
      }
    }
    const expires = headers['expires'] || headers['Expires'];
    if (expires) {
      const expiresDate = new Date(expires);
      if (!isNaN(expiresDate.getTime())) {
        return expiresDate.getTime() - Date.now();
      }
    }
    return null;
  }
  /**
   * Update access order for LRU eviction
   */
  private updateAccessOrder(key: string): void {
    const index = this.accessOrder.indexOf(key);
    if (index !== -1) {
      this.accessOrder.splice(index, 1);
    }
    this.accessOrder.push(key);
  }
  /**
   * Ensure cache capacity by evicting entries if needed
   */
  private async ensureCapacity(newEntrySize: number): Promise<void> {
    // Check size limit
    while (
      this.cache.size >= this.config.maxSize ||
      this.metrics.memoryUsage + newEntrySize > this.config.maxMemoryUsage
    ) {
      if (this.accessOrder.length === 0) {
        break; // No entries to evict
      }
      // Evict least recently used entry
      const lruKey = this.accessOrder[0];
      if (this.delete(lruKey)) {
        this.metrics.evictions++;
      }
    }
  }
  /**
   * Estimate size of data in bytes
   */
  private estimateSize(data: unknown): number {
    if (typeof data === 'string') {
      return data.length * 2; // Rough estimate for UTF-16
    }
    if (data instanceof ArrayBuffer) {
      return data.byteLength;
    }
    if (data instanceof Uint8Array) {
      return data.length;
    }
    // For objects, use JSON string length as approximation
    try {
      return JSON.stringify(data).length * 2;
    } catch {
      return 1024; // Default estimate
    }
  }
  /**
   * Compress data using built-in compression
   */
  private async compress(data: unknown): Promise<Uint8Array> {
    if (typeof CompressionStream === 'undefined') {
      throw new Error('Compression not supported');
    }
    const stream = new CompressionStream('gzip');
    const writer = stream.writable.getWriter();
    const reader = stream.readable.getReader();
    // Convert data to Uint8Array
    const encoder = new TextEncoder();
    const input = typeof data === 'string' ? encoder.encode(data) : encoder.encode(JSON.stringify(data));
    // Compress
    writer.write(input);
    writer.close();
    // Read compressed data
    const chunks: Uint8Array[] = [];
    let done = false;
    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        chunks.push(value);
      }
    }
    // Combine chunks
    const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
    const result = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      result.set(chunk, offset);
      offset += chunk.length;
    }
    return result;
  }
  /**
   * Decompress data
   */
  private async decompress(compressedData: Uint8Array): Promise<unknown> {
    if (typeof DecompressionStream === 'undefined') {
      throw new Error('Decompression not supported');
    }
    const stream = new DecompressionStream('gzip');
    const writer = stream.writable.getWriter();
    const reader = stream.readable.getReader();
    // Decompress
    writer.write(compressedData as BufferSource);
    writer.close();
    // Read decompressed data
    const chunks: Uint8Array[] = [];
    let done = false;
    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        chunks.push(value);
      }
    }
    // Combine chunks and decode
    const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
    const result = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      result.set(chunk, offset);
      offset += chunk.length;
    }
    const decoder = new TextDecoder();
    const decompressed = decoder.decode(result);
    try {
      return JSON.parse(decompressed);
    } catch {
      return decompressed;
    }
  }
  /**
   * Update hit rate metrics
   */
  private updateHitRate(): void {
    if (this.metrics.totalRequests > 0) {
      this.metrics.hitRate = this.metrics.cacheHits / this.metrics.totalRequests;
      this.metrics.missRate = this.metrics.cacheMisses / this.metrics.totalRequests;
    }
  }
  /**
   * Update compression ratio metrics
   */
  private updateCompressionRatio(): void {
    let totalOriginalSize = 0;
    let totalCompressedSize = 0;
    this.cache.forEach(entry => {
      if (entry.compressed) {
        totalCompressedSize += entry.size;
        // Estimate original size (rough approximation)
        totalOriginalSize += entry.size * 2;
      }
    });
    if (totalOriginalSize > 0) {
      this.metrics.compressionRatio = totalCompressedSize / totalOriginalSize;
    }
  }
  /**
   * Start cleanup timer for expired entries
   */
  private startCleanupTimer(): void {
    this.cleanupInterval = setInterval(() => {
      this.cleanupExpiredEntries();
    }, 60000); // Run every minute
  }
  /**
   * Cleanup expired entries
   */
  private cleanupExpiredEntries(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];
    this.cache.forEach((entry, key) => {
      if (now - entry.timestamp > entry.ttl) {
        expiredKeys.push(key);
      }
    });
    for (const key of expiredKeys) {
      this.delete(key);
    }
  }
  /**
   * Save cache to persistence
   */
  private saveToPersistence(): void {
    if (typeof localStorage === 'undefined') {
      return;
    }
    try {
      const cacheData = {
        entries: Array.from(this.cache.entries()),
        timestamp: Date.now(),
      };
      localStorage.setItem(this.config.persistenceKey, JSON.stringify(cacheData));
    } catch (error) {
      void error;
    }
  }
  /**
   * Load cache from persistence
   */
  private loadFromPersistence(): void {
    if (!this.config.enablePersistence || typeof localStorage === 'undefined') {
      return;
    }
    try {
      const stored = localStorage.getItem(this.config.persistenceKey);
      if (!stored) {
        return;
      }
      const cacheData: { entries: [string, CacheEntry][]; timestamp: number } = JSON.parse(stored);
      const now = Date.now();
      // Only load if data is not too old (1 hour)
      if (now - cacheData.timestamp > 3600000) {
        this.clearPersistence();
        return;
      }
      // Restore cache entries
      for (const [key, entry] of cacheData.entries) {
        if (!this.isExpired(entry)) {
          this.cache.set(key, entry);
          this.accessOrder.push(key);
        }
      }
      this.metrics.totalEntries = this.cache.size;
      let restoredMemoryUsage = 0;
      this.cache.forEach(cacheEntry => {
        restoredMemoryUsage += cacheEntry.size;
      });
      this.metrics.memoryUsage = restoredMemoryUsage;
    } catch (error) {
      void error;
      this.clearPersistence();
    }
  }
  /**
   * Clear persistence storage
   */
  private clearPersistence(): void {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(this.config.persistenceKey);
    }
  }
}
// Global cache instance
let requestResponseCache: RequestResponseCache | null = null;
/**
 * Get the global request/response cache instance
 */
export function getRequestResponseCache(): RequestResponseCache {
  if (!requestResponseCache) {
    requestResponseCache = new RequestResponseCache();
  }
  return requestResponseCache;
}
/**
 * Initialize request/response cache with custom configuration
 */
export function initializeRequestResponseCache(config?: Partial<CacheConfig>): RequestResponseCache {
  if (requestResponseCache) {
    requestResponseCache.shutdown();
  }
  requestResponseCache = new RequestResponseCache(config);
  return requestResponseCache;
}
/**
 * Shutdown the global request/response cache
 */
export function shutdownRequestResponseCache(): void {
  if (requestResponseCache) {
    requestResponseCache.shutdown();
    requestResponseCache = null;
  }
}
