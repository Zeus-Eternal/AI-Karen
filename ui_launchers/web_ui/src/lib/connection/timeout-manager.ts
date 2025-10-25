/**
 * Timeout Configuration Manager
 * 
 * Manages configurable timeout settings for different operation types
 * including connection, authentication, and health checks.
 * 
 * Requirements: 2.1, 2.2
 */

export interface TimeoutSettings {
  connection: number;
  authentication: number;
  sessionValidation: number;
  healthCheck: number;
  database: number;
}

export interface OperationTimeouts {
  [key: string]: number;
}

export enum OperationType {
  CONNECTION = 'connection',
  AUTHENTICATION = 'authentication',
  SESSION_VALIDATION = 'sessionValidation',
  HEALTH_CHECK = 'healthCheck',
  DATABASE = 'database',
}

/**
 * Timeout Configuration Manager
 * 
 * Provides centralized timeout management with configurable settings
 * for different types of operations and automatic environment detection.
 */
export class TimeoutManager {
  private timeouts: TimeoutSettings;
  private customTimeouts: Map<string, number> = new Map();

  constructor() {
    this.timeouts = this.loadTimeoutConfiguration();
  }

  /**
   * Load timeout configuration from environment variables
   */
  private loadTimeoutConfiguration(): TimeoutSettings {
    return {
      connection: this.getTimeoutFromEnv('CONNECTION_TIMEOUT_MS', 45000), // Increased for better reliability
      authentication: this.getTimeoutFromEnv('AUTH_TIMEOUT_MS', 60000), // Increased to 60s for better reliability
      sessionValidation: this.getTimeoutFromEnv('SESSION_VALIDATION_TIMEOUT_MS', 30000),
      healthCheck: this.getTimeoutFromEnv('HEALTH_CHECK_TIMEOUT_MS', 10000),
      database: this.getTimeoutFromEnv('DATABASE_TIMEOUT_MS', 30000),
    };
  }

  /**
   * Get timeout value from environment variable with fallback
   */
  private getTimeoutFromEnv(envVar: string, defaultValue: number): number {
    if (typeof process !== 'undefined' && process.env) {
      const value = process.env[envVar];
      if (value) {
        const parsed = parseInt(value, 10);
        if (!isNaN(parsed) && parsed > 0) {
          return parsed;
        }
      }
    }
    return defaultValue;
  }

  /**
   * Get timeout for a specific operation type
   */
  getTimeout(operationType: OperationType): number {
    return this.timeouts[operationType];
  }

  /**
   * Get timeout for a custom operation
   */
  getCustomTimeout(operationName: string, defaultTimeout?: number): number {
    const customTimeout = this.customTimeouts.get(operationName);
    if (customTimeout !== undefined) {
      return customTimeout;
    }
    return defaultTimeout || this.timeouts.connection;
  }

  /**
   * Set timeout for a specific operation type
   */
  setTimeout(operationType: OperationType, timeout: number): void {
    if (timeout <= 0) {
      throw new Error(`Timeout must be positive, got: ${timeout}`);
    }
    this.timeouts[operationType] = timeout;
  }

  /**
   * Set timeout for a custom operation
   */
  setCustomTimeout(operationName: string, timeout: number): void {
    if (timeout <= 0) {
      throw new Error(`Timeout must be positive, got: ${timeout}`);
    }
    this.customTimeouts.set(operationName, timeout);
  }

  /**
   * Get all timeout settings
   */
  getAllTimeouts(): TimeoutSettings {
    return { ...this.timeouts };
  }

  /**
   * Get all custom timeouts
   */
  getAllCustomTimeouts(): OperationTimeouts {
    return Object.fromEntries(this.customTimeouts);
  }

  /**
   * Update multiple timeout settings at once
   */
  updateTimeouts(updates: Partial<TimeoutSettings>): void {
    Object.entries(updates).forEach(([key, value]) => {
      if (value !== undefined && value > 0) {
        this.timeouts[key as keyof TimeoutSettings] = value;
      }
    });
  }

  /**
   * Reset timeouts to default values
   */
  resetToDefaults(): void {
    this.timeouts = this.loadTimeoutConfiguration();
    this.customTimeouts.clear();
  }

  /**
   * Get timeout with automatic scaling based on operation complexity
   */
  getScaledTimeout(operationType: OperationType, complexityFactor: number = 1): number {
    const baseTimeout = this.getTimeout(operationType);
    
    // Handle edge cases for very small or negative factors
    if (complexityFactor <= 0) {
      return 1000; // Return minimum timeout for invalid factors
    }
    
    const scaledTimeout = Math.round(baseTimeout * complexityFactor);
    
    // Ensure minimum timeout of 1 second
    return Math.max(scaledTimeout, 1000);
  }

  /**
   * Get timeout for database operations with connection pooling considerations
   */
  getDatabaseTimeout(operationType: 'query' | 'connection' | 'transaction' = 'query'): number {
    const baseTimeout = this.timeouts.database;
    
    switch (operationType) {
      case 'connection':
        return Math.round(baseTimeout * 0.5); // Connection should be faster
      case 'transaction':
        return Math.round(baseTimeout * 2); // Transactions may take longer
      case 'query':
      default:
        return baseTimeout;
    }
  }

  /**
   * Get timeout for authentication operations with different phases
   */
  getAuthTimeout(phase: 'login' | 'validation' | 'refresh' = 'login'): number {
    const baseTimeout = this.timeouts.authentication;
    
    switch (phase) {
      case 'login':
        return baseTimeout; // Full timeout for login
      case 'validation':
        return this.timeouts.sessionValidation; // Use session validation timeout
      case 'refresh':
        return Math.round(baseTimeout * 0.7); // Refresh should be faster
      default:
        return baseTimeout;
    }
  }

  /**
   * Validate timeout configuration
   */
  validateConfiguration(): { isValid: boolean; errors: string[]; warnings: string[] } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check for reasonable timeout values
    Object.entries(this.timeouts).forEach(([key, value]) => {
      if (value <= 0) {
        errors.push(`${key} timeout must be positive, got: ${value}`);
      } else if (value < 1000) {
        warnings.push(`${key} timeout is very low (${value}ms), consider increasing it`);
      } else if (value > 300000) { // 5 minutes
        warnings.push(`${key} timeout is very high (${value}ms), consider reducing it`);
      }
    });

    // Check for logical relationships
    if (this.timeouts.healthCheck > this.timeouts.connection) {
      warnings.push('Health check timeout is higher than connection timeout, this may cause issues');
    }

    if (this.timeouts.sessionValidation > this.timeouts.authentication) {
      warnings.push('Session validation timeout is higher than authentication timeout');
    }

    // Check custom timeouts
    this.customTimeouts.forEach((value, key) => {
      if (value <= 0) {
        errors.push(`Custom timeout '${key}' must be positive, got: ${value}`);
      }
    });

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * Get timeout configuration summary for debugging
   */
  getConfigurationSummary(): {
    timeouts: TimeoutSettings;
    customTimeouts: OperationTimeouts;
    validation: ReturnType<TimeoutManager['validateConfiguration']>;
  } {
    return {
      timeouts: this.getAllTimeouts(),
      customTimeouts: this.getAllCustomTimeouts(),
      validation: this.validateConfiguration(),
    };
  }

  /**
   * Create AbortController with timeout
   */
  createAbortController(operationType: OperationType, customTimeout?: number): {
    controller: AbortController;
    timeoutId: ReturnType<typeof setTimeout>;
    timeout: number;
  } {
    const controller = new AbortController();
    const timeout = customTimeout || this.getTimeout(operationType);
    
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, timeout);

    return {
      controller,
      timeoutId,
      timeout,
    };
  }

  /**
   * Create AbortController with scaled timeout
   */
  createScaledAbortController(
    operationType: OperationType,
    complexityFactor: number = 1
  ): {
    controller: AbortController;
    timeoutId: ReturnType<typeof setTimeout>;
    timeout: number;
  } {
    const controller = new AbortController();
    const timeout = this.getScaledTimeout(operationType, complexityFactor);
    
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, timeout);

    return {
      controller,
      timeoutId,
      timeout,
    };
  }
}

// Singleton instance
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
 * Initialize timeout manager
 */
export function initializeTimeoutManager(): TimeoutManager {
  timeoutManager = new TimeoutManager();
  return timeoutManager;
}

// Export types
export type {
  TimeoutSettings as TimeoutSettingsType,
  OperationTimeouts as OperationTimeoutsType,
};