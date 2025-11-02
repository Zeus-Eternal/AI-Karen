/**
 * HTTP Connection Pool Tests
 * 
 * Unit tests for HTTP connection pooling functionality.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { HttpConnectionPool } from '../http-connection-pool';

// Mock fetch
global.fetch = vi.fn();

describe('HttpConnectionPool', () => {
  let connectionPool: HttpConnectionPool;

  beforeEach(() => {
    vi.clearAllMocks();
    connectionPool = new HttpConnectionPool({
      maxConnections: 5,
      maxConnectionsPerHost: 2,
      connectionTimeout: 1000,
      enableKeepAlive: true,


  afterEach(async () => {
    await connectionPool.shutdown();

  describe('Basic Functionality', () => {
    it('should create connection pool with correct configuration', () => {
      const config = connectionPool.getConfig();
      
      expect(config.maxConnections).toBe(5);
      expect(config.maxConnectionsPerHost).toBe(2);
      expect(config.connectionTimeout).toBe(1000);
      expect(config.enableKeepAlive).toBe(true);

    it('should make successful HTTP requests', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true }),
      };

      (global.fetch as any).mockResolvedValue(mockResponse);

      const response = await connectionPool.request('https://api.example.com/test');
      
      expect(response.ok).toBe(true);
      expect(response.status).toBe(200);
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/test',
        expect.objectContaining({
          headers: expect.any(Headers),
          signal: expect.any(AbortSignal),
        })
      );

    it('should handle request failures', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      await expect(
        connectionPool.request('https://api.example.com/fail')
      ).rejects.toThrow('Network error');


  describe('Connection Pooling', () => {
    it('should reuse connections for the same host', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        json: async () => ({ success: true }),
      };

      (global.fetch as any).mockResolvedValue(mockResponse);

      // Make multiple requests to the same host
      await connectionPool.request('https://api.example.com/test1');
      await connectionPool.request('https://api.example.com/test2');
      await connectionPool.request('https://api.example.com/test3');

      const metrics = connectionPool.getMetrics();
      
      expect(metrics.connectionReuse).toBeGreaterThan(0);
      expect(metrics.totalConnections).toBeLessThan(3);

    it('should respect connection limits per host', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        json: async () => ({ success: true }),
      };

      (global.fetch as any).mockResolvedValue(mockResponse);

      // Make requests that would exceed per-host limit
      const promises = Array.from({ length: 5 }, (_, i) =>
        connectionPool.request(`https://api.example.com/test${i}`)
      );

      await Promise.all(promises);

      const metrics = connectionPool.getMetrics();
      
      // Should not exceed maxConnectionsPerHost (2)
      expect(metrics.totalConnections).toBeLessThanOrEqual(2);


  describe('Keep-Alive Headers', () => {
    it('should add keep-alive headers when enabled', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        json: async () => ({ success: true }),
      };

      (global.fetch as any).mockResolvedValue(mockResponse);

      await connectionPool.request('https://api.example.com/test');

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/test',
        expect.objectContaining({
          headers: expect.any(Headers),
        })
      );

      // Check that keep-alive headers were added
      const call = (global.fetch as any).mock.calls[0];
      const headers = call[1].headers;
      
      expect(headers.get('Connection')).toBe('keep-alive');
      expect(headers.get('Keep-Alive')).toContain('timeout=');


  describe('Metrics and Monitoring', () => {
    it('should track connection metrics', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        json: async () => ({ success: true }),
      };

      (global.fetch as any).mockResolvedValue(mockResponse);

      // Make some requests
      await connectionPool.request('https://api.example.com/test1');
      await connectionPool.request('https://api.example.com/test2');

      const metrics = connectionPool.getMetrics();
      
      expect(metrics.totalConnections).toBeGreaterThan(0);
      expect(metrics.connectionCreations).toBeGreaterThan(0);
      expect(metrics.connectionReuse).toBeGreaterThan(0);
      expect(typeof metrics.averageConnectionTime).toBe('number');

    it('should track request queue metrics', async () => {
      // Mock slow responses to create queue
      (global.fetch as any).mockImplementation(() =>
        new Promise(resolve => {
          setTimeout(() => resolve({
            ok: true,
            status: 200,
            statusText: 'OK',
            headers: new Headers(),
            json: async () => ({ success: true }),
          }), 100);
        })
      );

      // Make more requests than connection limit
      const promises = Array.from({ length: 10 }, (_, i) =>
        connectionPool.request(`https://api.example.com/test${i}`)
      );

      // Don't wait for all to complete, just check metrics
      setTimeout(() => {
        const metrics = connectionPool.getMetrics();
        expect(metrics.queuedRequests).toBeGreaterThanOrEqual(0);
      }, 50);

      await Promise.all(promises);


  describe('Error Handling', () => {
    it('should handle timeout errors', async () => {
      // Mock a request that never resolves
      (global.fetch as any).mockImplementation(() => new Promise(() => {}));

      const shortTimeoutPool = new HttpConnectionPool({
        connectionTimeout: 100, // Very short timeout

      await expect(
        shortTimeoutPool.request('https://api.example.com/timeout')
      ).rejects.toThrow();

      await shortTimeoutPool.shutdown();

    it('should handle network errors gracefully', async () => {
      (global.fetch as any).mockRejectedValue(new Error('ECONNREFUSED'));

      await expect(
        connectionPool.request('https://api.example.com/unreachable')
      ).rejects.toThrow('ECONNREFUSED');

      const metrics = connectionPool.getMetrics();
      expect(metrics.connectionTimeouts).toBeGreaterThan(0);


  describe('Cleanup and Shutdown', () => {
    it('should cleanup expired connections', async () => {
      const shortIdlePool = new HttpConnectionPool({
        maxIdleTime: 100, // Very short idle time

      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        json: async () => ({ success: true }),
      };

      (global.fetch as any).mockResolvedValue(mockResponse);

      // Make a request to create a connection
      await shortIdlePool.request('https://api.example.com/test');

      // Wait for connection to expire
      await new Promise(resolve => setTimeout(resolve, 200));

      const metrics = shortIdlePool.getMetrics();
      
      // Connection should be cleaned up
      expect(metrics.idleConnections).toBe(0);

      await shortIdlePool.shutdown();

    it('should shutdown gracefully', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Headers(),
        json: async () => ({ success: true }),
      };

      (global.fetch as any).mockResolvedValue(mockResponse);

      // Make some requests
      await connectionPool.request('https://api.example.com/test1');
      await connectionPool.request('https://api.example.com/test2');

      // Shutdown should complete without errors
      await expect(connectionPool.shutdown()).resolves.toBeUndefined();

      const metrics = connectionPool.getMetrics();
      expect(metrics.totalConnections).toBe(0);


