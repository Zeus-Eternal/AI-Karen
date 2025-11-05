/**
 * Environment Configuration Manager
 * 
 * Centralized configuration management for backend URLs and timeouts
 * with automatic environment detection (Docker vs local development)
 * and comprehensive validation logic.
 * 
 * Requirements: 1.1, 1.2
 */
export interface BackendConfig {
  primaryUrl: string;
  fallbackUrls: string[];
  timeout: number;
  retryAttempts: number;
  healthCheckInterval: number;
}
export interface TimeoutConfiguration {
  connection: number;
  authentication: number;
  sessionValidation: number;
  healthCheck: number;
}
export interface RetryPolicy {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  exponentialBase: number;
  jitterEnabled: boolean;
}
export interface EnvironmentInfo {
  type: 'local' | 'docker' | 'production';
  networkMode: 'localhost' | 'container' | 'external';
  isDocker: boolean;
  isProduction: boolean;
  detectedHostname?: string;
  detectedPort?: string;
}
export interface ValidationResult {
  isValid: boolean;
  warnings: string[];
  errors: string[];
  environment: EnvironmentInfo;
  config: BackendConfig;
}
/**
 * Environment Configuration Manager
 * 
 * Provides centralized configuration management with automatic environment detection,
 * validation, and fallback URL generation for reliable backend connectivity.
 */
export class EnvironmentConfigManager {
  private config: BackendConfig;
  private timeouts: TimeoutConfiguration;
  private retryPolicy: RetryPolicy;
  private environment: EnvironmentInfo;
  private validationCache: Map<string, { result: ValidationResult; timestamp: number }> = new Map();
  private readonly VALIDATION_CACHE_TTL = 60000; // 1 minute
  constructor() {
    this.environment = this.detectEnvironment();
    this.config = this.loadBackendConfiguration();
    this.timeouts = this.loadTimeoutConfiguration();
    this.retryPolicy = this.loadRetryPolicy();
    // Log configuration for debugging
    this.logConfiguration();
  }
  /**
   * Detect the current environment and network mode
   */
  private detectEnvironment(): EnvironmentInfo {
    const nodeEnv = this.getEnvVar('NODE_ENV', 'development');
    const karenEnv = this.getEnvVar('KAREN_ENVIRONMENT', '');
    const dockerContainer = this.getEnvVar('DOCKER_CONTAINER', '');
    const hostname = this.getEnvVar('HOSTNAME', '');
    const containerMode = this.getEnvVar('KAREN_CONTAINER_MODE', '');
    // Detect if running in Docker
    const isDocker = !!(
      dockerContainer ||
      containerMode === 'true' ||
      hostname.includes('docker') ||
      hostname.includes('container') ||
      (typeof process !== 'undefined' && process.env.DOCKER_CONTAINER)
    );
    // Detect if production environment
    const isProduction = nodeEnv === 'production' || karenEnv === 'production';
    // Determine environment type
    let type: 'local' | 'docker' | 'production';
    if (isProduction) {
      type = 'production';
    } else if (isDocker) {
      type = 'docker';
    } else {
      type = 'local';
    }
    // Determine network mode
    let networkMode: 'localhost' | 'container' | 'external';
    if (isDocker) {
      networkMode = 'container';
    } else if (this.isExternalAccess()) {
      networkMode = 'external';
    } else {
      networkMode = 'localhost';
    }
    // Detect hostname and port from current environment
    let detectedHostname: string | undefined;
    let detectedPort: string | undefined;
    if (typeof window !== 'undefined') {
      detectedHostname = window.location.hostname;
      detectedPort = window.location.port;
    }
    return {
      type,
      networkMode,
      isDocker,
      isProduction,
      detectedHostname,
      detectedPort,
    };
  }
  /**
   * Check if accessing via external IP or hostname
   */
  private isExternalAccess(): boolean {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      // Check if hostname is localhost or 127.0.0.1
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return false;
      }
      // Check for IP address patterns
      if (hostname.match(/^\d+\.\d+\.\d+\.\d+$/)) {
        return true;
      }
      // Check for non-localhost hostnames
      return hostname !== 'localhost' && hostname !== '127.0.0.1';
    }
    return false;
  }
  /**
   * Load backend configuration based on environment
   */
  private loadBackendConfiguration(): BackendConfig {
    const primaryUrl = this.determinePrimaryUrl();
    const fallbackUrls = this.generateFallbackUrls(primaryUrl);
    const timeout = this.getNumberEnv('AUTH_TIMEOUT_MS', 45000); // Increased from 15s to 45s
    const retryAttempts = this.getNumberEnv('MAX_RETRY_ATTEMPTS', 3);
    const healthCheckInterval = this.getNumberEnv('HEALTH_CHECK_INTERVAL_MS', 30000);
    return {
      primaryUrl,
      fallbackUrls,
      timeout,
      retryAttempts,
      healthCheckInterval,
    };
  }
  /**
   * Determine the primary backend URL based on environment
   */
  private determinePrimaryUrl(): string {
    // Determine if we're running server-side (Node.js) or client-side (browser)
    const isServerSide = typeof window === 'undefined';
    // Standardized environment variable lookup with priority order
    // Server-side: prioritize KAREN_BACKEND_URL, Client-side: prioritize NEXT_PUBLIC_KAREN_BACKEND_URL
    const standardizedUrls = isServerSide ? [
      this.getEnvVar('KAREN_BACKEND_URL', ''),
      this.getEnvVar('NEXT_PUBLIC_KAREN_BACKEND_URL', ''),
    ].filter(Boolean) : [
      this.getEnvVar('NEXT_PUBLIC_KAREN_BACKEND_URL', ''),
      this.getEnvVar('KAREN_BACKEND_URL', ''),
    ].filter(Boolean);
    // Legacy environment variables for backward compatibility (deprecated)
    const legacyUrls = [
      this.getEnvVar('API_BASE_URL', ''),
      this.getEnvVar('NEXT_PUBLIC_API_BASE_URL', ''),
    ].filter(Boolean);
    // Log deprecation warnings for legacy variables
    if (legacyUrls.length > 0) {
      if (this.getEnvVar('API_BASE_URL', '')) {
      }
      if (this.getEnvVar('NEXT_PUBLIC_API_BASE_URL', '')) {
      }
    }
    // Use standardized variables first, then fall back to legacy
    const allUrls = [...standardizedUrls, ...legacyUrls];
    if (allUrls.length > 0) {
      return this.normalizeUrl(allUrls[0]);
    }
    // Generate URL based on detected environment
    switch (this.environment.networkMode) {
      case 'container':
        const containerHost = this.getEnvVar('KAREN_CONTAINER_BACKEND_HOST', 'backend');
        const containerPort = this.getEnvVar('KAREN_CONTAINER_BACKEND_PORT', '8000');
        return `http://${containerHost}:${containerPort}`;
      case 'external':
        const externalHost = this.getEnvVar('KAREN_EXTERNAL_HOST', this.environment.detectedHostname || 'localhost');
        const externalPort = this.getEnvVar('KAREN_EXTERNAL_BACKEND_PORT', '8000');
        return `http://${externalHost}:${externalPort}`;
      case 'localhost':
      default:
        return 'http://localhost:8000';
    }
  }
  /**
   * Generate fallback URLs based on primary URL and environment
   */
  private generateFallbackUrls(primaryUrl: string): string[] {
    const fallbacks: string[] = [];
    // Check for explicit fallback URLs
    const explicitFallbacks = this.getEnvVar('KAREN_FALLBACK_BACKEND_URLS', '');
    if (explicitFallbacks) {
      const urls = explicitFallbacks.split(',').map(url => this.normalizeUrl(url.trim())).filter(Boolean);
      fallbacks.push(...urls);
    }
    try {
      const primaryUrlObj = new URL(primaryUrl);
      const port = primaryUrlObj.port || '8000';
      // Add localhost variations if not already localhost
      if (primaryUrlObj.hostname !== 'localhost') {
        fallbacks.push(`http://localhost:${port}`);
      }
      // Add 127.0.0.1 variation
      if (primaryUrlObj.hostname !== '127.0.0.1') {
        fallbacks.push(`http://127.0.0.1:${port}`);
      }
      // Add container networking fallback for Docker environments
      if (this.environment.isDocker && !primaryUrlObj.hostname.includes('api') && !primaryUrlObj.hostname.includes('backend')) {
        fallbacks.push(`http://api:${port}`); // Primary Docker service name
        fallbacks.push(`http://ai-karen-api:${port}`);
        fallbacks.push(`http://backend:${port}`);
      }
      // Add host.docker.internal for Docker Desktop
      if (this.environment.isDocker) {
        fallbacks.push(`http://host.docker.internal:${port}`);
      }
      // Add high availability fallback URLs for production
      if (this.environment.isProduction) {
        const haUrls = this.getEnvVar('KAREN_HA_BACKEND_URLS', '');
        if (haUrls) {
          const urls = haUrls.split(',').map(url => this.normalizeUrl(url.trim())).filter(Boolean);
          fallbacks.push(...urls);
        }
      }
    } catch (error) {
      // If URL parsing fails, add sensible defaults
      fallbacks.push('http://localhost:8000', 'http://127.0.0.1:8000');
    }
    // Remove duplicates and the primary URL
    return Array.from(new Set(fallbacks)).filter(url => url !== primaryUrl);
  }
  /**
   * Load timeout configuration
   */
  private loadTimeoutConfiguration(): TimeoutConfiguration {
    return {
      connection: this.getNumberEnv('CONNECTION_TIMEOUT_MS', 30000),
      authentication: this.getNumberEnv('AUTH_TIMEOUT_MS', 45000), // Increased from 15s
      sessionValidation: this.getNumberEnv('SESSION_VALIDATION_TIMEOUT_MS', 30000),
      healthCheck: this.getNumberEnv('HEALTH_CHECK_TIMEOUT_MS', 10000),
    };
  }
  /**
   * Load retry policy configuration
   */
  private loadRetryPolicy(): RetryPolicy {
    return {
      maxAttempts: this.getNumberEnv('MAX_RETRY_ATTEMPTS', 3),
      baseDelay: this.getNumberEnv('RETRY_BASE_DELAY_MS', 1000),
      maxDelay: this.getNumberEnv('RETRY_MAX_DELAY_MS', 10000),
      exponentialBase: this.getNumberEnv('RETRY_EXPONENTIAL_BASE', 2),
      jitterEnabled: this.getBooleanEnv('ENABLE_EXPONENTIAL_BACKOFF', true),
    };
  }
  /**
   * Get environment variable with fallback
   */
  private getEnvVar(key: string, defaultValue: string): string {
    if (typeof process !== 'undefined' && process.env) {
      return process.env[key] || defaultValue;
    }
    return defaultValue;
  }
  /**
   * Get boolean environment variable
   */
  private getBooleanEnv(key: string, defaultValue: boolean): boolean {
    const value = this.getEnvVar(key, '');
    if (!value) return defaultValue;
    return value.toLowerCase() === 'true';
  }
  /**
   * Get number environment variable
   */
  private getNumberEnv(key: string, defaultValue: number): number {
    const value = this.getEnvVar(key, '');
    if (!value) return defaultValue;
    const parsed = parseInt(value, 10);
    return isNaN(parsed) ? defaultValue : parsed;
  }
  /**
   * Normalize URL by removing trailing slashes
   */
  private normalizeUrl(url: string): string {
    return url.replace(/\/+$/, '');
  }
  /**
   * Validate the current configuration
   */
  public validateConfiguration(): ValidationResult {
    const cacheKey = 'config-validation';
    const cached = this.validationCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.VALIDATION_CACHE_TTL) {
      return cached.result;
    }
    const warnings: string[] = [];
    const errors: string[] = [];
    // Validate primary URL
    try {
      new URL(this.config.primaryUrl);
    } catch {
      errors.push(`Invalid primary backend URL: ${this.config.primaryUrl}`);
    }
    // Validate fallback URLs
    this.config.fallbackUrls.forEach((url, index) => {
      try {
        new URL(url);
      } catch {
        errors.push(`Invalid fallback URL[${index}]: ${url}`);
      }
    });

    // Validate timeout values
    if (this.timeouts.authentication < 1000) {
      warnings.push(`Authentication timeout is very low (${this.timeouts.authentication}ms), consider increasing it`);
    }
    if (this.timeouts.authentication > 120000) {
      warnings.push(`Authentication timeout is very high (${this.timeouts.authentication}ms), consider reducing it`);
    }
    // Validate retry configuration
    if (this.retryPolicy.maxAttempts > 10) {
      warnings.push(`Max retry attempts is very high (${this.retryPolicy.maxAttempts}), this may cause long delays`);
    }
    if (this.retryPolicy.baseDelay < 100) {
      warnings.push(`Retry base delay is very low (${this.retryPolicy.baseDelay}ms), this may overwhelm the server`);
    }
    // Environment-specific validations
    if (this.environment.type === 'docker' && this.environment.networkMode === 'localhost') {
      warnings.push('Docker environment with localhost network mode may cause connectivity issues');
    }
    // Check if Docker environment is using localhost URL (regardless of detected network mode)
    if (this.environment.isDocker && this.config.primaryUrl.includes('localhost')) {
      warnings.push('Docker environment with localhost network mode may cause connectivity issues');
    }
    if (this.environment.networkMode === 'external' && !this.getEnvVar('KAREN_EXTERNAL_HOST', '')) {
      warnings.push('External network mode detected but no external host configured');
    }
    // Validate environment variable consistency
    const karenBackendUrl = this.getEnvVar('KAREN_BACKEND_URL', '');
    const nextPublicKarenBackendUrl = this.getEnvVar('NEXT_PUBLIC_KAREN_BACKEND_URL', '');
    const legacyApiBaseUrl = this.getEnvVar('API_BASE_URL', '');
    const legacyNextPublicApiBaseUrl = this.getEnvVar('NEXT_PUBLIC_API_BASE_URL', '');
    // Check for conflicting environment variables
    if (karenBackendUrl && legacyApiBaseUrl && karenBackendUrl !== legacyApiBaseUrl) {
      warnings.push('Conflicting backend URLs: KAREN_BACKEND_URL and API_BASE_URL have different values');
    }
    if (nextPublicKarenBackendUrl && legacyNextPublicApiBaseUrl && nextPublicKarenBackendUrl !== legacyNextPublicApiBaseUrl) {
      warnings.push('Conflicting public backend URLs: NEXT_PUBLIC_KAREN_BACKEND_URL and NEXT_PUBLIC_API_BASE_URL have different values');
    }
    // Check for missing standardized variables when legacy ones are present
    if (legacyApiBaseUrl && !karenBackendUrl) {
      warnings.push('Using deprecated API_BASE_URL. Please migrate to KAREN_BACKEND_URL');
    }
    if (legacyNextPublicApiBaseUrl && !nextPublicKarenBackendUrl) {
      warnings.push('Using deprecated NEXT_PUBLIC_API_BASE_URL. Please migrate to NEXT_PUBLIC_KAREN_BACKEND_URL');
    }
    // Validate fallback URL configuration
    const fallbackUrls = this.getEnvVar('KAREN_FALLBACK_BACKEND_URLS', '');
    if (fallbackUrls) {
      const urls = fallbackUrls.split(',');
      if (urls.length > 10) {
        warnings.push('Too many fallback URLs configured (>10), this may impact performance');
      }
    }
    // High availability configuration validation
    if (this.environment.isProduction) {
      const haUrls = this.getEnvVar('KAREN_HA_BACKEND_URLS', '');
      const explicitFallbacks = this.getEnvVar('KAREN_FALLBACK_BACKEND_URLS', '');
      // Check if there are any explicitly configured high availability URLs
      if (!haUrls && !explicitFallbacks) {
        warnings.push('Production environment without high availability fallback URLs configured');
      }
    }
    const result: ValidationResult = {
      isValid: errors.length === 0,
      warnings,
      errors,
      environment: this.environment,
      config: this.config,
    };
    // Cache the result
    this.validationCache.set(cacheKey, {
      result,
      timestamp: Date.now(),
    });

    return result;
  }
  /**
   * Get the backend configuration
   */
  public getBackendConfig(): BackendConfig {
    return { ...this.config };
  }
  /**
   * Get timeout configuration
   */
  public getTimeoutConfig(): TimeoutConfiguration {
    return { ...this.timeouts };
  }
  /**
   * Get retry policy
   */
  public getRetryPolicy(): RetryPolicy {
    return { ...this.retryPolicy };
  }
  /**
   * Get environment information
   */
  public getEnvironmentInfo(): EnvironmentInfo {
    return { ...this.environment };
  }
  /**
   * Get health check URL
   */
  public getHealthCheckUrl(): string {
    return `${this.config.primaryUrl}/api/health`;
  }
  /**
   * Get all candidate URLs (primary + fallbacks)
   */
  public getAllCandidateUrls(): string[] {
    return [this.config.primaryUrl, ...this.config.fallbackUrls];
  }
  /**
   * Update configuration (for runtime changes)
   */
  public updateConfiguration(updates: Partial<BackendConfig>): void {
    this.config = { ...this.config, ...updates };
    this.validationCache.clear();
  }
  /**
   * Clear validation cache
   */
  public clearValidationCache(): void {
    this.validationCache.clear();
  }
  /**
   * Get standardized environment variable mapping
   */
  public getEnvironmentVariableMapping(): Record<string, { current: string; standardized: string; deprecated?: string }> {
    return {
      'Backend URL (Server-side)': {
        current: this.getEnvVar('KAREN_BACKEND_URL', '') || this.getEnvVar('API_BASE_URL', ''),
        standardized: 'KAREN_BACKEND_URL',
        deprecated: this.getEnvVar('API_BASE_URL', '') ? 'API_BASE_URL' : undefined,
      },
      'Backend URL (Client-side)': {
        current: this.getEnvVar('NEXT_PUBLIC_KAREN_BACKEND_URL', '') || this.getEnvVar('NEXT_PUBLIC_API_BASE_URL', ''),
        standardized: 'NEXT_PUBLIC_KAREN_BACKEND_URL',
        deprecated: this.getEnvVar('NEXT_PUBLIC_API_BASE_URL', '') ? 'NEXT_PUBLIC_API_BASE_URL' : undefined,
      },
      'Fallback URLs': {
        current: this.getEnvVar('KAREN_FALLBACK_BACKEND_URLS', ''),
        standardized: 'KAREN_FALLBACK_BACKEND_URLS',
      },
      'High Availability URLs': {
        current: this.getEnvVar('KAREN_HA_BACKEND_URLS', ''),
        standardized: 'KAREN_HA_BACKEND_URLS',
      },
      'Container Backend Host': {
        current: this.getEnvVar('KAREN_CONTAINER_BACKEND_HOST', 'backend'),
        standardized: 'KAREN_CONTAINER_BACKEND_HOST',
      },
      'Container Backend Port': {
        current: this.getEnvVar('KAREN_CONTAINER_BACKEND_PORT', '8000'),
        standardized: 'KAREN_CONTAINER_BACKEND_PORT',
      },
      'External Host': {
        current: this.getEnvVar('KAREN_EXTERNAL_HOST', ''),
        standardized: 'KAREN_EXTERNAL_HOST',
      },
      'External Backend Port': {
        current: this.getEnvVar('KAREN_EXTERNAL_BACKEND_PORT', '8000'),
        standardized: 'KAREN_EXTERNAL_BACKEND_PORT',
      },
    };
  }
  /**
   * Get migration recommendations for deprecated environment variables
   */
  public getMigrationRecommendations(): Array<{ from: string; to: string; action: string }> {
    const recommendations: Array<{ from: string; to: string; action: string }> = [];
    if (this.getEnvVar('API_BASE_URL', '')) {
      recommendations.push({
        from: 'API_BASE_URL',
        to: 'KAREN_BACKEND_URL',
        action: 'Rename environment variable for server-side backend URL',

    }
    if (this.getEnvVar('NEXT_PUBLIC_API_BASE_URL', '')) {
      recommendations.push({
        from: 'NEXT_PUBLIC_API_BASE_URL',
        to: 'NEXT_PUBLIC_KAREN_BACKEND_URL',
        action: 'Rename environment variable for client-side backend URL',

    }
    if (this.getEnvVar('BACKEND_PORT', '')) {
      recommendations.push({
        from: 'BACKEND_PORT',
        to: 'KAREN_BACKEND_PORT',
        action: 'Rename environment variable for backend port (optional, defaults to 8000)',

    }
    return recommendations;
  }
  /**
   * Log configuration information for debugging
   */
  private logConfiguration(): void {
    const debugLogging = this.getBooleanEnv('KAREN_DEBUG_LOGGING', false);
    if (!debugLogging) return;
    console.group('🔧 Environment Configuration Manager');
    // Log environment variable mapping
    console.log('Environment Variable Mapping:', this.getEnvironmentVariableMapping());
    // Log migration recommendations
    const migrations = this.getMigrationRecommendations();
    if (migrations.length > 0) {
    }
    console.groupEnd();
    // Validate and show warnings/errors
    const validation = this.validateConfiguration();
    if (validation.warnings.length > 0) {
      console.group('⚠️ Configuration Warnings');
      validation.warnings.forEach(warning => console.warn(warning));
      console.groupEnd();
    }
    if (validation.errors.length > 0) {
      console.group('❌ Configuration Errors');
      validation.errors.forEach(error => console.error(error));
      console.groupEnd();
    }
  }
}
// Singleton instance
let environmentConfigManager: EnvironmentConfigManager | null = null;
/**
 * Get the global environment configuration manager instance
 */
export function getEnvironmentConfigManager(): EnvironmentConfigManager {
  if (!environmentConfigManager) {
    environmentConfigManager = new EnvironmentConfigManager();
  }
  return environmentConfigManager;
}
/**
 * Initialize environment configuration manager
 */
export function initializeEnvironmentConfigManager(): EnvironmentConfigManager {
  environmentConfigManager = new EnvironmentConfigManager();
  return environmentConfigManager;
}
// Export types
export type {
};
