/**
 * Endpoint Fallback Service
 * Provides automatic fallback to alternative endpoints when primary fails
 * Prod-grade, browser/Node universal, with health scoring + retries
 */

import { getEndpointTester, type EndpointTestResult } from './endpoint-tester';
import { getConfigManager } from './endpoint-config';

export interface FallbackConfig {
  maxRetries: number;                 // retries per endpoint before moving on
  retryDelay: number;                 // base delay (ms) for backoff
  healthCheckInterval: number;        // ms between health sweeps
  cacheEndpointSelection: boolean;    // cache "best endpoint" per requestType
  cacheTtl: number;                   // ms TTL of best-endpoint cache
  cooldownFailuresToDisable: number;  // consecutive failures to mark inactive
  reenableOnHealthOk: boolean;        // allow health pass to reenable
  flapCooldownMs: number;             // prevent rapid enable/disable flapping
  priorityWeights: {
    responseTime: number;
    healthScore: number;
    reliability: number;
  };
}

export interface EndpointStatus {
  endpoint: string;
  isActive: boolean;
  lastTested: string;
  lastStateChange?: string;
  responseTime: number;   // ms (recent)
  healthScore: number;    // 0-100
  reliability: number;    // 0-100 (success/total)
  consecutiveFailures: number;
  totalRequests: number;
  successfulRequests: number;
  lastError?: string;
}

export interface FallbackResult {
  selectedEndpoint: string;
  wasFailover: boolean;
  attemptedEndpoints: string[];
  failedEndpoints: string[];
  responseTime: number; // ms
  timestamp: string;
}

export type TimerHandle = ReturnType<typeof setInterval>;

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function jitter(ms: number) {
  // ±20% jitter
  const range = ms * 0.2;
  return ms + (Math.random() * 2 - 1) * range;
}

function performanceNow(): number {
  // universal monotonic-ish time
  if (typeof performance !== 'undefined' && performance.now) return performance.now();
  return Date.now();
}

/**
 * Service for managing endpoint fallback and selection
 */
export class EndpointFallbackService {
  private config: FallbackConfig;
  private configManager = getConfigManager();
  private endpointTester = getEndpointTester();

  private endpointStats: Map<string, EndpointStatus> = new Map();
  private endpointCache: Map<string, { endpoint: string; timestamp: number }> = new Map();
  private healthTimer: TimerHandle | null = null;

  constructor(config?: Partial<FallbackConfig>) {
    this.config = {
      maxRetries: 2,
      retryDelay: 600,
      healthCheckInterval: 30000,
      cacheEndpointSelection: true,
      cacheTtl: 60000,
      cooldownFailuresToDisable: 3,
      reenableOnHealthOk: true,
      flapCooldownMs: 5000,
      priorityWeights: {
        responseTime: 0.4,
        healthScore: 0.4,
        reliability: 0.2,
      },
      ...config,
    };

    this.initializeEndpointStats();
    this.startHealthChecking();
  }

  /**
   * Initialize / reconcile endpoint statistics with current configuration
   */
  private initializeEndpointStats(): void {
    const all = this.getAllEndpoints();
    const allSet = new Set(all);

    // Remove stale endpoints
    for (const key of this.endpointStats.keys()) {
      if (!allSet.has(key)) this.endpointStats.delete(key);
    }

    // Add missing endpoints with warm defaults
    const now = new Date().toISOString();
    for (const endpoint of all) {
      if (!this.endpointStats.has(endpoint)) {
        this.endpointStats.set(endpoint, {
          endpoint,
          isActive: true,
          lastTested: now,
          lastStateChange: now,
          responseTime: 0,
          healthScore: 100,
          reliability: 100,
          consecutiveFailures: 0,
          totalRequests: 0,
          successfulRequests: 0,
        });
      }
    }
  }

  /**
   * Get all available endpoints (primary + fallbacks)
   */
  private getAllEndpoints(): string[] {
    const cfg = this.configManager.getConfiguration?.() ?? {};
    const primary = (cfg.backendUrl || '').trim();
    const fallbacks: string[] = Array.isArray(cfg.fallbackUrls) ? cfg.fallbackUrls : [];
    const list = [primary, ...fallbacks].map((e) => (e || '').trim()).filter(Boolean);

    // Basic URL sanity (keep http/https only)
    const httpish = list.filter((u) => /^https?:\/\//i.test(u));
    return Array.from(new Set(httpish));
  }

  /**
   * Select the best available endpoint (cached per requestType)
   */
  public async selectBestEndpoint(
    requestType: 'api' | 'auth' | 'chat' | 'health' = 'api'
  ): Promise<string> {
    const cacheKey = `best-endpoint:${requestType}`;

    if (this.config.cacheEndpointSelection) {
      const cached = this.endpointCache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < this.config.cacheTtl) {
        return cached.endpoint;
      }
    }

    const allEndpoints = this.getAllEndpoints();
    const activeEndpoints = allEndpoints.filter((endpoint) => {
      const stats = this.endpointStats.get(endpoint);
      return stats?.isActive !== false;
    });

    if (activeEndpoints.length === 0) {
      // All inactive — prefer primary anyway as a last hope
      const primaryEndpoint = this.configManager.getBackendUrl?.() ?? allEndpoints[0] ?? '';
      this.cacheEndpointSelection(cacheKey, primaryEndpoint);
      return primaryEndpoint;
    }

    const ranked = await this.scoreEndpoints(activeEndpoints);
    const bestEndpoint = ranked[0]?.endpoint ?? (this.configManager.getBackendUrl?.() ?? activeEndpoints[0]);
    this.cacheEndpointSelection(cacheKey, bestEndpoint);
    return bestEndpoint;
  }

  /**
   * Attempt request with automatic fallback and per-endpoint retries
   */
  public async requestWithFallback<T>(
    requestFn: (endpoint: string) => Promise<T>,
    requestType: 'api' | 'auth' | 'chat' | 'health' = 'api'
  ): Promise<{ data: T; fallbackResult: FallbackResult }> {
    const startTime = performanceNow();
    const timestamp = new Date().toISOString();
    const attemptedEndpoints: string[] = [];
    const failedEndpoints: string[] = [];

    const selectedEndpoint = await this.selectBestEndpoint(requestType);
    let wasFailover = false;

    // Helper: try one endpoint with retries/backoff
    const tryEndpoint = async (endpoint: string): Promise<T> => {
      let attempt = 0;
      let lastErr: unknown = null;
      while (attempt <= this.config.maxRetries) {
        try {
          const data = await requestFn(endpoint);
          return data;
        } catch (e) {
          lastErr = e;
          attempt++;
          if (attempt > this.config.maxRetries) break;
          const delay = jitter(this.config.retryDelay * Math.pow(2, attempt - 1));
          await this.delay(delay);
        }
      }
      throw lastErr;
    };

    // Primary candidate
    attemptedEndpoints.push(selectedEndpoint);
    try {
      const data = await tryEndpoint(selectedEndpoint);
      this.recordSuccess(selectedEndpoint, performanceNow() - startTime);
      return {
        data,
        fallbackResult: {
          selectedEndpoint,
          wasFailover,
          attemptedEndpoints,
          failedEndpoints,
          responseTime: performanceNow() - startTime,
          timestamp,
        },
      };
    } catch (error) {
      this.recordFailure(selectedEndpoint, error);
      failedEndpoints.push(selectedEndpoint);
    }

    // Fallbacks
    const all = this.getAllEndpoints();
    const fallbacks = all.filter((ep) => ep !== selectedEndpoint);

    for (const endpoint of fallbacks) {
      attemptedEndpoints.push(endpoint);
      wasFailover = true;

      // Inter-endpoint spacing grows with number of failures so far
      if (failedEndpoints.length > 0) {
        await this.delay(jitter(this.config.retryDelay * failedEndpoints.length));
      }

      try {
        const data = await tryEndpoint(endpoint);
        this.recordSuccess(endpoint, performanceNow() - startTime);
        this.cacheEndpointSelection(`best-endpoint:${requestType}`, endpoint);
        return {
          data,
          fallbackResult: {
            selectedEndpoint: endpoint,
            wasFailover,
            attemptedEndpoints,
            failedEndpoints,
            responseTime: performanceNow() - startTime,
            timestamp,
          },
        };
      } catch (error) {
        this.recordFailure(endpoint, error);
        failedEndpoints.push(endpoint);
      }
    }

    // All endpoints failed
    const attemptedMsg = attemptedEndpoints.length ? attemptedEndpoints.join(', ') : '(none)';
    const failedMsg = failedEndpoints.length ? failedEndpoints.join(', ') : '(none)';
    throw new Error(`All endpoints failed. Attempted: ${attemptedMsg}. Failed: ${failedMsg}`);
  }

  /**
   * Score endpoints based on performance, health, reliability, and staleness
   */
  private async scoreEndpoints(
    endpoints: string[]
  ): Promise<Array<{ endpoint: string; score: number }>> {
    const scored: Array<{ endpoint: string; score: number }> = [];
    const now = Date.now();

    for (const endpoint of endpoints) {
      const stats = this.endpointStats.get(endpoint);
      if (!stats) continue;

      // Response time: lower is better. 0 (unknown) treated as neutral 50.
      const rt = stats.responseTime > 0 ? stats.responseTime : 2000; // ms
      const responseTimeScore = clamp(100 - rt / 50, 0, 100); // 0 at ~5s, 100 at ~0ms

      // Freshness decay: if we haven't tested recently, down-weight slightly
      const last = new Date(stats.lastTested).getTime();
      const ageSec = (now - last) / 1000;
      const freshnessPenalty = clamp(ageSec / 2, 0, 15); // max 15 pts penalty

      // Flapping protection: if state changed very recently, down-weight
      let flapPenalty = 0;
      if (stats.lastStateChange) {
        const lastChange = new Date(stats.lastStateChange).getTime();
        const age = now - lastChange;
        if (age < this.config.flapCooldownMs) {
          flapPenalty = 10; // fixed penalty to avoid ping-pong
        }
      }

      let score =
        responseTimeScore * this.config.priorityWeights.responseTime +
        clamp(stats.healthScore, 0, 100) * this.config.priorityWeights.healthScore +
        clamp(stats.reliability, 0, 100) * this.config.priorityWeights.reliability;

      // Penalty for consecutive failures
      const failurePenalty = clamp(stats.consecutiveFailures * 8, 0, 40);

      score = clamp(score - freshnessPenalty - flapPenalty - failurePenalty, 0, 100);

      scored.push({ endpoint, score });
    }

    scored.sort((a, b) => b.score - a.score);
    return scored;
  }

  /**
   * Record successful request
   */
  private recordSuccess(endpoint: string, responseTime: number): void {
    const stats = this.endpointStats.get(endpoint);
    if (!stats) return;

    stats.totalRequests++;
    stats.successfulRequests++;
    stats.consecutiveFailures = 0;
    stats.responseTime = Math.max(0, responseTime);
    stats.reliability = clamp((stats.successfulRequests / stats.totalRequests) * 100, 0, 100);
    stats.lastTested = new Date().toISOString();

    // Gentle health adjustments
    if (responseTime < 600) {
      stats.healthScore = clamp(stats.healthScore + 2, 0, 100);
    } else if (responseTime < 1500) {
      stats.healthScore = clamp(stats.healthScore + 1, 0, 100);
    } else if (responseTime > 5000) {
      stats.healthScore = clamp(stats.healthScore - 3, 0, 100);
    }

    if (!stats.isActive) {
      stats.isActive = true;
      stats.lastStateChange = new Date().toISOString();
    }

    this.endpointStats.set(endpoint, stats);
  }

  /**
   * Record failed request
   */
  private recordFailure(endpoint: string, error: unknown): void {
    const stats = this.endpointStats.get(endpoint);
    if (!stats) return;

    stats.totalRequests++;
    stats.consecutiveFailures++;
    stats.reliability = clamp((stats.successfulRequests / stats.totalRequests) * 100, 0, 100);
    stats.lastTested = new Date().toISOString();
    stats.lastError =
      error instanceof Error
        ? `${error.name}: ${error.message}`
        : typeof error === 'string'
        ? error
        : 'Unknown error';

    // Reduce health score more aggressively on failure
    stats.healthScore = clamp(stats.healthScore - 10, 0, 100);

    // Mark inactive after too many consecutive failures
    if (stats.consecutiveFailures >= this.config.cooldownFailuresToDisable && stats.isActive) {
      stats.isActive = false;
      stats.lastStateChange = new Date().toISOString();
    }

    this.endpointStats.set(endpoint, stats);
  }

  /**
   * Cache endpoint selection
   */
  private cacheEndpointSelection(cacheKey: string, endpoint: string): void {
    this.endpointCache.set(cacheKey, { endpoint, timestamp: Date.now() });
  }

  /**
   * Start periodic health checking
   */
  private startHealthChecking(): void {
    if (this.healthTimer) clearInterval(this.healthTimer);
    this.healthTimer = setInterval(async () => {
      try {
        await this.performHealthChecks();
      } catch {
        // swallow — health loop must not crash
      }
    }, this.config.healthCheckInterval);
  }

  /**
   * Perform health checks on all endpoints
   */
  private async performHealthChecks(): Promise<void> {
    const allEndpoints = this.getAllEndpoints();
    const nowIso = new Date().toISOString();

    const healthCheckPromises = allEndpoints.map(async (endpoint) => {
      try {
        const result: EndpointTestResult = await this.endpointTester.testHealth(endpoint);
        const stats = this.endpointStats.get(endpoint);
        if (!stats) return;

        stats.lastTested = nowIso;

        if (result.isReachable) {
          // Improve health modestly; update response time
          stats.healthScore = clamp(stats.healthScore + 5, 0, 100);
          stats.responseTime = result.responseTime;

          // Optionally re-enable endpoint when health is ok and failures are cleared
          if (this.config.reenableOnHealthOk) {
            if (!stats.isActive) {
              // Avoid immediate flap: only reenable if no recent state change
              const lastChange = stats.lastStateChange ? new Date(stats.lastStateChange).getTime() : 0;
              if (!lastChange || Date.now() - lastChange > this.config.flapCooldownMs) {
                stats.consecutiveFailures = Math.max(0, stats.consecutiveFailures - 1);
                if (stats.consecutiveFailures === 0) {
                  stats.isActive = true;
                  stats.lastStateChange = nowIso;
                }
              }
            }
          }
        } else {
          stats.healthScore = clamp(stats.healthScore - 5, 0, 100);
          stats.lastError = result.error ?? 'Unreachable';
        }

        this.endpointStats.set(endpoint, stats);
      } catch (error) {
        // Health check failed (timeout/network); minor penalty
        const stats = this.endpointStats.get(endpoint);
        if (!stats) return;
        stats.healthScore = clamp(stats.healthScore - 2, 0, 100);
        stats.lastError =
          error instanceof Error ? `${error.name}: ${error.message}` : 'Health check failed';
        stats.lastTested = nowIso;
        this.endpointStats.set(endpoint, stats);
      }
    });

    await Promise.allSettled(healthCheckPromises);
  }

  /**
   * Public: get endpoint statistics
   */
  public getEndpointStats(): Map<string, EndpointStatus> {
    return new Map(this.endpointStats);
  }

  /**
   * Public: get endpoint statistics as array
   */
  public getEndpointStatsArray(): EndpointStatus[] {
    return Array.from(this.endpointStats.values());
  }

  /**
   * Reset endpoint statistics (single or all)
   */
  public resetEndpointStats(endpoint?: string): void {
    if (endpoint) {
      const stats = this.endpointStats.get(endpoint);
      if (stats) {
        stats.consecutiveFailures = 0;
        stats.totalRequests = 0;
        stats.successfulRequests = 0;
        stats.healthScore = 100;
        stats.reliability = 100;
        stats.isActive = true;
        stats.lastError = undefined;
        stats.lastStateChange = new Date().toISOString();
        this.endpointStats.set(endpoint, stats);
      }
    } else {
      // full reconcile to current configuration
      this.endpointStats.clear();
      this.initializeEndpointStats();
    }
  }

  /**
   * Manually mark endpoint as active/inactive
   */
  public setEndpointActive(endpoint: string, isActive: boolean): void {
    const stats = this.endpointStats.get(endpoint);
    if (stats) {
      if (stats.isActive !== isActive) {
        stats.isActive = isActive;
        stats.lastStateChange = new Date().toISOString();
      }
      if (isActive) {
        stats.consecutiveFailures = 0;
      }
      this.endpointStats.set(endpoint, stats);
    }
  }

  /**
   * Clear endpoint cache
   */
  public clearCache(): void {
    this.endpointCache.clear();
  }

  /**
   * Get cache statistics
   */
  public getCacheStats(): { size: number; keys: string[] } {
    return { size: this.endpointCache.size, keys: Array.from(this.endpointCache.keys()) };
  }

  /**
   * Update configuration (auto-restart health timer if interval changed)
   */
  public updateConfig(config: Partial<FallbackConfig>): void {
    const prevInterval = this.config.healthCheckInterval;
    this.config = { ...this.config, ...config };
    if (
      typeof config.healthCheckInterval === 'number' &&
      config.healthCheckInterval !== prevInterval
    ) {
      this.startHealthChecking();
    }
  }

  /**
   * Get current configuration
   */
  public getConfig(): FallbackConfig {
    return { ...this.config };
  }

  /**
   * Delay utility
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, Math.max(0, ms)));
  }

  /**
   * Cleanup resources
   */
  public destroy(): void {
    if (this.healthTimer) {
      clearInterval(this.healthTimer);
      this.healthTimer = null;
    }
    this.endpointStats.clear();
    this.endpointCache.clear();
  }
}

// Singleton instance
let fallbackService: EndpointFallbackService | null = null;

/**
 * Get the global endpoint fallback service instance
 */
export function getEndpointFallbackService(): EndpointFallbackService {
  if (!fallbackService) {
    fallbackService = new EndpointFallbackService();
  }
  return fallbackService;
}

/**
 * Initialize endpoint fallback service with custom configuration
 */
export function initializeEndpointFallbackService(
  config?: Partial<FallbackConfig>
): EndpointFallbackService {
  if (fallbackService) {
    fallbackService.destroy();
  }
  fallbackService = new EndpointFallbackService(config);
  return fallbackService;
}
