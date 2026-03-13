/**
 * Unified API Client
 * Consolidates multiple API client implementations into a single, consistent interface
 * Ensures DRY principles and eliminates conflicting implementations
 */

import { EnhancedApiClient } from '../base-api-client';

// Unified API client configuration
interface UnifiedApiConfig {
  baseURL?: string;
  timeout?: number;
  retries?: number;
  enableLogging?: boolean;
  enablePerformanceMonitoring?: boolean;
}

// Default configuration
const DEFAULT_CONFIG: UnifiedApiConfig = {
  timeout: 30000,
  retries: 3,
  enableLogging: process.env.NODE_ENV === 'development',
  enablePerformanceMonitoring: true
};

/**
 * Unified API Client that wraps EnhancedApiClient
 * Provides a single, consistent interface for all API operations
 */
export class UnifiedApiClient {
  private client: EnhancedApiClient;
  private config: UnifiedApiConfig;

  constructor(config: Partial<UnifiedApiConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.client = new EnhancedApiClient(this.config.baseURL || '');
    
    // Configure the client
    this.setupClientConfiguration();
  }

  /**
   * Setup client configuration and interceptors
   */
  private setupClientConfiguration(): void {
    // Set up request interceptors for logging and performance
    this.client.addRequestInterceptor(async (config) => {
      const startTime = performance.now();
      
      if (this.config.enableLogging) {
        console.debug(`[API] Request: ${config.method || 'GET'}`);
      }
      
      // Add performance tracking
      (config as any).__startTime = startTime;
      
      return config;
    });

    // Set up response interceptors for logging and performance
    this.client.addResponseInterceptor(async (response, config) => {
      const startTime = (config as any).__startTime;
      const duration = startTime ? performance.now() - startTime : 0;
      
      if (this.config.enableLogging) {
        console.debug(`[API] Response: ${response.status} (${duration.toFixed(2)}ms)`);
      }
      
      if (this.config.enablePerformanceMonitoring && duration > 1000) {
        console.warn(`[API] Slow request detected: took ${duration.toFixed(2)}ms`);
      }
      
      return response;
    });

    // Set up error interceptors for consistent error handling
    this.client.addErrorInterceptor(async (error, config) => {
      if (this.config.enableLogging) {
        console.error(`[API] Error: ${config.method || 'GET'}`, error);
      }
      
      return error;
    });
  }

  /**
   * Generic request method
   */
  async request<T = unknown>(
    endpoint: string,
    config: RequestInit & { timeout?: number; retries?: number } = {}
  ): Promise<{ data: T; status: string; meta?: any }> {
    try {
      const response = await this.client.request<T>(endpoint, {
        ...config,
        timeout: config.timeout || this.config.timeout,
        retries: config.retries || this.config.retries
      });
      
      return {
        data: response.data,
        status: 'success'
      };
    } catch (error) {
      return {
        data: null as T,
        status: 'error',
        meta: {
          error: error instanceof Error ? error.message : 'Unknown error',
          requestId: (error as any).requestId
        }
      };
    }
  }

  /**
   * GET request
   */
  async get<T = unknown>(endpoint: string, config?: RequestInit): Promise<{ data: T; status: string }> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T = unknown>(
    endpoint: string, 
    data?: unknown, 
    config?: RequestInit
  ): Promise<{ data: T; status: string }> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  /**
   * PUT request
   */
  async put<T = unknown>(
    endpoint: string, 
    data?: unknown, 
    config?: RequestInit
  ): Promise<{ data: T; status: string }> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  /**
   * PATCH request
   */
  async patch<T = unknown>(
    endpoint: string, 
    data?: unknown, 
    config?: RequestInit
  ): Promise<{ data: T; status: string }> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  /**
   * DELETE request
   */
  async delete<T = unknown>(endpoint: string, config?: RequestInit): Promise<{ data: T; status: string }> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  /**
   * File upload with progress tracking
   */
  async upload<T = unknown>(
    endpoint: string,
    file: File,
    config?: RequestInit,
    onProgress?: (progress: number) => void
  ): Promise<{ data: T; status: string }> {
    try {
      const response = await this.client.upload<T>(endpoint, file, config, onProgress);
      
      return {
        data: response.data,
        status: 'success'
      };
    } catch (error) {
      return {
        data: null as T,
        status: 'error'
      };
    }
  }

  /**
   * Batch requests for multiple operations
   */
  async batch<T = unknown>(
    requests: Array<{ endpoint: string; method?: string; data?: unknown }>
  ): Promise<Array<{ data: T; status: string }>> {
    const results = await Promise.allSettled(
      requests.map(req => 
        this.request<T>(req.endpoint, {
          method: req.method || 'GET',
          body: req.data ? JSON.stringify(req.data) : undefined
        })
      )
    );

    return results.map(result => 
      result.status === 'fulfilled' 
        ? result.value 
        : { data: null as T, status: 'error', meta: { error: result.reason } }
    );
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; data?: any }> {
    try {
      const response = await this.get('/api/health');
      return {
        status: 'healthy',
        data: response.data
      };
    } catch (error) {
      return {
        status: 'unhealthy'
      };
    }
  }

  /**
   * Get client configuration
   */
  getConfig(): UnifiedApiConfig {
    return { ...this.config };
  }

  /**
   * Update client configuration
   */
  updateConfig(newConfig: Partial<UnifiedApiConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.setupClientConfiguration();
  }
}

// Singleton instance
let unifiedApiClient: UnifiedApiClient | null = null;

/**
 * Get the unified API client instance
 */
export function getUnifiedApiClient(config?: Partial<UnifiedApiConfig>): UnifiedApiClient {
  if (!unifiedApiClient) {
    unifiedApiClient = new UnifiedApiClient(config);
  }
  return unifiedApiClient;
}

/**
 * Initialize the unified API client with custom configuration
 */
export function initializeUnifiedApiClient(config: Partial<UnifiedApiConfig>): UnifiedApiClient {
  unifiedApiClient = new UnifiedApiClient(config);
  return unifiedApiClient;
}

/**
 * Reset the unified API client instance
 */
export function resetUnifiedApiClient(): void {
  unifiedApiClient = null;
}

// Export the singleton instance for backward compatibility
export const apiClient = getUnifiedApiClient();

// Export convenience methods for backward compatibility
export const api = {
  get: <T = unknown>(endpoint: string, config?: RequestInit) => 
    apiClient.get<T>(endpoint, config),
  post: <T = unknown>(endpoint: string, data?: unknown, config?: RequestInit) => 
    apiClient.post<T>(endpoint, data, config),
  put: <T = unknown>(endpoint: string, data?: unknown, config?: RequestInit) => 
    apiClient.put<T>(endpoint, data, config),
  patch: <T = unknown>(endpoint: string, data?: unknown, config?: RequestInit) => 
    apiClient.patch<T>(endpoint, data, config),
  delete: <T = unknown>(endpoint: string, config?: RequestInit) => 
    apiClient.delete<T>(endpoint, config),
  upload: <T = unknown>(endpoint: string, file: File, config?: RequestInit, onProgress?: (progress: number) => void) => 
    apiClient.upload<T>(endpoint, file, config, onProgress),
  batch: <T = unknown>(requests: Array<{ endpoint: string; method?: string; data?: unknown }>) => 
    apiClient.batch<T>(requests),
  healthCheck: () => apiClient.healthCheck()
};

export default UnifiedApiClient;