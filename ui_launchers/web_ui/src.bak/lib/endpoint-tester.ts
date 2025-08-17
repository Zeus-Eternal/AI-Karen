/**
 * Endpoint Testing Service
 * Provides comprehensive endpoint connectivity testing with health checks and timeout handling
 */

export interface EndpointTestResult {
  endpoint: string;
  isReachable: boolean;
  responseTime: number;
  httpStatus?: number;
  error?: string;
  timestamp: string;
  testType: 'connectivity' | 'health' | 'api';
}

export interface HealthCheckResponse {
  status: 'ok' | 'error' | 'degraded';
  timestamp: string;
  services?: Record<string, {
    status: 'ok' | 'error' | 'degraded';
    responseTime?: number;
    error?: string;
  }>;
  version?: string;
  uptime?: number;
  environment?: string;
}

export interface EndpointTestConfig {
  timeout: number;
  retries: number;
  retryDelay: number;
  healthCheckPath: string;
  testApiPath: string;
  userAgent: string;
}

/**
 * Service for testing endpoint connectivity and health
 */
export class EndpointTester {
  private config: EndpointTestConfig;
  private testCache: Map<string, EndpointTestResult> = new Map();
  private readonly CACHE_TTL = 30000; // 30 seconds

  constructor(config?: Partial<EndpointTestConfig>) {
    this.config = {
      timeout: 5000,
      retries: 3,
      retryDelay: 1000,
      healthCheckPath: '/health',
      testApiPath: '/api/health',
      userAgent: 'AI-Karen-WebUI/1.0',
      ...config,
    };
  }

  /**
   * Test basic connectivity to an endpoint
   */
  public async testConnectivity(endpoint: string): Promise<EndpointTestResult> {
    const cacheKey = `connectivity:${endpoint}`;
    const cached = this.getCachedResult(cacheKey);
    if (cached) return cached;

    const startTime = performance.now();
    const timestamp = new Date().toISOString();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

      const response = await fetch(endpoint, {
        method: 'HEAD',
        signal: controller.signal,
        headers: {
          'User-Agent': this.config.userAgent,
          'Cache-Control': 'no-cache',
        },
        mode: 'cors',
      });

      clearTimeout(timeoutId);
      const responseTime = performance.now() - startTime;

      const result: EndpointTestResult = {
        endpoint,
        isReachable: true,
        responseTime,
        httpStatus: response.status,
        timestamp,
        testType: 'connectivity',
      };

      this.cacheResult(cacheKey, result);
      return result;

    } catch (error) {
      const responseTime = performance.now() - startTime;
      const result: EndpointTestResult = {
        endpoint,
        isReachable: false,
        responseTime,
        error: this.parseError(error),
        timestamp,
        testType: 'connectivity',
      };

      this.cacheResult(cacheKey, result);
      return result;
    }
  }

  /**
   * Test endpoint health using the /health endpoint
   */
  public async testHealth(endpoint: string): Promise<EndpointTestResult> {
    const cacheKey = `health:${endpoint}`;
    const cached = this.getCachedResult(cacheKey);
    if (cached) return cached;

    const healthUrl = `${endpoint}${this.config.healthCheckPath}`;
    const startTime = performance.now();
    const timestamp = new Date().toISOString();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

      const response = await fetch(healthUrl, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'User-Agent': this.config.userAgent,
          'Cache-Control': 'no-cache',
        },
        mode: 'cors',
      });

      clearTimeout(timeoutId);
      const responseTime = performance.now() - startTime;

      if (response.ok) {
        // Try to parse health response
        let healthData: HealthCheckResponse | null = null;
        try {
          healthData = await response.json();
        } catch {
          // If JSON parsing fails, treat as basic success
        }

        const result: EndpointTestResult = {
          endpoint,
          isReachable: true,
          responseTime,
          httpStatus: response.status,
          timestamp,
          testType: 'health',
        };

        // Add error if health check indicates issues
        if (healthData?.status === 'error') {
          result.error = 'Health check reports error status';
        } else if (healthData?.status === 'degraded') {
          result.error = 'Health check reports degraded status';
        }

        this.cacheResult(cacheKey, result);
        return result;

      } else {
        const result: EndpointTestResult = {
          endpoint,
          isReachable: false,
          responseTime,
          httpStatus: response.status,
          error: `Health check failed: HTTP ${response.status}`,
          timestamp,
          testType: 'health',
        };

        this.cacheResult(cacheKey, result);
        return result;
      }

    } catch (error) {
      const responseTime = performance.now() - startTime;
      const result: EndpointTestResult = {
        endpoint,
        isReachable: false,
        responseTime,
        error: `Health check error: ${this.parseError(error)}`,
        timestamp,
        testType: 'health',
      };

      this.cacheResult(cacheKey, result);
      return result;
    }
  }

  /**
   * Test API endpoint functionality
   */
  public async testApi(endpoint: string): Promise<EndpointTestResult> {
    const cacheKey = `api:${endpoint}`;
    const cached = this.getCachedResult(cacheKey);
    if (cached) return cached;

    const apiUrl = `${endpoint}${this.config.testApiPath}`;
    const startTime = performance.now();
    const timestamp = new Date().toISOString();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

      const response = await fetch(apiUrl, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'User-Agent': this.config.userAgent,
          'Cache-Control': 'no-cache',
        },
        mode: 'cors',
      });

      clearTimeout(timeoutId);
      const responseTime = performance.now() - startTime;

      const result: EndpointTestResult = {
        endpoint,
        isReachable: response.ok,
        responseTime,
        httpStatus: response.status,
        timestamp,
        testType: 'api',
      };

      if (!response.ok) {
        result.error = `API test failed: HTTP ${response.status}`;
      }

      this.cacheResult(cacheKey, result);
      return result;

    } catch (error) {
      const responseTime = performance.now() - startTime;
      const result: EndpointTestResult = {
        endpoint,
        isReachable: false,
        responseTime,
        error: `API test error: ${this.parseError(error)}`,
        timestamp,
        testType: 'api',
      };

      this.cacheResult(cacheKey, result);
      return result;
    }
  }

  /**
   * Comprehensive endpoint test (connectivity + health + API)
   */
  public async testEndpointComprehensive(endpoint: string): Promise<{
    connectivity: EndpointTestResult;
    health: EndpointTestResult;
    api: EndpointTestResult;
    overall: {
      isHealthy: boolean;
      score: number; // 0-100
      issues: string[];
    };
  }> {
    const [connectivity, health, api] = await Promise.all([
      this.testConnectivity(endpoint),
      this.testHealth(endpoint),
      this.testApi(endpoint),
    ]);

    // Calculate overall health score
    let score = 0;
    const issues: string[] = [];

    // Connectivity (40% weight)
    if (connectivity.isReachable) {
      score += 40;
      if (connectivity.responseTime < 1000) score += 10; // Bonus for fast response
    } else {
      issues.push(`Connectivity failed: ${connectivity.error}`);
    }

    // Health check (30% weight)
    if (health.isReachable) {
      score += 30;
      if (health.responseTime < 2000) score += 5; // Bonus for fast health check
    } else {
      issues.push(`Health check failed: ${health.error}`);
    }

    // API test (30% weight)
    if (api.isReachable) {
      score += 30;
    } else {
      issues.push(`API test failed: ${api.error}`);
    }

    return {
      connectivity,
      health,
      api,
      overall: {
        isHealthy: score >= 70, // Consider healthy if score is 70% or higher
        score,
        issues,
      },
    };
  }

  /**
   * Test multiple endpoints and return the best one
   */
  public async findBestEndpoint(endpoints: string[]): Promise<{
    bestEndpoint: string | null;
    results: Array<{
      endpoint: string;
      score: number;
      isHealthy: boolean;
      responseTime: number;
      issues: string[];
    }>;
  }> {
    if (endpoints.length === 0) {
      return { bestEndpoint: null, results: [] };
    }

    // Test all endpoints
    const testPromises = endpoints.map(async (endpoint) => {
      const comprehensive = await this.testEndpointComprehensive(endpoint);
      return {
        endpoint,
        score: comprehensive.overall.score,
        isHealthy: comprehensive.overall.isHealthy,
        responseTime: comprehensive.connectivity.responseTime,
        issues: comprehensive.overall.issues,
      };
    });

    const results = await Promise.all(testPromises);

    // Sort by score (descending) and response time (ascending)
    results.sort((a, b) => {
      if (a.score !== b.score) {
        return b.score - a.score; // Higher score first
      }
      return a.responseTime - b.responseTime; // Faster response first
    });

    // Find the best healthy endpoint
    const bestHealthy = results.find(r => r.isHealthy);
    const bestEndpoint = bestHealthy ? bestHealthy.endpoint : (results[0]?.endpoint || null);

    return { bestEndpoint, results };
  }

  /**
   * Test endpoint with retry logic
   */
  public async testWithRetry(endpoint: string, testType: 'connectivity' | 'health' | 'api' = 'connectivity'): Promise<EndpointTestResult> {
    let lastError: string | undefined;
    
    for (let attempt = 1; attempt <= this.config.retries; attempt++) {
      try {
        let result: EndpointTestResult;
        
        switch (testType) {
          case 'health':
            result = await this.testHealth(endpoint);
            break;
          case 'api':
            result = await this.testApi(endpoint);
            break;
          default:
            result = await this.testConnectivity(endpoint);
            break;
        }

        if (result.isReachable) {
          return result;
        }

        lastError = result.error;

      } catch (error) {
        lastError = this.parseError(error);
      }

      // Wait before retry (except for last attempt)
      if (attempt < this.config.retries) {
        await this.delay(this.config.retryDelay * attempt); // Exponential backoff
      }
    }

    // All retries failed
    return {
      endpoint,
      isReachable: false,
      responseTime: 0,
      error: `Failed after ${this.config.retries} attempts. Last error: ${lastError}`,
      timestamp: new Date().toISOString(),
      testType,
    };
  }

  /**
   * Parse error object into readable string
   */
  private parseError(error: unknown): string {
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return 'Request timeout';
      } else if (error.message.includes('CORS')) {
        return 'CORS error - cross-origin requests blocked';
      } else if (error.message.includes('fetch')) {
        return 'Network error - unable to connect';
      } else if (error.message.includes('Failed to fetch')) {
        return 'Network error - server unreachable';
      } else {
        return error.message;
      }
    }
    return 'Unknown error';
  }

  /**
   * Get cached result if still valid
   */
  private getCachedResult(cacheKey: string): EndpointTestResult | null {
    const cached = this.testCache.get(cacheKey);
    if (cached && Date.now() - new Date(cached.timestamp).getTime() < this.CACHE_TTL) {
      return cached;
    }
    return null;
  }

  /**
   * Cache test result
   */
  private cacheResult(cacheKey: string, result: EndpointTestResult): void {
    this.testCache.set(cacheKey, result);
  }

  /**
   * Delay utility for retry logic
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Clear test cache
   */
  public clearCache(): void {
    this.testCache.clear();
  }

  /**
   * Get cache statistics
   */
  public getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.testCache.size,
      keys: Array.from(this.testCache.keys()),
    };
  }

  /**
   * Update configuration
   */
  public updateConfig(config: Partial<EndpointTestConfig>): void {
    this.config = { ...this.config, ...config };
    this.clearCache(); // Clear cache when config changes
  }

  /**
   * Get current configuration
   */
  public getConfig(): EndpointTestConfig {
    return { ...this.config };
  }
}

// Singleton instance
let endpointTester: EndpointTester | null = null;

/**
 * Get the global endpoint tester instance
 */
export function getEndpointTester(): EndpointTester {
  if (!endpointTester) {
    endpointTester = new EndpointTester();
  }
  return endpointTester;
}

/**
 * Initialize endpoint tester with custom configuration
 */
export function initializeEndpointTester(config?: Partial<EndpointTestConfig>): EndpointTester {
  endpointTester = new EndpointTester(config);
  return endpointTester;
}

// Export types
export type {
  EndpointTestResult as EndpointTestResultType,
  HealthCheckResponse as HealthCheckResponseType,
  EndpointTestConfig as EndpointTestConfigType,
};