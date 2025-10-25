/**
 * Admin Performance Tests
 * 
 * Tests performance of admin interfaces under load, including database queries,
 * API responses, and component rendering times.
 * 
 * Requirements: 7.3, 7.5
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { 
  DatabasePerformanceMonitor,
  ApiPerformanceMonitor,
  ComponentPerformanceMonitor,
  PerformanceReporter,
  adminPerformanceMonitor
} from '@/lib/performance/admin-performance-monitor';
import { QueryOptimizer, getQueryOptimizer } from '@/lib/database/query-optimizer';
import { AdminCacheManager, UserListCache, UserCache } from '@/lib/cache/admin-cache';
import type { UserListFilter, PaginationParams } from '@/types/admin';

// Mock database client for testing
const mockDbClient = {
  query: vi.fn(),
};

// Mock fetch for API tests
global.fetch = vi.fn();

describe('Admin Performance Tests', () => {
  let queryOptimizer: QueryOptimizer;

  beforeAll(() => {
    queryOptimizer = new QueryOptimizer(mockDbClient as any);
    adminPerformanceMonitor.startMonitoring({
      reportInterval: 1000,
      enableConsoleReports: false,
      enableRemoteReporting: false
    });
  });

  afterAll(() => {
    adminPerformanceMonitor.stopMonitoring();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    AdminCacheManager.clearAll();
  });

  describe('Database Query Performance', () => {
    it('should track database query performance', async () => {
      const endQuery = DatabasePerformanceMonitor.startQuery('test_query', 'SELECT * FROM users');
      
      // Simulate query execution time
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const metric = endQuery();
      
      expect(metric.type).toBe('database_query');
      expect(metric.name).toBe('test_query');
      expect(metric.duration).toBeGreaterThan(40);
      expect(metric.duration).toBeLessThan(100);
    });

    it('should identify slow database queries', async () => {
      const endQuery = DatabasePerformanceMonitor.startQuery('slow_query', 'SELECT * FROM large_table');
      
      // Simulate slow query
      await new Promise(resolve => setTimeout(resolve, 1100));
      
      endQuery();
      
      const slowQueries = DatabasePerformanceMonitor.getSlowQueries(1000);
      expect(slowQueries).toHaveLength(1);
      expect(slowQueries[0].name).toBe('slow_query');
    });

    it('should optimize user search queries', async () => {
      const mockUsers = Array.from({ length: 100 }, (_, i) => ({
        user_id: `user-${i}`,
        email: `user${i}@example.com`,
        full_name: `User ${i}`,
        role: 'user',
        is_active: true,
        is_verified: true,
        created_at: new Date(),
        updated_at: new Date(),
        last_login_at: new Date(),
        total_count: '100'
      }));

      mockDbClient.query.mockResolvedValue({ rows: mockUsers.slice(0, 20) });

      const filters: UserListFilter = { search: 'user' };
      const pagination: PaginationParams = { page: 1, limit: 20 };

      const startTime = performance.now();
      const result = await queryOptimizer.searchUsersOptimized(filters, pagination);
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(100); // Should be fast
      expect(result.data).toHaveLength(20);
      expect(result.pagination.total).toBe(100);
    });

    it('should handle bulk operations efficiently', async () => {
      mockDbClient.query.mockImplementation((query: string) => {
        if (query === 'BEGIN' || query === 'COMMIT') {
          return Promise.resolve({ rows: [] });
        }
        if (query.includes('bulk_update_users')) {
          return Promise.resolve({ rows: [{ updated_count: 50 }] });
        }
        return Promise.resolve({ rows: [] });
      });

      const userIds = Array.from({ length: 50 }, (_, i) => `user-${i}`);
      const updates = { is_active: false };

      const startTime = performance.now();
      const result = await queryOptimizer.bulkUpdateUsers(userIds, updates, 'admin-user');
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(200); // Bulk operations should be fast
      expect(result.success).toBe(true);
      expect(result.updatedCount).toBe(50);
    });
  });

  describe('API Performance', () => {
    it('should track API response times', async () => {
      const endRequest = ApiPerformanceMonitor.startRequest('/api/admin/users', 'GET');
      
      // Simulate API processing time
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const metric = endRequest(200, 1024);
      
      expect(metric.type).toBe('api_response');
      expect(metric.name).toBe('GET /api/admin/users');
      expect(metric.duration).toBeGreaterThan(90);
      expect(metric.metadata.statusCode).toBe(200);
      expect(metric.metadata.responseSize).toBe(1024);
    });

    it('should identify slow API requests', async () => {
      const endRequest = ApiPerformanceMonitor.startRequest('/api/admin/slow-endpoint', 'POST');
      
      // Simulate slow API call
      await new Promise(resolve => setTimeout(resolve, 2100));
      
      endRequest(200);
      
      const slowRequests = ApiPerformanceMonitor.getSlowRequests(2000);
      expect(slowRequests).toHaveLength(1);
      expect(slowRequests[0].name).toBe('POST /api/admin/slow-endpoint');
    });

    it('should handle concurrent API requests efficiently', async () => {
      const requests = Array.from({ length: 10 }, (_, i) => {
        const endRequest = ApiPerformanceMonitor.startRequest(`/api/admin/users/${i}`, 'GET');
        return new Promise(resolve => {
          setTimeout(() => {
            const metric = endRequest(200);
            resolve(metric);
          }, Math.random() * 100);
        });
      });

      const startTime = performance.now();
      await Promise.all(requests);
      const endTime = performance.now();

      // Concurrent requests should complete faster than sequential
      expect(endTime - startTime).toBeLessThan(500);
      
      const apiMetrics = ApiPerformanceMonitor.getApiMetrics();
      expect(apiMetrics.length).toBeGreaterThanOrEqual(10);
    });
  });

  describe('Component Render Performance', () => {
    it('should track component render times', async () => {
      const endRender = ComponentPerformanceMonitor.startRender('UserManagementTable');
      
      // Simulate component render time
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const metric = endRender();
      
      expect(metric.type).toBe('component_render');
      expect(metric.name).toBe('UserManagementTable');
      expect(metric.duration).toBeGreaterThan(40);
    });

    it('should identify slow component renders', async () => {
      const endRender = ComponentPerformanceMonitor.startRender('SlowComponent');
      
      // Simulate slow render
      await new Promise(resolve => setTimeout(resolve, 150));
      
      endRender();
      
      const slowRenders = ComponentPerformanceMonitor.getSlowRenders(100);
      expect(slowRenders).toHaveLength(1);
      expect(slowRenders[0].name).toBe('SlowComponent');
    });
  });

  describe('Cache Performance', () => {
    it('should improve performance with caching', async () => {
      const testData = { user_id: 'test-user', email: 'test@example.com' } as any;
      
      // First access (cache miss)
      const startTime1 = performance.now();
      UserCache.set(testData);
      const cached1 = await UserCache.get('test-user');
      const endTime1 = performance.now();
      
      // Second access (cache hit)
      const startTime2 = performance.now();
      const cached2 = await UserCache.get('test-user');
      const endTime2 = performance.now();
      
      expect(cached1).toEqual(testData);
      expect(cached2).toEqual(testData);
      expect(endTime2 - startTime2).toBeLessThan(endTime1 - startTime1);
    });

    it('should handle cache invalidation correctly', async () => {
      const testData = { user_id: 'test-user', email: 'test@example.com' } as any;
      
      UserCache.set(testData);
      expect(await UserCache.get('test-user')).toEqual(testData);
      
      UserCache.invalidate('test-user');
      expect(await UserCache.get('test-user')).toBeNull();
    });

    it('should provide cache statistics', () => {
      const testData = { user_id: 'test-user', email: 'test@example.com' } as any;
      UserCache.set(testData);
      
      const stats = UserCache.getStats();
      expect(stats.size).toBeGreaterThan(0);
      expect(stats.maxSize).toBeGreaterThan(0);
      expect(typeof stats.ttl).toBe('number');
    });
  });

  describe('Performance Reporting', () => {
    it('should generate comprehensive performance reports', async () => {
      // Generate some test metrics
      const endQuery = DatabasePerformanceMonitor.startQuery('test_query', 'SELECT 1');
      await new Promise(resolve => setTimeout(resolve, 10));
      endQuery();

      const endRequest = ApiPerformanceMonitor.startRequest('/api/test', 'GET');
      await new Promise(resolve => setTimeout(resolve, 20));
      endRequest(200);

      const endRender = ComponentPerformanceMonitor.startRender('TestComponent');
      await new Promise(resolve => setTimeout(resolve, 30));
      endRender();

      const report = PerformanceReporter.generateReport();

      expect(report.summary.totalMetrics).toBeGreaterThan(0);
      expect(report.database.queryCount).toBeGreaterThan(0);
      expect(report.api.requestCount).toBeGreaterThan(0);
      expect(report.components.renderCount).toBeGreaterThan(0);
      expect(Array.isArray(report.recommendations)).toBe(true);
    });

    it('should export metrics in different formats', async () => {
      // Generate test metric
      const endQuery = DatabasePerformanceMonitor.startQuery('export_test', 'SELECT 1');
      await new Promise(resolve => setTimeout(resolve, 10));
      endQuery();

      const jsonExport = PerformanceReporter.exportMetrics('json');
      const csvExport = PerformanceReporter.exportMetrics('csv');

      expect(typeof jsonExport).toBe('string');
      expect(jsonExport).toContain('export_test');
      
      expect(typeof csvExport).toBe('string');
      expect(csvExport).toContain('Type,Name,Duration');
      expect(csvExport).toContain('export_test');
    });
  });

  describe('Load Testing', () => {
    it('should handle high user list pagination load', async () => {
      const mockUsers = Array.from({ length: 1000 }, (_, i) => ({
        user_id: `user-${i}`,
        email: `user${i}@example.com`,
        full_name: `User ${i}`,
        role: 'user',
        is_active: true,
        is_verified: true,
        created_at: new Date(),
        updated_at: new Date(),
        last_login_at: new Date(),
        total_count: '1000'
      }));

      mockDbClient.query.mockResolvedValue({ rows: mockUsers.slice(0, 50) });

      const requests = Array.from({ length: 20 }, async (_, i) => {
        const filters: UserListFilter = {};
        const pagination: PaginationParams = { page: i + 1, limit: 50 };
        return queryOptimizer.searchUsersOptimized(filters, pagination);
      });

      const startTime = performance.now();
      const results = await Promise.all(requests);
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(1000); // Should handle 20 concurrent requests in < 1s
      expect(results).toHaveLength(20);
      results.forEach(result => {
        expect(result.data).toHaveLength(50);
      });
    });

    it('should handle bulk operations under load', async () => {
      mockDbClient.query.mockImplementation((query: string) => {
        if (query === 'BEGIN' || query === 'COMMIT') {
          return Promise.resolve({ rows: [] });
        }
        if (query.includes('bulk_update_users')) {
          return Promise.resolve({ rows: [{ updated_count: 100 }] });
        }
        return Promise.resolve({ rows: [] });
      });

      const bulkOperations = Array.from({ length: 5 }, async (_, i) => {
        const userIds = Array.from({ length: 100 }, (_, j) => `user-${i}-${j}`);
        return queryOptimizer.bulkUpdateUsers(userIds, { is_active: false }, 'admin-user');
      });

      const startTime = performance.now();
      const results = await Promise.all(bulkOperations);
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(2000); // 5 bulk operations in < 2s
      expect(results).toHaveLength(5);
      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.updatedCount).toBe(100);
      });
    });
  });

  describe('Memory Usage', () => {
    it('should monitor memory usage during operations', () => {
      const initialMemory = AdminCacheManager.getMemoryUsage();
      
      // Add data to caches
      for (let i = 0; i < 100; i++) {
        UserCache.set({
          user_id: `user-${i}`,
          email: `user${i}@example.com`,
          full_name: `User ${i}`,
          role: 'user',
          is_active: true,
          is_verified: true,
          created_at: new Date(),
          updated_at: new Date(),
          last_login_at: new Date(),
          tenant_id: 'default',
          preferences: {},
          roles: [],
          failed_login_attempts: 0,
          locked_until: null,
          two_factor_enabled: false,
          two_factor_secret: null
        });
      }
      
      const finalMemory = AdminCacheManager.getMemoryUsage();
      
      expect(finalMemory.users).toBeGreaterThan(initialMemory.users);
      expect(finalMemory.total).toBeGreaterThan(initialMemory.total);
    });

    it('should clean up memory when caches are cleared', () => {
      // Add data to caches
      for (let i = 0; i < 50; i++) {
        UserCache.set({
          user_id: `user-${i}`,
          email: `user${i}@example.com`,
          full_name: `User ${i}`,
          role: 'user',
          is_active: true,
          is_verified: true,
          created_at: new Date(),
          updated_at: new Date(),
          last_login_at: new Date(),
          tenant_id: 'default',
          preferences: {},
          roles: [],
          failed_login_attempts: 0,
          locked_until: null,
          two_factor_enabled: false,
          two_factor_secret: null
        });
      }
      
      const beforeClear = AdminCacheManager.getMemoryUsage();
      AdminCacheManager.clearAll();
      const afterClear = AdminCacheManager.getMemoryUsage();
      
      expect(afterClear.total).toBeLessThan(beforeClear.total);
    });
  });
});