/**
 * Centralized Endpoint Configuration Manager
 * Provides consistent backend endpoint configuration across all Web UI components
 */

export type NetworkMode = 'localhost' | 'container' | 'external';
export type Environment = 'local' | 'docker' | 'production';

export interface EndpointConfig {
  backendUrl: string;
  environment: Environment;
  networkMode: NetworkMode;
  fallbackUrls: string[];
  healthCheckEnabled: boolean;
  healthCheckInterval: number;
  healthCheckTimeout: number;
  corsOrigins: string[];
}

export interface EndpointValidationResult {
  isValid: boolean;
  endpoint: string;
  responseTime?: number;
  error?: string;
  timestamp: string;
}

/**
 * Centralized configuration manager for backend endpoints
 * Handles environment detection, endpoint validation, and fallback logic
 */
export class ConfigManager {
  private config: EndpointConfig;
  private validationCache: Map<string, EndpointValidationResult> = new Map();
  private readonly CACHE_TTL = 60000; // 1 minute cache for validation results

  constructor() {
    this.config = this.loadConfiguration();
    this.detectEnvironment();
  }

  /**
   * Load configuration from environment variables with defaults
   */
  private loadConfiguration(): EndpointConfig {
    // Parse environment variables
    const backendUrl = this.getEnvVar('KAREN_BACKEND_URL', 'http://localhost:8000');
    const environment = this.getEnvVar('KAREN_ENVIRONMENT', 'local') as Environment;
    const networkMode = this.getEnvVar('KAREN_NETWORK_MODE', 'localhost') as NetworkMode;
    
    // Parse fallback URLs
    const fallbackUrlsStr = this.getEnvVar('KAREN_FALLBACK_BACKEND_URLS', '');
    const fallbackUrls = fallbackUrlsStr 
      ? fallbackUrlsStr.split(',').map(url => url.trim()).filter(Boolean)
      : this.getDefaultFallbackUrls(backendUrl);

    // Parse CORS origins
    const corsOriginsStr = this.getEnvVar('KAREN_CORS_ORIGINS', 'http://localhost:9002');
    const corsOrigins = corsOriginsStr.split(',').map(origin => origin.trim()).filter(Boolean);

    return {
      backendUrl,
      environment,
      networkMode,
      fallbackUrls,
      healthCheckEnabled: this.getBooleanEnv('KAREN_HEALTH_CHECK_ENABLED', true),
      healthCheckInterval: this.getNumberEnv('KAREN_HEALTH_CHECK_INTERVAL', 30000),
      healthCheckTimeout: this.getNumberEnv('KAREN_HEALTH_CHECK_TIMEOUT', 5000),
      corsOrigins,
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
   * Parse boolean environment variable
   */
  private getBooleanEnv(key: string, defaultValue: boolean): boolean {
    const value = this.getEnvVar(key, '');
    if (!value) return defaultValue;
    return value.toLowerCase() === 'true';
  }

  /**
   * Parse number environment variable
   */
  private getNumberEnv(key: string, defaultValue: number): number {
    const value = this.getEnvVar(key, '');
    if (!value) return defaultValue;
    const parsed = parseInt(value, 10);
    return isNaN(parsed) ? defaultValue : parsed;
  }

  /**
   * Generate default fallback URLs based on primary backend URL
   */
  private getDefaultFallbackUrls(primaryUrl: string): string[] {
    try {
      const url = new URL(primaryUrl);
      const fallbacks: string[] = [];
      
      // Add localhost variations if not already localhost
      if (url.hostname !== 'localhost') {
        fallbacks.push(`http://localhost:${url.port || '8000'}`);
      }
      
      // Add 127.0.0.1 variation
      if (url.hostname !== '127.0.0.1') {
        fallbacks.push(`http://127.0.0.1:${url.port || '8000'}`);
      }
      
      return fallbacks;
    } catch {
      // If URL parsing fails, return sensible defaults
      return ['http://localhost:8000', 'http://127.0.0.1:8000'];
    }
  }

  /**
   * Detect the current environment and update configuration accordingly
   */
  private detectEnvironment(): void {
    // Check if running in Docker container
    const isDocker = this.isRunningInDocker();
    
    // Check if accessing via external IP
    const isExternal = this.isExternalAccess();
    
    // Update network mode based on detection
    if (isDocker) {
      this.config.networkMode = 'container';
      this.config.environment = 'docker';
    } else if (isExternal) {
      this.config.networkMode = 'external';
    } else {
      this.config.networkMode = 'localhost';
      this.config.environment = 'local';
    }

    // Adjust backend URL based on detected environment
    this.adjustBackendUrlForEnvironment();
  }

  /**
   * Check if running in Docker container
   */
  private isRunningInDocker(): boolean {
    // Check for Docker-specific environment indicators
    if (typeof process !== 'undefined' && process.env) {
      // Common Docker environment variables
      if (process.env.DOCKER_CONTAINER || 
          process.env.HOSTNAME?.startsWith('docker-') ||
          process.env.KAREN_CONTAINER_MODE === 'true') {
        return true;
      }
    }

    // Check for container-specific network conditions
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      // If accessing via container name or internal Docker network
      if (hostname.includes('docker') || hostname.includes('container')) {
        return true;
      }
    }

    return false;
  }

  /**
   * Check if accessing via external IP
   */
  private isExternalAccess(): boolean {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      
      // Check if hostname is localhost or 127.0.0.1
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return false;
      }

      // Check for IP address patterns (any IP that's not localhost should be treated as external for our purposes)
      if (hostname.match(/^\d+\.\d+\.\d+\.\d+$/)) {
        return true;
      }

      // Check for non-localhost hostnames
      if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
        return true;
      }
    }

    return false;
  }

  /**
   * Adjust backend URL based on detected environment
   */
  private adjustBackendUrlForEnvironment(): void {
    const containerHost = this.getEnvVar('KAREN_CONTAINER_BACKEND_HOST', 'backend');
    const containerPort = this.getEnvVar('KAREN_CONTAINER_BACKEND_PORT', '8000');
    const externalHost = this.getEnvVar('KAREN_EXTERNAL_HOST', '');
    const externalPort = this.getEnvVar('KAREN_EXTERNAL_BACKEND_PORT', '8000');

    switch (this.config.networkMode) {
      case 'container':
        // Use container networking
        this.config.backendUrl = `http://${containerHost}:${containerPort}`;
        break;
        
      case 'external':
        // Use external IP if configured
        if (externalHost) {
          this.config.backendUrl = `http://${externalHost}:${externalPort}`;
        } else if (typeof window !== 'undefined') {
          // Use current hostname with backend port
          const currentHost = window.location.hostname;
          this.config.backendUrl = `http://${currentHost}:${externalPort}`;
        }
        break;
        
      case 'localhost':
      default:
        // Keep localhost configuration (already set in loadConfiguration)
        break;
    }
  }

  /**
   * Get the primary backend URL
   */
  public getBackendUrl(): string {
    return this.config.backendUrl;
  }

  /**
   * Get the authentication endpoint URL
   */
  public getAuthEndpoint(): string {
    return `${this.config.backendUrl}/api/auth`;
  }

  /**
   * Get the chat endpoint URL
   */
  public getChatEndpoint(): string {
    return `${this.config.backendUrl}/api/chat`;
  }

  /**
   * Get the memory endpoint URL
   */
  public getMemoryEndpoint(): string {
    return `${this.config.backendUrl}/api/memory`;
  }

  /**
   * Get the plugins endpoint URL
   */
  public getPluginsEndpoint(): string {
    return `${this.config.backendUrl}/api/plugins`;
  }

  /**
   * Get the health check endpoint URL
   */
  public getHealthEndpoint(): string {
    return `${this.config.backendUrl}/health`;
  }

  /**
   * Get all fallback URLs
   */
  public getFallbackUrls(): string[] {
    return [...this.config.fallbackUrls];
  }

  /**
   * Get current configuration
   */
  public getConfiguration(): EndpointConfig {
    return { ...this.config };
  }

  /**
   * Get current environment information
   */
  public getEnvironmentInfo(): {
    environment: Environment;
    networkMode: NetworkMode;
    backendUrl: string;
    isDocker: boolean;
    isExternal: boolean;
  } {
    return {
      environment: this.config.environment,
      networkMode: this.config.networkMode,
      backendUrl: this.config.backendUrl,
      isDocker: this.config.networkMode === 'container',
      isExternal: this.config.networkMode === 'external',
    };
  }

  /**
   * Validate endpoint connectivity
   */
  public async validateEndpoints(): Promise<EndpointValidationResult[]> {
    const endpoints = [this.config.backendUrl, ...this.config.fallbackUrls];
    const results: EndpointValidationResult[] = [];

    for (const endpoint of endpoints) {
      // Check cache first
      const cacheKey = `validation:${endpoint}`;
      const cached = this.validationCache.get(cacheKey);
      
      if (cached && Date.now() - new Date(cached.timestamp).getTime() < this.CACHE_TTL) {
        results.push(cached);
        continue;
      }

      // Perform validation
      const result = await this.validateSingleEndpoint(endpoint);
      
      // Cache result
      this.validationCache.set(cacheKey, result);
      results.push(result);
    }

    return results;
  }

  /**
   * Validate a single endpoint
   */
  private async validateSingleEndpoint(endpoint: string): Promise<EndpointValidationResult> {
    const startTime = performance.now();
    const timestamp = new Date().toISOString();

    try {
      const healthUrl = `${endpoint}/health`;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.healthCheckTimeout);

      const response = await fetch(healthUrl, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
        },
      });

      clearTimeout(timeoutId);
      const responseTime = performance.now() - startTime;

      if (response.ok) {
        return {
          isValid: true,
          endpoint,
          responseTime,
          timestamp,
        };
      } else {
        return {
          isValid: false,
          endpoint,
          responseTime,
          error: `HTTP ${response.status}: ${response.statusText}`,
          timestamp,
        };
      }
    } catch (error) {
      const responseTime = performance.now() - startTime;
      let errorMessage = 'Unknown error';

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = 'Request timeout';
        } else if (error.message.includes('fetch')) {
          errorMessage = 'Network error - unable to connect';
        } else {
          errorMessage = error.message;
        }
      }

      return {
        isValid: false,
        endpoint,
        responseTime,
        error: errorMessage,
        timestamp,
      };
    }
  }

  /**
   * Update configuration (for runtime changes)
   */
  public updateConfiguration(updates: Partial<EndpointConfig>): void {
    this.config = { ...this.config, ...updates };
    
    // Clear validation cache when configuration changes
    this.validationCache.clear();
    
    // Re-detect environment if backend URL changed
    if (updates.backendUrl) {
      this.detectEnvironment();
    }
  }

  /**
   * Clear validation cache
   */
  public clearValidationCache(): void {
    this.validationCache.clear();
  }

  /**
   * Get validation cache statistics
   */
  public getValidationCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.validationCache.size,
      keys: Array.from(this.validationCache.keys()),
    };
  }
}

// Singleton instance
let configManager: ConfigManager | null = null;

/**
 * Get the global configuration manager instance
 */
export function getConfigManager(): ConfigManager {
  if (!configManager) {
    configManager = new ConfigManager();
  }
  return configManager;
}

/**
 * Initialize configuration manager with custom settings
 */
export function initializeConfigManager(): ConfigManager {
  configManager = new ConfigManager();
  return configManager;
}

// Export types and utilities
export type { 
  EndpointConfig as EndpointConfigType, 
  EndpointValidationResult as EndpointValidationResultType 
};