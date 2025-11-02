/**
 * Unit tests for HealthMonitor
 * 
 * Tests health check functionality, monitoring, failover logic,
 * and event handling.
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { HealthMonitor, getHealthMonitor, initializeHealthMonitor, HealthEventType } from '../health-monitor';

// Mock the connection manager
const mockConnectionManager = {
  makeRequest: vi.fn(),
};

vi.mock('../connection-manager', () => ({
  getConnectionManager: vi.fn(() => mockConnectionManager),
}));

// Mock the timeout manager
vi.mock('../timeout-manager', () => ({
  getTimeoutManager: vi.fn(() => ({
    getTimeout: vi.fn(() => 10000),
  })),
  OperationType: {
    HEALTH_CHECK: 'healthCheck',
  },
}));

// Mock the environment config manager
vi.mock('../../config', () => ({
  getEnvironmentConfigManager: vi.fn(() => ({
    getBackendConfig: vi.fn(() => ({
      primaryUrl: 'http://localhost:8000',
      fallbackUrls: ['http://localhost:8001', 'http://localhost:8002'],
    })),
  })),
}));

describe('HealthMonitor', () => {
  let healthMonitor: HealthMonitor;

  beforeEach(() => {
    healthMonitor = new HealthMonitor();
    mockConnectionManager.makeRequest.mockClear();
    vi.clearAllTimers();
    vi.useFakeTimers();

  afterEach(() => {
    healthMonitor.stopMonitoring();
    vi.useRealTimers();
    vi.restoreAllMocks();

  describe('Initialization', () => {
    it('should initialize with default configuration', () => {
      const config = healthMonitor.getConfig();
      
      expect(config.checkInterval).toBe(30000);
      expect(config.maxConsecutiveFailures).toBe(3);
      expect(config.failoverEnabled).toBe(true);
      expect(config.healthCheckTimeout).toBe(10000);

    it('should initialize with custom configuration', () => {
      const customConfig = {
        checkInterval: 60000,
        maxConsecutiveFailures: 5,
        failoverEnabled: false,
      };
      
      const monitor = new HealthMonitor(customConfig);
      const config = monitor.getConfig();
      
      expect(config.checkInterval).toBe(60000);
      expect(config.maxConsecutiveFailures).toBe(5);
      expect(config.failoverEnabled).toBe(false);

    it('should initialize endpoints from configuration', () => {
      const endpoints = healthMonitor.getAllEndpoints();
      
      expect(endpoints).toHaveLength(3);
      expect(endpoints[0].url).toBe('http://localhost:8000');
      expect(endpoints[0].priority).toBe(1);
      expect(endpoints[0].isActive).toBe(true);
      
      expect(endpoints[1].url).toBe('http://localhost:8001');
      expect(endpoints[1].priority).toBe(2);
      expect(endpoints[1].isActive).toBe(false);

    it('should set active endpoint to primary', () => {
      expect(healthMonitor.getActiveEndpoint()).toBe('http://localhost:8000');


  describe('Endpoint Management', () => {
    it('should add endpoint', () => {
      healthMonitor.addEndpoint('http://localhost:9000', 10, false);
      
      const endpoints = healthMonitor.getAllEndpoints();
      const newEndpoint = endpoints.find(ep => ep.url === 'http://localhost:9000');
      
      expect(newEndpoint).toBeDefined();
      expect(newEndpoint!.priority).toBe(10);
      expect(newEndpoint!.isActive).toBe(false);

    it('should remove endpoint', () => {
      healthMonitor.removeEndpoint('http://localhost:8001');
      
      const endpoints = healthMonitor.getAllEndpoints();
      expect(endpoints.find(ep => ep.url === 'http://localhost:8001')).toBeUndefined();

    it('should update active endpoint when removing active endpoint', () => {
      // Remove the active endpoint
      healthMonitor.removeEndpoint('http://localhost:8000');
      
      // Should failover to next healthy endpoint
      const activeEndpoint = healthMonitor.getActiveEndpoint();
      expect(activeEndpoint).toBe('http://localhost:8001');

    it('should get endpoint health', () => {
      const health = healthMonitor.getEndpointHealth('http://localhost:8000');
      
      expect(health).toBeDefined();
      expect(health!.isHealthy).toBe(true);
      expect(health!.totalChecks).toBe(0);
      expect(health!.uptime).toBe(100);


  describe('Health Checks', () => {
    it('should perform successful health check', async () => {
      mockConnectionManager.makeRequest.mockResolvedValue({
        status: 200,
        data: { status: 'healthy' },

      const result = await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      expect(result.isHealthy).toBe(true);
      expect(result.endpoint).toBe('http://localhost:8000');
      expect(result.responseTime).toBeGreaterThanOrEqual(0);
      expect(result.error).toBeUndefined();
      
      expect(mockConnectionManager.makeRequest).toHaveBeenCalledWith(
        'http://localhost:8000/health',
        { method: 'GET' },
        {
          timeout: 10000,
          retryAttempts: 0,
          circuitBreakerEnabled: false,
        }
      );

    it('should handle failed health check', async () => {
      const error = new Error('Connection failed');
      mockConnectionManager.makeRequest.mockRejectedValue(error);

      const result = await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      expect(result.isHealthy).toBe(false);
      expect(result.endpoint).toBe('http://localhost:8000');
      expect(result.error).toBe('Connection failed');
      expect(result.details).toBe(error);

    it('should handle health check for non-existent endpoint', async () => {
      const result = await healthMonitor.checkEndpointHealth('http://localhost:9999');
      
      expect(result.isHealthy).toBe(false);
      expect(result.error).toBe('Endpoint not found');

    it('should check all endpoints', async () => {
      mockConnectionManager.makeRequest
        .mockResolvedValueOnce({ status: 200 }) // First endpoint succeeds
        .mockRejectedValueOnce(new Error('Failed')) // Second endpoint fails
        .mockResolvedValueOnce({ status: 200 }); // Third endpoint succeeds

      const results = await healthMonitor.checkAllEndpoints();
      
      expect(results).toHaveLength(3);
      expect(results[0].isHealthy).toBe(true);
      expect(results[1].isHealthy).toBe(false);
      expect(results[2].isHealthy).toBe(true);


  describe('Health Metrics', () => {
    it('should update health metrics on successful check', async () => {
      mockConnectionManager.makeRequest.mockResolvedValue({ status: 200 });

      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      const health = healthMonitor.getEndpointHealth('http://localhost:8000');
      expect(health!.totalChecks).toBe(1);
      expect(health!.successfulChecks).toBe(1);
      expect(health!.failedChecks).toBe(0);
      expect(health!.consecutiveFailures).toBe(0);
      expect(health!.isHealthy).toBe(true);
      expect(health!.uptime).toBe(100);

    it('should update health metrics on failed check', async () => {
      mockConnectionManager.makeRequest.mockRejectedValue(new Error('Failed'));

      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      const health = healthMonitor.getEndpointHealth('http://localhost:8000');
      expect(health!.totalChecks).toBe(1);
      expect(health!.successfulChecks).toBe(0);
      expect(health!.failedChecks).toBe(1);
      expect(health!.consecutiveFailures).toBe(1);
      expect(health!.isHealthy).toBe(true); // Still healthy until threshold reached
      expect(health!.uptime).toBe(0);

    it('should mark endpoint as unhealthy after consecutive failures', async () => {
      mockConnectionManager.makeRequest.mockRejectedValue(new Error('Failed'));

      // Perform 3 consecutive failed checks (default threshold)
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      const health = healthMonitor.getEndpointHealth('http://localhost:8000');
      expect(health!.consecutiveFailures).toBe(3);
      expect(health!.isHealthy).toBe(false);

    it('should reset consecutive failures on successful check', async () => {
      mockConnectionManager.makeRequest
        .mockRejectedValueOnce(new Error('Failed'))
        .mockRejectedValueOnce(new Error('Failed'))
        .mockResolvedValueOnce({ status: 200 });

      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      const health = healthMonitor.getEndpointHealth('http://localhost:8000');
      expect(health!.consecutiveFailures).toBe(0);
      expect(health!.isHealthy).toBe(true);


  describe('Failover Logic', () => {
    it('should perform automatic failover when active endpoint fails', async () => {
      mockConnectionManager.makeRequest.mockRejectedValue(new Error('Failed'));

      // Trigger consecutive failures to cause failover
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      // Should failover to next healthy endpoint
      expect(healthMonitor.getActiveEndpoint()).toBe('http://localhost:8001');

    it('should not perform failover when disabled', async () => {
      healthMonitor.updateConfig({ failoverEnabled: false });
      mockConnectionManager.makeRequest.mockRejectedValue(new Error('Failed'));

      // Trigger consecutive failures
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      // Should remain on original endpoint
      expect(healthMonitor.getActiveEndpoint()).toBe('http://localhost:8000');

    it('should force failover to specific endpoint', () => {
      const success = healthMonitor.forceFailover('http://localhost:8002');
      
      expect(success).toBe(true);
      expect(healthMonitor.getActiveEndpoint()).toBe('http://localhost:8002');

    it('should fail to force failover to non-existent endpoint', () => {
      const success = healthMonitor.forceFailover('http://localhost:9999');
      
      expect(success).toBe(false);
      expect(healthMonitor.getActiveEndpoint()).toBe('http://localhost:8000');


  describe('Monitoring', () => {
    it('should start monitoring', () => {
      expect(healthMonitor.isMonitoringActive()).toBe(false);
      
      healthMonitor.startMonitoring();
      
      expect(healthMonitor.isMonitoringActive()).toBe(true);

    it('should stop monitoring', () => {
      healthMonitor.startMonitoring();
      expect(healthMonitor.isMonitoringActive()).toBe(true);
      
      healthMonitor.stopMonitoring();
      
      expect(healthMonitor.isMonitoringActive()).toBe(false);

    it('should perform periodic health checks when monitoring', async () => {
      mockConnectionManager.makeRequest.mockResolvedValue({ status: 200 });
      
      healthMonitor.startMonitoring();
      
      // Fast-forward time to trigger health checks
      vi.advanceTimersByTime(30000); // Default check interval
      
      // Should have performed health checks on all endpoints (initial + periodic)
      expect(mockConnectionManager.makeRequest).toHaveBeenCalledTimes(6); // 3 endpoints * 2 checks

    it('should update configuration and restart monitoring', () => {
      healthMonitor.startMonitoring();
      
      healthMonitor.updateConfig({ checkInterval: 60000 });
      
      expect(healthMonitor.getConfig().checkInterval).toBe(60000);
      expect(healthMonitor.isMonitoringActive()).toBe(true);


  describe('Event Handling', () => {
    it('should emit health check success events', async () => {
      const eventListener = vi.fn();
      healthMonitor.addEventListener(HealthEventType.HEALTH_CHECK_SUCCESS, eventListener);
      
      mockConnectionManager.makeRequest.mockResolvedValue({ status: 200 });
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      expect(eventListener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: HealthEventType.HEALTH_CHECK_SUCCESS,
          endpoint: 'http://localhost:8000',
        })
      );

    it('should emit health check failure events', async () => {
      const eventListener = vi.fn();
      healthMonitor.addEventListener(HealthEventType.HEALTH_CHECK_FAILURE, eventListener);
      
      mockConnectionManager.makeRequest.mockRejectedValue(new Error('Failed'));
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      expect(eventListener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: HealthEventType.HEALTH_CHECK_FAILURE,
          endpoint: 'http://localhost:8000',
        })
      );

    it('should emit failover events', async () => {
      const eventListener = vi.fn();
      healthMonitor.addEventListener(HealthEventType.ENDPOINT_FAILOVER, eventListener);
      
      mockConnectionManager.makeRequest.mockRejectedValue(new Error('Failed'));
      
      // Trigger failover
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      expect(eventListener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: HealthEventType.ENDPOINT_FAILOVER,
          endpoint: 'http://localhost:8001',
          data: expect.objectContaining({
            from: 'http://localhost:8000',
            to: 'http://localhost:8001',
          }),
        })
      );

    it('should remove event listeners', async () => {
      const eventListener = vi.fn();
      healthMonitor.addEventListener(HealthEventType.HEALTH_CHECK_SUCCESS, eventListener);
      healthMonitor.removeEventListener(HealthEventType.HEALTH_CHECK_SUCCESS, eventListener);
      
      mockConnectionManager.makeRequest.mockResolvedValue({ status: 200 });
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      expect(eventListener).not.toHaveBeenCalled();


  describe('Health Summary', () => {
    it('should provide health summary', () => {
      const summary = healthMonitor.getHealthSummary();
      
      expect(summary.activeEndpoint).toBe('http://localhost:8000');
      expect(summary.totalEndpoints).toBe(3);
      expect(summary.healthyEndpoints).toBe(3);
      expect(summary.unhealthyEndpoints).toBe(0);
      expect(summary.overallUptime).toBe(100);
      expect(summary.isMonitoring).toBe(false);

    it('should update health summary after health checks', async () => {
      mockConnectionManager.makeRequest
        .mockResolvedValueOnce({ status: 200 })
        .mockRejectedValueOnce(new Error('Failed'))
        .mockResolvedValueOnce({ status: 200 });

      await healthMonitor.checkAllEndpoints();
      
      const summary = healthMonitor.getHealthSummary();
      // All endpoints are still healthy after just one failure (threshold is 3)
      expect(summary.healthyEndpoints).toBe(3);
      expect(summary.unhealthyEndpoints).toBe(0);
      expect(summary.overallUptime).toBeLessThan(100); // But uptime is affected


  describe('Statistics Reset', () => {
    it('should reset health statistics', async () => {
      mockConnectionManager.makeRequest.mockRejectedValue(new Error('Failed'));
      
      // Generate some statistics
      await healthMonitor.checkEndpointHealth('http://localhost:8000');
      
      let health = healthMonitor.getEndpointHealth('http://localhost:8000');
      expect(health!.totalChecks).toBe(1);
      expect(health!.failedChecks).toBe(1);
      
      // Reset statistics
      healthMonitor.resetHealthStatistics();
      
      health = healthMonitor.getEndpointHealth('http://localhost:8000');
      expect(health!.totalChecks).toBe(0);
      expect(health!.failedChecks).toBe(0);
      expect(health!.isHealthy).toBe(true);
      expect(health!.uptime).toBe(100);


  describe('Singleton Pattern', () => {
    it('should return same instance from getHealthMonitor', () => {
      const monitor1 = getHealthMonitor();
      const monitor2 = getHealthMonitor();
      expect(monitor1).toBe(monitor2);

    it('should create new instance with initializeHealthMonitor', () => {
      const monitor1 = getHealthMonitor();
      const monitor2 = initializeHealthMonitor();
      expect(monitor1).not.toBe(monitor2);
      
      // Subsequent calls should return the new instance
      const monitor3 = getHealthMonitor();
      expect(monitor2).toBe(monitor3);


  describe('Error Handling', () => {
    it('should handle errors in event listeners gracefully', async () => {
      const faultyListener = vi.fn(() => {
        throw new Error('Listener error');

      healthMonitor.addEventListener(HealthEventType.HEALTH_CHECK_SUCCESS, faultyListener);
      
      mockConnectionManager.makeRequest.mockResolvedValue({ status: 200 });
      
      // Should not throw error despite faulty listener
      await expect(healthMonitor.checkEndpointHealth('http://localhost:8000')).resolves.toBeDefined();
      expect(faultyListener).toHaveBeenCalled();


