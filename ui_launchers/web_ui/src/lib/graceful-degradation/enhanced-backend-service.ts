/**
 * Enhanced backend service with graceful degradation support
 * Wraps the existing KarenBackendService with graceful degradation capabilities
 */
import { 
  featureFlagManager, 
  extensionCache, 
  CacheAwareDataFetcher,
  type FeatureFlag 
} from './index';
export interface EnhancedRequestOptions {
  endpoint: string;
  options?: RequestInit;
  cacheKey?: string;
  enableCaching?: boolean;
  useStaleOnError?: boolean;
  maxStaleAge?: number;
  fallbackData?: any;
  serviceName?: string;
}
export interface ServiceHealthStatus {
  isHealthy: boolean;
  lastSuccessfulRequest?: Date;
  consecutiveFailures: number;
  lastError?: Error;
}
export class EnhancedBackendService {
  private serviceHealth: Map<string, ServiceHealthStatus> = new Map();
  private cacheFetcher: CacheAwareDataFetcher;
  private maxRetries: number = 3;
  private baseRetryDelay: number = 1000;
  constructor(private originalService: any) {
    this.cacheFetcher = new CacheAwareDataFetcher(
      extensionCache,
      async (key: string) => {
        // This will be overridden per request
        throw new Error('Cache fetcher not properly configured');
      }
    );
  }
  async makeEnhancedRequest<T>(options: EnhancedRequestOptions): Promise<T> {
    const {
      endpoint,
      options: requestOptions = {},
      cacheKey,
      enableCaching = true,
      useStaleOnError = true,
      maxStaleAge = 60 * 60 * 1000, // 1 hour
      fallbackData,
      serviceName = this.getServiceNameFromEndpoint(endpoint)
    } = options;
    // Check if the service feature is enabled
    const featureName = this.getFeatureNameFromService(serviceName);
    if (!featureFlagManager.isEnabled(featureName)) {
      return this.handleDisabledService(serviceName, cacheKey, fallbackData, useStaleOnError, maxStaleAge);
    }
    // Check service health
    const healthStatus = this.getServiceHealth(serviceName);
    if (!healthStatus.isHealthy && healthStatus.consecutiveFailures >= 3) {
      return this.handleUnhealthyService(serviceName, cacheKey, fallbackData, useStaleOnError, maxStaleAge);
    }
    let lastError: Error | null = null;
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        let result: T;
        if (enableCaching && cacheKey) {
          // Use cache-aware fetcher
          const fetcher = new CacheAwareDataFetcher(
            extensionCache,
            async () => await this.originalService.makeRequest(endpoint, requestOptions)
          );
          result = await fetcher.fetchWithCache<T>(cacheKey, {
            useStaleOnError,
            maxStaleAge,
            ttl: 5 * 60 * 1000 // 5 minutes default TTL
          });
        } else {
          result = await this.originalService.makeRequest(endpoint, requestOptions);
        }
        // Mark service as healthy on successful request
        this.markServiceHealthy(serviceName);
        return result;
      } catch (error) {
        lastError = error as Error;
        // Handle specific error types
        if (this.isAuthenticationError(lastError)) {
          return this.handleAuthenticationError(serviceName, endpoint, lastError, cacheKey, fallbackData, useStaleOnError, maxStaleAge);
        }
        if (this.isServiceUnavailableError(lastError)) {
          return this.handleServiceUnavailableError(serviceName, endpoint, lastError, attempt, cacheKey, fallbackData, useStaleOnError, maxStaleAge);
        }
        // Mark service as unhealthy
        this.markServiceUnhealthy(serviceName, lastError);
        // If this is the last attempt, handle the failure
        if (attempt === this.maxRetries) {
          return this.handleFinalFailure(serviceName, endpoint, lastError, cacheKey, fallbackData, useStaleOnError, maxStaleAge);
        }
        // Wait before retry with exponential backoff
        await this.delay(this.baseRetryDelay * Math.pow(2, attempt - 1));
      }
    }
    // This should never be reached, but just in case
    throw lastError || new Error('Request failed for unknown reason');
  }
  private async handleDisabledService<T>(
    serviceName: string,
    cacheKey?: string,
    fallbackData?: any,
    useStaleOnError?: boolean,
    maxStaleAge?: number
  ): Promise<T> {
    // Try to get cached data
    if (cacheKey && useStaleOnError) {
      const cachedData = extensionCache.getStale<T>(cacheKey, maxStaleAge);
      if (cachedData) {
        return cachedData;
      }
    }
    // Use fallback data if available
    if (fallbackData !== undefined) {
      return fallbackData;
    }
    // Throw error indicating service is disabled
    throw new Error(`Service ${serviceName} is currently disabled and no fallback data is available`);
  }
  private async handleUnhealthyService<T>(
    serviceName: string,
    cacheKey?: string,
    fallbackData?: any,
    useStaleOnError?: boolean,
    maxStaleAge?: number
  ): Promise<T> {
    // Try to get cached data
    if (cacheKey && useStaleOnError) {
      const cachedData = extensionCache.getStale<T>(cacheKey, maxStaleAge);
      if (cachedData) {
        return cachedData;
      }
    }
    // Use fallback data if available
    if (fallbackData !== undefined) {
      return fallbackData;
    }
    // Throw error indicating service is unhealthy
    throw new Error(`Service ${serviceName} is currently unhealthy and no fallback data is available`);
  }
  private async handleAuthenticationError<T>(
    serviceName: string,
    endpoint: string,
    error: Error,
    cacheKey?: string,
    fallbackData?: any,
    useStaleOnError?: boolean,
    maxStaleAge?: number
  ): Promise<T> {
    // Disable the extension auth feature flag
    featureFlagManager.handleServiceError('extension-auth', error);
    // Try to get cached data
    if (cacheKey && useStaleOnError) {
      const cachedData = extensionCache.getStale<T>(cacheKey, maxStaleAge);
      if (cachedData) {
        return cachedData;
      }
    }
    // Use fallback data if available
    if (fallbackData !== undefined) {
      return fallbackData;
    }
    // Re-throw authentication error
    throw error;
  }
  private async handleServiceUnavailableError<T>(
    serviceName: string,
    endpoint: string,
    error: Error,
    attempt: number,
    cacheKey?: string,
    fallbackData?: any,
    useStaleOnError?: boolean,
    maxStaleAge?: number
  ): Promise<T> {
    console.warn(`Service unavailable error for ${serviceName} (attempt ${attempt}):`, error.message);
    // If this is not the last attempt, don't use fallback yet
    if (attempt < this.maxRetries) {
      throw error; // Let the retry logic handle it
    }
    // Disable the service feature flag
    featureFlagManager.handleServiceError(serviceName, error);
    // Try to get cached data
    if (cacheKey && useStaleOnError) {
      const cachedData = extensionCache.getStale<T>(cacheKey, maxStaleAge);
      if (cachedData) {
        return cachedData;
      }
    }
    // Use fallback data if available
    if (fallbackData !== undefined) {
      return fallbackData;
    }
    // Re-throw service unavailable error
    throw error;
  }
  private async handleFinalFailure<T>(
    serviceName: string,
    endpoint: string,
    error: Error,
    cacheKey?: string,
    fallbackData?: any,
    useStaleOnError?: boolean,
    maxStaleAge?: number
  ): Promise<T> {
    // Disable the service feature flag
    featureFlagManager.handleServiceError(serviceName, error);
    // Try to get cached data as last resort
    if (cacheKey && useStaleOnError) {
      const cachedData = extensionCache.getStale<T>(cacheKey, maxStaleAge);
      if (cachedData) {
        return cachedData;
      }
    }
    // Use fallback data if available
    if (fallbackData !== undefined) {
      return fallbackData;
    }
    // Re-throw the error
    throw error;
  }
  private isAuthenticationError(error: any): boolean {
    return (
      error?.status === 401 ||
      error?.status === 403 ||
      error?.message?.includes('authentication') ||
      error?.message?.includes('unauthorized') ||
      error?.message?.includes('forbidden')
    );
  }
  private isServiceUnavailableError(error: any): boolean {
    return (
      error?.status === 503 ||
      error?.status === 502 ||
      error?.status === 504 ||
      error?.message?.includes('service unavailable') ||
      error?.message?.includes('network error') ||
      error?.message?.includes('timeout')
    );
  }
  private getServiceNameFromEndpoint(endpoint: string): string {
    if (endpoint.includes('/api/extensions')) return 'extension-api';
    if (endpoint.includes('/api/models')) return 'model-provider';
    if (endpoint.includes('/api/health')) return 'extension-health';
    if (endpoint.includes('background-task')) return 'background-tasks';
    return 'unknown-service';
  }
  private getFeatureNameFromService(serviceName: string): string {
    const mapping: Record<string, string> = {
      'extension-api': 'extensionSystem',
      'model-provider': 'modelProviderIntegration',
      'extension-health': 'extensionHealth',
      'background-tasks': 'backgroundTasks'
    };
    return mapping[serviceName] || 'extensionSystem';
  }
  private getServiceHealth(serviceName: string): ServiceHealthStatus {
    if (!this.serviceHealth.has(serviceName)) {
      this.serviceHealth.set(serviceName, {
        isHealthy: true,
        consecutiveFailures: 0
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
    // Re-enable the service feature flag if it was disabled
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
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  // Convenience methods for common extension endpoints
  async getExtensions(useCache: boolean = true): Promise<any[]> {
    return this.makeEnhancedRequest({
      endpoint: '/api/extensions/',
      cacheKey: useCache ? 'extensions-list' : undefined,
      enableCaching: useCache,
      serviceName: 'extension-api',
      fallbackData: []
    });
  }
  async getBackgroundTasks(useCache: boolean = true): Promise<any[]> {
    return this.makeEnhancedRequest({
      endpoint: '/api/extensions/background-tasks/',
      cacheKey: useCache ? 'background-tasks' : undefined,
      enableCaching: useCache,
      serviceName: 'background-tasks',
      fallbackData: []
    });
  }
  async getModelProviders(useCache: boolean = true): Promise<any[]> {
    return this.makeEnhancedRequest({
      endpoint: '/api/models/providers/',
      cacheKey: useCache ? 'model-providers' : undefined,
      enableCaching: useCache,
      serviceName: 'model-provider',
      fallbackData: []
    });
  }
  async getExtensionHealth(extensionName: string, useCache: boolean = true): Promise<any> {
    return this.makeEnhancedRequest({
      endpoint: `/api/extensions/${extensionName}/health/`,
      cacheKey: useCache ? `extension-health-${extensionName}` : undefined,
      enableCaching: useCache,
      serviceName: 'extension-health',
      fallbackData: { status: 'unknown', message: 'Health check unavailable' }
    });
  }
  // Get service health status
  getServiceHealthStatus(): Record<string, ServiceHealthStatus> {
    return Object.fromEntries(this.serviceHealth);
  }
  // Force refresh cached data
  refreshCache(cacheKey?: string): void {
    if (cacheKey) {
      extensionCache.delete(cacheKey);
    } else {
      extensionCache.clear();
    }
  }
}
