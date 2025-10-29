/**
 * Connection Library Index
 * 
 * Exports all connection-related utilities, managers, and types
 * for extension authentication and API communication.
 */

// Connection Manager exports
export {
  ConnectionManager,
  getConnectionManager,
  initializeConnectionManager,
  ConnectionError,
  ErrorCategory,
  CircuitBreakerState,
  type RequestConfig,
  type ConnectionOptions,
  type ConnectionResponse,
  type RequestResult,
  type ConnectionStatus,
  type ConnectionOptionsType,
  type RequestResultType,
  type ConnectionStatusType,
  type ConnectionErrorType,
} from './connection-manager';

// Timeout Manager exports
export {
  TimeoutManager,
  getTimeoutManager,
  initializeTimeoutManager,
  OperationType,
  type TimeoutConfig,
  type TimeoutSettings,
  type OperationTimeouts,
  type TimeoutSettingsType,
  type OperationTimeoutsType,
} from './timeout-manager';

// Health Monitor exports (if exists)
export * from './health-monitor';