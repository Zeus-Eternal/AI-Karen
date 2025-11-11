/**
 * Network Diagnostics Utility for AI Karen Web UI (production-grade)
 * - SSR-safe guards (no window/document on server)
 * - Deterministic timeouts via AbortController
 * - CORS preflight inspection and header extraction
 * - Consolidated comprehensive test suite w/ fallback backends
 * - Clean, structured logging via diagnostics logger
 */

import { webUIConfig } from './config';
import { getDiagnosticLogger, type NetworkDiagnostic, type CORSInfo, type NetworkInfo } from './diagnostics';

export interface NetworkTest {
  name: string;
  description: string;
  endpoint: string;            // absolute or relative
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'OPTIONS' | 'HEAD';
  expectedStatus?: number;
  timeout?: number;            // ms
  headers?: Record<string, string>;
  body?: string;
}

export interface NetworkTestResult {
  test: NetworkTest;
  success: boolean;
  diagnostic: NetworkDiagnostic;
  recommendations?: string[];
}

export interface ComprehensiveNetworkReport {
  timestamp: string;
  overallStatus: 'healthy' | 'degraded' | 'critical';
  summary: {
    totalTests: number;
    passedTests: number;
    failedTests: number;
    averageResponseTime: number;
  };
  testResults: NetworkTestResult[];
  systemInfo: NetworkInfo;
  recommendations: string[];
}

const isBrowser = typeof window !== 'undefined';
const nowISO = () => new Date().toISOString();

function buildFullUrl(endpoint: string): string {
  if (/^https?:\/\//i.test(endpoint)) return endpoint;
  const base = webUIConfig.backendUrl?.replace(/\/+$/, '') ?? '';
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${base}${path}`;
}

function readHeaders(h: Headers): Record<string, string> {
  const o: Record<string, string> = {};
  h.forEach((v, k) => { o[k] = v; });
  return o;
}

function classifyErrorMessage(msg: string): NetworkDiagnostic['status'] {
  const m = msg.toLowerCase();
  if (m.includes('abort') || m.includes('timeout')) return 'timeout';
  if (m.includes('cors') || m.includes('cross-origin')) return 'cors';
  if (m.includes('networkerror') || m.includes('failed to fetch')) return 'network';
  return 'error';
}

export class NetworkDiagnostics {
  private logger = getDiagnosticLogger();

  /**
   * Current client → backend network info (SSR-safe)
   */
  public getNetworkInfo(): NetworkInfo {
    let protocol = 'http';
    let host = 'any';
    let port = '80';

    try {
      const url = new URL(webUIConfig.backendUrl);
      protocol = url.protocol.replace(':', '') || 'http';
      host = url.hostname;
      port = url.port || (url.protocol === 'https:' ? '443' : '80');
    } catch {
      // ignore, leave defaults
    }

    return {
      userAgent: isBrowser ? (navigator.userAgent || 'browser') : 'server',
      connectionType: this.getConnectionType(),
      isOnline: isBrowser ? navigator.onLine : true,
      protocol,
      host,
      port,
    };
  }

  private getConnectionType(): string | undefined {
    if (!isBrowser) return undefined;
    const n = navigator as any;
    const conn = n?.connection ?? n?.mozConnection ?? n?.webkitConnection;
    return conn?.effectiveType || conn?.type;
  }

  /**
   * Fetch wrapper with timeout and clean abort
   */
  private async timedFetch(
    url: string,
    init: RequestInit & { timeout?: number } = {}
  ): Promise<Response> {
    const controller = new AbortController();
    const timeout = init.timeout ?? 5000;
    const id = setTimeout(() => controller.abort(), timeout);

    try {
      const res = await fetch(url, { ...init, signal: controller.signal });
      return res;
    } finally {
      clearTimeout(id);
    }
  }

  /**
   * Test connectivity to a given endpoint with diagnostics
   */
  public async testEndpointConnectivity(
    endpoint: string,
    method: NetworkTest['method'] = 'GET',
    timeout = 5000,
    headers?: Record<string, string>,
    body?: string
  ): Promise<NetworkDiagnostic> {
    const start = Date.now();
    const fullUrl = buildFullUrl(endpoint);

    try {
      const res = await this.timedFetch(fullUrl, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(headers ?? {}),
        },
        body,
        timeout,
      });

      const responseTime = Date.now() - start;
      const diagnostic: NetworkDiagnostic = {
        endpoint: fullUrl,
        method,
        status: res.ok ? 'success' : 'error',
        statusCode: res.status,
        responseTime,
        timestamp: nowISO(),
        headers: readHeaders(res.headers),
        networkInfo: this.getNetworkInfo(),
      };

      // If opaque or similar, `status` can be 0 in some modes (CORS no-cors),
      // but fetch in typical web apps returns non-0. We still handle CORS via OPTIONS below.
      if (!res.ok && res.status === 0) {
        diagnostic.status = 'cors';
        diagnostic.corsInfo = await this.analyzeCORS(fullUrl);
      }

      this.logger.logNetworkDiagnostic(diagnostic);
      return diagnostic;
    } catch (e) {
      const responseTime = Date.now() - start;
      const message = e instanceof Error ? e.message : String(e);
      const status = classifyErrorMessage(message);

      const diagnostic: NetworkDiagnostic = {
        endpoint: fullUrl,
        method,
        status,
        responseTime,
        timestamp: nowISO(),
        error: message,
        networkInfo: this.getNetworkInfo(),
      };

      if (status === 'cors') {
        diagnostic.corsInfo = await this.analyzeCORS(fullUrl);
      }

      this.logger.logNetworkDiagnostic(diagnostic);
      return diagnostic;
    }
  }

  /**
   * CORS analysis (preflight)
   */
  private async analyzeCORS(endpoint: string): Promise<CORSInfo> {
    const origin = isBrowser ? window.location.origin : 'any';

    const info: CORSInfo = {
      origin,
      preflightRequired: true,
    };

    try {
      const res = await this.timedFetch(endpoint, {
        method: 'OPTIONS',
        headers: {
          Origin: origin,
          'Access-Control-Request-Method': 'POST',
          'Access-Control-Request-Headers': 'Content-Type',
        },
        timeout: 5000,
      });

      info.preflightStatus = res.status;

      const allowOrigin = res.headers.get('Access-Control-Allow-Origin');
      const allowMethods = res.headers.get('Access-Control-Allow-Methods');
      const allowHeaders = res.headers.get('Access-Control-Allow-Headers');

      if (allowOrigin) info.allowedOrigins = [allowOrigin];
      if (allowMethods) info.allowedMethods = allowMethods.split(',').map(s => s.trim());
      if (allowHeaders) info.allowedHeaders = allowHeaders.split(',').map(s => s.trim());
    } catch (e) {
      info.corsError = e instanceof Error ? e.message : String(e);
    }

    return info;
  }

  /**
   * Run the full diagnostic suite against primary + fallback backends
   */
  public async runComprehensiveTest(): Promise<ComprehensiveNetworkReport> {
    const start = Date.now();

    const tests: NetworkTest[] = [
      {
        name: 'Backend Health Check',
        description: 'Test basic backend connectivity',
        endpoint: '/api/health',
        method: 'GET',
        expectedStatus: 200,
      },
      {
        name: 'Authentication Status',
        description: 'Auth endpoint availability',
        endpoint: '/api/auth/status',
        method: 'GET',
      },
      {
        name: 'Chat Endpoint',
        description: 'Conversation processing endpoint availability',
        endpoint: '/api/ai/conversation-processing',
        method: 'POST',
        body: JSON.stringify({ messages: [] }),
      },
      {
        name: 'Memory Endpoint Preflight',
        description: 'CORS preflight for memory endpoint',
        endpoint: '/api/memory/query',
        method: 'OPTIONS',
      },
      {
        name: 'Plugin List',
        description: 'Plugin listing endpoint',
        endpoint: '/api/plugins',
        method: 'GET',
      },
      {
        name: 'System Metrics',
        description: 'System metrics endpoint',
        endpoint: '/api/web/analytics/system',
        method: 'GET',
      },
      // Fallbacks
      ...(Array.isArray(webUIConfig.fallbackBackendUrls)
        ? webUIConfig.fallbackBackendUrls.map((base: string, i: number): NetworkTest => ({
            name: `Fallback Backend ${i + 1}`,
            description: `Test fallback backend connectivity`,
            endpoint: `${base.replace(/\/+$/, '')}/api/health`,
            method: 'GET',
            expectedStatus: 200,
          }))
        : []),
    ];

    const results: NetworkTestResult[] = [];
    let passed = 0;
    let totalResponse = 0;

    for (const test of tests) {
      try {
        const diagnostic = await this.testEndpointConnectivity(
          test.endpoint,
          test.method,
          test.timeout ?? 10_000,
          test.headers,
          test.body
        );

        const meetsCode = test.expectedStatus ? diagnostic.statusCode === test.expectedStatus : true;
        const success = diagnostic.status === 'success' && meetsCode;
        if (success) passed++;
        totalResponse += diagnostic.responseTime;

        results.push({
          test,
          success,
          diagnostic,
          recommendations: this.generateTestRecommendations(test, diagnostic),
        });
      } catch (e) {
        const diagnostic: NetworkDiagnostic = {
          endpoint: buildFullUrl(test.endpoint),
          method: test.method,
          status: 'error',
          responseTime: 0,
          timestamp: nowISO(),
          error: e instanceof Error ? e.message : String(e),
          networkInfo: this.getNetworkInfo(),
        };
        results.push({
          test,
          success: false,
          diagnostic,
          recommendations: ['Test execution failed', 'Check network connectivity'],
        });
      }
    }

    const failureRate = (tests.length - passed) / tests.length;
    const overallStatus: ComprehensiveNetworkReport['overallStatus'] =
      failureRate === 0 ? 'healthy' : failureRate < 0.3 ? 'degraded' : 'critical';

    const report: ComprehensiveNetworkReport = {
      timestamp: nowISO(),
      overallStatus,
      summary: {
        totalTests: tests.length,
        passedTests: passed,
        failedTests: tests.length - passed,
        averageResponseTime: tests.length ? totalResponse / tests.length : 0,
      },
      testResults: results,
      systemInfo: this.getNetworkInfo(),
      recommendations: this.generateOverallRecommendations(results, overallStatus),
    };

    this.logger.log('info', 'network', 'Comprehensive network diagnostic completed', {
      duration: Date.now() - start,
      overallStatus,
      summary: report.summary,
    });

    return report;
  }

  private generateTestRecommendations(test: NetworkTest, diagnostic: NetworkDiagnostic): string[] {
    const recs: string[] = [];

    if (!diagnostic.statusCode || diagnostic.statusCode >= 400) {
      recs.push(`Verify backend route for ${test.method} ${test.endpoint}`);
    }

    if (diagnostic.status === 'timeout') {
      recs.push('Increase client timeout (if appropriate)');
      recs.push('Investigate backend latency / queueing');
    }

    if (diagnostic.status === 'cors') {
      recs.push('Update CORS to allow current origin');
      recs.push('Verify OPTIONS preflight handler');
    }

    if (diagnostic.status === 'network') {
      recs.push('Check network/firewall connectivity to backend');
      recs.push('Confirm backend is reachable and running');
    }

    if ((diagnostic.responseTime ?? 0) > 5000) {
      recs.push('High response time: profile backend and DB hot paths');
    }

    return recs;
  }

  private generateOverallRecommendations(
    testResults: NetworkTestResult[],
    overallStatus: ComprehensiveNetworkReport['overallStatus']
  ): string[] {
    const recs: string[] = [];
    const failed = testResults.filter(r => !r.success);
    const corsIssues = failed.filter(r => r.diagnostic.status === 'cors');
    const netIssues = failed.filter(r => r.diagnostic.status === 'network');
    const timeouts = failed.filter(r => r.diagnostic.status === 'timeout');

    if (overallStatus === 'critical') {
      recs.push('Critical network issues detected — prioritize backend availability');
      recs.push('Verify base URL configuration and TLS/hostname DNS resolution');
    } else if (overallStatus === 'degraded') {
      recs.push('Intermittent network issues — monitor and tune timeouts/retries');
    }

    if (corsIssues.length) {
      recs.push('Fix CORS policy for current origin');
      recs.push('Ensure preflight responses include correct Allow-* headers');
    }
    if (netIssues.length) {
      recs.push('Check upstream connectivity / gateway / proxy rules');
      recs.push('Validate security groups / firewall / reverse-proxy routes');
    }
    if (timeouts.length) {
      recs.push('Increase client timeout or improve backend latency SLAs');
      recs.push('Add request tracing to identify slow spans');
    }

    const fallbackRows = testResults.filter(r => r.test.name.startsWith('Fallback Backend'));
    const failedFallbacks = fallbackRows.filter(r => !r.success);
    if (fallbackRows.length && failedFallbacks.length === fallbackRows.length) {
      recs.push('All fallbacks failing — recheck fallback URLs and health routes');
    }

    if (recs.length === 0) {
      recs.push('All network tests passed successfully');
      recs.push('Connectivity is healthy');
    }
    return recs;
  }

  /**
   * Detailed probe of a single endpoint (connectivity + CORS)
   */
  public async testEndpointDetailed(endpoint: string): Promise<{
    connectivity: NetworkDiagnostic;
    corsAnalysis: CORSInfo;
    recommendations: string[];
  }> {
    const connectivity = await this.testEndpointConnectivity(endpoint);
    const corsAnalysis = await this.analyzeCORS(buildFullUrl(endpoint));
    const recs: string[] = [];

    if (connectivity.status !== 'success') {
      recs.push('Endpoint connectivity failed');
      recs.push('Check backend service status / route mapping');
    }
    if (corsAnalysis.corsError) {
      recs.push('CORS configuration issue');
      recs.push('Update backend CORS allowlist and headers');
    }
    if ((connectivity.responseTime ?? 0) > 3000) {
      recs.push('Slow response detected — investigate backend performance');
    }

    return { connectivity, corsAnalysis, recommendations: recs };
  }

  /**
   * Lightweight periodic health monitoring
   */
  public startNetworkMonitoring(intervalMs = 60_000): () => void {
    const timer = setInterval(async () => {
      try {
        const hc = await this.testEndpointConnectivity('/api/health', 'GET', 5000);
        if (hc.status !== 'success') {
          this.logger.log('warn', 'network', 'Network monitoring detected connectivity issue', {
            endpoint: hc.endpoint,
            status: hc.status,
            error: hc.error,
          });
        }
      } catch (e) {
        this.logger.log('error', 'network', 'Network monitoring failed', undefined, undefined, undefined, e as Error);
      }
    }, intervalMs);

    this.logger.log('info', 'network', 'Network monitoring started', { interval: intervalMs });

    return () => {
      clearInterval(timer);
      this.logger.log('info', 'network', 'Network monitoring stopped');
    };
  }
}

// Singleton accessors
let networkDiagnostics: NetworkDiagnostics | null = null;

export function getNetworkDiagnostics(): NetworkDiagnostics {
  if (!networkDiagnostics) networkDiagnostics = new NetworkDiagnostics();
  return networkDiagnostics;
}

export function initializeNetworkDiagnostics(): NetworkDiagnostics {
  networkDiagnostics = new NetworkDiagnostics();
  return networkDiagnostics;
}

export default NetworkDiagnostics;
