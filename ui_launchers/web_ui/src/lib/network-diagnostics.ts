/**
 * Network Diagnostics Utility for AI Karen Web UI
 * Performs comprehensive network connectivity tests and diagnostics
 */

import { webUIConfig } from './config';
import { getDiagnosticLogger, NetworkDiagnostic, CORSInfo, NetworkInfo } from './diagnostics';

export interface NetworkTest {
  name: string;
  description: string;
  endpoint: string;
  method: string;
  expectedStatus?: number;
  timeout?: number;
  headers?: Record<string, string>;
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

class NetworkDiagnostics {
  private logger = getDiagnosticLogger();

  /**
   * Get current network information
   */
  public getNetworkInfo(): NetworkInfo {
    const url = new URL(webUIConfig.backendUrl);
    
    return {
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'server',
      connectionType: this.getConnectionType(),
      isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
      protocol: url.protocol.replace(':', ''),
      host: url.hostname,
      port: url.port || (url.protocol === 'https:' ? '443' : '80'),
    };
  }

  /**
   * Get connection type if available
   */
  private getConnectionType(): string | undefined {
    if (typeof navigator !== 'undefined' && 'connection' in navigator) {
      const connection = (navigator as any).connection;
      return connection?.effectiveType || connection?.type;
    }
    return undefined;
  }

  /**
   * Test basic connectivity to an endpoint
   */
  public async testEndpointConnectivity(
    endpoint: string,
    method: string = 'GET',
    timeout: number = 5000,
    headers?: Record<string, string>
  ): Promise<NetworkDiagnostic> {
    const startTime = Date.now();
    const fullUrl = endpoint.startsWith('http') ? endpoint : `${webUIConfig.backendUrl}${endpoint}`;
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(fullUrl, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      const responseTime = Date.now() - startTime;

      // Extract response headers
      const responseHeaders: Record<string, string> = {};
      response.headers.forEach((value, key) => {
        responseHeaders[key] = value;
      });

      const diagnostic: NetworkDiagnostic = {
        endpoint: fullUrl,
        method,
        status: response.ok ? 'success' : 'error',
        statusCode: response.status,
        responseTime,
        timestamp: new Date().toISOString(),
        headers: responseHeaders,
        networkInfo: this.getNetworkInfo(),
      };

      // Check for CORS issues
      if (!response.ok && response.status === 0) {
        diagnostic.status = 'cors';
        diagnostic.corsInfo = await this.analyzeCORS(fullUrl);
      }

      this.logger.logNetworkDiagnostic(diagnostic);
      return diagnostic;

    } catch (error) {
      const responseTime = Date.now() - startTime;
      let status: NetworkDiagnostic['status'] = 'error';
      let errorMessage = error instanceof Error ? error.message : String(error);

      // Analyze error type
      if (errorMessage.includes('AbortError') || errorMessage.includes('timeout')) {
        status = 'timeout';
      } else if (errorMessage.includes('CORS') || errorMessage.includes('cross-origin')) {
        status = 'cors';
      } else if (errorMessage.includes('NetworkError') || errorMessage.includes('Failed to fetch')) {
        status = 'network';
      }

      const diagnostic: NetworkDiagnostic = {
        endpoint: fullUrl,
        method,
        status,
        responseTime,
        timestamp: new Date().toISOString(),
        error: errorMessage,
        networkInfo: this.getNetworkInfo(),
      };

      // Add CORS info if it's a CORS error
      if (status === 'cors') {
        diagnostic.corsInfo = await this.analyzeCORS(fullUrl);
      }

      this.logger.logNetworkDiagnostic(diagnostic);
      return diagnostic;
    }
  }

  /**
   * Analyze CORS configuration for an endpoint
   */
  private async analyzeCORS(endpoint: string): Promise<CORSInfo> {
    const origin = typeof window !== 'undefined' ? window.location.origin : 'unknown';
    
    const corsInfo: CORSInfo = {
      origin,
      preflightRequired: false,
    };

    try {
      // Test preflight request
      const preflightResponse = await fetch(endpoint, {
        method: 'OPTIONS',
        headers: {
          'Origin': origin,
          'Access-Control-Request-Method': 'POST',
          'Access-Control-Request-Headers': 'Content-Type',
        },
      });

      corsInfo.preflightStatus = preflightResponse.status;
      corsInfo.preflightRequired = true;

      // Extract CORS headers
      const allowOrigin = preflightResponse.headers.get('Access-Control-Allow-Origin');
      const allowMethods = preflightResponse.headers.get('Access-Control-Allow-Methods');
      const allowHeaders = preflightResponse.headers.get('Access-Control-Allow-Headers');

      if (allowOrigin) {
        corsInfo.allowedOrigins = [allowOrigin];
      }
      if (allowMethods) {
        corsInfo.allowedMethods = allowMethods.split(',').map(m => m.trim());
      }
      if (allowHeaders) {
        corsInfo.allowedHeaders = allowHeaders.split(',').map(h => h.trim());
      }

    } catch (error) {
      corsInfo.corsError = error instanceof Error ? error.message : String(error);
    }

    return corsInfo;
  }

  /**
   * Run a comprehensive network diagnostic test
   */
  public async runComprehensiveTest(): Promise<ComprehensiveNetworkReport> {
    const startTime = Date.now();
    
    // Define test suite
    const tests: NetworkTest[] = [
      {
        name: 'Backend Health Check',
        description: 'Test basic backend connectivity',
        endpoint: '/api/health',
        method: 'GET',
        expectedStatus: 200,
      },
      {
        name: 'Authentication Endpoint',
        description: 'Test authentication endpoint availability',
        endpoint: '/api/auth/status',
        method: 'GET',
      },
      {
        name: 'Chat Endpoint Options',
        description: 'Test chat endpoint CORS preflight',
        endpoint: '/api/chat/process',
        method: 'OPTIONS',
      },
      {
        name: 'Memory Endpoint Options',
        description: 'Test memory endpoint CORS preflight',
        endpoint: '/api/memory/query',
        method: 'OPTIONS',
      },
      {
        name: 'Plugin List Endpoint',
        description: 'Test plugin listing endpoint',
        endpoint: '/api/plugins/list',
        method: 'GET',
      },
      {
        name: 'System Metrics Endpoint',
        description: 'Test system metrics endpoint',
        endpoint: '/api/analytics/system-metrics',
        method: 'GET',
      },
    ];

    // Add fallback endpoint tests
    webUIConfig.fallbackBackendUrls.forEach((fallbackUrl, index) => {
      tests.push({
        name: `Fallback Backend ${index + 1}`,
        description: `Test fallback backend connectivity: ${fallbackUrl}`,
        endpoint: `${fallbackUrl}/api/health`,
        method: 'GET',
        expectedStatus: 200,
      });
    });

    // Run all tests
    const testResults: NetworkTestResult[] = [];
    let totalResponseTime = 0;
    let passedTests = 0;

    for (const test of tests) {
      try {
        const diagnostic = await this.testEndpointConnectivity(
          test.endpoint,
          test.method,
          test.timeout || 10000
        );

        const success = diagnostic.status === 'success' && 
          (test.expectedStatus ? diagnostic.statusCode === test.expectedStatus : true);

        if (success) {
          passedTests++;
        }

        totalResponseTime += diagnostic.responseTime;

        const recommendations = this.generateTestRecommendations(test, diagnostic);

        testResults.push({
          test,
          success,
          diagnostic,
          recommendations,
        });

      } catch (error) {
        // Create a failed diagnostic for the test
        const diagnostic: NetworkDiagnostic = {
          endpoint: test.endpoint,
          method: test.method,
          status: 'error',
          responseTime: 0,
          timestamp: new Date().toISOString(),
          error: error instanceof Error ? error.message : String(error),
          networkInfo: this.getNetworkInfo(),
        };

        testResults.push({
          test,
          success: false,
          diagnostic,
          recommendations: ['Test execution failed', 'Check network connectivity'],
        });
      }
    }

    // Calculate overall status
    const failureRate = (tests.length - passedTests) / tests.length;
    let overallStatus: ComprehensiveNetworkReport['overallStatus'];
    
    if (failureRate === 0) {
      overallStatus = 'healthy';
    } else if (failureRate < 0.3) {
      overallStatus = 'degraded';
    } else {
      overallStatus = 'critical';
    }

    // Generate overall recommendations
    const recommendations = this.generateOverallRecommendations(testResults, overallStatus);

    const report: ComprehensiveNetworkReport = {
      timestamp: new Date().toISOString(),
      overallStatus,
      summary: {
        totalTests: tests.length,
        passedTests,
        failedTests: tests.length - passedTests,
        averageResponseTime: totalResponseTime / tests.length,
      },
      testResults,
      systemInfo: this.getNetworkInfo(),
      recommendations,
    };

    // Log the comprehensive report
    this.logger.log('info', 'network', 'Comprehensive network diagnostic completed', {
      duration: Date.now() - startTime,
      overallStatus,
      summary: report.summary,
    });

    return report;
  }

  /**
   * Generate recommendations for individual test results
   */
  private generateTestRecommendations(test: NetworkTest, diagnostic: NetworkDiagnostic): string[] {
    const recommendations: string[] = [];

    if (!diagnostic.statusCode || diagnostic.statusCode >= 400) {
      recommendations.push(`Check if ${test.endpoint} is properly configured on the backend`);
    }

    if (diagnostic.status === 'timeout') {
      recommendations.push('Consider increasing timeout values');
      recommendations.push('Check backend service performance');
    }

    if (diagnostic.status === 'cors') {
      recommendations.push('Update CORS configuration to allow the current origin');
      recommendations.push('Verify preflight request handling');
    }

    if (diagnostic.status === 'network') {
      recommendations.push('Check network connectivity');
      recommendations.push('Verify backend service is running and accessible');
    }

    if (diagnostic.responseTime > 5000) {
      recommendations.push('Response time is slow - investigate backend performance');
    }

    return recommendations;
  }

  /**
   * Generate overall recommendations based on test results
   */
  private generateOverallRecommendations(
    testResults: NetworkTestResult[],
    overallStatus: ComprehensiveNetworkReport['overallStatus']
  ): string[] {
    const recommendations: string[] = [];
    const failedTests = testResults.filter(result => !result.success);
    const corsIssues = failedTests.filter(result => result.diagnostic.status === 'cors');
    const networkIssues = failedTests.filter(result => result.diagnostic.status === 'network');
    const timeoutIssues = failedTests.filter(result => result.diagnostic.status === 'timeout');

    if (overallStatus === 'critical') {
      recommendations.push('Critical network issues detected - immediate attention required');
      recommendations.push('Check if backend service is running and accessible');
    } else if (overallStatus === 'degraded') {
      recommendations.push('Some network issues detected - monitoring recommended');
    }

    if (corsIssues.length > 0) {
      recommendations.push('CORS configuration issues detected');
      recommendations.push('Update backend CORS settings to allow the current origin');
      recommendations.push('Verify preflight request handling for complex requests');
    }

    if (networkIssues.length > 0) {
      recommendations.push('Network connectivity issues detected');
      recommendations.push('Check internet connection and firewall settings');
      recommendations.push('Verify backend service accessibility');
    }

    if (timeoutIssues.length > 0) {
      recommendations.push('Timeout issues detected');
      recommendations.push('Consider increasing timeout configuration');
      recommendations.push('Investigate backend service performance');
    }

    // Check for fallback endpoint issues
    const fallbackTests = testResults.filter(result => 
      result.test.name.includes('Fallback Backend')
    );
    const failedFallbacks = fallbackTests.filter(result => !result.success);
    
    if (failedFallbacks.length === fallbackTests.length && fallbackTests.length > 0) {
      recommendations.push('All fallback endpoints are failing');
      recommendations.push('Review fallback endpoint configuration');
    }

    if (recommendations.length === 0) {
      recommendations.push('All network tests passed successfully');
      recommendations.push('Network connectivity is healthy');
    }

    return recommendations;
  }

  /**
   * Test specific endpoint with detailed analysis
   */
  public async testEndpointDetailed(endpoint: string): Promise<{
    connectivity: NetworkDiagnostic;
    corsAnalysis: CORSInfo;
    recommendations: string[];
  }> {
    const connectivity = await this.testEndpointConnectivity(endpoint);
    const corsAnalysis = await this.analyzeCORS(endpoint);
    
    const recommendations: string[] = [];
    
    if (connectivity.status !== 'success') {
      recommendations.push('Endpoint connectivity failed');
      recommendations.push('Check backend service status');
    }
    
    if (corsAnalysis.corsError) {
      recommendations.push('CORS configuration issues detected');
      recommendations.push('Update backend CORS settings');
    }
    
    if (connectivity.responseTime > 3000) {
      recommendations.push('Slow response time detected');
      recommendations.push('Investigate backend performance');
    }

    return {
      connectivity,
      corsAnalysis,
      recommendations,
    };
  }

  /**
   * Monitor network connectivity continuously
   */
  public startNetworkMonitoring(interval: number = 60000): () => void {
    const monitoringInterval = setInterval(async () => {
      try {
        const healthCheck = await this.testEndpointConnectivity('/api/health', 'GET', 5000);
        
        if (healthCheck.status !== 'success') {
          this.logger.log('warn', 'network', 'Network monitoring detected connectivity issue', {
            endpoint: healthCheck.endpoint,
            status: healthCheck.status,
            error: healthCheck.error,
          });
        }
      } catch (error) {
        this.logger.log('error', 'network', 'Network monitoring failed', undefined, undefined, undefined, error);
      }
    }, interval);

    this.logger.log('info', 'network', 'Network monitoring started', { interval });

    return () => {
      clearInterval(monitoringInterval);
      this.logger.log('info', 'network', 'Network monitoring stopped');
    };
  }
}

// Global network diagnostics instance
let networkDiagnostics: NetworkDiagnostics | null = null;

export function getNetworkDiagnostics(): NetworkDiagnostics {
  if (!networkDiagnostics) {
    networkDiagnostics = new NetworkDiagnostics();
  }
  return networkDiagnostics;
}

export function initializeNetworkDiagnostics(): NetworkDiagnostics {
  networkDiagnostics = new NetworkDiagnostics();
  return networkDiagnostics;
}

// Export types
export type {
  NetworkTest,
  NetworkTestResult,
  ComprehensiveNetworkReport,
};

export { NetworkDiagnostics };