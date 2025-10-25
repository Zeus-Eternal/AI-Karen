/**
 * Connection Module
 * 
 * Exports connection manager, timeout manager, and related utilities
 * for reliable HTTP communication with retry logic and timeout management.
 */

// Connection Manager
export {
  ConnectionManager,
  getConnectionManager,
  initializeConnectionManager,
  CircuitBreakerState,
  ErrorCategory,
  ConnectionError,
} from './connection-manager';

export type {
  ConnectionOptions,
  RequestResult,
  ConnectionStatus,
  ConnectionOptionsType,
  RequestResultType,
  ConnectionStatusType,
  ConnectionErrorType,
} from './connection-manager';

// Timeout Manager
export {
  TimeoutManager,
  getTimeoutManager,
  initializeTimeoutManager,
  OperationType,
} from './timeout-manager';

export type {
  TimeoutSettings,
  OperationTimeouts,
  TimeoutSettingsType,
  OperationTimeoutsType,
} from './timeout-manager';

// Health Monitor
export {
  HealthMonitor,
  getHealthMonitor,
  initializeHealthMonitor,
  HealthEventType,
} from './health-monitor';

export type {
  HealthStatus,
  BackendEndpoint,
  HealthCheckResult,
  MonitoringConfig,
  HealthEvent,
  HealthStatusType,
  BackendEndpointType,
  HealthCheckResultType,
  MonitoringConfigType,
  HealthEventType as HealthEventTypeAlias,
} from './health-monitor';