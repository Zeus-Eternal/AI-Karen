/**
 * Cache Manager
 * 
 * Comprehensive caching system with CDN integration, edge caching strategies,
 * and intelligent cache invalidation for production optimization.
 */
export interface CacheConfig {
  defaultTTL: number;
  maxSize: number;
  enableCompression: boolean;
  enableCDN: boolean;
  cdnEndpoint?: string;
  edgeCaching: boolean;
  strategies: CacheStrategy[];
}
export interface CacheStrategy {
  pattern: string | RegExp;
  ttl: number;
  tags: string[];
  compression: boolean;
  cdn: boolean;
  edge: boolean;
  invalidationRules: InvalidationRule[];
}
export interface InvalidationRule {
  trigger: 'time' | 'event' | 'dependency' | 'manual';
  condition: string | number | ((data: any) => boolean);
  cascade: boolean;
}
export interface CacheEntry {
  key: string;
  data: any;
  timestamp: number;
  ttl: number;
  size: number;
  tags: string[];
  compressed: boolean;
  accessCount: number;
  lastAccessed: number;
}
export interface CacheStats {
  totalEntries: number;
  totalSize: number;
  hitRate: number;
  missRate: number;
  evictionCount: number;
  compressionRatio: number;
  averageAccessTime: number;
  topKeys: Array<{ key: string; accessCount: number; size: number }>;
}
export class CacheManager {
  private cache: Map<string, CacheEntry> = new Map();
  private config: CacheConfig;
  private stats: {
    hits: number;
    misses: number;
    evictions: number;
    totalAccessTime: number;
    accessCount: number;
  } = {
    hits: 0,
    misses: 0,
    evictions: 0,
    totalAccessTime: 0,
    accessCount: 0
  };
  private cleanupInterval: NodeJS.Timeout | null = null;
  private compressionWorker: Worker | null = null;
  constructor(config: Partial<CacheConfig> = {}) {
    this.config = {
      defaultTTL: 300000, // 5 minutes
      maxSize: 100 * 1024 * 1024, // 100MB
      enableCompression: true,
      enableCDN: false,
      edgeCaching: true,
      strategies: [],
      ...config
    };
    this.startCleanupProcess();
    this.initializeCompressionWorker();
  }
  private startCleanupProcess() {
    // Clean up expired entries every minute
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, 60000);
  }
  private initializeCompressionWorker() {
    if (this.config.enableCompression && typeof Worker !== 'undefined') {
      try {
        // In a real implementation, you would create a compression worker
        // this.compressionWorker = new Worker('/workers/compression-worker.js');
      } catch (error) {
      }
    }
  }
  private findStrategy(key: string): CacheStrategy | null {
    for (const strategy of this.config.strategies) {
      if (typeof strategy.pattern === 'string') {
        if (key.includes(strategy.pattern)) {
          return strategy;
        }
      } else if (strategy.pattern instanceof RegExp) {
        if (strategy.pattern.test(key)) {
          return strategy;
        }
      }
    }
    return null;
  }
  private async compressData(data: any): Promise<{ compressed: any; ratio: number }> {
    if (!this.config.enableCompression) {
      return { compressed: data, ratio: 1 };
    }
    try {
      const originalSize = JSON.stringify(data).length;
      // Simple compression simulation (in real implementation, use actual compression)
      const compressed = JSON.stringify(data);
      const compressedSize = compressed.length * 0.7; // Simulate 30% compression
      return {
        compressed: compressed,
        ratio: originalSize / compressedSize
      };
    } catch (error) {
      return { compressed: data, ratio: 1 };
    }
  }
  private async decompressData(compressed: any): Promise<any> {
    if (!this.config.enableCompression) {
      return compressed;
    }
    try {
      // Simple decompression simulation
      return typeof compressed === 'string' ? JSON.parse(compressed) : compressed;
    } catch (error) {
      return compressed;
    }
  }
  private calculateSize(data: any): number {
    try {
      return JSON.stringify(data).length;
    } catch (error) {
      return 0;
    }
  }
  private evictLRU() {
    if (this.cache.size === 0) return;
    // Find least recently used entry
    let lruKey = '';
    let lruTime = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccessed < lruTime) {
        lruTime = entry.lastAccessed;
        lruKey = key;
      }
    }
    if (lruKey) {
      this.cache.delete(lruKey);
      this.stats.evictions++;
    }
  }
  private enforceMaxSize() {
    let totalSize = 0;
    for (const entry of this.cache.values()) {
      totalSize += entry.size;
    }
    while (totalSize > this.config.maxSize && this.cache.size > 0) {
      this.evictLRU();
      // Recalculate total size
      totalSize = 0;
      for (const entry of this.cache.values()) {
        totalSize += entry.size;
      }
    }
  }
  public async set(
    key: string, 
    data: any, 
    options: {
      ttl?: number;
      tags?: string[];
      compress?: boolean;
      cdn?: boolean;
      edge?: boolean;
    } = {}
  ): Promise<void> {
    const strategy = this.findStrategy(key);
    const ttl = options.ttl || strategy?.ttl || this.config.defaultTTL;
    const tags = options.tags || strategy?.tags || [];
    const shouldCompress = options.compress !== undefined ? options.compress : 
                          strategy?.compression !== undefined ? strategy.compression : 
                          this.config.enableCompression;
    // Compress data if enabled
    const { compressed, ratio } = await this.compressData(data);
    const size = this.calculateSize(compressed);
    const entry: CacheEntry = {
      key,
      data: compressed,
      timestamp: Date.now(),
      ttl,
      size,
      tags,
      compressed: shouldCompress && ratio > 1.1, // Only mark as compressed if significant savings
      accessCount: 0,
      lastAccessed: Date.now()
    };
    this.cache.set(key, entry);
    // Enforce size limits
    this.enforceMaxSize();
    // Handle CDN caching
    if (options.cdn || strategy?.cdn || this.config.enableCDN) {
      await this.setCDNCache(key, data, ttl);
    }
    // Handle edge caching
    if (options.edge || strategy?.edge || this.config.edgeCaching) {
      await this.setEdgeCache(key, data, ttl);
    }
  }
  public async get(key: string): Promise<any | null> {
    const startTime = Date.now();
    const entry = this.cache.get(key);
    if (!entry) {
      this.stats.misses++;
      // Try CDN cache
      const cdnData = await this.getCDNCache(key);
      if (cdnData !== null) {
        // Cache locally for faster access
        await this.set(key, cdnData);
        return cdnData;
      }
      // Try edge cache
      const edgeData = await this.getEdgeCache(key);
      if (edgeData !== null) {
        await this.set(key, edgeData);
        return edgeData;
      }
      return null;
    }
    // Check if expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      this.stats.misses++;
      return null;
    }
    // Update access statistics
    entry.accessCount++;
    entry.lastAccessed = Date.now();
    this.stats.hits++;
    // Track access time
    const accessTime = Date.now() - startTime;
    this.stats.totalAccessTime += accessTime;
    this.stats.accessCount++;
    // Decompress data if needed
    const data = entry.compressed ? await this.decompressData(entry.data) : entry.data;
    return data;
  }
  public async delete(key: string): Promise<boolean> {
    const deleted = this.cache.delete(key);
    if (deleted) {
      // Also delete from CDN and edge caches
      await this.deleteCDNCache(key);
      await this.deleteEdgeCache(key);
    }
    return deleted;
  }
  public async invalidateByTag(tag: string): Promise<number> {
    let invalidatedCount = 0;
    for (const [key, entry] of this.cache.entries()) {
      if (entry.tags.includes(tag)) {
        await this.delete(key);
        invalidatedCount++;
      }
    }
    return invalidatedCount;
  }
  public async invalidateByPattern(pattern: string | RegExp): Promise<number> {
    let invalidatedCount = 0;
    for (const key of this.cache.keys()) {
      let matches = false;
      if (typeof pattern === 'string') {
        matches = key.includes(pattern);
      } else {
        matches = pattern.test(key);
      }
      if (matches) {
        await this.delete(key);
        invalidatedCount++;
      }
    }
    return invalidatedCount;
  }
  public has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) {
      return false;
    }
    // Check if expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return false;
    }
    return true;
  }
  public clear(): void {
    this.cache.clear();
    this.stats = {
      hits: 0,
      misses: 0,
      evictions: 0,
      totalAccessTime: 0,
      accessCount: 0
    };
  }
  public size(): number {
    return this.cache.size;
  }
  public getStats(): CacheStats {
    const totalRequests = this.stats.hits + this.stats.misses;
    const hitRate = totalRequests > 0 ? this.stats.hits / totalRequests : 0;
    const missRate = totalRequests > 0 ? this.stats.misses / totalRequests : 0;
    let totalSize = 0;
    let totalCompressionRatio = 0;
    let compressedEntries = 0;
    const keyStats: Array<{ key: string; accessCount: number; size: number }> = [];
    for (const [key, entry] of this.cache.entries()) {
      totalSize += entry.size;
      keyStats.push({
        key,
        accessCount: entry.accessCount,
        size: entry.size

      if (entry.compressed) {
        compressedEntries++;
        // Estimate compression ratio (simplified)
        totalCompressionRatio += 1.3; // Assume 30% compression
      }
    }
    const averageCompressionRatio = compressedEntries > 0 ? totalCompressionRatio / compressedEntries : 1;
    const averageAccessTime = this.stats.accessCount > 0 ? this.stats.totalAccessTime / this.stats.accessCount : 0;
    // Sort by access count for top keys
    keyStats.sort((a, b) => b.accessCount - a.accessCount);
    return {
      totalEntries: this.cache.size,
      totalSize,
      hitRate,
      missRate,
      evictionCount: this.stats.evictions,
      compressionRatio: averageCompressionRatio,
      averageAccessTime,
      topKeys: keyStats.slice(0, 10)
    };
  }
  private cleanup(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        expiredKeys.push(key);
      }
    }
    for (const key of expiredKeys) {
      this.cache.delete(key);
    }
  }
  // CDN Integration Methods
  private async setCDNCache(key: string, data: any, ttl: number): Promise<void> {
    if (!this.config.enableCDN || !this.config.cdnEndpoint) {
      return;
    }
    try {
      const response = await fetch(`${this.config.cdnEndpoint}/cache/${encodeURIComponent(key)}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': `max-age=${Math.floor(ttl / 1000)}`
        },
        body: JSON.stringify(data)

      if (!response.ok) {
      }
    } catch (error) {
    }
  }
  private async getCDNCache(key: string): Promise<any | null> {
    if (!this.config.enableCDN || !this.config.cdnEndpoint) {
      return null;
    }
    try {
      const response = await fetch(`${this.config.cdnEndpoint}/cache/${encodeURIComponent(key)}`);
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
    }
    return null;
  }
  private async deleteCDNCache(key: string): Promise<void> {
    if (!this.config.enableCDN || !this.config.cdnEndpoint) {
      return;
    }
    try {
      await fetch(`${this.config.cdnEndpoint}/cache/${encodeURIComponent(key)}`, {
        method: 'DELETE'

    } catch (error) {
    }
  }
  // Edge Caching Methods (Service Worker based)
  private async setEdgeCache(key: string, data: any, ttl: number): Promise<void> {
    if (!this.config.edgeCaching || typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
      return;
    }
    try {
      const registration = await navigator.serviceWorker.ready;
      if (registration.active) {
        registration.active.postMessage({
          type: 'CACHE_SET',
          key,
          data,
          ttl

      }
    } catch (error) {
    }
  }
  private async getEdgeCache(key: string): Promise<any | null> {
    if (!this.config.edgeCaching || typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
      return null;
    }
    try {
      const registration = await navigator.serviceWorker.ready;
      if (registration.active) {
        return new Promise((resolve) => {
          const messageChannel = new MessageChannel();
          messageChannel.port1.onmessage = (event) => {
            resolve(event.data.data || null);
          };
          registration.active!.postMessage({
            type: 'CACHE_GET',
            key
          }, [messageChannel.port2]);
          // Timeout after 1 second
          setTimeout(() => resolve(null), 1000);

      }
    } catch (error) {
    }
    return null;
  }
  private async deleteEdgeCache(key: string): Promise<void> {
    if (!this.config.edgeCaching || typeof navigator === 'undefined' || !('serviceWorker' in navigator)) {
      return;
    }
    try {
      const registration = await navigator.serviceWorker.ready;
      if (registration.active) {
        registration.active.postMessage({
          type: 'CACHE_DELETE',
          key

      }
    } catch (error) {
    }
  }
  public destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    if (this.compressionWorker) {
      this.compressionWorker.terminate();
      this.compressionWorker = null;
    }
    this.clear();
  }
  // Utility methods for cache warming and preloading
  public async warmCache(keys: string[], dataLoader: (key: string) => Promise<any>): Promise<void> {
    const promises = keys.map(async (key) => {
      try {
        const data = await dataLoader(key);
        await this.set(key, data);
      } catch (error) {
      }

    await Promise.allSettled(promises);
  }
  public async preloadCriticalData(criticalKeys: string[], dataLoader: (key: string) => Promise<any>): Promise<void> {
    // Preload critical data with higher priority
    for (const key of criticalKeys) {
      try {
        const data = await dataLoader(key);
        await this.set(key, data, { ttl: this.config.defaultTTL * 2 }); // Longer TTL for critical data
      } catch (error) {
      }
    }
  }
}
export default CacheManager;
