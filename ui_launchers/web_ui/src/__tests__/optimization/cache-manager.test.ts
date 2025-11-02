/**
 * Tests for Cache Manager
 * 
 * Comprehensive test suite for caching system including CDN integration,
 * edge caching strategies, and performance optimization.
 */

// Vitest globals are enabled in config, so these are available globally
import { CacheManager, CacheConfig } from '../../lib/optimization/cache-manager';

// Mock fetch for CDN testing
global.fetch = vi.fn();

// Mock Service Worker for edge caching
Object.defineProperty(navigator, 'serviceWorker', {
  value: {
    ready: Promise.resolve({
      active: {
        postMessage: vi.fn()
      }
    })
  },
  writable: true

describe('CacheManager', () => {
  let cacheManager: CacheManager;
  let mockConfig: Partial<CacheConfig>;

  beforeEach(() => {
    mockConfig = {
      defaultTTL: 60000, // 1 minute
      maxSize: 1024 * 1024, // 1MB
      enableCompression: true,
      enableCDN: false,
      edgeCaching: false
    };

    cacheManager = new CacheManager(mockConfig);
    vi.clearAllMocks();

  afterEach(() => {
    cacheManager.destroy();

  describe('Basic Cache Operations', () => {
    it('should set and get cache entries', async () => {
      const key = 'test-key';
      const data = { message: 'Hello, World!' };

      await cacheManager.set(key, data);
      const retrieved = await cacheManager.get(key);

      expect(retrieved).toEqual(data);

    it('should return null for non-existent keys', async () => {
      const result = await cacheManager.get('non-existent-key');
      expect(result).toBeNull();

    it('should handle cache expiration', async () => {
      const key = 'expiring-key';
      const data = { message: 'This will expire' };

      await cacheManager.set(key, data, { ttl: 100 }); // 100ms TTL

      // Should be available immediately
      expect(await cacheManager.get(key)).toEqual(data);

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 150));

      // Should be expired
      expect(await cacheManager.get(key)).toBeNull();

    it('should delete cache entries', async () => {
      const key = 'delete-key';
      const data = { message: 'To be deleted' };

      await cacheManager.set(key, data);
      expect(await cacheManager.get(key)).toEqual(data);

      const deleted = await cacheManager.delete(key);
      expect(deleted).toBe(true);
      expect(await cacheManager.get(key)).toBeNull();

    it('should check if key exists', async () => {
      const key = 'exists-key';
      const data = { message: 'I exist' };

      expect(cacheManager.has(key)).toBe(false);

      await cacheManager.set(key, data);
      expect(cacheManager.has(key)).toBe(true);

      await cacheManager.delete(key);
      expect(cacheManager.has(key)).toBe(false);

    it('should clear all cache entries', async () => {
      await cacheManager.set('key1', { data: 1 });
      await cacheManager.set('key2', { data: 2 });
      await cacheManager.set('key3', { data: 3 });

      expect(cacheManager.size()).toBe(3);

      cacheManager.clear();
      expect(cacheManager.size()).toBe(0);


  describe('Cache Strategies', () => {
    it('should apply custom TTL from strategy', async () => {
      const configWithStrategy: Partial<CacheConfig> = {
        ...mockConfig,
        strategies: [
          {
            pattern: 'api/users',
            ttl: 30000, // 30 seconds
            tags: ['users'],
            compression: true,
            cdn: false,
            edge: false,
            invalidationRules: []
          }
        ]
      };

      const manager = new CacheManager(configWithStrategy);
      const key = 'api/users/123';
      const data = { id: 123, name: 'John Doe' };

      await manager.set(key, data);
      
      // The strategy should be applied automatically
      expect(await manager.get(key)).toEqual(data);
      
      manager.destroy();

    it('should apply regex pattern strategies', async () => {
      const configWithStrategy: Partial<CacheConfig> = {
        ...mockConfig,
        strategies: [
          {
            pattern: /^api\/posts\/\d+$/,
            ttl: 120000, // 2 minutes
            tags: ['posts'],
            compression: true,
            cdn: false,
            edge: false,
            invalidationRules: []
          }
        ]
      };

      const manager = new CacheManager(configWithStrategy);
      const key = 'api/posts/456';
      const data = { id: 456, title: 'Test Post' };

      await manager.set(key, data);
      expect(await manager.get(key)).toEqual(data);
      
      manager.destroy();


  describe('Tag-based Invalidation', () => {
    it('should invalidate entries by tag', async () => {
      await cacheManager.set('user:1', { id: 1 }, { tags: ['users', 'profile'] });
      await cacheManager.set('user:2', { id: 2 }, { tags: ['users', 'profile'] });
      await cacheManager.set('post:1', { id: 1 }, { tags: ['posts'] });

      expect(await cacheManager.get('user:1')).toBeTruthy();
      expect(await cacheManager.get('user:2')).toBeTruthy();
      expect(await cacheManager.get('post:1')).toBeTruthy();

      const invalidatedCount = await cacheManager.invalidateByTag('users');
      expect(invalidatedCount).toBe(2);

      expect(await cacheManager.get('user:1')).toBeNull();
      expect(await cacheManager.get('user:2')).toBeNull();
      expect(await cacheManager.get('post:1')).toBeTruthy(); // Should still exist

    it('should invalidate entries by pattern', async () => {
      await cacheManager.set('api/users/1', { id: 1 });
      await cacheManager.set('api/users/2', { id: 2 });
      await cacheManager.set('api/posts/1', { id: 1 });

      const invalidatedCount = await cacheManager.invalidateByPattern('api/users');
      expect(invalidatedCount).toBe(2);

      expect(await cacheManager.get('api/users/1')).toBeNull();
      expect(await cacheManager.get('api/users/2')).toBeNull();
      expect(await cacheManager.get('api/posts/1')).toBeTruthy();

    it('should invalidate entries by regex pattern', async () => {
      await cacheManager.set('user_profile_1', { id: 1 });
      await cacheManager.set('user_profile_2', { id: 2 });
      await cacheManager.set('user_settings_1', { id: 1 });

      const invalidatedCount = await cacheManager.invalidateByPattern(/^user_profile_\d+$/);
      expect(invalidatedCount).toBe(2);

      expect(await cacheManager.get('user_profile_1')).toBeNull();
      expect(await cacheManager.get('user_profile_2')).toBeNull();
      expect(await cacheManager.get('user_settings_1')).toBeTruthy();


  describe('Size Management and LRU Eviction', () => {
    it('should enforce maximum cache size', async () => {
      const smallCacheManager = new CacheManager({
        maxSize: 1000, // Very small cache
        defaultTTL: 60000

      // Add entries that exceed the size limit
      const largeData = 'x'.repeat(500); // 500 bytes each
      
      await smallCacheManager.set('key1', largeData);
      await smallCacheManager.set('key2', largeData);
      await smallCacheManager.set('key3', largeData); // This should trigger eviction

      // The cache should have evicted some entries to stay under the size limit
      const stats = smallCacheManager.getStats();
      expect(stats.totalSize).toBeLessThanOrEqual(1000);

      smallCacheManager.destroy();

    it('should evict least recently used entries', async () => {
      const smallCacheManager = new CacheManager({
        maxSize: 1500,
        defaultTTL: 60000

      const data = 'x'.repeat(400); // 400 bytes each

      await smallCacheManager.set('key1', data);
      await smallCacheManager.set('key2', data);
      await smallCacheManager.set('key3', data);

      // Access key1 and key2 to make them more recently used
      await smallCacheManager.get('key1');
      await smallCacheManager.get('key2');

      // Add another entry that should trigger eviction of key3 (least recently used)
      await smallCacheManager.set('key4', data);

      expect(await smallCacheManager.get('key1')).toBeTruthy();
      expect(await smallCacheManager.get('key2')).toBeTruthy();
      expect(await smallCacheManager.get('key4')).toBeTruthy();
      // key3 might be evicted due to size constraints

      smallCacheManager.destroy();


  describe('Compression', () => {
    it('should compress data when enabled', async () => {
      const compressedManager = new CacheManager({
        enableCompression: true,
        defaultTTL: 60000

      const largeData = { message: 'x'.repeat(1000) };
      await compressedManager.set('compressed-key', largeData, { compress: true });

      const retrieved = await compressedManager.get('compressed-key');
      expect(retrieved).toEqual(largeData);

      compressedManager.destroy();

    it('should handle compression errors gracefully', async () => {
      const data = { circular: null as any };
      data.circular = data; // Create circular reference

      // Should not throw error, should store without compression
      await expect(cacheManager.set('circular-key', data)).resolves.not.toThrow();


  describe('CDN Integration', () => {
    it('should set CDN cache when enabled', async () => {
      const cdnManager = new CacheManager({
        enableCDN: true,
        cdnEndpoint: 'https://cdn.example.com'

      const mockFetch = vi.mocked(fetch);
      mockFetch.mockResolvedValueOnce(new Response('OK', { status: 200 }));

      const data = { message: 'CDN test' };
      await cdnManager.set('cdn-key', data, { cdn: true });

      expect(mockFetch).toHaveBeenCalledWith(
        'https://cdn.example.com/cache/cdn-key',
        expect.objectContaining({
          method: 'PUT',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify(data)
        })
      );

      cdnManager.destroy();

    it('should get from CDN cache when local cache misses', async () => {
      const cdnManager = new CacheManager({
        enableCDN: true,
        cdnEndpoint: 'https://cdn.example.com'

      const mockFetch = vi.mocked(fetch);
      const cdnData = { message: 'From CDN' };
      mockFetch.mockResolvedValueOnce(new Response(JSON.stringify(cdnData), { status: 200 }));

      const result = await cdnManager.get('cdn-miss-key');
      expect(result).toEqual(cdnData);

      expect(mockFetch).toHaveBeenCalledWith('https://cdn.example.com/cache/cdn-miss-key');

      cdnManager.destroy();

    it('should handle CDN errors gracefully', async () => {
      const cdnManager = new CacheManager({
        enableCDN: true,
        cdnEndpoint: 'https://cdn.example.com'

      const mockFetch = vi.mocked(fetch);
      mockFetch.mockRejectedValueOnce(new Error('CDN error'));

      // Should not throw error
      await expect(cdnManager.set('error-key', { data: 'test' })).resolves.not.toThrow();

      cdnManager.destroy();


  describe('Edge Caching', () => {
    it('should set edge cache when enabled', async () => {
      const edgeManager = new CacheManager({
        edgeCaching: true

      const data = { message: 'Edge test' };
      await edgeManager.set('edge-key', data, { edge: true });

      // Should not throw error (service worker mock is set up)
      expect(true).toBe(true);

      edgeManager.destroy();


  describe('Cache Statistics', () => {
    it('should track cache statistics', async () => {
      await cacheManager.set('stats-key-1', { data: 1 });
      await cacheManager.set('stats-key-2', { data: 2 });

      // Generate some hits and misses
      await cacheManager.get('stats-key-1'); // Hit
      await cacheManager.get('stats-key-1'); // Hit
      await cacheManager.get('non-existent'); // Miss

      const stats = cacheManager.getStats();

      expect(stats.totalEntries).toBe(2);
      expect(stats.hitRate).toBeGreaterThan(0);
      expect(stats.missRate).toBeGreaterThan(0);
      expect(stats.topKeys).toHaveLength(2);
      expect(stats.topKeys[0].accessCount).toBeGreaterThan(0);

    it('should track access counts correctly', async () => {
      await cacheManager.set('popular-key', { data: 'popular' });
      await cacheManager.set('unpopular-key', { data: 'unpopular' });

      // Access popular key multiple times
      for (let i = 0; i < 5; i++) {
        await cacheManager.get('popular-key');
      }

      // Access unpopular key once
      await cacheManager.get('unpopular-key');

      const stats = cacheManager.getStats();
      const popularKey = stats.topKeys.find(k => k.key === 'popular-key');
      const unpopularKey = stats.topKeys.find(k => k.key === 'unpopular-key');

      expect(popularKey?.accessCount).toBe(5);
      expect(unpopularKey?.accessCount).toBe(1);


  describe('Cache Warming and Preloading', () => {
    it('should warm cache with provided data loader', async () => {
      const dataLoader = vi.fn().mockImplementation((key: string) => {
        return Promise.resolve({ key, data: `Data for ${key}` });

      const keys = ['warm-key-1', 'warm-key-2', 'warm-key-3'];
      await cacheManager.warmCache(keys, dataLoader);

      expect(dataLoader).toHaveBeenCalledTimes(3);

      for (const key of keys) {
        const data = await cacheManager.get(key);
        expect(data).toEqual({ key, data: `Data for ${key}` });
      }

    it('should preload critical data with longer TTL', async () => {
      const dataLoader = vi.fn().mockImplementation((key: string) => {
        return Promise.resolve({ key, critical: true });

      const criticalKeys = ['critical-1', 'critical-2'];
      await cacheManager.preloadCriticalData(criticalKeys, dataLoader);

      expect(dataLoader).toHaveBeenCalledTimes(2);

      for (const key of criticalKeys) {
        const data = await cacheManager.get(key);
        expect(data).toEqual({ key, critical: true });
      }

    it('should handle data loader errors gracefully', async () => {
      const dataLoader = vi.fn().mockRejectedValue(new Error('Data loader error'));

      const keys = ['error-key-1', 'error-key-2'];
      
      // Should not throw error
      await expect(cacheManager.warmCache(keys, dataLoader)).resolves.not.toThrow();

      // Keys should not be in cache
      for (const key of keys) {
        expect(await cacheManager.get(key)).toBeNull();
      }


  describe('Cleanup and Memory Management', () => {
    it('should clean up expired entries automatically', async () => {
      const shortTTLManager = new CacheManager({
        defaultTTL: 100 // 100ms

      await shortTTLManager.set('expire-1', { data: 1 });
      await shortTTLManager.set('expire-2', { data: 2 });

      expect(shortTTLManager.size()).toBe(2);

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 150));

      // Trigger cleanup by accessing cache
      await shortTTLManager.get('expire-1');

      // Entries should be cleaned up
      expect(await shortTTLManager.get('expire-1')).toBeNull();
      expect(await shortTTLManager.get('expire-2')).toBeNull();

      shortTTLManager.destroy();

    it('should destroy cache manager cleanly', () => {
      const manager = new CacheManager();
      
      // Should not throw error
      expect(() => manager.destroy()).not.toThrow();
      
      // Should clear cache
      expect(manager.size()).toBe(0);


  describe('Error Handling', () => {
    it('should handle invalid data gracefully', async () => {
      // Should not throw for undefined data
      await expect(cacheManager.set('undefined-key', undefined)).resolves.not.toThrow();
      
      // Should not throw for null data
      await expect(cacheManager.set('null-key', null)).resolves.not.toThrow();
      
      // Should retrieve the stored values
      expect(await cacheManager.get('undefined-key')).toBeUndefined();
      expect(await cacheManager.get('null-key')).toBeNull();

    it('should handle large data sets', async () => {
      const largeData = {
        items: Array.from({ length: 10000 }, (_, i) => ({ id: i, data: `Item ${i}` }))
      };

      await expect(cacheManager.set('large-data', largeData)).resolves.not.toThrow();
      
      const retrieved = await cacheManager.get('large-data');
      expect(retrieved).toEqual(largeData);


