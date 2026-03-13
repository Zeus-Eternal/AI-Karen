/**
 * Connection Library Index
 * 
 * Exports all connection-related utilities, managers, and types
 * for extension authentication and API communication.
 */

// Connection Manager exports
export {
  getConnectionManager,
  initializeConnectionManager,
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
  getTimeoutManager,
  initializeTimeoutManager,
  type TimeoutConfig,
  type TimeoutSettings,
  type OperationTimeouts,
  type TimeoutSettingsType,
  type OperationTimeoutsType,
} from './timeout-manager';

// Health Monitor exports (if exists)
export * from './health-monitor';  // Ensure that './health-monitor' exists or remove if not necessary.
