/**
 * Performance Benchmarks and Tests
 * 
 * Comprehensive performance testing for HTTP connection pooling,
 * request/response caching, and database query optimization.
 * 
 * Requirements: 1.4, 4.4
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { HttpConnectionPool, initializeHttpConnectionPool } from '../http-connection-pool';
import { RequestResponseCache, initializeRequestResponseCache } from '../request-response-cache';
import { DatabaseQueryOptimizer, initializeDatabaseQueryOptimizer } from '../database-query-optimizer';
import { PerformanceOptimizer, initializePerformanceOptimizer } from '../performance-optimizer';

// Mock fetch for testing
global.fetch = vi.fn();

describe('Performance Benchmarks', () => {
  let connectionPool: HttpConnectionPool;
  let responseCache: RequestResponseCache;
  let queryOptimizer: DatabaseQueryOptimizer;
  let performanceOptimizer: PerformanceOptimizer;

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Initialize components with test configurations
    connectionPool = initializeHttpConnectionPool({
      maxConnections: 10,
      maxConnectionsPerHost: 5,
      connectionTimeout: 5000,
      enableKeepAlive: true,

    responseCache = initializeRequestResponseCache({
      maxSize: 100,
      defaultTtl: 60000,
      enableCompression: true,
      enablePersistence: false,

    queryOptimizer = initializeDatabaseQueryOptimizer({
      enableQueryCache: true,
      queryCacheTtl: 60000,
      enablePreparedStatements: true,
      maxCacheSize: 100,

    performanceOptimizer = initializePerformanceOptimizer({
      enableMetrics: true,
      metricsInterval: 1000,


  afterEach(async () => {
    await connectionPool.shutdown();
    responseCache.shutdown();
    queryOptimizer.shutdown();
    await performanceOptimizer.shutdown();

  describe('HTTP Connection Pool Performance', () => {
    it('should handle concurrent requests efficiently', async () => {
      // Mock successful responses
      (global.fetch as any).mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true }),

      const startTime = Date.now();
      const concurrentRequests = 20;
      
      // Make concurrent requests
      const promises = Array.from({ length: concurrentRequests }, (_, i) =>
        connectionPool.request(`https://api.example.com/test/${i}`, { method: 'GET' })
      );

      const responses = await Promise.all(promises);
      const endTime = Date.now();
      const totalTime = endTime - startTime;

      // Verify all requests succeeded
      expect(responses).toHaveLength(concurrentRequests);
      responses.forEach(response => {
        expect(response.ok).toBe(true);

      // Check performance metrics
      const metrics = connectionPool.getMetrics();
      expect(metrics.totalConnections).toBeGreaterThan(0);
      expect(metrics.connectionReuse).toBeGreaterThan(0);
      
      // Performance assertion: should complete within reasonable time
      expect(totalTime).toBeLessThan(5000); // 5 seconds max
      
      console.log(`Concurrent requests benchmark: ${concurrentRequests} requests in ${totalTime}ms`);
      console.log(`Connection pool metrics:`, metrics);

    it('should reuse connections effectively', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        json: async () => ({ success: true }),

      const url = 'https://api.example.com/test';
      
      // Make multiple requests to the same host
      await connectionPool.request(url, { method: 'GET' });
      await connectionPool.request(url, { method: 'GET' });
      await connectionPool.request(url, { method: 'GET' });

      const metrics = connectionPool.getMetrics();
      
      // Should have connection reuse
      expect(metrics.connectionReuse).toBeGreaterThan(1);
      expect(metrics.totalConnections).toBeLessThan(3); // Should reuse connections

    it('should handle connection failures gracefully', async () => {
      // Mock network error
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      const startTime = Date.now();
      
      try {
        await connectionPool.request('https://api.example.com/fail', { method: 'GET' });
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
      }

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      // Should fail quickly without hanging
      expect(totalTime).toBeLessThan(10000); // 10 seconds max


  describe('Request/Response Cache Performance', () => {
    it('should improve response times with caching', async () => {
      const testData = { message: 'Hello, World!', timestamp: Date.now() };
      const cacheKey = 'test-key';

      // First request - cache miss
      const startTime1 = Date.now();
      await responseCache.set(cacheKey, testData, {}, 200);
      const setTime = Date.now() - startTime1;

      // Second request - cache hit
      const startTime2 = Date.now();
      const cachedResult = await responseCache.get(cacheKey);
      const getTime = Date.now() - startTime2;

      expect(cachedResult).toBeTruthy();
      expect(cachedResult!.data).toEqual(testData);
      
      // Cache retrieval should be faster than setting
      expect(getTime).toBeLessThan(setTime);
      
      console.log(`Cache performance: Set ${setTime}ms, Get ${getTime}ms`);

    it('should handle large datasets efficiently', async () => {
      const largeData = Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        name: `Item ${i}`,
        description: `This is a description for item ${i}`.repeat(10),
      }));

      const startTime = Date.now();
      
      // Store large dataset
      await responseCache.set('large-dataset', largeData, {}, 200, {
        compress: true,

      // Retrieve large dataset
      const result = await responseCache.get('large-dataset');
      
      const endTime = Date.now();
      const totalTime = endTime - startTime;

      expect(result).toBeTruthy();
      expect(result!.data).toHaveLength(1000);
      
      // Should handle large data within reasonable time
      expect(totalTime).toBeLessThan(1000); // 1 second max
      
      const metrics = responseCache.getMetrics();
      console.log(`Large dataset cache: ${totalTime}ms, Memory: ${metrics.memoryUsage} bytes`);

    it('should maintain good hit rates under load', async () => {
      const requests = 100;
      const uniqueKeys = 20; // 80% cache hit rate expected
      
      // Populate cache
      for (let i = 0; i < uniqueKeys; i++) {
        await responseCache.set(`key-${i}`, { value: i }, {}, 200);
      }

      const startTime = Date.now();
      
      // Make requests with repeated keys
      for (let i = 0; i < requests; i++) {
        const keyIndex = i % uniqueKeys;
        await responseCache.get(`key-${keyIndex}`);
      }

      const endTime = Date.now();
      const totalTime = endTime - startTime;
      
      const metrics = responseCache.getMetrics();
      
      // Should have good hit rate
      expect(metrics.hitRate).toBeGreaterThan(0.7); // 70% hit rate minimum
      
      // Should be fast
      expect(totalTime).toBeLessThan(500); // 500ms max
      
      console.log(`Cache load test: ${requests} requests in ${totalTime}ms, Hit rate: ${(metrics.hitRate * 100).toFixed(1)}%`);


  describe('Database Query Optimizer Performance', () => {
    it('should cache authentication queries effectively', async () => {
      const email = 'test@example.com';
      const passwordHash = 'hashed_password';

      // First authentication - cache miss
      const startTime1 = Date.now();
      const result1 = await queryOptimizer.authenticateUser(email, passwordHash);
      const time1 = Date.now() - startTime1;

      // Second authentication - cache hit
      const startTime2 = Date.now();
      const result2 = await queryOptimizer.authenticateUser(email, passwordHash);
      const time2 = Date.now() - startTime2;

      expect(result1).toEqual(result2);
      
      // Second query should be faster due to caching
      expect(time2).toBeLessThan(time1);
      
      const metrics = queryOptimizer.getMetrics();
      expect(metrics.cacheHits).toBeGreaterThan(0);
      
      console.log(`Auth query performance: First ${time1}ms, Cached ${time2}ms`);

    it('should handle concurrent database queries', async () => {
      const concurrentQueries = 10;
      const userIds = Array.from({ length: concurrentQueries }, (_, i) => `user-${i}`);

      const startTime = Date.now();
      
      // Execute concurrent queries
      const promises = userIds.map(userId => queryOptimizer.getUserById(userId));
      const results = await Promise.all(promises);
      
      const endTime = Date.now();
      const totalTime = endTime - startTime;

      expect(results).toHaveLength(concurrentQueries);
      
      // Should complete within reasonable time
      expect(totalTime).toBeLessThan(2000); // 2 seconds max
      
      const metrics = queryOptimizer.getMetrics();
      console.log(`Concurrent queries: ${concurrentQueries} queries in ${totalTime}ms`);
      console.log(`Query metrics:`, metrics);

    it('should identify and track slow queries', async () => {
      // Mock a slow query by using a complex operation
      const complexQuery = 'SELECT * FROM users WHERE complex_condition = $1';
      
      const startTime = Date.now();
      await queryOptimizer.executeAuthQuery(complexQuery, ['complex_value']);
      const endTime = Date.now();
      
      const metrics = queryOptimizer.getMetrics();
      
      // Should track the query
      expect(metrics.totalQueries).toBeGreaterThan(0);
      expect(metrics.averageQueryTime).toBeGreaterThan(0);


  describe('Integrated Performance Optimizer', () => {
    it('should provide comprehensive performance optimization', async () => {
      // Mock successful API response
      (global.fetch as any).mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true, data: 'test' }),

      const startTime = Date.now();
      
      // Make optimized request
      const result = await performanceOptimizer.optimizedRequest(
        'https://api.example.com/test',
        { method: 'GET' },
        {
          useConnectionPool: true,
          enableCaching: true,
          cacheOptions: {
            ttl: 60000,
            tags: ['test'],
          },
        }
      );

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      expect(result).toBeTruthy();
      expect(totalTime).toBeLessThan(1000); // 1 second max
      
      const metrics = performanceOptimizer.getMetrics();
      console.log(`Integrated performance test: ${totalTime}ms`);
      console.log(`Performance metrics:`, metrics);

    it('should handle authentication flow efficiently', async () => {
      // Mock authentication response
      (global.fetch as any).mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          access_token: 'test-token',
          user: { id: 'test-user', email: 'test@example.com' },
        }),

      const startTime = Date.now();
      
      // Authenticate user
      const authResult = await performanceOptimizer.authenticateUser(
        'test@example.com',
        'password123'
      );

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      expect(authResult).toBeTruthy();
      expect(totalTime).toBeLessThan(2000); // 2 seconds max
      
      console.log(`Authentication flow: ${totalTime}ms`);

    it('should provide performance recommendations', () => {
      const recommendations = performanceOptimizer.getPerformanceRecommendations();
      
      expect(Array.isArray(recommendations)).toBe(true);
      
      // Should provide actionable recommendations
      console.log('Performance recommendations:', recommendations);

    it('should handle cache invalidation correctly', () => {
      // Test cache invalidation
      const clearedCount = performanceOptimizer.invalidateCache(['test', 'user']);
      
      expect(typeof clearedCount).toBe('number');
      expect(clearedCount).toBeGreaterThanOrEqual(0);


  describe('Performance Regression Tests', () => {
    it('should maintain performance under memory pressure', async () => {
      // Create memory pressure by caching many items
      const itemCount = 1000;
      
      const startTime = Date.now();
      
      for (let i = 0; i < itemCount; i++) {
        await responseCache.set(`item-${i}`, { id: i, data: `data-${i}` }, {}, 200);
      }
      
      // Retrieve items
      for (let i = 0; i < itemCount; i++) {
        await responseCache.get(`item-${i}`);
      }
      
      const endTime = Date.now();
      const totalTime = endTime - startTime;
      
      // Should handle large number of items efficiently
      expect(totalTime).toBeLessThan(5000); // 5 seconds max
      
      const metrics = responseCache.getMetrics();
      console.log(`Memory pressure test: ${itemCount} items in ${totalTime}ms`);
      console.log(`Memory usage: ${metrics.memoryUsage} bytes`);

    it('should maintain connection pool efficiency under load', async () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        json: async () => ({ success: true }),

      const requestCount = 100;
      const batchSize = 10;
      
      const startTime = Date.now();
      
      // Make requests in batches to simulate real load
      for (let batch = 0; batch < requestCount / batchSize; batch++) {
        const batchPromises = Array.from({ length: batchSize }, (_, i) =>
          connectionPool.request(`https://api.example.com/batch/${batch}-${i}`, { method: 'GET' })
        );
        
        await Promise.all(batchPromises);
      }
      
      const endTime = Date.now();
      const totalTime = endTime - startTime;
      
      const metrics = connectionPool.getMetrics();
      
      // Should maintain good performance
      expect(totalTime).toBeLessThan(10000); // 10 seconds max
      expect(metrics.connectionReuse).toBeGreaterThan(requestCount / 2); // Good reuse ratio
      
      console.log(`Load test: ${requestCount} requests in ${totalTime}ms`);
      console.log(`Connection reuse: ${metrics.connectionReuse}`);



describe('Performance Benchmarking Utilities', () => {
  it('should measure request latency accurately', async () => {
    const measurements: number[] = [];
    const iterations = 10;
    
    const testConnectionPool = initializeHttpConnectionPool({
      maxConnections: 5,
      maxConnectionsPerHost: 2,

    (global.fetch as any).mockImplementation(() => 
      new Promise(resolve => {
        setTimeout(() => resolve({
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: new Headers(),
          json: async () => ({ success: true }),
        }), Math.random() * 100 + 50); // 50-150ms delay
      })
    );

    for (let i = 0; i < iterations; i++) {
      const startTime = Date.now();
      await testConnectionPool.request('https://api.example.com/latency-test', { method: 'GET' });
      const endTime = Date.now();
      measurements.push(endTime - startTime);
    }

    await testConnectionPool.shutdown();

    const averageLatency = measurements.reduce((sum, time) => sum + time, 0) / measurements.length;
    const minLatency = Math.min(...measurements);
    const maxLatency = Math.max(...measurements);
    
    console.log(`Latency measurements over ${iterations} requests:`);
    console.log(`Average: ${averageLatency.toFixed(2)}ms`);
    console.log(`Min: ${minLatency}ms, Max: ${maxLatency}ms`);
    
    expect(averageLatency).toBeGreaterThan(0);
    expect(minLatency).toBeLessThan(maxLatency);

  it('should measure throughput accurately', async () => {
    const testConnectionPool = initializeHttpConnectionPool({
      maxConnections: 5,
      maxConnectionsPerHost: 2,

    (global.fetch as any).mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      headers: new Headers(),
      json: async () => ({ success: true }),

    const duration = 1000; // 1 second for faster test
    const startTime = Date.now();
    let requestCount = 0;
    
    // Make requests for the specified duration
    while (Date.now() - startTime < duration) {
      await testConnectionPool.request(`https://api.example.com/throughput-${requestCount}`, { method: 'GET' });
      requestCount++;
    }

    await testConnectionPool.shutdown();
    
    const actualDuration = Date.now() - startTime;
    const throughput = (requestCount / actualDuration) * 1000; // requests per second
    
    console.log(`Throughput test: ${requestCount} requests in ${actualDuration}ms`);
    console.log(`Throughput: ${throughput.toFixed(2)} requests/second`);
    
    expect(throughput).toBeGreaterThan(0);
    expect(requestCount).toBeGreaterThan(0);

