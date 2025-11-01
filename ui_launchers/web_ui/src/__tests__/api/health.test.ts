/**
 * Tests for Health Check API Endpoint
 * 
 * Comprehensive test suite for health monitoring endpoints
 * including system metrics, dependency checks, and error scenarios.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { NextRequest } from 'next/server';
import { GET } from '../../app/api/health/route';

// Mock external dependencies
vi.mock('fs/promises', () => ({
  access: vi.fn(),
  writeFile: vi.fn(),
  unlink: vi.fn(),
  constants: {
    F_OK: 0
  }
}));

vi.mock('path', () => ({
  join: vi.fn((...args) => args.join('/'))
}));

vi.mock('os', () => ({
  loadavg: vi.fn(() => [0.5, 0.7, 0.8]),
  totalmem: vi.fn(() => 8589934592), // 8GB
  freemem: vi.fn(() => 4294967296)   // 4GB
}));

describe('Health Check API', () => {
  let mockRequest: NextRequest;

  beforeEach(() => {
    // Mock NextRequest
    mockRequest = {
      url: 'http://localhost:3000/api/health',
      method: 'GET',
      headers: new Headers()
    } as NextRequest;

    // Mock process methods
    vi.spyOn(process, 'memoryUsage').mockReturnValue({
      rss: 100 * 1024 * 1024,      // 100MB
      heapTotal: 200 * 1024 * 1024, // 200MB
      heapUsed: 150 * 1024 * 1024,  // 150MB
      external: 10 * 1024 * 1024,   // 10MB
      arrayBuffers: 5 * 1024 * 1024  // 5MB
    });

    vi.spyOn(process, 'uptime').mockReturnValue(3600); // 1 hour
    vi.spyOn(process, 'cpuUsage').mockReturnValue({
      user: 1000000,    // 1 second
      system: 500000    // 0.5 seconds
    });

    // Mock environment variables
    process.env.npm_package_version = '1.0.0';
    process.env.NODE_ENV = 'test';

    // Clear any existing timers
    vi.clearAllTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  describe('Basic Health Check', () => {
    it('should return healthy status when all checks pass', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.status).toBe('healthy');
      expect(data.timestamp).toBeDefined();
      expect(data.version).toBe('1.0.0');
      expect(data.uptime).toBe(3600);
    });

    it('should include all required health checks', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks).toHaveProperty('database');
      expect(data.checks).toHaveProperty('redis');
      expect(data.checks).toHaveProperty('external_apis');
      expect(data.checks).toHaveProperty('filesystem');
      expect(data.checks).toHaveProperty('memory');
      expect(data.checks).toHaveProperty('performance');
    });

    it('should include system metrics', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.metrics).toHaveProperty('memory');
      expect(data.metrics).toHaveProperty('performance');
      expect(data.metrics).toHaveProperty('requests');

      expect(data.metrics.memory).toHaveProperty('rss');
      expect(data.metrics.memory).toHaveProperty('heapTotal');
      expect(data.metrics.memory).toHaveProperty('heapUsed');
      expect(data.metrics.memory).toHaveProperty('heapUsagePercent');
    });

    it('should include environment information', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.environment).toHaveProperty('nodeVersion');
      expect(data.environment).toHaveProperty('platform');
      expect(data.environment).toHaveProperty('environment');
      expect(data.environment.environment).toBe('test');
    });
  });

  describe('Database Health Check', () => {
    it('should report database as healthy when connection succeeds', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.database.status).toBe('healthy');
      expect(data.checks.database.message).toContain('successful');
      expect(data.checks.database.responseTime).toBeGreaterThan(0);
      expect(data.checks.database.details).toHaveProperty('connectionPool');
    });

    it('should include database connection details', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.database.details).toHaveProperty('activeConnections');
      expect(data.checks.database.details).toHaveProperty('maxConnections');
      expect(data.checks.database.details.activeConnections).toBe(5);
      expect(data.checks.database.details.maxConnections).toBe(20);
    });
  });

  describe('Redis Health Check', () => {
    it('should report Redis as healthy when connection succeeds', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.redis.status).toBe('healthy');
      expect(data.checks.redis.message).toContain('successful');
      expect(data.checks.redis.responseTime).toBeGreaterThan(0);
      expect(data.checks.redis.details).toHaveProperty('connected');
    });

    it('should include Redis connection details', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.redis.details).toHaveProperty('memoryUsage');
      expect(data.checks.redis.details).toHaveProperty('keyCount');
      expect(data.checks.redis.details.connected).toBe(true);
      expect(data.checks.redis.details.keyCount).toBe(150);
    });
  });

  describe('External APIs Health Check', () => {
    it('should report external APIs as healthy when no APIs configured', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.external_apis.status).toBe('healthy');
      expect(data.checks.external_apis.message).toContain('accessible');
      expect(data.checks.external_apis.details).toHaveProperty('totalAPIs');
      expect(data.checks.external_apis.details.totalAPIs).toBe(0);
    });

    it('should include API check statistics', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.external_apis.details).toHaveProperty('successfulAPIs');
      expect(data.checks.external_apis.details).toHaveProperty('failedAPIs');
      expect(data.checks.external_apis.details.successfulAPIs).toBe(0);
      expect(data.checks.external_apis.details.failedAPIs).toBe(0);
    });
  });

  describe('Filesystem Health Check', () => {
    it('should report filesystem as healthy when all paths accessible', async () => {
      const fs = await import('fs/promises');
      vi.mocked(fs.access).mockResolvedValue(undefined);
      vi.mocked(fs.writeFile).mockResolvedValue(undefined);
      vi.mocked(fs.unlink).mockResolvedValue(undefined);

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.filesystem.status).toBe('healthy');
      expect(data.checks.filesystem.message).toContain('accessible');
      expect(data.checks.filesystem.details).toHaveProperty('criticalPaths');
      expect(data.checks.filesystem.details).toHaveProperty('tempWritable');
    });

    it('should report filesystem as unhealthy when paths not accessible', async () => {
      const fs = await import('fs/promises');
      vi.mocked(fs.access).mockRejectedValue(new Error('Path not found'));

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.filesystem.status).toBe('unhealthy');
      expect(data.checks.filesystem.message).toContain('failed');
      expect(data.checks.filesystem.details).toHaveProperty('error');
    });

    it('should report filesystem as unhealthy when temp directory not writable', async () => {
      const fs = await import('fs/promises');
      vi.mocked(fs.access).mockResolvedValue(undefined);
      vi.mocked(fs.writeFile).mockRejectedValue(new Error('Permission denied'));

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.filesystem.status).toBe('unhealthy');
      expect(data.checks.filesystem.message).toContain('not writable');
    });
  });

  describe('Memory Health Check', () => {
    it('should report memory as healthy with normal usage', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.memory.status).toBe('healthy');
      expect(data.checks.memory.message).toContain('normal');
      expect(data.checks.memory.details).toHaveProperty('heapUsagePercent');
    });

    it('should report memory as degraded with high usage', async () => {
      vi.spyOn(process, 'memoryUsage').mockReturnValue({
        rss: 100 * 1024 * 1024,
        heapTotal: 200 * 1024 * 1024,
        heapUsed: 160 * 1024 * 1024, // 80% usage
        external: 10 * 1024 * 1024,
        arrayBuffers: 5 * 1024 * 1024
      });

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.memory.status).toBe('degraded');
      expect(data.checks.memory.message).toContain('High memory');
    });

    it('should report memory as unhealthy with critical usage', async () => {
      vi.spyOn(process, 'memoryUsage').mockReturnValue({
        rss: 100 * 1024 * 1024,
        heapTotal: 200 * 1024 * 1024,
        heapUsed: 185 * 1024 * 1024, // 92.5% usage
        external: 10 * 1024 * 1024,
        arrayBuffers: 5 * 1024 * 1024
      });

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.memory.status).toBe('unhealthy');
      expect(data.checks.memory.message).toContain('Critical memory');
    });

    it('should include detailed memory metrics', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.memory.details).toHaveProperty('rss');
      expect(data.checks.memory.details).toHaveProperty('heapTotal');
      expect(data.checks.memory.details).toHaveProperty('heapUsed');
      expect(data.checks.memory.details).toHaveProperty('heapUsagePercent');
      expect(data.checks.memory.details).toHaveProperty('external');

      expect(data.checks.memory.details.rss).toContain('MB');
      expect(data.checks.memory.details.heapUsagePercent).toContain('%');
    });
  });

  describe('Performance Health Check', () => {
    it('should report performance as healthy with normal metrics', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.performance.status).toBe('healthy');
      expect(data.checks.performance.message).toContain('normal');
      expect(data.checks.performance.details).toHaveProperty('uptime');
    });

    it('should report performance as degraded with recent restart', async () => {
      vi.spyOn(process, 'uptime').mockReturnValue(30); // 30 seconds

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.performance.status).toBe('degraded');
      expect(data.checks.performance.message).toContain('Recent restart');
    });

    it('should include detailed performance metrics', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.performance.details).toHaveProperty('uptime');
      expect(data.checks.performance.details).toHaveProperty('cpuUser');
      expect(data.checks.performance.details).toHaveProperty('cpuSystem');
      expect(data.checks.performance.details).toHaveProperty('pid');
      expect(data.checks.performance.details).toHaveProperty('platform');
      expect(data.checks.performance.details).toHaveProperty('nodeVersion');

      expect(data.checks.performance.details.uptime).toContain('s');
      expect(data.checks.performance.details.cpuUser).toContain('ms');
      expect(data.checks.performance.details.cpuSystem).toContain('ms');
    });
  });

  describe('Overall Health Status', () => {
    it('should return healthy when all checks pass', async () => {
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.status).toBe('healthy');
      expect(response.status).toBe(200);
    });

    it('should return degraded when some checks are degraded', async () => {
      // Mock high memory usage to trigger degraded state
      vi.spyOn(process, 'memoryUsage').mockReturnValue({
        rss: 100 * 1024 * 1024,
        heapTotal: 200 * 1024 * 1024,
        heapUsed: 160 * 1024 * 1024, // 80% usage
        external: 10 * 1024 * 1024,
        arrayBuffers: 5 * 1024 * 1024
      });

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.status).toBe('degraded');
      expect(response.status).toBe(200);
    });

    it('should return unhealthy when any check fails', async () => {
      // Mock filesystem failure
      const fs = await import('fs/promises');
      vi.mocked(fs.access).mockRejectedValue(new Error('Path not found'));

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.status).toBe('unhealthy');
      expect(response.status).toBe(503);
    });
  });

  describe('Request Metrics Tracking', () => {
    it('should track successful requests', async () => {
      // Make multiple requests
      await GET(mockRequest);
      await GET(mockRequest);
      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.metrics.requests.total).toBeGreaterThan(0);
      expect(data.metrics.requests.successful).toBeGreaterThan(0);
      expect(data.metrics.requests.averageResponseTime).toBeGreaterThan(0);
    });

    it('should track failed requests', async () => {
      // Mock filesystem failure to cause request failure
      const fs = await import('fs/promises');
      vi.mocked(fs.access).mockRejectedValue(new Error('Path not found'));

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.metrics.requests.total).toBeGreaterThan(0);
      expect(data.metrics.requests.failed).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle unexpected errors gracefully', async () => {
      // Mock an unexpected error
      vi.spyOn(process, 'memoryUsage').mockImplementation(() => {
        throw new Error('Unexpected error');
      });

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(response.status).toBe(503);
      expect(data.status).toBe('unhealthy');
      expect(data.timestamp).toBeDefined();
    });

    it('should include error details in response', async () => {
      // Mock filesystem error
      const fs = await import('fs/promises');
      vi.mocked(fs.access).mockRejectedValue(new Error('Specific error message'));

      const response = await GET(mockRequest);
      const data = await response.json();

      expect(data.checks.filesystem.status).toBe('unhealthy');
      expect(data.checks.filesystem.details).toHaveProperty('error');
      expect(data.checks.filesystem.details.error).toContain('Specific error message');
    });
  });

  describe('Response Headers', () => {
    it('should include cache control headers', async () => {
      const response = await GET(mockRequest);

      expect(response.headers.get('Cache-Control')).toBe('no-cache, no-store, must-revalidate');
      expect(response.headers.get('Pragma')).toBe('no-cache');
      expect(response.headers.get('Expires')).toBe('0');
    });
  });

  describe('Performance', () => {
    it('should complete health check within reasonable time', async () => {
      const startTime = Date.now();
      await GET(mockRequest);
      const endTime = Date.now();

      const duration = endTime - startTime;
      expect(duration).toBeLessThan(5000); // Should complete within 5 seconds
    });

    it('should handle concurrent health checks', async () => {
      const promises = Array(10).fill(null).map(() => GET(mockRequest));
      const responses = await Promise.all(promises);

      responses.forEach(response => {
        expect(response.status).toBeOneOf([200, 503]);
      });
    });
  });
});