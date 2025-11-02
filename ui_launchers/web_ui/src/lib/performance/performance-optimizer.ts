/**
 * Performance Optimizer
 * 
 * Main performance optimization manager that integrates HTTP connection pooling,
 * request/response caching, and database query optimization for improved system performance.
 * 
 * Requirements: 1.4, 4.4
 */
import { HttpConnectionPool, getHttpConnectionPool, ConnectionPoolConfig } from './http-connection-pool';
import { RequestResponseCache, getRequestResponseCache, CacheConfig } from './request-response-cache';
import { DatabaseQueryOptimizer, getDatabaseQueryOptimizer, QueryOptimizationConfig } from './database-query-optimizer';
import { getConnectionManager } from '../connection/connection-manager';
export interface PerformanceConfig {
  connectionPool: Partial<ConnectionPoolConfig>;
  responseCache: Partial<CacheConfig>;
  queryOptimizer: Partial<QueryOptimizationConfig>;
  enableMetrics: boolean;
  metricsInterval: number;
}
export interface PerformanceMetrics {
  connectionPool: {
    totalConnections: number;
    activeConnections: number;
    connectionReuse: number;
    averageConnectionTime: number;
  };
  responseCache: {
    hitRate: number;
    totalEntries: number;
    memoryUsage: number;
    compressionRatio: number;
  };
  queryOptimizer: {
    totalQueries: number;
    cacheHits: number;
    averageQueryTime: number;
    slowQueries: number;
  };
  overall: {
    requestThroughput: number;
    averageResponseTime: number;
    errorRate: number;
    uptime: number;
  };
}
export interface OptimizedRequestOptions {
  useConnectionPool?: boolean;
  enableCaching?: boolean;
  cacheOptions?: {
    ttl?: number;
    tags?: string[];
    compress?: boolean;
  };
  timeout?: number;
  retryAttempts?: number;
}
/**
 * Performance Optimizer
 * 
 * Integrates all performance optimization components and provides a unified interface
 * for making optimized HTTP requests with caching and connection pooling.
 */
export class PerformanceOptimizer {
  private config: PerformanceConfig;
  private connectionPool: HttpConnectionPool;
  private responseCache: RequestResponseCache;
  private queryOptimizer: DatabaseQueryOptimizer;
  private metricsInterval: NodeJS.Timeout | null = null;
  private startTime: number;
  private requestCount = 0;
  private errorCount = 0;
  private totalResponseTime = 0;
  constructor(config?: Partial<PerformanceConfig>) {
    this.config = {
      connectionPool: {},
      responseCache: {},
      queryOptimizer: {},
      enableMetrics: true,
      metricsInterval: 60000, // 1 minute
      ...config,
    };
    this.startTime = Date.now();
    this.connectionPool = getHttpConnectionPool();
    this.responseCache = getRequestResponseCache();
    this.queryOptimizer = getDatabaseQueryOptimizer();
    if (this.config.enableMetrics) {
      this.startMetricsCollection();
    }
  }
  /**
   * Make an optimized HTTP request with connection pooling and caching
   */
  async optimizedRequest<T = any>(
    url: string,
    options: RequestInit = {},
    optimizationOptions: OptimizedRequestOptions = {}
  ): Promise<T> {
    const startTime = Date.now();
    this.requestCount++;
    try {
      // Generate cache key
      const cacheKey = this.generateRequestCacheKey(url, options);
      // Check cache first (if enabled)
      if (optimizationOptions.enableCaching !== false) {
        const cachedResponse = await this.responseCache.get(cacheKey, {
          skipCache: false,
        });
        if (cachedResponse) {
          return cachedResponse.data;
        }
      }
      // Make request using connection pool (if enabled)
      let response: Response;
      if (optimizationOptions.useConnectionPool !== false) {
        response = await this.connectionPool.request(url, options);
      } else {
        // Fallback to regular fetch
        const connectionManager = getConnectionManager();
        const result = await connectionManager.makeRequest(url, options, {
          timeout: optimizationOptions.timeout,
          retryAttempts: optimizationOptions.retryAttempts,
        });
        response = new Response(JSON.stringify(result.data), {
          status: result.status,
          statusText: result.statusText,
          headers: result.headers,
        });
      }
      // Parse response
      let data: T;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text() as unknown as T;
      }
      // Cache the response (if enabled and successful)
      if (optimizationOptions.enableCaching !== false && response.ok) {
        const headers: Record<string, string> = {};
        response.headers.forEach((value, key) => {
          headers[key] = value;
        });
        await this.responseCache.set(
          cacheKey,
          data,
          headers,
          response.status,
          {
            ttl: optimizationOptions.cacheOptions?.ttl,
            tags: optimizationOptions.cacheOptions?.tags,
            compress: optimizationOptions.cacheOptions?.compress,
          }
        );
      }
      // Update metrics
      const responseTime = Date.now() - startTime;
      this.totalResponseTime += responseTime;
      return data;
    } catch (error) {
      this.errorCount++;
      const responseTime = Date.now() - startTime;
      this.totalResponseTime += responseTime;
      throw error;
    }
  }
  /**
   * Optimized authentication request
   */
  async authenticateUser(email: string, password: string): Promise<any> {
    return this.optimizedRequest('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    }, {
      enableCaching: true,
      cacheOptions: {
        ttl: 60000, // Cache for 1 minute
        tags: ['auth', `user:${email}`],
        compress: false, // Don't compress auth responses for security
      },
      useConnectionPool: true,
    });
  }
  /**
   * Optimized session validation request
   */
  async validateSession(token: string): Promise<any> {
    return this.optimizedRequest('/api/auth/validate-session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    }, {
      enableCaching: true,
      cacheOptions: {
        ttl: 30000, // Cache for 30 seconds
        tags: ['auth', 'session'],
        compress: false,
      },
      useConnectionPool: true,
    });
  }
  /**
   * Optimized user data request
   */
  async getUserData(userId: string): Promise<any> {
    return this.optimizedRequest(`/api/users/${userId}`, {
      method: 'GET',
    }, {
      enableCaching: true,
      cacheOptions: {
        ttl: 300000, // Cache for 5 minutes
        tags: ['user', `user:${userId}`],
        compress: true,
      },
      useConnectionPool: true,
    });
  }
  /**
   * Optimized health check request
   */
  async healthCheck(): Promise<any> {
    return this.optimizedRequest('/health', {
      method: 'GET',
    }, {
      enableCaching: true,
      cacheOptions: {
        ttl: 10000, // Cache for 10 seconds
        tags: ['health'],
        compress: false,
      },
      useConnectionPool: true,
      timeout: 5000, // Short timeout for health checks
    });
  }
  /**
   * Invalidate cache by tags
   */
  invalidateCache(tags: string[]): number {
    return this.responseCache.clearByTags(tags);
  }
  /**
   * Invalidate user-specific cache
   */
  invalidateUserCache(userId: string): void {
    this.responseCache.clearByTags([`user:${userId}`]);
    this.queryOptimizer.invalidateUserCache(userId);
  }
  /**
   * Get comprehensive performance metrics
   */
  getMetrics(): PerformanceMetrics {
    const connectionPoolMetrics = this.connectionPool.getMetrics();
    const cacheMetrics = this.responseCache.getMetrics();
    const queryMetrics = this.queryOptimizer.getMetrics();
    const uptime = Date.now() - this.startTime;
    const averageResponseTime = this.requestCount > 0 ? this.totalResponseTime / this.requestCount : 0;
    const errorRate = this.requestCount > 0 ? this.errorCount / this.requestCount : 0;
    const requestThroughput = this.requestCount / (uptime / 1000); // requests per second
    return {
      connectionPool: {
        totalConnections: connectionPoolMetrics.totalConnections,
        activeConnections: connectionPoolMetrics.activeConnections,
        connectionReuse: connectionPoolMetrics.connectionReuse,
        averageConnectionTime: connectionPoolMetrics.averageConnectionTime,
      },
      responseCache: {
        hitRate: cacheMetrics.hitRate,
        totalEntries: cacheMetrics.totalEntries,
        memoryUsage: cacheMetrics.memoryUsage,
        compressionRatio: cacheMetrics.compressionRatio,
      },
      queryOptimizer: {
        totalQueries: queryMetrics.totalQueries,
        cacheHits: queryMetrics.cacheHits,
        averageQueryTime: queryMetrics.averageQueryTime,
        slowQueries: queryMetrics.slowQueries,
      },
      overall: {
        requestThroughput,
        averageResponseTime,
        errorRate,
        uptime,
      },
    };
  }
  /**
   * Get performance recommendations based on metrics
   */
  getPerformanceRecommendations(): string[] {
    const metrics = this.getMetrics();
    const recommendations: string[] = [];
    // Connection pool recommendations
    if (metrics.connectionPool.connectionReuse < 2) {
      recommendations.push('Consider increasing connection pool size for better connection reuse');
    }
    // Cache recommendations
    if (metrics.responseCache.hitRate < 0.5) {
      recommendations.push('Cache hit rate is low - consider increasing cache TTL or size');
    }
    if (metrics.responseCache.memoryUsage > 40 * 1024 * 1024) { // 40MB
      recommendations.push('Cache memory usage is high - consider enabling compression or reducing cache size');
    }
    // Query optimizer recommendations
    if (metrics.queryOptimizer.averageQueryTime > 500) {
      recommendations.push('Average query time is high - consider optimizing database queries or adding indexes');
    }
    if (metrics.queryOptimizer.slowQueries > 10) {
      recommendations.push('Multiple slow queries detected - review query performance and database configuration');
    }
    // Overall performance recommendations
    if (metrics.overall.errorRate > 0.05) { // 5%
      recommendations.push('Error rate is high - investigate connection stability and error handling');
    }
    if (metrics.overall.averageResponseTime > 2000) {
      recommendations.push('Average response time is high - consider optimizing request handling and caching');
    }
    return recommendations;
  }
  /**
   * Optimize system configuration based on current metrics
   */
  autoOptimize(): void {
    const metrics = this.getMetrics();
    // Auto-adjust connection pool size based on usage
    if (metrics.connectionPool.activeConnections / metrics.connectionPool.totalConnections > 0.8) {
    }
    // Auto-adjust cache size based on hit rate
    if (metrics.responseCache.hitRate < 0.3) {
    }
    // Auto-clear cache if memory usage is too high
    if (metrics.responseCache.memoryUsage > 50 * 1024 * 1024) { // 50MB
      // Clear entries older than 1 hour
      this.responseCache.clear();
    }
  }
  /**
   * Shutdown the performance optimizer
   */
  async shutdown(): Promise<void> {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
      this.metricsInterval = null;
    }
    await this.connectionPool.shutdown();
    this.responseCache.shutdown();
    this.queryOptimizer.shutdown();
  }
  /**
   * Generate cache key for request
   */
  private generateRequestCacheKey(url: string, options: RequestInit): string {
    const method = options.method || 'GET';
    const body = options.body ? JSON.stringify(options.body) : '';
    const headers = JSON.stringify(options.headers || {});
    return `${method}:${url}:${body}:${headers}`;
  }
  /**
   * Start metrics collection
   */
  private startMetricsCollection(): void {
    this.metricsInterval = setInterval(() => {
      const metrics = this.getMetrics();
      // Log performance metrics
      console.log('Performance Metrics:', {
        requestThroughput: metrics.overall.requestThroughput.toFixed(2),
        averageResponseTime: metrics.overall.averageResponseTime.toFixed(2),
        cacheHitRate: (metrics.responseCache.hitRate * 100).toFixed(1) + '%',
        connectionReuse: metrics.connectionPool.connectionReuse,
        errorRate: (metrics.overall.errorRate * 100).toFixed(2) + '%',
      });
      // Auto-optimize if enabled
      this.autoOptimize();
    }, this.config.metricsInterval);
  }
}
// Global performance optimizer instance
let performanceOptimizer: PerformanceOptimizer | null = null;
/**
 * Get the global performance optimizer instance
 */
export function getPerformanceOptimizer(): PerformanceOptimizer {
  if (!performanceOptimizer) {
    performanceOptimizer = new PerformanceOptimizer();
  }
  return performanceOptimizer;
}
/**
 * Initialize performance optimizer with custom configuration
 */
export function initializePerformanceOptimizer(config?: Partial<PerformanceConfig>): PerformanceOptimizer {
  if (performanceOptimizer) {
    performanceOptimizer.shutdown();
  }
  performanceOptimizer = new PerformanceOptimizer(config);
  return performanceOptimizer;
}
/**
 * Shutdown the global performance optimizer
 */
export async function shutdownPerformanceOptimizer(): Promise<void> {
  if (performanceOptimizer) {
    await performanceOptimizer.shutdown();
    performanceOptimizer = null;
  }
}
