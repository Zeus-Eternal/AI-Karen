/**
 * Timeout Manager for Extension Authentication
 * 
 * Manages timeout configurations for different types of operations
 * to optimize performance and user experience.
 */

import { logger } from '../logger';

// Operation types for timeout configuration
export enum OperationType {
  API_REQUEST = 'api_request',
  AUTHENTICATION = 'authentication',
  SESSION_VALIDATION = 'session_validation',
  BACKGROUND_TASK = 'background_task',
  HEALTH_CHECK = 'health_check',
  FILE_UPLOAD = 'file_upload',
  STREAMING = 'streaming',
  CONNECTION = 'connection',
}

// Timeout configuration interface
export interface TimeoutConfig {
  default: number;
  fast: number;
  slow: number;
  critical: number;
}

// Timeout settings interface (alias for compatibility)
export type TimeoutSettings = TimeoutConfig;

// Operation timeout mappings
export interface OperationTimeouts {
  [OperationType.API_REQUEST]: number;
  [OperationType.AUTHENTICATION]: number;
  [OperationType.SESSION_VALIDATION]: number;
  [OperationType.BACKGROUND_TASK]: number;
  [OperationType.HEALTH_CHECK]: number;
  [OperationType.FILE_UPLOAD]: number;
  [OperationType.STREAMING]: number;
  [OperationType.CONNECTION]: number;
}

// Type aliases for compatibility
export type TimeoutSettingsType = TimeoutSettings;
export type OperationTimeoutsType = OperationTimeouts;

/**
 * Timeout Manager for handling operation-specific timeouts
 */
export class TimeoutManager {
  private timeoutConfig: TimeoutConfig;
  private operationTimeouts: OperationTimeouts;
  private dynamicAdjustments: Map<OperationType, number> = new Map();

  constructor() {
    this.timeoutConfig = {
      default: 30000,   // 30 seconds
      fast: 5000,       // 5 seconds
      slow: 60000,      // 60 seconds
      critical: 10000,  // 10 seconds
    };

    this.operationTimeouts = {
      [OperationType.API_REQUEST]: this.timeoutConfig.default,
      [OperationType.AUTHENTICATION]: this.timeoutConfig.critical,
      [OperationType.SESSION_VALIDATION]: this.timeoutConfig.fast,
      [OperationType.BACKGROUND_TASK]: this.timeoutConfig.slow,
      [OperationType.HEALTH_CHECK]: this.timeoutConfig.fast,
      [OperationType.FILE_UPLOAD]: this.timeoutConfig.slow,
      [OperationType.STREAMING]: this.timeoutConfig.slow,
      [OperationType.CONNECTION]: this.timeoutConfig.default,
    };

    logger.debug('Timeout manager initialized with config:', this.operationTimeouts);
  }

  /**
   * Get timeout for specific operation type
   */
  getTimeout(operationType: OperationType): number {
    // Check for dynamic adjustments first
    const dynamicTimeout = this.dynamicAdjustments.get(operationType);
    if (dynamicTimeout !== undefined) {
      return dynamicTimeout;
    }

    // Return configured timeout
    return this.operationTimeouts[operationType] || this.timeoutConfig.default;
  }

  /**
   * Set timeout for specific operation type
   */
  setTimeout(operationType: OperationType, timeout: number): void {
    if (timeout <= 0) {
      logger.warn(`Invalid timeout value ${timeout} for operation ${operationType}`);
      return;
    }

    this.operationTimeouts[operationType] = timeout;
    logger.debug(`Timeout updated for ${operationType}: ${timeout}ms`);
  }

  /**
   * Temporarily adjust timeout for specific operation
   */
  adjustTimeout(operationType: OperationType, timeout: number, durationMs: number = 60000): void {
    if (timeout <= 0) {
      logger.warn(`Invalid timeout adjustment ${timeout} for operation ${operationType}`);
      return;
    }

    this.dynamicAdjustments.set(operationType, timeout);
    logger.debug(`Timeout temporarily adjusted for ${operationType}: ${timeout}ms for ${durationMs}ms`);

    // Clear adjustment after duration
    setTimeout(() => {
      this.dynamicAdjustments.delete(operationType);
      logger.debug(`Timeout adjustment cleared for ${operationType}`);
    }, durationMs);
  }

  /**
   * Get timeout based on network conditions
   */
  getAdaptiveTimeout(operationType: OperationType, networkLatency?: number): number {
    const baseTimeout = this.getTimeout(operationType);

    if (!networkLatency) {
      return baseTimeout;
    }

    // Adjust timeout based on network latency
    let multiplier = 1;
    
    if (networkLatency > 1000) {
      // High latency - increase timeout significantly
      multiplier = 2;
    } else if (networkLatency > 500) {
      // Medium latency - increase timeout moderately
      multiplier = 1.5;
    } else if (networkLatency < 100) {
      // Low latency - can use shorter timeout
      multiplier = 0.8;
    }

    const adaptiveTimeout = Math.round(baseTimeout * multiplier);
    logger.debug(`Adaptive timeout for ${operationType}: ${adaptiveTimeout}ms (latency: ${networkLatency}ms)`);
    
    return adaptiveTimeout;
  }

  /**
   * Get timeout configuration for development mode
   */
  getDevelopmentTimeout(operationType: OperationType): number {
    // In development, use longer timeouts to account for debugging
    const baseTimeout = this.getTimeout(operationType);
    const devMultiplier = 2;
    
    return baseTimeout * devMultiplier;
  }

  /**
   * Get all current timeout configurations
   */
  getAllTimeouts(): Record<string, number> {
    const timeouts: Record<string, number> = {};
    
    for (const [operation, timeout] of Object.entries(this.operationTimeouts)) {
      const dynamicTimeout = this.dynamicAdjustments.get(operation as OperationType);
      timeouts[operation] = dynamicTimeout !== undefined ? dynamicTimeout : timeout;
    }
    
    return timeouts;
  }

  /**
   * Reset all timeouts to default values
   */
  resetToDefaults(): void {
    this.dynamicAdjustments.clear();
    
    this.operationTimeouts = {
      [OperationType.API_REQUEST]: this.timeoutConfig.default,
      [OperationType.AUTHENTICATION]: this.timeoutConfig.critical,
      [OperationType.SESSION_VALIDATION]: this.timeoutConfig.fast,
      [OperationType.BACKGROUND_TASK]: this.timeoutConfig.slow,
      [OperationType.HEALTH_CHECK]: this.timeoutConfig.fast,
      [OperationType.FILE_UPLOAD]: this.timeoutConfig.slow,
      [OperationType.STREAMING]: this.timeoutConfig.slow,
      [OperationType.CONNECTION]: this.timeoutConfig.default,
    };

    logger.debug('Timeout manager reset to defaults');
  }

  /**
   * Update base timeout configuration
   */
  updateConfig(config: Partial<TimeoutConfig>): void {
    this.timeoutConfig = { ...this.timeoutConfig, ...config };
    logger.debug('Timeout configuration updated:', this.timeoutConfig);
  }

  /**
   * Get timeout recommendation based on operation characteristics
   */
  getRecommendedTimeout(
    operationType: OperationType,
    options: {
      payloadSize?: number;
      complexity?: 'low' | 'medium' | 'high';
      priority?: 'low' | 'medium' | 'high';
    } = {}
  ): number {
    let baseTimeout = this.getTimeout(operationType);
    
    // Adjust based on payload size
    if (options.payloadSize) {
      if (options.payloadSize > 1024 * 1024) { // > 1MB
        baseTimeout *= 1.5;
      } else if (options.payloadSize > 100 * 1024) { // > 100KB
        baseTimeout *= 1.2;
      }
    }
    
    // Adjust based on complexity
    if (options.complexity) {
      switch (options.complexity) {
        case 'high':
          baseTimeout *= 1.5;
          break;
        case 'medium':
          baseTimeout *= 1.2;
          break;
        case 'low':
          baseTimeout *= 0.8;
          break;
      }
    }
    
    // Adjust based on priority
    if (options.priority) {
      switch (options.priority) {
        case 'high':
          baseTimeout *= 0.8; // Shorter timeout for high priority
          break;
        case 'low':
          baseTimeout *= 1.5; // Longer timeout for low priority
          break;
      }
    }
    
    return Math.round(baseTimeout);
  }
}

// Global instance
let timeoutManager: TimeoutManager | null = null;

/**
 * Get the global timeout manager instance
 */
export function getTimeoutManager(): TimeoutManager {
  if (!timeoutManager) {
    timeoutManager = new TimeoutManager();
  }
  return timeoutManager;
}

/**
 * Initialize a new timeout manager instance
 */
export function initializeTimeoutManager(config?: Partial<TimeoutConfig>): TimeoutManager {
  timeoutManager = new TimeoutManager();
  if (config) {
    timeoutManager.updateConfig(config);
  }
  return timeoutManager;
}