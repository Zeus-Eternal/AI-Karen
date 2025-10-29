/**
 * Custom error classes for model selection services
 */

/**
 * Base error class for all model selection related errors
 */
export class ModelSelectionError extends Error {
  public readonly code: string;
  public readonly service: string;
  public readonly timestamp: string;
  public readonly context?: Record<string, any>;

  constructor(
    message: string, 
    code: string, 
    service: string, 
    context?: Record<string, any>
  ) {
    super(message);
    this.name = 'ModelSelectionError';
    this.code = code;
    this.service = service;
    this.timestamp = new Date().toISOString();
    this.context = context;

    // Ensure proper prototype chain for instanceof checks
    Object.setPrototypeOf(this, ModelSelectionError.prototype);
  }

  /**
   * Convert error to a serializable object
   */
  toJSON(): Record<string, any> {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      service: this.service,
      timestamp: this.timestamp,
      context: this.context,
      stack: this.stack
    };
  }

  /**
   * Create a user-friendly error message
   */
  getUserMessage(): string {
    return this.message;
  }
}

/**
 * Error thrown when model scanning operations fail
 */
export class ModelScanError extends ModelSelectionError {
  public readonly directory?: string;
  public readonly scanType?: string;

  constructor(
    message: string, 
    directory?: string, 
    scanType?: string,
    context?: Record<string, any>
  ) {
    super(message, 'SCAN_ERROR', 'ModelScanner', context);
    this.name = 'ModelScanError';
    this.directory = directory;
    this.scanType = scanType;

    Object.setPrototypeOf(this, ModelScanError.prototype);
  }

  getUserMessage(): string {
    if (this.directory) {
      return `Failed to scan directory "${this.directory}": ${this.message}`;
    }
    return `Model scanning failed: ${this.message}`;
  }
}

/**
 * Error thrown when resource operations fail
 */
export class ResourceError extends ModelSelectionError {
  public readonly resourceType?: string;
  public readonly requiredAmount?: number;
  public readonly availableAmount?: number;

  constructor(
    message: string, 
    resourceType?: string,
    requiredAmount?: number,
    availableAmount?: number,
    context?: Record<string, any>
  ) {
    super(message, 'RESOURCE_ERROR', 'ResourceMonitor', context);
    this.name = 'ResourceError';
    this.resourceType = resourceType;
    this.requiredAmount = requiredAmount;
    this.availableAmount = availableAmount;

    Object.setPrototypeOf(this, ResourceError.prototype);
  }

  getUserMessage(): string {
    if (this.resourceType && this.requiredAmount && this.availableAmount) {
      return `Insufficient ${this.resourceType}: need ${this.requiredAmount}, have ${this.availableAmount}`;
    }
    return `Resource error: ${this.message}`;
  }
}

/**
 * Error thrown when model health checks fail
 */
export class ModelHealthError extends ModelSelectionError {
  public readonly modelId?: string;
  public readonly healthIssue?: string;

  constructor(
    message: string, 
    modelId?: string, 
    healthIssue?: string,
    context?: Record<string, any>
  ) {
    super(message, 'HEALTH_ERROR', 'ModelHealthMonitor', context);
    this.name = 'ModelHealthError';
    this.modelId = modelId;
    this.healthIssue = healthIssue;

    Object.setPrototypeOf(this, ModelHealthError.prototype);
  }

  getUserMessage(): string {
    if (this.modelId) {
      return `Health check failed for model "${this.modelId}": ${this.message}`;
    }
    return `Model health check failed: ${this.message}`;
  }
}

/**
 * Error thrown when performance monitoring fails
 */
export class PerformanceError extends ModelSelectionError {
  public readonly modelId?: string;
  public readonly metricType?: string;

  constructor(
    message: string, 
    modelId?: string, 
    metricType?: string,
    context?: Record<string, any>
  ) {
    super(message, 'PERFORMANCE_ERROR', 'PerformanceMonitor', context);
    this.name = 'PerformanceError';
    this.modelId = modelId;
    this.metricType = metricType;

    Object.setPrototypeOf(this, PerformanceError.prototype);
  }

  getUserMessage(): string {
    if (this.modelId && this.metricType) {
      return `Performance monitoring failed for model "${this.modelId}" (${this.metricType}): ${this.message}`;
    }
    return `Performance monitoring failed: ${this.message}`;
  }
}

/**
 * Error thrown when preferences operations fail
 */
export class PreferencesError extends ModelSelectionError {
  public readonly preferenceKey?: string;
  public readonly operation?: string;

  constructor(
    message: string, 
    preferenceKey?: string, 
    operation?: string,
    context?: Record<string, any>
  ) {
    super(message, 'PREFERENCES_ERROR', 'PreferencesService', context);
    this.name = 'PreferencesError';
    this.preferenceKey = preferenceKey;
    this.operation = operation;

    Object.setPrototypeOf(this, PreferencesError.prototype);
  }

  getUserMessage(): string {
    if (this.preferenceKey && this.operation) {
      return `Failed to ${this.operation} preference "${this.preferenceKey}": ${this.message}`;
    }
    return `Preferences operation failed: ${this.message}`;
  }
}

/**
 * Error thrown when directory watching fails
 */
export class DirectoryWatchError extends ModelSelectionError {
  public readonly directory?: string;
  public readonly watchOperation?: string;

  constructor(
    message: string, 
    directory?: string, 
    watchOperation?: string,
    context?: Record<string, any>
  ) {
    super(message, 'WATCH_ERROR', 'DirectoryWatcher', context);
    this.name = 'DirectoryWatchError';
    this.directory = directory;
    this.watchOperation = watchOperation;

    Object.setPrototypeOf(this, DirectoryWatchError.prototype);
  }

  getUserMessage(): string {
    if (this.directory) {
      return `Directory watching failed for "${this.directory}": ${this.message}`;
    }
    return `Directory watching failed: ${this.message}`;
  }
}

/**
 * Error thrown when model registry operations fail
 */
export class ModelRegistryError extends ModelSelectionError {
  public readonly registryOperation?: string;
  public readonly modelId?: string;

  constructor(
    message: string, 
    registryOperation?: string, 
    modelId?: string,
    context?: Record<string, any>
  ) {
    super(message, 'REGISTRY_ERROR', 'ModelRegistry', context);
    this.name = 'ModelRegistryError';
    this.registryOperation = registryOperation;
    this.modelId = modelId;

    Object.setPrototypeOf(this, ModelRegistryError.prototype);
  }

  getUserMessage(): string {
    if (this.registryOperation && this.modelId) {
      return `Model registry ${this.registryOperation} failed for "${this.modelId}": ${this.message}`;
    }
    return `Model registry operation failed: ${this.message}`;
  }
}

/**
 * Error thrown when configuration is invalid
 */
export class ConfigurationError extends ModelSelectionError {
  public readonly configKey?: string;
  public readonly expectedType?: string;
  public readonly actualValue?: any;

  constructor(
    message: string, 
    configKey?: string, 
    expectedType?: string,
    actualValue?: any,
    context?: Record<string, any>
  ) {
    super(message, 'CONFIG_ERROR', 'Configuration', context);
    this.name = 'ConfigurationError';
    this.configKey = configKey;
    this.expectedType = expectedType;
    this.actualValue = actualValue;

    Object.setPrototypeOf(this, ConfigurationError.prototype);
  }

  getUserMessage(): string {
    if (this.configKey && this.expectedType) {
      return `Invalid configuration for "${this.configKey}": expected ${this.expectedType}, got ${typeof this.actualValue}`;
    }
    return `Configuration error: ${this.message}`;
  }
}

/**
 * Error thrown when operations timeout
 */
export class TimeoutError extends ModelSelectionError {
  public readonly operation?: string;
  public readonly timeoutMs?: number;

  constructor(
    message: string, 
    operation?: string, 
    timeoutMs?: number,
    context?: Record<string, any>
  ) {
    super(message, 'TIMEOUT_ERROR', 'General', context);
    this.name = 'TimeoutError';
    this.operation = operation;
    this.timeoutMs = timeoutMs;

    Object.setPrototypeOf(this, TimeoutError.prototype);
  }

  getUserMessage(): string {
    if (this.operation && this.timeoutMs) {
      return `Operation "${this.operation}" timed out after ${this.timeoutMs}ms`;
    }
    return `Operation timed out: ${this.message}`;
  }
}

/**
 * Utility functions for error handling
 */
export class ErrorUtils {
  /**
   * Check if an error is a model selection error
   */
  static isModelSelectionError(error: any): error is ModelSelectionError {
    return error instanceof ModelSelectionError;
  }

  /**
   * Extract error code from any error
   */
  static getErrorCode(error: any): string {
    if (this.isModelSelectionError(error)) {
      return error.code;
    }
    return 'UNKNOWN_ERROR';
  }

  /**
   * Extract service name from any error
   */
  static getServiceName(error: any): string {
    if (this.isModelSelectionError(error)) {
      return error.service;
    }
    return 'Unknown';
  }

  /**
   * Get user-friendly error message
   */
  static getUserMessage(error: any): string {
    if (this.isModelSelectionError(error)) {
      return error.getUserMessage();
    }
    return error.message || 'An unknown error occurred';
  }

  /**
   * Create error context from additional information
   */
  static createContext(additionalInfo: Record<string, any> = {}): Record<string, any> {
    return {
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'Unknown',
      ...additionalInfo
    };
  }

  /**
   * Wrap a non-model-selection error
   */
  static wrapError(
    error: any, 
    service: string, 
    operation: string,
    context?: Record<string, any>
  ): ModelSelectionError {
    if (this.isModelSelectionError(error)) {
      return error;
    }

    return new ModelSelectionError(
      `${operation} failed: ${error.message || error}`,
      'WRAPPED_ERROR',
      service,
      { ...context, originalError: error.toString() }
    );
  }

  /**
   * Log error with appropriate level
   */
  static logError(error: any, logger?: { error: (msg: string, ...args: any[]) => void }): void {
    const message = this.getUserMessage(error);
    const code = this.getErrorCode(error);
    const service = this.getServiceName(error);

    if (logger) {
      logger.error(`[${service}:${code}] ${message}`, error);
    } else {
      console.error(`[${service}:${code}] ${message}`, error);
    }
  }
}