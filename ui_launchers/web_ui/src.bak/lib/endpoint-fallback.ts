/**
 * Endpoint Fallback Service
 * Provides automatic fallback to alternative endpoints when primary fails
 */

import { getEndpointTester, type EndpointTestResult } from './endpoint-tester';
import { getConfigManager } from './endpoint-config';

export interface FallbackConfig {
  maxRetries: number;
  retryDelay: number;
  healthCheckInterval: number;
  cacheEndpointSelection: boolean;
  cacheTtl: number;
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
  responseTime: number;
  healthScore: number; // 0-100
  reliability: number; // 0-100 based on success rate
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
  responseTime: number;
  timestamp: string;
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
  private healthCheckInterval: NodeJS.Timeout | null = null;

  constructor(config?: Partial<FallbackConfig>) {
    this.config = {
      maxRetries: 3,
      retryDelay: 1000,
      healthCheckInterval: 30000, // 30 seconds
      cacheEndpointSelection: true,
      cacheTtl: 60000, // 1 minute
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
   * Initialize endpoint statistics
   */
  private initializeEndpointStats(): void {
    const allEndpoints = this.getAllEndpoints();
    
    for (const endpoint of allEndpoints) {
      if (!this.endpointStats.has(endpoint)) {
        this.endpointStats.set(endpoint, {
          endpoint,
          isActive: true,
          lastTested: new Date().toISOString(),
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
    const config = this.configManager.getConfiguration();
    return [config.backendUrl, ...config.fallbackUrls];
  }

  /**
   * Select the best available endpoint
   */
  public async selectBestEndpoint(requestType: 'api' | 'auth' | 'chat' | 'health' = 'api'): Promise<string> {
    const cacheKey = `best-endpoint:${requestType}`;
    
    // Check cache first
    if (this.config.cacheEndpointSelection) {
      const cached = this.endpointCache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < this.config.cacheTtl) {
        return cached.endpoint;
      }
    }

    const allEndpoints = this.getAllEndpoints();
    const activeEndpoints = allEndpoints.filter(endpoint => {
      const stats = this.endpointStats.get(endpoint);
      return stats?.isActive !== false;
    });

    if (activeEndpoints.length === 0) {
      // All endpoints are marked as inactive, try primary anyway
      const primaryEndpoint = this.configManager.getBackendUrl();
      this.cacheEndpointSelection(cacheKey, primaryEndpoint);
      return primaryEndpoint;
    }

    // Score and rank endpoints
    const scoredEndpoints = await this.scoreEndpoints(activeEndpoints);
    
    // Select the best endpoint
    const bestEndpoint = scoredEndpoints[0]?.endpoint || this.configManager.getBackendUrl();
    
    // Cache the selection
    this.cacheEndpointSelection(cacheKey, bestEndpoint);
    
    return bestEndpoint;
  }

  /**
   * Attempt request with automatic fallback
   */
  public async requestWithFallback<T>(
    requestFn: (endpoint: string) => Promise<T>,
    requestType: 'api' | 'auth' | 'chat' | 'health' = 'api'
  ): Promise<{ data: T; fallbackResult: FallbackResult }> {
    const startTime = performance.now();
    const timestamp = new Date().toISOString();
    const attemptedEndpoints: string[] = [];
    const failedEndpoints: string[] = [];
    
    let selectedEndpoint = await this.selectBestEndpoint(requestType);
    let wasFailover = false;

    // Try primary endpoint first
    attemptedEndpoints.push(selectedEndpoint);
    
    try {
      const data = await requestFn(selectedEndpoint);
      this.recordSuccess(selectedEndpoint, performance.now() - startTime);
      
      return {
        data,
        fallbackResult: {
          selectedEndpoint,
          wasFailover,
          attemptedEndpoints,
          failedEndpoints,
          responseTime: performance.now() - startTime,
          timestamp,
        },
      };
    } catch (error) {
      this.recordFailure(selectedEndpoint, error);
      failedEndpoints.push(selectedEndpoint);
    }

    // Try fallback endpoints
    const allEndpoints = this.getAllEndpoints();
    const fallbackEndpoints = allEndpoints.filter(ep => ep !== selectedEndpoint);
    
    for (const endpoint of fallbackEndpoints) {
      attemptedEndpoints.push(endpoint);
      wasFailover = true;

      try {
        // Add delay between attempts
        if (failedEndpoints.length > 0) {
          await this.delay(this.config.retryDelay * failedEndpoints.length);
        }

        const data = await requestFn(endpoint);
        this.recordSuccess(endpoint, performance.now() - startTime);
        
        // Update cache to prefer this working endpoint
        this.cacheEndpointSelection(`best-endpoint:${requestType}`, endpoint);
        
        return {
          data,
          fallbackResult: {
            selectedEndpoint: endpoint,
            wasFailover,
            attemptedEndpoints,
            failedEndpoints,
            responseTime: performance.now() - startTime,
            timestamp,
          },
        };
      } catch (error) {
        this.recordFailure(endpoint, error);
        failedEndpoints.push(endpoint);
      }
    }

    // All endpoints failed
    throw new Error(
      `All endpoints failed. Attempted: ${attemptedEndpoints.join(', ')}. ` +
      `Failed: ${failedEndpoints.join(', ')}`
    );
  }

  /**
   * Score endpoints based on performance and reliability
   */
  private async scoreEndpoints(endpoints: string[]): Promise<Array<{ endpoint: string; score: number }>> {
    const scored: Array<{ endpoint: string; score: number }> = [];

    for (const endpoint of endpoints) {
      const stats = this.endpointStats.get(endpoint);
      if (!stats) continue;

      let score = 0;

      // Response time score (lower is better)
      const responseTimeScore = Math.max(0, 100 - (stats.responseTime / 100)); // 10s = 0 points
      score += responseTimeScore * this.config.priorityWeights.responseTime;

      // Health score
      score += stats.healthScore * this.config.priorityWeights.healthScore;

      // Reliability score
      score += stats.reliability * this.config.priorityWeights.reliability;

      // Penalty for consecutive failures
      const failurePenalty = Math.min(50, stats.consecutiveFailures * 10);
      score -= failurePenalty;

      scored.push({ endpoint, score: Math.max(0, score) });
    }

    // Sort by score (descending)
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
    stats.responseTime = responseTime;
    stats.reliability = (stats.successfulRequests / stats.totalRequests) * 100;
    stats.lastTested = new Date().toISOString();
    stats.isActive = true;

    // Update health score based on response time
    if (responseTime < 1000) {
      stats.healthScore = Math.min(100, stats.healthScore + 1);
    } else if (responseTime > 5000) {
      stats.healthScore = Math.max(0, stats.healthScore - 5);
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
    stats.reliability = (stats.successfulRequests / stats.totalRequests) * 100;
    stats.lastTested = new Date().toISOString();
    stats.lastError = error instanceof Error ? error.message : 'Unknown error';

    // Reduce health score
    stats.healthScore = Math.max(0, stats.healthScore - 10);

    // Mark as inactive after too many consecutive failures
    if (stats.consecutiveFailures >= 3) {
      stats.isActive = false;
    }

    this.endpointStats.set(endpoint, stats);
  }

  /**
   * Cache endpoint selection
   */
  private cacheEndpointSelection(cacheKey: string, endpoint: string): void {
    this.endpointCache.set(cacheKey, {
      endpoint,
      timestamp: Date.now(),
    });
  }

  /**
   * Start periodic health checking
   */
  private startHealthChecking(): void {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }

    this.healthCheckInterval = setInterval(async () => {
      await this.performHealthChecks();
    }, this.config.healthCheckInterval);
  }

  /**
   * Perform health checks on all endpoints
   */
  private async performHealthChecks(): Promise<void> {
    const allEndpoints = this.getAllEndpoints();
    
    const healthCheckPromises = allEndpoints.map(async (endpoint) => {
      try {
        const result = await this.endpointTester.testHealth(endpoint);
        const stats = this.endpointStats.get(endpoint);
        
        if (stats) {
          stats.lastTested = new Date().toISOString();
          
          if (result.isReachable) {
            stats.healthScore = Math.min(100, stats.healthScore + 5);
            stats.responseTime = result.responseTime;
            
            // Reactivate if it was inactive
            if (!stats.isActive && stats.consecutiveFailures > 0) {
              stats.consecutiveFailures = Math.max(0, stats.consecutiveFailures - 1);
              if (stats.consecutiveFailures === 0) {
                stats.isActive = true;
              }
            }
          } else {
            stats.healthScore = Math.max(0, stats.healthScore - 5);
            stats.lastError = result.error;
          }
          
          this.endpointStats.set(endpoint, stats);
        }
      } catch (error) {
        // Health check failed, but don't penalize too heavily
        const stats = this.endpointStats.get(endpoint);
        if (stats) {
          stats.healthScore = Math.max(0, stats.healthScore - 2);
          stats.lastError = error instanceof Error ? error.message : 'Health check failed';
          this.endpointStats.set(endpoint, stats);
        }
      }
    });

    await Promise.allSettled(healthCheckPromises);
  }

  /**
   * Get endpoint statistics
   */
  public getEndpointStats(): Map<string, EndpointStatus> {
    return new Map(this.endpointStats);
  }

  /**
   * Get endpoint statistics as array
   */
  public getEndpointStatsArray(): EndpointStatus[] {
    return Array.from(this.endpointStats.values());
  }

  /**
   * Reset endpoint statistics
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
        this.endpointStats.set(endpoint, stats);
      }
    } else {
      this.initializeEndpointStats();
    }
  }

  /**
   * Manually mark endpoint as active/inactive
   */
  public setEndpointActive(endpoint: string, isActive: boolean): void {
    const stats = this.endpointStats.get(endpoint);
    if (stats) {
      stats.isActive = isActive;
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
    return {
      size: this.endpointCache.size,
      keys: Array.from(this.endpointCache.keys()),
    };
  }

  /**
   * Update configuration
   */
  public updateConfig(config: Partial<FallbackConfig>): void {
    this.config = { ...this.config, ...config };
    
    // Restart health checking if interval changed
    if (config.healthCheckInterval) {
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
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Cleanup resources
   */
  public destroy(): void {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
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
export function initializeEndpointFallbackService(config?: Partial<FallbackConfig>): EndpointFallbackService {
  if (fallbackService) {
    fallbackService.destroy();
  }
  fallbackService = new EndpointFallbackService(config);
  return fallbackService;
}

// Export types
export type {
  FallbackConfig as FallbackConfigType,
  EndpointStatus as EndpointStatusType,
  FallbackResult as FallbackResultType,
};