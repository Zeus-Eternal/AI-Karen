'use client';
import { FeatureFlag } from '@/hooks/use-feature';
export interface FeatureFlagConfig {
  flags: Record<FeatureFlag, boolean>;
  environment: 'development' | 'production' | 'test';
  version: string;
  lastUpdated: string;
}
export interface FeatureFlagValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}
// Default configuration for different environments
export const DEFAULT_CONFIGS: Record<string, Partial<Record<FeatureFlag, boolean>>> = {
  development: {
    ,
    'analytics.detailed': true,
    'voice.input': true,
    'voice.output': true,
    'attachments.enabled': true,
  },
  production: {
    'debug.mode': false,
    'analytics.detailed': false,
    'voice.input': false,
    'voice.output': false,
    'attachments.enabled': false,
    'security.sanitization': true,
    'security.rbac': true,
    'telemetry.enabled': true,
  },
  test: {
    'debug.mode': false,
    'analytics.detailed': false,
    'telemetry.enabled': false,
    'security.sanitization': true,
    'security.rbac': true,
  }
};
// Security-critical flags that cannot be disabled
export const SECURITY_CRITICAL_FLAGS: FeatureFlag[] = [
  'security.sanitization',
  'security.rbac'
];
// Performance-critical flags that should be carefully managed
export const PERFORMANCE_CRITICAL_FLAGS: FeatureFlag[] = [
  'performance.virtualization',
  'analytics.detailed'
];
/**
 * Validates a feature flag configuration
 */
export const validateFeatureFlagConfig = (
  config: Partial<Record<FeatureFlag, boolean>>,
  environment: string = 'production'
): FeatureFlagValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];
  // Check security-critical flags
  SECURITY_CRITICAL_FLAGS.forEach(flag => {
    if (config.hasOwnProperty(flag) && config[flag] === false) {
      errors.push(`Security-critical flag '${flag}' cannot be disabled`);
    }
  });
  // Check performance implications in production
  if (environment === 'production') {
    if (config.hasOwnProperty('analytics.detailed') && config['analytics.detailed'] === true) {
      warnings.push('Detailed analytics may impact performance in production');
    }
    if (config.hasOwnProperty('debug.mode') && config['debug.mode'] === true) {
      warnings.push('Debug mode should not be enabled in production');
    }
  }
  // Check privacy implications
  if ((config.hasOwnProperty('voice.input') && config['voice.input'] === true) || 
      (config.hasOwnProperty('voice.output') && config['voice.output'] === true)) {
    warnings.push('Voice features may have privacy implications');
  }
  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};
/**
 * Merges configuration with environment-specific defaults
 */
export const mergeWithEnvironmentDefaults = (
  config: Partial<Record<FeatureFlag, boolean>>,
  environment: string = process.env.NODE_ENV || 'production'
): Record<FeatureFlag, boolean> => {
  const envDefaults = DEFAULT_CONFIGS[environment] || DEFAULT_CONFIGS.production;
  // Base defaults
  const baseDefaults: Record<FeatureFlag, boolean> = {
    'chat.streaming': true,
    'chat.tools': true,
    'chat.edit': true,
    'chat.quick_actions': true,
    'copilot.enabled': true,
    'voice.input': false,
    'voice.output': false,
    'attachments.enabled': false,
    'emoji.picker': true,
    'analytics.detailed': false,
    'security.sanitization': true,
    'security.rbac': true,
    'performance.virtualization': true,
    'accessibility.enhanced': true,
    'telemetry.enabled': true,
    'debug.mode': false
  };
  return {
    ...baseDefaults,
    ...envDefaults,
    ...config
  };
};
/**
 * Loads configuration from environment variables
 */
export const loadConfigFromEnvironment = (): Partial<Record<FeatureFlag, boolean>> => {
  const config: Partial<Record<FeatureFlag, boolean>> = {};
  // All possible feature flags
  const allFlags: FeatureFlag[] = [
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
    'debug.mode'
  ];
  // Load from environment variables
  allFlags.forEach(flag => {
    const envVar = `NEXT_PUBLIC_FEATURE_${flag.toUpperCase().replace(/\./g, '_')}`;
    const envValue = process.env[envVar];
    if (envValue !== undefined) {
      config[flag] = envValue.toLowerCase() === 'true';
    }
  });
  return config;
};
/**
 * Saves configuration to localStorage with validation
 */
export const saveConfigToStorage = (
  config: Partial<Record<FeatureFlag, boolean>>,
  storageKey: string = 'feature_flags'
): boolean => {
  try {
    const validation = validateFeatureFlagConfig(config);
    if (!validation.isValid) {
      return false;
    }
    if (validation.warnings.length > 0) {
    }
    const configWithMetadata: FeatureFlagConfig = {
      flags: mergeWithEnvironmentDefaults(config),
      environment: process.env.NODE_ENV || 'production',
      version: '1.0.0',
      lastUpdated: new Date().toISOString()
    };
    if (typeof window !== 'undefined') {
      localStorage.setItem(storageKey, JSON.stringify(configWithMetadata));
    }
    return true;
  } catch (error) {
    return false;
  }
};
/**
 * Loads configuration from localStorage with validation
 */
export const loadConfigFromStorage = (
  storageKey: string = 'feature_flags'
): Partial<Record<FeatureFlag, boolean>> | null => {
  try {
    if (typeof window === 'undefined') {
      return null;
    }
    const stored = localStorage.getItem(storageKey);
    if (!stored) {
      return null;
    }
    const config: FeatureFlagConfig = JSON.parse(stored);
    // Validate the loaded configuration
    const validation = validateFeatureFlagConfig(config.flags);
    if (!validation.isValid) {
      return null;
    }
    if (validation.warnings.length > 0) {
    }
    return config.flags;
  } catch (error) {
    return null;
  }
};
/**
 * Creates a runtime configuration updater
 */
export const createConfigUpdater = (
  onUpdate: (config: Partial<Record<FeatureFlag, boolean>>) => void
) => {
  return {
    updateFlag: (flag: FeatureFlag, value: boolean) => {
      const validation = validateFeatureFlagConfig({ [flag]: value });
      if (!validation.isValid) {
        throw new Error(`Cannot update flag '${flag}': ${validation.errors.join(', ')}`);
      }
      if (validation.warnings.length > 0) {
      }
      onUpdate({ [flag]: value });
    },
    updateFlags: (flags: Partial<Record<FeatureFlag, boolean>>) => {
      const validation = validateFeatureFlagConfig(flags);
      if (!validation.isValid) {
        throw new Error(`Cannot update flags: ${validation.errors.join(', ')}`);
      }
      if (validation.warnings.length > 0) {
      }
      onUpdate(flags);
    },
    resetToDefaults: (environment?: string) => {
      const defaults = mergeWithEnvironmentDefaults({}, environment);
      onUpdate(defaults);
    }
  };
};
