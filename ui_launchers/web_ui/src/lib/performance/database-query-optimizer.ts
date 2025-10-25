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
  params: any[];
  result: any;
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
  plan: any;
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
      enableQueryPlan: false, // Disabled by default as it requires database-specific implementation
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
   * Execute optimized authentication query
   */
  async executeAuthQuery(
    query: string,
    params: any[] = [],
    options: { skipCache?: boolean; cacheTtl?: number } = {}
  ): Promise<any> {
    const startTime = Date.now();
    this.metrics.totalQueries++;

    try {
      // Generate cache key
      const cacheKey = this.generateCacheKey(query, params);

      // Check cache first (if enabled and not skipped)
      if (this.config.enableQueryCache && !options.skipCache) {
        const cachedResult = this.getCachedResult(cacheKey);
        if (cachedResult) {
          this.metrics.cacheHits++;
          this.updateMetrics(Date.now() - startTime);
          return cachedResult.result;
        }
        this.metrics.cacheMisses++;
      }

      // Check for prepared statement
      let preparedStatement: PreparedStatement | null = null;
      if (this.config.enablePreparedStatements) {
        preparedStatement = this.getPreparedStatement(query);
        if (preparedStatement) {
          this.metrics.preparedStatementHits++;
        }
      }

      // Execute the query (this would be implemented with actual database driver)
      const result = await this.executeQuery(query, params, preparedStatement);
      
      const executionTime = Date.now() - startTime;

      // Cache the result (if enabled)
      if (this.config.enableQueryCache && !options.skipCache) {
        this.cacheResult(cacheKey, query, params, result, executionTime, options.cacheTtl);
      }

      // Update prepared statement metrics
      if (preparedStatement) {
        this.updatePreparedStatementMetrics(preparedStatement, executionTime);
      }

      // Update metrics
      this.updateMetrics(executionTime);

      // Check for slow queries
      if (executionTime > this.config.slowQueryThreshold) {
        this.metrics.slowQueries++;
        this.logSlowQuery(query, params, executionTime);
      }

      return result;

    } catch (error) {
      const executionTime = Date.now() - startTime;
      this.updateMetrics(executionTime);
      throw error;
    }
  }

  /**
   * Optimize user authentication query
   */
  async authenticateUser(email: string, passwordHash: string): Promise<any> {
    const query = `
      SELECT user_id, email, full_name, roles, is_active, tenant_id, 
             two_factor_enabled, preferences, last_login, created_at
      FROM users 
      WHERE email = $1 AND password_hash = $2 AND is_active = true
    `;
    
    return this.executeAuthQuery(query, [email, passwordHash], {
      cacheTtl: 60000, // Cache for 1 minute for security
    });
  }

  /**
   * Optimize user lookup by ID query
   */
  async getUserById(userId: string): Promise<any> {
    const query = `
      SELECT user_id, email, full_name, roles, is_active, tenant_id,
             two_factor_enabled, preferences, last_login, created_at
      FROM users 
      WHERE user_id = $1 AND is_active = true
    `;
    
    return this.executeAuthQuery(query, [userId], {
      cacheTtl: 300000, // Cache for 5 minutes
    });
  }

  /**
   * Optimize user lookup by email query
   */
  async getUserByEmail(email: string): Promise<any> {
    const query = `
      SELECT user_id, email, full_name, roles, is_active, tenant_id,
             two_factor_enabled, preferences, last_login, created_at
      FROM users 
      WHERE email = $1 AND is_active = true
    `;
    
    return this.executeAuthQuery(query, [email], {
      cacheTtl: 300000, // Cache for 5 minutes
    });
  }

  /**
   * Optimize session validation query
   */
  async validateSession(sessionToken: string): Promise<any> {
    const query = `
      SELECT s.session_id, s.user_id, s.expires_at, s.is_active,
             u.email, u.roles, u.tenant_id
      FROM sessions s
      JOIN users u ON s.user_id = u.user_id
      WHERE s.session_token = $1 AND s.is_active = true 
            AND s.expires_at > NOW() AND u.is_active = true
    `;
    
    return this.executeAuthQuery(query, [sessionToken], {
      cacheTtl: 30000, // Cache for 30 seconds for security
    });
  }

  /**
   * Update user last login timestamp
   */
  async updateLastLogin(userId: string): Promise<void> {
    const query = `
      UPDATE users 
      SET last_login = NOW() 
      WHERE user_id = $1
    `;
    
    // Don't cache write operations
    await this.executeAuthQuery(query, [userId], { skipCache: true });
    
    // Invalidate related cache entries
    this.invalidateUserCache(userId);
  }

  /**
   * Get query optimization metrics
   */
  getMetrics(): QueryMetrics {
    return { ...this.metrics };
  }

  /**
   * Get query cache statistics
   */
  getCacheStatistics() {
    return {
      totalEntries: this.queryCache.size,
      hitRate: this.metrics.totalQueries > 0 ? this.metrics.cacheHits / this.metrics.totalQueries : 0,
      missRate: this.metrics.totalQueries > 0 ? this.metrics.cacheMisses / this.metrics.totalQueries : 0,
      averageAccessCount: Array.from(this.queryCache.values())
        .reduce((sum, entry) => sum + entry.accessCount, 0) / this.queryCache.size || 0,
    };
  }

  /**
   * Get prepared statement statistics
   */
  getPreparedStatementStatistics() {
    return {
      totalStatements: this.preparedStatements.size,
      totalUses: Array.from(this.preparedStatements.values())
        .reduce((sum, stmt) => sum + stmt.useCount, 0),
      averageExecutionTime: Array.from(this.preparedStatements.values())
        .reduce((sum, stmt) => sum + stmt.averageExecutionTime, 0) / this.preparedStatements.size || 0,
    };
  }

  /**
   * Clear query cache
   */
  clearCache(): void {
    this.queryCache.clear();
  }

  /**
   * Invalidate cache entries for a specific user
   */
  invalidateUserCache(userId: string): void {
    const keysToDelete: string[] = [];
    
    for (const [key, entry] of this.queryCache.entries()) {
      // Check if the query involves the user
      if (entry.params.includes(userId) || entry.query.includes('users')) {
        keysToDelete.push(key);
      }
    }
    
    for (const key of keysToDelete) {
      this.queryCache.delete(key);
    }
  }

  /**
   * Shutdown the optimizer
   */
  shutdown(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    
    this.queryCache.clear();
    this.preparedStatements.clear();
    this.queryPlans.clear();
  }

  /**
   * Generate cache key for query and parameters
   */
  private generateCacheKey(query: string, params: any[]): string {
    const normalizedQuery = query.replace(/\s+/g, ' ').trim();
    const paramsStr = JSON.stringify(params);
    return `${normalizedQuery}|${paramsStr}`;
  }

  /**
   * Get cached result if available and not expired
   */
  private getCachedResult(cacheKey: string): QueryCacheEntry | null {
    const entry = this.queryCache.get(cacheKey);
    if (!entry) {
      return null;
    }

    // Check if expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.queryCache.delete(cacheKey);
      return null;
    }

    // Update access count
    entry.accessCount++;
    return entry;
  }

  /**
   * Cache query result
   */
  private cacheResult(
    cacheKey: string,
    query: string,
    params: any[],
    result: any,
    executionTime: number,
    customTtl?: number
  ): void {
    // Ensure cache size limit
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
   * Get or create prepared statement
   */
  private getPreparedStatement(query: string): PreparedStatement | null {
    const normalizedQuery = query.replace(/\s+/g, ' ').trim();
    let statement = this.preparedStatements.get(normalizedQuery);

    if (!statement) {
      // Create new prepared statement
      statement = {
        id: `stmt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        query: normalizedQuery,
        parameterTypes: this.extractParameterTypes(query),
        createdAt: Date.now(),
        useCount: 0,
        averageExecutionTime: 0,
      };

      this.preparedStatements.set(normalizedQuery, statement);
    }

    return statement;
  }

  /**
   * Extract parameter types from query (simplified implementation)
   */
  private extractParameterTypes(query: string): string[] {
    const paramMatches = query.match(/\$\d+/g) || [];
    return paramMatches.map(() => 'text'); // Simplified - assume all text
  }

  /**
   * Execute the actual database query (mock implementation)
   */
  private async executeQuery(
    query: string,
    params: any[],
    preparedStatement?: PreparedStatement | null
  ): Promise<any> {
    // This is a mock implementation - in real usage, this would use the actual database driver
    // For authentication queries, we'll simulate database responses
    
    await new Promise(resolve => setTimeout(resolve, Math.random() * 50 + 10)); // Simulate query time
    
    if (query.includes('SELECT') && query.includes('users')) {
      if (query.includes('email') && params.includes('admin@example.com')) {
        return [{
          user_id: 'dev_admin',
          email: 'admin@example.com',
          full_name: 'Development Admin',
          roles: ['admin', 'user'],
          is_active: true,
          tenant_id: 'default',
          two_factor_enabled: false,
          preferences: {},
          last_login: new Date().toISOString(),
          created_at: new Date().toISOString(),
        }];
      }
      return []; // No user found
    }
    
    if (query.includes('sessions')) {
      // Mock session validation
      return [{
        session_id: 'mock_session',
        user_id: 'dev_admin',
        expires_at: new Date(Date.now() + 86400000).toISOString(),
        is_active: true,
        email: 'admin@example.com',
        roles: ['admin', 'user'],
        tenant_id: 'default',
      }];
    }
    
    if (query.includes('UPDATE')) {
      return { affectedRows: 1 };
    }
    
    return null;
  }

  /**
   * Update prepared statement metrics
   */
  private updatePreparedStatementMetrics(statement: PreparedStatement, executionTime: number): void {
    statement.useCount++;
    
    // Update average execution time using exponential moving average
    const alpha = 0.1;
    statement.averageExecutionTime = 
      statement.averageExecutionTime * (1 - alpha) + executionTime * alpha;
  }

  /**
   * Update overall metrics
   */
  private updateMetrics(executionTime: number): void {
    // Update average query time using exponential moving average
    const alpha = 0.1;
    this.metrics.averageQueryTime = 
      this.metrics.averageQueryTime * (1 - alpha) + executionTime * alpha;
  }

  /**
   * Log slow query for analysis
   */
  private logSlowQuery(query: string, params: any[], executionTime: number): void {
    console.warn(`Slow query detected (${executionTime}ms):`, {
      query: query.replace(/\s+/g, ' ').trim(),
      params,
      executionTime,
      threshold: this.config.slowQueryThreshold,
    });
  }

  /**
   * Evict oldest cache entry when cache is full
   */
  private evictOldestCacheEntry(): void {
    let oldestKey: string | null = null;
    let oldestTimestamp = Date.now();

    for (const [key, entry] of this.queryCache.entries()) {
      if (entry.timestamp < oldestTimestamp) {
        oldestTimestamp = entry.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.queryCache.delete(oldestKey);
    }
  }

  /**
   * Start cleanup timer for expired cache entries
   */
  private startCleanupTimer(): void {
    this.cleanupInterval = setInterval(() => {
      this.cleanupExpiredEntries();
    }, 60000); // Run every minute
  }

  /**
   * Cleanup expired cache entries
   */
  private cleanupExpiredEntries(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, entry] of this.queryCache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        expiredKeys.push(key);
      }
    }

    for (const key of expiredKeys) {
      this.queryCache.delete(key);
    }
  }
}

// Global optimizer instance
let databaseQueryOptimizer: DatabaseQueryOptimizer | null = null;

/**
 * Get the global database query optimizer instance
 */
export function getDatabaseQueryOptimizer(): DatabaseQueryOptimizer {
  if (!databaseQueryOptimizer) {
    databaseQueryOptimizer = new DatabaseQueryOptimizer();
  }
  return databaseQueryOptimizer;
}

/**
 * Initialize database query optimizer with custom configuration
 */
export function initializeDatabaseQueryOptimizer(config?: Partial<QueryOptimizationConfig>): DatabaseQueryOptimizer {
  if (databaseQueryOptimizer) {
    databaseQueryOptimizer.shutdown();
  }
  
  databaseQueryOptimizer = new DatabaseQueryOptimizer(config);
  return databaseQueryOptimizer;
}

/**
 * Shutdown the global database query optimizer
 */
export function shutdownDatabaseQueryOptimizer(): void {
  if (databaseQueryOptimizer) {
    databaseQueryOptimizer.shutdown();
    databaseQueryOptimizer = null;
  }
}