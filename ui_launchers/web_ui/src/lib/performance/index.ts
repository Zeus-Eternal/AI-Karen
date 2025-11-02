/**
 * Performance Optimization Library
 * 
 * Exports all performance optimization components including HTTP connection pooling,
 * request/response caching, database query optimization, and integrated performance management.
 * 
 * Requirements: 1.4, 4.4
 */
// HTTP Connection Pool
export {
  HttpConnectionPool,
  getHttpConnectionPool,
  initializeHttpConnectionPool,
  shutdownHttpConnectionPool,
  type ConnectionPoolConfig,
  type ConnectionMetrics,
  type PooledConnection,
  type QueuedRequest,
} from './http-connection-pool';
// Request/Response Cache
export {
  RequestResponseCache,
  getRequestResponseCache,
  initializeRequestResponseCache,
  shutdownRequestResponseCache,
  type CacheConfig,
  type CacheEntry,
  type CacheMetrics,
  type CacheOptions,
} from './request-response-cache';
// Database Query Optimizer
export {
  DatabaseQueryOptimizer,
  getDatabaseQueryOptimizer,
  initializeDatabaseQueryOptimizer,
  shutdownDatabaseQueryOptimizer,
  type QueryOptimizationConfig,
  type QueryMetrics,
  type QueryCacheEntry,
  type PreparedStatement,
  type QueryPlan,
} from './database-query-optimizer';
// Performance Optimizer (Main Integration)
export {
  PerformanceOptimizer,
  getPerformanceOptimizer,
  initializePerformanceOptimizer,
  shutdownPerformanceOptimizer,
  type PerformanceConfig,
  type PerformanceMetrics,
  type OptimizedRequestOptions,
} from './performance-optimizer';
// Utility functions for performance optimization
export const PerformanceUtils = {
  /**
   * Initialize all performance optimization components
   */
  async initializeAll(config?: {
    connectionPool?: Partial<import('./http-connection-pool').ConnectionPoolConfig>;
    responseCache?: Partial<import('./request-response-cache').CacheConfig>;
    queryOptimizer?: Partial<import('./database-query-optimizer').QueryOptimizationConfig>;
  }) {
    const { initializeHttpConnectionPool } = await import('./http-connection-pool');
    const { initializeRequestResponseCache } = await import('./request-response-cache');
    const { initializeDatabaseQueryOptimizer } = await import('./database-query-optimizer');
    const { initializePerformanceOptimizer } = await import('./performance-optimizer');
    // Initialize individual components
    if (config?.connectionPool) {
      initializeHttpConnectionPool(config.connectionPool);
    }
    if (config?.responseCache) {
      initializeRequestResponseCache(config.responseCache);
    }
    if (config?.queryOptimizer) {
      initializeDatabaseQueryOptimizer(config.queryOptimizer);
    }
    // Initialize main performance optimizer
    return initializePerformanceOptimizer({
      connectionPool: config?.connectionPool || {},
      responseCache: config?.responseCache || {},
      queryOptimizer: config?.queryOptimizer || {},
      enableMetrics: true,
    });
  },
  /**
   * Shutdown all performance optimization components
   */
  async shutdownAll() {
    const { shutdownHttpConnectionPool } = await import('./http-connection-pool');
    const { shutdownRequestResponseCache } = await import('./request-response-cache');
    const { shutdownDatabaseQueryOptimizer } = await import('./database-query-optimizer');
    const { shutdownPerformanceOptimizer } = await import('./performance-optimizer');
    await Promise.all([
      shutdownHttpConnectionPool(),
      shutdownPerformanceOptimizer(),
    ]);
    shutdownRequestResponseCache();
    shutdownDatabaseQueryOptimizer();
  },
  /**
   * Get comprehensive performance metrics from all components
   */
  getComprehensiveMetrics() {
    const { getHttpConnectionPool } = require('./http-connection-pool');
    const { getRequestResponseCache } = require('./request-response-cache');
    const { getDatabaseQueryOptimizer } = require('./database-query-optimizer');
    const { getPerformanceOptimizer } = require('./performance-optimizer');
    try {
      const connectionPool = getHttpConnectionPool();
      const responseCache = getRequestResponseCache();
      const queryOptimizer = getDatabaseQueryOptimizer();
      const performanceOptimizer = getPerformanceOptimizer();
      return {
        connectionPool: connectionPool.getMetrics(),
        responseCache: responseCache.getMetrics(),
        queryOptimizer: queryOptimizer.getMetrics(),
        overall: performanceOptimizer.getMetrics(),
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        error: 'Failed to collect metrics',
        timestamp: new Date().toISOString(),
      };
    }
  },
  /**
   * Get performance recommendations from all components
   */
  getPerformanceRecommendations() {
    try {
      const { getPerformanceOptimizer } = require('./performance-optimizer');
      const performanceOptimizer = getPerformanceOptimizer();
      return performanceOptimizer.getPerformanceRecommendations();
    } catch (error) {
      return ['Performance optimization not initialized'];
    }
  },
  /**
   * Auto-optimize all components based on current metrics
   */
  autoOptimizeAll() {
    try {
      const { getPerformanceOptimizer } = require('./performance-optimizer');
      const performanceOptimizer = getPerformanceOptimizer();
      performanceOptimizer.autoOptimize();
    } catch (error) {
    }
  },
  /**
   * Clear all caches
   */
  clearAllCaches() {
    try {
      const { getRequestResponseCache } = require('./request-response-cache');
      const { getDatabaseQueryOptimizer } = require('./database-query-optimizer');
      const responseCache = getRequestResponseCache();
      const queryOptimizer = getDatabaseQueryOptimizer();
      responseCache.clear();
      queryOptimizer.clearCache();
      return true;
    } catch (error) {
      return false;
    }
  },
  /**
   * Invalidate caches for a specific user
   */
  invalidateUserCaches(userId: string) {
    try {
      const { getPerformanceOptimizer } = require('./performance-optimizer');
      const performanceOptimizer = getPerformanceOptimizer();
      performanceOptimizer.invalidateUserCache(userId);
      return true;
    } catch (error) {
      return false;
    }
  },
};
// Default export for convenience
export default {
  PerformanceUtils,
};
