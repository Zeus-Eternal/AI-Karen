'use client';

import { FeatureFlag } from '@/hooks/use-feature';

/**
 * Feature Flag Config Types
 */
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

/**
 * Environment defaults (local-first dev, locked-down prod)
 */
export const DEFAULT_CONFIGS: Record<
  'development' | 'production' | 'test',
  Partial<Record<FeatureFlag, boolean>>
> = {
  development: {
    'debug.mode': true,
    'analytics.detailed': true,
    'voice.input': true,
    'voice.output': true,
    'attachments.enabled': true,
    'telemetry.enabled': false, // keep dev quiet unless explicitly enabled
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
  },
};

/**
 * Security-critical flags that must never be disabled
 */
export const SECURITY_CRITICAL_FLAGS: FeatureFlag[] = [
  'security.sanitization',
  'security.rbac',
];

/**
 * Performance-sensitive flags to watch in prod
 */
export const PERFORMANCE_CRITICAL_FLAGS: FeatureFlag[] = [
  'performance.virtualization',
  'analytics.detailed',
];

/**
 * Utilities
 */
function hasKey<T extends object>(obj: T, key: PropertyKey): boolean {
  return Object.prototype.hasOwnProperty.call(obj, key);
}

function getEnv(): 'development' | 'production' | 'test' {
  const v =
    (typeof process !== 'undefined' &&
      process.env &&
      (process.env.NODE_ENV as 'development' | 'production' | 'test')) ||
    'production';
  return v ?? 'production';
}

function coerceEnvBool(val: string | undefined): boolean | undefined {
  if (typeof val === 'string') {
    const s = val.trim().toLowerCase();
    if (s === 'true') return true;
    if (s === 'false') return false;
  }
  return undefined;
}

/**
 * Validate a feature flag configuration
 */
export const validateFeatureFlagConfig = (
  config: Partial<Record<FeatureFlag, boolean>>,
  environment: 'development' | 'production' | 'test' = 'production'
): FeatureFlagValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  // 1) Security: never allow disabling critical flags
  SECURITY_CRITICAL_FLAGS.forEach((flag) => {
    if (hasKey(config, flag) && config[flag] === false) {
      errors.push(`Security-critical flag '${flag}' cannot be disabled`);
    }
  });

  // 2) Performance cautions (especially in production)
  if (environment === 'production') {
    if (hasKey(config, 'analytics.detailed') && config['analytics.detailed'] === true) {
      warnings.push('Detailed analytics may impact performance in production');
    }
    if (hasKey(config, 'debug.mode') && config['debug.mode'] === true) {
      warnings.push('Debug mode should not be enabled in production');
    }
  }

  // 3) Privacy cautions
  const voiceIn = hasKey(config, 'voice.input') && config['voice.input'] === true;
  const voiceOut = hasKey(config, 'voice.output') && config['voice.output'] === true;
  if (voiceIn || voiceOut) {
    warnings.push('Voice features may have privacy implications');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
};

/**
 * Merge user config with environment defaults and base defaults
 */
export const mergeWithEnvironmentDefaults = (
  config: Partial<Record<FeatureFlag, boolean>>,
  environment: 'development' | 'production' | 'test' = getEnv()
): Record<FeatureFlag, boolean> => {
  const envDefaults = DEFAULT_CONFIGS[environment] || DEFAULT_CONFIGS.production;

  // Base defaults (stable shape for the app)
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
    'debug.mode': false,
  };

  return {
    ...baseDefaults,
    ...envDefaults,
    ...config,
  } as Record<FeatureFlag, boolean>;
};

/**
 * Load configuration from environment variables (NEXT_PUBLIC_FEATURE_*).
 * NOTE: In Next.js, process.env is statically inlined at build; SSR-safe.
 */
export const loadConfigFromEnvironment = (): Partial<Record<FeatureFlag, boolean>> => {
  const config: Partial<Record<FeatureFlag, boolean>> = {};

  // List all supported flags here to generate exact env var names
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
    'debug.mode',
  ];

  allFlags.forEach((flag) => {
    const envVar = `NEXT_PUBLIC_FEATURE_${flag.toUpperCase().replace(/\./g, '_')}`;
    // process may be undefined in some client bundlers; guard it
    const envValue =
      typeof process !== 'undefined' && process.env ? process.env[envVar] : undefined;
    const bool = coerceEnvBool(envValue);
    if (typeof bool === 'boolean') {
      config[flag] = bool;
    }
  });

  return config;
};

/**
 * Save configuration to localStorage with validation
 */
export const saveConfigToStorage = (
  config: Partial<Record<FeatureFlag, boolean>>,
  storageKey: string = 'feature_flags'
): boolean => {
  try {
    const env = getEnv();
    const validation = validateFeatureFlagConfig(config, env);
    if (!validation.isValid) {
      // optionally log warnings/errors upstream
      return false;
    }

    const configWithMetadata: FeatureFlagConfig = {
      flags: mergeWithEnvironmentDefaults(config, env),
      environment: env,
      version: '1.0.0',
      lastUpdated: new Date().toISOString(),
    };

    if (typeof window !== 'undefined') {
      window.localStorage.setItem(storageKey, JSON.stringify(configWithMetadata));
    }
    return true;
  } catch {
    return false;
  }
};

/**
 * Load configuration from localStorage with validation
 */
export const loadConfigFromStorage = (
  storageKey: string = 'feature_flags'
): Partial<Record<FeatureFlag, boolean>> | null => {
  try {
    if (typeof window === 'undefined') return null;

    const stored = window.localStorage.getItem(storageKey);
    if (!stored) return null;

    const parsed = JSON.parse(stored) as FeatureFlagConfig;
    const env = parsed.environment ?? getEnv();

    const validation = validateFeatureFlagConfig(parsed.flags, env);
    if (!validation.isValid) {
      // stored config invalid → ignore it
      return null;
    }

    return parsed.flags;
  } catch {
    return null;
  }
};

/**
 * Runtime updater helpers (validation included)
 */
export const createConfigUpdater = (
  onUpdate: (config: Partial<Record<FeatureFlag, boolean>>) => void
) => {
  const env = getEnv();

  return {
    updateFlag: (flag: FeatureFlag, value: boolean) => {
      const validation = validateFeatureFlagConfig({ [flag]: value } as Partial<
        Record<FeatureFlag, boolean>
      >, env);

      if (!validation.isValid) {
        throw new Error(`Cannot update flag '${flag}': ${validation.errors.join(', ')}`);
      }
      onUpdate({ [flag]: value } as Partial<Record<FeatureFlag, boolean>>);
    },

    updateFlags: (flags: Partial<Record<FeatureFlag, boolean>>) => {
      const validation = validateFeatureFlagConfig(flags, env);
      if (!validation.isValid) {
        throw new Error(`Cannot update flags: ${validation.errors.join(', ')}`);
      }
      onUpdate(flags);
    },

    resetToDefaults: (environment?: 'development' | 'production' | 'test') => {
      const envResolved = environment ?? env;
      const defaults = mergeWithEnvironmentDefaults({}, envResolved);
      onUpdate(defaults);
    },
  };
};
