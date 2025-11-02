/**
 * Request/Response Cache Tests
 * 
 * Unit tests for request/response caching functionality.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { RequestResponseCache } from '../request-response-cache';

describe('RequestResponseCache', () => {
  let cache: RequestResponseCache;

  beforeEach(() => {
    cache = new RequestResponseCache({
      maxSize: 10,
      defaultTtl: 60000,
      enableCompression: false, // Disable for testing
      enablePersistence: false,


  afterEach(() => {
    cache.shutdown();

  describe('Basic Cache Operations', () => {
    it('should store and retrieve cache entries', async () => {
      const testData = { message: 'Hello, World!' };
      const key = 'test-key';

      // Store data
      await cache.set(key, testData, {}, 200);

      // Retrieve data
      const result = await cache.get(key);

      expect(result).toBeTruthy();
      expect(result!.data).toEqual(testData);
      expect(result!.status).toBe(200);

    it('should return null for non-existent keys', async () => {
      const result = await cache.get('non-existent-key');
      expect(result).toBeNull();

    it('should handle cache expiration', async () => {
      const testData = { message: 'Expires soon' };
      const key = 'expiring-key';

      // Store with short TTL
      await cache.set(key, testData, {}, 200, { ttl: 100 });

      // Should be available immediately
      let result = await cache.get(key);
      expect(result).toBeTruthy();

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 150));

      // Should be expired
      result = await cache.get(key);
      expect(result).toBeNull();

    it('should delete cache entries', async () => {
      const testData = { message: 'To be deleted' };
      const key = 'delete-key';

      await cache.set(key, testData, {}, 200);
      
      // Verify it exists
      let result = await cache.get(key);
      expect(result).toBeTruthy();

      // Delete it
      const deleted = cache.delete(key);
      expect(deleted).toBe(true);

      // Verify it's gone
      result = await cache.get(key);
      expect(result).toBeNull();


  describe('Cache Headers and TTL', () => {
    it('should extract TTL from Cache-Control headers', async () => {
      const testData = { message: 'Cached with headers' };
      const key = 'header-ttl-key';
      const headers = { 'Cache-Control': 'max-age=300' }; // 5 minutes

      await cache.set(key, testData, headers, 200);

      const result = await cache.get(key);
      expect(result).toBeTruthy();
      expect(result!.ttl).toBe(300000); // 5 minutes in milliseconds

    it('should extract TTL from Expires headers', async () => {
      const testData = { message: 'Expires header' };
      const key = 'expires-key';
      const futureDate = new Date(Date.now() + 600000); // 10 minutes from now
      const headers = { 'Expires': futureDate.toUTCString() };

      await cache.set(key, testData, headers, 200);

      const result = await cache.get(key);
      expect(result).toBeTruthy();
      expect(result!.ttl).toBeGreaterThan(500000); // Should be close to 10 minutes

    it('should use default TTL when no headers provided', async () => {
      const testData = { message: 'Default TTL' };
      const key = 'default-ttl-key';

      await cache.set(key, testData, {}, 200);

      const result = await cache.get(key);
      expect(result).toBeTruthy();
      expect(result!.ttl).toBe(60000); // Default TTL


  describe('Cache Tags and Invalidation', () => {
    it('should support cache tags', async () => {
      const userData = { id: 1, name: 'John' };
      const postData = { id: 1, title: 'Post 1' };

      await cache.set('user-1', userData, {}, 200, { tags: ['user', 'user:1'] });
      await cache.set('post-1', postData, {}, 200, { tags: ['post', 'user:1'] });

      // Both should exist
      expect(await cache.get('user-1')).toBeTruthy();
      expect(await cache.get('post-1')).toBeTruthy();

      // Clear by tag
      const cleared = cache.clearByTags(['user:1']);
      expect(cleared).toBe(2);

      // Both should be gone
      expect(await cache.get('user-1')).toBeNull();
      expect(await cache.get('post-1')).toBeNull();

    it('should clear all cache entries', async () => {
      // Add multiple entries
      await cache.set('key1', { data: 1 }, {}, 200);
      await cache.set('key2', { data: 2 }, {}, 200);
      await cache.set('key3', { data: 3 }, {}, 200);

      // Verify they exist
      expect(await cache.get('key1')).toBeTruthy();
      expect(await cache.get('key2')).toBeTruthy();
      expect(await cache.get('key3')).toBeTruthy();

      // Clear all
      cache.clear();

      // All should be gone
      expect(await cache.get('key1')).toBeNull();
      expect(await cache.get('key2')).toBeNull();
      expect(await cache.get('key3')).toBeNull();


  describe('Cache Size Management', () => {
    it('should respect maximum cache size', async () => {
      const maxSize = cache.getConfig().maxSize;

      // Fill cache beyond max size
      for (let i = 0; i < maxSize + 5; i++) {
        await cache.set(`key-${i}`, { data: i }, {}, 200);
      }

      const metrics = cache.getMetrics();
      expect(metrics.totalEntries).toBeLessThanOrEqual(maxSize);

    it('should evict least recently used entries', async () => {
      // Fill cache to max size
      for (let i = 0; i < 10; i++) {
        await cache.set(`key-${i}`, { data: i }, {}, 200);
      }

      // Access some entries to make them recently used
      await cache.get('key-5');
      await cache.get('key-6');
      await cache.get('key-7');

      // Add new entries to trigger eviction
      await cache.set('new-key-1', { data: 'new1' }, {}, 200);
      await cache.set('new-key-2', { data: 'new2' }, {}, 200);

      // Recently accessed entries should still exist
      expect(await cache.get('key-5')).toBeTruthy();
      expect(await cache.get('key-6')).toBeTruthy();
      expect(await cache.get('key-7')).toBeTruthy();

      // Some older entries should be evicted
      const oldEntries = await Promise.all([
        cache.get('key-0'),
        cache.get('key-1'),
        cache.get('key-2'),
      ]);

      const nullCount = oldEntries.filter(entry => entry === null).length;
      expect(nullCount).toBeGreaterThan(0);


  describe('Cache Metrics', () => {
    it('should track cache hit and miss rates', async () => {
      // Add some entries
      await cache.set('hit-key-1', { data: 1 }, {}, 200);
      await cache.set('hit-key-2', { data: 2 }, {}, 200);

      // Generate hits
      await cache.get('hit-key-1');
      await cache.get('hit-key-1');
      await cache.get('hit-key-2');

      // Generate misses
      await cache.get('miss-key-1');
      await cache.get('miss-key-2');

      const metrics = cache.getMetrics();
      
      expect(metrics.cacheHits).toBe(3);
      expect(metrics.cacheMisses).toBe(2);
      expect(metrics.hitRate).toBeCloseTo(0.6); // 3/5
      expect(metrics.missRate).toBeCloseTo(0.4); // 2/5

    it('should track memory usage', async () => {
      const largeData = { message: 'x'.repeat(1000) };
      
      await cache.set('large-key', largeData, {}, 200);

      const metrics = cache.getMetrics();
      expect(metrics.memoryUsage).toBeGreaterThan(0);
      expect(metrics.totalEntries).toBe(1);


  describe('Skip Cache Options', () => {
    it('should skip cache when requested', async () => {
      const testData = { message: 'Skip cache test' };
      const key = 'skip-key';

      // Set with skip cache
      await cache.set(key, testData, {}, 200, { skipCache: true });

      // Should not be in cache
      const result = await cache.get(key);
      expect(result).toBeNull();

    it('should skip cache retrieval when requested', async () => {
      const testData = { message: 'Skip retrieval test' };
      const key = 'skip-retrieval-key';

      // Store normally
      await cache.set(key, testData, {}, 200);

      // Get with skip cache should return null
      const result = await cache.get(key, { skipCache: true });
      expect(result).toBeNull();

      // Normal get should still work
      const normalResult = await cache.get(key);
      expect(normalResult).toBeTruthy();


  describe('Compression', () => {
    it('should handle compression when available', async () => {
      // Skip if compression not supported
      if (typeof CompressionStream === 'undefined') {
        return;
      }

      const compressionCache = new RequestResponseCache({
        enableCompression: true,
        maxSize: 10,

      const largeData = { message: 'x'.repeat(1000) };
      const key = 'compression-key';

      await compressionCache.set(key, largeData, {}, 200, { compress: true });

      const result = await compressionCache.get(key);
      expect(result).toBeTruthy();
      expect(result!.data).toEqual(largeData);

      compressionCache.shutdown();


  describe('Cleanup and Maintenance', () => {
    it('should cleanup expired entries automatically', async () => {
      // Create cache with short cleanup interval for testing
      const shortCleanupCache = new RequestResponseCache({
        maxSize: 10,
        defaultTtl: 100, // Very short TTL

      // Add entries that will expire
      await shortCleanupCache.set('expire-1', { data: 1 }, {}, 200);
      await shortCleanupCache.set('expire-2', { data: 2 }, {}, 200);

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 150));

      // Trigger cleanup by adding new entry
      await shortCleanupCache.set('new-entry', { data: 'new' }, {}, 200);

      // Expired entries should be gone
      expect(await shortCleanupCache.get('expire-1')).toBeNull();
      expect(await shortCleanupCache.get('expire-2')).toBeNull();

      // New entry should exist
      expect(await shortCleanupCache.get('new-entry')).toBeTruthy();

      shortCleanupCache.shutdown();


