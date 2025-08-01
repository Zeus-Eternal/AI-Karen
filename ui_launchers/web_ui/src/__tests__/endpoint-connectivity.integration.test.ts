/**
 * Integration tests for endpoint connectivity
 * Tests Web UI to backend communication across different environments
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ConfigManager } from '../lib/endpoint-config';
import { getNetworkDiagnostics } from '../lib/network-diagnostics';
import { getDiagnosticLogger } from '../lib/diagnostics';

// Mock fetch for controlled testing
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock performance.now
global.performance = {
  now: vi.fn(() => Date.now()),
} as any;

describe('Endpoint Connectivity Integration Tests', () => {
  let configManager: ConfigManager;
  let originalProcess: any;
  let originalWindow: any;

  beforeEach(() => {
    // Mock process.env
    originalProcess = global.process;
    global.process = {
      env: {
        KAREN_BACKEND_URL: 'http://localhost:8000',
        KAREN_ENVIRONMENT: 'local',
        KAREN_NETWORK_MODE: 'localhost',
        KAREN_FALLBACK_BACKEND_URLS: 'http://127.0.0.1:8000,http://localhost:8001',
        KAREN_HEALTH_CHECK_ENABLED: 'true',
      },
    } as any;

    // Mock window
    originalWindow = global.window;
    global.window = {
      location: {
        hostname: 'localhost',
        href: 'http://localhost:9002',
        origin: 'http://localhost:9002',
      },
    } as any;

    // Reset fetch mock
    mockFetch.mockReset();
    
    // Create fresh config manager
    configManager = new ConfigManager();
  });

  afterEach(() => {
    // Restore original globals
    global.process = originalProcess;
    global.window = originalWindow;
    vi.clearAllMocks();
  });

  describe('Backend Health Check Integration', () => {
    it('should successfully connect to backend health endpoint', async () => {
      // Mock successful health check response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map([
          ['content-type', 'application/json'],
        ]),
        json: async () => ({ status: 'healthy', timestamp: new Date().toISOString() }),
      });

      const results = await configManager.validateEndpoints();
      const primaryResult = results[0];

      expect(primaryResult.isValid).toBe(true);
      expect(primaryResult.endpoint).toBe('http://localhost:8000');
      expect(primaryResult.responseTime).toBeGreaterThanOrEqual(0);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/health',
        expect.objectContaining({
          method: 'GET',
          headers: { 'Accept': 'application/json' },
        })
      );
    });

    it('should handle backend unavailable scenario', async () => {
      // Mock network error (backend not running)
      mockFetch.mockRejectedValueOnce(new Error('Failed to fetch'));

      const results = await configManager.validateEndpoints();
      const primaryResult = results[0];

      expect(primaryResult.isValid).toBe(false);
      expect(primaryResult.error).toBe('Network error - unable to connect');
    });

    it('should handle backend returning error status', async () => {
      // Mock backend returning 500 error
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: new Map(),
      });

      const results = await configManager.validateEndpoints();
      const primaryResult = results[0];

      expect(primaryResult.isValid).toBe(false);
      expect(primaryResult.error).toBe('HTTP 500: Internal Server Error');
    });
  });

  describe('Authentication Endpoint Integration', () => {
    it('should successfully connect to authentication status endpoint', async () => {
      // Mock successful auth status response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map([
          ['content-type', 'application/json'],
          ['access-control-allow-origin', 'http://localhost:9002'],
        ]),
      });

      const networkDiagnostics = getNetworkDiagnostics();
      const result = await networkDiagnostics.testEndpointConnectivity('/api/auth/status');

      expect(result.status).toBe('success');
      expect(result.statusCode).toBe(200);
      expect(result.endpoint).toBe('http://localhost:8000/api/auth/status');
      expect(result.headers?.['access-control-allow-origin']).toBe('http://localhost:9002');
    });

    it('should handle authentication endpoint CORS issues', async () => {
      // Mock CORS error (status 0)
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 0,
        statusText: '',
        headers: new Map(),
      });

      // Mock CORS preflight analysis
      mockFetch.mockResolvedValueOnce({
        status: 200,
        headers: new Map([
          ['access-control-allow-origin', 'http://localhost:3000'], // Different origin
          ['access-control-allow-methods', 'GET, POST'],
        ]),
      });

      const networkDiagnostics = getNetworkDiagnostics();
      const result = await networkDiagnostics.testEndpointConnectivity('/api/auth/login', 'POST');

      expect(result.status).toBe('cors');
      expect(result.corsInfo).toBeDefined();
      expect(result.corsInfo?.origin).toBe('http://localhost:9002');
    });

    it('should handle authentication endpoint requiring credentials', async () => {
      // Mock 401 Unauthorized response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        headers: new Map([
          ['www-authenticate', 'Bearer'],
        ]),
      });

      const networkDiagnostics = getNetworkDiagnostics();
      const result = await networkDiagnostics.testEndpointConnectivity('/api/auth/protected');

      expect(result.status).toBe('error');
      expect(result.statusCode).toBe(401);
    });
  });

  describe('Fallback Endpoint Integration', () => {
    it('should test all fallback endpoints when primary fails', async () => {
      // Mock primary endpoint failure
      mockFetch.mockRejectedValueOnce(new Error('Connection refused'));
      
      // Mock first fallback success
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map(),
      });

      // Mock second fallback success
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map(),
      });

      const results = await configManager.validateEndpoints();

      expect(results).toHaveLength(3); // Primary + 2 fallbacks
      expect(results[0].isValid).toBe(false); // Primary failed
      expect(results[1].isValid).toBe(true);  // First fallback succeeded
      expect(results[2].isValid).toBe(true);  // Second fallback succeeded

      expect(results[1].endpoint).toBe('http://127.0.0.1:8000');
      expect(results[2].endpoint).toBe('http://localhost:8001');
    });

    it('should handle all endpoints failing', async () => {
      // Mock all endpoints failing
      mockFetch.mockRejectedValue(new Error('Network unreachable'));

      const results = await configManager.validateEndpoints();

      expect(results).toHaveLength(3);
      expect(results.every(result => !result.isValid)).toBe(true);
      expect(results.every(result => result.error === 'Network unreachable')).toBe(true);
    });
  });

  describe('Environment-Specific Integration Tests', () => {
    it('should handle localhost development environment', async () => {
      // Already configured for localhost in beforeEach
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map(),
      });

      const envInfo = configManager.getEnvironmentInfo();
      expect(envInfo.environment).toBe('local');
      expect(envInfo.networkMode).toBe('localhost');
      expect(envInfo.backendUrl).toBe('http://localhost:8000');

      const results = await configManager.validateEndpoints();
      expect(results[0].endpoint).toBe('http://localhost:8000');
    });

    it('should handle Docker container environment', async () => {
      // Mock Docker environment
      global.process.env.DOCKER_CONTAINER = 'true';
      global.process.env.KAREN_CONTAINER_BACKEND_HOST = 'backend-service';
      global.process.env.KAREN_CONTAINER_BACKEND_PORT = '8000';

      const dockerConfigManager = new ConfigManager();
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map(),
      });

      const envInfo = dockerConfigManager.getEnvironmentInfo();
      expect(envInfo.environment).toBe('docker');
      expect(envInfo.networkMode).toBe('container');
      expect(envInfo.backendUrl).toBe('http://backend-service:8000');

      const results = await dockerConfigManager.validateEndpoints();
      expect(results[0].endpoint).toBe('http://backend-service:8000');
    });

    it('should handle external IP environment', async () => {
      // Mock external IP environment
      global.window.location.hostname = '10.105.235.209';
      global.process.env.KAREN_EXTERNAL_HOST = '10.105.235.209';
      global.process.env.KAREN_EXTERNAL_BACKEND_PORT = '8000';

      const externalConfigManager = new ConfigManager();
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map(),
      });

      const envInfo = externalConfigManager.getEnvironmentInfo();
      expect(envInfo.networkMode).toBe('external');
      expect(envInfo.backendUrl).toBe('http://10.105.235.209:8000');

      const results = await externalConfigManager.validateEndpoints();
      expect(results[0].endpoint).toBe('http://10.105.235.209:8000');
    });
  });

  describe('Comprehensive Network Testing Integration', () => {
    it('should run comprehensive test across multiple endpoints', async () => {
      // Mock responses for all test endpoints
      const mockResponses = [
        // Backend Health Check
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // Authentication Endpoint
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // Chat Endpoint Options
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // Memory Endpoint Options
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // Plugin List Endpoint
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // System Metrics Endpoint
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // Fallback Backend 1
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // Fallback Backend 2
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
      ];

      mockResponses.forEach(response => {
        mockFetch.mockResolvedValueOnce(response);
      });

      const networkDiagnostics = getNetworkDiagnostics();
      const report = await networkDiagnostics.runComprehensiveTest();

      expect(report.overallStatus).toBe('healthy');
      expect(report.summary.totalTests).toBeGreaterThan(6); // At least 6 main tests + fallbacks
      expect(report.summary.passedTests).toBe(report.summary.totalTests);
      expect(report.summary.failedTests).toBe(0);
      expect(report.recommendations).toContain('All network tests passed successfully');
    });

    it('should handle mixed success/failure scenarios', async () => {
      // Mock mixed responses - some succeed, some fail
      const mockResponses = [
        // Backend Health Check - success
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // Authentication Endpoint - fail
        new Error('Connection refused'),
        // Chat Endpoint Options - success
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // Memory Endpoint Options - fail
        new Error('Timeout'),
        // Plugin List Endpoint - success
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // System Metrics Endpoint - success
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // Fallback Backend 1 - success
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
        // Fallback Backend 2 - success
        { ok: true, status: 200, statusText: 'OK', headers: new Map() },
      ];

      mockResponses.forEach(response => {
        if (response instanceof Error) {
          mockFetch.mockRejectedValueOnce(response);
        } else {
          mockFetch.mockResolvedValueOnce(response);
        }
      });

      const networkDiagnostics = getNetworkDiagnostics();
      const report = await networkDiagnostics.runComprehensiveTest();

      expect(report.overallStatus).toBe('degraded');
      expect(report.summary.failedTests).toBeGreaterThan(0);
      expect(report.summary.passedTests).toBeGreaterThan(0);
      expect(report.recommendations).toContain('Some network issues detected - monitoring recommended');
    });
  });

  describe('Authentication Flow Integration', () => {
    it('should test complete authentication flow endpoints', async () => {
      const authEndpoints = [
        '/api/auth/status',
        '/api/auth/login',
        '/api/auth/logout',
        '/api/auth/refresh',
      ];

      // Mock successful responses for all auth endpoints
      authEndpoints.forEach(() => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: new Map([
            ['content-type', 'application/json'],
            ['access-control-allow-origin', 'http://localhost:9002'],
          ]),
        });
      });

      const networkDiagnostics = getNetworkDiagnostics();
      const results = [];

      for (const endpoint of authEndpoints) {
        const result = await networkDiagnostics.testEndpointConnectivity(endpoint);
        results.push(result);
      }

      expect(results.every(result => result.status === 'success')).toBe(true);
      expect(results.every(result => result.statusCode === 200)).toBe(true);
      expect(results.every(result => 
        result.headers?.['access-control-allow-origin'] === 'http://localhost:9002'
      )).toBe(true);
    });

    it('should handle authentication flow with different endpoint configurations', async () => {
      // Test with different backend configurations
      const configurations = [
        { backendUrl: 'http://localhost:8000', expectedAuth: 'http://localhost:8000/api/auth' },
        { backendUrl: 'http://127.0.0.1:8000', expectedAuth: 'http://127.0.0.1:8000/api/auth' },
        { backendUrl: 'http://backend:8000', expectedAuth: 'http://backend:8000/api/auth' },
      ];

      for (const config of configurations) {
        configManager.updateConfiguration({ backendUrl: config.backendUrl });
        
        expect(configManager.getAuthEndpoint()).toBe(config.expectedAuth);
        expect(configManager.getChatEndpoint()).toBe(`${config.backendUrl}/api/chat`);
        expect(configManager.getMemoryEndpoint()).toBe(`${config.backendUrl}/api/memory`);
        expect(configManager.getPluginsEndpoint()).toBe(`${config.backendUrl}/api/plugins`);
      }
    });
  });

  describe('Error Recovery Integration', () => {
    it('should demonstrate endpoint failover behavior', async () => {
      // Mock primary endpoint timeout
      mockFetch.mockImplementationOnce(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), 100)
        )
      );

      // Mock fallback endpoints success
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map(),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map(),
      });

      const results = await configManager.validateEndpoints();

      // Primary should fail, fallbacks should succeed
      expect(results[0].isValid).toBe(false);
      expect(results[0].error).toContain('timeout');
      expect(results[1].isValid).toBe(true);
      expect(results[2].isValid).toBe(true);

      // Verify fallback URLs are correct
      expect(results[1].endpoint).toBe('http://127.0.0.1:8000');
      expect(results[2].endpoint).toBe('http://localhost:8001');
    });

    it('should handle gradual service recovery', async () => {
      // First test - all endpoints fail
      mockFetch.mockRejectedValue(new Error('Service unavailable'));

      let results = await configManager.validateEndpoints();
      expect(results.every(result => !result.isValid)).toBe(true);

      // Clear validation cache to simulate time passing
      configManager.clearValidationCache();

      // Second test - primary recovers
      mockFetch.mockReset();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map(),
      });
      mockFetch.mockRejectedValueOnce(new Error('Still down'));
      mockFetch.mockRejectedValueOnce(new Error('Still down'));

      results = await configManager.validateEndpoints();
      expect(results[0].isValid).toBe(true);  // Primary recovered
      expect(results[1].isValid).toBe(false); // Fallbacks still down
      expect(results[2].isValid).toBe(false);
    });
  });

  describe('Performance Integration', () => {
    it('should measure and report response times accurately', async () => {
      // Mock performance.now to return predictable values
      const mockPerformanceNow = vi.mocked(performance.now);
      mockPerformanceNow
        .mockReturnValueOnce(1000)  // Start time
        .mockReturnValueOnce(1250)  // End time (250ms response)
        .mockReturnValueOnce(2000)  // Start time for second call
        .mockReturnValueOnce(2100); // End time (100ms response)

      // Mock responses
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map(),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        headers: new Map(),
      });

      const results = await configManager.validateEndpoints();

      expect(results[0].responseTime).toBe(250);
      expect(results[1].responseTime).toBe(100);
    });

    it('should handle concurrent endpoint validation', async () => {
      // Mock multiple successful responses
      for (let i = 0; i < 6; i++) {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          headers: new Map(),
        });
      }

      const startTime = Date.now();
      
      // Run multiple validations concurrently
      const promises = [
        configManager.validateEndpoints(),
        configManager.validateEndpoints(),
      ];

      const results = await Promise.all(promises);
      const endTime = Date.now();

      // Should complete in reasonable time (concurrent, not sequential)
      expect(endTime - startTime).toBeLessThan(1000);
      
      // Both should succeed
      expect(results[0][0].isValid).toBe(true);
      expect(results[1][0].isValid).toBe(true);
    });
  });
});