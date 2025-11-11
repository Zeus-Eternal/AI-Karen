/**
 * Enhanced backend service with graceful degradation support
 * Wraps an existing backend client (originalService) and adds:
 *  - Feature-flag gating
 *  - Health state & exponential backoff retries
 *  - Cache-aware degraded mode with stale-while-revalidate
 *  - Specific handling for auth & service-unavailable errors
 */

import { featureFlagManager, extensionCache, CacheAwareDataFetcher } from "./index";

export interface EnhancedRequestOptions {
  endpoint: string;
  options?: RequestInit;
  cacheKey?: string;
  enableCaching?: boolean;
  useStaleOnError?: boolean;
  maxStaleAge?: number;
  fallbackData?: unknown;
  serviceName?: string;
}

export interface ServiceHealthStatus {
  isHealthy: boolean;
  lastSuccessfulRequest?: Date;
  consecutiveFailures: number;
  lastError?: Error;
}

const MAX_RETRIES_DEFAULT = 3;
const BASE_RETRY_DELAY_MS = 1000;

export class EnhancedBackendService {
  private serviceHealth: Map<string, ServiceHealthStatus> = new Map();
  private readonly maxRetries: number;
  private readonly baseRetryDelay: number;

  constructor(private originalService: { makeRequest: (endpoint: string, init?: RequestInit) => Promise<unknown> }, opts?: { maxRetries?: number; baseRetryDelayMs?: number }) {
    this.maxRetries = Math.max(1, opts?.maxRetries ?? MAX_RETRIES_DEFAULT);
    this.baseRetryDelay = Math.max(250, opts?.baseRetryDelayMs ?? BASE_RETRY_DELAY_MS);
  }

  /**
   * Core request wrapper with resilience + cache support.
   */
  async makeEnhancedRequest<T>(opts: EnhancedRequestOptions): Promise<T> {
    const {
      endpoint,
      options: requestOptions = {},
      cacheKey,
      enableCaching = true,
      useStaleOnError = true,
      maxStaleAge = 60 * 60 * 1000, // 1 hour
      fallbackData,
      serviceName = this.getServiceNameFromEndpoint(endpoint),
    } = opts;

    // 1) Feature gate
    const featureName = this.getFeatureNameFromService(serviceName);
    if (!featureFlagManager.isEnabled(featureName)) {
      return this.handleDisabledService<T>(serviceName, cacheKey, fallbackData, useStaleOnError, maxStaleAge);
    }

    // 2) Fast path for services recently marked as unhealthy
    const healthStatus = this.getServiceHealth(serviceName);
    if (!healthStatus.isHealthy && healthStatus.consecutiveFailures >= 3) {
      return this.handleUnhealthyService<T>(serviceName, cacheKey, fallbackData, useStaleOnError, maxStaleAge);
    }

    // 3) Attempt with retries
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        let result: T;

        if (enableCaching && cacheKey) {
          // Per-call fetcher using the current endpoint/init
          const fetcher = new CacheAwareDataFetcher(
            extensionCache,
            async () => await this.originalService.makeRequest(endpoint, requestOptions)
          );

          result = await fetcher.fetchWithCache<T>(cacheKey, {
            useStaleOnError,
            maxStaleAge,
            ttl: 5 * 60 * 1000, // 5 minutes
          });
        } else {
          result = await this.originalService.makeRequest(endpoint, requestOptions) as T;
        }

        // Success: mark healthy and return
        this.markServiceHealthy(serviceName);
        return result;
      } catch (e) {
        lastError = e as Error;

        // Special cases
        if (this.isAuthenticationError(lastError)) {
          return this.handleAuthenticationError<T>(serviceName, endpoint, lastError, cacheKey, fallbackData, useStaleOnError, maxStaleAge);
        }
        if (this.isServiceUnavailableError(lastError)) {
          // Only fallback on last attempt; otherwise retry
          if (attempt === this.maxRetries) {
            return this.handleServiceUnavailableError<T>(serviceName, endpoint, lastError, attempt, cacheKey, fallbackData, useStaleOnError, maxStaleAge);
          }
        }

        // Mark unhealthy and backoff unless final attempt
        this.markServiceUnhealthy(serviceName, lastError);
        if (attempt === this.maxRetries) {
          return this.handleFinalFailure<T>(serviceName, endpoint, lastError, cacheKey, fallbackData, useStaleOnError, maxStaleAge);
        }

        await this.delay(this.jitter(this.baseRetryDelay * Math.pow(2, attempt - 1)));
      }
    }

    // Should not reach
    throw lastError || new Error("Unknown failure");
  }

  /** ---------- Degraded-mode handlers ---------- */

  private async handleDisabledService<T>(
    serviceName: string,
    cacheKey?: string,
    fallbackData?: unknown,
    useStaleOnError?: boolean,
    maxStaleAge?: number
  ): Promise<T> {
    if (cacheKey && useStaleOnError) {
      const cached = extensionCache.getStale<T>(cacheKey, maxStaleAge);
      if (cached !== null) return cached;
    }
    if (fallbackData !== undefined) return fallbackData as T;
    throw new Error(`Service "${serviceName}" is disabled and no fallback is available.`);
  }

  private async handleUnhealthyService<T>(
    serviceName: string,
    cacheKey?: string,
    fallbackData?: unknown,
    useStaleOnError?: boolean,
    maxStaleAge?: number
  ): Promise<T> {
    if (cacheKey && useStaleOnError) {
      const cached = extensionCache.getStale<T>(cacheKey, maxStaleAge);
      if (cached !== null) return cached;
    }
    if (fallbackData !== undefined) return fallbackData as T;
    throw new Error(`Service "${serviceName}" is unhealthy and no fallback is available.`);
  }

  private async handleAuthenticationError<T>(
    serviceName: string,
    _endpoint: string,
    error: Error,
    cacheKey?: string,
    fallbackData?: unknown,
    useStaleOnError?: boolean,
    maxStaleAge?: number
  ): Promise<T> {
    // Disable extension auth related flag; downstream UI should prompt re-auth
    featureFlagManager.handleServiceError("extension-auth", error);

    if (cacheKey && useStaleOnError) {
      const cached = extensionCache.getStale<T>(cacheKey, maxStaleAge);
      if (cached !== null) return cached;
    }
    if (fallbackData !== undefined) return fallbackData as T;

    throw error;
  }

  private async handleServiceUnavailableError<T>(
    serviceName: string,
    _endpoint: string,
    error: Error,
    attempt: number,
    cacheKey?: string,
    fallbackData?: unknown,
    useStaleOnError?: boolean,
    maxStaleAge?: number
  ): Promise<T> {
    console.warn(`Service unavailable for ${serviceName} (attempt ${attempt}): ${error.message}`);
    featureFlagManager.handleServiceError(serviceName, error);

    if (cacheKey && useStaleOnError) {
      const cached = extensionCache.getStale<T>(cacheKey, maxStaleAge);
      if (cached !== null) return cached;
    }
    if (fallbackData !== undefined) return fallbackData as T;

    throw error;
  }

  private async handleFinalFailure<T>(
    serviceName: string,
    _endpoint: string,
    error: Error,
    cacheKey?: string,
    fallbackData?: unknown,
    useStaleOnError?: boolean,
    maxStaleAge?: number
  ): Promise<T> {
    featureFlagManager.handleServiceError(serviceName, error);

    if (cacheKey && useStaleOnError) {
      const cached = extensionCache.getStale<T>(cacheKey, maxStaleAge);
      if (cached !== null) return cached;
    }
    if (fallbackData !== undefined) return fallbackData as T;

    throw error;
  }

  /** ---------- Heuristics & helpers ---------- */

  private isAuthenticationError(error: unknown): boolean {
    const errorObj = error as { status?: number; message?: string };
    const msg = String(errorObj?.message ?? "").toLowerCase();
    return errorObj?.status === 401 || errorObj?.status === 403 || msg.includes("authentication") || msg.includes("unauthorized") || msg.includes("forbidden");
  }

  private isServiceUnavailableError(error: unknown): boolean {
    const errorObj = error as { status?: number; message?: string };
    const msg = String(errorObj?.message ?? "").toLowerCase();
    return errorObj?.status === 502 || errorObj?.status === 503 || errorObj?.status === 504 || msg.includes("service unavailable") || msg.includes("network error") || msg.includes("timeout");
  }

  private getServiceNameFromEndpoint(endpoint: string): string {
    if (endpoint.includes("/api/extensions")) return "extension-api";
    if (endpoint.includes("/api/models")) return "model-provider";
    if (endpoint.includes("/api/health")) return "extension-health";
    if (endpoint.includes("background-task")) return "background-tasks";
    return "unknown-service";
  }

  private getFeatureNameFromService(serviceName: string): string {
    const mapping: Record<string, string> = {
      "extension-api": "extensionSystem",
      "model-provider": "modelProviderIntegration",
      "extension-health": "extensionHealth",
      "background-tasks": "backgroundTasks",
      "unknown-service": "extensionSystem",
    };
    return mapping[serviceName] ?? "extensionSystem";
  }

  private getServiceHealth(serviceName: string): ServiceHealthStatus {
    if (!this.serviceHealth.has(serviceName)) {
      this.serviceHealth.set(serviceName, {
        isHealthy: true,
        consecutiveFailures: 0,
      });
    }
    return this.serviceHealth.get(serviceName)!;
  }

  private markServiceHealthy(serviceName: string): void {
    const health = this.getServiceHealth(serviceName);
    health.isHealthy = true;
    health.lastSuccessfulRequest = new Date();
    health.consecutiveFailures = 0;
    health.lastError = undefined;

    // If a previous error flipped a feature off, flip it back on
    const featureName = this.getFeatureNameFromService(serviceName);
    if (!featureFlagManager.isEnabled(featureName)) {
      featureFlagManager.handleServiceRecovery(serviceName);
    }
  }

  private markServiceUnhealthy(serviceName: string, error: Error): void {
    const health = this.getServiceHealth(serviceName);
    health.isHealthy = false;
    health.consecutiveFailures += 1;
    health.lastError = error;
  }

  private delay(ms: number): Promise<void> {
    return new Promise((r) => setTimeout(r, ms));
  }

  private jitter(ms: number): number {
    const delta = Math.floor(ms * 0.2); // ±20% jitter
    return ms - delta + Math.floor(Math.random() * (2 * delta + 1));
  }

  /** ---------- Convenience endpoints ---------- */

  async getExtensions(useCache: boolean = true): Promise<unknown[]> {
    return this.makeEnhancedRequest<unknown[]>({
      endpoint: "/api/extensions/",
      cacheKey: useCache ? "extensions-list" : undefined,
      enableCaching: useCache,
      serviceName: "extension-api",
      fallbackData: [],
    });
  }

  async getBackgroundTasks(useCache: boolean = true): Promise<unknown[]> {
    return this.makeEnhancedRequest<unknown[]>({
      endpoint: "/api/extensions/background-tasks/",
      cacheKey: useCache ? "background-tasks" : undefined,
      enableCaching: useCache,
      serviceName: "background-tasks",
      fallbackData: [],
    });
  }

  async getModelProviders(useCache: boolean = true): Promise<unknown[]> {
    return this.makeEnhancedRequest<unknown[]>({
      endpoint: "/api/models/providers/",
      cacheKey: useCache ? "model-providers" : undefined,
      enableCaching: useCache,
      serviceName: "model-provider",
      fallbackData: [],
    });
  }

  async getExtensionHealth(extensionName: string, useCache: boolean = true): Promise<unknown> {
    return this.makeEnhancedRequest<unknown>({
      endpoint: `/api/extensions/${extensionName}/health/`,
      cacheKey: useCache ? `extension-health-${extensionName}` : undefined,
      enableCaching: useCache,
      serviceName: "extension-health",
      fallbackData: { status: "unknown", message: "Health check unavailable" },
    });
  }

  /** ---------- Introspection & cache control ---------- */

  getServiceHealthStatus(): Record<string, ServiceHealthStatus> {
    return Object.fromEntries(this.serviceHealth);
  }

  refreshCache(cacheKey?: string): void {
    if (cacheKey) {
      extensionCache.delete(cacheKey);
    } else {
      extensionCache.clear();
    }
  }
}
