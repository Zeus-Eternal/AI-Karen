/**
 * Configuration Management Module
 * 
 * Centralized configuration management for the AI Karen Web UI
 * with environment detection and validation capabilities.
 */

export {
  getEnvironmentConfigManager,
  initializeEnvironmentConfigManager,
} from './environment-config-manager';
export type {
  BackendConfig,
  TimeoutConfiguration,
  RetryPolicy,
  EnvironmentInfo,
  ValidationResult,
} from './environment-config-manager';

// Re-export existing config for backward compatibility
export {
  getWebUIConfig,
  validateConfig,
  logConfigInfo,
  getRuntimeInfo,
  webUIConfig,
} from '../config';
export type { WebUIConfig } from '../config';