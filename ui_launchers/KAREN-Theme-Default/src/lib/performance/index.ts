/**
 * Performance Optimization Library
 *
 * Exports all performance optimization components:
 *  - HTTP connection pooling
 *  - Request/response caching
 *  - Database query optimization
 *  - Integrated performance manager
 *
 * Requirements: 1.4, 4.4
 */

/* ----------------------------------------
 * HTTP Connection Pool (static re-exports)
 * -------------------------------------- */
import {
  getHttpConnectionPool,
  initializeHttpConnectionPool,
  shutdownHttpConnectionPool,
} from './http-connection-pool';

export { getHttpConnectionPool, initializeHttpConnectionPool, shutdownHttpConnectionPool };

export type {
  ConnectionPoolConfig,
  ConnectionMetrics,
  PooledConnection,
  QueuedRequest,
} from './http-connection-pool';

/* ----------------------------------------
 * Request/Response Cache (static re-exports)
 * -------------------------------------- */
import {
  getRequestResponseCache,
  initializeRequestResponseCache,
  shutdownRequestResponseCache,
} from './request-response-cache';

export { getRequestResponseCache, initializeRequestResponseCache, shutdownRequestResponseCache };

export type {
  CacheConfig,
  CacheEntry,
  CacheMetrics,
  CacheOptions,
} from './request-response-cache';

/* ----------------------------------------
 * Database Query Optimizer (static re-exports)
 * -------------------------------------- */
import {
  getDatabaseQueryOptimizer,
  initializeDatabaseQueryOptimizer,
  shutdownDatabaseQueryOptimizer,
} from './database-query-optimizer';

export { getDatabaseQueryOptimizer, initializeDatabaseQueryOptimizer, shutdownDatabaseQueryOptimizer };

export type {
  QueryOptimizationConfig,
  QueryMetrics,
  QueryCacheEntry,
  PreparedStatement,
  QueryPlan,
} from './database-query-optimizer';

/* ----------------------------------------
 * Performance Optimizer (integration layer)
 * -------------------------------------- */
import {
  getPerformanceOptimizer,
  initializePerformanceOptimizer,
  shutdownPerformanceOptimizer,
} from './performance-optimizer';

export { getPerformanceOptimizer, initializePerformanceOptimizer, shutdownPerformanceOptimizer };

export type {
  PerformanceConfig,
  PerformanceMetrics,
  OptimizedRequestOptions,
} from './performance-optimizer';

/* ----------------------------------------
 * PerformanceUtils (runtime helpers)
 * - Uses dynamic imports to avoid circular deps
 * - Safe to call from anywhere
 * -------------------------------------- */

export const PerformanceUtils = {
  /**
   * Initialize all performance optimization components.
   * Returns the initialized PerformanceOptimizer singleton.
   */
  async initializeAll(config?: {
    connectionPool?: Partial<import('./http-connection-pool').ConnectionPoolConfig>;
    responseCache?: Partial<import('./request-response-cache').CacheConfig>;
    queryOptimizer?: Partial<import('./database-query-optimizer').QueryOptimizationConfig>;
    enableMetrics?: boolean;
    metricsInterval?: number;
  }) {
    const [
      poolMod,
      cacheMod,
      dbqMod,
      perfMod,
    ] = await Promise.all([
      import('./http-connection-pool'),
      import('./request-response-cache'),
      import('./database-query-optimizer'),
      import('./performance-optimizer'),
    ]);

    // Initialize leaf components first (idempotent in your impls)
    if (config?.connectionPool) {
      poolMod.initializeHttpConnectionPool(config.connectionPool);
    }
    if (config?.responseCache) {
      cacheMod.initializeRequestResponseCache(config.responseCache);
    }
    if (config?.queryOptimizer) {
      dbqMod.initializeDatabaseQueryOptimizer(config.queryOptimizer);
    }

    // Initialize the integrated optimizer last
    return perfMod.initializePerformanceOptimizer({
      connectionPool: config?.connectionPool ?? {},
      responseCache: config?.responseCache ?? {},
      queryOptimizer: config?.queryOptimizer ?? {},
      enableMetrics: config?.enableMetrics ?? true,
      metricsInterval: config?.metricsInterval ?? 60_000,
    });
  },

  /**
   * Shutdown all components gracefully.
   * Order: integrated optimizer → individual subsystems (best-effort).
   */
  async shutdownAll() {
    const [poolMod, cacheMod, dbqMod, perfMod] = await Promise.all([
      import('./http-connection-pool'),
      import('./request-response-cache'),
      import('./database-query-optimizer'),
      import('./performance-optimizer'),
    ]);

    // The performance optimizer may already call its own sub-shutdowns;
    // we still best-effort close the leaves for safety.
    try {
      await perfMod.shutdownPerformanceOptimizer();
    } catch (err) {
      console.warn('[PERF] Performance optimizer shutdown failed:', err);
    }
    try {
      await poolMod.shutdownHttpConnectionPool();
    } catch (err) {
      console.warn('[PERF] HTTP connection pool shutdown failed:', err);
    }
    try {
      cacheMod.shutdownRequestResponseCache();
    } catch (err) {
      console.warn('[PERF] Response cache shutdown failed:', err);
    }
    try {
      dbqMod.shutdownDatabaseQueryOptimizer();
    } catch (err) {
      console.warn('[PERF] Database query optimizer shutdown failed:', err);
    }
  },

  /**
   * Get comprehensive, point-in-time metrics across all components.
   */
  async getComprehensiveMetrics() {
    try {
      const [
        poolMod,
        cacheMod,
        dbqMod,
        perfMod,
      ] = await Promise.all([
        import('./http-connection-pool'),
        import('./request-response-cache'),
        import('./database-query-optimizer'),
        import('./performance-optimizer'),
      ]);

      const pool = poolMod.getHttpConnectionPool();
      const cache = cacheMod.getRequestResponseCache();
      const dbq  = dbqMod.getDatabaseQueryOptimizer();
      const perf = perfMod.getPerformanceOptimizer();

      return {
        connectionPool: pool.getMetrics(),
        responseCache: cache.getMetrics(),
        queryOptimizer: dbq.getMetrics(),
        overall: perf.getMetrics(),
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      return {
        error: (error as Error)?.message ?? 'Failed to collect metrics',
        timestamp: new Date().toISOString(),
      };
    }
  },

  /**
   * Get current performance recommendations (human-readable).
   */
  async getPerformanceRecommendations(): Promise<string[]> {
    try {
      const perfMod = await import('./performance-optimizer');
      const perf = perfMod.getPerformanceOptimizer();
      return perf.getPerformanceRecommendations();
    } catch {
      return ['Performance optimization is not initialized'];
    }
  },

  /**
   * Auto-optimize tunables across components based on live metrics.
   */
  async autoOptimizeAll() {
    try {
      const perfMod = await import('./performance-optimizer');
      const perf = perfMod.getPerformanceOptimizer();
      perf.autoOptimize();
    } catch {
      // Silently ignore if not initialized
    }
  },

  /**
   * Clear all caches (response cache + DB query cache).
   */
  async clearAllCaches() {
    try {
      const [cacheMod, dbqMod] = await Promise.all([
        import('./request-response-cache'),
        import('./database-query-optimizer'),
      ]);
      cacheMod.getRequestResponseCache().clear();
      dbqMod.getDatabaseQueryOptimizer().clearCache?.();
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Invalidate caches that relate to a specific user.
   */
  async invalidateUserCaches(userId: string) {
    try {
      const perfMod = await import('./performance-optimizer');
      const perf = perfMod.getPerformanceOptimizer();
      perf.invalidateUserCache(userId);
      return true;
    } catch {
      return false;
    }
  },
};

/* ----------------------------------------
 * Default export: names + utils
 * -------------------------------------- */
const _default = {
  // Pools
  getHttpConnectionPool,
  initializeHttpConnectionPool,
  shutdownHttpConnectionPool,

  // Cache
  getRequestResponseCache,
  initializeRequestResponseCache,
  shutdownRequestResponseCache,

  // DB Query Optimizer
  getDatabaseQueryOptimizer,
  initializeDatabaseQueryOptimizer,
  shutdownDatabaseQueryOptimizer,

  // Integrated Optimizer
  getPerformanceOptimizer,
  initializePerformanceOptimizer,
  shutdownPerformanceOptimizer,

  // Utils
  PerformanceUtils,
};

export default _default;
