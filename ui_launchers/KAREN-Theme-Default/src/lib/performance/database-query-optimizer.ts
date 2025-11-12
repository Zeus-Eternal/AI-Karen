/**
 * Database Query Optimizer for Authentication
 * 
 * Optimizes database queries for authentication operations with caching,
 * connection pooling, and query performance monitoring.
 * 
 * Requirements: 1.4, 4.4
 */

export interface QueryOptimizationConfig {
  enableQueryCache: boolean;
  queryCacheTtl: number;
  enablePreparedStatements: boolean;
  enableQueryPlan: boolean;
  maxCacheSize: number;
  enableMetrics: boolean;
  slowQueryThreshold: number;
}

export interface QueryMetrics {
  totalQueries: number;
  cacheHits: number;
  cacheMisses: number;
  averageQueryTime: number;
  slowQueries: number;
  preparedStatementHits: number;
  connectionPoolUtilization: number;
}

export interface QueryCacheEntry {
  query: string;
  params: unknown[];
  result: unknown;
  timestamp: number;
  ttl: number;
  accessCount: number;
  executionTime: number;
}

export interface PreparedStatement {
  id: string;
  query: string;
  parameterTypes: string[];
  createdAt: number;
  useCount: number;
  averageExecutionTime: number;
}

export interface QueryPlan {
  query: string;
  plan: unknown;
  cost: number;
  timestamp: number;
}

/**
 * Database Query Optimizer
 * 
 * Provides query caching, prepared statements, and performance monitoring
 * specifically optimized for authentication operations.
 */
export class DatabaseQueryOptimizer {
  private config: QueryOptimizationConfig;
  private queryCache: Map<string, QueryCacheEntry> = new Map();
  private preparedStatements: Map<string, PreparedStatement> = new Map();
  private queryPlans: Map<string, QueryPlan> = new Map();
  private metrics: QueryMetrics;
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor(config?: Partial<QueryOptimizationConfig>) {
    this.config = {
      enableQueryCache: true,
      queryCacheTtl: 300000, // 5 minutes
      enablePreparedStatements: true,
      enableQueryPlan: false, // Disabled by default
      maxCacheSize: 1000,
      enableMetrics: true,
      slowQueryThreshold: 1000, // 1 second
      ...config,
    };

    this.metrics = {
      totalQueries: 0,
      cacheHits: 0,
      cacheMisses: 0,
      averageQueryTime: 0,
      slowQueries: 0,
      preparedStatementHits: 0,
      connectionPoolUtilization: 0,
    };

    this.startCleanupTimer();
  }

  /**
   * Execute optimized query and handle caching, prepared statements, and metrics.
   */
  async executeAuthQuery(
    query: string,
    params: unknown[] = [],
    options: { skipCache?: boolean; cacheTtl?: number } = {}
  ): Promise<unknown> {
    const startTime = Date.now();
    this.metrics.totalQueries++;

    try {
      const cacheKey = this.generateCacheKey(query, params);

      if (this.config.enableQueryCache && !options.skipCache) {
        const cachedResult = this.getCachedResult(cacheKey);
        if (cachedResult) {
          this.metrics.cacheHits++;
          this.updateMetrics(Date.now() - startTime);
          return cachedResult.result;
        }
        this.metrics.cacheMisses++;
      }

      let preparedStatement: PreparedStatement | null = null;
      if (this.config.enablePreparedStatements) {
        const resolved = this.resolvePreparedStatement(query, params);
        if (resolved) {
          preparedStatement = resolved.statement;
          if (resolved.hit) {
            this.metrics.preparedStatementHits++;
          }
        }
      }

      const result = await this.executeQuery(query, params, preparedStatement);

      const executionTime = Date.now() - startTime;
      if (this.config.enableQueryCache && !options.skipCache) {
        this.cacheResult(cacheKey, query, params, result, executionTime, options.cacheTtl);
      }

      if (preparedStatement) {
        this.updatePreparedStatementMetrics(preparedStatement, executionTime);
      }

      this.updateMetrics(executionTime);

      if (executionTime > this.config.slowQueryThreshold) {
        this.metrics.slowQueries++;
        this.logSlowQuery(query, params, executionTime);
      }

      return result;

    } catch (error) {
      const executionTime = Date.now() - startTime;
      this.updateMetrics(executionTime);
      this.logError(query, error);
      throw error;
    }
  }

  /**
   * Mock execute query implementation - replace with actual DB query execution logic
   */
  private async executeQuery(
    query: string,
    params: unknown[],
    _preparedStatement?: PreparedStatement | null
  ): Promise<unknown> {
    await new Promise(resolve => setTimeout(resolve, Math.random() * 50 + 10)); // Simulate query time
    if (query.includes('SELECT') && query.includes('users')) {
      if (params[0] === 'admin@example.com') {
        return [{ user_id: 'dev_admin', email: 'admin@example.com' }];
      }
      return [];
    }
    return null;
  }

  /**
   * Logging the error for future analysis
   */
  private logError(query: string, error: unknown) {
    console.error('Database Query Execution Failed:', {
      query,
      error,
    });
  }

  /**
   * Logging slow queries for analysis
   */
  private logSlowQuery(query: string, params: unknown[], executionTime: number) {
    console.warn(`Slow query detected (${executionTime}ms):`, {
      query: query.replace(/\s+/g, ' ').trim(),
      params,
      executionTime,
      threshold: this.config.slowQueryThreshold,
    });
  }

  /**
   * Cache result after query execution
   */
  private cacheResult(
    cacheKey: string,
    query: string,
    params: unknown[],
    result: unknown,
    executionTime: number,
    customTtl?: number
  ): void {
    if (this.queryCache.size >= this.config.maxCacheSize) {
      this.evictOldestCacheEntry();
    }

    const entry: QueryCacheEntry = {
      query,
      params,
      result,
      timestamp: Date.now(),
      ttl: customTtl || this.config.queryCacheTtl,
      accessCount: 1,
      executionTime,
    };

    this.queryCache.set(cacheKey, entry);
  }

  /**
   * Generate a unique cache key based on query and parameters
   */
  private generateCacheKey(query: string, params: unknown[]): string {
    const normalizedQuery = this.normalizeQuery(query);
    const paramsStr = JSON.stringify(params);
    return `${normalizedQuery}|${paramsStr}`;
  }

  /**
   * Get cached query result if available and not expired
   */
  private getCachedResult(cacheKey: string): QueryCacheEntry | null {
    const entry = this.queryCache.get(cacheKey);
    if (!entry || Date.now() - entry.timestamp > entry.ttl) {
      this.queryCache.delete(cacheKey);
      return null;
    }
    entry.accessCount++;
    return entry;
  }

  /**
   * Evict the oldest cache entry when the cache is full
   */
  private evictOldestCacheEntry(): void {
    let oldestKey: string | null = null;
    let oldestTimestamp = Date.now();

    this.queryCache.forEach((entry, key) => {
      if (entry.timestamp < oldestTimestamp) {
        oldestTimestamp = entry.timestamp;
        oldestKey = key;
      }
    });

    if (oldestKey) {
      this.queryCache.delete(oldestKey);
    }
  }

  /**
   * Update overall metrics (e.g., average query time)
   */
  private updateMetrics(executionTime: number): void {
    const alpha = 0.1;
    this.metrics.averageQueryTime = this.metrics.averageQueryTime * (1 - alpha) + executionTime * alpha;
  }

  /**
   * Update prepared statement metrics (e.g., average execution time)
   */
  private updatePreparedStatementMetrics(statement: PreparedStatement, executionTime: number): void {
    statement.useCount++;
    const alpha = 0.1;
    statement.averageExecutionTime = statement.averageExecutionTime * (1 - alpha) + executionTime * alpha;
  }

  /**
   * Get query optimization metrics
   */
  getMetrics(): QueryMetrics {
    return { ...this.metrics };
  }

  /**
   * Clear all cached entries
   */
  clearCache(): void {
    this.queryCache.clear();
  }

  /**
   * Reset the optimizer (e.g., after a configuration change)
   */
  reset(): void {
    this.queryCache.clear();
    this.preparedStatements.clear();
    this.queryPlans.clear();
    this.metrics = {
      totalQueries: 0,
      cacheHits: 0,
      cacheMisses: 0,
      averageQueryTime: 0,
      slowQueries: 0,
      preparedStatementHits: 0,
      connectionPoolUtilization: 0,
    };
  }

  invalidateUserCache(userId: string): void {
    if (!userId) return;
    this.queryCache.forEach((entry, key) => {
      const matchesUser = entry.params.some(param => {
        if (param == null) return false;
        if (typeof param === 'string' || typeof param === 'number') {
          return String(param) === userId;
        }
        if (typeof param === 'object') {
          const candidate = (param as Record<string, unknown>).userId ?? (param as Record<string, unknown>).id;
          return typeof candidate === 'string' && candidate === userId;
        }
        return false;
      });

      if (matchesUser) {
        this.queryCache.delete(key);
      }
    });
  }

  updateConfig(config: Partial<QueryOptimizationConfig>): void {
    this.config = { ...this.config, ...config };
    if (this.cleanupInterval) {
      this.stopCleanupTimer();
      this.startCleanupTimer();
    }
  }

  shutdown(): void {
    this.stopCleanupTimer();
    this.queryCache.clear();
    this.preparedStatements.clear();
    this.queryPlans.clear();
  }

  private normalizeQuery(query: string): string {
    return query.replace(/\s+/g, ' ').trim();
  }

  private resolvePreparedStatement(
    query: string,
    params: unknown[]
  ): { statement: PreparedStatement; hit: boolean } | null {
    const normalizedQuery = this.normalizeQuery(query);
    const existing = this.preparedStatements.get(normalizedQuery);
    if (existing) {
      return { statement: existing, hit: true };
    }

    const statement: PreparedStatement = {
      id: `stmt_${Math.random().toString(36).slice(2)}`,
      query: normalizedQuery,
      parameterTypes: params.map(param => typeof param),
      createdAt: Date.now(),
      useCount: 0,
      averageExecutionTime: 0,
    };

    this.preparedStatements.set(normalizedQuery, statement);
    return { statement, hit: false };
  }

  private startCleanupTimer(): void {
    if (this.cleanupInterval) return;
    const interval = Math.max(this.config.queryCacheTtl, 1000);
    this.cleanupInterval = setInterval(() => this.cleanupExpiredEntries(), interval);
  }

  private stopCleanupTimer(): void {
    if (!this.cleanupInterval) return;
    clearInterval(this.cleanupInterval);
    this.cleanupInterval = null;
  }

  private cleanupExpiredEntries(): void {
    const now = Date.now();
    this.queryCache.forEach((entry, key) => {
      if (now - entry.timestamp > entry.ttl) {
        this.queryCache.delete(key);
      }
    });
  }
}

// Singleton instance
let instance: DatabaseQueryOptimizer | null = null;

/**
 * Get or create the singleton DatabaseQueryOptimizer instance
 */
export function getDatabaseQueryOptimizer(config?: Partial<QueryOptimizationConfig>): DatabaseQueryOptimizer {
  if (!instance) {
    instance = new DatabaseQueryOptimizer(config);
  } else if (config) {
    instance.updateConfig(config);
  }
  return instance;
}

export function initializeDatabaseQueryOptimizer(
  config?: Partial<QueryOptimizationConfig>
): DatabaseQueryOptimizer {
  instance = getDatabaseQueryOptimizer(config);
  return instance;
}

export function shutdownDatabaseQueryOptimizer(): void {
  if (instance) {
    instance.shutdown();
    instance = null;
  }
}
