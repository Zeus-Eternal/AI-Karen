/**
 * Performance Optimizer
 *
 * Integrates HTTP connection pooling, request/response caching,
 * and database query optimization with robust metrics.
 *
 * Requirements: 1.4, 4.4
 */

import {
  HttpConnectionPool,
  getHttpConnectionPool,
  initializeHttpConnectionPool,
  ConnectionPoolConfig,
} from './http-connection-pool';
import {
  RequestResponseCache,
  getRequestResponseCache,
  initializeRequestResponseCache,
  CacheConfig,
} from './request-response-cache';
import {
  DatabaseQueryOptimizer,
  getDatabaseQueryOptimizer,
  initializeDatabaseQueryOptimizer,
  QueryOptimizationConfig,
} from './database-query-optimizer';
import { getConnectionManager } from '../connection/connection-manager';

export type HeaderLike = HeadersInit | undefined;

export interface PerformanceConfig {
  connectionPool: Partial<ConnectionPoolConfig>;
  responseCache: Partial<CacheConfig>;
  queryOptimizer: Partial<QueryOptimizationConfig>;
  enableMetrics: boolean;
  metricsInterval: number; // ms
  defaultTimeoutMs?: number;
  defaultRetries?: number;
  defaultCacheTtlMs?: number;
  cacheNonIdempotent?: boolean; // allow caching for POST/PUT etc. when explicitly requested
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
    averageResponseTime: number; // ms
    errorRate: number;           // 0..1
    uptime: number;              // ms
  };
}

export interface OptimizedRequestOptions {
  useConnectionPool?: boolean;
  enableCaching?: boolean;
  cacheOptions?: {
    ttl?: number;       // ms
    tags?: string[];
    compress?: boolean;
  };
  timeout?: number;      // ms
  retryAttempts?: number;
  retryBackoffMs?: number; // base backoff
  retryOn?: number[];    // HTTP codes to retry
}

function stableStringify(obj: unknown): string {
  if (obj == null) return '';
  if (typeof obj === 'string') return obj;
  if (obj instanceof URLSearchParams) return obj.toString();
  try {
    return JSON.stringify(obj, Object.keys(obj).sort());
  } catch {
    return String(obj);
  }
}

function headersToObject(headers: HeaderLike): Record<string, string> {
  if (!headers) return {};
  if (Array.isArray(headers)) {
    const out: Record<string, string> = {};
    for (const [k, v] of headers) out[String(k).toLowerCase()] = String(v);
    return out;
  }
  if (headers instanceof Headers) {
    const out: Record<string, string> = {};
    headers.forEach((v, k) => (out[k.toLowerCase()] = v));
    return out;
  }
  // Record<string, string>
  const headerRecord = headers as Record<string, string | number | boolean | undefined>;
  const normalized: Record<string, string> = {};
  for (const k of Object.keys(headerRecord)) {
    const value = headerRecord[k];
    if (value !== undefined) {
      normalized[k.toLowerCase()] = String(value);
    }
  }
  return normalized;
}

function methodAllowsDefaultCaching(method?: string) {
  const m = (method || 'GET').toUpperCase();
  return m === 'GET' || m === 'HEAD';
}

export class PerformanceOptimizer {
  private readonly config: PerformanceConfig;
  private readonly connectionPool: HttpConnectionPool;
  private readonly responseCache: RequestResponseCache;
  private readonly queryOptimizer: DatabaseQueryOptimizer;

  private metricsInterval: NodeJS.Timeout | null = null;
  private readonly startTime = Date.now();

  private requestCount = 0;
  private errorCount = 0;
  private totalResponseTime = 0;

  constructor(config?: Partial<PerformanceConfig>) {
    this.config = {
      connectionPool: {},
      responseCache: {},
      queryOptimizer: {},
      enableMetrics: true,
      metricsInterval: 60_000,
      defaultTimeoutMs: 20_000,
      defaultRetries: 2,
      defaultCacheTtlMs: 60_000,
      cacheNonIdempotent: false,
      ...config,
    };

    const hasPoolOverrides = Object.keys(this.config.connectionPool).length > 0;
    const hasCacheOverrides = Object.keys(this.config.responseCache).length > 0;
    const hasQueryOverrides = Object.keys(this.config.queryOptimizer).length > 0;

    this.connectionPool = hasPoolOverrides
      ? initializeHttpConnectionPool(this.config.connectionPool)
      : getHttpConnectionPool();
    this.responseCache = hasCacheOverrides
      ? initializeRequestResponseCache(this.config.responseCache)
      : getRequestResponseCache();
    this.queryOptimizer = hasQueryOverrides
      ? initializeDatabaseQueryOptimizer(this.config.queryOptimizer)
      : getDatabaseQueryOptimizer();

    if (this.config.enableMetrics) {
      this.startMetricsCollection();
    }
  }

  /**
   * Make an optimized HTTP request with pooling, timeout/retry, and caching.
   */
  async optimizedRequest<T = unknown>(
    url: string,
    options: RequestInit = {},
    optimizationOptions: OptimizedRequestOptions = {}
  ): Promise<T> {
    const started = Date.now();
    this.requestCount++;

    const method = (options.method || 'GET').toUpperCase();
    const shouldConsiderCache =
      optimizationOptions.enableCaching !== false &&
      (methodAllowsDefaultCaching(method) || this.config.cacheNonIdempotent);

    const cacheKey = this.generateRequestCacheKey(url, options);

    // Try cache first
    if (shouldConsiderCache) {
      const cached = await this.responseCache.get(cacheKey, { skipCache: false });
      if (cached) {
        // Update metrics
        const dt = Date.now() - started;
        this.totalResponseTime += dt;
        return cached.data as T;
      }
    }

    // Prepare request with timeout & retries
    const timeoutMs = optimizationOptions.timeout ?? this.config.defaultTimeoutMs!;
    const retryAttempts = optimizationOptions.retryAttempts ?? this.config.defaultRetries!;
    const backoffBase = optimizationOptions.retryBackoffMs ?? 300;
    const retryOn = new Set(optimizationOptions.retryOn ?? [408, 425, 429, 500, 502, 503, 504]);

    let lastErr: unknown;

    for (let attempt = 0; attempt <= retryAttempts; attempt++) {
      const abortController = new AbortController();
      const timer = setTimeout(() => abortController.abort(), timeoutMs);

      try {
        let response: Response;

        if (optimizationOptions.useConnectionPool !== false) {
          // Pool path
          response = await this.connectionPool.request(url, { ...options, signal: abortController.signal });
        } else {
          // Fallback path via connection manager
          const connectionManager = getConnectionManager();
          const result = await connectionManager.makeRequest(
            url,
            options,
            {
              timeout: timeoutMs,
              retryAttempts: 0,
            }
          );

          response = new Response(
            typeof result.data === 'string' ? result.data : JSON.stringify(result.data),
            {
              status: result.status,
              statusText: result.statusText,
              headers: result.headers as HeadersInit,
            }
          );
        }

        clearTimeout(timer);

        // Parse response
        const ctype = response.headers.get('content-type') || '';
        let data: unknown;
        if (ctype.includes('application/json')) {
          data = await response.json();
        } else if (ctype.startsWith('text/')) {
          data = await response.text();
        } else {
          // Fallback: arrayBuffer -> base64 string to avoid holding raw buffers
          const buf = await response.arrayBuffer();
          data = Buffer.from(buf).toString('base64');
        }

        // Non-200s can be retried depending on code
        if (!response.ok && retryOn.has(response.status) && attempt < retryAttempts) {
          const delay = backoffBase * Math.pow(2, attempt);
          await new Promise(res => setTimeout(res, delay));
          continue;
        }

        // Cache successful responses if allowed
        if (shouldConsiderCache && response.ok) {
          const headersObj = headersToObject(response.headers);
          await this.responseCache.set(
            cacheKey,
            data,
            headersObj,
            response.status,
            {
              ttl: optimizationOptions.cacheOptions?.ttl ?? this.config.defaultCacheTtlMs,
              tags: optimizationOptions.cacheOptions?.tags,
              compress: optimizationOptions.cacheOptions?.compress ?? method === 'GET',
            }
          );
        }

        const dt = Date.now() - started;
        this.totalResponseTime += dt;

        if (!response.ok) {
          // Surface an error with context
          const err = new Error(`HTTP ${response.status} ${response.statusText}`) as Error & { status?: number; data?: unknown };
          err.status = response.status;
          err.data = data;
          throw err;
        }

        return data as T;
      } catch (err: unknown) {
        clearTimeout(timer);
        lastErr = err;

        // Retry on abort/network or selected HTTP codes (already handled above).
        const errorObj = err as { name?: string; message?: string } | null;
        const isAbort = errorObj?.name === 'AbortError';
        const isNetwork = /network/i.test(String(errorObj?.message ?? ''));
        if ((isAbort || isNetwork) && attempt < retryAttempts) {
          const delay = backoffBase * Math.pow(2, attempt);
          await new Promise(res => setTimeout(res, delay));
          continue;
        }

        // No more retries
        break;
      }
    }

    // Update metrics on error
    this.errorCount++;
    const dt = Date.now() - started;
    this.totalResponseTime += dt;
    throw lastErr;
  }

  /** Convenience: Optimized authentication request */
  async authenticateUser(email: string, password: string): Promise<unknown> {
    return this.optimizedRequest(
      '/api/auth/login',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      },
      {
        enableCaching: false, // do not cache login responses by default
        useConnectionPool: true,
        timeout: 10_000,
        retryAttempts: 1,
      }
    );
  }

  /** Convenience: Optimized session validation request */
  async validateSession(token: string): Promise<unknown> {
    return this.optimizedRequest(
      '/api/auth/validate-session',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      },
      {
        enableCaching: true,
        cacheOptions: {
          ttl: 30_000,
          tags: ['auth', 'session'],
          compress: false,
        },
        useConnectionPool: true,
        timeout: 8_000,
        retryAttempts: 1,
      }
    );
  }

  /** Convenience: Optimized user data request */
  async getUserData(userId: string): Promise<unknown> {
    return this.optimizedRequest(
      `/api/users/${userId}`,
      { method: 'GET' },
      {
        enableCaching: true,
        cacheOptions: {
          ttl: 300_000,
          tags: ['user', `user:${userId}`],
          compress: true,
        },
        useConnectionPool: true,
        timeout: 10_000,
      }
    );
  }

  /** Health check */
  async healthCheck(): Promise<unknown> {
    return this.optimizedRequest(
      '/health',
      { method: 'GET' },
      {
        enableCaching: true,
        cacheOptions: { ttl: 10_000, tags: ['health'], compress: false },
        useConnectionPool: true,
        timeout: 5_000,
        retryAttempts: 0,
      }
    );
  }

  /** Invalidate cache by tags */
  invalidateCache(tags: string[]): number {
    return this.responseCache.clearByTags(tags);
  }

  /** Invalidate a single user's cache */
  invalidateUserCache(userId: string): void {
    this.responseCache.clearByTags([`user:${userId}`]);
    this.queryOptimizer.invalidateUserCache(userId);
  }

  /** Metrics snapshot */
  getMetrics(): PerformanceMetrics {
    const pool = this.connectionPool.getMetrics();
    const cache = this.responseCache.getMetrics();
    const query = this.queryOptimizer.getMetrics();

    const uptime = Date.now() - this.startTime;
    const avgResp = this.requestCount > 0 ? this.totalResponseTime / this.requestCount : 0;
    const errRate = this.requestCount > 0 ? this.errorCount / this.requestCount : 0;
    const rps = uptime > 0 ? this.requestCount / (uptime / 1000) : 0;

    return {
      connectionPool: {
        totalConnections: pool.totalConnections,
        activeConnections: pool.activeConnections,
        connectionReuse: pool.connectionReuse,
        averageConnectionTime: pool.averageConnectionTime,
      },
      responseCache: {
        hitRate: cache.hitRate,
        totalEntries: cache.totalEntries,
        memoryUsage: cache.memoryUsage,
        compressionRatio: cache.compressionRatio,
      },
      queryOptimizer: {
        totalQueries: query.totalQueries,
        cacheHits: query.cacheHits,
        averageQueryTime: query.averageQueryTime,
        slowQueries: query.slowQueries,
      },
      overall: {
        requestThroughput: rps,
        averageResponseTime: avgResp,
        errorRate: errRate,
        uptime,
      },
    };
  }

  /** Human guidance based on metrics */
  getPerformanceRecommendations(): string[] {
    const m = this.getMetrics();
    const recs: string[] = [];

    // Connection pool
    if (m.connectionPool.connectionReuse < 2) {
      recs.push('Increase connection pool size / max idle to improve reuse.');
    }

    // Cache
    if (m.responseCache.hitRate < 0.5) {
      recs.push('Low cache hit rate — consider longer TTL or broader keying policy.');
    }
    if (m.responseCache.memoryUsage > 40 * 1024 * 1024) {
      recs.push('Cache memory usage high — enable compression or reduce entry size/TTL.');
    }

    // DB queries
    if (m.queryOptimizer.averageQueryTime > 500) {
      recs.push('High average DB latency — add indexes, reduce N+1s, or widen query cache TTL.');
    }
    if (m.queryOptimizer.slowQueries > 10) {
      recs.push('Multiple slow queries detected — profile and tune hot paths.');
    }

    // Overall
    if (m.overall.errorRate > 0.05) {
      recs.push('Error rate >5% — investigate network instability and error handling.');
    }
    if (m.overall.averageResponseTime > 2000) {
      recs.push('Avg response time >2s — optimize request handlers and leverage caching more aggressively.');
    }

    return recs;
  }

  /** Auto-tune configurations based on live metrics */
  autoOptimize(): void {
    const m = this.getMetrics();

    // If pool is hot (≥80% active), signal underlying pool to scale if supported.
    if (
      m.connectionPool.totalConnections > 0 &&
      m.connectionPool.activeConnections / m.connectionPool.totalConnections >= 0.8
    ) {
      // Example: this.connectionPool.resize({ max: current + 10 }) if your pool supports it.
      // Leaving as a no-op here to avoid guessing your pool API.
    }

    // If hit rate poor, bump cache TTL a bit via cache’s own config (if supported).
    if (m.responseCache.hitRate < 0.3) {
      // Example: this.responseCache.updateConfig({ defaultTtlMs: 120_000 });
    }

    // Guardrail: memory pressure — purge old entries.
    if (m.responseCache.memoryUsage > 50 * 1024 * 1024) {
      this.responseCache.clear(); // consider a smarter LRU trim if available
    }
  }

  /** Graceful shutdown */
  async shutdown(): Promise<void> {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
      this.metricsInterval = null;
    }
    await this.connectionPool.shutdown();
    this.responseCache.shutdown();
    this.queryOptimizer.shutdown();
  }

  /* ---------------------------
   * Internals
   * ------------------------- */

  private generateRequestCacheKey(url: string, options: RequestInit): string {
    const method = (options.method || 'GET').toUpperCase();
    const headersObj = headersToObject(options.headers);
    // Body may be string, URLSearchParams, FormData, or object — make it stable.
    let bodyStr = '';
    if (options.body instanceof URLSearchParams) {
      bodyStr = options.body.toString();
    } else if (typeof options.body === 'string') {
      bodyStr = options.body;
    } else if (options.body && typeof options.body === 'object') {
      bodyStr = stableStringify(options.body as unknown);
    }
    const keyObj = {
      m: method,
      u: url,
      h: headersObj, // normalized, lowercase keys
      b: bodyStr,
    };
    return stableStringify(keyObj);
  }

  private startMetricsCollection(): void {
    this.metricsInterval = setInterval(() => {
      const m = this.getMetrics();
      // Minimal structured log (wire this into your logger)
      // eslint-disable-next-line no-console
      console.log('[PerfMetrics]', JSON.stringify({
        ts: new Date().toISOString(),
        rps: Number(m.overall.requestThroughput.toFixed(2)),
        avgMs: Number(m.overall.averageResponseTime.toFixed(2)),
        cacheHit: Number((m.responseCache.hitRate * 100).toFixed(1)),
        connReuse: m.connectionPool.connectionReuse,
        errPct: Number((m.overall.errorRate * 100).toFixed(2)),
      }));
      this.autoOptimize();
    }, this.config.metricsInterval);
  }
}

/* --------------------------------
 * Global singleton helpers
 * ------------------------------ */

let performanceOptimizer: PerformanceOptimizer | null = null;

export function getPerformanceOptimizer(): PerformanceOptimizer {
  if (!performanceOptimizer) {
    performanceOptimizer = new PerformanceOptimizer();
  }
  return performanceOptimizer;
}

export function initializePerformanceOptimizer(config?: Partial<PerformanceConfig>): PerformanceOptimizer {
  if (performanceOptimizer) {
    // Best-effort shutdown of old instance
    void performanceOptimizer.shutdown();
  }
  performanceOptimizer = new PerformanceOptimizer(config);
  return performanceOptimizer;
}

export async function shutdownPerformanceOptimizer(): Promise<void> {
  if (performanceOptimizer) {
    await performanceOptimizer.shutdown();
    performanceOptimizer = null;
  }
}
