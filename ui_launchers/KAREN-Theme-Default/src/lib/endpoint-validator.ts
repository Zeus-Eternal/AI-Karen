/**
 * Endpoint Configuration Validation Service
 * Provides comprehensive validation and health checking for backend endpoints
 */

import {
  getConfigManager,
  type EndpointValidationResult,
  type EndpointConfig,
} from "./endpoint-config";

export interface ValidationError {
  field: string;
  message: string;
  severity: "error" | "warning" | "info";
}

export interface ConfigValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  info: ValidationError[];
}

export interface HealthCheckResult {
  endpoint: string;
  status: "healthy" | "degraded" | "unhealthy";
  responseTime: number;
  timestamp: string;
  details: {
    services?: Record<string, HealthServiceStatus>;
    version?: string;
    uptime?: number;
    error?: string;
  };
}

export interface ConnectivityTestResult {
  endpoint: string;
  isReachable: boolean;
  responseTime?: number;
  httpStatus?: number;
  error?: string;
  corsEnabled?: boolean;
  timestamp: string;
}

type HealthServiceStatus = {
  status?: string;
} & Record<string, unknown>;

interface HealthEndpointData {
  status?: string;
  services?: Record<string, HealthServiceStatus>;
  version?: string;
  uptime?: number;
}

function safeNowISO(): string {
  try {
    return new Date().toISOString();
  } catch {
    // Extremely unlikely, but keep service fail-soft
    return "" + Date.now();
  }
}

function validHttpProtocol(protocol: string): boolean {
  return protocol === "http:" || protocol === "https:";
}

function tryParseUrl(u: string): URL | null {
  try {
    return new URL(u);
  } catch {
    return null;
  }
}

function perfNow(): number {
  try {
    return performance.now();
  } catch {
    return Date.now();
  }
}

export class EndpointValidationService {
  private configManager = getConfigManager();
  private healthCheckCache: Map<string, HealthCheckResult> = new Map();
  private connectivityCache: Map<string, ConnectivityTestResult> = new Map();
  private readonly HEALTH_CACHE_TTL = 30_000; // 30s
  private readonly CONNECTIVITY_CACHE_TTL = 60_000; // 60s

  private parseHealthEndpointData(rawData: unknown): HealthEndpointData {
    if (!rawData || typeof rawData !== "object") {
      return {};
    }

    const payload = rawData as Record<string, unknown>;
    const status = payload.status;
    const version = payload.version;
    const uptime = payload.uptime;

    return {
      status: typeof status === "string" ? status : undefined,
      services: this.parseHealthServices(payload["services"]),
      version: typeof version === "string" ? version : undefined,
      uptime: typeof uptime === "number" ? uptime : undefined,
    };
  }

  private parseHealthServices(
    services: unknown
  ): Record<string, HealthServiceStatus> | undefined {
    if (!services || typeof services !== "object") {
      return undefined;
    }

    const normalized: Record<string, HealthServiceStatus> = {};
    for (const [key, value] of Object.entries(
      services as Record<string, unknown>
    )) {
      normalized[key] = this.parseHealthServiceStatus(value);
    }
    return normalized;
  }

  private parseHealthServiceStatus(value: unknown): HealthServiceStatus {
    if (!value || typeof value !== "object") {
      return {};
    }

    const record = value as Record<string, unknown>;
    const status = record.status;

    return {
      ...record,
      status: typeof status === "string" ? status : undefined,
    } as HealthServiceStatus;
  }

  /**
   * Validate the current endpoint configuration
   */
  public validateConfiguration(): ConfigValidationResult {
    const config = this.configManager.getConfiguration();
    const errors: ValidationError[] = [];
    const warnings: ValidationError[] = [];
    const info: ValidationError[] = [];

    this.validateBackendUrl(config.backendUrl, errors, warnings);
    this.validateFallbackUrls(config.fallbackUrls ?? [], errors, warnings);
    this.validateHealthCheckConfig(config, errors, warnings);
    this.validateCorsOrigins(config.corsOrigins ?? [], errors, warnings);
    this.validateEnvironmentConsistency(config, warnings, info);
    this.validateTimeoutValues(config, warnings);

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      info,
    };
  }

  /**
   * Validate backend URL format and accessibility (format only here)
   */
  private validateBackendUrl(
    backendUrl: string,
    errors: ValidationError[],
    warnings: ValidationError[]
  ): void {
    if (!backendUrl) {
      errors.push({
        field: "backendUrl",
        message: "Backend URL is required",
        severity: "error",
      });
      return;
    }

    const url = tryParseUrl(backendUrl);
    if (!url) {
      errors.push({
        field: "backendUrl",
        message: `Invalid URL format: ${backendUrl}`,
        severity: "error",
      });
      return;
    }

    // Protocol
    if (!validHttpProtocol(url.protocol)) {
      errors.push({
        field: "backendUrl",
        message: `Invalid protocol: ${url.protocol}. Only HTTP and HTTPS are supported`,
        severity: "error",
      });
    }

    // Prod checks
    const env = this.configManager.getEnvironmentInfo().environment;
    if (
      env === "production" &&
      (url.hostname === "localhost" || url.hostname === "127.0.0.1")
    ) {
      warnings.push({
        field: "backendUrl",
        message:
          "Using localhost in production environment may cause connectivity issues",
        severity: "warning",
      });
    }
    if (env === "production" && url.protocol === "http:") {
      warnings.push({
        field: "backendUrl",
        message:
          "Using HTTP in production is not recommended for security reasons",
        severity: "warning",
      });
    }

    // Port range
    if (url.port) {
      const port = parseInt(url.port, 10);
      if (Number.isNaN(port) || port < 1 || port > 65_535) {
        errors.push({
          field: "backendUrl",
          message: `Invalid port number: ${url.port}. Must be between 1 and 65535`,
          severity: "error",
        });
      }
    }
  }

  /**
   * Validate fallback URLs
   */
  private validateFallbackUrls(
    fallbackUrls: string[],
    errors: ValidationError[],
    warnings: ValidationError[]
  ): void {
    if (!Array.isArray(fallbackUrls) || fallbackUrls.length === 0) {
      warnings.push({
        field: "fallbackUrls",
        message:
          "No fallback URLs configured. Consider adding fallback endpoints for better reliability",
        severity: "warning",
      });
      return;
    }

    fallbackUrls.forEach((u, index) => {
      const parsed = tryParseUrl(u);
      if (!parsed) {
        errors.push({
          field: `fallbackUrls[${index}]`,
          message: `Invalid fallback URL format: ${u}`,
          severity: "error",
        });
        return;
      }
      if (!validHttpProtocol(parsed.protocol)) {
        errors.push({
          field: `fallbackUrls[${index}]`,
          message: `Invalid protocol in fallback URL: ${parsed.protocol}`,
          severity: "error",
        });
      }
      if (parsed.port) {
        const p = parseInt(parsed.port, 10);
        if (Number.isNaN(p) || p < 1 || p > 65_535) {
          errors.push({
            field: `fallbackUrls[${index}]`,
            message: `Invalid port number: ${parsed.port}. Must be between 1 and 65535`,
            severity: "error",
          });
        }
      }
    });

    // Duplicate detection
    const unique = new Set(fallbackUrls);
    if (unique.size !== fallbackUrls.length) {
      warnings.push({
        field: "fallbackUrls",
        message: "Duplicate fallback URLs detected",
        severity: "warning",
      });
    }
  }

  /**
   * Validate health check configuration
   */
  private validateHealthCheckConfig(
    config: EndpointConfig,
    errors: ValidationError[],
    warnings: ValidationError[]
  ): void {
    if (!config.healthCheckEnabled) return;

    if (config.healthCheckInterval < 5_000) {
      warnings.push({
        field: "healthCheckInterval",
        message: `Health check interval is very low (${config.healthCheckInterval}ms). This may impact performance`,
        severity: "warning",
      });
    }

    if (config.healthCheckInterval > 300_000) {
      warnings.push({
        field: "healthCheckInterval",
        message: `Health check interval is very high (${config.healthCheckInterval}ms). Issues may not be detected quickly`,
        severity: "warning",
      });
    }

    if (config.healthCheckTimeout < 1_000) {
      warnings.push({
        field: "healthCheckTimeout",
        message: `Health check timeout is very low (${config.healthCheckTimeout}ms). May cause false negatives`,
        severity: "warning",
      });
    }

    if (config.healthCheckTimeout >= config.healthCheckInterval) {
      errors.push({
        field: "healthCheckTimeout",
        message: `Health check timeout (${config.healthCheckTimeout}ms) must be less than interval (${config.healthCheckInterval}ms)`,
        severity: "error",
      });
    }
  }

  /**
   * Validate CORS origins
   */
  private validateCorsOrigins(
    corsOrigins: string[],
    errors: ValidationError[],
    warnings: ValidationError[]
  ): void {
    if (!Array.isArray(corsOrigins) || corsOrigins.length === 0) {
      warnings.push({
        field: "corsOrigins",
        message:
          "No CORS origins configured. This may cause cross-origin request issues",
        severity: "warning",
      });
      return;
    }

    corsOrigins.forEach((origin, index) => {
      if (origin === "*") {
        warnings.push({
          field: `corsOrigins[${index}]`,
          message: "Wildcard CORS origin (*) is not recommended for production",
          severity: "warning",
        });
        return;
      }
      const parsed = tryParseUrl(origin);
      if (!parsed) {
        errors.push({
          field: `corsOrigins[${index}]`,
          message: `Invalid CORS origin format: ${origin}`,
          severity: "error",
        });
      }
    });
  }

  /**
   * Validate environment consistency
   */
  private validateEnvironmentConsistency(
    config: EndpointConfig,
    warnings: ValidationError[],
    info: ValidationError[]
  ): void {
    const envInfo = this.configManager.getEnvironmentInfo();

    if (
      envInfo.environment === "docker" &&
      !config.backendUrl.includes("docker") &&
      !config.backendUrl.includes("container") &&
      !config.backendUrl.includes("backend")
    ) {
      warnings.push({
        field: "environment",
        message:
          "Docker environment detected but backend URL may not use container networking",
        severity: "warning",
      });
    }

    if (
      envInfo.networkMode === "external" &&
      (config.backendUrl.includes("localhost") ||
        config.backendUrl.includes("127.0.0.1"))
    ) {
      warnings.push({
        field: "networkMode",
        message:
          "External network mode detected but backend URL uses localhost",
        severity: "warning",
      });
    }

    info.push({
      field: "environment",
      message: `Detected environment: ${envInfo.environment}, network mode: ${envInfo.networkMode}`,
      severity: "info",
    });
  }

  /**
   * Validate timeout values
   */
  private validateTimeoutValues(
    config: EndpointConfig,
    warnings: ValidationError[]
  ): void {
    if (config.healthCheckTimeout > 30_000) {
      warnings.push({
        field: "healthCheckTimeout",
        message: `Health check timeout is very high (${config.healthCheckTimeout}ms). Consider reducing for better responsiveness`,
        severity: "warning",
      });
    }
  }

  /**
   * Perform comprehensive health check on an endpoint
   */
  public async performHealthCheck(
    endpoint: string
  ): Promise<HealthCheckResult> {
    const cacheKey = `health:${endpoint}`;
    const cached = this.healthCheckCache.get(cacheKey);
    if (
      cached &&
      Date.now() - new Date(cached.timestamp).getTime() < this.HEALTH_CACHE_TTL
    ) {
      return cached;
    }

    const startTime = perfNow();
    const timestamp = safeNowISO();

    try {
      const healthUrl = endpoint.replace(/\/+$/, "") + "/health";
      const config = this.configManager.getConfiguration();
      const controller = new AbortController();
      const timeoutId = setTimeout(
        () => controller.abort(),
        Math.max(1_000, config.healthCheckTimeout)
      );

      const response = await fetch(healthUrl, {
        method: "GET",
        signal: controller.signal,
        headers: {
          Accept: "application/json",
          "Cache-Control": "no-cache",
        },
        credentials: "same-origin",
      });

      clearTimeout(timeoutId);
      const responseTime = Math.max(0, perfNow() - startTime);

      if (response.ok) {
        let healthData: HealthEndpointData = {};
        try {
          const rawData = await response.json();
          healthData = this.parseHealthEndpointData(rawData);
        } catch {
          healthData = { status: "ok" };
        }

        const result: HealthCheckResult = {
          endpoint,
          status: this.determineHealthStatus(healthData, responseTime),
          responseTime,
          timestamp,
          details: {
            services: healthData.services,
            version: healthData.version,
            uptime: healthData.uptime,
          },
        };

        this.healthCheckCache.set(cacheKey, result);
        return result;
      }

      const result: HealthCheckResult = {
        endpoint,
        status: "unhealthy",
        responseTime,
        timestamp,
        details: {
          error: `HTTP ${response.status}: ${response.statusText}`,
        },
      };
      this.healthCheckCache.set(cacheKey, result);
      return result;
    } catch (error: unknown) {
      const err = error as Error;
      const responseTime = Math.max(0, perfNow() - startTime);
      let errorMessage = "Unknown error";

      if (err?.name === "AbortError") {
        errorMessage = "Health check timeout";
      } else if (typeof err?.message === "string") {
        if (err.message.toLowerCase().includes("fetch")) {
          errorMessage = "Network error - unable to connect";
        } else {
          errorMessage = err.message;
        }
      }

      const result: HealthCheckResult = {
        endpoint,
        status: "unhealthy",
        responseTime,
        timestamp,
        details: { error: errorMessage },
      };
      this.healthCheckCache.set(cacheKey, result);
      return result;
    }
  }

  /**
   * Determine health status based on response data and performance
   */
  private determineHealthStatus(
    healthData: HealthEndpointData,
    responseTime: number
  ): "healthy" | "degraded" | "unhealthy" {
    // Latency heuristic
    if (responseTime > 10_000) return "degraded";

    // Service map heuristic
    if (healthData?.services) {
      const services = Object.values(healthData.services);
      const unhealthy = services.filter(
        (s) => s?.status === "error" || s?.status === "unhealthy"
      );
      if (unhealthy.length > 0) {
        return unhealthy.length === services.length ? "unhealthy" : "degraded";
      }
    }

    // Explicit status
    if (typeof healthData?.status === "string") {
      const s = healthData.status.toLowerCase();
      if (s === "ok" || s === "healthy") return "healthy";
      if (s === "degraded" || s === "warning") return "degraded";
      if (s === "error" || s === "unhealthy") return "unhealthy";
    }

    return "healthy";
  }

  /**
   * Test basic connectivity to an endpoint
   */
  public async testConnectivity(
    endpoint: string
  ): Promise<ConnectivityTestResult> {
    const cacheKey = `connectivity:${endpoint}`;
    const cached = this.connectivityCache.get(cacheKey);
    if (
      cached &&
      Date.now() - new Date(cached.timestamp).getTime() <
        this.CONNECTIVITY_CACHE_TTL
    ) {
      return cached;
    }

    const startTime = perfNow();
    const timestamp = safeNowISO();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10_000);

      const response = await fetch(endpoint, {
        method: "HEAD",
        signal: controller.signal,
        mode: "cors",
        credentials: "same-origin",
      });

      clearTimeout(timeoutId);
      const responseTime = Math.max(0, perfNow() - startTime);

      const result: ConnectivityTestResult = {
        endpoint,
        isReachable: true,
        responseTime,
        httpStatus: response.status,
        corsEnabled:
          response.headers.get("Access-Control-Allow-Origin") !== null,
        timestamp,
      };

      this.connectivityCache.set(cacheKey, result);
      return result;
    } catch (error: unknown) {
      const err = error as Error;
      const responseTime = Math.max(0, perfNow() - startTime);

      let errorMessage = "Unknown error";
      const msg = String(err?.message || "");
      if (err?.name === "AbortError") errorMessage = "Connection timeout";
      else if (msg.toLowerCase().includes("cors"))
        errorMessage = "CORS error - cross-origin requests blocked";
      else if (msg.toLowerCase().includes("fetch"))
        errorMessage = "Network error - unable to connect";
      else if (msg) errorMessage = msg;

      const result: ConnectivityTestResult = {
        endpoint,
        isReachable: false,
        responseTime,
        error: errorMessage,
        timestamp,
      };

      this.connectivityCache.set(cacheKey, result);
      return result;
    }
  }

  /**
   * Validate all configured endpoints
   */
  public async validateAllEndpoints(): Promise<{
    primary: EndpointValidationResult | null;
    fallbacks: EndpointValidationResult[];
    healthChecks: HealthCheckResult[];
    connectivity: ConnectivityTestResult[];
  }> {
    const config = this.configManager.getConfiguration();
    const allEndpoints = [config.backendUrl, ...(config.fallbackUrls ?? [])];

    // Basic validation results from config manager
    const validationResults = await this.configManager.validateEndpoints();

    const healthChecks = await Promise.all(
      allEndpoints.map((endpoint) => this.performHealthCheck(endpoint))
    );

    const connectivity = await Promise.all(
      allEndpoints.map((endpoint) => this.testConnectivity(endpoint))
    );

    const primary = validationResults.length > 0 ? validationResults[0] : null;
    const fallbacks =
      validationResults.length > 1 ? validationResults.slice(1) : [];

    return {
      primary,
      fallbacks,
      healthChecks,
      connectivity,
    };
  }

  /**
   * Clear all caches
   */
  public clearCaches(): void {
    this.healthCheckCache.clear();
    this.connectivityCache.clear();
    this.configManager.clearValidationCache();
  }

  /**
   * Get cache statistics
   */
  public getCacheStats(): {
    healthCheck: { size: number; keys: string[] };
    connectivity: { size: number; keys: string[] };
    validation: { size: number; keys: string[] };
  } {
    return {
      healthCheck: {
        size: this.healthCheckCache.size,
        keys: Array.from(this.healthCheckCache.keys()),
      },
      connectivity: {
        size: this.connectivityCache.size,
        keys: Array.from(this.connectivityCache.keys()),
      },
      validation: this.configManager.getValidationCacheStats(),
    };
  }
}

// Singleton instance
let validationService: EndpointValidationService | null = null;

/**
 * Get the global endpoint validation service instance
 */
export function getEndpointValidationService(): EndpointValidationService {
  if (!validationService) {
    validationService = new EndpointValidationService();
  }
  return validationService;
}

/**
 * Initialize endpoint validation service
 */
export function initializeEndpointValidationService(): EndpointValidationService {
  validationService = new EndpointValidationService();
  return validationService;
}

// Re-export types (keep explicit; avoid empty export blocks that break TS)
export type {
  ConfigValidationResult as EndpointConfigValidationResult,
  HealthCheckResult as EndpointHealthCheckResult,
  ConnectivityTestResult as EndpointConnectivityTestResult,
  ValidationError as EndpointValidationError,
};
