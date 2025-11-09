/**
 * Configuration Management Module
 * 
 * Centralized configuration management for the AI Karen Web UI
 * with environment detection and validation capabilities.
 */

export {
  getEnvironmentConfigManager,
  initializeEnvironmentConfigManager,
  type BackendConfig,
  type BackendConfigType,
  type TimeoutConfiguration,
  type TimeoutConfigurationType,
  type RetryPolicy,
  type RetryPolicyType,
  type EnvironmentInfo,
  type EnvironmentInfoType,
  type ValidationResult,
  type ValidationResultType,
} from './environment-config-manager';

// Re-export existing config for backward compatibility
export {
  getWebUIConfig,
  validateConfig,
  logConfigInfo,
  getRuntimeInfo,
  webUIConfig,
  type WebUIConfig,
} from '../config';