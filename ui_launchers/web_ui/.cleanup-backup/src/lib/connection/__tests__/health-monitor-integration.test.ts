/**
 * Integration tests for HealthMonitor
 * 
 * Tests health check functionality with real backend endpoints,
 * monitoring behavior, failover logic, and event handling.
 * 
 * Requirements: 5.1, 5.4
 */

import { describe, it, expect, beforeEach, afterEach, vi, beforeAll, afterAll } from 'vitest';
import {
  HealthMonitor,
  getHealthMonitor,
  initializeHealthMonitor,
  HealthEventType,
  type HealthCheckResult,
  type HealthEvent,
} from '../health-monitor';
import { getConnectionManager } from '../connection-manager';
import { getEnvironmentConfigManager } from '../../config/index';

// Mock server setup for integration tests
let mockServer: any = null;
const TEST_PORT = 8999;
const TEST_BASE_URL = `http://localhost:${TEST_PORT}`;

// Simple mock server implementation
class MockHealthServer {
  private server: any = null;
  private responses: Map<string, { status: number; body: any; delay?: number }> = new Map();

  constructor(private port: number) {}

  setResponse(path: string, status: number, body: any, delay?: number) {
    this.responses.set(path, { status, body, delay });
  }

  async start() {
    // Use a simple HTTP server for testing
    const http = await import('http');
    
    this.server = http.createServer((req, res) => {
      const url = req.url || '';
      const response = this.responses.get(url);
      
      if (response) {
        const { status, body, delay = 0 } = response;
        
        setTimeout(() => {
          res.writeHead(status, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify(body));
        }, delay);
      } else {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Not found' }));
      }
    });

    return new Promise<void>((resolve, reject) => {
      this.server.listen(this.port, (err: any) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  async stop() {
    if (this.server) {
      return new Promise<void>((resolve) => {
        this.server.close(() => resolve());
      });
    }
  }
}

describe('HealthMonitor Integration Tests', () => {
  let healthMonitor: HealthMonitor;
  let mockServer: MockHealthServer;

  beforeAll(async () => {
    // Start mock server
    mockServer = new MockHealthServer(TEST_PORT);
    await mockServer.start();
  });

  afterAll(async () => {
    // Stop mock server
    if (mockServer) {
      await mockServer.stop();
    }
  });

  beforeEach(() => {
    // Initialize health monitor with test configuration
    healthMonitor = new HealthMonitor({
      checkInterval: 1000, // 1 second for faster tests
      maxConsecutiveFailures: 2,
      failoverEnabled: true,
      healthCheckTimeout: 5000,
      endpoints: [
        `${TEST_BASE_URL}`,
        `${TEST_BASE_URL.replace('8999', '9000')}`, // Fallback endpoint
      ],
    });

    // Add test endpoints
    healthMonitor.addEndpoint(`${TEST_BASE_URL}`, 1, true);
    healthMonitor.addEndpoint(`${TEST_BASE_URL.replace('8999', '9000')}`, 2, false);

    vi.clearAllTimers();
    vi.useFakeTimers();
  });

  afterEach(() => {
    healthMonitor.stopMonitoring();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe('Real Health Check Integration', () => {
    it('should perform successful health check against mock server', async () => {
      // Setup mock server response
      mockServer.setResponse('/health', 200, { status: 'healthy' });

      const result = await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      
      expect(result.isHealthy).toBe(true);
      expect(result.endpoint).toBe(`${TEST_BASE_URL}`);
      expect(result.responseTime).toBeGreaterThan(0);
      expect(result.error).toBeUndefined();
    });

    it('should handle failed health check against unavailable endpoint', async () => {
      const result = await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL.replace('8999', '9999')}`);
      
      expect(result.isHealthy).toBe(false);
      expect(result.endpoint).toBe(`${TEST_BASE_URL.replace('8999', '9999')}`);
      expect(result.error).toBeDefined();
    });

    it('should handle slow health check responses', async () => {
      // Setup slow response
      mockServer.setResponse('/health', 200, { status: 'healthy' }, 100);

      const startTime = Date.now();
      const result = await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      const endTime = Date.now();
      
      expect(result.isHealthy).toBe(true);
      expect(endTime - startTime).toBeGreaterThanOrEqual(100);
      expect(result.responseTime).toBeGreaterThanOrEqual(100);
    });

    it('should handle server error responses', async () => {
      // Setup server error response
      mockServer.setResponse('/health', 500, { error: 'Internal server error' });

      const result = await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      
      expect(result.isHealthy).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('Monitoring Integration', () => {
    it('should perform periodic health checks when monitoring is active', async () => {
      // Setup successful responses
      mockServer.setResponse('/health', 200, { status: 'healthy' });

      const healthCheckSpy = vi.spyOn(healthMonitor, 'checkEndpointHealth');
      
      healthMonitor.startMonitoring();
      
      // Fast-forward time to trigger periodic checks
      vi.advanceTimersByTime(1000); // First interval
      await vi.runAllTimersAsync();
      
      vi.advanceTimersByTime(1000); // Second interval
      await vi.runAllTimersAsync();
      
      // Should have performed initial check + 2 periodic checks for each endpoint
      expect(healthCheckSpy).toHaveBeenCalledTimes(6); // 2 endpoints * 3 checks
    });

    it('should stop periodic health checks when monitoring is stopped', async () => {
      mockServer.setResponse('/health', 200, { status: 'healthy' });

      const healthCheckSpy = vi.spyOn(healthMonitor, 'checkEndpointHealth');
      
      healthMonitor.startMonitoring();
      vi.advanceTimersByTime(1000);
      await vi.runAllTimersAsync();
      
      healthMonitor.stopMonitoring();
      
      // Clear previous calls
      healthCheckSpy.mockClear();
      
      // Advance time - should not trigger more checks
      vi.advanceTimersByTime(5000);
      await vi.runAllTimersAsync();
      
      expect(healthCheckSpy).not.toHaveBeenCalled();
    });
  });

  describe('Failover Integration', () => {
    it('should perform automatic failover when primary endpoint fails', async () => {
      const eventListener = vi.fn();
      healthMonitor.addEventListener(HealthEventType.ENDPOINT_FAILOVER, eventListener);

      // Primary endpoint fails, fallback succeeds
      mockServer.setResponse('/health', 500, { error: 'Server error' });

      // Trigger consecutive failures to cause failover
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      
      // Should failover to next endpoint (even though it's not available in this test)
      const activeEndpoint = healthMonitor.getActiveEndpoint();
      expect(activeEndpoint).not.toBe(`${TEST_BASE_URL}`);
      
      // Should emit failover event
      expect(eventListener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: HealthEventType.ENDPOINT_FAILOVER,
          data: expect.objectContaining({
            from: `${TEST_BASE_URL}`,
          }),
        })
      );
    });

    it('should recover from failover when primary endpoint becomes healthy', async () => {
      // First, cause a failover
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL.replace('8999', '9999')}`); // Non-existent
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL.replace('8999', '9999')}`);
      
      // Now make primary healthy again
      mockServer.setResponse('/health', 200, { status: 'healthy' });
      
      // Check primary endpoint health
      const result = await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      expect(result.isHealthy).toBe(true);
      
      // Health should be restored
      const health = healthMonitor.getEndpointHealth(`${TEST_BASE_URL}`);
      expect(health?.isHealthy).toBe(true);
      expect(health?.consecutiveFailures).toBe(0);
    });
  });

  describe('Event Integration', () => {
    it('should emit events during real health checks', async () => {
      const successListener = vi.fn();
      const failureListener = vi.fn();
      
      healthMonitor.addEventListener(HealthEventType.HEALTH_CHECK_SUCCESS, successListener);
      healthMonitor.addEventListener(HealthEventType.HEALTH_CHECK_FAILURE, failureListener);

      // Test successful health check
      mockServer.setResponse('/health', 200, { status: 'healthy' });
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      
      expect(successListener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: HealthEventType.HEALTH_CHECK_SUCCESS,
          endpoint: `${TEST_BASE_URL}`,
        })
      );

      // Test failed health check
      mockServer.setResponse('/health', 500, { error: 'Server error' });
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      
      expect(failureListener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: HealthEventType.HEALTH_CHECK_FAILURE,
          endpoint: `${TEST_BASE_URL}`,
        })
      );
    });

    it('should emit monitoring start/stop events', () => {
      const startListener = vi.fn();
      const stopListener = vi.fn();
      
      healthMonitor.addEventListener(HealthEventType.MONITORING_STARTED, startListener);
      healthMonitor.addEventListener(HealthEventType.MONITORING_STOPPED, stopListener);

      healthMonitor.startMonitoring();
      expect(startListener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: HealthEventType.MONITORING_STARTED,
        })
      );

      healthMonitor.stopMonitoring();
      expect(stopListener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: HealthEventType.MONITORING_STOPPED,
        })
      );
    });
  });

  describe('Health Metrics Integration', () => {
    it('should track accurate health metrics during real checks', async () => {
      // Perform mix of successful and failed checks
      mockServer.setResponse('/health', 200, { status: 'healthy' });
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      
      mockServer.setResponse('/health', 500, { error: 'Server error' });
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      
      const health = healthMonitor.getEndpointHealth(`${TEST_BASE_URL}`);
      expect(health?.totalChecks).toBe(3);
      expect(health?.successfulChecks).toBe(2);
      expect(health?.failedChecks).toBe(1);
      expect(health?.uptime).toBeCloseTo(66.67, 1); // 2/3 * 100
    });

    it('should provide accurate health summary', async () => {
      // Setup one healthy, one unhealthy endpoint
      mockServer.setResponse('/health', 200, { status: 'healthy' });
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      
      // Second endpoint will fail (doesn't exist)
      await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL.replace('8999', '9000')}`);
      
      const summary = healthMonitor.getHealthSummary();
      expect(summary.totalEndpoints).toBe(2);
      expect(summary.healthyEndpoints).toBe(1);
      expect(summary.unhealthyEndpoints).toBe(1);
    });
  });

  describe('Configuration Integration', () => {
    it('should respect timeout configuration during health checks', async () => {
      // Setup very slow response
      mockServer.setResponse('/health', 200, { status: 'healthy' }, 2000);

      // Configure short timeout
      const fastMonitor = new HealthMonitor({
        healthCheckTimeout: 100,
        endpoints: [`${TEST_BASE_URL}`],
      });
      fastMonitor.addEndpoint(`${TEST_BASE_URL}`, 1, true);

      const startTime = Date.now();
      const result = await fastMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      const endTime = Date.now();
      
      // Should timeout quickly
      expect(result.isHealthy).toBe(false);
      expect(endTime - startTime).toBeLessThan(1000); // Much less than 2000ms delay
    });

    it('should update configuration and restart monitoring', async () => {
      mockServer.setResponse('/health', 200, { status: 'healthy' });

      healthMonitor.startMonitoring();
      expect(healthMonitor.isMonitoringActive()).toBe(true);
      
      // Update configuration
      healthMonitor.updateConfig({ checkInterval: 2000 });
      
      // Should still be monitoring with new config
      expect(healthMonitor.isMonitoringActive()).toBe(true);
      expect(healthMonitor.getConfig().checkInterval).toBe(2000);
    });
  });

  describe('Error Recovery Integration', () => {
    it('should handle network errors gracefully', async () => {
      // Test with completely invalid URL
      const result = await healthMonitor.checkEndpointHealth('http://invalid-domain-that-does-not-exist.com');
      
      expect(result.isHealthy).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.responseTime).toBeGreaterThan(0);
    });

    it('should handle malformed responses gracefully', async () => {
      // Setup malformed response
      const http = await import('http');
      const malformedServer = http.createServer((req, res) => {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end('invalid json{');
      });

      const malformedPort = 8998;
      await new Promise<void>((resolve) => {
        malformedServer.listen(malformedPort, () => resolve());
      });

      try {
        const result = await healthMonitor.checkEndpointHealth(`http://localhost:${malformedPort}`);
        
        // Should still complete the health check
        expect(result.endpoint).toBe(`http://localhost:${malformedPort}`);
        expect(result.responseTime).toBeGreaterThan(0);
      } finally {
        await new Promise<void>((resolve) => {
          malformedServer.close(() => resolve());
        });
      }
    });
  });

  describe('Concurrent Operations Integration', () => {
    it('should handle concurrent health checks correctly', async () => {
      mockServer.setResponse('/health', 200, { status: 'healthy' }, 50);

      // Perform multiple concurrent health checks
      const promises = Array.from({ length: 5 }, () =>
        healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`)
      );

      const results = await Promise.all(promises);
      
      // All should succeed
      results.forEach(result => {
        expect(result.isHealthy).toBe(true);
        expect(result.responseTime).toBeGreaterThanOrEqual(50);
      });

      // Health metrics should reflect all checks
      const health = healthMonitor.getEndpointHealth(`${TEST_BASE_URL}`);
      expect(health?.totalChecks).toBe(5);
      expect(health?.successfulChecks).toBe(5);
    });

    it('should handle monitoring during manual health checks', async () => {
      mockServer.setResponse('/health', 200, { status: 'healthy' });

      // Start monitoring
      healthMonitor.startMonitoring();
      
      // Perform manual health check while monitoring is active
      const manualResult = await healthMonitor.checkEndpointHealth(`${TEST_BASE_URL}`);
      expect(manualResult.isHealthy).toBe(true);
      
      // Advance time for periodic check
      vi.advanceTimersByTime(1000);
      await vi.runAllTimersAsync();
      
      // Should have multiple checks recorded
      const health = healthMonitor.getEndpointHealth(`${TEST_BASE_URL}`);
      expect(health?.totalChecks).toBeGreaterThan(1);
    });
  });
});