/**
 * Feature Flag Configuration Module
 * Provides configuration management for feature flags
 */

import { FeatureFlags } from './feature-flags';

export type FeatureFlagConfig = Record<string, boolean>;
export type FeatureFlagInput = FeatureFlags | FeatureFlagConfig;

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * Load configuration from environment variables
 */
export function loadConfigFromEnvironment(): Partial<FeatureFlags> {
  const config: Partial<FeatureFlags> = {};
  
  // Map environment variables to feature flags
  const envMappings: Record<string, keyof FeatureFlags> = {
    'NEXT_PUBLIC_CHAT_STREAMING': 'chat.streaming',
    'NEXT_PUBLIC_CHAT_TOOLS': 'chat.tools',
    'NEXT_PUBLIC_CHAT_EDIT': 'chat.edit',
    'NEXT_PUBLIC_CHAT_QUICK_ACTIONS': 'chat.quick_actions',
    'NEXT_PUBLIC_COPILOT_ENABLED': 'copilot.enabled',
    'NEXT_PUBLIC_VOICE_INPUT': 'voice.input',
    'NEXT_PUBLIC_VOICE_OUTPUT': 'voice.output',
    'NEXT_PUBLIC_ATTACHMENTS_ENABLED': 'attachments.enabled',
    'NEXT_PUBLIC_EMOJI_PICKER': 'emoji.picker',
    'NEXT_PUBLIC_ANALYTICS_DETAILED': 'analytics.detailed',
    'NEXT_PUBLIC_SECURITY_SANITIZATION': 'security.sanitization',
    'NEXT_PUBLIC_SECURITY_RBAC': 'security.rbac',
    'NEXT_PUBLIC_PERFORMANCE_VIRTUALIZATION': 'performance.virtualization',
    'NEXT_PUBLIC_ACCESSIBILITY_ENHANCED': 'accessibility.enhanced',
    'NEXT_PUBLIC_TELEMETRY_ENABLED': 'telemetry.enabled',
    'NEXT_PUBLIC_DEBUG_MODE': 'debug.mode',
  };
  
  Object.entries(envMappings).forEach(([envKey, featureKey]) => {
    const envValue = process.env[envKey];
    if (envValue !== undefined) {
      config[featureKey] = envValue === 'true' || envValue === '1';
    }
  });
  
  return config;
}

/**
 * Load configuration from localStorage
 */
export function loadConfigFromStorage(): Partial<FeatureFlags> {
  try {
    const stored = localStorage.getItem('karen-feature-config');
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.warn('Failed to load feature config from storage:', error);
  }
  
  return {};
}

/**
 * Merge configuration with environment defaults
 */
export function mergeWithEnvironmentDefaults(config: Partial<FeatureFlags>): FeatureFlags {
  const envConfig = loadConfigFromEnvironment();
  const defaults: FeatureFlags = {
    'chat.streaming': true,
    'chat.tools': true,
    'chat.edit': false,
    'chat.quick_actions': false,
    'copilot.enabled': true,
    'voice.input': false,
    'voice.output': false,
    'attachments.enabled': true,
    'emoji.picker': true,
    'analytics.detailed': false,
    'security.sanitization': true,
    'security.rbac': false,
    'performance.virtualization': false,
    'accessibility.enhanced': true,
    'telemetry.enabled': true,
    'debug.mode': false,
  };
  
  return {
    ...defaults,
    ...envConfig,
    ...config,
  };
}

/**
 * Validate feature flag configuration
 */
export function validateFeatureFlagConfig(config: FeatureFlagInput): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  // Check that all values are boolean
  Object.entries(config).forEach(([key, value]) => {
    if (typeof value !== 'boolean') {
      errors.push(`Feature flag '${key}' must be a boolean, got ${typeof value}`);
    }
  });
  
  // Check for unknown feature flags
  const knownFeatures = [
    'chat.streaming',
    'chat.tools', 
    'chat.edit',
    'chat.quick_actions',
    'copilot.enabled',
    'voice.input',
    'voice.output',
    'attachments.enabled',
    'emoji.picker',
    'analytics.detailed',
    'security.sanitization',
    'security.rbac',
    'performance.virtualization',
    'accessibility.enhanced',
    'telemetry.enabled',
    'debug.mode',
  ];
  
  Object.keys(config).forEach(key => {
    if (!knownFeatures.includes(key)) {
      warnings.push(`Unknown feature flag '${key}'`);
    }
  });
  
  // Security checks for critical features
  if (config['security.sanitization'] === false) {
    warnings.push('Security sanitization is disabled - this may expose the application to XSS attacks');
  }
  
  if (config['debug.mode'] === true) {
    warnings.push('Debug mode is enabled - this should not be used in production');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Save configuration to localStorage
 */
export function saveConfigToStorage(config: Partial<FeatureFlags>): void {
  try {
    const currentConfig = loadConfigFromStorage();
    const updatedConfig = { ...currentConfig, ...config };
    localStorage.setItem('karen-feature-config', JSON.stringify(updatedConfig));
  } catch (error) {
    console.warn('Failed to save feature config to storage:', error);
  }
}

/**
 * Reset configuration to defaults
 */
export function resetConfigToDefaults(): void {
  try {
    localStorage.removeItem('karen-feature-config');
  } catch (error) {
    console.warn('Failed to reset feature config:', error);
  }
}

/**
 * Get configuration summary for debugging
 */
export function getConfigSummary(config: FeatureFlagInput): Record<string, unknown> {
  const summary: Record<string, unknown> = {
    totalFlags: Object.keys(config).length,
    enabledFlags: Object.values(config).filter(Boolean).length,
    disabledFlags: Object.values(config).filter(v => !v).length,
  };

  Object.entries(config).forEach(([key, value]) => {
    summary[key] = value;
  });

  return summary;
}
