/**
 * Endpoint Configuration Validation Service
 * Provides comprehensive validation and health checking for backend endpoints
 */

import { getConfigManager, type EndpointValidationResult, type EndpointConfig } from './endpoint-config';

export interface ValidationError {
  field: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
}

export interface ConfigValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  info: ValidationError[];
}

export interface HealthCheckResult {
  endpoint: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  responseTime: number;
  timestamp: string;
  details: {
    services?: Record<string, any>;
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

/**
 * Configuration validation service for endpoint management
 */
export class EndpointValidationService {
  private configManager = getConfigManager();
  private healthCheckCache: Map<string, HealthCheckResult> = new Map();
  private connectivityCache: Map<string, ConnectivityTestResult> = new Map();
  private readonly HEALTH_CACHE_TTL = 30000; // 30 seconds
  private readonly CONNECTIVITY_CACHE_TTL = 60000; // 1 minute

  /**
   * Validate the current endpoint configuration
   */
  public validateConfiguration(): ConfigValidationResult {
    const config = this.configManager.getConfiguration();
    const errors: ValidationError[] = [];
    const warnings: ValidationError[] = [];
    const info: ValidationError[] = [];

    // Validate backend URL
    this.validateBackendUrl(config.backendUrl, errors, warnings);

    // Validate fallback URLs
    this.validateFallbackUrls(config.fallbackUrls, errors, warnings);

    // Validate health check configuration
    this.validateHealthCheckConfig(config, errors, warnings);

    // Validate CORS origins
    this.validateCorsOrigins(config.corsOrigins, errors, warnings);

    // Validate environment consistency
    this.validateEnvironmentConsistency(config, warnings, info);

    // Validate timeout values
    this.validateTimeoutValues(config, warnings);

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      info,
    };
  }

  /**
   * Validate backend URL format and accessibility
   */
  private validateBackendUrl(backendUrl: string, errors: ValidationError[], warnings: ValidationError[]): void {
    if (!backendUrl) {
      errors.push({
        field: 'backendUrl',
        message: 'Backend URL is required',
        severity: 'error',

      return;
    }

    try {
      const url = new URL(backendUrl);
      
      // Check protocol
      if (!['http:', 'https:'].includes(url.protocol)) {
        errors.push({
          field: 'backendUrl',
          message: `Invalid protocol: ${url.protocol}. Only HTTP and HTTPS are supported`,
          severity: 'error',

      }

      // Check for localhost in production
      if (this.configManager.getEnvironmentInfo().environment === 'production' && 
          (url.hostname === 'localhost' || url.hostname === '127.0.0.1')) {
        warnings.push({
          field: 'backendUrl',
          message: 'Using localhost in production environment may cause connectivity issues',
          severity: 'warning',

      }

      // Check for HTTP in production
      if (this.configManager.getEnvironmentInfo().environment === 'production' && 
          url.protocol === 'http:') {
        warnings.push({
          field: 'backendUrl',
          message: 'Using HTTP in production is not recommended for security reasons',
          severity: 'warning',

      }

      // Check port range
      if (url.port) {
        const port = parseInt(url.port, 10);
        if (port < 1 || port > 65535) {
          errors.push({
            field: 'backendUrl',
            message: `Invalid port number: ${port}. Must be between 1 and 65535`,
            severity: 'error',

        }
      }

    } catch (error) {
      errors.push({
        field: 'backendUrl',
        message: `Invalid URL format: ${backendUrl}`,
        severity: 'error',

    }
  }

  /**
   * Validate fallback URLs
   */
  private validateFallbackUrls(fallbackUrls: string[], errors: ValidationError[], warnings: ValidationError[]): void {
    if (fallbackUrls.length === 0) {
      warnings.push({
        field: 'fallbackUrls',
        message: 'No fallback URLs configured. Consider adding fallback endpoints for better reliability',
        severity: 'warning',

      return;
    }

    fallbackUrls.forEach((url, index) => {
      try {
        const parsedUrl = new URL(url);
        
        // Check protocol
        if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
          errors.push({
            field: `fallbackUrls[${index}]`,
            message: `Invalid protocol in fallback URL: ${parsedUrl.protocol}`,
            severity: 'error',

        }

      } catch (error) {
        errors.push({
          field: `fallbackUrls[${index}]`,
          message: `Invalid fallback URL format: ${url}`,
          severity: 'error',

      }

    // Check for duplicate URLs
    const uniqueUrls = new Set(fallbackUrls);
    if (uniqueUrls.size !== fallbackUrls.length) {
      warnings.push({
        field: 'fallbackUrls',
        message: 'Duplicate fallback URLs detected',
        severity: 'warning',

    }
  }

  /**
   * Validate health check configuration
   */
  private validateHealthCheckConfig(config: EndpointConfig, errors: ValidationError[], warnings: ValidationError[]): void {
    if (config.healthCheckEnabled) {
      // Validate interval
      if (config.healthCheckInterval < 5000) {
        warnings.push({
          field: 'healthCheckInterval',
          message: `Health check interval is very low (${config.healthCheckInterval}ms). This may impact performance`,
          severity: 'warning',

      }

      if (config.healthCheckInterval > 300000) { // 5 minutes
        warnings.push({
          field: 'healthCheckInterval',
          message: `Health check interval is very high (${config.healthCheckInterval}ms). Issues may not be detected quickly`,
          severity: 'warning',

      }

      // Validate timeout
      if (config.healthCheckTimeout < 1000) {
        warnings.push({
          field: 'healthCheckTimeout',
          message: `Health check timeout is very low (${config.healthCheckTimeout}ms). May cause false negatives`,
          severity: 'warning',

      }

      if (config.healthCheckTimeout >= config.healthCheckInterval) {
        errors.push({
          field: 'healthCheckTimeout',
          message: `Health check timeout (${config.healthCheckTimeout}ms) must be less than interval (${config.healthCheckInterval}ms)`,
          severity: 'error',

      }
    }
  }

  /**
   * Validate CORS origins
   */
  private validateCorsOrigins(corsOrigins: string[], errors: ValidationError[], warnings: ValidationError[]): void {
    if (corsOrigins.length === 0) {
      warnings.push({
        field: 'corsOrigins',
        message: 'No CORS origins configured. This may cause cross-origin request issues',
        severity: 'warning',

      return;
    }

    corsOrigins.forEach((origin, index) => {
      if (origin === '*') {
        warnings.push({
          field: `corsOrigins[${index}]`,
          message: 'Wildcard CORS origin (*) is not recommended for production',
          severity: 'warning',

        return;
      }

      try {
        new URL(origin);
      } catch (error) {
        errors.push({
          field: `corsOrigins[${index}]`,
          message: `Invalid CORS origin format: ${origin}`,
          severity: 'error',

      }

  }

  /**
   * Validate environment consistency
   */
  private validateEnvironmentConsistency(config: EndpointConfig, warnings: ValidationError[], info: ValidationError[]): void {
    const envInfo = this.configManager.getEnvironmentInfo();

    // Check for environment/URL mismatches
    if (envInfo.environment === 'docker' && !config.backendUrl.includes('docker') && 
        !config.backendUrl.includes('container') && !config.backendUrl.includes('backend')) {
      warnings.push({
        field: 'environment',
        message: 'Docker environment detected but backend URL does not appear to use container networking',
        severity: 'warning',

    }

    if (envInfo.networkMode === 'external' && 
        (config.backendUrl.includes('localhost') || config.backendUrl.includes('127.0.0.1'))) {
      warnings.push({
        field: 'networkMode',
        message: 'External network mode detected but backend URL uses localhost',
        severity: 'warning',

    }

    // Provide environment info
    info.push({
      field: 'environment',
      message: `Detected environment: ${envInfo.environment}, network mode: ${envInfo.networkMode}`,
      severity: 'info',

  }

  /**
   * Validate timeout values
   */
  private validateTimeoutValues(config: EndpointConfig, warnings: ValidationError[]): void {
    if (config.healthCheckTimeout > 30000) {
      warnings.push({
        field: 'healthCheckTimeout',
        message: `Health check timeout is very high (${config.healthCheckTimeout}ms). Consider reducing for better responsiveness`,
        severity: 'warning',

    }
  }

  /**
   * Perform comprehensive health check on an endpoint
   */
  public async performHealthCheck(endpoint: string): Promise<HealthCheckResult> {
    const cacheKey = `health:${endpoint}`;
    const cached = this.healthCheckCache.get(cacheKey);
    
    if (cached && Date.now() - new Date(cached.timestamp).getTime() < this.HEALTH_CACHE_TTL) {
      return cached;
    }

    const startTime = performance.now();
    const timestamp = new Date().toISOString();

    try {
      const healthUrl = `${endpoint}/health`;
      const config = this.configManager.getConfiguration();
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), config.healthCheckTimeout);

      const response = await fetch(healthUrl, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache',
        },

      clearTimeout(timeoutId);
      const responseTime = performance.now() - startTime;

      if (response.ok) {
        let healthData: any = {};
        try {
          healthData = await response.json();
        } catch {
          // If JSON parsing fails, treat as basic health check
          healthData = { status: 'ok' };
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

      } else {
        const result: HealthCheckResult = {
          endpoint,
          status: 'unhealthy',
          responseTime,
          timestamp,
          details: {
            error: `HTTP ${response.status}: ${response.statusText}`,
          },
        };

        this.healthCheckCache.set(cacheKey, result);
        return result;
      }

    } catch (error) {
      const responseTime = performance.now() - startTime;
      let errorMessage = 'Unknown error';

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = 'Health check timeout';
        } else if (error.message.includes('fetch')) {
          errorMessage = 'Network error - unable to connect';
        } else {
          errorMessage = error.message;
        }
      }

      const result: HealthCheckResult = {
        endpoint,
        status: 'unhealthy',
        responseTime,
        timestamp,
        details: {
          error: errorMessage,
        },
      };

      this.healthCheckCache.set(cacheKey, result);
      return result;
    }
  }

  /**
   * Determine health status based on response data and performance
   */
  private determineHealthStatus(healthData: any, responseTime: number): 'healthy' | 'degraded' | 'unhealthy' {
    // Check if response time is too high
    if (responseTime > 10000) { // 10 seconds
      return 'degraded';
    }

    // Check service status if available
    if (healthData.services) {
      const services = Object.values(healthData.services);
      const unhealthyServices = services.filter((service: any) => 
        service.status === 'error' || service.status === 'unhealthy'
      );
      
      if (unhealthyServices.length > 0) {
        return services.length === unhealthyServices.length ? 'unhealthy' : 'degraded';
      }
    }

    // Check overall status if provided
    if (healthData.status) {
      switch (healthData.status.toLowerCase()) {
        case 'ok':
        case 'healthy':
          return 'healthy';
        case 'degraded':
        case 'warning':
          return 'degraded';
        case 'error':
        case 'unhealthy':
          return 'unhealthy';
      }
    }

    return 'healthy';
  }

  /**
   * Test basic connectivity to an endpoint
   */
  public async testConnectivity(endpoint: string): Promise<ConnectivityTestResult> {
    const cacheKey = `connectivity:${endpoint}`;
    const cached = this.connectivityCache.get(cacheKey);
    
    if (cached && Date.now() - new Date(cached.timestamp).getTime() < this.CONNECTIVITY_CACHE_TTL) {
      return cached;
    }

    const startTime = performance.now();
    const timestamp = new Date().toISOString();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const response = await fetch(endpoint, {
        method: 'HEAD', // Use HEAD to minimize data transfer
        signal: controller.signal,
        mode: 'cors', // Test CORS

      clearTimeout(timeoutId);
      const responseTime = performance.now() - startTime;

      const result: ConnectivityTestResult = {
        endpoint,
        isReachable: true,
        responseTime,
        httpStatus: response.status,
        corsEnabled: response.headers.get('Access-Control-Allow-Origin') !== null,
        timestamp,
      };

      this.connectivityCache.set(cacheKey, result);
      return result;

    } catch (error) {
      const responseTime = performance.now() - startTime;
      let errorMessage = 'Unknown error';

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = 'Connection timeout';
        } else if (error.message.includes('CORS')) {
          errorMessage = 'CORS error - cross-origin requests blocked';
        } else if (error.message.includes('fetch')) {
          errorMessage = 'Network error - unable to connect';
        } else {
          errorMessage = error.message;
        }
      }

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
    primary: EndpointValidationResult;
    fallbacks: EndpointValidationResult[];
    healthChecks: HealthCheckResult[];
    connectivity: ConnectivityTestResult[];
  }> {
    const config = this.configManager.getConfiguration();
    const allEndpoints = [config.backendUrl, ...config.fallbackUrls];

    // Get basic validation results
    const validationResults = await this.configManager.validateEndpoints();
    
    // Perform health checks
    const healthChecks = await Promise.all(
      allEndpoints.map(endpoint => this.performHealthCheck(endpoint))
    );

    // Test connectivity
    const connectivity = await Promise.all(
      allEndpoints.map(endpoint => this.testConnectivity(endpoint))
    );

    return {
      primary: validationResults[0],
      fallbacks: validationResults.slice(1),
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

// Export types with unique names to avoid conflicts
export type {
};