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
  services?: Record<
    string,
    {
      status: 'ok' | 'error' | 'degraded';
      responseTime?: number;
      error?: string;
    }
  >;
  version?: string;
  uptime?: number;
  environment?: string;
}

export interface EndpointTestConfig {
  timeout: number;       // ms
  retries: number;
  retryDelay: number;    // ms (base backoff)
  healthCheckPath: string;
  testApiPath: string;
  userAgent: string;
}

/* ---------------------- Internal Utilities ---------------------- */

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
}

function nowMs(): number {
  try {
    return performance.now();
  } catch {
    return Date.now();
  }
}

function isoNow(): string {
  try {
    return new Date().toISOString();
  } catch {
    return String(Date.now());
  }
}

function joinUrl(base: string, path: string): string {
  const b = base.replace(/\/+$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${b}${p}`;
}

function toReadableError(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message || 'Unknown error';
    const low = msg.toLowerCase();
    if (err.name === 'AbortError') return 'Request timeout';
    if (low.includes('cors')) return 'CORS error - cross-origin requests blocked';
    if (low.includes('failed to fetch')) return 'Network error - server unreachable';
    if (low.includes('fetch')) return 'Network error - unable to connect';
    return msg;
  }
  return 'Unknown error';
}

/* ---------------------- Service ---------------------- */

export class EndpointTester {
  private config: EndpointTestConfig;
  private testCache: Map<string, EndpointTestResult> = new Map();
  private readonly CACHE_TTL = 30_000; // 30s

  constructor(config?: Partial<EndpointTestConfig>) {
    this.config = {
      timeout: 5_000,
      retries: 3,
      retryDelay: 1_000,
      healthCheckPath: '/health',
      testApiPath: '/api/health',
      userAgent: 'AI-Karen-WebUI/1.0',
      ...config,
    };
  }

  /* ---------------- Connectivity (HEAD) ---------------- */

  public async testConnectivity(endpoint: string): Promise<EndpointTestResult> {
    const cacheKey = `connectivity:${endpoint}`;
    const cached = this.getCachedResult(cacheKey);
    if (cached) return cached;

    const start = nowMs();
    const timestamp = isoNow();

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
        credentials: 'same-origin',
      });

      clearTimeout(timeoutId);
      const responseTime = Math.max(0, nowMs() - start);

      const result: EndpointTestResult = {
        endpoint,
        isReachable: response.ok || (response.status >= 200 && response.status < 500),
        responseTime,
        httpStatus: response.status,
        timestamp,
        testType: 'connectivity',
      };

      this.cacheResult(cacheKey, result);
      return result;
    } catch (error) {
      const responseTime = Math.max(0, nowMs() - start);
      const result: EndpointTestResult = {
        endpoint,
        isReachable: false,
        responseTime,
        error: toReadableError(error),
        timestamp,
        testType: 'connectivity',
      };
      this.cacheResult(cacheKey, result);
      return result;
    }
  }

  /* ---------------- Health (/health) ---------------- */

  public async testHealth(endpoint: string): Promise<EndpointTestResult> {
    const cacheKey = `health:${endpoint}`;
    const cached = this.getCachedResult(cacheKey);
    if (cached) return cached;

    const healthUrl = joinUrl(endpoint, this.config.healthCheckPath);
    const start = nowMs();
    const timestamp = isoNow();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

      const response = await fetch(healthUrl, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          'User-Agent': this.config.userAgent,
          'Cache-Control': 'no-cache',
        },
        mode: 'cors',
        credentials: 'same-origin',
      });

      clearTimeout(timeoutId);
      const responseTime = Math.max(0, nowMs() - start);

      if (response.ok) {
        let healthData: HealthCheckResponse | null = null;
        try {
          healthData = (await response.json()) as HealthCheckResponse;
        } catch {
          // Non-JSON or empty → treat as basic success
        }

        const result: EndpointTestResult = {
          endpoint,
          isReachable: true,
          responseTime,
          httpStatus: response.status,
          timestamp,
          testType: 'health',
        };

        if (healthData?.status === 'error') {
          result.error = 'Health check reports error status';
        } else if (healthData?.status === 'degraded') {
          result.error = 'Health check reports degraded status';
        }

        this.cacheResult(cacheKey, result);
        return result;
      }

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
    } catch (error) {
      const responseTime = Math.max(0, nowMs() - start);
      const result: EndpointTestResult = {
        endpoint,
        isReachable: false,
        responseTime,
        error: `Health check error: ${toReadableError(error)}`,
        timestamp,
        testType: 'health',
      };
      this.cacheResult(cacheKey, result);
      return result;
    }
  }

  /* ---------------- API (/api/health) ---------------- */

  public async testApi(endpoint: string): Promise<EndpointTestResult> {
    const cacheKey = `api:${endpoint}`;
    const cached = this.getCachedResult(cacheKey);
    if (cached) return cached;

    const apiUrl = joinUrl(endpoint, this.config.testApiPath);
    const start = nowMs();
    const timestamp = isoNow();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

      const response = await fetch(apiUrl, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          'User-Agent': this.config.userAgent,
          'Cache-Control': 'no-cache',
        },
        mode: 'cors',
        credentials: 'same-origin',
      });

      clearTimeout(timeoutId);
      const responseTime = Math.max(0, nowMs() - start);

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
      const responseTime = Math.max(0, nowMs() - start);
      const result: EndpointTestResult = {
        endpoint,
        isReachable: false,
        responseTime,
        error: `API test error: ${toReadableError(error)}`,
        timestamp,
        testType: 'api',
      };
      this.cacheResult(cacheKey, result);
      return result;
    }
  }

  /* ---------------- Comprehensive (all three) ---------------- */

  public async testEndpointComprehensive(endpoint: string): Promise<{
    connectivity: EndpointTestResult;
    health: EndpointTestResult;
    api: EndpointTestResult;
    overall: { isHealthy: boolean; score: number; issues: string[] };
  }> {
    const [connectivity, health, api] = await Promise.all([
      this.testConnectivity(endpoint),
      this.testHealth(endpoint),
      this.testApi(endpoint),
    ]);

    let score = 0;
    const issues: string[] = [];

    // Connectivity (40% + 10 bonus for <1s)
    if (connectivity.isReachable) {
      score += 40;
      if (connectivity.responseTime < 1_000) score += 10;
    } else {
      issues.push(`Connectivity failed: ${connectivity.error ?? 'unknown'}`);
    }

    // Health (30% + 5 bonus for <2s)
    if (health.isReachable) {
      score += 30;
      if (health.responseTime < 2_000) score += 5;
      if (health.error) issues.push(health.error);
    } else {
      issues.push(`Health check failed: ${health.error ?? 'unknown'}`);
    }

    // API (30%)
    if (api.isReachable) {
      score += 30;
    } else {
      issues.push(`API test failed: ${api.error ?? 'unknown'}`);
    }

    // Clamp score to 0..100
    score = Math.max(0, Math.min(100, score));

    return {
      connectivity,
      health,
      api,
      overall: {
        isHealthy: score >= 70,
        score,
        issues,
      },
    };
  }

  /* ---------------- Best Endpoint Across Many ---------------- */

  public async findBestEndpoint(endpoints: string[]): Promise<{
    bestEndpoint: string | null;
    results: Array<{ endpoint: string; score: number; isHealthy: boolean; responseTime: number; issues: string[] }>;
  }> {
    if (!Array.isArray(endpoints) || endpoints.length === 0) {
      return { bestEndpoint: null, results: [] };
    }

    const results = await Promise.all(
      endpoints.map(async (endpoint) => {
        const comprehensive = await this.testEndpointComprehensive(endpoint);
        return {
          endpoint,
          score: comprehensive.overall.score,
          isHealthy: comprehensive.overall.isHealthy,
          responseTime: comprehensive.connectivity.responseTime,
          issues: comprehensive.overall.issues,
        };
      })
    );

    results.sort((a, b) => {
      if (a.score !== b.score) return b.score - a.score; // higher score first
      return a.responseTime - b.responseTime;            // then faster
    });

    const bestHealthy = results.find((r) => r.isHealthy);
    const bestEndpoint = bestHealthy ? bestHealthy.endpoint : results[0]?.endpoint ?? null;

    return { bestEndpoint, results };
  }

  /* ---------------- Retry Wrapper ---------------- */

  public async testWithRetry(
    endpoint: string,
    testType: 'connectivity' | 'health' | 'api' = 'connectivity'
  ): Promise<EndpointTestResult> {
    let lastError: string | undefined;

    for (let attempt = 1; attempt <= this.config.retries; attempt++) {
      try {
        let result: EndpointTestResult;
        if (testType === 'health') result = await this.testHealth(endpoint);
        else if (testType === 'api') result = await this.testApi(endpoint);
        else result = await this.testConnectivity(endpoint);

        if (result.isReachable) return result;
        lastError = result.error;
      } catch (error) {
        lastError = toReadableError(error);
      }

      if (attempt < this.config.retries) {
        // Exponential backoff (linear multiplier)
        await this.delay(this.config.retryDelay * attempt);
      }
    }

    return {
      endpoint,
      isReachable: false,
      responseTime: 0,
      error: `Failed after ${this.config.retries} attempts. Last error: ${lastError ?? 'unknown'}`,
      timestamp: isoNow(),
      testType,
    };
  }

  /* ---------------- Cache + Config ---------------- */

  private getCachedResult(cacheKey: string): EndpointTestResult | null {
    const cached = this.testCache.get(cacheKey);
    if (cached && Date.now() - new Date(cached.timestamp).getTime() < this.CACHE_TTL) {
      return cached;
    }
    return null;
  }

  private cacheResult(cacheKey: string, result: EndpointTestResult): void {
    this.testCache.set(cacheKey, result);
  }

  private delay(ms: number): Promise<void> {
    return new Promise((res) => setTimeout(res, ms));
  }

  public clearCache(): void {
    this.testCache.clear();
  }

  public getCacheStats(): { size: number; keys: string[] } {
    return { size: this.testCache.size, keys: Array.from(this.testCache.keys()) };
  }

  public updateConfig(config: Partial<EndpointTestConfig>): void {
    this.config = { ...this.config, ...config };
    this.clearCache(); // flush cache when behavior changes
  }

  public getConfig(): EndpointTestConfig {
    return { ...this.config };
  }
}

/* ---------------- Singleton Helpers ---------------- */

let endpointTester: EndpointTester | null = null;

export function getEndpointTester(): EndpointTester {
  if (!endpointTester) endpointTester = new EndpointTester();
  return endpointTester;
}

export function initializeEndpointTester(config?: Partial<EndpointTestConfig>): EndpointTester {
  endpointTester = new EndpointTester(config);
  return endpointTester;
}

// Re-export types to avoid empty export blocks
export type {
  EndpointTestResult as KariEndpointTestResult,
  EndpointTestConfig as KariEndpointTestConfig,
  HealthCheckResponse as KariHealthCheckResponse,
};
