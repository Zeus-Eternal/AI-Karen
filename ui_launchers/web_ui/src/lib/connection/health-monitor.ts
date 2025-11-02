/**
 * Health Monitor
 * 
 * Provides health check endpoints, client-side monitoring,
 * connection status tracking, and automatic backend failover logic.
 * 
 * Requirements: 5.1, 5.4
 */
import { getConnectionManager } from './connection-manager';
import { getTimeoutManager, OperationType } from './timeout-manager';
import { getEnvironmentConfigManager } from '../config/index';
export interface HealthStatus {
  isHealthy: boolean;
  lastCheck: Date;
  responseTime: number;
  consecutiveFailures: number;
  totalChecks: number;
  successfulChecks: number;
  failedChecks: number;
  averageResponseTime: number;
  uptime: number; // Percentage
}
export interface BackendEndpoint {
  url: string;
  priority: number;
  isActive: boolean;
  health: HealthStatus;
}
export interface HealthCheckResult {
  endpoint: string;
  isHealthy: boolean;
  responseTime: number;
  timestamp: Date;
  error?: string;
  details?: any;
}
export interface MonitoringConfig {
  checkInterval: number;
  maxConsecutiveFailures: number;
  failoverEnabled: boolean;
  healthCheckTimeout: number;
  endpoints: string[];
}
export enum HealthEventType {
  HEALTH_CHECK_SUCCESS = 'health_check_success',
  HEALTH_CHECK_FAILURE = 'health_check_failure',
  ENDPOINT_FAILOVER = 'endpoint_failover',
  ENDPOINT_RECOVERY = 'endpoint_recovery',
  MONITORING_STARTED = 'monitoring_started',
  MONITORING_STOPPED = 'monitoring_stopped',
}
export interface HealthEvent {
  type: HealthEventType;
  timestamp: Date;
  endpoint: string;
  data?: any;
}
/**
 * Health Monitor
 * 
 * Monitors backend health, tracks connection status,
 * and provides automatic failover capabilities.
 */
export class HealthMonitor {
  private endpoints: Map<string, BackendEndpoint> = new Map();
  private activeEndpoint: string | null = null;
  private monitoringInterval: NodeJS.Timeout | null = null;
  private config: MonitoringConfig;
  private eventListeners: Map<HealthEventType, ((event: HealthEvent) => void)[]> = new Map();
  private responseTimes: number[] = [];
  private maxResponseTimeHistory: number = 100;
  private isMonitoring: boolean = false;
  constructor(config?: Partial<MonitoringConfig>) {
    this.config = {
      checkInterval: 30000, // 30 seconds
      maxConsecutiveFailures: 3,
      failoverEnabled: true,
      healthCheckTimeout: 10000, // 10 seconds
      endpoints: [],
      ...config,
    };
    this.initializeEndpoints();
  }
  /**
   * Initialize endpoints from configuration
   */
  private initializeEndpoints(): void {
    try {
      const configManager = getEnvironmentConfigManager();
      const primaryUrl = configManager.getBackendConfig().primaryUrl;
      const fallbackUrls = configManager.getBackendConfig().fallbackUrls;
      // Add primary endpoint
      this.addEndpoint(primaryUrl, 1, true);
      // Add fallback endpoints
      fallbackUrls.forEach((url, index) => {
        this.addEndpoint(url, index + 2, false);

      // Set active endpoint to primary
      this.activeEndpoint = primaryUrl;
    } catch (error) {
      // Fallback to default endpoints
      const defaultEndpoints = this.config.endpoints.length > 0 
        ? this.config.endpoints 
        : ['http://localhost:8000'];
      defaultEndpoints.forEach((url, index) => {
        this.addEndpoint(url, index + 1, index === 0);

      if (defaultEndpoints.length > 0) {
        this.activeEndpoint = defaultEndpoints[0];
      }
    }
  }
  /**
   * Add an endpoint to monitor
   */
  addEndpoint(url: string, priority: number = 1, isActive: boolean = false): void {
    const endpoint: BackendEndpoint = {
      url,
      priority,
      isActive,
      health: {
        isHealthy: true,
        lastCheck: new Date(),
        responseTime: 0,
        consecutiveFailures: 0,
        totalChecks: 0,
        successfulChecks: 0,
        failedChecks: 0,
        averageResponseTime: 0,
        uptime: 100,
      },
    };
    this.endpoints.set(url, endpoint);
    if (isActive) {
      this.activeEndpoint = url;
    }
  }
  /**
   * Remove an endpoint from monitoring
   */
  removeEndpoint(url: string): void {
    this.endpoints.delete(url);
    if (this.activeEndpoint === url) {
      this.activeEndpoint = this.getNextHealthyEndpoint();
    }
  }
  /**
   * Get the currently active endpoint
   */
  getActiveEndpoint(): string | null {
    return this.activeEndpoint;
  }
  /**
   * Get all endpoints with their health status
   */
  getAllEndpoints(): BackendEndpoint[] {
    return Array.from(this.endpoints.values()).sort((a, b) => a.priority - b.priority);
  }
  /**
   * Get health status for a specific endpoint
   */
  getEndpointHealth(url: string): HealthStatus | null {
    const endpoint = this.endpoints.get(url);
    return endpoint ? endpoint.health : null;
  }
  /**
   * Perform health check on a specific endpoint
   */
  async checkEndpointHealth(url: string): Promise<HealthCheckResult> {
    const startTime = Date.now();
    const endpoint = this.endpoints.get(url);
    if (!endpoint) {
      return {
        endpoint: url,
        isHealthy: false,
        responseTime: 0,
        timestamp: new Date(),
        error: 'Endpoint not found',
      };
    }
    try {
      const connectionManager = getConnectionManager();
      const timeoutManager = getTimeoutManager();
      // Perform health check request
      await connectionManager.makeRequest(`${url}/health`, { method: 'GET' }, {
        timeout: timeoutManager.getTimeout(OperationType.HEALTH_CHECK),
        retryAttempts: 0, // No retries for health checks
        circuitBreakerEnabled: false,

      const responseTime = Date.now() - startTime;
      // Update endpoint health
      this.updateEndpointHealth(url, true, responseTime);
      const result: HealthCheckResult = {
        endpoint: url,
        isHealthy: true,
        responseTime,
        timestamp: new Date(),
      };
      this.emitEvent(HealthEventType.HEALTH_CHECK_SUCCESS, url, result);
      return result;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      // Update endpoint health
      this.updateEndpointHealth(url, false, responseTime);
      const result: HealthCheckResult = {
        endpoint: url,
        isHealthy: false,
        responseTime,
        timestamp: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error',
        details: error,
      };
      this.emitEvent(HealthEventType.HEALTH_CHECK_FAILURE, url, result);
      return result;
    }
  }
  /**
   * Perform health check on all endpoints
   */
  async checkAllEndpoints(): Promise<HealthCheckResult[]> {
    const results = await Promise.allSettled(
      Array.from(this.endpoints.keys()).map(url => this.checkEndpointHealth(url))
    );
    return results.map(result => 
      result.status === 'fulfilled' 
        ? result.value 
        : {
            endpoint: 'unknown',
            isHealthy: false,
            responseTime: 0,
            timestamp: new Date(),
            error: 'Health check failed',
          }
    );
  }
  /**
   * Update endpoint health metrics
   */
  private updateEndpointHealth(url: string, isHealthy: boolean, responseTime: number): void {
    const endpoint = this.endpoints.get(url);
    if (!endpoint) return;
    const health = endpoint.health;
    // Update basic metrics
    health.lastCheck = new Date();
    health.responseTime = responseTime;
    health.totalChecks++;
    if (isHealthy) {
      health.successfulChecks++;
      health.consecutiveFailures = 0;
      health.isHealthy = true;
    } else {
      health.failedChecks++;
      health.consecutiveFailures++;
      // Mark as unhealthy if consecutive failures exceed threshold
      if (health.consecutiveFailures >= this.config.maxConsecutiveFailures) {
        health.isHealthy = false;
      }
    }
    // Update average response time
    this.responseTimes.push(responseTime);
    if (this.responseTimes.length > this.maxResponseTimeHistory) {
      this.responseTimes.shift();
    }
    health.averageResponseTime = 
      this.responseTimes.reduce((sum, time) => sum + time, 0) / this.responseTimes.length;
    // Update uptime percentage
    health.uptime = health.totalChecks > 0 
      ? (health.successfulChecks / health.totalChecks) * 100 
      : 100;
    // Check if failover is needed
    if (!isHealthy && url === this.activeEndpoint && this.config.failoverEnabled) {
      this.performFailover();
    }
  }
  /**
   * Perform automatic failover to next healthy endpoint
   */
  private performFailover(): void {
    const currentEndpoint = this.activeEndpoint;
    const nextEndpoint = this.getNextHealthyEndpoint();
    if (nextEndpoint && nextEndpoint !== currentEndpoint) {
      const oldEndpoint = this.activeEndpoint;
      this.activeEndpoint = nextEndpoint;
      // Update active status
      if (oldEndpoint) {
        const oldEp = this.endpoints.get(oldEndpoint);
        if (oldEp) oldEp.isActive = false;
      }
      const newEp = this.endpoints.get(nextEndpoint);
      if (newEp) newEp.isActive = true;
      this.emitEvent(HealthEventType.ENDPOINT_FAILOVER, nextEndpoint, {
        from: oldEndpoint,
        to: nextEndpoint,

    }
  }
  /**
   * Get the next healthy endpoint based on priority
   */
  private getNextHealthyEndpoint(): string | null {
    const healthyEndpoints = Array.from(this.endpoints.entries())
      .filter(([_, endpoint]) => endpoint.health.isHealthy)
      .sort(([_, a], [__, b]) => a.priority - b.priority);
    return healthyEndpoints.length > 0 ? healthyEndpoints[0][0] : null;
  }
  /**
   * Start health monitoring
   */
  startMonitoring(): void {
    if (this.isMonitoring) {
      return;
    }
    this.isMonitoring = true;
    // Perform initial health check
    this.checkAllEndpoints();
    // Set up periodic health checks
    this.monitoringInterval = setInterval(() => {
      this.checkAllEndpoints();
    }, this.config.checkInterval);
    this.emitEvent(HealthEventType.MONITORING_STARTED, this.activeEndpoint || 'unknown');
  }
  /**
   * Stop health monitoring
   */
  stopMonitoring(): void {
    if (!this.isMonitoring) {
      return;
    }
    this.isMonitoring = false;
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
    this.emitEvent(HealthEventType.MONITORING_STOPPED, this.activeEndpoint || 'unknown');
  }
  /**
   * Check if monitoring is active
   */
  isMonitoringActive(): boolean {
    return this.isMonitoring;
  }
  /**
   * Update monitoring configuration
   */
  updateConfig(updates: Partial<MonitoringConfig>): void {
    this.config = { ...this.config, ...updates };
    // Restart monitoring if it was active
    if (this.isMonitoring) {
      this.stopMonitoring();
      this.startMonitoring();
    }
  }
  /**
   * Get monitoring configuration
   */
  getConfig(): MonitoringConfig {
    return { ...this.config };
  }
  /**
   * Add event listener
   */
  addEventListener(eventType: HealthEventType, listener: (event: HealthEvent) => void): void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, []);
    }
    this.eventListeners.get(eventType)!.push(listener);
  }
  /**
   * Remove event listener
   */
  removeEventListener(eventType: HealthEventType, listener: (event: HealthEvent) => void): void {
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }
  /**
   * Emit health event
   */
  private emitEvent(type: HealthEventType, endpoint: string, data?: any): void {
    const event: HealthEvent = {
      type,
      timestamp: new Date(),
      endpoint,
      data,
    };
    const listeners = this.eventListeners.get(type);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(event);
        } catch (error) {
        }

    }
  }
  /**
   * Get overall system health summary
   */
  getHealthSummary(): {
    activeEndpoint: string | null;
    totalEndpoints: number;
    healthyEndpoints: number;
    unhealthyEndpoints: number;
    averageResponseTime: number;
    overallUptime: number;
    isMonitoring: boolean;
  } {
    const endpoints = Array.from(this.endpoints.values());
    const healthyCount = endpoints.filter(ep => ep.health.isHealthy).length;
    const totalResponseTime = endpoints.reduce((sum, ep) => sum + ep.health.averageResponseTime, 0);
    const totalUptime = endpoints.reduce((sum, ep) => sum + ep.health.uptime, 0);
    return {
      activeEndpoint: this.activeEndpoint,
      totalEndpoints: endpoints.length,
      healthyEndpoints: healthyCount,
      unhealthyEndpoints: endpoints.length - healthyCount,
      averageResponseTime: endpoints.length > 0 ? totalResponseTime / endpoints.length : 0,
      overallUptime: endpoints.length > 0 ? totalUptime / endpoints.length : 100,
      isMonitoring: this.isMonitoring,
    };
  }
  /**
   * Force failover to a specific endpoint
   */
  forceFailover(targetUrl: string): boolean {
    const targetEndpoint = this.endpoints.get(targetUrl);
    if (!targetEndpoint) {
      return false;
    }
    const oldEndpoint = this.activeEndpoint;
    this.activeEndpoint = targetUrl;
    // Update active status
    this.endpoints.forEach((endpoint, url) => {
      endpoint.isActive = url === targetUrl;

    this.emitEvent(HealthEventType.ENDPOINT_FAILOVER, targetUrl, {
      from: oldEndpoint,
      to: targetUrl,
      forced: true,

    return true;
  }
  /**
   * Reset health statistics for all endpoints
   */
  resetHealthStatistics(): void {
    this.endpoints.forEach(endpoint => {
      endpoint.health = {
        isHealthy: true,
        lastCheck: new Date(),
        responseTime: 0,
        consecutiveFailures: 0,
        totalChecks: 0,
        successfulChecks: 0,
        failedChecks: 0,
        averageResponseTime: 0,
        uptime: 100,
      };

    this.responseTimes = [];
  }
}
// Singleton instance
let healthMonitor: HealthMonitor | null = null;
/**
 * Get the global health monitor instance
 */
export function getHealthMonitor(): HealthMonitor {
  if (!healthMonitor) {
    healthMonitor = new HealthMonitor();
  }
  return healthMonitor;
}
/**
 * Initialize health monitor
 */
export function initializeHealthMonitor(config?: Partial<MonitoringConfig>): HealthMonitor {
  healthMonitor = new HealthMonitor(config);
  return healthMonitor;
}
// Export types
export type {
};
